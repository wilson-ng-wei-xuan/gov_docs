from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class StoreOptions(str, Enum):
    """
    enum for store options
    """

    OPENSEARCH = "opensearch"


class StoreDocument(BaseModel):
    """
    Model for store document
    Attributes:
        source (str): s3 bucket source for index
        page_number (str): page number of the source
        last_update_date (str): last modified date
        text (str): raw text of index
        chunk (int): chunk index number
        embedding (List[float]): vector embedding of embedded text
    """

    source: str
    page_number: int
    last_update_date: str
    text: str
    chunk: int
    # set as optional to minimise SQS message size
    embedding: Optional[List[float]] = None


class StoreConfig(BaseModel):
    """
    Model for RAG store configuration
    Attributes:
        host (str): host string
        index_name (str): index name of embedding store
        embedding_type (str): embedding family to use
    """

    type: StoreOptions
    host: str
    index_name: str
    # TODO: make embedding type more comprehensive
    # when other embedding models are introduced
    embedding_type: Literal["cohere"] = "cohere"


class SQSRAGStore(BaseModel):
    """
    Model for RAG store
    Attributes:
        config (SQSRAGStoreConfig):
            configuration to push to documents
        inputs (List[Dict[str,Any]]):
            list of inputs to upload to store
        results (List[Dict[str,Any]]):
            results of uploading to embedding store
    """

    config: StoreConfig
    inputs: List[Dict[str, Any]]
    results: List[Dict[str, Any]]
