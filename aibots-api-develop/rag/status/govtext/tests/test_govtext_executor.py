import json
import logging
from copy import deepcopy
from io import BytesIO
from unittest.mock import Mock

import httpx
import pytest
from atlas.schemas import State, ExecutionState
from botocore.exceptions import ClientError

from aibots.models import RAGPipelineStages
from aibots.models.rags import RAGPipelineStatus
from aibots.models.rags.internal import StatusResult
from aibots.rags import AtlasRAGException, GovTextEngine
from aibots.rags.govtext import GovTextJobResponse, GovTextJobStatus

from ..lambda_function import GovTextStatusEnviron, GovTextStatusExecutor


@pytest.fixture
def govtext_invalid_api_key():
    return "7c1d015e774f123a3db13cfad12444b3b330707f83c936d011a7a838662a03bc"


@pytest.fixture()
def mock_s3_client(
    aws_region,
    govtext_bucket,
    mock_aws_infra,
    govtext_rag_pipeline_status,
):
    # creates scheduler bucket
    s3 = mock_aws_infra.client("s3", region_name=aws_region)
    s3.create_bucket(
        Bucket=govtext_bucket,
        CreateBucketConfiguration={"LocationConstraint": aws_region},
    )

    s3.upload_fileobj(
        BytesIO(govtext_rag_pipeline_status.model_dump_json().encode("utf-8")),
        govtext_bucket,
        f"schedule/minute/"
        f"{govtext_rag_pipeline_status.results.metadata['job_id']}_"
        f"{govtext_rag_pipeline_status.agent}_govtext.json"
    )
    yield s3

    objs = s3.list_objects(Bucket=govtext_bucket)
    for obj in objs.get("Contents", []):
        s3.delete_object(Bucket=govtext_bucket, Key=obj["Key"])
    s3.delete_bucket(
        Bucket=govtext_bucket,
    )


@pytest.fixture()
def govtext_rag_pipeline_status_absent_file() -> RAGPipelineStatus:
    """
    Returns:
        RAGPipelineStatus with non-existent file
    """
    status_result: StatusResult = StatusResult(
        metadata={
            "job_id": "2574b82d5cca40b99abb10bbdf5e6818",
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


@pytest.fixture()
def govtext_rag_pipeline_status_wrong_format() -> RAGPipelineStatus:
    """
    Sends file to GovText, Creates incorrect RAGPipelineStatus
    to be stored in mock AWS bucket
    """
    status_result: StatusResult = StatusResult(
        metadata={
            "wrong_job_id": "wrong_job_id",
            "wrong_knowledge_bases": [1, 2, 3],
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


@pytest.fixture
def govtext_engine_invalid_api_key(
    govtext_bucket,
    govtext_url,
    govtext_invalid_api_key,
    mock_s3_client,
):
    engine = GovTextEngine(
        s3_bucket=govtext_bucket,
        s3_service=mock_s3_client,
        endpoint=govtext_url,
        headers={
            "accept": "application/json",
            "X-API-KEY": govtext_invalid_api_key,
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
    return engine


class TestGovTextExecutor:
    async def test_govtext_executor_call_success(
        self,
        govtext_environ,
        mock_aws_infra,
        mock_s3_client,
        govtext_rag_pipeline_status,
        govtext_engine,
        mock_logger,
    ):
        # tests call to govtext staging environment for status

        environ: GovTextStatusEnviron = govtext_environ
        await govtext_engine.atlas_ainit()
        poller = GovTextStatusExecutor(
            message=govtext_rag_pipeline_status,
            environ=environ,
            s3=mock_s3_client,
            engine=govtext_engine,
            logger=mock_logger,
        )

        response: RAGPipelineStatus = await poller()
        assert response.status == ExecutionState.completed
        assert isinstance(response.results, StatusResult)
        status_result: StatusResult = response.results
        assert GovTextJobResponse.model_validate(status_result.metadata)

    @pytest.mark.parametrize(
        argnames="test_status_message, test_govtext_engine, test_output",
        argvalues=[
            pytest.param(
                "govtext_rag_pipeline_status_absent_file",
                "govtext_engine",
                {"status_code": 404},
                id="job_id_not_found",
            ),
            pytest.param(
                "govtext_rag_pipeline_status",
                "govtext_engine_invalid_api_key",
                {"status_code": 403},
                id="invalid_api_key",
            ),
            pytest.param(
                "govtext_rag_pipeline_status_wrong_format",
                "govtext_engine",
                {"status_code": 400},
                id="invalid_pipeline_status_message",
            ),
        ],
    )
    async def test_govtext_executor_call_errors(
        self,
        test_status_message,
        test_output,
        test_govtext_engine,
        govtext_environ,
        mock_aws_infra,
        mock_s3_client,
        mock_logger,
        request,
    ):
        status_message = request.getfixturevalue(test_status_message)
        engine = request.getfixturevalue(test_govtext_engine)
        await engine.atlas_ainit()
        poller = GovTextStatusExecutor(
            message=status_message,
            environ=govtext_environ,
            s3=mock_s3_client,
            engine=engine,
            logger=mock_logger,
        )
        with pytest.raises(AtlasRAGException) as e:
            await poller()
        assert e.value.status_code == test_output["status_code"]

    async def test_govtext_executor_next_status_message_already_seen(
        self,
        mocker,
        caplog,
        govtext_executor
    ):
        job_response_model: GovTextJobResponse = GovTextJobResponse(
            **{
                "job_id": "c0c8fa1b-3987-469d-b706-390a8bbaf69f",
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "status": GovTextJobStatus.RUNNING,
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
            }
        )
        mock_set_kb_state = Mock()
        mock_set_rag_config_state = Mock()

        mocker.patch(
            "govtext.lambda_function.GovTextStatusExecutor.set_kb_state",
            mock_set_kb_state,
        )
        mocker.patch(
            "govtext.lambda_function.GovTextStatusExecutor.set_rag_config_state",
            mock_set_rag_config_state,
        )
        govtext_executor.next(response=job_response_model, seen=["c0c8fa1b-3987-469d-b706-390a8bbaf69f"])
        assert len(caplog.records) == 0
        assert mock_set_rag_config_state.call_count == 0
        assert mock_set_kb_state.call_count == 0

    @pytest.mark.parametrize(
        argnames=[
            "govtext_job_status",
            "log_message",
            "test_set_kb_state",
            "test_set_rag_config_state",
        ],
        argvalues=[
            pytest.param(
                GovTextJobStatus.COMPLETED,
                "Handled successful GovText job",
                {"count": 1, "state": "completed"},
                {"count": 1, "state": "completed"},
                id="test_job_status_completed",
            ),
            pytest.param(
                GovTextJobStatus.FAILED,
                "Handled failed GovText job",
                {"count": 1, "state": "failed"},
                {"count": 1, "state": "failed"},
                id="test_job_status_failed",
            ),
            pytest.param(
                GovTextJobStatus.CRASHED,
                "Handled failed GovText job",
                {"count": 1, "state": "crashed"},
                {"count": 1, "state": "crashed"},
                id="test_job_status_crashed",
            ),
            pytest.param(
                GovTextJobStatus.CANCELLED,
                "Handled failed GovText job",
                {"count": 1, "state": "cancelled"},
                {"count": 1, "state": "cancelled"},
                id="test_job_status_cancelled",
            ),
            pytest.param(
                GovTextJobStatus.CANCELLING,
                "Handled failed GovText job",
                {"count": 1, "state": "cancelling"},
                {"count": 1, "state": "cancelling"},
                id="test_job_status_cancelling",
            ),
            pytest.param(
                GovTextJobStatus.CANCELLING,
                "Handled failed GovText job",
                {"count": 1, "state": "cancelling"},
                {"count": 1, "state": "cancelling"},
                id="test_job_already_seen",
            )
        ],
    )
    async def test_govtext_next_status_success_fail_update(
        self,
        mocker,
        caplog,
        govtext_executor,
        govtext_job_status,
        log_message,
        test_set_kb_state,
        test_set_rag_config_state,
    ) -> None:
        job_response_model: GovTextJobResponse = GovTextJobResponse(
            **{
                "job_id": "c0c8fa1b-3987-469d-b706-390a8bbaf69f",
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "status": govtext_job_status,
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
            }
        )

        mock_set_kb_state = Mock()
        mock_set_rag_config_state = Mock()

        mocker.patch(
            "govtext.lambda_function.GovTextStatusExecutor.set_kb_state",
            mock_set_kb_state,
        )
        mocker.patch(
            "govtext.lambda_function.GovTextStatusExecutor.set_rag_config_state",
            mock_set_rag_config_state,
        )

        with caplog.at_level(logging.INFO, logger="status.govtext.execute"):
            govtext_executor.next(response=job_response_model, seen=set())
        assert caplog.records[0].msg["event"] == log_message
        assert mock_set_kb_state.call_count == test_set_kb_state["count"]
        if test_set_kb_state.get("state"):
            assert (
                    mock_set_kb_state.call_args[1]["state"].state
                    == test_set_kb_state["state"]
            )
        assert (
                mock_set_rag_config_state.call_count
                == test_set_rag_config_state["count"]
        )
        if test_set_rag_config_state.get("state"):
            assert (
                    mock_set_rag_config_state.call_args[1]["state"].state
                    == test_set_rag_config_state["state"]
            )

    @pytest.mark.parametrize(
        argnames=[
            "before_status",
            "after_status",
            "log_message",
            "test_set_kb_state",
            "test_set_rag_config_state",
        ],
        argvalues=[
            pytest.param(
                GovTextJobStatus.SCHEDULED,
                GovTextJobStatus.RUNNING,
                "Handled executing GovText job",
                {"count": 1, "state": "running"},
                {"count": 1, "state": "running"},
                id="test_job_status_running",
            ),
            pytest.param(
                GovTextJobStatus.SCHEDULED,
                GovTextJobStatus.PAUSED,
                "Handled executing GovText job",
                {"count": 1, "state": "paused"},
                {"count": 1, "state": "paused"},
                id="test_job_status_paused",
            ),
            pytest.param(
                GovTextJobStatus.SCHEDULED,
                GovTextJobStatus.PENDING,
                "Handled executing GovText job",
                {"count": 1, "state": "pending"},
                {"count": 1, "state": "pending"},
                id="test_job_status_pending",
            ),
            pytest.param(
                GovTextJobStatus.PAUSED,
                GovTextJobStatus.SCHEDULED,
                "Handled executing GovText job",
                {"count": 1, "state": "scheduled"},
                {"count": 1, "state": "scheduled"},
                id="test_job_status_scheduled",
            ),
            pytest.param(
                GovTextJobStatus.SCHEDULED,
                GovTextJobStatus.SCHEDULED,
                "Handled executing GovText job by doing nothing",
                {"count": 0},
                {"count": 0},
                id="test_job_status_do_nothing",
            ),
        ],
    )
    async def test_govtext_next_status_executing_update(
        self,
        mocker,
        caplog,
        govtext_executor,
        govtext_rag_pipeline_status,
        before_status,
        after_status,
        log_message,
        test_set_kb_state,
        test_set_rag_config_state,
    ) -> None:
        mock_set_kb_state = Mock()
        mock_set_rag_config_state = Mock()

        mocker.patch(
            "govtext.lambda_function.GovTextStatusExecutor.set_kb_state",
            mock_set_kb_state,
        )
        mocker.patch(
            "govtext.lambda_function.GovTextStatusExecutor.set_rag_config_state",
            mock_set_rag_config_state,
        )
        status_message: RAGPipelineStatus = deepcopy(govtext_rag_pipeline_status)
        govtext_executor.message = status_message
        status_message.status = ExecutionState[before_status.lower()]
        govtext_executor.message = status_message
        job_response_model: GovTextJobResponse = GovTextJobResponse(
            **{
                "job_id": "c0c8fa1b-3987-469d-b706-390a8bbaf69f",
                "dataset_id": "902f1c53-d12b-475d-95c4-bdc07e441bc2",
                "job_type": "INGEST",
                "status": after_status,
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
            }
        )
        with caplog.at_level(logging.INFO, logger="status.govtext.execute"):
            govtext_executor.next(response=job_response_model, seen=set())
        assert caplog.records[0].msg["event"] == log_message
        assert mock_set_kb_state.call_count == test_set_kb_state["count"]
        if test_set_kb_state.get("state"):
            assert (
                    mock_set_kb_state.call_args[1]["state"].state
                    == test_set_kb_state["state"]
            )
        assert (
                mock_set_rag_config_state.call_count
                == test_set_rag_config_state["count"]
        )
        if test_set_rag_config_state.get("state"):
            assert (
                    mock_set_rag_config_state.call_args[1]["state"].state
                    == test_set_rag_config_state["state"]
            )

    def test_govtext_delete_file_from_bucket_successfully_deleted_file_from_bucket(
        self,
        govtext_executor,
        mock_s3_client,
        govtext_bucket,
        govtext_rag_pipeline_status,
    ) -> None:
        key = f"schedule/minute/{govtext_rag_pipeline_status.results.metadata['job_id']}_{govtext_rag_pipeline_status.agent}_govtext.json"
        govtext_executor.delete_file_from_bucket(
            bucket=govtext_bucket, key=key
        )
        with pytest.raises(ClientError) as error:
            mock_s3_client.get_object(Bucket=govtext_bucket, Key=key)
        assert error.value.response["Error"]["Code"] == "NoSuchKey"

    async def test_govtext_delete_file_from_bucket_non_existent_bucket_error(
            self, govtext_executor
    ) -> None:
        with pytest.raises(AtlasRAGException) as error:
            await govtext_executor.delete_file_from_bucket(
                bucket="this_bucket_does_not_exist",
                key="this_file_does_not_exist",
            )
        assert error.value.status_code == "NoSuchBucket"
        assert error.value.message == "The specified bucket does not exist"

    async def test_govtext_update_kb_failed(
            self, govtext_executor, httpx_mock
    ) -> None:
        httpx_mock.add_response(
            status_code=404,
            json={"message": "Knowledge Base does not exist", "code": 404},
        )

        with pytest.raises(AtlasRAGException) as error:
            await govtext_executor.set_kb_state(
                agent_id="e2ed604e70e747cf91236f3498ee50d4",
                kb_id="bb8bdcbfb0a2422891543149f9141aea",
                rag_config_id="c0bf32cf2abc4094afbb61c462e05cb4",
                state=State(state=ExecutionState.completed),
            )
        assert error.value.status_code == 404
        assert error.value.message == "Knowledge Base does not exist"

    async def test_govtext_update_rag_config_failed(
        self, govtext_executor, httpx_mock
    ) -> None:
        httpx_mock.add_response(
            status_code=404,
            json={"message": "RAG Config does not exist", "code": 404},
        )

        with pytest.raises(AtlasRAGException) as error:
            await govtext_executor.set_rag_config_state(
                agent_id="e2ed604e70e747cf91236f3498ee50d4",
                rag_config_id="c0bf32cf2abc4094afbb61c462e05cb4",
                state=State(state=ExecutionState.completed),
            )
        assert error.value.status_code == 404
        assert error.value.message == "RAG Config does not exist"

    async def test_govtext_update_bucket_rag_status_pipeline_file_success(
        self,
        mock_s3_client,
        govtext_bucket,
        govtext_rag_pipeline_status,
        govtext_executor
    ) -> None:
        key = f"schedule/minute/{govtext_rag_pipeline_status.results.metadata['job_id']}_{govtext_rag_pipeline_status.agent}_govtext.json"
        status_message_copy = deepcopy(govtext_rag_pipeline_status)
        status_message_copy.status = ExecutionState.pending
        govtext_executor.update_bucket_rag_config_file(
            updated_rag_pipeline_status=status_message_copy, key=key
        )
        response = mock_s3_client.get_object(Bucket=govtext_bucket, Key=key)['Body'].read().decode('utf-8')
        status_json = json.loads(response)
        assert RAGPipelineStatus.model_validate(status_json["payload"])
        assert RAGPipelineStatus(**status_json["payload"]).status == ExecutionState.pending

    async def test_govtext_update_bucket_rag_status_pipeline_file_wrong_bucket(
        self,
        govtext_executor,
        govtext_rag_pipeline_status
    ) -> None:
        with pytest.raises(AtlasRAGException) as error:
            govtext_executor.environ.govtext.bucket = "this_bucket_does_not_exists"
            await govtext_executor.update_bucket_rag_config_file(
                updated_rag_pipeline_status=govtext_rag_pipeline_status,
                key="this_file_does_not_exist",
            )
        assert error.value.status_code == "NoSuchBucket"
        assert error.value.message == "The specified bucket does not exist"
