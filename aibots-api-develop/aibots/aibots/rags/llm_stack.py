from __future__ import annotations

from io import BytesIO
from logging import Logger
from typing import Any, Dict

import httpx
from atlas.httpx import HttpxService
from atlas.schemas import ExecutionState, State, Uuid
from pydantic import AnyUrl, BaseModel, ConfigDict, Field

from aibots.models import (
    Agent,
    Chunk,
    EmbeddingsMetadata,
    KnowledgeBase,
    RAGConfig,
)

from .base import AtlasRAGException, RAGEngine

__all__ = ("LLMStackEngine",)


class LLMStackMetadata(BaseModel):
    """
    Metadata class for storing LLM Stack metadata

    Attributes:
        url (AnyUrl): Presigned S3 URL
        s3_url (AnyUrl): S3 Object URL to store file
        key (str): Flow key
        access_key (str): AWS Access Key
        security_token (str): AWS security token
        policy (str): AWS S3 policy
        signature (str): Signature of the Lambda function to be invoked
    """

    model_config: ConfigDict = ConfigDict(populate_by_name=True)

    url: AnyUrl
    s3_url: AnyUrl = Field(alias="s3_object_url")
    key: str
    access_key: str = Field(alias="AWSAccessKeyId")
    security_token: str = Field(alias="x-amz-security-token")
    policy: str
    signature: str


class LLMStackEngine(RAGEngine, HttpxService):
    """
    Class for wrapping embeddings functionality provided from LLM Stack.
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

        type (str): Name of the Engine, defaults to "llmstack"
        endpoint (str): Integration endpoint
    """  # noqa: E501

    type: str = "llmstack"
    required: list[str] = ["collection", "user"]

    def __init__(self, *args: Any, **kwargs: Any):
        """
        Creates an LLMStackEngine

        Args:
            *args (Any): Additional arguments for the service
            **kwargs (Any): Additional keyword arguments for the service

        """  # noqa: E501
        super().__init__(*args, **kwargs)
        self.endpoint: str = self.kwargs.pop("endpoint")
        self.is_async: bool = True

    async def __atlas_ainit__(self, logger: Logger | None = None):
        """
        Asynchronous initialisation logic for the Embeddings engine

        Args:
            logger (Optional[Logger]): Logger for logging details

        Returns:
            Any: Closing output
        """
        await super().__atlas_ainit__(logger)
        self.s3_client: httpx.AsyncClient = httpx.AsyncClient(
            transport=self.kwargs["transport"],
            timeout=self.kwargs["timeout"],
            limits=self.kwargs["limits"],
        )

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
        await self.s3_client.aclose()

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
                    "collection": rag_config.id,
                    "user": rag_config.id,
                }
            )
        rag_config.previous = rag_config.current
        rag_config.current = State(state=ExecutionState.running)

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
        with the LLM stack

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

        flow_id: str = "Flow_LLMS_Vector_Store_Upsert_Documents_83d6fc4e"

        # Retrieve presigned S3 URL
        resp: httpx.Response = await self.service.get(
            self.endpoint + "/v1/flows/upload-file-url",
            params={"flow_id": flow_id, "filename": knowledge_base.name},
        )
        output: Dict[str, Any] = resp.json()

        # Validate output
        if output["status"] != "success":
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Unable to retrieve presigned S3 URL",
                details={
                    "response": resp.text,
                    "url": self.endpoint + "/v1/flows/upload-file-url",
                    "params": {
                        "flow_id": flow_id,
                        "filename": knowledge_base.name,
                    },
                },
            )

        # Upload file to S3
        pipeline_metadata: LLMStackMetadata = LLMStackMetadata(
            **{
                "url": output["data"]["url"],
                "s3_url": output["data"]["s3_object_url"],
                **output["data"]["fields"],
            }
        )
        form: dict[str, Any] = pipeline_metadata.model_dump(
            by_alias=True, exclude={"url", "s3_url"}, mode="json"
        )
        files = {"file": (knowledge_base.name, bytes(content.getvalue()))}
        resp: httpx.Response = await self.s3_client.post(
            pipeline_metadata.url.unicode_string(), data=form, files=files
        )
        if not resp.is_success:
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Unable to upload file to S3 url",
                details={
                    "response": resp.text,
                    "url": pipeline_metadata.url.unicode_string(),
                    "data": form,
                    "filename": knowledge_base.name,
                },
            )

        # Trigger flow to generate embeddings on document
        # TODO: Parameterize some of these configs
        resp: httpx.Response = await self.service.post(
            self.endpoint + "/v1/flows/execute",
            json={
                "flow_id": flow_id,
                "user_id": rag_config.id,
                "inputs": [
                    {
                        "urls": [],
                        "file_urls": [
                            pipeline_metadata.s3_url.unicode_string()
                        ],
                        "separators": ["\n\n"],
                        "chunk_size": 1200,
                        "collection_name": rag_config.id,
                        "number_of_returned_documents": 100,
                    }
                ],
            },
        )

        # Validate output
        output: Dict[str, Any] = resp.json()
        if output["status"] != "success":
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Unable to trigger flow to generate embeddings",
                details={
                    "response": resp.text,
                    "url": self.endpoint + "/v1/flows/execute",
                    "params": {
                        "flow_id": flow_id,
                        "user_id": rag_config.id,
                        "inputs": [
                            {
                                "urls": [],
                                "file_urls": [
                                    pipeline_metadata.s3_url.unicode_string()
                                ],
                                "separators": ["\n\n"],
                                "chunk_size": 1200,
                                "collection_name": rag_config.id,
                                "number_of_returned_documents": 100,
                            }
                        ],
                    },
                },
            )

        # Structure return values and update states
        embeddings: EmbeddingsMetadata = EmbeddingsMetadata(
            current=State(state=ExecutionState.completed),
            metadata=pipeline_metadata.model_dump(
                by_alias=True, exclude={"url", "s3_url"}, mode="json"
            ),
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
        with the LLM stack

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
        flow_id: str = "Flow_LLMS_Vector_Store_Find_Documents_0fe446ce"
        kb_map: dict[str, Uuid] = {kb.name: kb.id for kb in knowledge_bases}
        user: str = rag_config.retrieval["user"]
        collection: str = rag_config.retrieval["collection"]
        json: dict[str, Any] = {
            "flow_id": flow_id,
            "user_id": user,
            "inputs": [
                {
                    "collection_name": collection,
                    "question": prompt,
                }
            ],
        }
        resp: httpx.Response = await self.service.post(
            self.endpoint + "/v1/flows/execute", json=json
        )
        resp_json = resp.json()

        # Validate output
        if not resp.is_success:
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Unable to execute query flow",
                details={
                    "response": resp.text,
                    "url": self.endpoint + "/v1/flows/execute",
                    "params": json,
                },
            )

        chunks: list[Chunk] = []
        for chunk in resp_json.get("data", [{"documents": []}])[0].get(
            "documents", []
        ):
            source: str | None = chunk.get("metadata", {}).get("source")
            score: float | None = chunk.get("metadata", {}).get("score")
            chunks.append(
                Chunk(
                    **{
                        "id": chunk["id"],
                        "chunk": chunk["content"],
                        "knowledgeBase": kb_map.get(source),
                        "source": source,
                        "score": score,
                        "metadata": {
                            "content_type": chunk.get("content_type"),
                            **chunk.get("metadata", {}),
                        },
                    }
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
        Deleting a collection from LLM Stack

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
        flow_id: str = "Flow_LLMS_Vector_Store_Delete_Documents_ad34ccbb"
        user: str = rag_config.retrieval["user"]
        collection: str = rag_config.retrieval["collection"]
        documents: list[str] = [kb.name for kb in knowledge_bases]
        resp: httpx.Response = await self.service.post(
            self.endpoint + "/v1/flows/execute",
            json={
                "flow_id": flow_id,
                "user_id": user,
                "inputs": [
                    {
                        "collection_name": collection,
                        "document_names": documents,
                    }
                ],
            },
        )

        # Validate output
        if not resp.is_success:
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Unable to execute delete flow",
                details={
                    "response": resp.text,
                    "url": self.endpoint + "/v1/flows/execute",
                    "params": {
                        "flow_id": flow_id,
                        "user_id": user,
                        "inputs": [
                            {
                                "collection_name": collection,
                                "document_names": documents,
                            }
                        ],
                    },
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

    async def atlas_alist(
        self,
        collection: str,
        user: str,
        filename: str = None,
        flow_id: str = "Flow_LLMS_Vector_Store_List_Documents_2fbd4efa",
    ) -> Dict[str, Any]:
        """ """

        documents = [filename] if filename else []

        # print("calling LLMstack with:", flow_id, user, collection, documents)
        resp: httpx.Response = await self.service.post(
            self.endpoint + "/v1/flows/execute",
            json={
                "flow_id": flow_id,
                "user_id": user,
                "inputs": [
                    {
                        "collection_name": collection,
                        "document_names": documents,
                    }
                ],
            },
        )

        # Validate output
        if not resp.is_success:
            raise AtlasRAGException(
                status_code=resp.status_code,
                message="Unable to execute listing flow",
                details={
                    "response": resp.text,
                    "url": self.endpoint + "/v1/flows/execute",
                    "params": {
                        "flow_id": flow_id,
                        "user_id": user,
                        "inputs": [
                            {
                                "collection_name": collection,
                                "document_names": documents,
                            }
                        ],
                    },
                },
            )

        return resp.json()

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
        on LLM Stack

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
