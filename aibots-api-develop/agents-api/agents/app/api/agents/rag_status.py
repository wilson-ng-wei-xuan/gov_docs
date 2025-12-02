from __future__ import annotations

from atlas.asgi.exceptions import AtlasAPIException, AtlasAuthException
from atlas.asgi.schemas import APIKey, AtlasASGIConfig
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import State
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi_utils.cbv import cbv

from agents.models import AgentDB, KnowledgeBaseDB, RAGConfigDB

from .base import AgentsAPIMixin

__doc__ = """
Contains all the API calls for the KnowledgeBases API

Attributes:
    router (APIRouter): KnowledgeBases API Router
"""

__all__ = ("router",)

router: APIRouter = AtlasRouters.atlas_get_router(
    prefix="",
    tags=["Agents"],
    dependencies=[],
)


@cbv(router)
class RAGStatusAPI(AgentsAPIMixin):
    """
    API Class for updating Agent RAG and Knowledge Base statuses

    Attributes:
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

    api_key: APIKey = Depends(
        AtlasDependencies.get_registry_item("auth_api_key")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    @router.put(
        "/agents/{agent_id}/knowledge/bases/{secondary_id}/statuses/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/agents/{agent_id}/knowledge/bases/{secondary_id}/statuses",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def update_embeddings(
        self,
        response: Response,
        agent_id: str,
        secondary_id: str,
        state: State,
        rag_config_id: str = Query(alias="ragConfig"),
    ) -> Response:
        """

        Args:
            response (Response): response for API
            agent_id (str): agent ID to be referenced
            secondary_id (str): knowledge base ID to be updated
            rag_config_id (str): RAG config ID to be updated
            state (State): state to be updated to

        Returns:
            Response: FastAPI Response
        Raises:
            AtlasAPIException: If agent ID is not found
            AtlasAPIException: If RAGConfig ID is not found
            AtlasAPIException: If agent does not have RAGConfig of stated ID
            AtlasAPIException: If RAGConfig failed to update
        """
        # logger: structlog.typing.FilteringBoundLogger = (
        #     self.logger.get_structlog_logger(
        #       self.atlas.environ.loggers["api"]
        #     )
        # )
        # TODO: refactor into reusable method.
        if self.api_key.key not in self.atlas.environ.internal_api_keys:
            raise AtlasAuthException(
                user=self.api_key.key,
                message=self.messages.api_agents_api_key_not_valid,
            )
        # 1) if agent exists, continue,
        # else throw error that agent does not exist
        agent: AgentDB = await self.atlas_get_agent(agent_id=agent_id)

        # 2) if knowledge base exists within agent,
        # else throw error that knowledge base not under agent
        if secondary_id not in agent.knowledge_bases:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_knowledge_bases_not_found_in_agent_error_msg,
            )
        # 3) if rag config exists in agent rags,
        # else throw error that rag config not under agent
        if rag_config_id not in agent.rags:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_rag_configs_not_found_error_msg,
            )
        # 4) if knowledge base exists, continue,
        # else throw error that knowledge base does not exist
        kb: KnowledgeBaseDB = await self.knowledge_bases.get_item_by_id(
            item_id=secondary_id
        )
        if kb is None:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_knowledge_bases_not_found_error_msg,
            )
        # 5) if rag config exists, continue,
        # else throw error that rag config does not exist
        await self.__get_rag_config(rag_config_id=rag_config_id)

        # 6) set state to knowledge base
        kb.embeddings = {
            **kb.embeddings,
            rag_config_id: state.model_dump(mode="json"),
        }
        # TODO: add in canonical logging
        if not await self.knowledge_bases.replace_item(kb):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="There was an error updating knowledge base state",
            )
        response.status_code = 204
        return response
        # end

    @router.put(
        "/agents/{agent_id}/rags/{rag_config_id}/statuses/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/agents/{agent_id}/rags/{rag_config_id}/statuses",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def update_rag_config(
        self,
        response: Response,
        agent_id: str,
        rag_config_id: str,
        state: State,
    ) -> Response:
        """
        Args:
            response (Response): response of API
            agent_id (str): id of agent
            rag_config_id (str): id of RAG config to be updated
            state (State): state to be updated to

        Returns:
            Response: response of API
        """
        # logger: structlog.typing.FilteringBoundLogger = (
        #     self.logger.get_structlog_logger(
        #           self.atlas.environ.loggers["api"]
        #       )
        # )
        if self.api_key.key not in self.atlas.environ.internal_api_keys:
            raise AtlasAuthException(
                user=self.api_key.key,
                message=self.messages.api_agents_api_key_not_valid,
            )
        # 1) check to see if RAG Config with defined user exists
        rag_config: RAGConfigDB = await self.__get_rag_config(
            rag_config_id=rag_config_id
        )

        # 2) check to see if rag config exists in agent
        agent: AgentDB = await self.__get_agent(agent_id=agent_id)
        if rag_config_id not in agent.rags:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_rag_configs_not_found_error_msg,
            )

        # 3) update schema for RAG Config
        rag_config.previous = rag_config.current
        rag_config.current = state
        rag_config.timestamp = rag_config.timestamp

        # 3) replace RAG Config
        # TODO: add in canonical log
        if not await self.rag_configs.replace_item(rag_config):
            raise AtlasAPIException(
                status_code=500,
                message=self.messages.api_rag_configs_update_error_msg,
            )
        response.status_code = 204
        return response

    async def __get_agent(self, agent_id: str) -> AgentDB:
        """
        convenience method to get agent
        Args:
            agent_id:

        Returns:
            AgentDB: agent of agent_id
        """
        agent: AgentDB = await self.atlas_get_agent(agent_id)
        if agent is None:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_agents_agent_not_found_error_msg,
                details={"agent_id": agent_id},
            )
        return agent

    async def __get_rag_config(self, rag_config_id: str) -> RAGConfigDB:
        """
        Convenience method to get rag config id
        Args:
            rag_config_id (str): id of rag configs

        Returns:
            RAGConfigDB: rag config of rag_config_id
        """
        rag_config: RAGConfigDB = await self.rag_configs.get_item_by_id(
            rag_config_id
        )
        if rag_config is None:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_rag_configs_not_found_error_msg,
                details={"rag_config_id": rag_config_id},
            )
        return rag_config
