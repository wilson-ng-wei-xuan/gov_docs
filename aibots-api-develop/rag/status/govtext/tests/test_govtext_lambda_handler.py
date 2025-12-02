import json
from io import BytesIO

import pytest
from botocore.exceptions import ClientError

from aibots.models import RAGPipelineStatus, StatusResult, SQSMessageRecord, RAGPipelineStages
from aibots.rags.govtext import GovTextJobStatus
from atlas.utils import generate_uuid

from ..lambda_function import lambda_handler, GovTextStatusMessage, GovTextPipelineStatus


@pytest.fixture()
def pipeline_id():
    return generate_uuid()


@pytest.fixture()
def agent_id():
    return generate_uuid()


@pytest.fixture()
def rag_config_id():
    return generate_uuid()


@pytest.fixture()
def sqs_message_template():
    return {
        "messageId": "213e3fce1b2e42ff9dd512d8f1b86163",
        "receiptHandle": "AQEBKBDAklp+lnFJe+Nkn9OBVjBp9elLY5jjSvrFxUPSJf7s76cS58HiUOjY380nTiNDsv5jyrA9qTwa5oEBszlursx7+IoFcFMP0lAZeIHRsQ8Qr/4zi/1vCkQ4KSO26YNT4KcxCsA+hKnNLTPtu4OiN/vmoasBERUXdVALX+/mlX5URX+AWOTpc2R4hBc2PI+xt2SdiaaDVRikDDpmfF5mbtdFUIYFoq+ucOx7yIJUjgO5MdHTxD9GIm04uFypwUnVPSTYgm2B9mjkoCoppoL2qQEuRS85EETi76u3LgINNs+GImUpQo9GKPzDldNbQkQjeV5qa+JoXB8sJF3tc4uwr6WaHhUh+np6mKH3h8k3mshuuyzLiguJ7P8SLeOTyt1wOj5RZivk9G77BlFl0q9HU92ukWObyimW8ZHRN/m6xuY=",
        "body": '',
        "attributes": {},
        "messageAttributes": {},
        "md5OfMessageAttributes": None,
        "md5OfBody": "853731de9e45ec50948df25ae3287521",
        "eventSourceARN": "arn:aws:sqs:ap-southeast-1:471112510129:sqs-sitezapp-aibots-rag-parse-zip",
        "eventSource": "aws:sqs",
        "awsRegion": "ap-southeast-1",
    }


@pytest.fixture
def assert_all_responses_were_requested() -> bool:
    return False


@pytest.fixture()
def mock_s3_client(
    aws_region,
    govtext_bucket,
    mock_aws_infra,
):
    # creates scheduler bucket
    s3 = mock_aws_infra.client("s3", region_name=aws_region)
    s3.create_bucket(
        Bucket=govtext_bucket,
        CreateBucketConfiguration={"LocationConstraint": aws_region},
    )

    yield mock_aws_infra.client("s3", region_name=aws_region)

    objs = s3.list_objects(Bucket=govtext_bucket)
    for obj in objs.get("Contents", []):
        s3.delete_object(Bucket=govtext_bucket, Key=obj["Key"])
    s3.delete_bucket(
        Bucket=govtext_bucket,
    )


@pytest.fixture(scope='function')
async def clear_environment():
    from ..lambda_function import reset_lambda

    await reset_lambda()
    yield
    await reset_lambda()


@pytest.fixture()
def test_single_success_status(
    agent_id,
    pipeline_id,
    rag_config_id,
):
    return [
        {
            "job_id": "c0c8fa1b-3987-469d-b706-390a8bbaf69f",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
    ]


@pytest.fixture()
def test_single_failed_status(
    agent_id,
    pipeline_id,
    rag_config_id,
):
    return [
        {
            "job_id": "c0c8fa1b-3987-469d-b706-390a8bbaf69f",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
    ]


@pytest.fixture()
def test_multiple_all_failed_statuses(
    agent_id,
    pipeline_id,
    rag_config_id,
):
    return [
        {
            "job_id": "a1fd42c7-7b06-4b84-80f6-5bfeb45047a1",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "4180dd6b-adaf-4b42-825d-02be958137cf",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "90064985-0e62-44ed-9f19-d67fc13d601a",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "710d5fb4-41a7-4acd-8db5-2651fac1c602",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "f145c5b4-a9b0-4a2c-99f6-f0c1fa3c3fbb",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "e8b79ace-7fd2-4b9c-bb11-8f1e889957ef",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "efddda57-d468-4fd9-8c6a-ead88aa45a29",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "33a650e5-5b10-4882-aadd-64de58c6c356",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "b61d1901-ebd8-4a7d-9a50-5d109931972b",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "7592318b-9246-4c43-97b9-7fe8003df621",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
    ]


@pytest.fixture()
def test_multiple_all_success_statuses(
    agent_id,
    pipeline_id,
    rag_config_id,
):
    return [
        {
            "job_id": "a1fd42c7-7b06-4b84-80f6-5bfeb45047a1",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "4180dd6b-adaf-4b42-825d-02be958137cf",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "90064985-0e62-44ed-9f19-d67fc13d601a",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "710d5fb4-41a7-4acd-8db5-2651fac1c602",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "f145c5b4-a9b0-4a2c-99f6-f0c1fa3c3fbb",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "e8b79ace-7fd2-4b9c-bb11-8f1e889957ef",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "efddda57-d468-4fd9-8c6a-ead88aa45a29",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "33a650e5-5b10-4882-aadd-64de58c6c356",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "b61d1901-ebd8-4a7d-9a50-5d109931972b",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "7592318b-9246-4c43-97b9-7fe8003df621",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
    ]


@pytest.fixture()
def test_multiple_partial_success_failed_running_statuses(
    agent_id,
    pipeline_id,
    rag_config_id,
):
    return [
        {
            "job_id": "a1fd42c7-7b06-4b84-80f6-5bfeb45047a1",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "4180dd6b-adaf-4b42-825d-02be958137cf",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "90064985-0e62-44ed-9f19-d67fc13d601a",
            "status": "PAUSED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "710d5fb4-41a7-4acd-8db5-2651fac1c602",
            "status": "SCHEDULED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "f145c5b4-a9b0-4a2c-99f6-f0c1fa3c3fbb",
            "status": "CANCELLED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "e8b79ace-7fd2-4b9c-bb11-8f1e889957ef",
            "status": "CANCELLING",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "efddda57-d468-4fd9-8c6a-ead88aa45a29",
            "status": "CANCELLED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "33a650e5-5b10-4882-aadd-64de58c6c356",
            "status": "CRASHED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "b61d1901-ebd8-4a7d-9a50-5d109931972b",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "7592318b-9246-4c43-97b9-7fe8003df621",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
    ]


@pytest.fixture()
def test_multiple_partial_success_failed_running_statuses_across_different_agents_pipelines_rag_configs(
    agent_id,
    pipeline_id,
    rag_config_id,
):
    return [
        {
            "job_id": "a1fd42c7-7b06-4b84-80f6-5bfeb45047a1",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "4180dd6b-adaf-4b42-825d-02be958137cf",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "90064985-0e62-44ed-9f19-d67fc13d601a",
            "status": "PAUSED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "710d5fb4-41a7-4acd-8db5-2651fac1c602",
            "status": "SCHEDULED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "f145c5b4-a9b0-4a2c-99f6-f0c1fa3c3fbb",
            "status": "CANCELLED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "e8b79ace-7fd2-4b9c-bb11-8f1e889957ef",
            "status": "CANCELLING",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "efddda57-d468-4fd9-8c6a-ead88aa45a29",
            "status": "CANCELLED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "33a650e5-5b10-4882-aadd-64de58c6c356",
            "status": "CRASHED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": generate_uuid(),
            "pipeline_id": generate_uuid(),
            "rag_config_id": generate_uuid(),
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "b61d1901-ebd8-4a7d-9a50-5d109931972b",
            "status": "RUNNING",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": generate_uuid(),
            "pipeline_id": generate_uuid(),
            "rag_config_id": generate_uuid(),
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "7592318b-9246-4c43-97b9-7fe8003df621",
            "status": "RUNNING",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": generate_uuid(),
            "pipeline_id": generate_uuid(),
            "rag_config_id": generate_uuid(),
            "knowledge_base_id": generate_uuid()
        },
    ]


@pytest.fixture()
def test_multiple_partial_success_failed_running_statuses_across_different_agents_pipelines_rag_configs(
    agent_id,
    pipeline_id,
    rag_config_id,
):
    return [
        {
            "job_id": "a1fd42c7-7b06-4b84-80f6-5bfeb45047a1",
            "status": "COMPLETED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "4180dd6b-adaf-4b42-825d-02be958137cf",
            "status": "FAILED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "90064985-0e62-44ed-9f19-d67fc13d601a",
            "status": "PAUSED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "710d5fb4-41a7-4acd-8db5-2651fac1c602",
            "status": "SCHEDULED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "f145c5b4-a9b0-4a2c-99f6-f0c1fa3c3fbb",
            "status": "CANCELLED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "e8b79ace-7fd2-4b9c-bb11-8f1e889957ef",
            "status": "CANCELLING",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "efddda57-d468-4fd9-8c6a-ead88aa45a29",
            "status": "CANCELLED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": agent_id,
            "pipeline_id": pipeline_id,
            "rag_config_id": rag_config_id,
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "33a650e5-5b10-4882-aadd-64de58c6c356",
            "status": "CRASHED",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": generate_uuid(),
            "pipeline_id": generate_uuid(),
            "rag_config_id": generate_uuid(),
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "b61d1901-ebd8-4a7d-9a50-5d109931972b",
            "status": "RUNNING",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": generate_uuid(),
            "pipeline_id": generate_uuid(),
            "rag_config_id": generate_uuid(),
            "knowledge_base_id": generate_uuid()
        },
        {
            "job_id": "7592318b-9246-4c43-97b9-7fe8003df621",
            "status": "RUNNING",
            "s3_status": "running",
            "response": {
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "start_time": "2024-09-13T15:26:47+08:00",
                "ingest_pipeline": {
                    "parse": {"output_format": "TEXT"},
                    "chunk": {
                        "chunk_overlap": 30,
                        "chunk_size": 100,
                        "chunk_strategy": "FIXED_SIZE",
                        "separators": ["[]"],
                    },
                },
            },
            "agent_id": generate_uuid(),
            "pipeline_id": generate_uuid(),
            "rag_config_id": generate_uuid(),
            "knowledge_base_id": generate_uuid()
        },
    ]


class TestGovTextLambdaHandler:

    @staticmethod
    def get_sqs_record(
        job_id,
        pipeline_id,
        agent_id,
        rag_config_id,
        knowledge_base_id,
        status,
    ):
        return RAGPipelineStatus(
            id=pipeline_id,
            agent=agent_id,
            rag_config=rag_config_id,
            status=status,
            knowledge_base=knowledge_base_id,
            error=None,
            results=StatusResult(
                metadata=GovTextStatusMessage(
                    job_id=job_id,
                    knowledge_bases=[knowledge_base_id],
                ).model_dump(mode="json")
            ),
            type=RAGPipelineStages.external,
        )

    @staticmethod
    def upload_file(
        sqs,
        s3_client,
        bucket,
        agent_id,
        job_id,
        status
    ):
        # uploads to cloudfront
        s3_client.upload_fileobj(
            BytesIO(json.dumps({"sqs": sqs, "payload": status.model_dump(mode='json')}).encode("utf-8")),
            bucket,
            f"schedule/minute/{job_id}_{agent_id}_govtext.json"
        )

    @pytest.mark.parametrize(
        argnames="test_status_inputs",
        argvalues=[
            pytest.param(
                "test_single_success_status",
                id="single_success"
            ),
            pytest.param(
                "test_single_failed_status",
                id="single_failed"
            ),
            pytest.param(
                "test_multiple_all_failed_statuses",
                id="multiple_all_failed"
            ),
            pytest.param(
                "test_multiple_all_success_statuses",
                id="multiple_all_success"
            ),
            pytest.param(
                "test_multiple_partial_success_failed_running_statuses",
                id="multiple_partial_success_failed_running"
            ),
            pytest.param(
                "test_multiple_partial_success_failed_running_statuses_across_different_agents_pipelines_rag_configs",
                id="multiple_partial_success_failed_running_different_agents_pipelines_rag_configs"
            ),
        ],
    )
    def test_govtext_lambda_handler_end_to_end(
        self,
        sqs_message_template,
        test_status_inputs,
        httpx_mock,
        mock_aws_infra,
        govtext_param,
        govtext_sqs,
        govtext_bucket,
        govtext_url,
        aibots_param,
        aibots_url,
        log,
        request,
        aws_region,
        tmp_path_factory,
        mock_s3_client,
        clear_environment,
    ):
        status_inputs = request.getfixturevalue(test_status_inputs)

        records = []
        running = []
        for i in status_inputs:
            response = {**i["response"], "job_id": i["job_id"], "status": i["status"]}
            httpx_mock.add_response(status_code=200, json=response, url=govtext_url + f"jobs/{i['job_id']}")
            httpx_mock.add_response(status_code=204, url=f'{aibots_url}' + f"latest/agents/{i['agent_id']}/knowledge/bases/{i['knowledge_base_id']}/statuses?ragConfig={i['rag_config_id']}")
            httpx_mock.add_response(status_code=204, url=aibots_url + f"latest/agents/{i['agent_id']}/rags/{i['rag_config_id']}/statuses")
            status = self.get_sqs_record(
                rag_config_id=i["rag_config_id"],
                pipeline_id=i["pipeline_id"],
                agent_id=i["agent_id"],
                knowledge_base_id=i["knowledge_base_id"],
                job_id=i["job_id"],
                status=i["s3_status"]
            )
            records.append(
                SQSMessageRecord(
                    **{**sqs_message_template, "body": status.model_dump_json()}
                ).model_dump(mode="json", by_alias=True)
            )
            self.upload_file(
                govtext_sqs,
                mock_s3_client,
                govtext_bucket,
                i["agent_id"],
                i["job_id"],
                status,
            )
            if GovTextJobStatus[i["status"]].is_running():
                running.append(i["job_id"])

        assert len(mock_s3_client.list_objects(Bucket=govtext_bucket)['Contents']) == len(status_inputs)

        lambda_handler(
            event=GovTextPipelineStatus(Records=records).model_dump(mode="json", by_alias=True),
            context=None
        )

        for i in status_inputs:
            key = f"schedule/minute/{i['job_id']}_{i['agent_id']}_govtext.json"

            if GovTextJobStatus[i["status"]].is_successful():
                with pytest.raises(ClientError) as error:
                    mock_s3_client.get_object(Bucket=govtext_bucket, Key=key)
                assert error.value.response["Error"]["Code"] == "NoSuchKey"

                assert log.has(
                    "Successfully updated knowledge base status",
                    level="info",
                    data={"knowledge_base_id": i["knowledge_base_id"], "state": i["status"].lower()}
                )
                assert log.has(
                    "Successfully updated rag config status",
                    level="info",
                    data={"rag_config_id": i["rag_config_id"], "state": i["status"].lower()}
                )
                assert log.has(
                    "Handled successful GovText job",
                    level="info",
                    data={"job_id": i["job_id"]}
                )
            elif GovTextJobStatus[i["status"]].is_error():
                with pytest.raises(ClientError) as error:
                    mock_s3_client.get_object(Bucket=govtext_bucket, Key=key)
                assert error.value.response["Error"]["Code"] == "NoSuchKey"

                assert log.has(
                    "Successfully updated knowledge base status",
                    level="info",
                    data={"knowledge_base_id": i["knowledge_base_id"], "state": i["status"].lower()}
                )
                assert log.has(
                    "Successfully updated rag config status",
                    level="info",
                    data={"rag_config_id": i["rag_config_id"], "state": i["status"].lower()}
                )
                assert log.has(
                    "Handled failed GovText job",
                    level="info",
                    data={"job_id": i["job_id"]}
                )
            else:
                status_message = mock_s3_client.get_object(Bucket=govtext_bucket, Key=key)
                output = json.loads(status_message['Body'].read())
                assert output['payload']['id'] == i['pipeline_id']
                assert output['payload']['rag_config'] == i['rag_config_id']
                assert output['payload']['agent'] == i['agent_id']
                assert output['payload']['knowledge_base'] == i['knowledge_base_id']
                assert output['payload']['status'] == i['status'].lower()

                if i["status"].lower() != i["s3_status"]:
                    assert log.has(
                        "Successfully updated knowledge base status",
                        level="info",
                        data={"knowledge_base_id": i["knowledge_base_id"], "state": i["status"].lower()}
                    )
                    assert log.has(
                        "Successfully updated rag config status",
                        level="info",
                        data={"rag_config_id": i["rag_config_id"], "state": i["status"].lower()}
                    )
                    assert log.has(
                        "Handled executing GovText job",
                        level="info",
                        data={"job_id": i["job_id"]}
                    )
                else:
                    assert log.has(
                        "Handled executing GovText job by doing nothing",
                        level="info",
                        data={"job_id": i["job_id"]}
                    )
