import json
from os.path import join
from pathlib import Path

import httpx
import pytest

from io import BytesIO
from aibots.models import RAGPipelineStatus
from aibots.rags import AtlasRAGException
from aibots.rags.govtext import GovTextEngine
from aibots.models.rag_configs import RAGConfig
from aibots.models.knowledge_bases import KnowledgeBase


@pytest.fixture()
async def test_rag_config_wrong_values():
    return RAGConfig(config={
        "chunk_strategy": "WRONG_SIZE",
        "chunk_size": 100,
        "chunk_overlap": 30,
        "chunk_seperator": [],
        "parse_output_format": "WRONG",
        "top_k": 3
    })


@pytest.fixture()
async def test_rag_config_correct_values():
    return RAGConfig(config={
        "chunkStrategy": "FIXED_SIZE",
        "chunkSize": 500,
        "chunkOverlap": 100,
        "chunkSeperator": [],
        "parseOutputFormat": "TEXT",
        "topK": 3
    })


@pytest.fixture()
async def pdf_content(request: pytest.FixtureRequest):
    with open(join(Path(request.fspath).parent, "data", "computer.pdf"), "rb") as f:
        return BytesIO(f.read())


@pytest.fixture()
async def txt_content(request):
    with open(join(Path(request.fspath).parent, "data", "short_story.txt"), "rb") as f:
        return BytesIO(f.read())


@pytest.fixture()
async def docx_content(request):
    with open(join(Path(request.fspath).parent, "data", "test_file.docx"), "rb") as f:
        return BytesIO(f.read())


@pytest.fixture()
async def govtext_engine_wrong_api_key(
    test_agent, test_rag_config, s3_service, govtext_url
):
    engine: GovTextEngine = GovTextEngine(
        s3_bucket="bucket",
        s3_service=s3_service,
        endpoint=govtext_url,
        headers={
            "accept": "application/json",
            "X-API-KEY": "ju2tgs56e653e6ty54e4fe6b6uq4ft4eh4gs56e653e6te4y54e4q",
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


class TestGovText:

    """
    Class used to test GovTextEngine's embedding of documents.
    API_KEY and BASE_URL environment variables from GovText are required to run these test.
    """

    async def test_govtext_engine_atlas_init_pipeline_successful_dataset_creation(
        self, govtext_engine, test_agent, test_rag_config
    ):
        await govtext_engine.atlas_init_pipeline(test_agent, test_rag_config)
        dataset_id = test_rag_config.retrieval.get('datasetId')
        assert len(dataset_id) == 36
        await govtext_engine.atlas_adelete_embeddings_collection(test_rag_config)

    async def test_govtext_engine_atlas_init_pipeline_invalid_api_key(
        self, govtext_engine_wrong_api_key, test_agent, test_rag_config
    ):
        with pytest.raises(AtlasRAGException) as e:
            await govtext_engine_wrong_api_key.atlas_init_pipeline(test_agent, test_rag_config)
            assert e.value.message == "Failed to create dataset"
            assert e.value.status_code == 400

    async def test_govtext_engine_atlas_init_pipeline_govtext_service_down(
        self, govtext_engine, test_agent, test_rag_config, httpx_mock
    ):
        httpx_mock.add_response(status_code=502, html="<body>502 Gateway Error</body>")

        with pytest.raises(AtlasRAGException) as e:
            await govtext_engine.atlas_init_pipeline(test_agent, test_rag_config)
            assert e.value.message == "Failed to create dataset"
            assert e.value.status_code == 502

    # TODO: Uploading duplicate file to S3

    async def test_govtext_engine_atlas_aembed_successfully_string_content(
            self, govtext_engine, test_rag_config, pdf_content, test_agent, s3_service, govtext_sqs
    ):
        knowledge_base: KnowledgeBase = KnowledgeBase(name="computer.pdf")
        await govtext_engine.atlas_init_pipeline(test_agent, test_rag_config)
        embeddings = await govtext_engine.atlas_aembed(
            agent=test_agent,
            rag_config=test_rag_config,
            knowledge_base=knowledge_base,
            content="This is a short sentence"
        )
        if embeddings:
            knowledge_base.embeddings[test_rag_config.id] = embeddings
        assert embeddings
        assert embeddings == knowledge_base.embeddings[test_rag_config.id]
        retrieve = s3_service.service.get_object(
            Bucket='bucket',
            Key=f'schedule/minute/{embeddings.metadata["job_id"]}_{test_agent.id}_govtext.json'
        )
        output = json.loads(retrieve['Body'].read().decode('utf-8'))
        assert output['sqs'] == govtext_sqs
        rag_pipeline_status: RAGPipelineStatus = RAGPipelineStatus.model_validate(output['payload'])
        assert rag_pipeline_status.agent == test_agent.id
        assert rag_pipeline_status.status == "scheduled"
        assert rag_pipeline_status.knowledge_base == knowledge_base.id
        assert rag_pipeline_status.rag_config == test_rag_config.id
        assert rag_pipeline_status.results.metadata.get('job_id') == embeddings.metadata.get('job_id')
        await govtext_engine.atlas_adelete_embeddings_collection(test_rag_config)

    # TODO: Add BytesIO test
    # TODO: Shift all these document uploads to Postman
    # TODO: Add CSV and XLSX to Postman
    async def test_govtext_engine_atlas_aembed_successfully_uploaded_pdf_document(
        self, govtext_engine, test_rag_config, pdf_content, test_agent, s3_service, govtext_sqs
    ):
        knowledge_base: KnowledgeBase = KnowledgeBase(name="computer.pdf")
        await govtext_engine.atlas_init_pipeline(test_agent, test_rag_config)
        embeddings = await govtext_engine.atlas_aembed(
            agent=test_agent,
            rag_config=test_rag_config,
            knowledge_base=knowledge_base,
            content=pdf_content
        )
        if embeddings:
            knowledge_base.embeddings[test_rag_config.id] = embeddings
        assert embeddings
        assert embeddings == knowledge_base.embeddings[test_rag_config.id]
        retrieve = s3_service.service.get_object(
            Bucket='bucket',
            Key=f'schedule/minute/{embeddings.metadata["job_id"]}_{test_agent.id}_govtext.json'
        )
        output = json.loads(retrieve['Body'].read().decode('utf-8'))
        assert output['sqs'] == govtext_sqs
        rag_pipeline_status: RAGPipelineStatus = RAGPipelineStatus.model_validate(output['payload'])
        assert rag_pipeline_status.agent == test_agent.id
        assert rag_pipeline_status.status == "scheduled"
        assert rag_pipeline_status.knowledge_base == knowledge_base.id
        assert rag_pipeline_status.rag_config == test_rag_config.id
        assert rag_pipeline_status.results.metadata.get('job_id') == embeddings.metadata.get('job_id')
        await govtext_engine.atlas_adelete_embeddings_collection(test_rag_config)

    async def test_govtext_engine_atlas_aembed_successfully_uploaded_txt_document(
            self, govtext_engine, test_rag_config, txt_content, test_agent, s3_service, govtext_sqs
    ):
        knowledge_base: KnowledgeBase = KnowledgeBase(name="short_story.txt")
        await govtext_engine.atlas_init_pipeline(test_agent, test_rag_config)
        embeddings = await govtext_engine.atlas_aembed(
            agent=test_agent,
            rag_config=test_rag_config,
            knowledge_base=knowledge_base,
            content=txt_content
        )
        if embeddings:
            knowledge_base.embeddings[test_rag_config.id] = embeddings
        assert embeddings
        assert embeddings == knowledge_base.embeddings[test_rag_config.id]
        retrieve = s3_service.service.get_object(
            Bucket='bucket',
            Key=f'schedule/minute/{embeddings.metadata["job_id"]}_{test_agent.id}_govtext.json')
        output = json.loads(retrieve['Body'].read().decode('utf-8'))
        assert output['sqs'] == govtext_sqs
        rag_pipeline_status: RAGPipelineStatus = RAGPipelineStatus.model_validate(output['payload'])
        assert rag_pipeline_status.agent == test_agent.id
        assert rag_pipeline_status.status == "scheduled"
        assert rag_pipeline_status.knowledge_base == knowledge_base.id
        assert rag_pipeline_status.rag_config == test_rag_config.id
        assert rag_pipeline_status.results.metadata.get('job_id') == embeddings.metadata.get('job_id')
        await govtext_engine.atlas_adelete_embeddings_collection(test_rag_config)

    async def test_govtext_engine_atlas_aembed_successfully_uploaded_docx_document(
        self, govtext_engine, test_rag_config, docx_content, test_agent, s3_service, govtext_sqs
    ):
        knowledge_base: KnowledgeBase = KnowledgeBase(name="test_file.docx")
        await govtext_engine.atlas_init_pipeline(test_agent, test_rag_config)
        embeddings = await govtext_engine.atlas_aembed(
            agent=test_agent,
            rag_config=test_rag_config,
            knowledge_base=knowledge_base,
            content=docx_content
        )
        if embeddings:
            knowledge_base.embeddings[test_rag_config.id] = embeddings
        assert embeddings
        assert embeddings == knowledge_base.embeddings[test_rag_config.id]
        retrieve = s3_service.service.get_object(
            Bucket='bucket',
            Key=f'schedule/minute/{embeddings.metadata["job_id"]}_{test_agent.id}_govtext.json')
        output = json.loads(retrieve['Body'].read().decode('utf-8'))
        assert output['sqs'] == govtext_sqs
        rag_pipeline_status: RAGPipelineStatus = RAGPipelineStatus.model_validate(output['payload'])
        assert rag_pipeline_status.agent == test_agent.id
        assert rag_pipeline_status.status == "scheduled"
        assert rag_pipeline_status.knowledge_base == knowledge_base.id
        assert rag_pipeline_status.rag_config == test_rag_config.id
        assert rag_pipeline_status.results.metadata.get('job_id') == embeddings.metadata.get('job_id')
        await govtext_engine.atlas_adelete_embeddings_collection(test_rag_config)

    async def test_govtext_engine_atlas_dataset_not_initialised(
            self, govtext_engine, test_rag_config, test_agent, s3_service,
    ):
        knowledge_base: KnowledgeBase = KnowledgeBase(name="test_kb")
        with pytest.raises(AtlasRAGException) as e:
            await govtext_engine.atlas_aembed(
                agent=test_agent,
                rag_config=test_rag_config,
                knowledge_base=knowledge_base,
                content="example short string"
            )
        assert e.value.status_code == 404
        assert (e.value.details["response"] ==
                '{"error":{"type":"Not Found","status":404,"message":"Dataset None not found.","details":[]}}')

    async def test_govtext_engine_atlas_aembed_upload_pdf_document_with_wrong_rag_config(
            self, govtext_engine, test_rag_config_wrong_values, pdf_content, test_agent, s3_service
    ):
        knowledge_base = KnowledgeBase(name="computer.pdf")

        await govtext_engine.atlas_init_pipeline(test_agent, test_rag_config_wrong_values)
        with pytest.raises(AtlasRAGException) as exc_info:
            embeddings = await govtext_engine.atlas_aembed(
                agent=test_agent,
                rag_config=test_rag_config_wrong_values,
                knowledge_base=knowledge_base,
                content=pdf_content
            )

        assert exc_info.value.message == 'Failed to create embedding'
        await govtext_engine.atlas_adelete_embeddings_collection(test_rag_config_wrong_values)

    async def test_govtext_engine_atlas_aembed_successfully_upload_pdf_document_with_correct_rag_config(
            self, govtext_engine, test_rag_config_correct_values, pdf_content, test_agent, s3_service, govtext_sqs
    ):
        knowledge_base: KnowledgeBase = KnowledgeBase(name="computer.pdf")
        await govtext_engine.atlas_init_pipeline(test_agent, test_rag_config_correct_values)
        embeddings = await govtext_engine.atlas_aembed(
            agent=test_agent,
            rag_config=test_rag_config_correct_values,
            knowledge_base=knowledge_base,
            content=pdf_content
        )
        if embeddings:
            knowledge_base.embeddings[test_rag_config_correct_values.id] = embeddings
        assert embeddings
        assert embeddings == knowledge_base.embeddings[test_rag_config_correct_values.id]
        retrieve = s3_service.service.get_object(
            Bucket='bucket',
            Key=f'schedule/minute/{embeddings.metadata["job_id"]}_{test_agent.id}_govtext.json'
        )
        output = json.loads(retrieve['Body'].read().decode('utf-8'))
        assert output['sqs'] == govtext_sqs
        rag_pipeline_status: RAGPipelineStatus = RAGPipelineStatus.model_validate(output['payload'])
        assert rag_pipeline_status.agent == test_agent.id
        assert rag_pipeline_status.status == "scheduled"
        assert rag_pipeline_status.knowledge_base == knowledge_base.id
        assert rag_pipeline_status.rag_config == test_rag_config_correct_values.id
        assert rag_pipeline_status.results.metadata.get('job_id') == embeddings.metadata.get('job_id')
        assert test_rag_config_correct_values.config.get('chunkSize') == 500
        assert test_rag_config_correct_values.config.get('chunkOverlap') == 100
        await govtext_engine.atlas_adelete_embeddings_collection(test_rag_config_correct_values)
