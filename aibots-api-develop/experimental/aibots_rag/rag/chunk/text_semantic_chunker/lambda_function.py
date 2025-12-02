import json
import os
from typing import Any, Dict, List

import boto3
from langchain_community.embeddings import BedrockEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
import logging
from aibots.aws_lambda.chunker import RAGChunker
from aibots.aws_lambda.models.rag import SQSRAGPipelineMessage
from aibots.aws_lambda.sqs_router import RAGSQSRouter

from aibots.models.rags.base import RAGPipelineExecutor

from aibots.models.rags.api import ExecutionState, RAGPipelineStages, RAGPipelineStatus

from aibots.models.rags.internal import ChunkResult, Page, ParseResult


class SemanticRAGChunker(RAGPipelineExecutor):
    def __call__(self) -> RAGPipelineStatus:
        try:
            parsed: ParseResult = self.previous_result
            config = self.message.pipeline.config["chunk"]
            chunk_results: List[Page] = []
            chunk_size = config["chunk_size"]
            chunk_count: int = 0
            for doc in parsed.pages:
                chunks = self.semantic_chunker([doc.text], chunk_size)
                for chunk in chunks:
                    chunk_page = Page(**doc.model_dump())
                    chunk_page.chunk = chunk_count
                    chunk_page.text = chunk
                    chunk_count += 1
                    chunk_results.append(chunk_page)
            self.message.results.append(
                ChunkResult(chunks=chunk_results)
            )
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.completed,
                knowledge_base=self.message.knowledge_base,
                error=None,
                results=json.dumps([chunk_result.model_dump()
                                    for chunk_result in chunk_results]),
                type=RAGPipelineStages.chunking
            )
        except Exception as e:
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.failed,
                knowledge_base=self.message.knowledge_base,
                error=str(e),
                results=None,
                type=RAGPipelineStages.chunking
            )

    def semantic_chunker(self, texts: List[str], chunk_size: int) -> List[str]:
        """
        returns:
            docs (list of langchain object): chunks
        """

        # no_of_chunks = 1 if len(text) // chunk_size == 0 else len(text) // chunk_size
        embeddings = BedrockEmbeddings(
            region_name="ap-southeast-1",
            model_id='cohere.embed-english-v3'
        )
        text_splitter = SemanticChunker(
            embeddings, number_of_chunks=chunk_size)

        docs = text_splitter.create_documents(texts)

        list_of_chunks = [doc.page_content for doc in docs]

        return list_of_chunks

    def chunk_docs(self, docs: List[Dict[str, Any]], chunk_size: int) -> List[Dict[str, Any]]:
        df_json_with_metadata = []

        for doc in docs:
            # For each existing chunk, re-chunk based on semantic chunker
            list_of_text = ''.join(doc["text"])

            if chunk_size < len(list_of_text):
                chunks = self.semantic_chunker(list_of_text, chunk_size)

            else:
                chunks = [list_of_text]

            # Re-populate the data with appropriate chunks
            for chunk in chunks:
                doc_copy = doc.copy()
                doc_copy["text"] = chunk
                df_json_with_metadata.append(doc_copy)

        return [{"text": document["text"],
                 **document["metadata"], "chunk": i} for i, document in enumerate(df_json_with_metadata)]

    def next(self) -> None:
        stringify = json.dumps(self.message.model_dump(mode="json"))
        # send out stringify message via sqs
        self.sqs.send_message(QueueUrl=str(self.environ.project_rag_store.url), MessageBody=stringify)


def lambda_handler(event, context):
    chunker = RAGChunker(event=event, context=context, chunker=chunk_docs)
    sqs_router = RAGSQSRouter()
    successes, fails = chunker.run()
    logging.getLogger().setLevel(logging.INFO)
    for _, success in enumerate(successes):
        try:
            message: SQSRAGPipelineMessage = SQSRAGPipelineMessage(
                **success["body"])
            sqs_router.send_message_to_rag_chunk_sqs(
                chunk=message.configs.embed.type, message=message.model_dump())
        except Exception as e:
            fails.append(success)
            logging.error(e)
    failed_message_ids = [{"itemIdentifier": fail["messageId"]}
                          for fail in fails]
    return {"batchItemFailures": failed_message_ids}
