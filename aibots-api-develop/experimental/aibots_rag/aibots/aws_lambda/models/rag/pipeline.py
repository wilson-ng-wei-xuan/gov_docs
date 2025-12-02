from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .chunk import ChunkDocument, ChunkerConfig
from .embedding import EmbedderConfig
from .parse import ParseConfig, ParsedPage
from .store import StoreConfig, StoreDocument


class ExecutionState(str, Enum):
    """
    RAG pipeline status

    pending = The pipeline has been created but not scheduled for execution
    scheduled = The pipeline has been scheduled for execution
    running = The pipeline is currently executing
    cancelling = The pipeline has been cancelled but clean up has
                 not been completed
    cancelled = The pipeline has been cancelled
    completed = The pipeline has been completed
    failed = The pipeline has failed because of a software issue
    crashed = The pipeline failed because of an infrastructure issue
    """

    pending = "pending"
    scheduled = "scheduled"
    running = "running"
    cancelling = "cancelling"
    cancelled = "cancelled"
    completed = "completed"
    failed = "failed"
    crashed = "crashed"


class SQSRAGConfigs(BaseModel):
    """
    Model for configurations
    Attributes:
        parse (ParseConfig): configurations for parser
        chunk (ChunkerConfig): configurations for chunker
        embed (EmbedderConfig): configurations for embedder
        store (StoreConfig): configurations for storer
    """

    parse: ParseConfig
    chunk: ChunkerConfig
    embed: EmbedderConfig
    store: StoreConfig


class SQSRAGResults(BaseModel):
    """
    Model for RAG results in SQS message
    Attributes:
        parse (Optional[List[ParsedPage]] | None): list of parsed pages
        chunk (Optional[List[ChunkDocument]] | None): list of chunks
        embed (Optional[List[StoreDocument]] | None):
            list of store documents created
        store (Optional[Dict[str,Any]]): embedding bulk insert response status
    """

    parse: Optional[List[ParsedPage]] = None
    chunk: Optional[List[ChunkDocument]] = None
    embed: Optional[List[StoreDocument]] = None
    store: Optional[Dict[str, Any]] = None


class SQSRAGPipelineMessage(BaseModel):
    """
    Model for rag pipeline sqs message
    Attributes:
        bot_id (str): id of bot
        document_id (str): id of document
        process_start_datetime (str): datetime of when process starts
        process_end_datetime (str): datetime of when process ends
        process_status (str): status of pipeline
        error_message (Dict[str, Any]| None):
            error object if process fails, else None
        configs (Dict[str,Any]): configurations for each node of the pipeline
        results (Dict[str,Any]): results for each node of the pipeline
    """

    # TODO: compress setters to singular method, use discriminator to route
    # TODO: rename document_id, remove last updated, execution status TBC
    bot_id: str
    document_id: str
    process_start_datetime: str
    process_last_updated: str
    process_end_datetime: str
    error_message: Dict[str, Any]
    execution_status: ExecutionState
    configs: SQSRAGConfigs
    results: SQSRAGResults

    def set_parse_results(self, results: List[Dict[str, Any]]) -> None:
        """
        adds parse message into sqs message:
        Args:
            results (List[Dict[str,Any]]): result from parser
        """
        self.results.parse = [ParsedPage(**result) for result in results]
        self.__update_last_updated()

    def set_chunk_results(self, results: List[Dict[str, Any]]) -> None:
        """
        adds chunk message into sqs message
        Args:
            results (List[Dict[str,Any]]): result from chunker
        """
        self.results.chunk = [ChunkDocument(**result) for result in results]
        self.__update_last_updated()

    def set_embed_results(self, results: List[Dict[str, Any]]) -> None:
        """
        adds embed message into sqs message
        Args:
            results (List[Dict[str,Any]]): result from embed
        """
        self.results.embed = [StoreDocument(**result) for result in results]
        self.__update_last_updated()

    def add_store_results(self, result: Dict[str, Any]) -> None:
        """
        adds embed message into sqs message
        Args:
            result (Dict[str,Any]): result from store
        """
        self.results.store = result

    def set_execution_status(self, status: ExecutionState) -> None:
        """
        sets execution status for pipeline
        Args:
            status (ExecutionState): state of the pipeline
        """
        self.execution_status = status

    def __update_last_updated(self) -> None:
        """
        updates last updated
        """
        self.process_last_updated = datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
