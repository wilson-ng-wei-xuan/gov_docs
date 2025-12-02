from __future__ import annotations

import json
import logging
from pathlib import Path
from io import BytesIO
from typing import Any, Dict, List
from boto3 import client
from pydantic import validate_call
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.html import partition_html
from aibots.aws_lambda.s3_file import S3File
from aibots.aws_lambda.parser import RAGParser
from aibots.aws_lambda.models.rag import SQSRAGPipelineMessage
from aibots.aws_lambda.sqs_router import RAGSQSRouter

from aibots.models.rags.internal import AIBotsPipelineMessage

from aibots.models.rags.internal import SQSMessageRecord

from aibots.models.rags.base import RAGPipelineEnviron, RAGPipelineExecutor

from aibots.models.rags.api import RAGPipelineStatus

from aibots.models.rags.internal import SourceResult

from aibots.models.rags.api import ExecutionState, RAGPipelineStages

from aibots.models.rags.internal import Page, ParseResult


class HTMLParser(RAGPipelineExecutor):
    def __call__(self) -> RAGPipelineStatus:
        try:
            source: SourceResult = self.previous_result
            data, last_modified_date = self.get_file()
            # Get the file's last modified date
            # Download the file from S3 to the local file system
            elements = partition_html(file=BytesIO(data))

            elements = [el for el in elements if el.category != "Header"]

            num_title = len(
                [el for el in elements if el.category.lower() == "title"])

            if num_title > 0:
                documents = self.chunk_document(
                    elements,
                    self.message.pipeline.config["parse"]["chunk_size"],
                    last_modified_date,
                    source.key
                )
                self.message.results.append(
                    ParseResult(
                        pages=[Page(**page) for page in documents])
                )
                return RAGPipelineStatus(
                    agent=self.message.agent,
                    pipeline=self.message.knowledge_base,
                    status=ExecutionState.completed,
                    knowledge_base=self.message.knowledge_base,
                    error=None,
                    results=json.dumps(documents),
                    type=RAGPipelineStages.extraction
                )
            # TODO: change this, num_title doesn't have the same modelling as Page
            self.message.results.append(
                ParseResult(
                    pages=[Page(**page) for page in num_title])
            )
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.completed,
                knowledge_base=self.message.knowledge_base,
                error=None,
                results=json.dumps(num_title),
                type=RAGPipelineStages.extraction
            )
        except Exception as e:
            # TODO: return appropriate rag pipeline status
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.failed,
                knowledge_base=self.message.knowledge_base,
                error=str(e),
                results=None,
                type=RAGPipelineStages.extraction
            )

    def chunk_document(self, elements, chunk_size, last_modified, filename):
        elements = chunk_by_title(
            elements,
            new_after_n_chars=chunk_size,
            # overlap = int(chunk_size*.10)
        )
        cleaned_json_list = []
        for element in elements:
            metadata = element.metadata.to_dict()
            del metadata["languages"]
            metadata["source"] = filename
            # documents.append(Document(
            # page_content=element.text, metadata=metadata))
            page_number = str(
                metadata["page_number"]
                if "page_number" in list(metadata.keys())
                else ""
            )
            text = (
                    "{" + f"File name: {filename}, "
                          f"page: {page_number}, content: {element.text}" + "}"
            )
            cleaned_json = {
                "text": text,
                "metadata": {
                    "source": filename
                    if "filename" in metadata
                    else filename,
                    "page_number": page_number,
                    "last_update_date": last_modified.strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    ),
                },
            }
            cleaned_json_list.append(cleaned_json)
        return cleaned_json_list

    def next(self):
        stringify = json.dumps(self.message.model_dump(mode="json"))
        # send out stringify message via sqs
        config = self.message.pipeline.config
        chunk_type = config["chunk"]["type"]
        url = getattr(self.environ.project_rag_chunk, chunk_type).url
        self.sqs.send_message(QueueUrl=str(url), MessageBody=stringify)

    def get_file(self):
        source: SourceResult = self.previous_result
        s3_file = S3File(bucket=self.environ.bucket.bucket,
                         file_key=source.key)
        # Get the file's last modified date
        last_modified_date = s3_file.get_last_modified()
        # Read the file from S3
        data = s3_file.get_file(decode=False)
        return data, last_modified_date


sqs = client("sqs", region_name="ap-southeast-1")
environ: RAGPipelineEnviron = RAGPipelineEnviron()


def lambda_handler(event: AIBotsPipelineMessage, context):
    """
    lambda function for html parsing
    Args:
        event: lambda event
        context: lambda context
    """
    failed: List[SQSMessageRecord] = []
    for i, message in enumerate(event.pipeline_messages):
        executor: RAGPipelineExecutor = HTMLParser(
            message, sqs, environ)
        status: RAGPipelineStatus = executor()
        if status.error:
            # takes in failed sqs message record
            failed.append(event.records[i])
            continue
        executor.send_status()
        executor.next()

    return {"batchItemFailures": [{"itemIdentifier": fail.message_id}
                                  for fail in failed]}
