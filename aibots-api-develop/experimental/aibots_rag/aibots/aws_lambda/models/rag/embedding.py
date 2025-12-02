from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal

from pydantic import BaseModel


class EmbeddingOptions(str, Enum):
    """
    enum for embedding options
    """

    COHERE = "cohere"


class EmbedderConfig(BaseModel):
    """
    model for embedder configuration
    Attributes:
        model (str): name of embedding model
    """

    type: EmbeddingOptions
    model: Literal["cohere.embed-english-v3"]


# TODO: firm up typings for embedder configurations, inputs and results


class SQSRAGEmbedder(BaseModel):
    """
    Model for RAG Embedder
    Attributes:
        config (Dict[str,Any]): configuration for embedder
        inputs (List[Dict[str,Any]]): inputs for embeddings to be created
        results (List[Dict[str,Any]]): results from embedder
    """

    config: Dict[str, Any] | None
    inputs: List[Dict[str, Any]] | None
    results: List[Dict[str, Any]] | None
