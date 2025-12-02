import pytest
from typing import Dict, Any
from aibots.models import RAGConfig

import json
from typing import List
import pytest
from aibots.models.rags.internal import KnowledgeBase
from aibots.models import KnowledgeBaseStorage

from aibots.models.rags.internal import RAGPipelineMessage, SQSMessageRecord

from aibots.models import RAGConfig


@pytest.fixture(scope="session")
def csv_parse_config() -> Dict[str, Any]:
    yield {
            "parse": {
                "chunk_size": 10
            }
        }


@pytest.fixture(scope="session")
def fixed_chunk_config() -> Dict[str, Any]:
    yield {
        "chunk": {
            "type": "fixed"
        }
    }


@pytest.fixture(scope="session")
def dataframe_chunk_config() -> Dict[str, Any]:
    yield {
        "chunk": {
            "type": "dataframe"
        }
    }


@pytest.fixture(scope="session")
def semantic_chunk_config() -> Dict[str, Any]:
    yield {
        "chunk": {
            "type": "semantic"
        }
    }



@pytest.fixture
def csv_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        storage=KnowledgeBaseStorage(
            location="tests/examplecsv.csv"
        )
    )


@pytest.fixture
def docx_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.docx"
        )
    )


@pytest.fixture
def pptx_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.pptx"
        )
    )


@pytest.fixture
def html_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.html"
        )
    )


@pytest.fixture
def xlsx_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        storage=KnowledgeBaseStorage(
            location="tests/exampleexcel.xlsx"
        )
    )


@pytest.fixture
def txt_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.txt"
        )
    )


@pytest.fixture
def pdf_knowledge_base() -> KnowledgeBase:
    yield KnowledgeBase(
        storage=KnowledgeBaseStorage(
            location="tests/exampledoc.pdf"
        )
    )


@pytest.fixture
def sqs_message_record(agent_rag_config: RAGConfig, knowledge_bases: List[KnowledgeBase]):
    return SQSMessageRecord(
        messageId="213e3fce1b2e42ff9dd512d8f1b86163",
        receiptHandle="AQEBKBDAklp+lnFJe+Nkn9OBVjBp9elLY5jjSvrFxUPSJf7s76cS58HiUOjY380nTiNDsv5jyrA9qTwa5oEBszlursx7+IoFcFMP0lAZeIHRsQ8Qr/4zi/1vCkQ4KSO26YNT4KcxCsA+hKnNLTPtu4OiN/vmoasBERUXdVALX+/mlX5URX+AWOTpc2R4hBc2PI+xt2SdiaaDVRikDDpmfF5mbtdFUIYFoq+ucOx7yIJUjgO5MdHTxD9GIm04uFypwUnVPSTYgm2B9mjkoCoppoL2qQEuRS85EETi76u3LgINNs+GImUpQo9GKPzDldNbQkQjeV5qa+JoXB8sJF3tc4uwr6WaHhUh+np6mKH3h8k3mshuuyzLiguJ7P8SLeOTyt1wOj5RZivk9G77BlFl0q9HU92ukWObyimW8ZHRN/m6xuY=",
        body=json.dumps(RAGPipelineMessage(
            agent="dad32f1794b94153a2fd9997929a4280",
            knowledge_base="0c2622b62eec4f7d-9b35-9ba0388e2d44",
            knowledge_bases=[*knowledge_bases],
            pipeline=agent_rag_config,
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
