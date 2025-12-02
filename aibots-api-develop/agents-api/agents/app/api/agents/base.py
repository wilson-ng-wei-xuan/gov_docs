from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any

import structlog.typing
from aibots.constants import DEFAULT_RAG_PIPELINE_TYPE
from aibots.models import (
    DataSource,
    DataSourceType,
    DeploymentState,
)
from aibots.rags import AtlasRAGException, RAGEngine
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIPostPut
from atlas.beanie import BeanieDataset
from atlas.schemas import Permissions, Uuid, VisibilityLevel
from atlas.services import ServiceManager
from atlas.utils import generate_uuid
from beanie.odm.operators.find.logical import Or
from fastapi import status
from pydantic import AnyUrl

from agents.mixins.files import FilesAPIMixin
from agents.models import AgentDB, AgentSharing, KnowledgeBaseDB, RAGConfigDB
from agents.utils import convert_string_to_url

__all__ = ("DataSourcePost", "RAGConfigPost", "AgentsAPIMixin")


class DataSourcePost(APIPostPut, DataSource):
    """
    Represents the raw data and its associated metadata

    Attributes:
        name (str): Name of the Data Source
        description (str): Brief description of the Data Source
        type (DataSourceType): Types of supported data sources
        content (Uuid | AnyUrl | str): Data content
        metadata (dict[str, Any]): Additional metadata to be
                                   appended together with the
                                   Data Source, defaults to
                                   an empty dictionary
    """

    type: DataSourceType = DataSourceType.file
    content: Uuid | AnyUrl | str | None = None
    metadata: dict[str, Any] = {}


class RAGConfigPost(APIPostPut):
    """
    RAG pipelines and configuration associated with a Agent

    Attributes:
        type (str): RAG pipeline type, one of the supported
                    RAG pipelines
        config (dict[str, Any]): RAG pipeline configuration, defaults
                                 to an empty dictionary
    """

    type: str = DEFAULT_RAG_PIPELINE_TYPE
    config: dict[str, Any] = {}


class AgentsAPIMixin(FilesAPIMixin):
    """
    Base Class for handling Agent APIs

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

    def __init__(self):
        super().__init__()
        self.messages: SimpleNamespace = SimpleNamespace(
            **self.environ.messages["agents"],
            **self.environ.messages["knowledge_bases"],
            **self.environ.messages["rag_configs"],
        )
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

    @property
    def ownership_resource(self) -> str:
        """
        Convenience function to standardise the ownership
        permissions value of Agents

        Returns:
            str: Agent ownership permission string
        """
        return "agents.authorizations"

    @property
    def augment_allow(self) -> dict[str, list[str]]:
        """
        Convenience function to retrieve the standardised
        augment allow component for ownership

        Returns:
            dict[str, list[str]]: Augment allow details
        """
        return {
            "owner": [
                "chats.{}:create,read,update,delete",
                "messages.{}:create,read,update,delete",
                "rags.{}:create,read,update,delete",
            ],
            "admin": [
                "chats.{}:create,read,update,delete",
                "messages.{}:create,read,update,delete",
                "rags.{}:create,read,update,delete",
            ],
            "editor": [
                "chats.{}:create,read,update,delete",
                "messages.{}:create,read,update,delete",
                "rags.{}:create,read,update,delete",
            ],
            "user": [
                "chats.{}:create,read,update,delete",
                "messages.{}:create,read,update,delete",
            ],
        }

    async def atlas_get_agent(
        self, agent_id: Uuid | str, deleted: bool = False
    ) -> AgentDB:
        """
        Convenience function to retrieve the Agent and
        validate if it exists

        Args:
            agent_id (Uuid | str): ID or slug of the Agent
            deleted (bool): Indicates if deleted Agents are
                            to be included, defaults to True

        Returns:
            AgentDB: Validated agent

        Raises:
            AtlasAPIException: If Agent does not exist
        """
        query_filters: list[Any] = [
            Or(AgentDB.id == agent_id, AgentDB.sharing.url_path == agent_id)
        ]
        if not deleted:
            query_filters.append(
                AgentDB.meta.deleted == None,  # noqa: E711
            )

        if (agent := await self.agents.get_item(*query_filters)) is None:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_agents_agent_not_found_error_msg,
                details={"id": agent_id},
            )

        return agent

    async def atlas_generate_url_slug(self, agent_id: Uuid, name: str) -> str:
        """
        Convenience function for generating an Agent's URL slug

        Args:
            agent_id (Uuid): ID of the Agent
            name (str): Name of the Agent

        Returns:
            str: Generated URL
        """
        slug: str = convert_string_to_url(name)
        exists: list[AgentDB] = await self.agents.get_items(
            AgentDB.sharing.url_path == slug
        )
        if exists:
            slug = agent_id
        return slug

    def atlas_generate_agent_sharing(
        self, slug: str, api_version: str = "v1.0"
    ) -> AgentSharing:
        """
        Convenience function for standardising the AgentSharing creation

        Args:
            slug (str): Url slug
            api_version (str): Latest API version

        Returns:
            AgentSharing: Generated AgentSharing
        """
        return AgentSharing(
            url_path=slug,
            public_url=str(self.environ.project.pub_url) + f"chats/{slug}",
            api_url=str(self.environ.project_api.pub_url)
            + f"{api_version}/chats/{slug}",
        )

    def atlas_generate_agent_permissions(
        self,
        agent: AgentDB,
    ) -> list[Permissions]:
        """
        Convenience function for generating the Agent permissions

        Args:
            agent (AgentDB): Agent details

        Returns:
            list[Permissions]: List of permissions
        """
        return agent.generate_permissions(
            ownership_resource=self.ownership_resource,
            augment_allow=self.augment_allow,
        )

    async def atlas_validate_ownership(
        self,
        release_state: DeploymentState,
        visibility: VisibilityLevel,
        users: list[Uuid | str],
        groups: list[Uuid | str],
        details: dict[str, Any],
    ) -> None:
        """
        Validates the ownership details of the Agent

        Args:
            release_state (DeploymentState): Deployment state of the Agent
            visibility (VisibilityLevel): Visibility of the Agent
            users (list[Uuid | str]): List of users
            groups (list[Uuid | str): List of groups
            details (dict[str, Any]): Validation details

        Returns:
            None

        Raises:
            AtlasAPIException: Attempting to modify visibility of
                               non-production Agents
            AtlasAPIException: Invalid users or groups were set
        """
        # Validate ownership details for non-production Agents
        # 1. Check that only Production Agents can modify the visibility
        #    level to wog and public
        if release_state != DeploymentState.production:  # noqa: SIM102
            if visibility in [VisibilityLevel.wog, VisibilityLevel.public]:
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=self.messages.api_agents_only_production_agents_wog_visibility_error_msg,
                    details=details,
                )

        # For production Agents
        # 1. Check that all users exist
        # 2. Check that all groups exist
        try:
            await self.atlas_validate_users(users)
            await self.atlas_validate_groups(groups)
        except AtlasAPIException as e:
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=e.message,
                details=e.details,
            ) from e

    def atlas_validate_rag_configs(
        self,
        rag_configs: list[RAGConfigPost],
    ):
        """
        Validates the RAG configs of the Agent

        Args:
            rag_configs (list[RAGConfigPost]): RAG config details

        Returns:
            None

        Raises:
            AtlasAPIException: Invalid RAG Config type
            AtlasAPIException: Invalid default pipeline set
            AtlasAPIException: Default pipeline set but RAG configs
                               not set
            AtlasAPIException: Default pipeline not found in RAG
                               configs
        """

        if rag_configs:  # noqa: SIM102
            # Invalid RAG pipeline type
            if not all(i.type in self.rag for i in rag_configs):
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=self.messages.api_agents_invalid_default_pipeline_error_msg,
                )

            # TODO: Invalid RAG config, validated via schema

    def atlas_validate_default_pipeline(
        self,
        default_pipeline: Uuid | None,
        rag_configs: list[Uuid],
    ) -> None:
        """
        Validates the default pipeline value of the Agent

        Args:
            default_pipeline (Uuid | None): Default RAG pipeline
            rag_configs (list[Uuid]): RAG config IDs

        Returns:
            None

        Raises:
            AtlasAPIException: Invalid RAG Config type
            AtlasAPIException: Invalid default pipeline set
            AtlasAPIException: Default pipeline set but RAG configs
                               not set
            AtlasAPIException: Default pipeline not found in RAG
                               configs
        """

        if default_pipeline is not None:
            # RAG configs were not provided
            if not rag_configs:
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=self.messages.api_agents_default_pipeline_but_no_rag_configs_error_msg,
                )

            # Default pipeline not found in RAG configs
            if default_pipeline not in rag_configs:
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=self.messages.api_agents_default_pipeline_but_not_set_in_rag_configs_error_msg,
                )

    async def atlas_validate_knowledge_bases(
        self, kbs: list[DataSourcePost]
    ) -> None:
        """
        Validates the Knowledge Base contents, checking if all files exist

        Args:
            kbs (list[DataSourcePost]): List of Knowledge Bases

        Returns:
            None
        """
        # Validate Knowledge Bases
        # Check all files for Knowledge Bases exists
        await self.atlas_validate_files(
            [kb.content for kb in kbs if kb.type == DataSourceType.file]
        )

        # TODO: Validate if KB urls are whitelisted using a service
        #  e.g. Google Safe Browsing

    def atlas_create_knowledge_base(
        self,
        kbs: list[DataSourcePost],
        agent: Uuid,
    ) -> list[KnowledgeBaseDB]:
        """
        Convenience function for creating Knowledge Bases

        Args:
            kbs (list[DataSourcePost]): List of knowledge bases to be
                                        created
            agent (Uuid): ID of the associated Agent

        Returns:
            list[KnowledgeBaseDB]: List of Knowledge Bases to be
                                   created
        """
        storage: dict[str, Any]
        knowledge_bases: list[KnowledgeBaseDB] = []
        for kb in kbs:
            if kb.type == DataSourceType.file:
                storage = {
                    "type": "aibots",
                    "location": self.atlas_get_public_url(kb.content, kb.name),
                    "value": kb.content,
                }
            else:
                storage = {
                    "type": "aibots",
                    "location": None,
                    "value": None,
                }
            knowledge_bases.append(
                KnowledgeBaseDB(
                    id=generate_uuid(),
                    agent=agent,
                    storage=storage,
                    **kb.model_dump(),
                )
            )
        return knowledge_bases

    async def atlas_get_knowledge_bases(
        self, agent_id: Uuid
    ) -> list[KnowledgeBaseDB]:
        """
        Convenience function for retrieving all Knowledge Bases
        associated with an Agent

        Args:
            agent_id (Uuid): ID of the Agent

        Returns:
            list[KnowledgeBaseDB]: List of Knowledge Bases
        """
        return await self.knowledge_bases.get_items(
            KnowledgeBaseDB.agent == agent_id,
            sort=[(KnowledgeBaseDB.timestamp, 1)],
        )

    async def atlas_clear_knowledge_base_rag_embeddings(
        self,
        agent: AgentDB,
        rag_config: RAGConfigDB,
        knowledge_bases: list[KnowledgeBaseDB],
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        """
        Clears the embeddings of a given RAG pipeline if they have been
        generated i.e. there is metadata present in the embeddings

        Args:
            agent (AgentDB): Agent to clear
            rag_config (RAGConfigDB): RAG config
            knowledge_bases (list[KnowledgeBaseDB]): Knowledge Bases
            logger (
                structlog.typing.FilteringBoundLogger
            ): Logger for logging details

        Returns:
            None

        Raises:
            AtlasAPIException: If any issues occur when
                               embeddings are being cleared
        """
        try:
            engine: RAGEngine = self.rag.get(rag_config.type)
            kbs: list[KnowledgeBaseDB] = [
                kb for kb in knowledge_bases if rag_config.id in kb.embeddings
            ]
            await logger.ainfo(
                self.messages.api_knowledge_bases_delete_embeddings_fmt.format(
                    rag_config.id,
                    rag_config.type,
                    agent.id,
                    [kb.id for kb in kbs],
                )
            )
            if kbs:
                await engine.atlas_adelete_embeddings(
                    agent=agent,
                    rag_config=rag_config,
                    knowledge_bases=kbs,
                )
            await logger.ainfo(
                self.messages.api_knowledge_bases_deleted_embeddings_fmt.format(
                    rag_config.id,
                    rag_config.type,
                    agent.id,
                    [kb.id for kb in kbs],
                )
            )
        except AtlasRAGException as e:
            await logger.ainfo(
                self.messages.api_knowledge_bases_deleting_embeddings_error_fmt.format(
                    e.__class__.__name__,
                    str(e),
                    rag_config.id,
                    rag_config.type,
                    agent.id,
                    [kb.id for kb in knowledge_bases],
                ),
                data=json.dumps(e.exception()),
            )
            raise AtlasAPIException(**e.exception()) from e

    async def atlas_delete_knowledge_base_embeddings(
        self,
        agent: AgentDB,
        rag_configs: list[RAGConfigDB],
        knowledge_bases: list[KnowledgeBaseDB],
        logger: structlog.typing.FilteringBoundLogger,
    ):
        """
        Deletes the knowledge base and clears all
        associated embeddings

        Args:
            agent (AgentDB): Agent to clear
            rag_configs (list[RAGConfigDB]): RAG Configs
            knowledge_bases (list[KnowledgeBaseDB]): Knowledge Bases
            logger (
                structlog.typing.FilteringBoundLogger
            ): Logger for logging details

        Returns:
            None

        Raises:
            AtlasAPIException: If any issues occur when
                               embeddings are being cleared
        """

        await asyncio.gather(
            *(
                self.atlas_clear_knowledge_base_rag_embeddings(
                    agent=agent,
                    rag_config=rag_config,
                    knowledge_bases=knowledge_bases,
                    logger=logger,
                )
                for rag_config in rag_configs
            )
        )

    async def atlas_delete_knowledge_base_files(
        self, knowledge_bases: list[KnowledgeBaseDB]
    ):
        """
        Deletes all files added from the various Knowledge Bases

        Args:
            knowledge_bases (list[KnowledgeBaseDB]): List of knowledge bases

        Returns:
            None
        """
        await asyncio.gather(
            *(
                self.atlas_delete_file(kb.storage.value)
                for kb in knowledge_bases
            )
        )

    @staticmethod
    def atlas_create_rag_configs(
        rag_configs: list[RAGConfigPost | RAGConfigDB],
        agent: Uuid,
    ) -> list[RAGConfigDB]:
        """
        Convenience function for creating RAG Configs

        Args:
            rag_configs (
                list[RAGConfigPost | RAGConfigDB]
            ): List of RAG Configs to be created
            agent (Uuid): ID of the associated Agent

        Returns:
            list[RAGConfigDB]: List of RAG Configs to be
                                   created
        """
        configs: list[RAGConfigDB] = []
        for rag_config in rag_configs:
            configs.append(
                RAGConfigDB(
                    id=generate_uuid(),
                    agent=agent,
                    **rag_config.model_dump(include={"type", "config"}),
                )
            )
        return configs

    async def atlas_get_rag_configs(self, agent_id: Uuid) -> list[RAGConfigDB]:
        """
        Convenience function for retrieving all RAG Configs
        associated with an Agent

        Args:
            agent_id (Uuid): ID of the Agent

        Returns:
            list[RAGConfigDB]: List of Knowledge Bases
        """
        return await self.rag_configs.get_items(
            RAGConfigDB.agent == agent_id,
            sort=[(RAGConfigDB.timestamp, 1)],
        )
