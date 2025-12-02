from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from atlas.schemas import AtlasID, DescriptiveName, ExecutionState, State, Uuid
from atlas.utils import generate_curr_datetime
from pydantic import AnyUrl, BaseModel, ConfigDict, Field

__doc__ = """
Contains all data models associated with Knowledge Bases
"""


__all__ = [
    "DataSourceType",
    "DataSource",
    "EmbeddingsMetadata",
    "StorageType",
    "KnowledgeBaseStorage",
    "KnowledgeBase",
]


class DataSourceType(str, Enum):
    """
    Types of supported data sources

    Attributes:
        file (str): Text, image and other static files
        stream (str): Video and audio stream
        govkb (str): Gov KB virtual filesystem
        website (str): Website to be scraped
    """

    file = "file"
    stream = "stream"
    govkb = "govkb"
    website = "website"


class StorageType(str, Enum):
    """
    Support storage types

    Attributes:
        aibots (str): AI Bots Content Management System
        govkb (str): Gov KB virtual filesystem
    """

    aibots = "aibots"
    govkb = "govkb"


class DataSource(DescriptiveName):
    """
    Represents the raw data and its associated metadata

    Attributes:
        name (str): Name of the Data Source, this is the
                    filename, url link, folder link to access
                    the data.
        description (str): Brief description of the Data Source
        type (DataSourceType): Types of supported data sources,
                               defaults to file
        content (Uuid | AnyUrl | str | None): Data content,
                                              defaults to None
        metadata (dict[str, Any]): Additional metadata to be
                                   appended together with the
                                   Data Source, defaults to
                                   an empty dictionary
    """

    model_config: ConfigDict = ConfigDict(extra="allow", use_enum_values=True)

    type: DataSourceType = DataSourceType.file
    content: Uuid | AnyUrl | str | None = None
    metadata: dict[str, Any] = {}


class EmbeddingsMetadata(BaseModel):
    """
    Embeddings and associated data generated via the embeddings process
    that the RAG engine can utilise to reference and query the embeddings
    from

    Attributes:
        current (State): Current execution state, defaults to pending
        metadata (dict[str, Any]): Metadata details, defaults to an
                                   empty dictionary
    """

    model_config: ConfigDict = ConfigDict(extra="allow")

    current: State = State(state=ExecutionState.pending)
    metadata: dict[str, Any] = {}


class KnowledgeBaseStorage(BaseModel):
    """
    References to the storage locations of the actual files

    Attributes:
        type (StorageType): Storage Type of the Knowledge Base,
                            defaults to aibots
        location (AnyUrl | Uuid | str | None): Reference link to
                                               the stored Knowledge
                                               Base, defaults to None
        value (Uuid | str | None): Value of the stored Knowledge Base,
                                   defaults to None
    """

    model_config: ConfigDict = ConfigDict(
        extra="allow",
        use_enum_values=True,
    )

    type: StorageType = StorageType.aibots
    location: AnyUrl | Uuid | str | None = None
    value: Uuid | str | None = None


class KnowledgeBase(DataSource, AtlasID):
    """
    Knowledge Base that represents data uploaded with embeddings generated

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

    agent: Uuid | None = None
    storage: KnowledgeBaseStorage = KnowledgeBaseStorage()
    embeddings: dict[str, EmbeddingsMetadata] = {}
    timestamp: datetime = Field(default_factory=generate_curr_datetime)

    def delete_embeddings(self, rag_config: str) -> None:
        """
        Clears all embeddings references of a pipeline type

        Args:
            rag_config (str): RAG config ID

        Returns:
            None
        """
        del self.embeddings[rag_config]
