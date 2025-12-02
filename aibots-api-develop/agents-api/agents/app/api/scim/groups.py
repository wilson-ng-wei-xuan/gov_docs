from __future__ import annotations

from typing import Annotated, Any, Dict, List, Union

import structlog
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig
from atlas.environ import E
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import (
    DescriptiveName,
    UserLogin,
    Uuid,
)
from atlas.schemas import (
    ScimGroup as AliasedScimGroup,
)
from atlas.services import DS
from atlas.structlog import StructLogService
from atlas.utils import generate_randstr
from beanie.odm.operators.find.comparison import In, NotIn
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version
from pydantic import Field, StrictStr

from agents.models import (
    ScimGroup,
    ScimGroupDB,
    ScimGroupExtensions,
    ScimReference,
    ScimUser,
    ScimUserDB,
)

router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "tags": ["Groups"],
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


class GroupsHierarchyPut(APIPostPut, DescriptiveName):
    """
    PUT representation of a Group Hierarchy

    Attributes:
        group_id (Uuid): UUID of the node (particular group) to edit
        parent (Uuid | None): UUID of the parent organisation
                       (if None, it unsets parents)
        children (list[Uuid] | None): List of children organisation
                                      part of the group (if None)
    """

    group_id: Uuid
    parent: Uuid | None = None
    children: list[Uuid] | None = None


class ScimGroupPost(APIPostPut, ScimGroup):
    """
    POST representation of a Scim group

    Attributes:
        schemas (list[str]): SCIM resource schema reference
        id (Uuid): Uuid of the SCIM resource
        meta (Meta): Descriptive metadata about the SCIM resource
        display_name (str): Display name of the group
        members (list[ScimReference]): List of members of the group,
                                       defaults to an empty list
        atlas_extensions (ScimGroupExtensions): Atlas extensions to Scim
    """


class ScimGroupPut(APIPostPut, ScimGroup):
    """
    PUT representation of a ScimGroup

    Attributes:
        schemas (list[str] | None): SCIM resource schema reference,
                                    defaults to None
        id (Uuid | str | None): ID of the SCIM resource, defaults to
                                None
        display_name (str | None): Display name of the group,
                                   defaults to None
        members (list[ScimReference]): List of members of the group,
                                       defaults to None
        atlas_extensions (
            ScimGroupExtensions | None
        ): Atlas extensions to Scim, defaults to None
    """

    display_name: str | None = None
    members: List[ScimReference] | None = None
    atlas_extensions: Annotated[
        ScimGroupExtensions | None,
        Field(
            None,
            validation_alias="urn:ietf:params:scim:schemas:extensions:atlas:2.0:Group",
        ),
    ]


class ScimGroupGet(APIGet, AliasedScimGroup):
    """
    GET representation of a Scim group

    Attributes:
        schemas (list[str]): SCIM resource schema reference
        id (Uuid): Uuid of the SCIM resource
        meta (Meta): Descriptive metadata about the SCIM resource
        display_name (str): Display name of the group
        members (list[ScimReference]): List of members of the group,
                                       defaults to an empty list
        atlas_extensions (ScimGroupExtensions): Atlas extensions to Scim
    """


class ScimGroupListResponse(APIGet):
    """
    GET representation of SCIM Group Get Response

    Attributes:
        schemas (list[StrictStr]): List of SCIM schemas
        total_results (int): Total number of results returned by the search
        start_index (int): The 1-based index of the first result
                           in the current set of search results
        items_per_page (int): The number of resources returned in
                              a results page
        resources (list[SCIMGroup]): List of SCIM Users from search
    """

    schemas: list[StrictStr]
    total_results: int
    start_index: int
    items_per_page: int
    resources: list[ScimGroupGet]


# TODO: Use messages from environment
@cbv(router)
class SCIMGroupsAPI:
    """
    Class-based view for representing the APIs for managing
    SCIM Groups

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
        self.scim_groups: DS = self.atlas.db.atlas_dataset(
            ScimGroupDB.Settings.name
        )
        self.scim_users: DS = self.atlas.users
        self.logger: StructLogService = self.atlas.logger

    @router.post(
        "/groups/",
        status_code=status.HTTP_201_CREATED,
        response_model=Dict[str, Any],
        include_in_schema=False,
    )
    @router.post(
        "/groups",
        status_code=status.HTTP_201_CREATED,
        response_model=Dict[str, Any],
        responses={
            status.HTTP_201_CREATED: {
                "description": "Successfully created SCIM Groups",
                "content": {"application/json": {"example": []}},
                "model": ScimGroupGet,
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    @api_version(1, 0)
    async def create_group(
        self,
        details: ScimGroupPost,
        include: str | None = Query(None, alias="attributes"),
        exclude: str | None = Query(None, alias="excluded_attributes"),
    ) -> JSONResponse:
        """
        Creates a new SCIM group

        Args:
            include (str | None): Attributes to be included,
                                  defaults to None
            exclude (str | None): Attributes to be excluded,
                                  defaults to None
            details (ScimGroupPost): Scim group details

        Returns:
            JSONResponse: FastAPI Response

        Raises:
            AtlasAPIException: If
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Validates group details
        await self.validate_group(details)

        # Create Scim Group and ensure version is included
        group: ScimGroupDB = ScimGroupDB.create_schema(
            user=self.user.id,
            resource_type=ScimGroupDB.Settings.name,
            location=str(self.environ.pub_url) + f"latest/groups/{details.id}",
            version=1,
            **details.model_dump(),
        )
        if group.meta.version is None:
            group.meta.version = 1

        # Insert Scim Group into database
        await logger.ainfo("Creating SCIM group", data=group.model_dump_json())
        if not await self.scim_groups.create_item(group):
            # TODO: Return a Scim Exception
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error creating chat",
                details=group.model_dump(exclude_unset=True, mode="json"),
            )
        await self.ref_group_in_user(
            [*group.members, *group.atlas_extensions.administrators], group
        )
        # Structure the response
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            media_type="application/scim+json",
            content=ScimGroupGet(**group.model_dump()).model_dump(
                mode="json", by_alias=True
            ),
        )

    @router.get(
        "/groups/",
        status_code=status.HTTP_200_OK,
        response_model=List[ScimGroupGet],
        include_in_schema=False,
    )
    @router.get(
        "/groups",
        status_code=status.HTTP_200_OK,
        response_model=List[ScimGroupGet],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved SCIM Groups",
                "content": {"application/json": {"example": []}},
                "model": List[ScimGroupGet],
            },
        },
    )
    @api_version(1, 0)
    async def get_groups(
        self,
    ) -> JSONResponse:
        """
        Retrieves multiple Scim groups with pagination

        Returns:
            JSONResponse: FastAPI Response
        """
        scim_groups: List[ScimGroupDB] = await self.scim_groups.get_items({})

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            media_type="application/scim+json",
            content=[
                ScimGroupGet(**g.model_dump()).model_dump(
                    mode="json", by_alias=True
                )
                for g in scim_groups
            ],
        )

    @router.put(
        "/groups/{group_id}/",
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
    )
    @router.put(
        "/groups/{group_id}",
        status_code=status.HTTP_200_OK,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def update_group(
        self, group_id: Uuid, details: ScimGroupPut
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

        # Check existence of Scim Group
        scim_group: ScimGroupDB = await self.__get_group(group_id)

        # Validate that the IDs provided match
        if details.id is not None and group_id != details.id:
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="IDs provided do not match",
                details=details.model_dump(exclude_unset=True, mode="json"),
            )

        # Generate version and updated SCIM group
        version: Union[str, int]
        if details.meta.version is not None:
            version = details.meta.version
        elif isinstance(scim_group.meta.version, int):
            version = scim_group.meta.version + 1
        else:
            version = generate_randstr()

        # Handle Atlas Extensions
        atlas_extensions: ScimGroupExtensions = scim_group.atlas_extensions
        if details.atlas_extensions:
            atlas_extensions = atlas_extensions.model_copy(
                update=details.atlas_extensions.model_dump(exclude_unset=True)
            )

        updated: ScimGroupDB = scim_group.update_schema(
            user=self.user.id,
            version=version,
            **{
                **details.model_dump(
                    exclude={"atlas_extensions"}, exclude_unset=True
                ),
                "atlas_extensions": atlas_extensions,
            },
        )

        # Validate Scim group membership details
        await self.validate_group(updated)

        # reference users that have not been added into a group
        await self.ref_group_in_user(
            [*scim_group.members, *scim_group.atlas_extensions.administrators],
            scim_group,
        )

        await logger.ainfo(
            f"Updating SCIM group {group_id}", data=updated.model_dump_json()
        )
        if not await self.scim_groups.replace_item(updated):
            # TODO: Return a Scim Exception
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Error updating Scim Group {group_id}",
                details=details.model_dump(exclude_unset=True, mode="json"),
            )

        # Structure the response
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            media_type="application/scim+json",
            content=ScimGroupGet(**updated.model_dump()).model_dump(
                mode="json", by_alias=True
            ),
        )

    @router.get(
        "/scim/v2/Groups/{group_id}/",
        status_code=status.HTTP_200_OK,
        response_model=Dict[str, Any],
        include_in_schema=False,
    )
    @router.get(
        "/scim/v2/Groups/{group_id}",
        status_code=status.HTTP_200_OK,
        response_model=Dict[str, Any],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully requested group",
                "content": {"application/json": {"example": {}}},
                "model": Dict[str, Any],
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_group(
        self,
        group_id: Union[Uuid, str],
        include: str | None = Query(None, alias="attributes"),
        exclude: str | None = Query(None, alias="excluded_attributes"),
    ) -> JSONResponse:
        """
        Retrieves a SCIM Group

        Args:
            group_id (Union[Uuid, str]): Group ID
            include (str | None): Attributes to be included,
                                  defaults to None
            exclude (str | None): Attributes to be excluded,
                                  defaults to None

        Returns:
            JSONResponse: FastAPI Response
        """
        scim_group: ScimGroupDB = await self.__get_group(group_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            media_type="application/scim+json",
            content=ScimGroupGet(**scim_group.model_dump()).model_dump(
                mode="json", by_alias=True
            ),
        )

    @router.delete(
        "/scim/v2/Groups/{group_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/scim/v2/Groups/{group_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("deleted_response"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def delete_group(
        self, group_id: Union[Uuid, str], response: Response
    ) -> Response:
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

        # Check existence of Scim Group
        scim_group: ScimGroupDB = await self.__get_group(group_id)

        # Deference group from the associated users
        # TODO: Simplify this with the $pull operator
        users_in_group: list[ScimUser] = await self.scim_users.get_items(
            In(ScimUserDB.groups.value, [group_id])
        )
        for user in users_in_group:
            new_list_of_groups: list[ScimReference] = [
                group for group in user.groups if group.value != group_id
            ]
            user.groups = new_list_of_groups
            user.update_schema(user=self.user.id)
            if not await self.scim_users.replace_item(user):
                # TODO: Change to SCIM Reference
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Error dereferencing group",
                    details={"group_id": group_id, "user_id": user.id},
                )

        # TODO: Remove backward references in hierarchy

        # Delete SCIM Group from the database
        scim_group.delete_schema(user=self.user.id)
        await logger.ainfo(f"Deleting SCIM group {group_id}")
        if not await self.scim_groups.replace_item(scim_group):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error deleting group",
                details={"id": group_id},
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    async def __get_group(self, group_id: Union[Uuid, str]) -> ScimGroupDB:
        """
        Checks if the group exists, if not raises an error

        Args:
            group_id (Union[Uuid, str]): Scim Group ID

        Returns:
            ScimGroupDB: Scim Group ID

        Raises:
            AtlasAPIException: If Scim Group does not exist
        """
        scim_group: ScimGroupDB | None = await self.scim_groups.get_item(
            ScimGroupDB.id == group_id,
            ScimGroupDB.meta.deleted == None,  # noqa: E711
        )
        if not scim_group:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Scim Group does not exist",
                details={"id": group_id},
            )
        return scim_group

    async def validate_group(
        self, group: Union[ScimGroupDB, ScimGroupPost]
    ) -> None:
        """
        Validates ScimReferences within incoming group for POST/PUT requests

        Args:
            group (
                Union[ScimGroupDB, ScimGroupPost]
            ): Group details to be validated

        Returns:
            None

        Raises:
            AtlasAPIException: If Scim reference in members do not exist
            AtlasAPIException: If Scim reference in parents do not exist
            AtlasAPIException: If Scim reference in children do not exist
            AtlasAPIException: If Scim reference in admins do not exist
        """
        members, atlas_extensions = (
            group.members,
            group.atlas_extensions,
        )
        if members:
            await self.validate_scim_reference(
                group, "members", members, self.scim_users
            )
        if atlas_extensions:
            parent, children, admins = (
                atlas_extensions.parent,
                atlas_extensions.children,
                atlas_extensions.administrators,
            )
            if parent:
                await self.validate_scim_reference(
                    group, "parent", [parent], self.scim_groups
                )
            if children:
                await self.validate_scim_reference(
                    group, "children", children, self.scim_groups
                )
            if admins:
                await self.validate_scim_reference(
                    group, "admins", admins, self.scim_users
                )

        # TODO: Add validation of default role

    async def ref_group_in_user(
        self,
        user_refs: List[ScimReference],
        group: Union[ScimGroupPost, ScimGroupPut],
    ) -> bool:
        # get all users that are added,
        # get those users who are not part of the group yet.
        users: List[ScimUserDB] = await self.scim_users.get_items(
            In(ScimUserDB.id, [ref.value for ref in user_refs]),
            NotIn(ScimUserDB.groups.value, [group.id]),
            ScimUserDB.meta.deleted == None,  # noqa: E711
        )
        # if not, add them group into members under "groups"
        group_ref: ScimReference = ScimReference(
            ref=str(self.environ.project.pub_url)
            + f"scim/v2/Groups/{group.id}",
            type="groups",
            value=group.id,
            display=group.display_name,
        )
        updated_users: List[ScimUserDB] = []
        for user in users:
            user.groups.append(group_ref)
            user.update_schema(user=self.user.id)
            updated_users.append(user)
        # update all users
        if not await self.scim_users.update_items(*updated_users):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error inserting users",
                details={"users": [u.model_dump() for u in updated_users]},
            )

    @staticmethod
    async def validate_scim_reference(
        group: Union[ScimGroupDB, ScimGroupPost],
        field: str,
        members: List[ScimReference],
        reference_col: DS,
    ) -> None:
        """
        Validates if each group member in the list of ScimReference
        exists using ID
        Args:
            group (
                Union[ScimGroupDB, ScimGroupPost, ScimGroupPut]
            ): Scim group details
            field (str): Field name being checked
            members (List[ScimReference]): List of members to be validated
            reference_col (DS): Reference dataset to be checked
        Raises:
            AtlasAPIException: If scim reference does not exist
        """
        group_members: List[
            reference_col.dataset
        ] = await reference_col.get_items(
            In(reference_col.dataset.id, [m.value for m in members])
        )
        if {g.id for g in group_members} != {m.value for m in members}:
            # TODO: Raise Scim Exception
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"ScimReferences in {field} do not exist",
                details=group.model_dump(exclude_unset=True, mode="json"),
            )
