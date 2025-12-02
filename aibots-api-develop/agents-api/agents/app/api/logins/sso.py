from __future__ import annotations

import base64
import json
from typing import Annotated, Any, Optional

import httpx
import structlog
from annotated_types import Ge
from atlas.asgi.exceptions import AtlasAPIException, AtlasAuthException
from atlas.asgi.schemas import AtlasASGIConfig
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.httpx import HttpxService
from atlas.schemas import (
    Email,
    UserLogin,
)
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Json,
    StrictStr,
)

from agents.mixins.uam import LoginsAPIMixin
from agents.models import (
    RoleDB,
    ScimGroupDB,
    ScimUserDB,
    UserLoginGet,
)

__all__ = ("router",)


router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "tags": ["Logins"],
        "prefix": "",
        "dependencies": [
            Depends(AtlasDependencies.get_registry_item("reject_api_key"))
        ],
        "responses": {
            **AtlasRouters.response("500_internal_server_error"),
        },
    }
)


class MoonshotSSOPost(BaseModel):
    """
    POST representation of Moonshot SSO

    Attributes:
        accessToken (str): AWS SSO Access Token
        identity (str): AWS SSO identity
        data (str): AWS SSO data
    """

    accessToken: StrictStr
    identity: StrictStr
    data: StrictStr


class AWSCognitoPayload(BaseModel):
    """
    POST representation of AWS Cognito payload

    Attributes:
        email (EmailStr): Email of the user
        email_verified (bool): Is the email verified
        exp (int): Expiry timestamp from epoch
        identities (Json): User ID data from AWS Cognito
        iss (str): Issuer
        name (str): Name of the user
        profile (str): Profile of the user
        sub (str): Subject of the user
        username (str): AWS Cognito username
        preferred_username (str): Name of the user
    """

    model_config: ConfigDict = ConfigDict(extra="allow")

    email: Annotated[EmailStr, AfterValidator(lambda v: v.lower())]
    email_verified: bool = False
    exp: Annotated[float, Ge(0)] = 0
    identities: Json = []
    iss: str = ""
    name: str = ""
    profile: str = ""
    sub: str = ""
    username: str = ""
    preferred_username: str = ""


@cbv(router)
class SSOMoonshotAPI(LoginsAPIMixin):
    """
    Class-based view for representing the POST APIs of
    authentication via Moonshot's SSO funcitonality

    Attributes
        atlas (AtlasASGIConfig): Atlas API config
        environ (AppraiserEnviron): Environment variables
        db (BeanieService): MongoDB Service
        jwt (JoseService): JWT Service
        roles (DS): Roles Dataset
        users (DS): Users Dataset
        logins (DS): User Login Dataset
        logger (StructLogService): Atlas logger
    """

    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    # TODO: Request details to be extracted and bound to logger
    def __init__(self):
        super().__init__()
        self.rest: HttpxService = self.atlas.rest

    @staticmethod
    def decode_jwt(jwt: str) -> dict[str, Any]:
        """
        Decodes an AWS Cognito JWT token

        Args:
            jwt (str): AWS Cognito JWT

        Returns:
            dict[str, Any]: Decoded AWS Cognito JWT token
        """
        return json.loads(base64.b64decode(jwt.split(".")[0]).decode("utf-8"))

    @router.post(
        "/sso/moonshot/logins/",
        status_code=status.HTTP_201_CREATED,
        include_in_schema=False,
    )
    @router.post(
        "/sso/moonshot/logins",
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_201_CREATED: {
                "description": "Successfully logged a user in via SSO",
                "content": {"application/json": {"example": {}}},
                "model": UserLoginGet,
            },
            **AtlasRouters.response("401_authentication_error"),
        },
    )
    @api_version(1, 0)
    async def login_moonshot_sso(self, sso: MoonshotSSOPost) -> JSONResponse:
        """
        Logins a user via Moonshot SSO, registering new users
        in the process

        Args:
            sso (MoonshotSSOPost): Moonshot SSO details

        Returns:
            Response: FastAPI Response
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Decode AWS Cognito ODIC token
        try:
            odic_token: dict[str, Any] = self.decode_jwt(sso.data)
        except Exception as e:
            raise AtlasAuthException(
                "Unable to decode Moonshot JWT token"
            ) from e

        # Retrieve public key from AWS
        try:
            resp: httpx.Response = await self.rest.get(
                f"https://public-keys.auth.elb.{self.environ.aws_region}.amazonaws.com/{odic_token['kid']}"
            )
            public_key: str = resp.text
        except Exception as e:
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Unable to retrieve public key from AWS",
            ) from e

        try:
            aws_jwt: AWSCognitoPayload = AWSCognitoPayload(
                **self.jwt.service.decode(
                    sso.data, public_key, algorithms=["ES256"]
                )
            )
        except Exception as e:
            raise AtlasAuthException(
                "Unable to decode Moonshot JWT token"
            ) from e

        # Check if user already exists
        # If user does not exist, check domain rules and create user
        user_role: RoleDB
        new_user: bool
        user_id: str = ScimUserDB.atlas_get_uuid(aws_jwt.email)
        user: Optional[ScimUserDB] = await self.users.get_item_by_id(user_id)
        if user:
            # 1. Validate if user is authorised
            # 2. Update a user's unverified state
            await self.atlas_block_unauthorised_user(user)
            await self.atlas_update_unverified_user(user)

            user_role = await self.roles.get_item_by_id(
                user.roles.primary.value
            )
            new_user = False
        else:
            group: ScimGroupDB = await self.atlas_block_unauthorised_group(
                aws_jwt.email
            )
            user, user_role, permissions, group = await self.atlas_create_user(
                email=aws_jwt.email,
                name=Email.atlas_get_name(aws_jwt.email),
                username=aws_jwt.preferred_username,
                uid=user_id,
                group=group,
            )

            # Create a new user
            await logger.ainfo(
                f"Creating new user {user.emails.primary.value} with "
                f"role {user_role.name}",
                data=user.model_dump_json(),
            )
            if not await self.users.create_item(user):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Error creating new user",
                )

            # Add their permission set
            await logger.ainfo(
                "Create user's permission set",
                data=permissions.model_dump_json(),
            )
            if not await self.permissions.create_item(permissions):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Error creating user's permission set",
                )

            # Add the association to a new group
            await logger.ainfo(
                f"Adding user {user.emails.primary.value} "
                f"to group {group.display_name}",
            )
            if not await self.groups.replace_item(group):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Error adding user to group",
                )
            new_user = True

        # Log user out and back in again
        await self.atlas_get_login(user)

        # Retrieve all individual and group permissions
        (
            user_permissions,
            all_permissions,
            group_permissions,
        ) = await self.atlas_get_all_user_permissions(user)

        # Login a user
        user_login: UserLogin = await self.atlas_login_user(
            all_permissions=all_permissions,
            group_permissions=group_permissions,
            user_permissions=user_permissions,
            error_details={},
            logger=logger,
            new_user=new_user,
            user=user,
            user_role=user_role,
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=UserLoginGet.model_construct(
                **user_login.model_dump()
            ).model_dump(mode="json", by_alias=True, exclude={"access_token"}),
            headers={"Authorization": f"Bearer {user_login.token}"},
        )
