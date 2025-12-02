import os
from typing import List
from moto import mock_aws
import boto3
from botocore.exceptions import ClientError

import json
from pathlib import Path
from copy import deepcopy
import pytest

from aibots.models.rags.internal import AIBotsPipelineMessage, RAGPipelineMessage, SQSMessageRecord, SourceResult

from aibots.models.knowledge_bases import EmbeddingsMetadata, KnowledgeBase

from aibots.models import RAGConfig

from aibots.models.knowledge_bases import KnowledgeBaseStorage

from aibots.models.rags.base import RAGPipelineEnviron

from boto3 import client

from ..lambda_function import SourceExecutor, lambda_handler

# TODO: Refactor this into a fixture
event = AIBotsPipelineMessage(
    Records=[
        SQSMessageRecord(
            messageId="213e3fce1b2e42ff9dd512d8f1b86163",
            receiptHandle="AQEBKBDAklp+lnFJe+Nkn9OBVjBp9elLY5jjSvrFxUPSJf7s76cS58HiUOjY380nTiNDsv5jyrA9qTwa5oEBszlursx7+IoFcFMP0lAZeIHRsQ8Qr/4zi/1vCkQ4KSO26YNT4KcxCsA+hKnNLTPtu4OiN/vmoasBERUXdVALX+/mlX5URX+AWOTpc2R4hBc2PI+xt2SdiaaDVRikDDpmfF5mbtdFUIYFoq+ucOx7yIJUjgO5MdHTxD9GIm04uFypwUnVPSTYgm2B9mjkoCoppoL2qQEuRS85EETi76u3LgINNs+GImUpQo9GKPzDldNbQkQjeV5qa+JoXB8sJF3tc4uwr6WaHhUh+np6mKH3h8k3mshuuyzLiguJ7P8SLeOTyt1wOj5RZivk9G77BlFl0q9HU92ukWObyimW8ZHRN/m6xuY=",
            body=json.dumps(RAGPipelineMessage(
                agent="dad32f1794b94153a2fd9997929a4280",
                knowledge_base="0c2622b62eec4f7d-9b35-9ba0388e2d44",
                knowledge_bases=[KnowledgeBase(
                    storage=KnowledgeBaseStorage(
                        location="tests/examplecsv.csv"
                    ),
                    name="knowledge_base",
                    embeddings={"main": EmbeddingsMetadata()},
                ), KnowledgeBase(
                    storage=KnowledgeBaseStorage(
                        location="tests/exampledoc.docx"
                    ),
                    name="knowledge_base",
                    embeddings={"main": EmbeddingsMetadata()},
                )],
                pipeline=RAGConfig(
                    config={
                        "parse": {
                            "chunk_size": 10
                        }
                    }),
                results=[],
                supported_pipelines=[{}]
            ).model_dump(mode="json")),
            attributes={},
            messageAttributes={},
            md5OfMessage_attributes=None,
            md5OfBody="853731de9e45ec50948df25ae3287521",
            eventSourceARN="arn:aws:sqs:ap-southeast-1:471112510129:sqs-sitezapp-aibots-rag-parse-zip",
            eventSource="aws:sqs",
            awsRegion="ap-southeast-1"
        )
    ]
)
PRIVATE_BUCKET_NAME = "private_bucket"
CLOUDFRONT_BUCKET_NAME = "cloudfront_bucket"
TEST_FILES_DIR = "./test_files"


class TestSourceExecutor:

    @pytest.fixture(scope="class", autouse=True)
    def setup_infra(self, request):
        self.mock_aws_infra = request.getfixturevalue("mock_aws_infra")
        self.sqs_message = request.getfixturevalue("sqs_message")
        self.rag_pipeline_message = request.getfixturevalue("rag_pipeline_message")

    @pytest.mark.parametrize(
        argnames=["knowledge_base"],
        argvalues=[
            pytest.param(
                "csv_knowledge_base",
                id="move_csv_knowledge_base"
            ),
            pytest.param(
                "docx_knowledge_base",
                id="move_docx_knowledge_base"
            ),
            pytest.param(
                "pptx_knowledge_base",
                id="move_pptx_knowledge_base"
            ),
            pytest.param(
                "html_knowledge_base",
                id="move_html_knowledge_base"
            ),
            pytest.param(
                "xlsx_knowledge_base",
                id="move_xlsx_knowledge_base"
            ),
            pytest.param(
                "txt_knowledge_base",
                id="move_txt_knowledge_base"
            ),
            pytest.param(
                "pdf_knowledge_base",
                id="move_pdf_knowledge_base"
            )

        ]
    )
    def test_source_executor_move_kb_successful_copy(self, request, knowledge_base):
        kb_to_move: KnowledgeBase = request.getfixturevalue(knowledge_base)

        mock_aws_infra: boto3.Session = request.getfixturevalue("mock_aws_infra")

        sqs = mock_aws_infra.client("sqs", region_name="ap-southeast-1")
        s3 = mock_aws_infra.client("s3", region_name="ap-southeast-1")

        environ: RAGPipelineEnviron = RAGPipelineEnviron()

        message: RAGPipelineMessage = deepcopy(request.getfixturevalue("rag_pipeline_message"))

        executor = SourceExecutor(message, sqs, environ)

        environ.bucket.bucket, environ.cloudfront_bucket.bucket = PRIVATE_BUCKET_NAME, CLOUDFRONT_BUCKET_NAME

        cloudfront_kb_file = s3.get_object(Bucket=environ.cloudfront_bucket.bucket, Key=kb_to_move.storage.location)

        try:
            s3.get_object(Bucket=environ.bucket.bucket, Key=kb_to_move.storage.location)
            # checks if file is absent
            assert False
        except ClientError as e:
            if e:
                assert True
        assert cloudfront_kb_file is not None

        executor.move_kb(kb=kb_to_move, s3=mock_aws_infra.resource("s3", "ap-southeast-1"))

        try:
            s3.get_object(Bucket=environ.bucket.bucket, Key=kb_to_move.storage.location)
            # checks if file is present
            assert True
        except ClientError as e:
            if e:
                assert False
        s3.delete_object(Bucket=environ.bucket.bucket, Key=kb_to_move.storage.location)

    # @pytest.mark.parametrize(
    #     argnames=["test_input, test_output"],
    #     argvalues=[
    #         pytest.param(
    #             "fixture_name", "fixture_output_name",
    #             id="error_file_missing"
    #         )
    #     ]
    # )
    def test_source_executor_move_kb_error_file_missing(self, request):
        pass
        # fixture1 = request.getfixturevalue(test_input)
        # fixture2 = request.getfixturevalue(test_output)
        # self.infra_client
        # with pytest.raises(AtlasRAGException) as e:
        #     SourceExecutor().move_kb(fixture1)
        # assert str(e.value) == fixture2

    def test_source_executor_move_kb_error_destination_folder_deleted(self):
        pass

    @pytest.mark.parametrize(
        argnames=["sources"],
        argvalues=[
            pytest.param(
                ["docx_knowledge_base"],
                id="test_docx"
            ),
            pytest.param(
                ["html_knowledge_base"],
                id="test_html"
            ),
            pytest.param(
                ["xlsx_knowledge_base"],
                id="test_xlsx"
            ),
            pytest.param(
                ["pdf_knowledge_base"],
                id="test_pdf"
            ),
            pytest.param(
                ["pptx_knowledge_base"],
                id="test_pptx"
            ),
            pytest.param(
                ["csv_knowledge_base"],
                id="test_csv"
            ),
            pytest.param(
                ["txt_knowledge_base"],
                id="test_txt"
            ),
            pytest.param(
                ["xlsx_knowledge_base", "csv_knowledge_base"],
                id="test_xlsx_csv"
            ),
            pytest.param(
                ["csv_knowledge_base", "pptx_knowledge_base"],
                id="test_csv_pptx"
            ),
            pytest.param(
                ["csv_knowledge_base", "pdf_knowledge_base"],
                id="test_csv_pdf"
            ),
            pytest.param(
                ["csv_knowledge_base", "docx_knowledge_base"],
                id="test_csv_docx"
            ),
            pytest.param(
                ["csv_knowledge_base", "html_knowledge_base"],
                id="test_csv_html"
            ),
            pytest.param(
                ["xlsx_knowledge_base", "pptx_knowledge_base"],
                id="test_xlsx_pptx"
            ),
            pytest.param(
                ["xlsx_knowledge_base", "pdf_knowledge_base"],
                id="test_xlsx_pdf"
            ),
            pytest.param(
                ["html_knowledge_base", "xlsx_knowledge_base"],
                id="test_html_xlsx"
            ),
            pytest.param(
                ["xlsx_knowledge_base", "docx_knowledge_base"],
                id="test_xlsx_docx"
            ),
            pytest.param(
                ["pptx_knowledge_base", "html_knowledge_base"],
                id="test_pptx_html"
            ),
            pytest.param(
                ["pptx_knowledge_base", "txt_knowledge_base"],
                id="test_pptx_txt"
            ),
            pytest.param(
                ["pptx_knowledge_base", "docx_knowledge_base"],
                id="test_pptx_docx"
            ),
            pytest.param(
                ["pptx_knowledge_base", "pdf_knowledge_base"],
                id="test_pptx_pdf"
            ),
            # TODO: ADD IN MORE CASES...
        ]
    )
    def test_source_executor_successful_call(self, request, sources) -> None:
        environ: RAGPipelineEnviron = RAGPipelineEnviron()
        mock_aws_infra: boto3.Session = request.getfixturevalue("mock_aws_infra")
        rag_pipeline_message: RAGPipelineMessage = request.getfixturevalue("rag_pipeline_message")

        sources: List[KnowledgeBase] = [request.getfixturevalue(source) for source in sources]

        sqs = mock_aws_infra.client("sqs", region_name="ap-southeast-1")

        message = deepcopy(rag_pipeline_message)

        # add sources
        for source in sources:
            message.knowledge_bases.append(source)

        environ.bucket.bucket, environ.cloudfront_bucket.bucket = PRIVATE_BUCKET_NAME, CLOUDFRONT_BUCKET_NAME

        status_response = SourceExecutor(message, sqs, environ)()

        parser_queues = []
        for source in sources:
            ext = Path(source.storage.location).suffix[1:]
            url = getattr(environ.project_rag_parse, ext).url
            queue = sqs.receive_message(
                QueueUrl=str(url))
            parser_queues.append(queue)
        sqs_status = sqs.receive_message(
            QueueUrl=str(environ.project_rag_status.url))

        for queue_messages in parser_queues:
            result_body = json.loads(queue_messages["Messages"][0]["Body"])
            SourceResult.model_validate(result_body["results"][0])
            RAGPipelineMessage.model_validate(result_body)
            assert len(result_body["results"]) == 1

        assert "Messages" not in sqs_status.keys()
        assert status_response.status == "completed"
