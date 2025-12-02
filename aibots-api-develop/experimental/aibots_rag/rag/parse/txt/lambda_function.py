from __future__ import annotations
import logging
import json
from typing import Any, Dict, List
from aibots.aws_lambda.s3_file import S3File
from aibots.aws_lambda.parser import RAGParser
from aibots.aws_lambda.models.rag import SQSRAGPipelineMessage
from aibots.aws_lambda.sqs_router import RAGSQSRouter
from boto3 import client

from aibots.models.rags.base import RAGPipelineEnviron, RAGPipelineExecutor

from aibots.models.rags.internal import SourceResult, SQSMessageRecord

from aibots.models.rags.api import RAGPipelineStatus

from aibots.models.rags.api import ExecutionState

from aibots.models.rags.api import RAGPipelineStages

from aibots.models.rags.internal import Page, ParseResult


class TxtParser(RAGPipelineExecutor):

    def __call__(self) -> RAGPipelineStatus:
        try:
            source: SourceResult = self.previous_result
            data, last_modified_date = self.get_file()

            text = data.read()

            df_json_with_metadata = {
                "text": text,
                "metadata": {
                    "source": source.key,
                    "page_number": 0,
                    "last_update_date": last_modified_date.strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    ),
                },
            }
            self.message.results.append(
                ParseResult(
                    pages=[Page(**page) for page in [df_json_with_metadata]])
            )
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.completed,
                knowledge_base=self.message.knowledge_base,
                results=json.dumps([df_json_with_metadata]),
                error=None,
                type=RAGPipelineStages.extraction
            )
        except Exception as e:
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.completed,
                knowledge_base=self.message.knowledge_base,
                results=None,
                error=str(e),
                type=RAGPipelineStages.extraction
            )

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
        data = s3_file.get_file()
        return data, last_modified_date


sqs = client("sqs", region_name="ap-southeast-1")
environ: RAGPipelineEnviron = RAGPipelineEnviron()


def lambda_handler(event, context) -> dict[str, Any]:
    failed: List[SQSMessageRecord] = []
    for i, message in enumerate(event.pipeline_messages):
        executor: RAGPipelineExecutor = TxtParser(
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
