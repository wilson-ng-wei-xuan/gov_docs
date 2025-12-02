from __future__ import annotations

from typing import Type

from beanie import Document

from .uam import LoginDB
from .files import FileDB
from .knowledge_bases import KnowledgeBaseDB
from .rag_configs import RAGConfigDB
from .agents import AgentDB
from .chats import ChatDB, ChatMessageDB
from .rags import RAGPipelineDB

__doc__ = """
Aggregates all implemented document models for MongoDB
"""


__all__ = (
    "models",
    "LoginDB",
    "FileDB",
    "KnowledgeBaseDB",
    "RAGConfigDB",
    "AgentDB",
    "ChatDB",
    "ChatMessageDB",
    "RAGPipelineDB",
)


models: list[Type[Document]] = [
    LoginDB,
    FileDB,
    KnowledgeBaseDB,
    RAGConfigDB,
    AgentDB,
    ChatMessageDB,
    ChatDB,
    RAGPipelineDB,
]
