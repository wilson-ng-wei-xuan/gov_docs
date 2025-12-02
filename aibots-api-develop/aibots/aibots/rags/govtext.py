from __future__ import annotations

import io
import json
from datetime import datetime
from enum import Enum
from io import BytesIO
from logging import Logger
from typing import Any

import httpx
from atlas.boto3.services import S3Service
from atlas.httpx import HttpxService
from atlas.schemas import ExecutionState, State, Uuid
from pydantic import AnyUrl, BaseModel, ConfigDict

from aibots.models import (
    Agent,
    Chunk,
    EmbeddingsMetadata,
    KnowledgeBase,
    RAGConfig,
    RAGPipelineStages,
    RAGPipelineStatus,
)

from .base import AtlasRAGException, RAGEngine

__all__ = (
    "GovTextJobStatus",
    "GovTextMetadata",
    "GovTextChunkConfig",
    "GovTextParseConfig",
    "GovTextIngestPipelineConfig",
    "GovTextJobResponse",
    "GovTextEngine",
)


class GovTextJobStatus(str, Enum):
    """
    Class for representing GovText Job Status

    Attributes:
        SCHEDULED (str): Scheduled state
        PENDING (str): Pending state
        RUNNING (str): Running state
        PAUSED (str): Paused state
        CANCELLING (str): Cancelling state
        CANCELLED (str): Cancelled state
        COMPLETED (str): Completed state
        FAILED (str): Failed state
        CRASHED (str): Crashed state
    """

    SCHEDULED = "SCHEDULED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CRASHED = "CRASHED"

    def get_aibots_state(self) -> ExecutionState:
        """
        Convenience function for retrieving associated
        AIBots state

        Returns:
            ExecutionState
        """
        return ExecutionState[self.value.lower()]

    def is_successful(self) -> bool:
        """
        Indicates if the current state is successful

        Returns:
            bool: State is successful
        """
        return self.value in [GovTextJobStatus.COMPLETED]

    def is_error(self) -> bool:
        """
        Indicates if the current state is successful

        Returns:
            bool: State is error
        """
        return self.value in [
            GovTextJobStatus.CRASHED,
            GovTextJobStatus.FAILED,
            GovTextJobStatus.CANCELLED,
            GovTextJobStatus.CANCELLING,
        ]

    def is_running(self) -> bool:
        """
        Indicates if the current state is running

        Returns:
            bool: State is error
        """
        return self.value in [
            GovTextJobStatus.SCHEDULED,
            GovTextJobStatus.PENDING,
            GovTextJobStatus.RUNNING,
            GovTextJobStatus.PAUSED,
        ]


class GovTextMetadata(BaseModel):
    """
    Metadata class for storing GovText metadata

    Attributes:
        dataset_id (Uuid): ID of the GovText dataset
        upsert_document_ids (dict[str, Uuid]): IDs of the documents
                                               inserted, defaults to
                                               an empty dictionary
        job_id (Uuid): ID of the Job
        failed_documents (dict[str, Uuid]): Documents that failed to
                                            parse, defaults to an empty
                                            dictionary
    """

    dataset_id: str
    upsert_document_ids: dict[str, str] = {}
    job_id: str
    failed_documents: dict[str, str] = {}


class GovTextChunkConfig(BaseModel):
    """
    Base model for chunk model

    Attributes:
        chunk_strategy (str | None): label for chunk strategies
        chunk_size (int | None): chunk size
        chunk_overlap (int | None): chunk overlap
        separators (list[str]): list of separators to split chunks
    """

    chunk_strategy: str | None = None
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    separators: list[str] = []


class GovTextParseConfig(BaseModel):
    """
    Base Model for parsing

    Attributes:
        output_format (str): Format of parsing output,
                             defaults to None
    """

    output_format: str | None = None


class GovTextIngestPipelineConfig(BaseModel):
    """
    GovText Pipeline ingestion config

    Attributes:
        chunk (GovTextChunkConfig): Chunking config details
        parse (GovTextParseConfig): Parsing config details
    """

    chunk: GovTextChunkConfig = GovTextChunkConfig()
    parse: GovTextParseConfig = GovTextParseConfig()


class GovTextJobResponse(BaseModel):
    """
    Base model for GovText job response

    Attributes:
        job_id (str): id of job
        dataset_id (str): id of dataset
        job_type (str): type of job
        status (GovTextJobStatus): status of GovText pipeline
        start_time (datetime): start time of the pipeline
        end_time (datetime | None): end time of the pipeline
        upserted_document_ids (list[str]): list of document ids
        failed_upsert_documents (list[str]): list of failed document ids
        deleted_document_ids (list[str]): list of deleted document ids
        failed_delete_documents (list[str]):
            list of failed delete documents
        ingest_pipeline (GovTextIngestPipelineConfig):
            configuration for GovText pipeline
    """

    model_config: ConfigDict = ConfigDict(extra="allow")

    job_id: str
    dataset_id: str
    job_type: str
    status: GovTextJobStatus
    start_time: datetime
    end_time: datetime | None = None
    upserted_document_ids: list[str] = []
    failed_upsert_documents: list[dict[str, Any]] = []
    deleted_document_ids: list[str] = []
    failed_delete_documents: list[dict[str, Any]] = []
    ingest_pipeline: GovTextIngestPipelineConfig = (
        GovTextIngestPipelineConfig()
    )


class GovTextEngine(RAGEngine, HttpxService):
    """
    Class for wrapping embeddings functionality provided from GovText.
    Here an embeddings collection corresponds to the entire knowledge
    base for a bot.

    Attributes:
        service (Any): Wrapper of the service
        args (Sequence[Any]): Arguments to initialise the
                              service with
        kwargs (dict[str, Any]): Keyword Arguments to
                                    initialise the service with
        _active (bool): Flag to indicate if the Service is active
        is_async (bool): Flag to indicate if the Service is asynchronous

        type (str): Name of the Engine, defaults to "govtext"
        endpoint (str): Integration endpoint
    """  # noqa: E501

    type: str = "govtext"
    required: list[str] = [
        "datasetId",
        "topK",
    ]

    def __init__(self, *args: Any, **kwargs: Any):
        """
        Creates a GovTextEngine

        Args:
            *args (Any): Additional arguments for the service
            **kwargs (Any): Additional keyword arguments for the service

        """  # noqa: E501
        super().__init__(*args, **kwargs)
        self.endpoint: str = AnyUrl(self.kwargs.pop("endpoint"))
        self.is_async: bool = True
        self.s3_service: S3Service = self.kwargs.pop("s3_service")
        self.s3_bucket: str = self.kwargs.pop("s3_bucket")

    async def __atlas_ainit__(self, logger: Logger | None = None):
        """
        Asynchronous initialisation logic for the Embeddings engine

        Args:
            logger (Logger | None): Logger for logging details

        Returns:
            Any: Closing output
        """
        await super().__atlas_ainit__(logger)

    async def __atlas_aclose__(
        self,
        logger: Logger | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Logic for shutting down the Service

        Args:
             logger (Optional[Logger]): Logger for logging details
             *args (Any): Arguments for Shutting down the Service
             **kwargs (Any): Keyword Arguments for Shutting down
                             the Service

        Returns:
            Any: Shutdown logic
        """
        await super().__atlas_aclose__()

    async def atlas_init_pipeline(
        self,
        agent: Agent,
        rag_config: RAGConfig,
    ) -> None:
        """
        Initialises the RAG pipeline

        Args:
            agent (Agent): Agent details
            rag_config (RAGConfig): RAG Config to be run

        Returns:
            None
        """
        # TODO: check that it doestn initialise twice,
        #       add unit test to make sure initialise
        #       function properly differentiates
        # TODO scenerio test using postman
        if not rag_config.initialised(self.required):
            resp: httpx.Response = await self.service.post(
                str(self.endpoint) + "datasets",
                headers=self.headers,
            )
            if resp.status_code != 200:
                raise AtlasRAGException(
                    status_code=resp.status_code,
                    message="Failed to create dataset",
                    details={
                        "response": resp.text,
                        "url": str(self.endpoint) + "datasets",
                    },
                )
            rag_config.retrieval.update(
                {
                    "datasetId": resp.json().get("dataset_id"),
                    "topK": rag_config.config.get("topK", 10),
                }
            )
        rag_config.previous = rag_config.current
        rag_config.current = State(state=ExecutionState.running)
        # TODO: update rag config current and prev,
        #       current to running,
        #       prev to pending outside of initialised

    async def atlas_aembed(
        self,
        agent: Agent,
        rag_config: RAGConfig,
        knowledge_base: KnowledgeBase,
        content: BytesIO | str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> EmbeddingsMetadata | None:
        """
        Convenience function for wrapping embeddings generation
        with the GovText

        Args:
            agent (Agent): Agent details
            rag_config (RAGConfig): RAG config details
            knowledge_base (KnowledgeBase): Knowledge Base Details
            content (BytesIO | str | None): File details to be embedded,
                                         defaults to None
            *args (Any): Arguments for running the embeddings
                         pipeline
            **kwargs: Keyword arguments for running the embeddings
                      pipeline

        Returns:
            EmbeddingsMetadata | None: Generated retrieval configuration
                                       and embeddings metadata
        """  # noqa: E501

        # Trigger flow to generate embeddings on document
        if isinstance(content, str):
            files = [("files", (knowledge_base.name, content))]
        else:
            files = [("files", (knowledge_base.name, content.getvalue()))]
        rag_json = {
            "chunk_strategy": rag_config.config.get(
                "chunk_strategy", "FIXED_SIZE"
            ),
            "chunk_size": rag_config.config.get("chunk_size", 300),
            "chunk_overlap": rag_config.config.get("chunk_overlap", 20),
            "chunk_separators": rag_config.config.get("chunk_seperator", []),
            "parse_output_format": rag_config.config.get(
                "parse_output_format", "TEXT"
            ),
        }

        dataset_id = rag_config.retrieval.get("datasetId")
        resp: httpx.Response = await self.service.patch(
            str(self.endpoint) + f"datasets/{dataset_id}",
            headers=self.headers,
            data=rag_json,
            files=files,
        )

        # Validate output from GovText by checking status code
        #       and whether file is in upsert_document_ids
        if resp.status_code != 200 or not resp.json()[
            "upsert_document_ids"
        ].get(knowledge_base.name):
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Failed to create embedding",
                details={
                    "response": resp.text,
                    "url": str(self.endpoint) + "datasets",
                    "params": rag_json,
                },
            )

        govtext_metadata: GovTextMetadata = GovTextMetadata(**resp.json())

        # Structure return values
        embeddings: EmbeddingsMetadata = EmbeddingsMetadata(
            current=State(state=ExecutionState.completed),
            metadata={
                "document_id": govtext_metadata.upsert_document_ids.get(
                    knowledge_base.name
                ),
                "dataset_id": govtext_metadata.dataset_id,
                "job_id": govtext_metadata.job_id,
                "status": ExecutionState.scheduled,
            },
        )

        # the job_id received from GovText
        # and agent id is used as the s3_key in the bucket
        s3_bucket_key = (
            f"schedule/minute/"
            f"{govtext_metadata.job_id}_{agent.id}_govtext.json"
        )
        rag_pipeline_status: RAGPipelineStatus = RAGPipelineStatus(
            rag_config=rag_config.id,
            agent=agent.id,
            knowledge_base=knowledge_base.id,
            type=RAGPipelineStages.external,
            status=ExecutionState.scheduled,
            results={
                "metadata": {
                    "job_id": govtext_metadata.job_id,
                    "knowledge_bases": [
                        knowledge_base.id,
                    ],
                }
            },
        )

        self.s3_service.service.upload_fileobj(
            io.BytesIO(
                json.dumps(
                    {
                        "sqs": "sqs-sitezapp-aibots-rag-status-govtext",
                        "payload": rag_pipeline_status.model_dump(mode="json"),
                    }
                ).encode("utf-8")
            ),
            self.s3_bucket,
            s3_bucket_key,
        )

        return embeddings

    async def atlas_aquery(
        self,
        prompt: str,
        agent: Agent,
        rag_config: RAGConfig,
        knowledge_bases: list[KnowledgeBase],
        *args: Any,
        **kwargs: Any,
    ) -> list[Chunk]:
        """
        Convenience function for wrapping embeddings query
        with the GovText

        Args:
            prompt (str): Text to query on
            agent (Agent): Agent details
            rag_config (RAGConfig): RAG config details
            knowledge_bases (list[KnowledgeBase]): Knowledge Bases
                                                   to query
            *args (Any): Arguments for querying the
                         RAG pipeline
            **kwargs (Any): Keyword arguments for querying
                            the RAG pipeline

        Returns:
            list[Chunk]: Query results
        """
        kb_map: dict[str, Uuid] = {kb.name: kb.id for kb in knowledge_bases}
        payload: dict[str, Any] = {
            "dataset_id": rag_config.retrieval.get("datasetId"),
            "text": prompt,
            "top_k": rag_config.retrieval.get("topK", 5),
            **kwargs,
        }
        resp: httpx.Response = await self.service.post(
            str(self.endpoint) + "query", json=payload
        )
        resp_json = resp.json()

        # Validate output
        if not resp.is_success:
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Unable to execute query flow",
                details={
                    "response": resp.text,
                    "url": str(self.endpoint) + "/query",
                    "params": payload,
                },
            )

        chunks: list[Chunk] = []
        for chunk in resp_json.get("chunks"):
            document_name: str | None = chunk.get("metadata", {}).get(
                "document_name"
            )
            chunks.append(
                Chunk(
                    id=chunk.get("metadata", {}).get("chunk_id"),
                    source=document_name,
                    chunk=chunk.get("content"),
                    knowledge_base=kb_map.get(document_name),
                    score=chunk.get("metadata", {}).get("score"),
                    document_id=chunk.get("metadata", {}).get("document_id"),
                    chunk_size=chunk.get("metadata", {}).get("chunk_size"),
                )
            )
        return chunks

    async def atlas_adelete_embeddings(
        self,
        agent: Agent,
        rag_config: RAGConfig,
        knowledge_bases: list[KnowledgeBase],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Deleting a collection from GovText

        Args:
            agent (Agent): Agent details
            rag_config (RAGConfig): RAG config details
            knowledge_bases (list[KnowledgeBase]): Knowledge Bases
            *args (Any): Arguments for deleting embeddings from a
                         collection in the RAG pipeline
            **kwargs (Any): Keyword arguments for deleting
                            embeddings from a collection in the
                            RAG pipeline

        Returns:
            Dict[str, Any]:
        """
        document_ids_to_delete = [
            kb.embeddings[rag_config.id].metadata.get("document_id")
            for kb in knowledge_bases
        ]
        if not document_ids_to_delete:
            raise AtlasRAGException(
                status_code=404,
                message="document ids not found "
                "in knowledge base's embeddings",
            )
        dataset_id: str = rag_config.retrieval.get("datasetId")
        resp: httpx.Response = await self.service.patch(
            str(self.endpoint) + f"datasets/{dataset_id}",
            headers=self.headers,
            data={"delete_document_ids": document_ids_to_delete},
        )

        # Validate output
        if not resp.is_success:
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Unable to execute delete flow",
                details={
                    "response": resp.text,
                    "url": str(self.endpoint) + f"datasets/{dataset_id}",
                },
            )

        # Clear collection data from documents
        for kb in knowledge_bases:
            kb.delete_embeddings(rag_config.id)

        await super().atlas_adelete_embeddings(
            agent,
            rag_config,
            knowledge_bases,
            *args,
            **kwargs,
        )

        return resp.json()

    async def atlas_alist(self, *args: Any, **kwargs: Any) -> Any:
        """
        Lists all the embedding collections

        Args:
            *args (Any): Arguments for listing the collections
                         within the RAG pipeline
            **kwargs (Any): Keyword arguments for listing the
                            collections within the RAG pipeline

        Returns:
            Any: Collection details
        """
        raise NotImplementedError("Not implemented")

    async def atlas_aembed_bulk(
        self,
        agent: Agent,
        rag_config: RAGConfig,
        knowledge_bases: list[KnowledgeBase],
        content: BytesIO | str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> list[EmbeddingsMetadata | None]:
        """
        Runs the embeddings pipeline asynchronously

        Args:
            agent (Agent): Agent details
            rag_config (RAGConfig): RAG config details
            knowledge_bases (
                list[KnowledgeBase]
            ): Knowledge Bases to be embedded
            content (BytesIO | str | None): Content details to
                                            be embedded, defaults
                                            to None
            *args (Any): Arguments for running the embeddings
                         pipeline
            **kwargs: Keyword arguments for running the embeddings
                      pipeline

        Returns:
            list[EmbeddingsMetadata | None]:
                Generated retrieval configuration and embeddings
                metadata
        """
        raise NotImplementedError("Not implemented")

    async def atlas_aupdate(self, *args: Any, **kwargs: Any) -> Any:
        """
        Convenience function for updating an embeddings collection
        on GovText

        Args:
            *args (Any): Arguments for updating an embeddings collection
            **kwargs (Any): Keyword arguments for updating an embeddings
                            collection

        Returns:
            Any: Updated results
        """
        raise NotImplementedError("Not implemented")

    async def atlas_adelete_embeddings_collection(
        self,
        rag_config: RAGConfig,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Deletes the entire embeddings collection

        Args:
            rag_config (RAGConfig): RAG config details
            *args (Any): Arguments for deleting embedding collection
                            when the RAG pipeline is deleted
            **kwargs (Any): Keyword arguments for deleting
                            embedding collection when the
                            RAG pipeline is deleted

        Returns:
            Any: Deletion details
        """
        dataset_id: str = rag_config.retrieval.get("datasetId")
        resp: httpx.Response = await self.service.delete(
            str(self.endpoint) + f"datasets/{dataset_id}",
            headers=self.headers,
        )

        # Validate output
        if not resp.is_success:
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Unable to execute delete collection flow",
                details={
                    "response": resp.text,
                    "url": str(self.endpoint) + f"datasets/{dataset_id}",
                },
            )

    async def get_job_status(self, job_id: str) -> GovTextJobResponse | None:
        """
        Checks the status of GovText Job

        Args:
            job_id (str): id for the existing job

        Returns:
            GovTextJobResponseModel
        """
        response: httpx.Response = await self.service.get(
            str(self.endpoint) + f"jobs/{job_id}", headers=self.headers
        )

        if response.is_success:
            return GovTextJobResponse(**response.json())

        raise AtlasRAGException(
            status_code=response.status_code,
            message=response.json()["error"]["message"],
        )
