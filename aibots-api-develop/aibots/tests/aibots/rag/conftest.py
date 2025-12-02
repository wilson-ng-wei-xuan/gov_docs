import os

from moto import mock_aws
import httpx
import pytest

from aibots.rags.govtext import GovTextEngine
from atlas.boto3.services import S3Service
from aibots.models.agents import Agent
from aibots.models.rag_configs import RAGConfig


@pytest.fixture(scope="session")
def govtext_url():
    if not os.environ["GOVTEXT_URL"].endswith("/"):
        os.environ["GOVTEXT_URL"] = os.environ["GOVTEXT_URL"] + "/"
    return os.environ["GOVTEXT_URL"]


@pytest.fixture(scope="session")
def govtext_api_key():
    return os.environ["GOVTEXT_API_KEY"]


@pytest.fixture(scope="session")
def govtext_sqs():
    return os.environ["GOVTEXT__SQS"]


@pytest.fixture()
def s3_service():
    with mock_aws():
        service = S3Service(region_name="us-east-1")
        service.atlas_init()

        service.create_bucket(Bucket="bucket")

        yield service
        service.atlas_close()


@pytest.fixture()
def test_agent():
    return Agent(name="Agent1", agency="dsta")


@pytest.fixture()
def test_rag_config():
    return RAGConfig()


@pytest.fixture()
async def govtext_engine(
    test_agent, s3_service, govtext_url, govtext_api_key
):
    engine: GovTextEngine = GovTextEngine(
        s3_bucket="bucket",
        s3_service=s3_service,
        endpoint=govtext_url,
        headers={
            "accept": "application/json",
            "X-API-KEY": govtext_api_key,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0)"
                          " Gecko/20100101 Firefox/81.0",
        },
        timeout=httpx.Timeout(
            connect=15.0, read=180.0, write=180.0, pool=15.0
        ),
        limits=httpx.Limits(
            max_keepalive_connections=100, max_connections=500
        ),
        transport=httpx.AsyncHTTPTransport(retries=3),
    )
    await engine.atlas_ainit()
    return engine



