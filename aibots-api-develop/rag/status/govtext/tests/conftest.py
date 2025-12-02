import json
import os
from pathlib import Path
from typing import Any, Dict

import boto3
import httpx
import pytest
from atlas.schemas import ExecutionState
from atlas.structlog import StructLogService

from aibots.models import RAGPipelineStages
from aibots.models.rags.internal import StatusResult
from aibots.rags import GovTextEngine
from aibots.models.rags import RAGPipelineStatus
from moto import mock_aws

from ..lambda_function import GovTextStatusEnviron, GovTextStatusExecutor


@pytest.fixture(scope="session")
def aws_region():
    return "ap-southeast-1"


@pytest.fixture(scope="session")
def govtext_url():
    if not os.environ["GOVTEXT_URL"].endswith("/"):
        os.environ["GOVTEXT_URL"] = os.environ["GOVTEXT_URL"] + "/"
    return os.environ["GOVTEXT_URL"]


@pytest.fixture(scope="session")
def govtext_api_key():
    return os.environ["GOVTEXT_API_KEY"]


@pytest.fixture(scope="session")
def govtext_bucket():
    return os.environ["GOVTEXT__BUCKET"]


@pytest.fixture(scope="session")
def govtext_sqs():
    return os.environ["GOVTEXT__SQS"]


@pytest.fixture(scope="session")
def aibots_url():
    return "http://test_url/"


@pytest.fixture(scope="session")
def aibots_api_key():
    return "test_api_key"


@pytest.fixture(scope="session")
def govtext_param():
    param = "param-sitez-aibots-govtext"
    os.environ["GOVTEXT__PARAM"] = param
    yield param
    del os.environ["GOVTEXT__PARAM"]


@pytest.fixture(scope="session")
def aibots_param():
    param = "param-sitezapp-aibots-main-api"
    os.environ["AIBOTS__PARAM"] = param
    yield param
    del os.environ["AIBOTS__PARAM"]


@pytest.fixture(scope="package")
def test_data(request):
    return Path(request.fspath).parent


@pytest.fixture(scope="module")
def govtext_rag_pipeline_status(
    govtext_url, govtext_api_key, test_data
) -> RAGPipelineStatus:
    """
    Sends file to GovText, Creates RAGPipelineStatus
    to be stored in mock AWS bucket
    """
    files: Dict[str, Any] = {
        "files": open(os.path.join(test_data, "data/exampledoc.pdf"), "rb")
    }
    response = httpx.post(
        url=f"{govtext_url}" + "datasets",
        headers={
            "accept": "application/json",
            "X-API-KEY": govtext_api_key,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0",
        },
        json={
            "file_paths": [],
            "chunk_strategy": "FIXED_SIZE",
            "chunk_size": "300",
            "chunk_overlap": "30",
            "chunk_separators": ["\n"],
            "parse_output_format": "TEXT",
        },
        files=files,
    ).json()
    print(response)
    status_result: StatusResult = StatusResult(
        metadata={
            "job_id": response["job_id"],
            "rag_config_id": "efe6b2f55bec4cf6bcace7c360d1ed8e",
            "knowledge_bases": ["fff2f70e87d0478b80ed55473dcbb741"],
        }
    )
    yield RAGPipelineStatus(
        agent="9f5b322c2ada4d8b95c96d4a2ce7af7b",
        rag_config="4e8169ffdcc24610b6215805e6c86a05",
        knowledge_base="a5f5a8fade4c4dd6a4f17e198af8a5d0",
        status=ExecutionState.running,
        results=status_result,
        error=None,
        type=RAGPipelineStages.external,
    )


@pytest.fixture(scope="module")
def mock_logger():
    logger = StructLogService()
    logger.atlas_init()
    return logger.get_structlog_logger("govtext.status")


@pytest.fixture(scope="module")
def mock_aws_infra(
    aws_region,
    govtext_bucket,
    govtext_param,
    govtext_url,
    govtext_api_key,
    aibots_param,
    aibots_url,
    aibots_api_key,
) -> boto3.Session:
    """
    Creates mock AWS environment
    """

    with mock_aws():
        session = boto3.Session(
            aws_access_key_id="FAKE_ACCESS_KEY_ID",
            aws_secret_access_key="FAKE_SECRET_ACCESS_KEY",
            region_name=aws_region,
        )

        ssm = session.client("ssm")
        ssm.put_parameter(
            Name=govtext_param,
            Value=json.dumps(
                {"key": govtext_api_key, "endpoint": govtext_url}
            ),
            Type="SecureString",
        )
        ssm.put_parameter(
            Name=aibots_param,
            Value=json.dumps({"key": aibots_api_key, "endpoint": aibots_url}),
            Type="SecureString",
        )

        yield session


@pytest.fixture()
async def govtext_environ(mock_aws_infra) -> GovTextStatusEnviron:
    from ..lambda_function import init_lambda

    await init_lambda()

    from ..lambda_function import environ

    yield environ


@pytest.fixture()
async def govtext_executor(
    govtext_rag_pipeline_status,
    govtext_environ,
    govtext_engine,
    mock_aws_infra,
    mock_s3_client,
    mock_logger,
):
    executor = GovTextStatusExecutor(
        message=govtext_rag_pipeline_status,
        environ=govtext_environ,
        s3=mock_s3_client,
        engine=govtext_engine,
        logger=mock_logger,
    )
    yield executor


@pytest.fixture()
def govtext_engine(
    govtext_bucket,
    govtext_url,
    govtext_api_key,
    mock_s3_client,
) -> GovTextEngine:
    engine = GovTextEngine(
        s3_bucket=govtext_bucket,
        s3_service=mock_s3_client,
        endpoint=govtext_url,
        headers={
            "accept": "application/json",
            "X-API-KEY": govtext_api_key,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0",
        },
        timeout=httpx.Timeout(
            connect=15.0, read=180.0, write=180.0, pool=15.0
        ),
        limits=httpx.Limits(
            max_keepalive_connections=100, max_connections=500
        ),
        transport=httpx.AsyncHTTPTransport(retries=3),
    )
    yield engine
