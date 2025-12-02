import os
from typing import List
from moto import mock_aws
import boto3
import json

import pytest

from aibots.models.rags.internal import AIBotsPipelineMessage, RAGPipelineMessage, SQSMessageRecord, SourceResult

from aibots.models.knowledge_bases import EmbeddingsMetadata, KnowledgeBase

from aibots.models import RAGConfig

from aibots.models.knowledge_bases import KnowledgeBaseStorage


@pytest.fixture
def csv_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        name="csv",
        storage=KnowledgeBaseStorage(
            location="tests/examplecsv.csv"
        )
    )


@pytest.fixture
def docx_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        name="docx",
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.docx"
        )
    )


@pytest.fixture
def pptx_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        name="pptx",
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.pptx"
        )
    )


@pytest.fixture
def html_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        name="html",
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.html"
        )
    )


@pytest.fixture
def xlsx_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        name="xlsx",
        storage=KnowledgeBaseStorage(
            location="tests/exampleexcel.xlsx"
        )
    )


@pytest.fixture
def txt_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        name="txt",
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.txt"
        )
    )


@pytest.fixture
def pdf_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        name="pdf",
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.pdf"
        )
    )


@pytest.fixture(scope="session")
def aibots_pipeline_message() -> AIBotsPipelineMessage:
    yield AIBotsPipelineMessage(
        Records=[]
    )


@pytest.fixture(scope="session")
def sqs_message() -> SQSMessageRecord:
    yield SQSMessageRecord(
        messageId="213e3fce1b2e42ff9dd512d8f1b86163",
        receiptHandle="AQEBKBDAklp+lnFJe+Nkn9OBVjBp9elLY5jjSvrFxUPSJf7s76cS58HiUOjY380nTiNDsv5jyrA9qTwa5oEBszlursx7+IoFcFMP0lAZeIHRsQ8Qr/4zi/1vCkQ4KSO26YNT4KcxCsA+hKnNLTPtu4OiN/vmoasBERUXdVALX+/mlX5URX+AWOTpc2R4hBc2PI+xt2SdiaaDVRikDDpmfF5mbtdFUIYFoq+ucOx7yIJUjgO5MdHTxD9GIm04uFypwUnVPSTYgm2B9mjkoCoppoL2qQEuRS85EETi76u3LgINNs+GImUpQo9GKPzDldNbQkQjeV5qa+JoXB8sJF3tc4uwr6WaHhUh+np6mKH3h8k3mshuuyzLiguJ7P8SLeOTyt1wOj5RZivk9G77BlFl0q9HU92ukWObyimW8ZHRN/m6xuY=",
        body=json.dumps(RAGPipelineMessage(
            agent="dad32f1794b94153a2fd9997929a4280",
            knowledge_base="0c2622b62eec4f7d-9b35-9ba0388e2d44",
            knowledge_bases=[],
            pipeline=RAGConfig(config={}),
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


@pytest.fixture(scope="session")
def rag_pipeline_message() -> RAGPipelineMessage:
    yield RAGPipelineMessage(
        agent="dad32f1794b94153a2fd9997929a4280",
        knowledge_base="0c2622b62eec4f7d-9b35-9ba0388e2d44",
        knowledge_bases=[],
        pipeline=RAGConfig(),
        results=[],
        supported_pipelines=[{}])


PRIVATE_BUCKET_NAME = "private_bucket"
CLOUDFRONT_BUCKET_NAME = "cloudfront_bucket"
TEST_FILES_DIR = "./test_files"


@pytest.fixture(scope="session")
def mock_aws_infra() -> boto3.Session:
    with mock_aws():
        REGION_NAME = "ap-southeast-1"
        session = boto3.Session(
            aws_access_key_id="FAKE_ACCESS_KEY_ID",
            aws_secret_access_key="FAKE_SECRET_ACCESS_KEY",
            region_name=REGION_NAME
        )

        config = {"LocationConstraint": REGION_NAME}
        # create client for s3 and sqs
        s3 = session.client("s3")
        sqs = session.client("sqs")
        ssm = session.client("ssm")
        # creates private bucket

        s3.create_bucket(Bucket=PRIVATE_BUCKET_NAME,
                         CreateBucketConfiguration=config)
        # creates cloudfront bucket
        s3.create_bucket(Bucket=CLOUDFRONT_BUCKET_NAME,
                         CreateBucketConfiguration=config)
        # insert mock ssm
        ssm.put_parameter(
            Name="param-sitezapp-aibots-rag-aoss-picker",
            Type="SecureString",
            Description="Optimal Opensearch Endpoint",
            Value='{"Collection":"tests","Endpoint":"http://localhost:9200"}',
        )
        # creates all files in cloudfront bucket
        for file_dir in os.listdir(TEST_FILES_DIR):
            with open(f"{TEST_FILES_DIR}/{file_dir}", mode="rb") as test_file:
                s3.upload_fileobj(
                    test_file, CLOUDFRONT_BUCKET_NAME, f"tests/{file_dir}")

        # initialises status queue
        os.environ["PROJECT_RAG_STATUS__URL"] = sqs.create_queue(QueueName="STATUS")[
            "QueueUrl"]

        file_types = ("PPTX", "DOCX", "CSV", "XLSX", "TXT", "PDF", "HTML")
        # initialise parser queues
        for name in file_types:
            url = sqs.create_queue(QueueName=name)["QueueUrl"]
            environ_name = f"PROJECT_RAG_PARSE__{name}__URL"
            os.environ[environ_name] = url

        chunking_types = ("FIXED", "DATAFRAME", "SEMANTIC")
        # initialise chunking queues
        for name in chunking_types:
            url = sqs.create_queue(QueueName=name)["QueueUrl"]
            environ_name = f"PROJECT_RAG_CHUNK_{name}__URL"
            os.environ[environ_name] = url

        # initialise storing queue
        os.environ["PROJECT_RAG_STORE__URL"] = sqs.create_queue(QueueName="STORE")[
            "QueueUrl"]

        yield session
        del os.environ["PROJECT_RAG_STORE__URL"]

        # delete all environ variables
        for name in file_types:
            environ_name = f"PROJECT_RAG_PARSE__{name}__URL"
            del os.environ[environ_name]

        for name in chunking_types:
            environ_name = f"PROJECT_RAG_CHUNK_{name}__URL"
            del os.environ[environ_name]
