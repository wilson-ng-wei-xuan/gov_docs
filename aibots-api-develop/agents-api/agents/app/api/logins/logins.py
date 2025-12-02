from __future__ import annotations

from typing import Any

import structlog
from atlas.asgi.schemas import AtlasASGIConfig
from atlas.environ import E
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.jose import JoseService
from atlas.schemas import UserLogin
from atlas.services import DBS, DS
from atlas.structlog import StructLogService
from fastapi import APIRouter, Depends, Response, status
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version

from agents.models import UserLoginGet

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


@cbv(router)
class LoginAPI:
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
        self.logins: DS = self.atlas.logins
        self.jwt: JoseService = self.atlas.services.get("jwt")
        self.logger: StructLogService = self.atlas.logger

    @router.get(
        "/logins/",
        status_code=status.HTTP_200_OK,
        response_model=list[UserLoginGet],
        response_model_exclude={
            "__all__": {"token", "access_token", "jti", "at_hash", "start_use"}
        },
        include_in_schema=False,
    )
    @router.get(
        "/logins",
        status_code=status.HTTP_200_OK,
        response_model=list[UserLoginGet],
        response_model_exclude={
            "__all__": {"token", "access_token", "jti", "at_hash", "start_use"}
        },
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved all User Login details",
                "content": {"application/json": {"example": []}},
                "model": list[UserLoginGet],
            },
            **AtlasRouters.response("403_permissions_error"),
        },
    )
    @api_version(1, 0)
    async def get_logins(self) -> list[dict[str, Any]]:
        """
        Retrieves all Users Logins

        Returns:
            Response: FastAPI Response
        """
        # TODO: Add permissions
        # TODO: Add filters based on user's role
        return [
            self.jwt.atlas_decode(i).model_dump()
            for i in await self.logins.get_items({})
        ]

    @router.delete(
        "/logins/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/logins",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("deleted_response"),
        },
    )
    @api_version(1, 0)
    async def logout_user(self, response: Response) -> Response:
        """
        Logs a user out by deleting user login entry

        Args:
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response
        """

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # TODO: Support admin mass logout via query params
        # Delete User Login details
        logger.info(f"Logging user {self.user.email} out")
        await self.logins.delete_item_by_id(self.user.id)

        response.status_code = status.HTTP_204_NO_CONTENT
        return response
