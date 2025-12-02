from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from boto3 import client
from pydantic import BaseModel, HttpUrl

from aibots.aws_lambda.models.rag import (
    ChunkingOptions,
    EmbeddingOptions,
    ParseableFileType,
    StoreOptions,
)


class SQSParseUrl(BaseModel):
    docx: HttpUrl
    pptx: HttpUrl
    xlsx: HttpUrl
    txt: HttpUrl
    html: HttpUrl
    pdf: HttpUrl
    csv: HttpUrl


class SQSChunkUrl(BaseModel):
    fixed: HttpUrl
    dataframe: HttpUrl
    semantic: HttpUrl


class SQSEmbedUrl(BaseModel):
    cohere: HttpUrl


class SQSStoreUrl(BaseModel):
    opensearch: HttpUrl


class SQSStatusUrl(BaseModel):
    main: HttpUrl


class RAGSQSRouter:
    """
    class for wrapping boto3 SQS handlers and routing for RAG pipeline
    """

    # TODO: compress message senders to singular method,
    #       use discriminator to route

    def __init__(self) -> None:
        self.status: SQSStatusUrl = SQSStatusUrl(
            main=os.environ["PROJECT_RAG_STATUS__SQS"]
        )

        self.parse: SQSParseUrl = SQSParseUrl(
            html=os.environ["PROJECT_RAG_PARSE__HTML__URL"],
            docx=os.environ["PROJECT_RAG_PARSE_DOCX__SQS"],
            xlsx=os.environ["PROJECT_RAG_PARSE_XLSX__SQS"],
            csv=os.environ["PROJECT_RAG_PARSE_CSV__SQS"],
            pdf=os.environ["PROJECT_RAG_PARSE_PDF__SQS"],
            txt=os.environ["PROJECT_RAG_PARSE_TXT__SQS"],
            pptx=os.environ["PROJECT_RAG_PARSE_PPTX__SQS"],
        )
        self.chunk: SQSChunkUrl = SQSChunkUrl(
            fixed=os.environ["PROJECT_RAG_CHUNK_FIXED__SQS"],
            dataframe=os.environ["PROJECT_RAG_CHUNK_DATAFRAME__SQS"],
            semantic=os.environ["PROJECT_RAG_CHUNK_SEMANTIC__SQS"],
        )
        self.embed: SQSEmbedUrl = SQSEmbedUrl(
            cohere=os.environ["PROJECT_RAG_EMBED__SQS"]
        )
        self.store: SQSStoreUrl = SQSStoreUrl(
            opensearch=os.environ["PROJECT_RAG_STORE__SQS"]
        )

        self.sqs = client("sqs", region_name="ap-southeast-1")
        self.logger = logging
        self.logger.getLogger().setLevel(logging.INFO)

    def send_message_to_rag_status_sqs(self, message: Dict[str, Any]) -> None:
        """sends message to rag status queue
        Args:
            message (Dict[str, Any]): body payload to be sent
        Returns:
            None
        """
        self.logger.info("Sending message to RAG Status SQS")
        self.sqs.send_message(
            QueueUrl=self.rag_status_url, MessageBody=json.dumps(message)
        )

    def send_message_to_rag_embed_sqs(
        self, embed: EmbeddingOptions, message: Dict[str, Any]
    ) -> None:
        """sends message to rag embed queue
        Args:
            message (Dict[str, Any]): body payload to be sent
        Returns:
            None
        """
        self.logger.info("Sending message to RAG Embed SQS")
        self.sqs.send_message(
            QueueUrl=self.embed.model_dump()[embed.value],
            MessageBody=json.dumps(message),
        )

    def send_message_to_rag_parse_sqs(
        self, parse: ParseableFileType, message: Dict[str, Any]
    ) -> None:
        """sends message to rag embed queue
        Args:
            message (Dict[str, Any]): body payload to be sent
        Returns:
            None
        """
        self.logger.info("Sending message to RAG Embed SQS")
        self.sqs.send_message(
            QueueUrl=self.parse.model_dump()[parse.value],
            MessageBody=json.dumps(message),
        )

    def send_message_to_rag_chunk_sqs(
        self, chunk: ChunkingOptions, message: Dict[str, Any]
    ) -> None:
        """sends message to rag embed queue
        Args:
            message (Dict[str, Any]): body payload to be sent
        Returns:
            None
        """
        self.logger.info("Sending message to RAG Embed SQS")
        self.sqs.send_message(
            QueueUrl=self.chunk.model_dump()[chunk.value],
            MessageBody=json.dumps(message),
        )

    def send_message_to_rag_store_sqs(
        self, store: StoreOptions, message: Dict[str, Any]
    ) -> None:
        """sends message to rag embed queue
        Args:
            message (Dict[str, Any]): body payload to be sent
        Returns:
            None
        """
        self.logger.info("Sending message to RAG Embed SQS")
        self.sqs.send_message(
            QueueUrl=self.store.model_dump()[store.value],
            MessageBody=json.dumps(message),
        )
