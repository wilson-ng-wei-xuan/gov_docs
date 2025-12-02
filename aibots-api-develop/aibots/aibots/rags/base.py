from __future__ import annotations

from abc import abstractmethod
from io import BytesIO
from typing import Any

from atlas.exceptions import AtlasException
from atlas.services import Service

from aibots.models import (
    Agent,
    Chunk,
    EmbeddingsMetadata,
    KnowledgeBase,
    RAGConfig,
)

__all__ = (
    "AtlasRAGException",
    "RAGEngine",
)


class AtlasRAGException(AtlasException):
    """
    Atlas RAG Exception class

    Attributes:
        status_code (int | str): REST API status code
        message (str): Brief message summarising error
        details (dict[str, Any]): More details on the error
    """

    def __init__(
        self,
        status_code: int | str,
        message: str,
        details: dict[str, Any] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.details = details or {}

    def exception(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Method for structuring the error return format

        Args:
            *args (Any): Args for the function
            **kwargs (Any): Kwargs for the function

        Returns:
            Any: Structure error format
        """
        return {
            "status_code": self.status_code,
            "message": self.message,
            "details": self.details,
        }


class RAGEngine(Service):
    """
    Generic service for managing a RAG pipeline

    Attributes:
        service (Any): Wrapper of the service
        args (Sequence[Any]): Arguments to initialise the
                              service with
        kwargs (dict[str, Any]): Keyword Arguments to
                                    initialise the service with
        _active (bool): Flag to indicate if the Service is active
        is_async (bool): Flag to indicate if the Service is asynchronous

        type (str): Name of the RAG pipeline, defaults to an empty string
        required (list[str]): List of required keys to facilitate
                              interaction with the RAG Service, defaults
                              to an empty list
    """

    type: str = ""
    required: list[str] = []

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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
            agent (Agent): Agent configuration
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

    @abstractmethod
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

    @abstractmethod
    async def atlas_aupdate(self, *args: Any, **kwargs: Any) -> Any:
        """
        Makes updates to an embeddings collection asynchronously

        Args:
            *args (Any): Arguments for updating a collection in the
                         RAG pipeline
            **kwargs (Any): Keyword arguments for updating a
                            collection in the RAG pipeline

        Returns:
            Any: Updated collection details
        """

    @abstractmethod
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
            agent (Agent): Agent configuration
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
        # If all the embeddings from an embeddings collection are
        # deleted, we automatically clear the associated embeddings
        # collection
        if set(agent.knowledge_bases) == {kb.id for kb in knowledge_bases}:
            await self.atlas_adelete_embeddings_collection(
                rag_config, *args, **kwargs
            )
            rag_config.retrieval.clear()

    @abstractmethod
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
