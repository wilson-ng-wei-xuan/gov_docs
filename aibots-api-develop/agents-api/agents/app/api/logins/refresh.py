from __future__ import annotations

import traceback
from datetime import datetime, timedelta, timezone

import structlog
from atlas.asgi.exceptions import AtlasAPIException, AtlasAuthException
from atlas.asgi.schemas import AtlasASGIConfig
from atlas.environ import E
from atlas.exceptions import AtlasServiceException
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.jose import JoseService
from atlas.schemas import Login, UserLogin
from atlas.services import DBS, DS
from atlas.structlog import StructLogService
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version
from pydantic import BaseModel

from agents.models import LoginDB, UserLoginGet

__all__ = ("router",)

router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "tags": ["Logins"],
        "prefix": "",
        "dependencies": [
            Depends(AtlasDependencies.get_registry_item("reject_api_key"))
        ],
        "responses": {
            **AtlasRouters.response("401_authentication_error"),
            **AtlasRouters.response("500_internal_server_error"),
        },
    }
)


class RefreshToken(BaseModel):
    """
    Refresh token body

    Attributes:
        token (str): Refresh token
    """

    token: str


@cbv(router)
class RefreshAPI:
    """
    Class-based view for representing the POST APIs of
    authentication with Email OTPs

    Attributes
        user (UserLogin): Authenticated user details
        atlas (AtlasASGIConfig): Atlas API config
        environ (AppraiserEnviron): Environment variables
        db (BeanieService): MongoDB Service
        logger (StructLogService): Atlas logger
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    # TODO: Request details to be extracted and bound to logger
    def __init__(self):
        super().__init__()
        self.environ: E = self.atlas.environ
        self.db: DBS = self.atlas.db
        self.jwt: JoseService = self.atlas.services.get("jwt")
        self.logins: DS = self.atlas.logins
        self.logger: StructLogService = self.atlas.logger

    @router.post(
        "/refresh/",
        status_code=status.HTTP_201_CREATED,
        include_in_schema=False,
    )
    @router.post(
        "/refresh",
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_201_CREATED: {
                "description": "Successfully logged a user in via Email OTP",
                "content": {"application/json": {"example": {}}},
                "model": UserLoginGet,
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    @api_version(1, 0)
    async def refresh_token(self, token: RefreshToken) -> JSONResponse:
        """
        Refreshes a user's login token

        Attributes:
            token (RefreshToken): Refresh token

        Returns:
            JSONResponse: FastAPI Response

        Raises:
            AtlasAuthException: Refresh token provided does not match
            AtlasAuthException: Exceeded number of allowable token
                                refresh attempts
            AtlasAPIException: Error encrypting JWT token
            AtlasAPIException: Error inserting new token into DB
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Validate the user's refresh token
        if token.token != self.user.refresh_token:
            raise AtlasAuthException(
                message="Refresh token provided does not match",
                details=token.model_dump(exclude_unset=True, mode="json"),
            )

        # Check that the user has not refreshed more than the maximum
        # allowable attempts
        if self.user.refresh_count >= self.user.max_refresh:
            raise AtlasAuthException(
                message="Exceeded number of allowable token refresh attempts"
            )

        # Delete the current User's Login details
        await self.logins.delete_item_by_id(self.user.id)

        # Regenerate the user's login details
        new_login: UserLogin = UserLogin(
            **self.user.model_dump(
                include={
                    "name",
                    "email",
                    "scopes",
                    "item_scopes",
                    "role",
                    "superuser",
                    "agency",
                }
            ),
            id=self.user.id,
            issuer=self.environ.issuer,
            product=self.environ.project.public_domain,
            start_use=datetime.now(timezone.utc),
            expiry=datetime.now(timezone.utc)
            + timedelta(hours=self.environ.expiry.jwt),
            refresh_count=self.user.refresh_count + 1,
            max_refresh=self.user.max_refresh,
        )

        # Encode the new login details
        try:
            login: Login = self.jwt.atlas_encode(new_login)
        except AtlasServiceException as e:
            logger.exception(str(e))
            logger.exception(traceback.format_exc())
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error generating JWT",
                details=new_login.model_dump(exclude_unset=True, mode="json"),
            ) from e

        # Insert into DB
        logger.info(
            f"Regenerating user {self.user.email}'s JWT",
            data=new_login.model_dump_json(),
        )
        if not await self.logins.create_item(
            LoginDB.model_construct(**login.model_dump())
        ):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error refreshing user token",
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=UserLoginGet.model_construct(
                **new_login.model_dump()
            ).model_dump(mode="json", by_alias=True, exclude={"access_token"}),
            headers={"Authorization": f"Bearer {new_login.token}"},
        )
