from __future__ import annotations

from typing import Annotated, Any, Dict, List, Union

import structlog
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig, IDResponse
from atlas.environ import E
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import (
    DescriptiveName,
    UserLogin,
    Uuid,
)
from atlas.schemas import ScimGroup as AliasedScimGroup
from atlas.services import DS
from atlas.structlog import StructLogService
from beanie.odm.operators.find.comparison import In, NotIn
from fastapi import APIRouter, Depends, Response, status
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version
from pydantic import Field

from agents.app.api.logins.users import (
    UserBrief,
)

# TODO: Move to common library
from agents.models import (
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
    parent: Union[Uuid, None] = None
    children: Union[List[Uuid], None] = None


class ScimGroupPost(APIPostPut):
    """
    POST representation of a Scim group

    Attributes:
        display_name (str): Display name of the group
        members (list[ScimReference]): List of members of the group,
                                       defaults to an empty list
        atlas_extensions (ScimGroupExtensions): Atlas extensions to Scim
    """

    display_name: str
    members: list[ScimReference] = []
    atlas_extensions: Annotated[
        ScimGroupExtensions,
        Field(
            validation_alias="urn:ietf:params:scim:schemas:extensions:atlas:2.0:Group",
        ),
    ]


class ScimGroupPut(APIPostPut):
    """
    PUT representation of a ScimGroup

    Attributes:
        display_name (str | None): Display name of the group,
                                   defaults to None
        members (list[ScimReference]): List of members of the group,
                                       defaults to None
        atlas_extensions (
            ScimGroupExtensionsOptional | None
        ): Atlas extensions to Scim, defaults to None
    """

    display_name: Union[str, None] = None
    members: Union[List[ScimReference], None] = None
    atlas_extensions: Annotated[
        Union[ScimGroupExtensions, None],
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


class GroupParentPut(APIPostPut):
    """
    PUT schema for modifying a Group's parent details

    Attributes:
        parent (Uuid): Uuid of parent to set in group
    """

    parent: Uuid


class GroupChildrenPut(APIPostPut):
    """
    PUT schema for modifying a Group's children details

    Attributes:
        children (List[Uuid]): List of children group Uuid
    """

    children: List[Uuid]


@cbv(router)
class GroupsAPI:
    # TODO: Tidy up docstrings
    """
    Class-based view for representing the APIs for managing
    SCIM Groups

    Attributes
        user (UserLogin): Authenticated user details
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
        response_model=IDResponse,
        include_in_schema=False,
    )
    @router.post(
        "/groups",
        status_code=status.HTTP_201_CREATED,
        response_model=IDResponse,
        responses={
            **AtlasRouters.response("created_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    @api_version(1, 0)
    async def create_group(
        self,
        details: ScimGroupPost,
    ) -> Dict[str, str]:
        """
        Creates a new SCIM group

        Args:
            details (ScimGroupPost): Scim group details

        Returns:
            Dict[str, str]: Scim Group ID

        Raises:
            AtlasAPIException: Agency and Domain both None
            AtlasAPIException: Error creating group
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Validates group details
        await self.validate_group(details)

        # validate if agency and domain are both none, throw an error.
        # (Example given: DSAID is a child of GovTech but it does not
        #  have an agency name, we want to allow None for either domain
        #  or agency but not both) (21/06/2024, David)
        # TODO: decide whether or not to set none to empty stri
        detail_agency, detail_domain, detail_name = (
            details.atlas_extensions.agency,
            details.atlas_extensions.domain,
            details.display_name,
        )
        # Create Scim Group and ensure version is included
        group_id: Uuid = ScimGroupDB.atlas_get_uuid(
            agency=detail_agency, domain=detail_domain, name=detail_name
        )
        group: ScimGroupDB = ScimGroupDB.create_schema(
            user=self.user.id,
            uid=group_id,
            resource_type=ScimGroupDB.Settings.name,
            location=str(self.environ.pub_url) + f"groups/{group_id}",
            version=1,
            **details.model_dump(),
        )
        # if a parent is set for the group,
        # add it as a child of the parent group
        parent, children = (
            group.atlas_extensions.parent,
            group.atlas_extensions.children,
        )

        # Insert Scim Group into database
        await logger.ainfo("Creating SCIM group", data=group.model_dump_json())
        if not await self.scim_groups.create_item(group):
            # TODO: Return a Scim Exception
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error creating group",
                details=group.model_dump(exclude_unset=True, mode="json"),
            )
        if parent:
            await self.set_child_for_parent(group)
        # if a child is set for the group,
        # add it as a parent for the child group
        if children:
            await self.set_parent_for_child(group)

        await self.ref_group_in_user(
            [*group.members, *group.atlas_extensions.administrators], group
        )

        # TODO: Incorporate permissions creation

        # Structure the response
        return {"id": group.id}

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
    ) -> List[Dict[str, Any]]:
        """
        Retrieves multiple Scim groups

        Returns:
            list[dict[str, Any]]: Scim groups
        """
        # TODO: Incorporate permissions to read
        scim_groups: List[ScimGroupDB] = await self.scim_groups.get_items({})

        return [g.model_dump() for g in scim_groups]

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
        self, group_id: Uuid, details: ScimGroupPut, response: Response
    ) -> Response:
        # TODO: Update docstring
        """

        Args:
            group_id (Uuid): Uuid of group to update
            details (ScimGroupPut): details of group
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Check existence of Scim Group
        scim_group: ScimGroupDB = await self.__get_group(group_id)

        # Validate Scim group membership details
        await self.validate_group(details)
        # Generate version and updated SCIM group
        updated: ScimGroupDB = scim_group.update_schema(
            user=self.user.id,
            version=scim_group.meta.version + 1,
            **{
                **details.model_dump(
                    exclude={"atlas_extensions", "members"}, exclude_unset=True
                ),
                "atlas_extensions": ScimGroupExtensions(
                    **{
                        **scim_group.atlas_extensions.model_dump(
                            exclude_unset=True
                        ),
                        **details.atlas_extensions.model_dump(
                            exclude_unset=True
                        ),
                    }
                ),
                "members": details.members,
            },
        )

        # dereference groups from members that have
        #  not been set in incoming group details
        members_to_be_removed: set = {
            m.value for m in scim_group.members
        }.difference({m.value for m in details.members})
        old_members = [
            m for m in scim_group.members if m.value in members_to_be_removed
        ]
        # dereference groups from admins that have not
        #  been set in incoming group details
        admin_to_be_removed: set = {
            a.value for a in scim_group.atlas_extensions.administrators
        }.difference(
            {a.value for a in details.atlas_extensions.administrators}
        )
        old_admins = [
            a
            for a in details.atlas_extensions.administrators
            if a.value in admin_to_be_removed
        ]

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
        # dereferences users that are not in updated group
        await self.deref_group_in_user([*old_members, *old_admins], scim_group)
        # reference users that have not been added into a group
        await self.ref_group_in_user(
            [*details.members, *details.atlas_extensions.administrators],
            scim_group,
        )

        parent, children = (
            scim_group.atlas_extensions.parent,
            scim_group.atlas_extensions.children,
        )
        # if a parent is set for the group,
        #  add it as a child of the parent group
        if parent:
            await self.set_child_for_parent(scim_group)
        # if a child is set for the group,
        # add it as a parent for the child group
        if children:
            await self.set_parent_for_child(scim_group)

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get(
        "/groups/{group_id}/",
        status_code=status.HTTP_200_OK,
        response_model=ScimGroupGet,
        include_in_schema=False,
    )
    @router.get(
        "/groups/{group_id}",
        status_code=status.HTTP_200_OK,
        response_model=ScimGroupGet,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully requested group",
                "content": {"application/json": {"example": {}}},
                "model": ScimGroupGet,
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_group(
        self,
        group_id: Uuid,
    ) -> Dict[str, Any]:
        """
        Retrieves a SCIM Group

        Args:
            group_id (Uuid): Group ID

        Returns:
            dict[str, Any]: FastAPI Response
        """
        # TODO: Incorporate permissions to read
        return (await self.__get_group(group_id)).model_dump()

    @router.delete(
        "/groups/{group_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/groups/{group_id}",
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
        users_in_group: List[ScimUser] = await self.scim_users.get_items(
            In(ScimUserDB.groups.value, [group_id])
        )
        updated_users: List[ScimUserDB] = []
        for user in users_in_group:
            new_list_of_groups: List[ScimReference] = [
                group for group in user.groups if group.value != group_id
            ]
            user.groups = new_list_of_groups
            user.update_schema(user=self.user.id)
            updated_users.append(user)
        if not await self.scim_users.update_items(*updated_users):
            # TODO: Change to SCIM Reference
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error dereferencing group",
                details={"group_id": group_id, "user_id": user.id},
            )

        # if parent is not None, get parent and remove deleted group as child
        parent, children = (
            scim_group.atlas_extensions.parent,
            scim_group.atlas_extensions.children,
        )
        if parent:
            await self.unset_child_from_parent(group_id, parent)
        # if children is not None, get each child and set parent to None
        if children:
            await self.unset_parent_from_children(children)
        # Delete SCIM Group from the database
        scim_group.delete_schema(user=self.user.id)
        await logger.ainfo(f"Deleting SCIM group {group_id}")
        if not await self.scim_groups.replace_item(scim_group):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error deleting group",
                details={"id": group_id},
            )

        # TODO: Delete all permissions
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get(
        "/groups/{group_id}/members/",
        status_code=status.HTTP_200_OK,
        response_model=List[UserBrief],
        include_in_schema=False,
    )
    @router.get(
        "/groups/{group_id}/members",
        status_code=status.HTTP_200_OK,
        response_model=List[UserBrief],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved group members",
                "content": {"application/json": {"example": []}},
                "model": List[UserBrief],
            },
        },
    )
    @api_version(1, 0)
    async def get_group_members(self, group_id: Uuid) -> List[Dict[str, Any]]:
        """
        Gets the group members of an existing SCIM group

        Args:
            group_id (Uuid): SCIM group ID

        Returns:
            List[dict[str, Any]]: List of queried users
        Raises:
            AtlasAPIException: if group does not exists
        """
        scim_group: ScimGroupDB = await self.__get_group(group_id)
        member_refs: List[ScimReference] = scim_group.members
        # get members using refs
        members: List[ScimUserDB] = await self.scim_users.get_items(
            In(ScimUserDB.id, [m.value for m in member_refs])
        )
        # apply users to user brief
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
            for u in members
        ]

    @router.put(
        "/groups/{group_id}/children/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/groups/{group_id}/children",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @api_version(1, 0)
    async def update_group_children(
        self,
        group_id: str,
        group_children: GroupChildrenPut,
        response: Response,
    ) -> Response:
        """
         Updates the children of a group

        Args:
            group_id (Uuid): group ID
            group_children (GroupChildrenPut): Children to add to parent group
            response (Response): API Response
        Returns:
            Response
        Raises:
            AtlasAPIException: if group does not exists
            AtlasAPIException: if children do not exists
        """
        # check group's existence
        group: ScimGroupDB = await self.__get_group(group_id)
        if not group:
            AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Group does not exists",
                details={"group": group_id},
            )
        # get children, then check if the returned number of children
        # get children that are in the list of child groups,
        # and do not have group set as parent

        children_groups = await self.scim_groups.get_items(
            In(ScimGroupDB.id, group_children.children),
            ScimGroupDB.meta.deleted == None,  # noqa: E711
        )

        # is the same as input list
        mismatch: set = {c.id for c in children_groups}.difference(
            set(group_children.children)
        )

        # checks if there are any non-existent groups
        if len(mismatch) > 0:
            AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Groups do not exists",
                details={"groups": list(mismatch)},
            )
        # check for the difference in the current list of children
        # and incoming list of children
        to_be_removed: set = {
            c.value for c in group.atlas_extensions.children
        }.difference(set(group_children.children))

        # removes parent from children that are being unsetted
        parent_unset = [
            c
            for c in group.atlas_extensions.children
            if c.value in to_be_removed
        ]

        await self.unset_parent_from_children(parent_unset)

        # create child refs
        child_refs: List[ScimReference] = [
            ScimReference(
                ref=str(self.environ.project.pub_url) + f"groups/{c.id}",
                type="groups",
                value=c.id,
                display=c.display_name,
            )
            for c in children_groups
        ]

        # add child to group
        group.atlas_extensions.children = child_refs
        group.update_schema(user=self.user.id)
        if not await self.scim_groups.replace_item(group):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error setting parent for group",
                details={"group": group.id},
            )
        # adds group as parent for all child
        await self.set_parent_for_child(group)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.put(
        "/groups/{group_id}/parent/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/groups/{group_id}/parent",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def update_group_parent(
        self, group_id: str, group_parent: GroupParentPut, response: Response
    ) -> Response:
        """
        Updates the parent of a group

        Args:
            group_id (Uuid): SCIM group ID
            group_parent (GroupParentPut): Parent to add to group
            response (Response): API Response
        Raises:
            AtlasAPIException: if group does not exists
            AtlasAPIException: if parent does not exists
        """
        # TODO: test update parent group
        # check for parent's existence
        parent_group: ScimGroupDB = await self.__get_group(group_parent.parent)
        if not parent_group:
            AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Parent does not exists",
                details={"parent": group_parent.group_parent},
            )
        # check for group's existence
        group: ScimGroupDB = await self.__get_group(group_id)
        if not group:
            AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="group does not exists",
                details={"group": group_id},
            )
        # get previous parent if any
        curr_group_parent: ScimReference | None = group.atlas_extensions.parent

        if curr_group_parent:
            # unset child from parent if a former parent exists
            self.unset_child_from_parent(
                group_id=group.id, parent=curr_group_parent
            )
        # create parent group ref
        parent_ref: ScimReference = ScimReference(
            ref=str(self.environ.project.pub_url)
            + f"groups/{parent_group.id}",
            type="groups",
            value=parent_group.id,
            display=parent_group.display_name,
        )
        # sets parent for group
        group.atlas_extensions.parent = parent_ref
        # update group with set parent
        if not await self.scim_groups.replace_item(group):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error setting parent for group",
                details={"group": group.id, "parent": group_parent.parent},
            )
        # set group as child of parent group
        await self.set_child_for_parent(group)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    async def __get_group(self, group_id: Uuid) -> ScimGroupDB:
        """
        Checks if the group exists, if not raises an error

        Args:
            group_id (Uuid): Group ID

        Returns:
            ScimGroupDB: Group ID

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

    async def set_parent_for_child(
        self,
        group: ScimGroupDB,
    ) -> None:
        """
        set group as parent for children
          Args:
            group (ScimGroupDB): group to set as parent for children
          Raises:
            AtlasAPIException: If children do not exist
        """
        # validates if parent exists
        parent: ScimGroupDB = await self.__get_group(group.id)

        # create ref to parent group
        parent_ref: ScimReference = ScimReference(
            ref=str(self.environ.project.pub_url) + f"groups/{parent.id}",
            type="groups",
            value=parent.id,
            display=parent.display_name,
        )
        # get groups that are in children
        children: List[ScimGroupDB] = await self.scim_groups.get_items(
            In(
                ScimGroupDB.id,
                [c.value for c in group.atlas_extensions.children],
            )
        )

        updated: List[ScimGroupDB] = []
        # set updated children schema with parent
        for c in children:
            if not c.atlas_extensions.parent:
                c.atlas_extensions.parent = parent_ref
                c.update_schema(user=self.user.id)
                updated.append(c)
            else:
                # throws a conflict exception if user tries to se
                #  parent for group with existing parent
                raise AtlasAPIException(
                    status_code=status.HTTP_409_CONFLICT,
                    message="""There is a conflict error,
                      there is already a parent in group""",
                    details={"id": c.id},
                )
        # update children to have group as parent
        if not await self.scim_groups.update_items(*updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error setting parent",
                details={"groups": [g.model_dump() for g in children]},
            )

    async def set_child_for_parent(self, group: ScimGroupDB) -> None:
        """
        set child for parent
          Args:
            group (ScimGroupDB): group to set as child for parent
          Raises:
            AtlasAPIException: If parent do not exist
        """
        parent_id: str = group.atlas_extensions.parent.value
        # get parent group
        parent: ScimGroupDB = await self.__get_group(parent_id)
        child: ScimGroupDB = await self.__get_group(group.id)
        # create ref for child group
        child_ref: ScimReference = ScimReference(
            ref=str(self.environ.project.pub_url) + f"groups/{child.id}",
            type="groups",
            value=child.id,
            display=child.display_name,
        )
        # add child ref under parent
        parent.atlas_extensions.children.append(child_ref)
        parent.update_schema(user=self.user.id)
        if not await self.scim_groups.replace_item(parent):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error setting child for parent",
                details={"parent": parent_id},
            )

    async def unset_child_from_parent(
        self, group_id: Uuid, parent: ScimReference
    ) -> None:
        """Removes the current group from its
        parent's children list when being deleted
        Args:
          group_id (Uuid): Uuid of group to be removed
          parent (ScimReference): reference for parent
        Raises:
          AtlasAPIException: If parent does not exist
        """
        # TODO: test this code in postman
        # get parent group
        group: ScimGroupDB = await self.__get_group(parent.value)
        # get new list of students
        new_children: List[ScimReference] = [
            g for g in group.atlas_extensions.children if g.value != group_id
        ]
        # set new list of children
        group.atlas_extensions.children = new_children
        # updates new schema
        updated = group.update_schema(user=self.user.id)
        # replace old parent with new parent, new set of children
        if not await self.scim_groups.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error unsetting child",
                details={"id": parent.value},
            )

    async def unset_parent_from_children(
        self, children: List[ScimReference]
    ) -> None:
        """Removes parent from children element
        Args:
          children (List[ScimReference]): List of children to unset parent
        Raises:
          AtlasAPIException: If parent does not exist
        """
        # gets all children of the group
        child_groups: List[ScimGroupDB] = await self.scim_groups.get_items(
            In(ScimGroupDB.id, [c.value for c in children])
        )
        updated: List[ScimGroupDB] = []
        # if the counts do not match, one of the children does not exist
        if len(child_groups) != len(children):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error with getting child groups",
                details={"groups": [c.value for c in children]},
            )
        # updates schema by unsetting
        for group in child_groups:
            group.atlas_extensions.parent = None
            group.update_schema(user=self.user.id)
            updated.append(group)
        # bulk update
        if not await self.scim_groups.update_items(*updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error unsetting child",
                details={"groups": [g.model_dump() for g in children]},
            )

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
        group: ScimGroupDB,
    ) -> None:
        """Adds group to members
        Args:
          user_refs (List[ScimReference]): List of user
            references to add group to
          group (ScimGroupDB): Group to be added to the user
        Raises:
          AtlasAPIException: If parent does not exist
        """
        # get all users that are added,
        # get those users who are not part of the group yet.
        users: List[ScimUserDB] = await self.scim_users.get_items(
            In(ScimUserDB.id, [ref.value for ref in user_refs]),
            NotIn(ScimUserDB.groups.value, [group.id]),
            ScimUserDB.meta.deleted == None,  # noqa: E711
        )

        # if not, add them group into members under "groups"
        group_ref: ScimReference = ScimReference(
            ref=str(self.environ.project.pub_url) + f"groups/{group.id}",
            type="groups",
            value=group.id,
            display=group.display_name,
        )

        updated_users: List[ScimUserDB] = []
        for user in users:
            user.groups.append(group_ref)
            updated_users.append(user)

        # update all users
        if not await self.scim_users.update_items(*updated_users):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error inserting users",
                details={"users": [u.model_dump() for u in updated_users]},
            )

    async def deref_group_in_user(
        self,
        user_refs: List[ScimReference],
        group: ScimGroupDB,
    ) -> None:
        """remove group from members
        Args:
          user_refs (List[ScimReference]): List of user
            references to remove group from
          group (ScimGroupDB): Group to be removed from the user
        Raises:
          AtlasAPIException: If user does not exist
        """
        # get all users that are to be removed,
        # get those users who have group to be removed.
        users: List[ScimUserDB] = await self.scim_users.get_items(
            In(ScimUserDB.id, [ref.value for ref in user_refs]),
            In(ScimUserDB.groups.value, [group.id]),
            ScimUserDB.meta.deleted == None,  # noqa: E711
        )

        updated_users: List[ScimUserDB] = []
        for user in users:
            # set new list of group references
            new_group_refs: List[ScimReference] = [
                g for g in user.groups if g.value != group.id
            ]
            user.groups = new_group_refs
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
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"ScimReferences in {field} do not exist",
                details=group.model_dump(exclude_unset=True, mode="json"),
            )
