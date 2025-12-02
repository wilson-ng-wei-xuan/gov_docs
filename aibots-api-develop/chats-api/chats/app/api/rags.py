from __future__ import annotations

import json
from io import BytesIO
from types import SimpleNamespace
from typing import Annotated, Any

import structlog
from aibots.constants import DEFAULT_PLAYGROUND_AGENT
from aibots.models import EmbeddingsMetadata, RAGPipeline
from aibots.rags import AtlasRAGException, RAGEngine
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig
from atlas.beanie import BeanieDataset, BeanieService
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import ExecutionState, UserLogin, Uuid
from atlas.services import ServiceManager
from atlas.structlog import StructLogService
from beanie.odm.operators.find.comparison import In
from fastapi import APIRouter, Depends, status
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version
from pydantic import Field

from chats.environ import AIBotsChatEnviron
from chats.mixins.files import FilesAPIMixin
from chats.models import AgentDB, KnowledgeBaseDB, RAGConfigDB

__doc__ = """
Contains all the API calls for the RAG API

Attributes:
    router (APIRouter): RAG API Router
"""


__all__ = ("router",)

router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "prefix": "",
        "tags": ["RAG"],
        "dependencies": [
            Depends(AtlasDependencies.get_registry_item("reject_api_key"))
        ],
        "responses": {
            **AtlasRouters.response("created_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("401_authentication_error"),
            **AtlasRouters.response("403_permissions_error"),
            **AtlasRouters.response("500_internal_server_error"),
        },
    }
)


class RAGPipelinePost(APIPostPut):
    """
    POST representation for triggering a RAG pipeline

    Attributes:
        pipelines (list[Uuid]): Configured pipelines,
                                defaults to an empty list
        knowledge_bases (list[Uuid]): Knowledge bases to
                                      be triggered
    """

    pipelines: list[Uuid] = []
    knowledge_bases: Annotated[list[Uuid], Field([], alias="knowledgeBases")]


class RAGPipelineGet(APIGet, RAGPipeline):
    """
    GET representation of a RAG pipeline

    Attributes:
        id (Uuid): ID of the pipeline
        knowledge_bases (list[Uuid]): IDs of the associated Knowledge Bases
        status (StateTransitions): Generic representation that consolidates
                                   the state transitions
        embeddings (Embeddings): Embeddings and associated data generated
                                 via the embeddings process
        meta (Meta): Meta information associated with the resource
    """  # noqa: E501


@cbv(router)
class RAGPipelineAPI(FilesAPIMixin):
    """
    Class-based view for representing the RAG API

    Attributes:
        user (UserLogin): Authenticated user details
        atlas (AtlasConfig): Atlas Config class
        environ (AIBotsChatEnviron): Environment variables
        db (BeanieService): MongoDB Service
        knowledge_bases (BeanieDataset): KnowledgeBases Dataset
        agents (BeanieDataset): Agents Dataset
        files (BeanieDataset): Files Dataset
        logger (StructLogService): Logging Service
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    def __init__(self):
        super().__init__()
        self.environ: AIBotsChatEnviron = self.atlas.environ
        self.messages: SimpleNamespace = SimpleNamespace(
            **self.environ.messages["rag"],
            **self.environ.messages["chats"],
        )
        self.bucket: str = self.environ.cloudfront.bucket
        self.db: BeanieService = self.atlas.db
        self.knowledge_bases: BeanieDataset = self.db.atlas_dataset(
            KnowledgeBaseDB.Settings.name
        )
        self.rag_configs: BeanieDataset = self.db.atlas_dataset(
            RAGConfigDB.Settings.name
        )
        self.agents: BeanieDataset = self.db.atlas_dataset(
            AgentDB.Settings.name
        )
        self.rag: ServiceManager = self.atlas.services.get("rag")
        self.logger: StructLogService = self.atlas.logger

    @router.post(
        "/rags/{agent_id}/pipelines/",
        response_model=RAGPipelineGet,
        include_in_schema=False,
    )
    @router.post("/rags/{agent_id}/pipelines", response_model=RAGPipelineGet)
    @api_version(1, 0)
    async def trigger_pipeline(
        self,
        agent_id: Uuid,
        rag_details: RAGPipelinePost,
    ) -> dict[str, Any]:
        """
        Triggers the Retrieval Augmented Generation (RAG) pipeline
        configurations encapsulated as an Agent config. The pipelines will
        run asynchronously and update their status in the background. When
        the pipelines are complete or if any errors occur during processing,
        a completion email/notification will be sent out.

        Args:
            agent_id (Uuid): ID of the Agent
            rag_details (RAGPipelinePost): Details of the RAG Pipeline

        Returns:
            FastAPI Response

        Raises:
            AtlasAPIException: If user does not have permissions to
                               trigger RAG pipeline
        """

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Check that playground agent cannot be used for RAG pipelines
        if agent_id == DEFAULT_PLAYGROUND_AGENT.get("_id"):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_rag_cannot_rag_on_playground_bot_error_msg,
                details={
                    **rag_details.model_dump(mode="json", exclude_unset=True),
                    "id": agent_id,
                },
            )

        # TODO: Check if user has permission to access selected Agents

        # Validate if the agent exists and has a RAG pipeline configured
        agent: AgentDB = await self.agents.get_item_by_id(agent_id)
        if not agent:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_agent_not_found_msg,
                details={
                    **rag_details.model_dump(mode="json", exclude_unset=True),
                    "id": agent_id,
                },
            )
        if not agent.rags:
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_rag_agent_no_rag_config_error_msg,
                details={
                    **rag_details.model_dump(mode="json", exclude_unset=True),
                    "id": agent_id,
                },
            )

        # Validate knowledge bases to be triggered
        knowledge_bases: list[Uuid] = (
            rag_details.knowledge_bases or agent.knowledge_bases
        )
        if not set(agent.knowledge_bases) >= set(knowledge_bases):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_rag_perform_rag_on_invalid_knowledge_base_error_msg,
                details={
                    **rag_details.model_dump(mode="json", exclude_unset=True),
                    "id": agent_id,
                },
            )

        # Validate agent's pipeline configurations to be generated
        rag_configs: list[Uuid] = rag_details.pipelines or agent.rags
        if not set(agent.rags) >= set(rag_configs):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_rag_perform_rag_on_invalid_pipeline_configuration_error_msg,
                details={
                    **rag_details.model_dump(mode="json", exclude_unset=True),
                    "id": agent_id,
                },
            )

        # Trigger the relevant pipelines
        pipelines: list[RAGConfigDB] = await self.rag_configs.get_items(
            In(RAGConfigDB.id, rag_configs)
        )
        knowledge_bases: list[
            KnowledgeBaseDB
        ] = await self.knowledge_bases.get_items(
            In(KnowledgeBaseDB.id, knowledge_bases)
        )
        updated_kbs: list[KnowledgeBaseDB] = []
        for pipeline in pipelines:
            engine: RAGEngine = self.rag.get(pipeline.type)
            await engine.atlas_init_pipeline(agent, pipeline)

            for knowledge_base in knowledge_bases:
                # TODO: Send SQS message with the appropriate data schema.
                #   Until then we will execute the respective pipelines
                #   accordingly

                # Run pipeline only if embeddings are not present
                if not knowledge_base.embeddings.get(pipeline.id):
                    # Run pipeline
                    await logger.ainfo(
                        self.messages.api_rag_generate_pipeline_fmt.format(
                            pipeline.type, agent_id, knowledge_base.id
                        ),
                        data=json.dumps(
                            {
                                "pipeline": pipeline.model_dump(mode="json"),
                                "knowledge_base": knowledge_base.model_dump(
                                    mode="json"
                                ),
                            }
                        ),
                    )

                    embeddings: EmbeddingsMetadata | None
                    _, file = await self.atlas_download_file(
                        knowledge_base.content
                    )
                    try:
                        embeddings = await engine.atlas_aembed(
                            agent=agent,
                            rag_config=pipeline,
                            knowledge_base=knowledge_base,
                            content=BytesIO(file.read()),
                        )
                    except AtlasRAGException as e:
                        raise AtlasAPIException(
                            status_code=e.status_code,
                            message=f"Pipeline: {pipeline.type} - {e.message}",
                            details=e.details,
                        ) from e
                    if embeddings:
                        knowledge_base.embeddings[pipeline.id] = embeddings

                    if knowledge_base.id not in [kb.id for kb in updated_kbs]:
                        updated_kbs.append(knowledge_base)

                # Update the state of the pipeline to complete if all
                # the embeddings are complete
                if all(
                    kb.embeddings[pipeline.id].current.state
                    == ExecutionState.completed
                    for kb in knowledge_bases
                ):
                    pipeline.update_state(ExecutionState.completed)

        # Update Agent and knowledge base details in DB
        agent.knowledge_bases = [kb.id for kb in knowledge_bases]
        agent.rags = rag_configs

        if not await self.agents.replace_item(agent):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_rag_update_agent_error_msg,
                details={
                    **rag_details.model_dump(mode="json", exclude_unset=True),
                    "id": agent_id,
                },
            )

        # TODO: This should be handled by the respective status objects
        if not await self.knowledge_bases.update_items(*updated_kbs):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_rag_update_knowledge_base_error_msg,
                details={
                    **rag_details.model_dump(mode="json", exclude_unset=True),
                    "id": agent_id,
                },
            )

        if not await self.rag_configs.update_items(*pipelines):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_rag_update_pipeline_error_msg,
                details={
                    **rag_details.model_dump(mode="json", exclude_unset=True),
                    "id": agent_id,
                },
            )

        # TODO: v2: Insert pipeline into DB
        return {
            "id": agent_id,
            "pipeline": AgentDB.atlas_get_uuid(),
            "config": {
                "knowledge_bases": [kb.id for kb in knowledge_bases],
                "pipelines": rag_details.pipelines,
            },
        }

    @router.get(
        "/rags/pipelines/",
        status_code=status.HTTP_200_OK,
        response_model=list[RAGPipelineGet],
        include_in_schema=False,
    )
    @router.get(
        "/rags/pipelines",
        status_code=status.HTTP_200_OK,
        response_model=list[RAGPipelineGet],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved all a User's Chats",
                "content": {"application/json": {"example": []}},
                "model": list[RAGPipelineGet],
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_pipelines(self) -> list[dict[str, Any]]:
        """
        Retrieves all the pipelines associated with the user

        Returns:
            list[dict[str, Any]]: List of all pipelines
        """
        # Retrieve and return a user's chats
        # Note: Retrieve only user's chats from modifications dictionary

        return status.HTTP_501_NOT_IMPLEMENTED
