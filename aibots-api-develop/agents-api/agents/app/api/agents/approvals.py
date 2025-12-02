from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import structlog
from aibots.models import AgentReleaseState, Comment, DeploymentState
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import (
    Ownership,
    Permissions,
    UserLogin,
    Uuid,
    VisibilityLevel,
)
from atlas.utils import generate_curr_datetime
from beanie.odm.operators.find.logical import And, Or
from beanie.operators import In
from fastapi import APIRouter, Body, Depends, Query, Response, status
from fastapi_utils.cbv import cbv
from pydantic import AnyUrl

from agents.mixins.uam import PermissionsAPIMixin
from agents.models import AgentDB, PermissionsDB

from .base import AgentsAPIMixin

__doc__ = """
Contains all the API calls for the Agents API

Attributes:
    router (APIRouter): agents API Router
"""

__all__ = ("router",)

router: APIRouter = AtlasRouters.atlas_get_router(
    prefix="",
    tags=["Agents"],
    dependencies=[
        Depends(AtlasDependencies.get_registry_item("reject_api_key"))
    ],
    responses={
        **AtlasRouters.response("401_authentication_error"),
        **AtlasRouters.response("403_permissions_error"),
        **AtlasRouters.response("500_internal_server_error"),
    },
)


class AgentApprovalGet(APIGet):
    """
    GET representation of an agent approval

    Attributes:
        id (Uuid): UUID string
        name (constr): Name of the Agent
        description (constr): Brief description of the Agent
        agency (str): Agency associated with the Agent
        location (AnyUrl): Location of the Agent
        created (datetime | None): Creation timestamp of the
                                   Agent Approval request,
                                   defaults to None
        last_modified (datetime | None): Last modified timestamp of the
                                         Agent Approval request,
                                         defaults to None
        last_modified_user (Uuid | str | None): Last modified user of the
                                                Agent Approval request,
                                                defaults to None
        owner (Uuid | str): ID of the owner
        denied (bool | None): Indicates if the Agent Approval request has
                              been denied, defaults to None
        comments (list[Comment]): List of comments, defaults to an empty
                                  list
    """  # noqa: E501

    id: Uuid
    name: str
    description: str
    agency: str
    location: AnyUrl
    created: datetime | None = None
    last_modified: datetime | None = None
    last_modified_user: Uuid | str | None = None
    denied: bool | None = None
    owner: Uuid | str
    comments: list[Comment] = []


class AgentApprovalPost(APIPostPut):
    """
    Put representation of an agent approval

    Attributes:
        comments (list[Comment]) Comment Details, defaults to an empty list
    """

    comments: list[Comment] = []


@cbv(router)
class AgentApprovalsAPI(PermissionsAPIMixin, AgentsAPIMixin):
    """
    Class for handling Agent Approval APIs

    Attributes:
        atlas (AtlasASGIConfig): Atlas API config
        environ (AppraiserEnviron): Environment variables
        db (BeanieService): MongoDB Service
        s3 (S3Service): S3 Service
        cf (CloudfrontService): Cloudfront Service
        files (DS): Files dataset
        logger (StructLogService): Atlas logger
        messages (SimpleNamespace): Agent and Knowledge Base messages
        knowledge_bases (BeanieDataset): Knowledge Base Dataset
        agents (BeanieDataset): Agent Dataset
        rag (Service): RAG engines
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    @router.get(
        "/agents/approvals/",
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
        response_model=list[AgentApprovalGet],
    )
    @router.get(
        "/agents/approvals",
        status_code=status.HTTP_200_OK,
        response_model=list[AgentApprovalGet],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved Agent Approvals",
                "content": {"application/json": {"example": []}},
                "model": list[AgentApprovalGet],
            }
        },
    )
    async def get_agents_approval(
        self,
        ids: list[Uuid] = Query([]),
        pending: bool = Query(True),
        rejected: bool = Query(True),
        approved: bool = Query(True),
    ) -> list[dict[str, Any]]:
        """
        Retrieves all agents visible to the user

        Args:
            ids (list[Uuid]): List of IDs
            pending (bool): Indicates that all Agents with pending
                            states will be returned, defaults to
                            True
            rejected (bool): Indicates that all Agents that have
                             been rejected will be returned, defaults
                             to True
            approved (bool): Indicates that all Agents with approved
                             states will be returned, defaults to True

        Returns:
            list[dict[str, Any]]: Collection of Agent Approvals
        """

        # Handle query filters
        query_filters: list[Any] = []
        state_filters: list[Any] = []
        if pending:
            state_filters.append(
                AgentDB.release_state.state == DeploymentState.pending
            )
        if approved:
            state_filters.append(
                AgentDB.release_state.state == DeploymentState.production
            )
        if rejected:
            state_filters.append(AgentDB.release_state.denied == True)  # noqa: E712

        query_filters.append(Or(*state_filters))
        if ids:
            query_filters.append(In(AgentDB.id, ids))

        return [
            {
                "location": i.meta.location,
                "owner": i.meta.owner,
                **i.release_state.model_dump(),
                **i.model_dump(
                    include={"id", "name", "description", "agency"}
                ),
            }
            for i in await self.agents.get_items(
                And(*query_filters), sort=[(AgentDB.release_state.created, -1)]
            )
        ]

    @router.post(
        "/agents/approvals/{agent_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.post(
        "/agents/approvals/{agent_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def create_agent_approval(
        self,
        agent_id: str,
        response: Response,
    ) -> Response:
        """
        Creates a new agent Approval

        Args:
            agent_id (Uuid): ID of the Agent seeking approval
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        # TODO: Restrict access to those who are owners and admins

        # Retrieve existing agent
        agent: AgentDB = await self.atlas_get_agent(agent_id)

        # Update the Agent's release state
        update: AgentDB = agent.update_schema(
            user=self.user.id,
            version=agent.meta.version + 1,
            **{
                "release_state": AgentReleaseState(
                    **{
                        "created": generate_curr_datetime(),
                        "state": DeploymentState.pending,
                        "last_modified": generate_curr_datetime(),
                        "last_modified_user": self.user.id,
                        "denied": None,
                        "comments": agent.release_state.comments,
                    }
                )
            },
        )

        # Update database
        await logger.ainfo(
            self.messages.api_agents_approval_create_fmt.format(agent.id),
            data=update.model_dump_json(),
        )
        if not await self.agents.replace_item(update):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_update_error_msg,
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.post(
        "/agents/approvals/{agent_id}/approves/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.post(
        "/agents/approvals/{agent_id}/approves",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def approve_agent(
        self,
        agent_id: str,
        response: Response,
        approval_details: AgentApprovalPost = Body(AgentApprovalPost()),
    ) -> Response:
        """
        Updates an existing Agent's Release State

        Args:
            agent_id (str): ID of the agent
            response (Response): FastAPI Response
            approval_details (AgentApprovalPost): Approval details

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If agent does not exist
        """
        # Perform validation on the agent's configuration
        # 1. Check that the AI Configuration is valid

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        # TODO: Restrict access to superusers and certain roles

        # Retrieve existing agent
        agent: AgentDB = await self.atlas_get_agent(agent_id)

        # Only allow approvals of:
        #   1. Pending Agents
        #   2. Agents previously rejected
        if not (
            agent.release_state.state == DeploymentState.pending
            or (
                agent.release_state.state != DeploymentState.pending
                and agent.release_state.denied is True
            )
        ):
            raise AtlasAPIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=self.messages.api_agents_approval_invalid_state_error_msg,
                details={
                    "id": agent.id,
                    **approval_details.model_dump(
                        mode="json", exclude_unset=True
                    ),
                },
            )

        # Merge configuration
        update: AgentDB = agent.update_schema(
            user=self.user.id,
            version=agent.meta.version + 1,
            **{
                "release_state": AgentReleaseState(
                    **{
                        "created": agent.release_state.created,
                        "state": DeploymentState.production,
                        "last_modified": generate_curr_datetime(),
                        "last_modified_user": self.user.id,
                        "denied": False,
                        "comments": agent.release_state.comments
                        + approval_details.comments,
                    }
                )
            },
        )

        # Insert into Database
        await logger.ainfo(
            self.messages.api_agents_approval_grant_fmt.format(agent.id),
            data=update.model_dump_json(),
        )
        if not await self.agents.replace_item(update):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_update_error_msg,
                details=approval_details.model_dump(
                    mode="json", exclude_unset=True
                ),
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.post(
        "/agents/approvals/{agent_id}/rejects/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.post(
        "/agents/approvals/{agent_id}/rejects",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def reject_agent(
        self,
        agent_id: str,
        response: Response,
        approval_details: AgentApprovalPost = Body(AgentApprovalPost()),
    ) -> Response:
        """
        Updates an existing Agent's Release State

        Args:
            agent_id (str): ID of the agent
            response (Response): FastAPI Response
            approval_details (AgentApprovalPost): Approval details

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If agent does not exist
        """
        # Perform validation on the agent's configuration
        # 1. Check that the AI Configuration is valid

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        # TODO: Restrict access to superusers and certain roles

        # Retrieve existing agent
        agent: AgentDB = await self.atlas_get_agent(agent_id)

        # Only allow rejection of
        #   1. Pending Agents
        #   2. Previously approved Agents
        if agent.release_state.state not in [
            DeploymentState.pending,
            DeploymentState.production,
        ]:
            raise AtlasAPIException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=self.messages.api_agents_approval_invalid_state_error_msg,
                details={
                    "id": agent.id,
                    **approval_details.model_dump(
                        mode="json", exclude_unset=True
                    ),
                },
            )

        # Downgrade the visibility back to private, updating permissions
        ownership: Ownership = agent.ownership
        to_update: list[PermissionsDB] = []
        if agent.ownership.visibility in [
            VisibilityLevel.wog,
            VisibilityLevel.public,
        ]:
            delete: list[Permissions]
            add: list[Permissions]

            ownership = agent.ownership.model_copy(
                update={"visibility": VisibilityLevel.private}
            )
            delete, add = agent.compare_ownership(
                agent.ownership,
                ownership,
                ownership_resource=self.ownership_resource,
                augment_allow=self.augment_allow,
            )
            to_update = await self.atlas_consolidate_permissions(delete, add)

        # Merge configuration
        updated: AgentDB = agent.update_schema(
            user=self.user.id,
            version=agent.meta.version + 1,
            **{
                "ownership": ownership,
                "release_state": AgentReleaseState(
                    **{
                        "created": agent.release_state.created,
                        "state": DeploymentState.beta,
                        "last_modified": generate_curr_datetime(),
                        "last_modified_user": self.user.id,
                        "denied": True,
                        "comments": agent.release_state.comments
                        + approval_details.comments,
                    }
                ),
            },
        )

        # Insert into Database
        await logger.ainfo(
            self.messages.api_agents_approval_reject_fmt.format(agent.id),
            data=updated.model_dump_json(),
        )
        if not await self.agents.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_update_error_msg,
                details=approval_details.model_dump(
                    mode="json", exclude_unset=True
                ),
            )

        # Update permissions
        if to_update:
            await logger.ainfo(
                self.messages.api_agents_permissions_updating_fmt.format(
                    agent_id
                ),
                data=json.dumps(
                    [p.model_dump(mode="json") for p in to_update]
                ),
            )
            if not await self.permissions.update_items(*to_update):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=self.messages.api_agents_update_error_msg,
                )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response
