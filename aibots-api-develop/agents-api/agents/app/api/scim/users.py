from __future__ import annotations

from typing import Any, Dict, List, Union

import structlog
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig
from atlas.environ import E
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import ScimUser as AliasedScimUser
from atlas.schemas import UserLogin, Uuid
from atlas.services import DS
from atlas.structlog import StructLogService
from atlas.utils import generate_randstr
from beanie.operators import In
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version
from pydantic import StrictStr

from agents.models import ScimGroupDB, ScimReference, ScimUser, ScimUserDB

__all__ = ("router",)


router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "tags": ["SCIMUsers"],
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


class ScimUserPut(APIPostPut, ScimUser):
    """
    PUT representation of a User

     Attributes:
        schemas (list[str]): SCIM resource schema reference
        id (Uuid): Uuid of the SCIM resource
        meta (Meta): Descriptive metadata about the SCIM resource
        external_id (str): External ID of the user, defaults to ID value
        user_name (Optional[str]): Username of the user, defaults to None
        name (ScimName): Full name of the user, extracted from the display name
        display_name (Optional[str]): Display name of the user,
                                    defaults to None
        nick_name (Optional[str]): Nickname of the user, defaults to None
        profile_url (Optional[AnyUrl]): URL of the user's profile, defaults to
                                        None
        title (Optional[str]): Official job title of the
                                user, defaults to None
        user_type (Optional[str]): Used to identify the relationship between
                                the organization and the user, defaults to None
        preferred_language (str): Preferred language of the user, defaults to
                                    en
        locale (str): Preferred locale of the user, defaults to en_SG
        timezone (str): Current timezone of the user, defaults to Singapore
        password (Optional[str]): Password of the user,
                                    defaults to None
        emails (ScimList[ScimEmail]): Email addresses of the user, defaults to
                                        an empty list
        phone_numbers (ScimList[ScimStringProperty]): Phone numbers of the
                                                        user, defaults to an
                                                        empty list
        ims (ScimList[ScimStringProperty]): List of instant messaging handles
                                            of the user, defaults to an empty
                                            list
        photos (ScimList[ScimStringProperty]): List of photos of the user,
                                                defaults to an empty list
        addresses (ScimList[ScimAddress]): List of addresses belonging to the
                                            user, defaults to an empty list
        groups (list[ScimReference]): List of groups the user belongs to,
                                        defaults to an empty list
        entitlements (ScimList[ScimStringProperty]): Permissions that the user
                                                    has, defaults to an empty
                                                    list
        roles (ScimList[ScimStringProperty]): List of roles that the user has,
                                                defaults to an empty list
        x509_certificates (ScimList[ScimStringProperty]): List of X.509
                                                          certificates,
                                                          defaults to an empty
                                                          list
        atlas_extensions (ScimUserExtensions): Atlas extensions to Scim
                                               Users, defaults to
                                               ScimUserExtensions values
    """


class ScimUserPost(APIPostPut, ScimUser):
    """
    POST representation of a User

     Attributes:
        schemas (list[str]): SCIM resource schema reference
        id (Uuid): Uuid of the SCIM resource
        meta (Meta): Descriptive metadata about the SCIM resource
        external_id (str): External ID of the user, defaults to ID value
        user_name (Optional[str]): Username of the user, defaults to None
        name (ScimName): Full name of the user, extracted from the display name
        display_name (Optional[str]): Display name of the user,
                                    defaults to None
        nick_name (Optional[str]): Nickname of the user, defaults to None
        profile_url (Optional[AnyUrl]): URL of the user's profile, defaults to
                                        None
        title (Optional[str]): Official job title of the
                                user, defaults to None
        user_type (Optional[str]): Used to identify the relationship between
                                the organization and the user, defaults to None
        preferred_language (str): Preferred language of the user, defaults to
                                    en
        locale (str): Preferred locale of the user, defaults to en_SG
        timezone (str): Current timezone of the user, defaults to Singapore
        password (Optional[str]): Password of the user,
                                    defaults to None
        emails (ScimList[ScimEmail]): Email addresses of the user, defaults to
                                        an empty list
        phone_numbers (ScimList[ScimStringProperty]): Phone numbers of the
                                                        user, defaults to an
                                                        empty list
        ims (ScimList[ScimStringProperty]): List of instant messaging handles
                                            of the user, defaults to an empty
                                            list
        photos (ScimList[ScimStringProperty]): List of photos of the user,
                                                defaults to an empty list
        addresses (ScimList[ScimAddress]): List of addresses belonging to the
                                            user, defaults to an empty list
        groups (list[ScimReference]): List of groups the user belongs to,
                                        defaults to an empty list
        entitlements (ScimList[ScimStringProperty]): Permissions that the user
                                                    has, defaults to an empty
                                                    list
        roles (ScimList[ScimStringProperty]): List of roles that the user has,
                                                defaults to an empty list
        x509_certificates (ScimList[ScimStringProperty]): List of X.509
                                                          certificates,
                                                          defaults to an empty
                                                          list
        atlas_extensions (ScimUserExtensions): Atlas extensions to Scim
                                               Users, defaults to"""


class ScimUserListResponse(APIGet):
    """
    GET representation of SCIM User Get Response
        schemas(List[StrictStr]): List of SCIM schemas
        total_results(int): Total number of results returned by the search
        start_index(int): The 1-based index of the first result in the curent
                            set of search results
        items_per_page(int): The number of resources returned
                            in a results page
        resources(List[SCIMUser]): List of SCIM Users from search
    """

    schemas: list[StrictStr]
    total_results: int
    start_index: int
    items_per_page: int
    resources: list[ScimUserGet]


class ScimUserGet(APIGet, AliasedScimUser):
    """
    GET representation of a User

    Attributes:
        To be added...
    """


@cbv(router)
class SCIMUsersAPI:
    """
    Class-based view for representing the APIs for managing
    SCIM Users

    Attributes
        To be filled...
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
        self.scim_users: DS = self.atlas.users
        self.scim_groups: DS = self.atlas.db.atlas_dataset(
            ScimGroupDB.Settings.name
        )
        self.logger: StructLogService = self.atlas.logger

    @router.post(
        "/scim/v2/Users/",
        status_code=status.HTTP_201_CREATED,
        response_model=Dict[str, Any],
        response_model_exclude={"atlas_extensions": {"salt"}},
        include_in_schema=False,
    )
    @router.post(
        "/scim/v2/Users",
        status_code=status.HTTP_201_CREATED,
        response_model=Dict[str, Any],
        response_model_exclude={"atlas_extensions": {"salt"}},
        responses={
            status.HTTP_201_CREATED: {
                "description": "Successfully created SCIM Users",
                "content": {"application/json": {"example": []}},
                "model": ScimUserGet,
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    @api_version(1, 0)
    async def create_user(self, scim_user_details: ScimUser) -> Response:
        """
        Creates a new SCIM user

        Args:

            details(ScimUser): Representation of a SCIM User.

        Returns:
            JSONResponse: FastAPI Response

        Raises:
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )
        user: ScimUserDB = ScimUserDB.create_schema(
            user=self.user.id, **scim_user_details.model_dump()
        )
        await self.validate_scim_reference(
            user, "groups", user.groups, self.scim_groups
        )

        if not await self.scim_users.create_item(user):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_create_error_msg,
                details=user.model_dump(exclude_unset=True, mode="json"),
            )
        await logger.ainfo("Creating SCIM user", data=user.model_dump_json())

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            media_type="application/scim+json",
            content=ScimUserGet.model_construct(
                **user.model_dump()
            ).model_dump(mode="json", by_alias=True),
        )

    @router.get(
        "/scim/v2/Users/",
        status_code=status.HTTP_200_OK,
        response_model=Dict[str, Any],
        response_model_exclude={"atlas_extensions": {"salt"}},
        include_in_schema=False,
    )
    @router.get(
        "/scim/v2/Users",
        status_code=status.HTTP_200_OK,
        response_model=Dict[str, Any],
        response_model_exclude={"atlas_extensions": {"salt"}},
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved SCIM Users",
                "content": {"application/json": {"example": []}},
                "model": ScimUserListResponse,
            },
        },
    )
    @api_version(1, 0)
    async def get_users_paginated(
        self,
        # TODO implement error handling
        # TODO implement the query parameters in the future with more details
        include: str | None = Query(None, alias="attributes"),
        exclude: str | None = Query(None, alias="excluded_attributes"),
        query_filter: str = Query(None, alias="filter"),
        count: int = Query(None),
        sort_by: str = Query(None),
        sort_order: str = Query(None),
        start_index: int | None = 0,
    ) -> JSONResponse:
        """
        Retrieves multiple Scim users with pagination

        Args:
            include (str | None): Attributes to be included,
                                  defaults to None
            exclude (str | None): Attributes to be excluded,
                                  defaults to None
            query_filter: (str): String to query documents
            count (int): Specifies the desired maximum number
                         of query results per page
            sort_by (str): The attribute whose value will be
                           used to order the returned responses
            sort_order (str): Order in which the sortBy param is
                              applied. Allowed values are "ascending"
                              and "descending"

        Returns:
            JSONResponse: FastAPI Response
        """
        scim_users: List[ScimUserDB] = await self.scim_users.get_items({})
        schemas: List[str] = list(
            {
                schema
                for scim_user in scim_users
                for schema in scim_user.schemas
            }
        )

        total_results = len(scim_users)
        # TODO: define the no. of resources per page in the future
        items_per_page = total_results
        scim_users_response: Dict[str, Any] = {
            "schemas": schemas,
            "total_results": total_results,
            "items_per_page": items_per_page,
            "start_index": 1,
            "resources": [
                ScimUserGet(**g.model_dump()).model_dump(
                    mode="json", by_alias=True
                )
                for g in scim_users
            ],
        }
        return scim_users_response

    @router.put(
        "/scim/v2/Users/{user_id}/",
        status_code=status.HTTP_200_OK,
        response_model=Dict[str, Any],
        response_model_exclude={"atlas_extensions": {"salt"}},
        include_in_schema=False,
    )
    @router.put(
        "/scim/v2/Users/{user_id}",
        status_code=status.HTTP_200_OK,
        response_model=Dict[str, Any],
        response_model_exclude={"atlas_extensions": {"salt"}},
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully updated user",
                "content": {"application/json": {"example": {}}},
                "model": ScimUserGet,
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def update_user(
        self,
        user_id: Uuid,
        details: ScimUserPut,
        include: str | None = Query(None, alias="attributes"),
        exclude: str | None = Query(None, alias="excluded_attributes"),
    ) -> JSONResponse:
        """
        Args:
            group_id:
            details:
            include (str | None): Attributes to be included,
                                  defaults to None
            exclude (str | None): Attributes to be excluded,
                                  defaults to None

        Returns:

        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # check for existance of SCIM user
        scim_user: ScimUserDB | None = await self.scim_users.get_item(
            ScimUserDB.id == user_id,
            ScimUserDB.meta.deleted == None,  # noqa: E711
        )
        if not scim_user:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_chat_not_found_msg,
                details={"id": user_id},
            )

        version: Union[str, int]
        if details.meta.version is not None:
            version = details.meta.version
        elif isinstance(scim_user.meta.version, int):
            version = scim_user.meta.version + 1
        else:
            version = generate_randstr()

        updated: ScimUserDB = scim_user.update_schema(
            user=self.user.id,
            version=version,
            **details.model_dump(exclude_unset=True),
        )
        await self.validate_scim_reference(
            scim_user, "groups", scim_user.groups, self.scim_groups
        )

        await logger.ainfo(
            f"Updating SCIM user {user_id}", data=updated.model_dump_json()
        )
        if not await self.scim_users.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Error updating Scim User {user_id}",
                details=details.model_dump(exclude_unset=True, mode="json"),
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            media_type="application/scim+json",
            content=ScimUserGet(**updated.model_dump()).model_dump(
                mode="json", by_alias=True
            ),
        )

    @router.get(
        "/scim/v2/Users/{user_id}/",
        status_code=status.HTTP_200_OK,
        response_model=Dict[str, Any],
        response_model_exclude={"atlas_extensions": {"salt"}},
        include_in_schema=False,
    )
    @router.get(
        "/scim/v2/Users/{user_id}",
        status_code=status.HTTP_200_OK,
        response_model=Dict[str, Any],
        response_model_exclude={"atlas_extensions": {"salt"}},
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved user",
                "content": {"application/json": {"example": {}}},
                "model": ScimUserGet,
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_user(
        self,
        user_id: Union[Uuid, str],
        include: str | None = Query(None, alias="attributes"),
        exclude: str | None = Query(None, alias="excluded_attributes"),
    ) -> JSONResponse:
        """
        Retrieves a SCIM Group

        Args:
            user_id (Union[Uuid, str]): User ID
            include (str | None): Attributes to be included,
                                  defaults to None
            exclude (str | None): Attributes to be excluded,
                                  defaults to None

        Returns:
            JSONResponse: FastAPI Response
        """
        # checks if user exists
        scim_user: ScimUserDB | None = await self.scim_users.get_item(
            ScimUserDB.id == user_id,
            ScimUserDB.meta.deleted == None,  # noqa: E711
        )
        if not scim_user:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User does not exist",
                details={"id": user_id},
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            media_type="application/scim+json",
            content=ScimUserGet(**scim_user.model_dump()).model_dump(
                mode="json", by_alias=True
            ),
        )

    @router.delete(
        "/scim/v2/Users/{user_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/scim/v2/Users/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("deleted_response"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def delete_user(self, user_id: Uuid, response: Response) -> Response:
        """
        Deletes a SCIM group

        Args:
            group_id (Union[Uuid, str]): SCIM group ID
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:

        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )
        # checks to see if user exists
        scim_user: ScimUserDB | None = await self.scim_users.get_item(
            ScimUserDB.id == user_id,
            ScimUserDB.meta.deleted == None,  # noqa: E711
        )
        # if user does not exists throw an error
        if not scim_user:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User does not exist",
                details={"id": user_id},
            )
        # if user exists, delete user

        scim_user.delete_schema(user=self.user.id)

        await logger.ainfo(f"Deleting SCIM user {user_id}")
        # set meta.deleted to scim user
        if not await self.scim_users.replace_item(scim_user):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error deleting user",
                details={"id": user_id},
            )

        updated_groups: List[ScimGroupDB] = []

        groups_with_user: list[ScimGroupDB] = await self.scim_groups.get_items(
            In(ScimGroupDB.members.value, [user_id])
        )

        for group in groups_with_user:
            new_members_of_group: list[ScimReference] = [
                member for member in group.members if member.value != user_id
            ]
            group.members = new_members_of_group
            group.update_schema(user=self.user.id)
            updated_groups.append(group)

        if not await self.scim_groups.update_items(*updated_groups):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error deleting user",
                details={"id": user_id},
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @staticmethod
    async def validate_scim_reference(
        user: Union[ScimUserDB, ScimUserPost],
        field: str,
        groups: List[ScimReference],
        reference_col: ScimGroupDB,
    ) -> None:
        """
        Validates if each group in the list of ScimReference in user
        exists using ID

        Args:
            user(
                Union[ScimUserDB, ScimUserPost]
            ): Scim user details
            field(str): Field name being checked
            groups(List[ScimReference]): List of groups to be validated
            reference_col(
                Type[Union[ScimGroupDB, ScimUserDB]]
            ): Reference collection to be checked

        Raises:
            AtlasAPIException: If scim reference does not exist
        """
        # gets list of groups that are user is part of
        q_groups: List[reference_col.dataset] = await reference_col.get_items(
            In(reference_col.dataset.id, [g.value for g in groups])
        )

        if {q.id for q in q_groups} != {g.value for g in groups}:
            # TODO: Raise Scim Exception
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"ScimReferences in {field} do not exist",
                details=user.model_dump(exclude_unset=True, mode="json"),
            )
