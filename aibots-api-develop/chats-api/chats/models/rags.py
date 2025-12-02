from __future__ import annotations

from aibots.models import RAGPipeline
from beanie import Document

__doc__ = """
Data models for RAG pipelines, includes reusable fields 
and MongoDB schema models
"""

__all__ = ("RAGPipelineDB",)


class RAGPipelineDB(RAGPipeline, Document):
    """
    Schema of a Agent to be stored in MongoDB

    Attributes:
        id (Uuid): ID of the pipeline
        agent (Uuid): ID of the associated Agent
        knowledge_bases (list[Uuid]): IDs of the associated Knowledge Bases
        status (StateTransitions): Generic representation that consolidates
                                   the state transitions
        embeddings (Embeddings): Embeddings and associated data generated
                                 via the embeddings process
        meta (Meta): Meta information associated with the resource
    """

    class Settings:
        name: str = "rag_pipelines"
