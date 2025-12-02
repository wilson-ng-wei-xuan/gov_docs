from __future__ import annotations

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from typing import Any, Dict, List, Optional, Union

from atlas.asgi.schemas import APIPostPut, AtlasASGIConfig
from atlas.environ import E
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import (
    AccessRoleType,
    Ownership,
    OwnershipOptional,
    Permissions,
    UserLogin,
    Uuid,
)
from atlas.services import DS, S
from fastapi import APIRouter, Depends, Response, status
from fastapi_utils.cbv import cbv
from pydantic import Field

from agents.models import (
    PermissionsDB,
)

__doc__ = """
Contains all the API calls for the agents API

Attributes:
    router (APIRouter): agents API Router
"""


__all__ = ("router",)


router: APIRouter = AtlasRouters.atlas_get_router(
    prefix="",
    tags=["Access Controls"],
    dependencies=[
        Depends(AtlasDependencies.get_registry_item("reject_api_key"))
    ],
    responses={
        **AtlasRouters.response("401_authentication_error"),
        **AtlasRouters.response("403_permissions_error"),
        **AtlasRouters.response("500_internal_server_error"),
    },
)


class AuthorisationControlsPut(APIPostPut, OwnershipOptional):
    """
    Generic description of Ownership details of a Resource used for
    updating the ownership details

    Attributes:
        curr (Ownership): Current ownership details
        new (Ownership): New ownership details
        product_version (Optional[str]): Product version information,
                                         defaults to None
        ownership_resource (Optional[str]): Ownership resource details,
                                            defaults to None
        augment_allow (
            Optional[Dict[Union[AccessRoleType, str], List[str]]]
        ): Additional scopes to augment the allowed functionality,
           defaults to None
    """

    curr: Ownership
    new: Ownership
    product_version: Annotated[
        Optional[str], Field(None, alias="productVersion")
    ]
    ownership_resource: Annotated[
        Optional[str], Field(None, alias="ownershipResource")
    ]
    augment_allow: Annotated[
        Optional[Dict[Union[AccessRoleType, str], List[str]]],
        Field(None, alias="augmentAllow"),
    ]


@cbv(router)
class ControlsAPI:
    """
    Class-based view for representing the User Access Controls API

    Attributes:
        user (UserLogin): Authenticated user details
        atlas (AtlasASGIConfig): Atlas ASGI Config
        environ (AIBotsAgentEnviron): User Environment
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    def __init__(self):
        self.environ: E = self.atlas.environ
        self.logger: S = self.atlas.logger
        self.permissions: DS = self.atlas.db.atlas_dataset(
            PermissionsDB.Settings.name
        )

    async def delete_permissions(
        self, delete: List[Permissions], item_id: Uuid, logger: Any = None
    ) -> List[PermissionsDB]:
        """
        Functionality to delete permissions

        Args:
            delete (list[Permissions]: Permissions to be deleted
            item_id (Uuid): ID of the Agent
            logger (Any): Logger for logging details

        Returns:
            list[PermissionsDB]: Deleted permissions

        Raises:
            AtlasAPIException: Error deleting permissions
        """
        # Remove delete scopes from permissions
        p_delete: List[PermissionsDB] = await self.permissions.get_items(
            *(PermissionsDB.item == d.item for d in delete)
        )
        p_dict: Dict[str, Permissions] = {p.item: p for p in delete}
        for p in p_delete:
            if p.item not in p_dict:
                continue
            p.scopes = [s for s in p.scopes if s not in p_dict[p.item].scopes]
        if logger:
            await logger.ainfo(
                f"Deleting permissions for item {item_id}",
                data=[p.model_dump(mode="json") for p in p_delete],
            )
        return p_delete

    async def add_permissions(
        self, add: List[Permissions], item_id: Uuid, logger: Any = None
    ) -> List[PermissionsDB]:
        """
        Functionality to add permissions

        Args:
            add (list[Permissions]: Permissions to be added
            item_id (Uuid): ID of the Item
            logger (Any): Logger for logging details

        Returns:
            list[PermissionsDB]: Added permissions

        Raises:
            AtlasAPIException: Error adding permissions
        """
        p_add: List[PermissionsDB] = await self.permissions.get_items(
            *(PermissionsDB.item == d.item for d in add)
        )
        p_dict: dict[str, Permissions] = {p.item: p for p in add}
        for a in p_add:
            if a.item not in p_dict:
                continue
            a.scopes += p_dict[a.item].scopes
        if logger:
            await logger.ainfo(
                f"Adding permissions for {item_id}",
                data=[p.model_dump(mode="json") for p in p_add],
            )
        return p_add

    @router.put(
        "/controls/authorizations/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/controls/authorizations",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def update_authorization(
        self, details: AuthorisationControlsPut, response: Response
    ) -> Response:
        """
        Updates authorization controls

        Args:
            details (AuthorisationControlsPut): Ownership details of the Agent
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If the Agent does not exist
        """

        # logger: structlog.typing.FilteringBoundLogger = (
        #     self.logger.get_structlog_logger(
        #       self.atlas.environ.loggers["api"]
        #     )
        # )
        #
        # delete: list[Permissions]
        # add: list[Permissions]
        #
        # # Generating changes between current and new ownership details
        # new_ownership: Ownership = Ownership(
        #     resource_key=agent.ownership.resource_key, **details.model_dump()
        # )
        # delete, add = agent.compare_ownership(
        #     new_ownership,
        #     ownership_resource="agents.authorizations",
        #     augment_allow=[
        #         "chats.{}:create,read,update,delete",
        #         "messages.{}:create,read,update,delete",
        #         "rags.{}:create,read,update,delete",
        #     ],
        # )
        #
        # # Remove delete scopes from permissions
        # await self.delete_permissions(delete, agent.id, logger)
        #
        # # Insert add scopes to permissions
        # await self.add_permissions(add, agent.id, logger)
        #
        # response.status_code = status.HTTP_204_NO_CONTENT
        # return response
