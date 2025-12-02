from __future__ import annotations

import asyncio
import json
from typing import Annotated, Any

import structlog
from aibots.constants import DEFAULT_AGENT_WELCOME_MESSAGE
from aibots.models import Agent as AliasedAgent
from aibots.models import (
    AgentSharing,
    AgentTemplate,
    DeploymentState,
)
from annotated_types import Ge
from atlas.asgi.exceptions import AtlasAPIException, AtlasPermissionsException
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig, IDResponse
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import (
    AccessRoleType,
    DescriptiveName,
    DescriptiveNameOptional,
    Modifications,
    Ownership,
    OwnershipBase,
    Permissions,
    PermissionsType,
    UserLogin,
    Uuid,
    VisibilityLevel,
)
from beanie.odm.operators.find.logical import And, Or
from beanie.operators import In
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi_utils.cbv import cbv
from pydantic import BaseModel, Field

from agents.mixins.uam import UsersAPIMixin
from agents.models import (
    AgentChatConfig,
    AgentDB,
    AgentReleaseState,
    KnowledgeBaseDB,
    PermissionsDB,
    RAGConfigDB,
)

from .base import AgentsAPIMixin, DataSourcePost, RAGConfigPost

__doc__ = """
Contains all the API calls for the agents API

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


class AgentPost(APIPostPut, DescriptiveName):
    """
    POST parameters for creating a agent

    Attributes:
        name (constr): Name of the agent
        description (constr): Brief description of the agent
        ownership (OwnershipBase | None): Ownership details, defaults to None
        files (list[Uuid]): Non-embedded files associated with the agent,
                            defaults to an empty set of files
        knowledge_bases (list[DataSourcePost]): Knowledge Bases associated
                                                with agent, defaults to an
                                                empty list
        agency (str): Agency associated with the agent
        welcome_message (str): Welcome message the agent will display when a
                               new chat is created, defaults to the default
                               agent welcome message
        templates (list[AgentTemplate]): Default templates to use with the
                                         agent, defaults to an empty list
        rags (list[RAGConfigPost]): RAG configuration for the agent,
                                    defaults an empty list
        chat (AgentChatConfig): Chat configuration for the agent, defaults to
                                default Chat configuration
        tools (list[Uuid]): Tools that the Agent is able to access, defaults
                            to an empty list
        settings (dict[str, Any]): Additional settings associated with the
                                   agent, defaults to an empty dictionary
        tags (list[str]): Tags associated with the Agent, defaults to an
                          empty list
    """

    ownership: OwnershipBase | None = None
    files: list[Uuid] = []
    knowledge_bases: list[DataSourcePost] = []
    agency: str
    welcome_message: str = DEFAULT_AGENT_WELCOME_MESSAGE
    templates: list[AgentTemplate] = []
    rags: list[RAGConfigPost] = []
    chat: AgentChatConfig = AgentChatConfig()
    tools: list[Uuid] = []
    settings: dict[str, Any] = {}
    tags: list[str] = []


class AgentClonePost(DescriptiveNameOptional, AgentPost):
    """
    POST parameters for cloning a agent

    Attributes:
        name (Optional[StrictStr]): Name field with no length restriction
        description (Optional[StrictStr]): Description field, defaults to None
        ownership (OwnershipBase | None): Ownership details, defaults to None
        files (list[Uuid]): Non-embedded files associated with the agent,
                            defaults to an empty set of files
        knowledge_bases (list[DataSourcePost]): Knowledge Bases associated
                                                with agent, defaults to an
                                                empty list
        agency (str | None): Agency associated with the agent
        welcome_message (str): Welcome message the agent will display when a
                               new chat is created, defaults to the default
                               agent welcome message
        templates (list[AgentTemplate]): Default templates to use with the
                                         agent, defaults to an empty list
        rags (list[RAGConfigPost]): RAG configuration for the agent,
                                    defaults an empty list
        chat (AgentChatConfig): Chat configuration for the agent, defaults to
                                default Chat configuration
        tools (list[Uuid]): Tools that the Agent is able to access, defaults
                            to an empty list
        settings (dict[str, Any]): Additional settings associated with the
                                   agent, defaults to an empty dictionary
        tags (list[str]): Tags associated with the Agent, defaults to an
                          empty list
    """

    agency: str | None = None


class AgentPut(APIPostPut, DescriptiveNameOptional):
    """
    PUT parameters for modifying an existing agent

    Attributes:
        name (Optional[StrictStr]): Name field with no length restriction
        description (Optional[StrictStr]): Description field, defaults to None
        files (list[Uuid] | None): Non-embedded files associated with the
                                   agent, defaults to None
        agency (str | None): Agency associated with the agent, defaults to
                             None
        welcome_message (str | None): Welcome message the agent will
                                      display when a new chat is created,
                                      defaults to None
        templates (list[AgentTemplate] | None): Default templates to use
                                                with the agent, defaults
                                                to None
        chat (AgentChatConfig | None): Chat configuration for the agent,
                                       defaults to None
        tools (list[Uuid] | None): Tools that the Agent is able to access,
                                   defaults to None
        settings (dict[str, Any] | None): Additional settings associated
                                          with the agent, defaults to None
        tags (list[str] | None): Tags associated with the agent, defaults to
                                 None
    """

    files: list[Uuid] | None = None
    agency: str | None = None
    welcome_message: str | None = None
    templates: list[AgentTemplate] | None = None
    chat: AgentChatConfig | None = None
    tools: list[Uuid] | None = None
    settings: dict[str, Any] | None = None
    tags: list[str] | None = None


class AgentOwnershipPut(APIPostPut, OwnershipBase):
    """
    Generic description of Ownership details of a Resource used for
    updating the ownership details

    Attributes:
        visibility (VisibilityLevel): Visibility level of the Resource
        access (ResourceAccess): Users or groups with access to the
                                 Resource
    """

    visibility: VisibilityLevel


class AgentSharingPut(APIPostPut):
    """
    PUT representation of an Agent's sharing details

    Attributes:
        url_path (str): URL slug
    """

    url_path: Annotated[str, Field(validation_alias="urlPath")]


class AgentRAGPipelinePut(APIPostPut):
    """
    PUT parameters for modifying an Agent's default RAG pipeline

    Attributes:
        default_pipeline (Uuid | None): Default pipeline
    """

    default_pipeline: Uuid | None


class AgentGet(APIGet, AliasedAgent):
    """
    GET representation of an Agent

    Attributes:
        id (Uuid): UUID string
        name (constr): Name of the Agent
        description (constr): Brief description of the Agent
        featured (bool): Indicates if the Agent is featured,
                         defaults to False
        clone (Uuid | None): Indicates if the Agent is cloned
        sharing (AgentSharing): Sharing details of the Agent
        ownership (Ownership | None): Ownership details
        files (list[Uuid]): Non-embedded files associated
                            with the Agent
        agency (str): Agency associated with the Agent
        welcome_message (str): Welcome message the Agent will display when a
                               new chat is created
        templates (list[AgentTemplate]): Default templates to use
                                        with the Agent
        release_state (AgentReleaseState):  Represents the release status
                                            of the Agent, defaults to
                                            default release state values
        knowledge_bases (list[Uuid]): Knowledge Bases associated with Agent,
                                     defaults to an empty list
        default_pipeline (str | None): Default RAG pipeline, defaults to
                                       None
        rags (list[RAGConfig]): RAG configuration for the Agent,
                                     defaults to an empty list
        chat (AgentChatConfig): Chat configuration for the Agent,
                                defaults to default AgentChatConfig
                                values
        tools (list[Uuid]): Tools that the Agent is able to access,
                            defaults to an empty list
        settings (dict[str, Any]): Additional settings associated
                                   with the Agent, defaults to an empty
                                   dictionary
        tags (list[str]): Tags associated with the Agent, defaults to
                          an empty list
        meta (Meta): Meta information associated with the Agent
        modifications (Modifications): Modifications made to the Agent,
                                       defaults to an empty dictionary
    """


class AgentBriefGet(APIGet, DescriptiveName, Modifications):
    """
    Brief GET representation of an Agent

    Attributes:
        id (Uuid): UUID string
        name (constr): Name of the Agent
        description (constr): Brief description of the Agent
        featured (bool): Indicates if the Agent is featured,
                         defaults to False
        files (list[Uuid] | None): Non-embedded files associated
                            with the Agent
        sharing (AgentSharing): Sharing details of the Agent
        agency (str): Agency associated with the Agent
        meta (Meta): Meta information associated with the Agent
    """

    id: Uuid
    featured: bool
    agency: str
    files: list[Uuid]
    sharing: AgentSharing


class AgentCount(BaseModel):
    """
    Count of all Agents visible to the user.

    Attributes:
        owner (int): Number of Agents owned by the user.
        admin (int): Number of Agents with admin privileges.
        shared (int): Number of Agents shared with the user.
        public (int): Number of Agents shared with WOG.
    """

    owner: Annotated[int, Ge(0)] = 0
    admin: Annotated[int, Ge(0)] = 0
    shared: Annotated[int, Ge(0)] = 0
    public: Annotated[int, Ge(0)] = 0


# TODO: Restrict Agents to those with permissions granted
@cbv(router)
class AgentsAPI(UsersAPIMixin, AgentsAPIMixin):
    """
    Class-based view for representing the agents API

    Attributes:
        user (UserLogin): Authenticated user details
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    @router.post(
        "/agents/",
        response_model=IDResponse,
        status_code=status.HTTP_201_CREATED,
        include_in_schema=False,
    )
    @router.post(
        "/agents",
        response_model=IDResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            **AtlasRouters.response("created_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    async def create_agent(self, agent_details: AgentPost) -> dict[str, str]:
        """
        Creates a new agent

        Args:
            agent_details (agentPost): Details for creating an Agent

        Returns:
            dict[str, str]: Generated agent ID
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        # TODO: Validate Chat details
        # 1. AI Model should be supported
        # 2. Chat parameters should be supported

        # TODO: Validate Settings
        # 1. Settings should be supported

        # Check that the Agency exists
        try:
            await self.atlas_validate_agency(agent_details.agency)
        except AtlasAPIException as e:
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=e.message,
                details=e.details,
            ) from e

        # Check if url compatible string is unique
        # if not use the Bot ID
        agent_id: Uuid = AgentDB.atlas_get_uuid()
        slug: str = await self.atlas_generate_url_slug(
            agent_id, agent_details.name
        )

        # Check all files exists
        try:
            await self.atlas_validate_files(agent_details.files)
        except AtlasAPIException as e:
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=e.message,
                details=e.details,
            ) from e

        # Validate and create new knowledge bases to be added
        try:
            await self.atlas_validate_knowledge_bases(
                agent_details.knowledge_bases
            )
        except AtlasAPIException as e:
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=e.message,
                details=e.details,
            ) from e
        knowledge_bases: list[
            KnowledgeBaseDB
        ] = self.atlas_create_knowledge_base(
            agent_details.knowledge_bases, agent=agent_id
        )

        # Validate RAG Configs create new RAG configs to be added
        try:
            self.atlas_validate_rag_configs(agent_details.rags)
        except AtlasAPIException as e:
            raise AtlasAPIException(
                status_code=e.status_code,
                message=e.message,
                details=agent_details.model_dump(
                    mode="json", exclude_unset=True
                ),
            ) from e
        rag_configs: list[RAGConfigDB] = self.atlas_create_rag_configs(
            agent_details.rags, agent=agent_id
        )

        # Create the Agent
        agent: AgentDB = AgentDB.create_schema(
            user=self.user.id,
            uid=agent_id,
            resource_type="agents",
            location=str(self.environ.project.pub_url)
            + f"latest/agents/{agent_id}",
            version=1,
            **{
                "knowledge_bases": [kb.id for kb in knowledge_bases],
                "rags": [r.id for r in rag_configs],
                "release_state": AgentReleaseState(),
                "sharing": self.atlas_generate_agent_sharing(slug),
                **agent_details.model_dump(
                    exclude={"ownership", "knowledge_bases", "rags"}
                ),
            },
        )

        # Validate ownership details
        agent.generate_ownership(agent_details.ownership)
        await self.atlas_validate_ownership(
            release_state=agent.release_state.state,
            visibility=agent.ownership.visibility,
            users=list(agent.atlas_users()),
            groups=list(agent.atlas_groups()),
            details=agent_details.model_dump(mode="json", exclude_unset=True),
        )

        # Insert into Database
        await logger.ainfo(
            self.messages.api_agents_create_fmt.format(agent.id),
            data=agent.model_dump_json(),
        )
        if not await self.agents.create_item(agent):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_create_error_msg,
                details=agent_details.model_dump(
                    mode="json", exclude_unset=True
                ),
            )

        # Generating and adding all the permissions
        to_add: list[PermissionsDB] = await self.atlas_add_permissions(
            self.atlas_generate_agent_permissions(agent)
        )
        await logger.ainfo(
            self.messages.api_agents_permissions_adding_fmt.format(agent.id),
            data=json.dumps([a.model_dump(mode="json") for a in to_add]),
        )
        if not await self.permissions.update_items(*to_add):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_permissions_adding_error_msg,
                details=agent_details.model_dump(
                    mode="json", exclude_unset=True
                ),
            )

        # Creating knowledge bases
        if knowledge_bases:
            await logger.ainfo(
                self.messages.api_knowledge_bases_create_fmt.format(
                    agent.knowledge_bases
                ),
                data=json.dumps(
                    [kb.model_dump(mode="json") for kb in knowledge_bases]
                ),
            )
            if not await self.knowledge_bases.create_items(knowledge_bases):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=self.messages.api_knowledge_bases_create_error_msg,
                )

        # Creating RAG Configs
        if rag_configs:
            await logger.ainfo(
                self.messages.api_rag_configs_create_fmt.format(agent.rags),
                data=json.dumps(
                    [r.model_dump(mode="json") for r in rag_configs]
                ),
            )
            if not await self.rag_configs.create_items(rag_configs):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=self.messages.api_rag_configs_create_error_msg,
                )

        # TODO: Create an Agent pipeline configuration

        # Return ID
        return {"id": agent.id}

    @router.get(
        "/agents/",
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
        response_model_exclude={
            "__all__": {"rags": {"__all__": {"retrieval"}}}
        },
        response_model=list[AgentGet],
    )
    @router.get(
        "/agents",
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved Agents",
                "content": {"application/json": {"example": {}}},
                "model": list[AgentGet],
            },
        },
        response_model_exclude={
            "__all__": {"rags": {"__all__": {"retrieval"}}}
        },
        response_model=list[AgentGet],
    )
    async def get_agents(
        self,
        ids: list[Uuid] = Query([]),
        featured: bool = Query(False),
        public: bool = Query(True),
        owner: bool = Query(True),
        admin: bool = Query(True),
        shared: bool = Query(True),
    ) -> list[dict[str, Any]]:
        """
        Retrieves all agents visible to the user

        Args:
            ids (list[Uuid]): List of Agent IDs to be retrieved,
                              defaults to an empty list
            featured (bool): Retrieve all featured agents, defaults
                             to True
            public (bool): Retrieve all agents available to the WOG,
                           defaults to True
            owner (bool): Retrieve all agents that user owns, defaults
                          to True
            admin (bool): Retrieve all agents where user is an admin,
                          defaults to True
            shared (bool): Retrieve all agents shared with the user,
                           defaults to True

        Returns:
            list[dict[str, Any]]: Collection of agents
        """
        user_permissions: PermissionsDB
        all_permissions: PermissionsDB
        group_permissions: list[PermissionsDB]

        query_filters: list[Any] = []
        (
            user_permissions,
            all_permissions,
            group_permissions,
        ) = await self.atlas_get_all_user_permissions(self.user.id)

        if any(i for i in [owner, admin, shared]):
            shared_ids: list[Uuid] = []
            scopes: dict[
                Uuid, AccessRoleType
            ] = user_permissions.get_resource_scopes(
                user_permissions.scopes, "agents"
            )

            # User is an owner
            if owner:
                shared_ids.extend(
                    [  # noqa: C416
                        k
                        for k, v in scopes.items()
                        if v == AccessRoleType.owner
                    ]
                )

            # User is an admin
            if admin:
                shared_ids.extend(
                    [  # noqa: C416
                        k
                        for k, v in scopes.items()
                        if v == AccessRoleType.admin
                    ]
                )

            # Shared with user
            if shared:
                shared_ids.extend(
                    [  # noqa: C416
                        k
                        for k, v in scopes.items()
                        if v
                        not in [
                            AccessRoleType.owner,
                            AccessRoleType.admin,
                        ]
                    ]
                )

                # Shared with group user belongs to
                for g in group_permissions:
                    shared_ids.extend(
                        [  # noqa: C416
                            i
                            for i in g.get_resource_scopes(g.scopes, "agents")
                        ]
                    )

            if ids:
                shared_ids = list(set(ids) & set(shared_ids))

            query_filters.append(In(AgentDB.id, shared_ids))

        # Retrieve all publicly owned Agents
        if public:
            scopes: list[str] = list(
                all_permissions.get_resource_scopes(
                    all_permissions.scopes, "agents"
                )
            )
            if ids:
                scopes = list(set(ids) & set(scopes))
            query_filters.append(
                And(
                    AgentDB.release_state.state == DeploymentState.production,
                    In(AgentDB.id, scopes),
                )
            )

        # Retrieve featured Agents
        if featured:
            query_filters.append(AgentDB.featured == True)  # noqa: E712

        return [
            a.model_dump()
            for a in await self.agents.get_items(
                And(
                    *[
                        AgentDB.meta.deleted == None,  # noqa: E711
                        Or(*query_filters),
                    ]
                ),
                sort=[(AgentDB.featured, -1), (AgentDB.meta.created, -1)],
            )
        ]

    @router.post(
        "/agents/clones/",
        response_model=IDResponse,
        status_code=status.HTTP_201_CREATED,
        include_in_schema=False,
    )
    @router.post(
        "/agents/clones",
        response_model=IDResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            **AtlasRouters.response("created_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    async def clone_agent(
        self,
        agent_details: AgentClonePost,
        clone: Uuid = Query(),
    ) -> dict[str, str]:
        """
        Clones an existing agent to create a new agent

        Args:
            agent_details (AgentClonePost): Details for clone an agent
            clone (Uuid): Denotes the original agent ID that the
                          configuration is being cloned from

        Returns:
            dict[str, str]: Generated Agent ID
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        original_agent: AgentDB = await self.atlas_get_agent(clone)

        # TODO: Validate Chat details
        # 1. AI Model should be supported
        # 2. Chat parameters should be supported

        # TODO: Validate Settings
        # 1. Settings should be supported

        # Check that the Agency exists
        if agent_details.agency:
            try:
                await self.atlas_validate_agency(agent_details.agency)
            except AtlasAPIException as e:
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=e.message,
                    details=e.details,
                ) from e

        # Check if url compatible string is unique
        # if not use the Bot ID
        agent_id: Uuid = AgentDB.atlas_get_uuid()
        slug: str = agent_id
        if agent_details.name:
            slug: str = await self.atlas_generate_url_slug(
                agent_id, agent_details.name
            )

        # Check all files exists
        if agent_details.files:
            try:
                await self.atlas_validate_files(agent_details.files)
            except AtlasAPIException as e:
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=e.message,
                    details=e.details,
                ) from e

        # Handle Knowledge Bases:
        # TODO: 1. Clone existing knowledge bases,
        #  including duplicating files
        knowledge_bases: list[KnowledgeBaseDB] = []
        if original_agent.knowledge_bases:
            pass
        # Validate and create additional knowledge bases
        if agent_details.knowledge_bases:
            try:
                await self.atlas_validate_knowledge_bases(
                    agent_details.knowledge_bases
                )
            except AtlasAPIException as e:
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=e.message,
                    details=e.details,
                ) from e
            knowledge_bases: list[
                KnowledgeBaseDB
            ] = self.atlas_create_knowledge_base(
                agent_details.knowledge_bases, agent=agent_id
            )

        # Handle RAG Configs:
        # Duplicate existing RAG Configs
        rag_configs: list[RAGConfigDB] = []
        if original_agent.rags:
            rag_configs.extend(
                self.atlas_create_rag_configs(
                    await self.atlas_get_rag_configs(clone), agent=agent_id
                )
            )
        # Validate RAG Configs and create new RAG configs to be added
        if agent_details.rags:
            try:
                self.atlas_validate_rag_configs(agent_details.rags)
            except AtlasAPIException as e:
                raise AtlasAPIException(
                    status_code=e.status_code,
                    message=e.message,
                    details=agent_details.model_dump(
                        mode="json", exclude_unset=True
                    ),
                ) from e
            rag_configs.extend(
                self.atlas_create_rag_configs(
                    agent_details.rags, agent=agent_id
                )
            )

        # Merge the chat configuration
        chat: AgentChatConfig = original_agent.chat
        if agent_details.chat:
            chat = AgentChatConfig(
                **{
                    **chat.model_dump(),
                    **agent_details.chat.model_dump(exclude_unset=True),
                }
            )

        # Clone the Agent
        agent: AgentDB = AgentDB.create_schema(
            user=self.user.id,
            uid=agent_id,
            resource_type="agents",
            location=str(self.environ.project.pub_url)
            + f"latest/agents/{agent_id}",
            version=1,
            **{
                **original_agent.model_dump(
                    exclude={
                        "id",
                        "ownership",
                        "release_state",
                        "sharing",
                        "knowledge_bases",
                        "rags",
                        "files",
                        "chat",
                        "meta",
                        "modifications",
                    }
                ),
                **agent_details.model_dump(
                    exclude_unset=True,
                    exclude={
                        "files",
                        "chat",
                        "ownership",
                        "knowledge_bases",
                        "rags",
                    },
                ),
                "chat": chat,
                "files": original_agent.files + agent_details.files,
                "knowledge_bases": [kb.id for kb in knowledge_bases],
                "rags": [r.id for r in rag_configs],
                "release_state": AgentReleaseState(),
                "sharing": self.atlas_generate_agent_sharing(slug),
                "clone": clone,
            },
        )

        # Validate ownership details
        agent.generate_ownership(agent_details.ownership)
        await self.atlas_validate_ownership(
            release_state=agent.release_state.state,
            visibility=agent.ownership.visibility,
            users=list(agent.atlas_users()),
            groups=list(agent.atlas_groups()),
            details=agent_details.model_dump(mode="json", exclude_unset=True),
        )

        # Insert into Database
        await logger.ainfo(
            self.messages.api_agents_create_fmt.format(agent.id),
            data=agent.model_dump_json(),
        )
        if not await self.agents.create_item(agent):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_create_error_msg,
                details=agent_details.model_dump(
                    mode="json", exclude_unset=True
                ),
            )

        # Updating all the permissions
        to_add: list[PermissionsDB] = await self.atlas_add_permissions(
            self.atlas_generate_agent_permissions(agent)
        )
        await logger.ainfo(
            self.messages.api_agents_permissions_adding_fmt.format(agent.id),
            data=json.dumps([a.model_dump(mode="json") for a in to_add]),
        )
        if not await self.permissions.update_items(*to_add):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_permissions_updating_error_msg,
                details=agent_details.model_dump(
                    mode="json", exclude_unset=True
                ),
            )

        # Updating knowledge bases references
        if knowledge_bases:
            await logger.ainfo(
                self.messages.api_knowledge_bases_create_fmt.format(
                    agent.knowledge_bases
                ),
                data=json.dumps(
                    [kb.model_dump(mode="json") for kb in knowledge_bases]
                ),
            )
            if not await self.knowledge_bases.create_items(knowledge_bases):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=self.messages.api_knowledge_bases_create_error_msg,
                )

        # Creating RAG Configs
        if rag_configs:
            await logger.ainfo(
                self.messages.api_rag_configs_create_fmt.format(agent.rags),
                data=json.dumps(
                    [r.model_dump(mode="json") for r in rag_configs]
                ),
            )
            if not await self.rag_configs.create_items(rag_configs):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=self.messages.api_rag_configs_create_error_msg,
                )

        # TODO: Create an Agent pipeline configuration

        # Return ID
        return {"id": agent.id}

    @router.get(
        "/agents/all/",
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
        response_model=list[AgentBriefGet],
    )
    @router.get(
        "/agents/all",
        status_code=status.HTTP_200_OK,
        response_model=list[AgentBriefGet],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved all Agents",
                "example": {"application/json": []},
                "model": list[AgentBriefGet],
            }
        },
    )
    async def get_all_agents(
        self, deleted: bool = False
    ) -> list[dict[str, Any]]:
        """
        Retrieves all Agents created, only accessible to superusers

        Args:
            deleted (bool): Flag that indicates if deleted Agents
                            should be included, defaults to False

        Returns:
            list[dict[str, Any]]: List of all created Agents
        """

        # TODO: Add superuser validation via dependencies
        # Validates if user is a superuser
        if not self.user.superuser:
            raise AtlasPermissionsException(
                message=self.messages.api_agents_superuser_view_error_msg,
                user=self.user.id,
            )

        filters: list[Any] = []
        if not deleted:
            filters.append(
                AgentDB.meta.deleted == None  # noqa: E711
            )
        return [
            agent.model_dump(
                include={
                    "id",
                    "name",
                    "description",
                    "agency",
                    "files",
                    "sharing",
                    "featured",
                    "meta",
                }
            )
            for agent in await self.agents.get_items(
                *filters,
                sort=[(AgentDB.featured, -1), (AgentDB.meta.created, -1)],
            )
        ]

    @router.get(
        "/agents/counts/",
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
        response_model=AgentCount,
    )
    @router.get(
        "/agents/counts",
        status_code=status.HTTP_200_OK,
        response_model=AgentCount,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved Agent counts",
                "content": {"application/json": {"example": {}}},
                "model": AgentCount,
            },
        },
    )
    async def get_agents_counts(self) -> AgentCount:
        """
        Retrieves a count of all 4 types of Agents visible to the user.

        Returns:
            AgentCount: count of all Agents visible to the user
        """

        user_permissions: PermissionsDB
        all_permissions: PermissionsDB
        group_permissions: list[PermissionsDB]

        (
            user_permissions,
            all_permissions,
            group_permissions,
        ) = await self.atlas_get_all_user_permissions(self.user.id)

        # Public agents count
        public_agents = await AgentDB.find(
            And(
                In(
                    AgentDB.id,
                    list(
                        all_permissions.get_resource_scopes(
                            all_permissions.scopes, "agents"
                        )
                    ),
                ),
                AgentDB.release_state.state == DeploymentState.production,
                AgentDB.meta.deleted == None,  # noqa: E711
            )
        ).count()

        # Owner, Admin, Shared counts
        permissions: list[PermissionsDB] = await self.atlas_get_permissions(
            ids=[self.user.id], p_type=PermissionsType.user
        )
        scopes: dict[
            Uuid, AccessRoleType
        ] = user_permissions.get_resource_scopes(
            user_permissions.scopes, "agents"
        )

        # Owner count
        owner_agents = await AgentDB.find(
            And(
                In(
                    AgentDB.id,
                    [
                        k
                        for k, v in scopes.items()
                        if v == AccessRoleType.owner
                    ],
                ),
                AgentDB.meta.deleted == None,  # noqa: E711
            )
        ).count()

        # Admin count
        admin_agents = await AgentDB.find(
            And(
                In(
                    AgentDB.id,
                    [
                        k
                        for k, v in scopes.items()
                        if v == AccessRoleType.admin
                    ],
                ),
                AgentDB.meta.deleted == None,  # noqa: E711
            )
        ).count()

        # Shared count
        groups: list[PermissionsDB] = await self.atlas_get_permissions(
            ids=permissions[0].groups, p_type=PermissionsType.group
        )

        shared_agents = await AgentDB.find(
            And(
                In(
                    AgentDB.id,
                    [
                        k
                        for k, v in scopes.items()
                        if v
                        not in [AccessRoleType.owner, AccessRoleType.admin]
                    ]
                    + [
                        i
                        for g in groups
                        for i in g.get_resource_scopes(g.scopes, "agents")
                    ],
                ),
                AgentDB.meta.deleted == None,  # noqa: E711
            )
        ).count()

        return AgentCount(
            public=public_agents,
            owner=owner_agents,
            admin=admin_agents,
            shared=shared_agents,
        )

    @router.put(
        "/agents/{agent_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/agents/{agent_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def update_agent(
        self,
        agent_id: Uuid,
        agent_details: AgentPut,
        response: Response,
    ) -> Response:
        """
        Updates an existing agent's Configuration

        Args:
            agent_id (Uuid): ID of the agent
            agent_details (agentPut): agent details to be updated
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If agent does not exist
        """
        # Perform validation on the agent's configuration

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        # Retrieve existing agent
        agent: AgentDB = await self.atlas_get_agent(agent_id)

        # TODO: Validate Chat details
        # 1. AI Model should be supported
        # 2. Chat parameters should be supported

        # TODO: Validate Settings
        # 1. Settings should be supported

        # Check that the Agency exists
        if agent_details.agency:
            try:
                await self.atlas_validate_agency(agent_details.agency)
            except AtlasAPIException as e:
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=e.message,
                    details=e.details,
                ) from e

        # Check all files exists
        if agent_details.files:
            try:
                await self.atlas_validate_files(agent_details.files)
            except AtlasAPIException as e:
                raise AtlasAPIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message=e.message,
                    details=e.details,
                ) from e

        # Merge configuration
        update: AgentDB = agent.update_schema(
            user=self.user.id,
            version=agent.meta.version + 1,
            **agent_details.model_dump(exclude_unset=True),
        )

        # Insert into Database
        await logger.ainfo(
            self.messages.api_agents_update_fmt.format(agent.id),
            data=update.model_dump_json(),
        )
        if not await self.agents.replace_item(update):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_update_error_msg,
                details=agent_details.model_dump(mode="json"),
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get(
        "/agents/{agent_id}/",
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
        response_model=AgentGet,
        response_model_exclude={"rags": {"__all__": {"retrieval"}}},
    )
    @router.get(
        "/agents/{agent_id}",
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved Agent",
                "content": {"application/json": {"example": {}}},
                "model": AgentGet,
            },
            **AtlasRouters.response("404_not_found_error"),
        },
        response_model=AgentGet,
        response_model_exclude={"rags": {"__all__": {"retrieval"}}},
    )
    async def get_agent(self, agent_id: Uuid | str) -> dict[str, Any]:
        """
        Retrieves an existing Agent

        Args:
            agent_id (Uuid | str): ID of the Agent

        Returns:
            dict[str, Any]: Agent configuration retrieved

        Raises:
            AtlasAPIException: Agent does not exist
        """
        agent: AgentDB = await self.atlas_get_agent(agent_id, deleted=True)
        return agent.model_dump()

    @router.delete(
        "/agents/{agent_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/agents/{agent_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("deleted_response"),
            **AtlasRouters.response("404_not_found_error"),
            **AtlasRouters.response("422_invalid_deletion_error"),
        },
    )
    async def delete_agent(
        self,
        agent_id: Uuid,
        response: Response,
    ) -> Response:
        """
        Deletes an existing agent

        Args:
            agent_id (Uuid): ID of the agent
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: Agent does not exist
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        # Retrieve the existing agent and associated Knowledge Bases
        agent: AgentDB = await self.atlas_get_agent(agent_id)
        kbs: list[KnowledgeBaseDB] = await self.atlas_get_knowledge_bases(
            agent_id
        )
        rag_configs: list[RAGConfigDB] = await self.atlas_get_rag_configs(
            agent_id
        )

        # TODO: Prevent deletion of Agent if pipeline is running

        # Clear all KB embeddings
        await logger.ainfo(
            self.messages.api_knowledge_bases_delete_all_embeddings_fmt.format(
                agent.id
            )
        )
        try:
            await self.atlas_delete_knowledge_base_embeddings(
                agent,
                rag_configs,
                kbs,
                logger,
            )
        except AtlasAPIException:
            raise

        await logger.ainfo(
            self.messages.api_knowledge_bases_delete_fmt.format(
                [kb.id for kb in kbs]
            ),
            data=json.dumps([kb.model_dump(mode="json") for kb in kbs]),
        )
        if kbs:  # noqa: SIM102
            if not await self.knowledge_bases.delete_items(
                KnowledgeBaseDB.agent == agent_id,
            ):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=self.messages.api_knowledge_bases_delete_error_msg,
                )

        # Delete RAG Configs
        await logger.ainfo(
            self.messages.api_rag_configs_delete_fmt.format(
                [r.id for r in rag_configs]
            ),
            data=json.dumps([r.model_dump(mode="json") for r in rag_configs]),
        )
        if rag_configs:  # noqa: SIM102
            if not await self.rag_configs.delete_items(
                RAGConfigDB.agent == agent_id,
            ):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=self.messages.api_rag_configs_delete_error_msg,
                )

        # Deletes the hardcopy files
        if agent.files:
            await asyncio.gather(
                *(self.atlas_delete_file(file) for file in agent.files)
            )
        if kbs:
            await self.atlas_delete_knowledge_base_files(kbs)

        # Delete permissions rights
        to_delete: list[PermissionsDB] = await self.atlas_delete_permissions(
            self.atlas_generate_agent_permissions(agent)
        )
        if to_delete:
            await logger.ainfo(
                self.messages.api_agents_permissions_deleting_fmt.format(
                    agent_id
                ),
                data=json.dumps(
                    [p.model_dump(mode="json") for p in to_delete]
                ),
            )
            if not await self.permissions.update_items(*to_delete):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=self.messages.api_agents_permissions_updating_error_msg,
                    details=agent.model_dump(mode="json"),
                )

        # TODO: Delete RAG Pipeline Config

        # Perform soft deletion
        agent.delete_schema(user=self.user.id)

        # Update Database
        await logger.ainfo(
            self.messages.api_agents_delete_fmt.format(agent.id),
            data=agent.model_dump_json(),
        )
        if not await self.agents.replace_item(agent):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_delete_error_msg,
                details=agent.model_dump(mode="json"),
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.put(
        "/agents/{agent_id}/ownership/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/agents/{agent_id}/ownership",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def update_agent_ownership(
        self, agent_id: Uuid, details: AgentOwnershipPut, response: Response
    ) -> Response:
        """
        Updates the ownership details of the Agent

        Args:
            agent_id (Uuid): ID of the Agent
            details (AgentOwnershipPut): Ownership details of the Agent
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If the Agent does not exist
        """

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        delete: list[Permissions]
        add: list[Permissions]

        agent: AgentDB = await self.atlas_get_agent(agent_id)
        new: AgentDB = agent.model_copy(deep=True)
        new.ownership = Ownership(
            resource_key=agent.ownership.resource_key, **details.model_dump()
        )

        # Validate new ownership details
        await self.atlas_validate_ownership(
            release_state=agent.release_state.state,
            visibility=details.visibility,
            users=list(new.atlas_users()),
            groups=list(new.atlas_groups()),
            details=details.model_dump(mode="json", exclude_unset=True),
        )

        # Generating changes between current and new ownership details
        delete, add = agent.compare_ownership(
            curr=agent.ownership,
            new=new.ownership,
            ownership_resource=self.ownership_resource,
            augment_allow=self.augment_allow,
        )

        # Validate ownership modifications against these rules:
        #   1. Only owners and admins can modify permissions
        #   2. Admins cannot modify owner permissions
        resource_role: AccessRoleType = await self.atlas_get_ownership_role(
            self.user.id, agent.ownership
        )
        self.atlas_validate_permissions_matrix(
            self.user.id, resource_role, delete, add
        )

        # Updating Agent ownership details
        updated: AgentDB = agent.update_schema(
            user=self.user.id,
            version=agent.meta.version + 1,
            **{"ownership": new.ownership},
        )
        await logger.ainfo(
            self.messages.api_agents_ownership_update_fmt.format(agent.id),
            data=updated.model_dump_json(),
        )
        if not await self.agents.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_update_error_msg,
                details=details.model_dump(mode="json", exclude_unset=True),
            )

        # Updating permissions
        to_update: list[
            PermissionsDB
        ] = await self.atlas_consolidate_permissions(delete, add)
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

    @router.put(
        "/agents/{agent_id}/sharing/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/agents/{agent_id}/sharing",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
            **AtlasRouters.response("409_duplicated_entry_error"),
        },
    )
    async def update_agent_sharing(
        self, agent_id: Uuid, details: AgentSharingPut, response: Response
    ) -> Response:
        """
        Updates the Agent's sharing details

        Args:
            agent_id (Uuid): ID of the Agent
            details (AgentSharingPut): Details of the Agent
            response (Response): FastAPI response

        Returns:
            Response: FastAPI Response
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        agent: AgentDB = await self.atlas_get_agent(agent_id)

        # URL slug should be a new value otherwise it will be regenerated
        if details.url_path == agent.sharing.url_path:
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_agents_url_slug_no_updates_error_msg,
                details=details.model_dump(mode="json", exclude_unset=True),
            )

        # Check if URL slug is already taken
        slug: str = await self.atlas_generate_url_slug(
            agent_id, details.url_path
        )
        if slug == agent_id:
            raise AtlasAPIException(
                status_code=status.HTTP_409_CONFLICT,
                message=self.messages.api_agents_url_slug_taken_error_msg,
                details=details.model_dump(mode="json", exclude_unset=True),
            )

        # Updating Agent details
        updated: AgentDB = agent.update_schema(
            user=self.user.id,
            version=agent.meta.version + 1,
            **{"sharing": self.atlas_generate_agent_sharing(slug)},
        )
        await logger.ainfo(
            self.messages.api_agents_sharing_update_fmt.format(agent.id),
            data=updated.model_dump_json(),
        )
        if not await self.agents.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_update_error_msg,
                details=details.model_dump(mode="json", exclude_unset=True),
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.put(
        "/agents/{agent_id}/default/pipelines/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/agents/{agent_id}/default/pipelines",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    async def update_agent_default_pipeline(
        self, agent_id: Uuid, details: AgentRAGPipelinePut, response: Response
    ) -> Response:
        """
        Updates the Agent's RAG default pipeline details

        Args:
            agent_id (Uuid): ID of the Agent
            details (AgentRAGPipelinePut): Details of the Agent
            response (Response): FastAPI response

        Returns:
            Response: FastAPI Response
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.atlas.environ.loggers["api"])
        )

        agent: AgentDB = await self.atlas_get_agent(agent_id)

        # Validate default pipeline
        try:
            self.atlas_validate_default_pipeline(
                details.default_pipeline,
                agent.rags,
            )
        except AtlasAPIException as e:
            raise AtlasAPIException(
                status_code=e.status_code,
                message=e.message,
                details=details.model_dump(mode="json", exclude_unset=True),
            ) from e

        # Updating Agent details
        updated: AgentDB = agent.update_schema(
            user=self.user.id,
            version=agent.meta.version + 1,
            **{
                "default_pipeline": details.default_pipeline,
            },
        )
        await logger.ainfo(
            self.messages.api_agents_rag_pipelines_update_fmt.format(agent.id),
            data=updated.model_dump_json(),
        )
        if not await self.agents.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_agents_update_error_msg,
                details=details.model_dump(mode="json", exclude_unset=True),
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response
