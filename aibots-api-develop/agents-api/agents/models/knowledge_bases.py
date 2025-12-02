from __future__ import annotations

from aibots.models import KnowledgeBase
from beanie import Document

__doc__ = """
Contains all data models associated with Knowledge Bases
"""


__all__ = [
    "KnowledgeBaseDB",
]


class KnowledgeBaseDB(KnowledgeBase, Document):
    """
    Schema of a KnowledgeBase to be stored in MongoDB

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

    class Settings:
        name = "knowledge_bases"
