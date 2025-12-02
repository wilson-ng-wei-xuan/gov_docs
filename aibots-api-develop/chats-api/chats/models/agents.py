from __future__ import annotations

from aibots.models import Agent
from beanie import Document

__doc__ = """
Contains all data structures associated with Launchpad Agents
"""

__all__ = ("AgentDB",)


class AgentDB(Agent, Document):
    """
    Schema of a Agent to be stored in MongoDB

    Attributes:
        id (Uuid): UUID string
        name (constr): Name of the Agent
        description (constr): Brief description of the Agent
        featured (bool): Indicates if the Agent is featured,
                         defaults to False
        clone (Uuid | None): Indicates if the Agent is cloned
        sharing (AgentSharing): Sharing details of the Agent
        ownership (Ownership | None): Ownership details
        files (list[Uuid] | None): Non-embedded files associated
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
        default_pipeline (Uuid | None): Default RAG pipeline, defaults to
                                        None
        rags (list[Uuid]): RAG configuration for the Agent, defaults to an
                           empty list
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

    class Settings:
        name: str = "agents"
