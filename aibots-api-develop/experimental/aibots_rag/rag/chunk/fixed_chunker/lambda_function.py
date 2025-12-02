from __future__ import annotations

import json
from typing import List

from aibots.models.rags.api import (
    ExecutionState,
    RAGPipelineStages,
    RAGPipelineStatus,
)
from aibots.models.rags.base import (
    RAGPipelineEnviron,
    RAGPipelineExecutor,
)
from aibots.models.rags.internal import (
    AIBotsPipelineMessage,
    ChunkResult,
    Page,
    ParseResult,
    SQSMessageRecord,
)
from boto3 import client
from langchain_text_splitters.character import CharacterTextSplitter
from pydantic import validate_call


class FixedChunker(RAGPipelineExecutor):
    def __call__(self, *args, **kwargs) -> RAGPipelineStatus:
        try:
            parsed: ParseResult = self.previous_result
            config = self.message.pipeline.config["chunk"]
            chunk_size, chunk_overlap, separator = (
                config["chunk_size"],
                config["chunk_overlap"],
                config["separator"],
            )
            chunk_results: List[Page] = []
            chunk_count: int = 0
            for doc in parsed.pages:
                # For each existing chunk, re-chunk based on semantic chunker
                list_of_text = doc.text
                if chunk_size < len(list_of_text):
                    chunks = self.fixed_size_chunker(
                        list_of_text, chunk_size, chunk_overlap, separator
                    )

                else:
                    chunks = [list_of_text]
                # Re-populate the data with appropriate chunks
                for chunk in chunks:
                    chunk_page = Page(**doc.model_dump())
                    chunk_page.chunk = chunk_count
                    chunk_page.text = chunk
                    chunk_count += 1
                    chunk_results.append(chunk_page)

            self.message.results.append(ChunkResult(chunks=chunk_results))
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.completed,
                knowledge_base=self.message.knowledge_base,
                error=None,
                results=json.dumps(
                    [
                        chunk_result.model_dump()
                        for chunk_result in chunk_results
                    ]
                ),
                type=RAGPipelineStages.chunking,
            )
        except Exception as e:
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.failed,
                knowledge_base=self.message.knowledge_base,
                error=str(e),
                results=None,
                type=RAGPipelineStages.chunking,
            )

    def next(self) -> None:
        stringify = json.dumps(self.message.model_dump(mode="json"))
        # send out stringify message via sqs
        self.sqs.send_message(
            QueueUrl=str(self.environ.project_rag_store.url),
            MessageBody=stringify,
        )

    def fixed_size_chunker(self, text, chunk_size, chunk_overlap, separator):
        """
        returns:
            docs (list of langchain object): chunks
        """
        text_splitter = CharacterTextSplitter(
            separator=separator,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        docs = text_splitter.create_documents([text])
        list_of_chunks = [doc.page_content for doc in docs]
        return list_of_chunks


environ: RAGPipelineEnviron = RAGPipelineEnviron()
sqs = client("sqs", region_name="ap-southeast-1")


@validate_call
def lambda_handler(event: AIBotsPipelineMessage, context):
    # Event body is a list of chunks with metadata
    failed: List[SQSMessageRecord] = []
    for i, message in enumerate(event.pipeline_messages):
        executor: RAGPipelineExecutor = FixedChunker(message, sqs, environ)
        status: RAGPipelineStatus = executor()
        if status.error:
            # takes in failed sqs message record
            failed.append(event.records[i])
            continue
        executor.send_status(status=status)
        executor.next()

    return {
        "batchItemFailures": [
            {"itemIdentifier": fail.message_id} for fail in failed
        ]
    }
