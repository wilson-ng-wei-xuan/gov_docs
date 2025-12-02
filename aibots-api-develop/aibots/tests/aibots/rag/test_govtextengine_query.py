import httpx
import pytest

from pydantic.alias_generators import to_snake

from aibots.rags import AtlasRAGException
from aibots.rags.govtext import GovTextEngine
from aibots.models.rag_configs import RAGConfig
from aibots.models.knowledge_bases import KnowledgeBase


@pytest.fixture()
def default_rag_config():
    return RAGConfig(
        retrieval={
            "datasetId": "29a35cc9-4f1d-4808-b711-b9736b22d0a1"
        }
    )


@pytest.fixture()
def top_k_rag_config():
    return RAGConfig(
        retrieval={
            "datasetId": "29a35cc9-4f1d-4808-b711-b9736b22d0a1",
            "topK": 5
        }
    )

@pytest.fixture()
def non_existent_dataset_rag_config():
    return RAGConfig(
        retrieval={
            "datasetId": "12b35cc9-4f1d-4808-b711-b9736b22d111",
        }
    )

@pytest.fixture()
def test_rag_config_negative_top_k():
    return RAGConfig(
        retrieval={
            "datasetId": "29a35cc9-4f1d-4808-b711-b9736b22d0a1",
            "topK": -2
        }
    )


@pytest.fixture()
def test_rag_config_wrong_top_k():
    return RAGConfig(
        retrieval={
            "datasetId": "29a35cc9-4f1d-4808-b711-b9736b22d0a1",
            "topK": "wrong"
        }
    )


@pytest.fixture()
def test_knowledge_base():
    return KnowledgeBase(name="Kb1")


@pytest.fixture()
async def govtext_engine_fast_timeout(
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
            connect=15.0, read=0.1, write=180.0, pool=15.0
        ),
        limits=httpx.Limits(
            max_keepalive_connections=100, max_connections=500
        ),
        transport=httpx.AsyncHTTPTransport(retries=3),
    )
    await engine.atlas_ainit()
    return engine


class TestGovTextQuery:
    """
    Class used to test GovTextEngine's querying.
    API_KEY and BASE_URL environment variables from GovText are required to run these test.
    """

    @pytest.mark.parametrize(
        argnames="rag_config, output, prompt",
        argvalues=[
            # manually updated the dataset id to a dataset that already has documents embedded to test querying
            pytest.param(
                "default_rag_config",
                [
                    {'source': 'Archive/story.txt', 'chunk': 401},
                    {'source': 'Archive/story.txt', 'chunk': 1367},
                    {'source': 'Archive/story.txt', 'chunk': 481},
                    {'source': 'Archive/story.txt', 'chunk': 959},
                    {'source': 'Archive/story.txt', 'chunk': 385},
                ],
                "what happen in season 7?",
                id="default_variables"
            ),
            pytest.param(
                "top_k_rag_config",
                [
                    {"source": 'Archive/story.txt', "chunk": 401},
                    {"source": 'Archive/story.txt', "chunk": 1367},
                    {"source": 'Archive/story.txt', "chunk": 481},
                    {"source": 'Archive/story.txt', "chunk": 959},
                    {"source": 'Archive/story.txt', "chunk": 385}
                ],
                "what happen in season 7?",
                id="top_k_retrieved"
            )
        ]
    )
    async def test_successful_querying_of_dataset(
        self, test_agent, rag_config, output, test_knowledge_base, govtext_engine, request, prompt
    ):
        rag_config = request.getfixturevalue(rag_config)
        chunks = await govtext_engine.atlas_aquery(
            prompt=prompt,
            agent=test_agent,
            rag_config=rag_config,
            knowledge_bases=[test_knowledge_base],
            **{to_snake(k): v for k, v in rag_config.retrieval.items() if k != "datasetId"}
        )
        assert len(chunks) == len(output)
        for chunk, test_output in zip(chunks, output):
            assert chunk.source == test_output['source']
            assert len(chunk.chunk) == test_output['chunk']

    @pytest.mark.parametrize(
        argnames="test_rag_config, prompt, output, error",
        argvalues=[
            pytest.param(
                "non_existent_dataset_rag_config",
                "what happen in season 7?",
                "Unable to execute query flow",
                "Not Found",
                id="non_existent_dataset"
            ),
            pytest.param(
                "test_rag_config_negative_top_k",
                "what happen in season 7?",
                "Unable to execute query flow",
                "Input should be greater than or equal to 0",
                id="negative_top_k"
            ),
            pytest.param(
                "test_rag_config_wrong_top_k",
                "what happen in season 7?",
                "Unable to execute query flow",
                "Input should be a valid integer, unable to parse string as an integer",
                id="wrong_top_k"
            )
        ]
    )
    async def test_querying_errors(
            self, test_agent, test_rag_config, test_knowledge_base, govtext_engine, request, prompt, output, error
    ):
        rag_config = request.getfixturevalue(test_rag_config)

        with pytest.raises(AtlasRAGException) as exc_info:
            await govtext_engine.atlas_aquery(
                prompt=prompt,
                agent=test_agent,
                rag_config=rag_config,
                knowledge_bases=[test_knowledge_base],
            )

        assert exc_info.value.message == output
        assert (error in exc_info.value.details['response'])

    async def test_querying_dataset_immediately(
            self, test_agent, test_rag_config, test_knowledge_base, govtext_engine
    ):
        await govtext_engine.atlas_init_pipeline(test_agent, test_rag_config)

        await govtext_engine.atlas_aembed(
            agent=test_agent,
            rag_config=test_rag_config,
            knowledge_base=test_knowledge_base,
            content="This is an example short sentence"
        )

        with pytest.raises(AtlasRAGException) as exc_info:
            await govtext_engine.atlas_aquery(
                prompt="what happen in season 7?",
                agent=test_agent,
                rag_config=test_rag_config,
                knowledge_bases=[test_knowledge_base],
            )

        assert exc_info.value.message == "Unable to execute query flow"


    async def test_timeout_error_with_fast_timeout_engine(
        self, test_agent, default_rag_config, test_knowledge_base, govtext_engine_fast_timeout
    ):

        # Use pytest.raises to check for TimeoutException
        with pytest.raises(httpx.TimeoutException):
            await govtext_engine_fast_timeout.atlas_aquery(
                prompt="what happen in season 7?",
                agent=test_agent,
                rag_config=default_rag_config,
                knowledge_bases=[test_knowledge_base],
            )