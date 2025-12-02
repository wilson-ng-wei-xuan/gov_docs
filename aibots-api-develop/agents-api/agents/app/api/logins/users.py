from __future__ import annotations

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

import json
import re
from typing import Any, Dict, List, Optional, Set, Union

import httpx
import structlog
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig
from atlas.environ import E
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.httpx import HttpxService
from atlas.schemas import (
    DescriptiveNameOptional,
    Email,
    ScimStringProperty,
    UserLogin,
    Uuid,
)
from atlas.services import DS
from atlas.structlog import StructLogService
from atlas.utils import generate_randstr
from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.find.logical import Or
from fastapi import APIRouter, Depends, Response, status
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version
from pydantic import EmailStr, StrictStr, StringConstraints

from agents.constants import DEFAULT_EMAIL_TEMPLATES
from agents.mixins.uam import UsersAPIMixin
from agents.models import (
    PermissionsDB,
    RoleDB,
    ScimGroupDB,
    ScimUserDB,
)

__all__ = ("router",)


router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "tags": ["Users"],
        "prefix": "",
        "dependencies": [
            Depends(AtlasDependencies.get_registry_item("reject_api_key"))
        ],
        "responses": {
            **AtlasRouters.response("401_authentication_error"),
            **AtlasRouters.response("403_permissions_error"),
            **AtlasRouters.response("500_internal_server_error"),
        },
    }
)


class UserProfilePut(APIPostPut, DescriptiveNameOptional):
    """
    PUT representation of a User's Profile

    Attributes:
        name (StrictStr | None): Name field with no length restriction
        description (StrictStr | None): Description field, defaults to None
        agency (StrictStr | None): Agency of the user, defaults to None
        avatar (Uuid | None): Avatar UUID of the User, defaults to None
        settings (dict[str, Any] | None): Settings of the User, defaults to
                                          None
        favourites (dict[str, list[str]] | None): Favourites of the User,
                                                  defaults to None
        details (dict[str, Any] | None): Additional Details of the User,
                                         defaults to None
    """

    agency: StrictStr | None = None
    description: str | None = None
    avatar: Uuid | None = None
    settings: Dict[str, Any] | None = None
    favourites: Dict[str, List[str]] | None = None
    details: Dict[str, Any] | None = None


class UnverifiedUserGet(APIGet):
    """
    GET representation of an unverified user

    Attributes:
        id (Uuid): Created ID of the user
        email (EmailStr): Email of the user
    """

    id: Uuid
    email: EmailStr


class UserQueriesPost(APIPostPut):
    """
    POST representation of a user query

    Attributes:
        ids (List[Uuid]): List of IDs to filter
        emails (List[str]): List of strings to match with user's email
    """

    ids: List[Uuid]
    emails: List[str]


class UserBrief(APIGet):
    """
    Get representation of a Brief identifying details of a User in
    Group Hierarchy

    Attributes:
        external_id (StrictStr | None): Identifier of the resource useful from
                                        the perspective of the provisioning
                                        client, defaults to None.
                                        See section 3.1 of RFC 7643
        user_name (StrictStr | None): Identifier for the user, typically used
                                      by the user to directly authenticate (id
                                      and externalId are opaque identifiers
                                      generally not known by users), defaults
                                      to None
        display_name (StrictStr | None): Name of the user suitable for display
                                         to end-users, defaults to None
        nick_name (StrictStr | None): Casual way to address the user in real
                                      life, defaults to None
        profile_url (StrictStr | None): URI pointing to a location
                                        representing the User's online
                                        profile, defaults to None
        title (StrictStr | None): Flexible string for representing a user's
                                  professional title, defaults to None
        deleted (bool | None): show if user has been shallow deleted
        verified (bool | None): show if user has been verified
    """

    external_id: StrictStr | None = None
    user_name: StrictStr | None = None
    display_name: StrictStr | None = None
    nick_name: StrictStr | None = None
    profile_url: StrictStr | None = None
    title: StrictStr | None = None
    deleted: bool | None = False
    verified: bool | None = True


@cbv(router)
class UsersAPI(UsersAPIMixin):
    """
    Class-based view for representing the APIs for managing
    Users

    Attributes
        atlas (AtlasASGIConfig): Atlas API config
        environ (AppraiserEnviron): Environment variables
        db (BeanieService): MongoDB Service
        jwt (JWTService): JWT Service
        roles (DS): Roles Dataset
        users (DS): Users Dataset
        logins (DS): User Login Dataset
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
        self.roles: DS = self.atlas.roles
        self.users: DS = self.atlas.users
        self.groups: DS = self.atlas.db.atlas_dataset(
            ScimGroupDB.Settings.name
        )
        self.permissions: DS = self.atlas.db.atlas_dataset(
            PermissionsDB.Settings.name
        )
        self.rest: HttpxService = self.atlas.rest
        self.logger: StructLogService = self.atlas.logger

    @router.post(
        "/users/unverified/",
        status_code=status.HTTP_201_CREATED,
        response_model=List[UnverifiedUserGet],
        include_in_schema=False,
    )
    @router.post(
        "/users/unverified",
        status_code=status.HTTP_201_CREATED,
        response_model=List[UnverifiedUserGet],
        responses={
            status.HTTP_201_CREATED: {
                "description": "Successfully created SCIM Unverified Users",
                "content": {"application/json": {"example": []}},
                "model": List[UnverifiedUserGet],
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    @api_version(1, 0)
    async def create_unverified_users(
        self,
        emails: List[Annotated[EmailStr, StringConstraints(to_lower=True)]],
    ) -> List[Dict[str, Any]]:
        """
        Create unverified SCIM users

        Args:
            emails (List[EmailStr]): List of unverified emails

        Returns:
            List[Dict[str, Any]]: List of SCIM users created
        Raises:
            AtlasAPIException: If there is an error adding users
            AtlasAPIException: If there is an error sending emails
            AtlasAPIException: If format of list of emails is incorrect
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Ensure no duplicates
        if await self.users.get_items(In(ScimUserDB.emails.value, emails)):
            raise AtlasAPIException(
                status_code=status.HTTP_409_CONFLICT,
                message="Users already exist",
                details={"emails": emails},
            )

        # Check if groups are authorised
        domains: Set[str] = {Email.atlas_get_domain(e) for e in emails}
        groups: List[ScimGroupDB] = await self.groups.get_items(
            In(
                ScimGroupDB.atlas_extensions.domain,
                domains,
            ),
            ScimGroupDB.atlas_extensions.allow == True,  # noqa: E712
            ScimGroupDB.meta.deleted == None,  # noqa: E711
        )
        if len(groups) < len(domains):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Attempting to create unverified users "
                "belonging to unauthorised group",
                details={"emails": emails},
            )
        groups_dict: Dict[str, ScimGroupDB] = {
            g.atlas_extensions.domain: g for g in groups
        }

        user_role: RoleDB
        users: List[ScimUserDB] = []
        permissions: List[PermissionsDB] = []
        superuser_role: RoleDB = await self.roles.get_item(
            RoleDB.superuser == True  # noqa: E712
        )
        default_role: RoleDB = await self.roles.get_item(
            RoleDB.default == True  # noqa: E712
        )
        for email in emails:
            # Populate User with default values
            user, user_role, permission, group = await self.atlas_create_user(
                email=email,
                name=Email.atlas_get_name(email),
                username=email,
                group=groups_dict[Email.atlas_get_domain(email)],
                uid=ScimUserDB.atlas_get_uuid(email),
                verified=False,
                active=False,
                default_role=default_role,
                superuser_role=superuser_role,
            )
            users.append(user)
            permissions.append(permission)

        # Creating users and their associated permissions
        await logger.ainfo(
            "Inserting users", data=[u.model_dump_json() for u in users]
        )
        if not await self.users.create_items(users):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error inserting users",
                details={"emails": emails},
            )
        await logger.ainfo(
            "Inserting user permissions",
            data=[p.model_dump_json() for p in permissions],
        )
        if not await self.permissions.create_items(permissions):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error inserting user permissions",
                details={"emails": emails},
            )
        await logger.ainfo(
            "Updating user's group memberships",
            data=[g.model_dump_json() for g in groups],
        )
        if not await self.groups.update_items(*groups):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error adding users to groups",
            )

        # Mass send email to unverified users prompting them to login
        # to verify their email addresses
        for email in emails:
            email: Email = Email(
                name=self.environ.email.name,
                to=[email],
                subject="Welcome to AIBots! You've Been Invited",
                text=DEFAULT_EMAIL_TEMPLATES.get("unverified_user_text"),
                html=DEFAULT_EMAIL_TEMPLATES.get("unverified_user_html"),
            )
            if self.environ.use_aws:
                auth: dict[str, Any] = json.loads(self.environ.emails_api.auth)
                email.sender = auth["SMTP_FROM"]
                email_body: dict[str, Any] = {
                    **email.model_dump(),
                    "smtp_key": auth,
                    "sender_name": self.environ.email.name,
                }
                resp: httpx.Response = await self.rest.post(
                    str(self.environ.emails_api.url),
                    content=json.dumps(email_body).encode("utf-8"),
                )
                try:
                    resp.raise_for_status()
                except (httpx.HTTPError, httpx.StreamError):
                    raise AtlasAPIException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        message="Error when sending email login via Email ",
                        details=await resp.json(),
                    ) from None
            else:
                email.sender = self.environ.email.sender
                self.atlas.emails.atlas_send_email(email=email)

        return [
            {**u.model_dump(include=["id"]), "email": emails[idx]}
            for idx, u in enumerate(users)
        ]

    @router.post(
        "/queries/users/",
        status_code=status.HTTP_200_OK,
        response_model=List[UserBrief],
        include_in_schema=False,
    )
    @router.post(
        "/queries/users",
        status_code=status.HTTP_200_OK,
        response_model=List[UserBrief],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved Users",
                "content": {"application/json": {"example": []}},
                "model": List[UserBrief],
            },
        },
    )
    @api_version(1, 0)
    async def get_users_by_query(
        self, user_queries: UserQueriesPost
    ) -> List[Dict[str, Any]]:
        """
        Updates a User's profile, users can only update their
        own profiles

        Args:
            user_queries (UserQueriesPost): User query body for querying users

        Returns:
            List[dict[str, Any]]: List of queried users

        Raises:
            AtlasAPIException: If no IDs or emails given
        """

        # Handle scenario where no IDs or emails were provided
        ids, emails = user_queries.ids, user_queries.emails
        if not (ids or emails):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Only usage with IDs or Emails queries is supported",
            )

        filters: List[Any] = []
        if ids:
            filters.append(In(ScimUserDB.id, ids))
        if emails:
            filters.append(
                In(
                    ScimUserDB.emails.value,
                    [
                        re.compile(r"{}".format(e.lower()), re.IGNORECASE)
                        for e in emails
                    ],
                )
            )

        # TODO: Improve with RBAC
        return [
            {
                **u.model_dump(
                    include=[
                        "external_id",
                        "user_name",
                        "display_name",
                        "nick_name",
                        "profile_url",
                        "title",
                    ],
                ),
                "deleted": (u.meta.deleted != None),  # noqa: E711
                "verified": u.atlas_extensions.verified,
            }
            for u in await self.users.get_items(
                Or(*filters), **{"sort": [(ScimUserDB.display_name, 1)]}
            )
        ]

    @router.put(
        "/profiles/{user_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/profiles/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def update_user_profile(
        self,
        user_id: Uuid,
        profile_details: UserProfilePut,
        response: Response,
    ) -> Response:
        """
        Updates a User's profile, users can only update their
        own profiles

        Args:
            user_id (Uuid): UUID of the User
            profile_details (UserProfilePut): User Profile details
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response
        """

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Ensure user only updates his own profile
        if user_id != self.user.id:
            raise AtlasAPIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Unable to modify another user's profile",
                details={"id": user_id},
            )

        # Check user exists
        user: ScimUserDB | None = await self.users.get_item_by_id(user_id)
        if not user:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User does not exist",
                details={"id": user_id},
            )

        # Validating if agency provided exists
        if profile_details.agency:
            group: Optional[ScimGroupDB] = await self.groups.get_item(
                ScimGroupDB.atlas_extensions.agency == profile_details.agency,
                ScimGroupDB.meta.deleted == None,  # noqa: E711
                ScimGroupDB.atlas_extensions.allow == True,  # noqa: E712
            )
            if not group:
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Invalid agency provided",
                    details=profile_details.model_dump(
                        exclude_unset=True, mode="json"
                    ),
                )

        version: Union[str, int]
        if isinstance(user.meta.version, int):
            version = user.meta.version + 1
        else:
            version = generate_randstr()

        # Updating user profile details
        name: str = user.display_name
        if profile_details.name:
            name: str = profile_details.name
        photos: List[ScimStringProperty[str]] = user.photos
        if profile_details.avatar and profile_details.avatar not in [
            photo.value for photo in user.photos
        ]:
            user.photos.append(
                ScimStringProperty[str](
                    display="Avatar",
                    primary=False,
                    type="avatar",
                    value=profile_details.avatar,
                )
            )
        updated: ScimUserDB = user.update_schema(
            user=self.user.id,
            version=version,
            **{
                "display_name": name,
                "photos": photos,
                "atlas_extensions": {
                    **user.atlas_extensions.model_dump(),
                    **profile_details.model_dump(
                        exclude={"name", "avatar"}, exclude_unset=True
                    ),
                },
            },
        )
        await logger.ainfo(
            f"Updating user {user_id}", data=updated.model_dump_json()
        )
        if not await self.users.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error updating user",
                details=profile_details.model_dump(
                    exclude_unset=True, mode="json"
                ),
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response
