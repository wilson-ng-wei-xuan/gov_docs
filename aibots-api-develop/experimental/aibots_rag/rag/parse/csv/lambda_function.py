import json

from pydantic import validate_call

from aibots.aws_lambda.s3_file import S3File
from aibots.aws_lambda.models.sqs import SQSMessageHandler, SQSMessageRecord
from aibots.models.rags.base import RAGPipelineEnviron, RAGPipelineExecutor, RAGPipelineMessage
from aibots.models.rags.api import RAGPipelineStatus
from aibots.models.rags.internal import AIBotsPipelineMessage, SourceResult
from boto3 import client
from typing import Dict, Any, List
import pandas as pd

from aibots.models.rags.internal import ParseResult

from aibots.models.rags.internal import Page

from aibots.models.rags.api import ExecutionState

from aibots.models.rags.api import RAGPipelineStages

environ: RAGPipelineEnviron = RAGPipelineEnviron()
sqs = client("sqs", region_name="ap-southeast-1")


class CSVParser(RAGPipelineExecutor):
    def __call__(self, s3_client=None, *args, **kwargs) -> RAGPipelineStatus:
        try:

            data, last_modified_date = self.get_file(s3_client)
            source: SourceResult = self.previous_result
            df = pd.read_csv(data)
            df_json = df.to_dict(orient="records")
            df_json_with_metadata = []

            for row in df_json:
                # Format SQS message
                df_json_with_metadata.append(
                    {
                        "text": json.dumps({"file": source.key, "data": str(row)}),
                        "metadata": {
                            "source": source.key,
                            "page_number": 0,
                            "last_update_date": last_modified_date.strftime(
                                "%Y-%m-%d %H:%M:%S.%f"
                            ),
                        },
                    }
                )
            self.message.results.append(
                ParseResult(
                    pages=[Page(**page) for page in df_json_with_metadata])
            )
            # Update message here
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

    def get_file(self, s3_client=None):

        source: SourceResult = self.previous_result

        s3_file = S3File(bucket=self.environ.bucket.bucket,
                         file_key=source.key, s3_client=s3_client)
        # Get the file's last modified date
        last_modified_date = s3_file.get_last_modified()
        # Read the file from S3
        data = s3_file.get_file()
        return data, last_modified_date

    def next(self):
        """
        sends sqs message to next part of the pipeline
        """
        stringify = json.dumps(self.message.model_dump(mode="json"))
        # send out stringify message via sqs
        config = self.message.pipeline.config
        chunk_type = config["chunk"]["type"]
        url = getattr(self.environ.project_rag_chunk, chunk_type).url
        self.sqs.send_message(QueueUrl=str(url), MessageBody=stringify)


@validate_call
def lambda_handler(event: AIBotsPipelineMessage, context):
    failed: List[SQSMessageRecord] = []
    for i, message in enumerate(event.pipeline_messages):
        executor: RAGPipelineExecutor = CSVParser(
            message, sqs, environ)
        status: RAGPipelineStatus = executor()
        if status.error:
            # takes in failed sqs message record
            failed.append(event.records[i])
            continue
        executor.send_status(status=status)
        executor.next()

    return {"batchItemFailures": [{"itemIdentifier": fail.message_id}
                                  for fail in failed]}

# @validate_call
# def lambda_handler(event, context):
#     """
#     lambda function for parsing csv files
#     Args:
#         event: lambda event
#         context: lambda context
#     """
#     # validates incoming event body
#     # event, context = SQSMessageHandler().validate_inner(event=event, context=context)
#     # instantiates praser
#     parser = RAGBase(func=csv_parser)
#     # instantiates router
#     sqs_router = RAGSQSRouter()
#     failed = []
#     for _, record in enumerate(event["Records"]):
#         # for each record instantiate the following
#
#
#
#         body = SQSMessageRecord(**record).body
#         message = SQSRAGPipelineMessage(**json.loads(body))
#         parse_config: ParseConfig = message.configs.parse
#         try:
#             # runs parser
#             response = parser.run(parse_config)
#             # sets response
#             message.set_parse_results(response)
#             # sends message to the next chunk lambdas
#             sqs_router.send_message_to_rag_chunk_sqs(chunk=message.configs.chunk.type,
#                                                      message=message.model_dump())
#             # TODO: send message to status lambda via sqs
#         except Exception as e:
#             parser.log(e)
#             failed.append(record)
#         # parser = RAGParser(event=event, context=context, parser=csv_parser)
#         # sqs_router = RAGSQSRouter()
#         # successes, fails = parser.run()
#         # logging.getLogger().setLevel(logging.INFO)
#         # for _, success in enumerate(successes):
#         #     try:
#         #         message: SQSRAGPipelineMessage = SQSRAGPipelineMessage(
#         #             **success["body"])
#         #         sqs_router.send_message_to_rag_chunk_sqs(
#         #             chunk=message.configs.chunk.type, message=message.model_dump())
#         #     except Exception as e:
#         #         fails.append(success)
#         #         logging.error(e)
#         # failed_message_ids = [{"itemIdentifier": fail["messageId"]}
#         #                           for fail in failed]
#     return {"batchItemFailures": [{"itemIdentifier": fail["messageId"]}
#                                   for fail in failed]}
