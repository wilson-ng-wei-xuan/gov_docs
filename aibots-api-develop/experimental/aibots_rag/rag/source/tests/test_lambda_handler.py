import json
from copy import deepcopy
from typing import List

import pytest
import boto3
from aibots.models.rags import RAGPipelineEnviron
from aibots.models.rags.internal import AIBotsPipelineMessage, SQSMessageRecord
from aibots.models.rags.base import RAGPipelineStatus

from ..lambda_function import lambda_handler


class TestSourceLambdaHandler:

    def test_successful_lambda_run(self, request) -> None:
        aibots_pipeline_message: AIBotsPipelineMessage = request.getfixturevalue("aibots_pipeline_message")
        sqs_message: SQSMessageRecord = request.getfixturevalue("sqs_message")
        mock_aws_infra: boto3.Session = request.getfixturevalue("mock_aws_infra")

        aws_aibots_message = deepcopy(aibots_pipeline_message)
        aws_aibots_message.records.append(sqs_message)
        response = lambda_handler(event=aws_aibots_message, context=None)

        sqs = mock_aws_infra.client("sqs", region_name="ap-southeast-1")

        environ = RAGPipelineEnviron()

        messages = sqs.receive_message(QueueUrl=str(environ.project_rag_status.url))["Messages"]

        for message in messages:
            message_body = json.loads(message["Body"])
            print(message_body)
            RAGPipelineStatus.model_validate(message_body)
            assert RAGPipelineStatus(**message_body).status == "completed"

        assert len(messages) == 1
        assert len(response["batchItemFailures"]) == 0

    # def test_unsuccessful_lambda_run_wrong_message_error(self, request):
    #     pass
