from __future__ import annotations

import json
from typing import Any

import structlog
from aibots.models import KnowledgeBase
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, AtlasASGIConfig
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import UserLogin, Uuid
from beanie.operators import In
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi_utils.cbv import cbv

from agents.models import AgentDB, KnowledgeBaseDB, RAGConfigDB

from .base import AgentsAPIMixin, DataSourcePost

__doc__ = """
Contains all the API calls for the KnowledgeBases API

Attributes:
    router (APIRouter): KnowledgeBases API Router
"""

__all__ = ("router",)

router: APIRouter = AtlasRouters.atlas_get_router(
    prefix="",
    tags=["Agents"],
    dependencies=[
        Depends(AtlasDependencies.get_registry_item("reject_api_key"))
    ],
)


class KnowledgeBaseGet(APIGet, KnowledgeBase):
    """
    GET representation of a KnowledgeBase

    Attributes:
        id (Uuid): ID of the Knowledge Base.
        name (str): Name of the Data Source
        description (str): Brief description of the Data Source
        type (DataSourceType): Types of supported data sources
        content (Uuid | AnyUrl | str | None): Data content, defaults
                                              to None
        metadata (dict[str, Any]): Additional metadata to be appended
                                   together with the Data Source,
                                   defaults to an empty dictionary
        agent (Uuid | None): ID of associated Agent, defaults to None
        storage (KnowledgeBaseStorage): References to the storage locations
                                        of the actual files.
        embeddings (
            dict[str, EmbeddingsMetadata]
        ): Embeddings and associated data generated during the
           embeddings process, defaults to an empty dictionary
        timestamp (datetime): Timestamp the Knowledge Base was created,
                              defaults to the current datetime
    """


# TODO: Restrict Agents to those with permissions granted
@cbv(router)
class KnowledgeBasesAPI(AgentsAPIMixin):
    """
    Class-based view for representing the KnowledgeBases API

    Attributes:
        user (UserLogin): Authenticated user details
        atlas (AtlasASGIConfig): Atlas Config class
        environ (AIBotsAgentEnviron): Environment variables
        messages (M): Message class
        db (BeanieService): MongoDB Service
        knowledge_bases (BeanieDataset): knowledge_bases Dataset
        agents (BeanieDataset): agents Dataset
        logger (StructLogService): Logging Service
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    @router.post(
        "/agents/{agent_id}/knowledge/bases/",
        response_model=list[KnowledgeBaseGet],
        status_code=status.HTTP_201_CREATED,
        include_in_schema=False,
    )
    @router.post(
        "/agents/{agent_id}/knowledge/bases",
        response_model=list[KnowledgeBaseGet],
        status_code=status.HTTP_201_CREATED,
        responses={
            **AtlasRouters.response("created_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    async def create_knowledge_base(
        self,
        agent_id: Uuid,
        details: list[DataSourcePost],
    ) -> list[dict[str, Any]]:
        """
        Creates new Knowledge Bases

        Args:
            agent_id (Uuid): ID of the Agent
            details (
                list[KnowledgeBasePost]
            ): Details for creating knowledge bases

        Returns:
            list[dict[str, Any]]: Generated Knowledge Bases
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        agent: AgentDB = await self.atlas_get_agent(agent_id)

        # Validate files
        try:
            await self.atlas_validate_knowledge_bases(details)
        except AtlasAPIException as e:
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=e.message,
                details=e.details,
            ) from e

        # Generate knowledge bases
        knowledge_bases: list[
            KnowledgeBaseDB
        ] = self.atlas_create_knowledge_base(details, agent.id)

        # Insert into Database
        await logger.ainfo(
            self.messages.api_knowledge_bases_create_fmt.format(
                [kb for kb in knowledge_bases]  # noqa: C416
            ),
            data=json.dumps(
                [kb.model_dump(mode="json") for kb in knowledge_bases]
            ),
        )
        if not await self.knowledge_bases.create_items(knowledge_bases):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_knowledge_bases_create_error_msg,
                details={
                    "knowledge_bases": [
                        kb.model_dump(mode="json", exclude_unset=True)
                        for kb in details
                    ]
                },
            )

        # Extending Agent with new Knowledge Bases
        updated: AgentDB = agent.update_schema(
            user=self.user.id,
            version=agent.meta.version + 1,
            **{
                "knowledge_bases": agent.knowledge_bases
                + [kb.id for kb in knowledge_bases]
            },
        )
        await logger.ainfo(
            self.messages.api_knowledge_bases_adding_to_agent_fmt.format(
                [kb.id for kb in knowledge_bases],  # noqa: C416
                agent.id,
            ),
            data=updated.model_dump_json(),
        )
        if not await self.agents.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_update_error_msg,
            )

        return [kb.model_dump() for kb in knowledge_bases]

    @router.get(
        "/agents/{agent_id}/knowledge/bases/",
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
        response_model=list[KnowledgeBaseGet],
    )
    @router.get(
        "/agents/{agent_id}/knowledge/bases",
        status_code=status.HTTP_200_OK,
        response_model=list[KnowledgeBaseGet],
    )
    async def get_knowledge_bases(
        self,
        agent_id: Uuid,
    ) -> list[dict[str, Any]]:
        """
        Retrieves all knowledge_bases visible to the user,
            based on the list of agents

        Args:
            agent_id (list[Uuid]): Agent ID

        Returns:
            list[dict[str, Any]]: Collection of knowledge_bases
        """
        await self.atlas_get_agent(agent_id)
        return [
            i.model_dump()
            for i in await self.knowledge_bases.get_items(
                KnowledgeBaseDB.agent == agent_id
            )
        ]

    @router.delete(
        "/agents/{agent_id}/knowledge/bases/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/agents/{agent_id}/knowledge/bases",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("deleted_response"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def delete_knowledge_bases(
        self,
        response: Response,
        agent_id: Uuid,
        ids: list[Uuid] = Query([]),
        files: bool = Query(True),
    ) -> Response:
        """
        Deletes all the knowledge bases given in the list of IDs

        Args:
            response (Response): FastAPI Response
            agent_id (list[Uuid]): Agent ID
            ids (list[Uuid]): IDs of Knowledge Bases to be deleted,
                              defaults to an empty list
            files (bool): Flag to indicate that files should be deleted,
                          defaults to True

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If duplicate IDs are found in
                               deletion list
            AtlasAPIException: If some of the Knowledge Bases
                               could not be retrieved
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        agent: AgentDB = await self.atlas_get_agent(agent_id)

        # TODO: Prevent deletion of Knowledge Bases if pipeline is running

        if ids:
            # Check that all IDs exist
            if invalid_ids := set(ids) - set(agent.knowledge_bases):
                raise AtlasAPIException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=self.messages.api_knowledge_bases_not_found_error_msg,
                    details={"ids": list(invalid_ids)},
                )
        else:
            # Default to the entire agent's collection
            ids = agent.knowledge_bases

        # Retrieve list of associated knowledge bases
        kbs: list[KnowledgeBaseDB] = await self.knowledge_bases.get_items(
            In(KnowledgeBaseDB.id, ids)
        )
        rag_configs: list[RAGConfigDB] = await self.atlas_get_rag_configs(
            agent_id
        )

        # Clear all associated embeddings
        try:
            await self.atlas_delete_knowledge_base_embeddings(
                agent,
                rag_configs,
                kbs,
                logger,
            )
        except AtlasAPIException:
            raise

        # Updating Agent details
        updated: AgentDB = agent.update_schema(
            user=self.user.id,
            version=agent.meta.version + 1,
            **{
                "knowledge_bases": [
                    kb
                    for kb in agent.knowledge_bases
                    if kb not in [k.id for k in kbs]
                ]
            },
        )
        await logger.ainfo(
            self.messages.api_knowledge_bases_update_agent_fmt.format(
                updated.id, [k.id for k in kbs]
            ),
            data=updated.model_dump_json(),
        )
        if not await self.agents.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_update_error_msg,
            )

        # Deletes Knowledge Bases
        await logger.ainfo(
            self.messages.api_knowledge_bases_delete_fmt.format(
                [k.id for k in kbs]
            )
        )
        if not await self.knowledge_bases.delete_items(
            In(KnowledgeBaseDB.id, ids),
        ):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_knowledge_bases_delete_error_msg,
            )

        # Deletes the hardcopy files
        if files:
            await self.atlas_delete_knowledge_base_files(kbs)

        response.status_code = status.HTTP_204_NO_CONTENT
        return response
