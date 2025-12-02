from __future__ import annotations

from typing import Any, Dict, List, Union

import structlog
from atlas.asgi.exceptions import (
    AtlasAPIException,
    AtlasPermissionsException,
)
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import Permissions, PermissionsType, UserLogin, Uuid
from atlas.services import DS
from beanie.odm.operators.find.comparison import In
from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from pydantic import Field

from agents.mixins.uam import PermissionsAPIMixin
from agents.models import PermissionsDB, ScimGroupDB

__all__ = ("router",)


router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "tags": ["Access Controls"],
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


class PermissionsPut(APIPostPut):
    """
    PUT request for updating Item Permissions

    Attributes:
        scopes (list[str]): List of scopes, defaults to an
                            empty list
        groups (list[Uuid]): Relevant groups associated with
                             permission set to get additional
                             permissions from
    """

    scopes: List[str] | None = None
    groups: List[Uuid] | None = None


class PermissionsGet(APIGet, Permissions):
    """
    Consolidates all user, group, API Key and Public
    permissions

    Attributes:
        type (PermissionsType): Type of the permission set
        scopes (list[str]): List of scopes, defaults to an
                            empty list
        item (Uuid | str | None): ID of the item, defaults to
                                  None
        groups (list[Uuid]): Relevant groups associated with
                             permission set to get additional
                             permissions from
    """

    id: Any = Field(None, exclude=True)


# TODO: Move this to an Atlas dependency
def auth_superuser(
    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    ),
) -> UserLogin:
    """
    Only grants access to superusers

    Args:
        user (UserLogin): User login details

    Returns:
        UserLogin: Superuser login details
    """

    # Only allow superusers to access this endpoint
    if not user.superuser:
        raise AtlasPermissionsException(
            message="This endpoint is only accessible to superusers",
            user=user.id,
        )
    return user


# TODO: Move these messages to Atlas Christis Environment Variables
@cbv(router)
class PermissionsAPI(PermissionsAPIMixin):
    """
    Class-based view for representing the APIs for managing
    permissions

    Attributes:
        user (UserLogin): User login details
        atlas (AtlasASGIConfig): Atlas application config
        logger (StructLogService): Logging service
        permissions (DS): Permissions dataset
        groups (DS): Groups dataset
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    def __init__(self):
        super().__init__()
        self.groups: DS = self.atlas.db.atlas_dataset(
            ScimGroupDB.Settings.name
        )

    @router.put(
        "/permissions/all/",
        status_code=status.HTTP_200_OK,
        response_model=PermissionsGet,
        include_in_schema=False,
    )
    @router.put(
        "/permissions/all",
        status_code=status.HTTP_200_OK,
        response_model=PermissionsGet,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved an item permission set",
                "content": {"application/json": {"example": {}}},
                "model": PermissionsGet,
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def update_all_permissions(
        self,
        permissions_details: PermissionsPut,
    ) -> Dict[str, Any]:
        """
        Updates a specified item permissions set

        Args:
            permissions_details (PermissionsPut): Item permissions details

        Returns:
            Dict[str, Any]: Retrieved Item Permissions set
        """

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        permissions: PermissionsDB = await self.atlas_get_permission(
            "*", PermissionsType.all
        )

        # TODO: Ensure that it is a valid scope collection

        # Check that the associated Groups exist
        groups: List[ScimGroupDB] = await self.groups.get_items(
            In(ScimGroupDB.id, permissions_details.groups)
        )
        if not len(permissions_details.groups) == len(groups):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Some of the specified groups do not exist",
                details=permissions_details.model_dump(mode="json"),
            )

        updated: PermissionsDB = permissions.model_copy(
            update=permissions_details.model_dump(exclude_none=True)
        )

        await logger.ainfo(
            "Updating item permissions set", data=updated.model_dump_json()
        )
        if not await self.permissions.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error occurred when updating Item Permissions Set",
            )

        return permissions.model_dump(exclude={"id"})

    @router.get(
        "/permissions/all/",
        status_code=status.HTTP_200_OK,
        response_model=PermissionsGet,
        include_in_schema=False,
    )
    @router.get(
        "/permissions/all",
        status_code=status.HTTP_200_OK,
        response_model=PermissionsGet,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved an item permission set",
                "content": {"application/json": {"example": {}}},
                "model": PermissionsGet,
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def get_all_permissions(
        self,
    ) -> Dict[str, Any]:
        """
        Retrieves specified item permissions set

        Returns:
            Dict[str, Any]: Retrieved Item Permissions set
        """

        permissions: PermissionsDB = await self.atlas_get_permission(
            "*", PermissionsType.all
        )
        return permissions.model_dump()

    @router.put(
        "/permissions/{item_type}/{item_id}/",
        status_code=status.HTTP_200_OK,
        response_model=PermissionsGet,
        include_in_schema=False,
    )
    @router.put(
        "/permissions/{item_type}/{item_id}",
        status_code=status.HTTP_200_OK,
        response_model=PermissionsGet,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved an item permission set",
                "content": {"application/json": {"example": {}}},
                "model": PermissionsGet,
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def update_permissions(
        self,
        item_type: PermissionsType,
        permissions_details: PermissionsPut,
        item_id: Union[Uuid, str, None] = None,
    ) -> Dict[str, Any]:
        """
        Updates a specified item permissions set

        Args:
            item_type (PermissionsType): Item type
            permissions_details (PermissionsPut): Item permissions details
            item_id (Union[Uuid, str, None]): Item ID

        Returns:
            Dict[str, Any]: Retrieved Item Permissions set
        """

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        permissions: PermissionsDB = await self.atlas_get_permission(
            item_id, item_type
        )

        # TODO: Ensure that it is a valid scope collection

        # Check that the associated Groups exist
        groups: List[ScimGroupDB] = await self.groups.get_items(
            In(ScimGroupDB.id, permissions_details.groups)
        )
        if not len(permissions_details.groups) == len(groups):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Some of the specified groups do not exist",
                details=permissions_details.model_dump(mode="json"),
            )

        updated: PermissionsDB = permissions.model_copy(
            update=permissions_details.model_dump(exclude_none=True)
        )

        await logger.ainfo(
            "Updating item permissions set", data=updated.model_dump_json()
        )
        if not await self.permissions.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error occurred when updating Item Permissions Set",
            )

        return permissions.model_dump(exclude={"id"})

    @router.get(
        "/permissions/{item_type}/{item_id}/",
        status_code=status.HTTP_200_OK,
        response_model=PermissionsGet,
        include_in_schema=False,
    )
    @router.get(
        "/permissions/{item_type}/{item_id}",
        status_code=status.HTTP_200_OK,
        response_model=PermissionsGet,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved an item permission set",
                "content": {"application/json": {"example": {}}},
                "model": PermissionsGet,
            },
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def get_permissions(
        self,
        item_type: PermissionsType,
        item_id: Union[Uuid, str, None] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves specified item permissions set

        Args:
            item_type (PermissionsType): Item type
            item_id (Union[Uuid, str, None]): Item ID

        Returns:
            Dict[str, Any]: Retrieved Item Permissions set
        """

        permissions: PermissionsDB = await self.atlas_get_permission(
            item_id, item_type
        )

        return permissions.model_dump()
