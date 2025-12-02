import json
import re
from copy import deepcopy
from pathlib import Path
from boto3 import resource
from typing import Any, List, Dict, Optional
from pydantic import validate_call
from aibots.models.rags.internal import AIBotsPipelineMessage
from aibots.models.rags.base import RAGPipelineExecutor, RAGPipelineStatus
from aibots.models.rags import SourceResult
from atlas.environ import ServiceEnvVars
from aibots.models.knowledge_bases import KnowledgeBase

from aibots.models.rags.internal import RAGPipelineMessage

from aibots.models.rags.api import ExecutionState, RAGPipelineStages

from aibots.models.rags.internal import SQSMessageRecord

from boto3 import client
from aibots.models.rags.base import RAGPipelineEnviron
from pydantic import BaseModel, Field


class RAGAOSSConfiguration(BaseModel):
    collection: str = Field(alias="Collection")
    host: str
    port: int
    is_local: Optional[bool]


class SourceExecutor(RAGPipelineExecutor):

    def __call__(self, *args: Any, **kwargs: Any) -> RAGPipelineStatus:
        # iterate through messages and their knowledge bases knowledge bases
        s3 = resource("s3")
        # list of created fanout messages
        fanout_messages: List[RAGPipelineMessage] = []
        kbs: List[KnowledgeBase] = self.message.knowledge_bases
        try:
            # for each kb, move file from cloudfront to priv
            for kb in kbs:
                try:
                    # move kb from cloudfront to private
                    source: SourceResult = self.move_kb(kb=kb, s3=s3)
                    # create new message to be sent to parser with source result
                    fanout_message: RAGPipelineMessage = deepcopy(
                        self.message)

                    curr_config: Dict[str, Any] = {**fanout_message.pipeline.config,
                                                   "store": self.get_optimal_aoss_endpoint().model_dump(mode="json")}
                    fanout_message.pipeline.config = curr_config

                    fanout_message.results.append(source)

                    fanout_messages.append(fanout_message)
                except Exception as e:
                    # TODO: send error for copying to status when fail

                    self.send_status(
                        status=RAGPipelineStatus(
                            agent=self.message.agent,
                            pipeline=self.message.id,
                            status=ExecutionState.failed,
                            knowledge_base=kb.id,
                            error=str(e),
                            results=None,
                            type=RAGPipelineStages.source
                        )
                    )

            # for each RAG message, send sqs
            for fanout_message in fanout_messages:
                try:
                    # send to parser via sqs
                    self.send_to_parser(message=fanout_message)
                except Exception as e:
                    # if there is an error in sending to parser,
                    # send to status error
                    self.send_status(
                        status=RAGPipelineStatus(
                            agent=fanout_message.agent,
                            pipeline=fanout_message.id,
                            status=ExecutionState.failed,
                            knowledge_base=fanout_message.knowledge_base,
                            error=str(e),
                            results=None,
                            type=RAGPipelineStages.source
                        )
                    )
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.pipeline.id,
                status=ExecutionState.completed,
                knowledge_base=self.message.knowledge_base,
                error=None,
                results=json.dumps([fanout_message.model_dump(
                    mode="json") for fanout_message in fanout_messages]),
                type=RAGPipelineStages.source
            )

        except Exception as e:
            # if any stage of the processing fails, send to status

            self.send_status(
                status=RAGPipelineStatus(
                    agent=self.message.agent,
                    pipeline=self.message.id,
                    status=ExecutionState.failed,
                    knowledge_base=self.message.knowledge_base,
                    error=str(e),
                    results=None,
                    type=RAGPipelineStages.source
                )
            )

    def next(self) -> None:
        # routes & sends pipeline message to appropriate parser
        pass

    def move_kb(self, kb: KnowledgeBase, s3: Any) -> SourceResult:
        try:
            # moves s3 file from private to cloudfront bucket
            priv_bucket, cloudfront_bucket = self.environ.bucket.bucket, self.environ.cloudfront_bucket.bucket
            # kb.storage.location should be the bucket file key
            # for example (tests/file.pdf)
            copy_source = {"Bucket": cloudfront_bucket,
                           "Key": kb.storage.location}
            other_bucket = s3.Bucket(priv_bucket)
            other_bucket.copy(copy_source, str(kb.storage.location))
            return SourceResult(key=str(kb.storage.location))
        except Exception as e:
            raise e

    def get_optimal_aoss_endpoint(self) -> RAGAOSSConfiguration:
        param_name = self.environ.project_rag_aoss.param
        ssm = client("ssm", region_name="ap-southeast-1")
        param_values = ssm.get_parameter(
            Name=param_name,
            WithDecryption=True
        )
        config = json.loads(param_values["Parameter"]["Value"])
        pattern = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
        match = re.search(pattern, config["Endpoint"])
        host, port = match.group('host'), match.group('port')
        port = 80 if port == "" else port
        return RAGAOSSConfiguration(collection=config["Collection"], host=host, port=port)

    def send_to_parser(self, message: RAGPipelineMessage):
        kb_file: SourceResult = message.results[0]
        file_type: str = Path(kb_file.key).suffix[1:]
        # gets file parser sqs url
        if hasattr(self.environ.project_rag_parse, file_type):
            file_service_env_vars: ServiceEnvVars = getattr(
                self.environ.project_rag_parse, file_type)
        else:
            # Throws error if parser does not exist for file
            raise Exception(f"Parser for file type {file_type} does not exist")
        # sends message to sqs for parsing
        self.sqs.send_message(
            QueueUrl=str(file_service_env_vars.url),
            MessageBody=json.dumps(message.model_dump(mode="json"))
        )


environ: RAGPipelineEnviron = RAGPipelineEnviron()
sqs = client("sqs", region_name="ap-southeast-1")


@validate_call
def lambda_handler(event: AIBotsPipelineMessage, context):
    failed: List[SQSMessageRecord] = []
    for i, message in enumerate(event.pipeline_messages):
        executor: RAGPipelineExecutor = SourceExecutor(
            message, sqs, environ
        )
        status: RAGPipelineStatus = executor()
        if status.error:
            # takes in failed sqs message record
            failed.append(event.records[i])
            continue
        executor.send_status(status=status)
    return {"batchItemFailures": [{"itemIdentifier": fail.message_id}
                                  for fail in failed]}
