from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from atlas.schemas import AtlasID, Uuid
from atlas.utils import generate_curr_datetime
from pydantic import Field

__doc__ = """
Data models for RAG pipelines, includes reusable fields 
and MongoDB schema models
"""

__all__ = (
    "RAGPipelineRunConfig",
    "RAGPipeline",
)


class RAGPipelineRunConfig(AtlasID):
    """
    Representation of the RAG Pipeline run configuration

    Attributes:
        id (Uuid): Pipeline run job ID
        knowledge_bases (list[Uuid]): Knowledge bases to be triggered,
                                      defaults to an empty list
        rag_configs (list[Uuid]): List of RAG Config IDs, defaults to an
                                  empty list
        timestamp (datetime): Created timestamp of the pipeline run
                              configuration
    """

    knowledge_bases: list[Uuid] = []
    rag_configs: list[Uuid] = []
    timestamp: Annotated[
        datetime, Field(default_factory=generate_curr_datetime)
    ]


class RAGPipeline(AtlasID):
    """
    Representation of an Agent's latest RAG pipeline run configuration and
    associated status

    Attributes:
        id (Uuid): ID of the Agent
        config (RAGPipelineRunConfig): Latest pipeline run config
        status (Any): Latest pipeline run status, defaults to None
    """

    config: RAGPipelineRunConfig
    status: Any = None
