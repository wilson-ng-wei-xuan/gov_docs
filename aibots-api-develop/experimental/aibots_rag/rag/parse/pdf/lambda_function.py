from __future__ import annotations
import logging
import json
from pathlib import Path
from io import BytesIO
from typing import Any, Dict, List
from boto3 import client
from document import Document
# from pydantic import validate_call
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.pdf import partition_pdf
from aibots.aws_lambda.s3_file import S3File
from aibots.aws_lambda.models.rag import SQSRAGPipelineMessage
from aibots.aws_lambda.sqs_router import RAGSQSRouter
from aibots.aws_lambda.parser import RAGParser

from aibots.models.rags.base import RAGPipelineExecutor

from aibots.models.rags.internal import SourceResult

from aibots.models.rags.internal import AIBotsPipelineMessage, SQSMessageRecord

from aibots.models.rags.api import RAGPipelineStatus

from aibots.models.rags.base import RAGPipelineEnviron

from aibots.models.rags.api import ExecutionState, RAGPipelineStages

from aibots.models.rags.internal import Page, ParseResult


class PDFParser(RAGPipelineExecutor):
    def __call__(self) -> RAGPipelineStatus:
        try:
            source: SourceResult = self.previous_result
            data, last_modified_date = self.get_file()

            elements = partition_pdf(
                file=BytesIO(data),
                pdf_infer_table_structure=True,
                model_name="yolox",
            )

            elements = [el for el in elements if el.category != "Header"]

            documents = self.chunk_document(
                elements,
                chunk_size=self.message.pipeline.config["parse"]["chunk_size"],
                filename=source.key)
            df_json_with_metadata = self.docs_to_json(
                documents, source.key, last_modified_date
            )
            self.message.results.append(
                ParseResult(
                    pages=[Page(**page) for page in df_json_with_metadata])
            )
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.completed,
                knowledge_base=self.message.knowledge_base,
                error=None,
                results=json.dumps(df_json_with_metadata),
                type=RAGPipelineStages.extraction
            )
        except Exception as e:
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.failed,
                knowledge_base=self.message.knowledge_base,
                error=str(e),
                results=None,
                type=RAGPipelineStages.extraction
            )

    def next(self):
        stringify = json.dumps(self.message.model_dump(mode="json"))
        # send out stringify message via sqs
        config = self.message.pipeline.config
        chunk_type = config["chunk"]["type"]
        url = getattr(self.environ.project_rag_chunk, chunk_type).url
        self.sqs.send_message(QueueUrl=str(url), MessageBody=stringify)

    def chunk_document(self, elements, chunk_size, filename):
        elements = chunk_by_title(
            elements,
            new_after_n_chars=chunk_size,
            # overlap = int(chunk_size*.10)
        )
        documents = []
        for element in elements:
            metadata = element.metadata.to_dict()
            del metadata["languages"]
            metadata["source"] = filename
            documents.append(
                Document(page_content=element.text, metadata=metadata)
            )

        return documents

    def docs_to_json(self, docs, filename: str, last_modified: str = None):
        cleaned_json_list = []
        for doc in docs:
            page_number = str(
                doc.metadata["page_number"]
                if "page_number" in list(doc.metadata.keys())
                else ""
            )
            text = (
                    "{" + f"File name: {filename}, "
                          f"page: {page_number}, content: {doc.page_content}" + "}"
            )
            cleaned_json = {
                "text": text,
                "metadata": {
                    "source": filename,
                    "page_number": page_number,
                    "last_update_date": last_modified.strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    ),
                },
            }
            cleaned_json_list.append(cleaned_json)
        return cleaned_json_list

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
    for record in event['Records']:
        # Get the SQS message
        message = json.loads(record['body'])

        # Extract bucket name and file key from the message
        bucket_name = message['Records'][0]['s3']['bucket']['name']
        file_key = message['Records'][0]['s3']['object']['key']
    """
    failed: List[SQSMessageRecord] = []
    for i, message in enumerate(event.pipeline_messages):
        executor: RAGPipelineExecutor = PDFParser(
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
