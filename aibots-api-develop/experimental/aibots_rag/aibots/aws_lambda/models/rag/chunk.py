from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Union

from pydantic import BaseModel


class ChunkingOptions(Enum):
    FIXED = "fixed"
    DATAFRAME = "dataframe"
    SEMANTIC = "semantic"


class FixedChunker(BaseModel):
    """
    Model for Fixed Chunker
    Attributes:
        type (Literal["fixed"]): type of chunking
        chunk_size (int): size of chunk
        separator (str): string used as separator
        chunk_overlap (int): chunk size overlap
    """

    type: Literal["fixed"]
    chunk_size: int
    separator: str
    chunk_overlap: int


class DataframeChunker(BaseModel):
    """
    Model for Dataframe Chunking
    Attributes:
        type (Literal["dataframe"]): type of chunking
        chunk_size (int): size of chunk
        min_cluster_size (int): minimum number of clusters
        analyze_full_excel (str): boolean to determine how to analyse excel
    """

    type: Literal["dataframe"]
    chunk_size: int
    min_cluster_size: int
    # TODO: make this into boolean if possible
    analyze_full_excel: Union[Literal["False"], Literal["True"]]


class SemanticChunker(BaseModel):
    """
    Model for Semantic Chunking
    Attributes:
        type (Literal["semantic"]): type of chunking
        chunk_size (int): size of chunk
    """

    type: Literal["semantic"]
    chunk_size: int


class ChunkDocument(BaseModel):
    """
    Model for Chunk Document
    Attributes:
        text (str): text of chunk document
    """

    text: str
    chunk: int
    page_number: int
    last_update_date: str


class SQSRAGChunker(BaseModel):
    """
    Model for Chunker
    Attributes:
        config (Union[SemanticChunker, DataframeChunker, FixedChunker]):
            configuration on which chunker to run
        inputs (List[ChunkDocument]):
            documents to chunk
        results (List[Dict[str,Any]]):
            chunk results
    """

    config: Union[SemanticChunker, DataframeChunker, FixedChunker] | None
    inputs: List[ChunkDocument] | None
    results: List[Dict[str, Any]]


ChunkerConfig = Union[FixedChunker, DataframeChunker, SemanticChunker]
