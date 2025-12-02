from typing import Type

from beanie import Document

from .knowledge_bases import KnowledgeBaseDB
from .rag_configs import RAGConfigDB
from .agents import (
    AgentChatConfig,
    AgentSharing,
    Agent,
    AgentDB,
    AgentReleaseState,
)
from .chats import ChatDB, ChatMessageDB
from .files import FileDB
from .scim import (
    ScimReference,
    ScimGroupExtensions,
    ScimGroup,
    ScimGroupDB,
    ScimName,
    ScimAddress,
    ScimUserExtensions,
    ScimUser,
    ScimUserDB,
)
from .permissions import PermissionsDB
from .uam import LoginDB, OtpDB, RoleDB, UserLoginGet, APIKeyDB

__doc__ = """
Aggregates all implemented document models for MongoDB
"""

__all__ = (
    "models",
    "FileDB",
    "KnowledgeBaseDB",
    "RAGConfigDB",
    "AgentSharing",
    "AgentReleaseState",
    "AgentChatConfig",
    "Agent",
    "AgentDB",
    "ChatMessageDB",
    "ChatDB",
    "PermissionsDB",
    "APIKeyDB",
    "OtpDB",
    "LoginDB",
    "RoleDB",
    "ScimGroupDB",
    "ScimUserDB",
    "ScimReference",
    "ScimGroupExtensions",
    "ScimGroup",
    "ScimGroupDB",
    "ScimName",
    "ScimAddress",
    "ScimUserExtensions",
    "ScimUser",
    "ScimUserDB",
    "UserLoginGet",
)

models: list[Type[Document]] = [
    FileDB,
    APIKeyDB,
    OtpDB,
    LoginDB,
    RoleDB,
    PermissionsDB,
    ScimUserDB,
    ScimGroupDB,
    ChatMessageDB,
    ChatDB,
    KnowledgeBaseDB,
    RAGConfigDB,
    AgentDB,
]
