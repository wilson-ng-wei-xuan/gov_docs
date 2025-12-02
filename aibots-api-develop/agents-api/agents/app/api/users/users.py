from __future__ import annotations

from typing import Any, Dict, List, Union

import structlog
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig, IDResponse
from atlas.environ import E
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import ScimUser as AliasedScimUser
from atlas.schemas import UserLogin, Uuid
from atlas.services import DS
from atlas.structlog import StructLogService
from atlas.utils import generate_randstr
from beanie.operators import In
from fastapi import APIRouter, Depends, Response, status
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version

from agents.models import ScimGroupDB, ScimReference, ScimUser, ScimUserDB

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


class ScimUserPut(APIPostPut, ScimUser):
    """
    PUT representation of a User

    Attributes:
        schemas (list[str]): Scim resource schema reference
        id (Uuid): Uuid of the Scim resource
        meta (Meta): Descriptive metadata about the Scim resource
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
        schemas (list[str]): Scim resource schema reference
        id (Uuid): Uuid of the Scim resource
        meta (Meta): Descriptive metadata about the Scim resource
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
        password (Optional[str]): Password of the user, defaults to None
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
    """


class ScimUserGet(APIGet, AliasedScimUser):
    """
    GET representation of a User

    Attributes:
        schemas (list[str]): Scim resource schema reference
        id (Uuid): Uuid of the Scim resource
        meta (Meta): Descriptive metadata about the Scim resource
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
    """


@cbv(router)
class UsersAPI:
    """
    Class-based view for representing the APIs for managing
    Users

    Attributes
        user (UserLogin): Authenticated user details
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    def __init__(self):
        super().__init__()
        self.environ: E = self.atlas.environ
        self.scim_users: DS = self.atlas.users
        self.scim_groups: DS = self.atlas.db.atlas_dataset(
            ScimGroupDB.Settings.name
        )
        self.logger: StructLogService = self.atlas.logger

    @router.post(
        "/users/",
        status_code=status.HTTP_201_CREATED,
        include_in_schema=False,
    )
    @router.post(
        "/users",
        status_code=status.HTTP_201_CREATED,
        response_model=IDResponse,
        responses={
            status.HTTP_201_CREATED: {
                "description": "Successfully created Scim Users",
                "content": {"application/json": {"example": []}},
                "model": IDResponse,
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    @api_version(1, 0)
    async def create_user(
        self, scim_user_details: ScimUserPost
    ) -> Dict[str, str]:
        """
        Creates a new Scim user

        Args:

            scim_user_details(ScimUser): Representation of a Scim User.

        Returns:
            IDResponse: id of user created

        Raises:
            AtlasAPIException: if there is an error creating user
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )
        user_id = ScimUserDB.atlas_get_uuid(
            scim_user_details.emails.primary.value
        )
        user: ScimUserDB = ScimUserDB.create_schema(
            uid=user_id, user=self.user.id, **scim_user_details.model_dump()
        )
        await self.validate_scim_reference(
            user, "groups", user.groups, self.scim_groups
        )

        if not await self.scim_users.create_item(user):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error creating user",
                details=user.model_dump(exclude_unset=True, mode="json"),
            )
        # set member into group
        await self.set_member(user)

        await logger.ainfo("Creating Scim user", data=user.model_dump_json())

        return {"id": user.id}

    @router.get(
        "/users/",
        status_code=status.HTTP_200_OK,
        response_model=List[ScimUserGet],
        response_model_by_alias=True,
        response_model_exclude={"__all__": {"atlas_extensions": {"salt"}}},
        include_in_schema=False,
    )
    @router.get(
        "/users",
        status_code=status.HTTP_200_OK,
        response_model=List[ScimUserGet],
        response_model_by_alias=True,
        response_model_exclude={"__all__": {"atlas_extensions": {"salt"}}},
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved Scim Users",
                "content": {"application/json": {"example": []}},
                "model": List[ScimUserGet],
            },
        },
    )
    @api_version(1, 0)
    async def get_users(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves multiple Scim users with pagination

        Returns:
            List[Dict[str, Any]]: List of Scim Users
        """
        scim_users: List[ScimUserDB] = await self.scim_users.get_items({})
        return [u.model_dump() for u in scim_users]

    @router.put(
        "/users/{user_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/users/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def update_user(
        self, user_id: Uuid, details: ScimUserPut, response: Response
    ) -> Response:
        """
        Args:
            user_id (Uuid): Uuid of the user to update
            details (ScimUserPut): details of user being updated
        Returns:
            Response
        Raises:
            AtlasException: if user is not found
            AtlasException: if user is not being added
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # check for existance of Scim user
        scim_user: ScimUserDB | None = await self.scim_users.get_item(
            ScimUserDB.id == user_id,
            ScimUserDB.meta.deleted == None,  # noqa: E711
        )
        if not scim_user:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="There was no user found",
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
            scim_user, "groups", details.groups, self.scim_groups
        )

        await logger.ainfo(
            f"Updating Scim user {user_id}", data=updated.model_dump_json()
        )
        if not await self.scim_users.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Error updating Scim User {user_id}",
                details=details.model_dump(exclude_unset=True, mode="json"),
            )
        # set as group member
        await self.set_member(scim_user)
        to_be_removed: set = {g.value for g in scim_user.groups}.difference(
            {g.value for g in details.groups}
        )
        group_to_unset_user_from: List[ScimReference] = [
            g for g in scim_user.groups if g.value in to_be_removed
        ]
        # unsets group member
        # TODO: write test case for this
        await self.unset_member(user_id, group_to_unset_user_from)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get(
        "/users/{user_id}/",
        status_code=status.HTTP_200_OK,
        response_model=ScimUserGet,
        response_model_by_alias=True,
        response_model_exclude={"atlas_extensions": {"salt"}},
        include_in_schema=False,
    )
    @router.get(
        "/users/{user_id}",
        status_code=status.HTTP_200_OK,
        response_model=ScimUserGet,
        response_model_by_alias=True,
        response_model_exclude={"atlas_extensions": {"salt"}},
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully requested user",
                "content": {"application/json": {"example": {}}},
                "model": ScimUserGet,
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_user(self, user_id: Union[Uuid, str]) -> Dict[str, Any]:
        """
        Retrieves a Scim Group

        Args:
            user_id (Union[Uuid, str]): User ID

        Returns:
            Dict[str, Any]: Scim user
        Raises:
            AtlasAPIException: if user is not found
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

        return scim_user.model_dump()

    @router.delete(
        "/users/{user_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/users/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("deleted_response"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def delete_user(self, user_id: Uuid, response: Response) -> Response:
        """
        Deletes a Scim group

        Args:
            user_id (Uuid): Scim user ID
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If user does not exist
            AtlasAPIException: If there is an internal error deleting user
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

        await logger.ainfo(f"Deleting Scim user {user_id}")
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

    async def set_member(self, user: ScimUserDB) -> None:
        """
        sets a member when group is added

        Args:
            user (Union[ScimUser,ScimUserDB]): Scim group ID

        Returns: None
        Raises:
            AtlasAPIException: if there is an error retrieving groups
            AtlasAPIException: if there is an error updating groups
        """
        # 1)get all groups that are under user's set groups

        groups: List[ScimGroupDB] = await self.scim_groups.get_items(
            In(ScimGroupDB.id, [g.value for g in user.groups]),
            ScimGroupDB.meta.deleted == None,  # noqa: E711
        )

        user_ref: ScimReference = ScimReference(
            ref=str(self.environ.project.pub_url) + f"users/{user.id}",
            type="users",
            value=user.id,
            display=user.display_name,
        )
        # 2) adds scim reference to user in each of the group
        updated: List[ScimGroupDB] = []
        for group in groups:
            if user.id not in [m.value for m in group.members]:
                group.members.append(user_ref)
                updated.append(group)

        # 3) mass update groups
        if not await self.scim_groups.update_items(*updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error updating groups",
                details={"groups": [g.model_dump() for g in groups]},
            )

    async def unset_member(
        self, user_id: Uuid, group_refs: List[ScimReference]
    ) -> None:
        """
        unsets a member when group is removed

        Args:
            groups (List[ScimReference]): List of groups to unset user

        Returns: None
        Raises:
            AtlasAPIException: if there is an error retrieving groups
            AtlasAPIException: if there is an error updating groups
        """
        # get all groups
        groups: List[ScimGroupDB] = await self.scim_groups.get_items(
            In(ScimGroupDB.id, [g.value for g in group_refs]),
            ScimGroupDB.meta.deleted == None,  # noqa: E711
        )
        # iterate and unset user from members & adminstrators if present
        updated: List[ScimGroupDB] = []
        # append to updated groups
        for group in groups:
            new_members = [g for g in group.members if g.value != user_id]
            group.members = new_members
            group.update_schema(user=self.user.id)
            updated.append(group)
        # update all group items
        if not await self.scim_groups.update_items(*groups):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error updating groups",
                details={"groups": [g.model_dump() for g in groups]},
            )

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
