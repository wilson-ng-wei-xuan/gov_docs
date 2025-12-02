from __future__ import annotations

import asyncio
import json
from io import BytesIO
from logging import Logger
from typing import Any

import botocore
from atlas.boto3.services import LambdaService
from atlas.schemas import Uuid
from atlas.utils import run_sync_as_async

from aibots.models import (
    Agent,
    Chunk,
    EmbeddingsMetadata,
    KnowledgeBase,
    RAGConfig,
)

from .base import AtlasRAGException, RAGEngine

__all__ = ("AIBotsEngine",)


class AIBotsEngine(RAGEngine, LambdaService):
    """
    Class for wrapping AIBots custom pipeline calls.

    Attributes:
        service (Any): Wrapper of the service
        args (Sequence[Any]): Arguments to initialise the
                              service with
        kwargs (dict[str, Any]): Keyword Arguments to
                                    initialise the service with
        _active (bool): Flag to indicate if the Service is active
        is_async (bool): Flag to indicate if the Service is asynchronous

        type (str): Name of the Engine, defaults to "aibots_aio"
    """  # noqa: E501

    type: str = "aibots"
    required: list[str] = ["index_name", "top_n"]

    def __init__(self, *args: Any, **kwargs: Any):
        """
        Creates an AIBotsEngine

        Args:
            *args (Any): Additional arguments for the service
            **kwargs (Any): Additional keyword arguments for the service

        """  # noqa: E501
        cfg = botocore.config.Config(
            retries={"max_attempts": 0},
            read_timeout=180,
            connect_timeout=180,
        )
        super().__init__(*args, **kwargs, config=cfg)
        self.arn: str = self.kwargs.pop("arn")
        self.s3_bucket: str = self.kwargs.pop("s3_bucket")
        # self.aoss: str = self.kwargs.pop("aoss")
        # self.aoss_collection: str = self.kwargs.pop("aoss_collection")
        self.is_async: bool = False

    def __atlas_init__(self, logger: Logger | None = None):
        """
        Asynchronous initialisation logic for the Embeddings engine

        Args:
            logger (Optional[Logger]): Logger for logging details

        Returns:
            Any: Closing output
        """
        super().__atlas_init__(logger)

    def __atlas_close__(
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
        super().__atlas_close__()

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
        if not rag_config.initialised(self.required):
            rag_config.retrieval.update(
                {
                    # "aoss": self.aoss,
                    # "collection": self.aoss_collection,
                    "index_name": rag_config.id,
                    "top_n": 3,
                }
            )

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
        Runs the embeddings pipeline asynchronously

        Args:
            agent (Agent): Agent details
            rag_config (RAGConfig): RAG config details
            knowledge_base (KnowledgeBase): Knowledge Base
                                            details
            content (BytesIO | str | None): Content details to
                                            be embedded, defaults
                                            to None
            *args (Any): Arguments for running the embeddings
                         pipeline
            **kwargs: Keyword arguments for running the embeddings
                      pipeline

        Returns:
            EmbeddingsMetadata | None: Generated retrieval configuration
                                       and embeddings metadata
        """
        response = await run_sync_as_async(
            self.service.invoke,
            **{
                "FunctionName": self.arn,
                "Payload": json.dumps(
                    {
                        "flow": "upsert",
                        "file_path": f"s3://{self.s3_bucket}/files/"
                        + f"{knowledge_base.content}/{knowledge_base.name}",
                        "index_name": rag_config.id,
                    }
                ),
            },
        )
        output = json.loads(response["Payload"].read())

        # Handle outputs and update Agent retrieval details
        if output["statusCode"] != 200:
            raise AtlasRAGException(
                status_code=output["statusCode"],
                message="Error embedding knowledge base",
                details={
                    "pipeline": self.type,
                    "rag_config": rag_config.id,
                    "knowledge_base": knowledge_base.id,
                    "response": output["body"],
                },
            )

        # Structure return values
        embeddings: EmbeddingsMetadata = EmbeddingsMetadata(
            metadata={"body": output["body"]}
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
        Queries the RAG pipeline asynchronously

        Args:
            prompt (str): Prompt details
            agent (Agent): Agent details
            rag_config (RAGConfig): RAG config details
            knowledge_bases (
                list[KnowledgeBase]
            ): Knowledge bases that form the collection
            *args (Any): Arguments for querying the
                         RAG pipeline
            **kwargs (Any): Keyword arguments for querying
                            the RAG pipeline

        Returns:
            list[Chunk]: Retrieved chunks details
        """
        kb_map: dict[str, Uuid] = {kb.name: kb.id for kb in knowledge_bases}
        output = await run_sync_as_async(
            self.service.invoke,
            **{
                "FunctionName": self.arn,
                "Payload": json.dumps(
                    {
                        "flow": "query",
                        "text": prompt,
                        "index_name": rag_config.retrieval["index_name"],
                    }
                ),
            },
        )

        # Handle outputs and return chunks
        if output["StatusCode"] != 200:
            raise AtlasRAGException(
                status_code=output["StatusCode"],
                message="Error querying knowledge base",
                details={"pipeline": self.type, "response": output},
            )
        payload = json.loads(output["Payload"].read())
        return [
            Chunk(
                id=c["_id"],
                source=c["_source"]["source"],
                chunk=c["_source"]["text"],
                score=c["_score"],
                knowledge_base=kb_map[c["_source"]["source"]],
                metadata={
                    "page": c["_source"]["page_number"],
                    "chunk_id": c["_source"]["chunk"],
                    "last_modified": c["_source"]["last_update_date"],
                },
            )
            for c in json.loads(payload.get("body", "[]"))
        ]

    async def atlas_adelete_embeddings(
        self,
        agent: Agent,
        rag_config: RAGConfig,
        knowledge_bases: list[KnowledgeBase],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Deletes embeddings from an embeddings collection
        asynchronously, if all the knowledge bases are
        specified

        Args:
            agent (Agent): Agent details
            rag_config (RAGConfig): RAG config details
            knowledge_bases (list[KnowledgeBase]): Knowledge Bases
                                                   to be deleted
            *args (Any): Arguments for deleting embeddings from a
                         collection in the RAG pipeline
            **kwargs (Any): Keyword arguments for deleting
                            embeddings from a collection in the
                            RAG pipeline

        Returns:
            Any: Deletion details
        """
        output = await asyncio.gather(
            run_sync_as_async(
                self.service.invoke,
                **{
                    "FunctionName": self.arn,
                    "Payload": json.dumps(
                        {
                            "flow": "delete",
                            "file_path": f"s3://{self.s3_bucket}/files/{kb.content}/{kb.name}",
                            "index_name": rag_config.id,
                        }
                    ),
                },
            )
            for kb in knowledge_bases
        )

        # Validate output errors and clear embeddings
        for o in output:
            if o["StatusCode"] != 200:
                raise AtlasRAGException(
                    status_code=500,
                    message="Error clearing knowledge bases",
                    details={
                        "pipeline": self.type,
                        "rag_config": rag_config.id,
                        "knowledge_bases": [kb.id for kb in knowledge_bases],
                        "response": output["Payload"],
                    },
                )
        for kb in knowledge_bases:
            kb.delete_embeddings(rag_config.id)

        await super().atlas_adelete_embeddings(
            agent,
            rag_config,
            knowledge_bases,
            *args,
            **kwargs,
        )

    async def atlas_aembed_bulk(
        self,
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

    async def atlas_aupdate(self, *args: Any, **kwargs: Any) -> Any:
        """
        Convenience function for updating an embeddings collection

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
        return super().atlas_adelete_embeddings_collection(
            rag_config, *args, **kwargs
        )
