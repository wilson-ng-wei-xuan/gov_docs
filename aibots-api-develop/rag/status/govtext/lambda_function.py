from __future__ import annotations

import asyncio
import io
import json
from copy import deepcopy
from typing import Any, Callable

import httpx
from aibots.models import (
    RAGPipelineStages,
    RAGPipelineStatus,
)
from aibots.models.rags.internal import SQSMessage, StatusResult
from aibots.rags import AtlasRAGException, GovTextEngine
from aibots.rags.govtext import GovTextJobResponse, GovTextJobStatus
from atlas.boto3.services import S3Service, SSMService
from atlas.environ import AWSEnvVars, ServiceEnvVars
from atlas.schemas import ExecutionState, State
from atlas.structlog import StructLogService
from botocore.exceptions import ClientError
from httpx import Response
from pydantic import AnyUrl, BaseModel, ValidationError, validate_call
from pydantic_settings import BaseSettings, SettingsConfigDict


# TODO: Fix this when https://github.com/pydantic/pydantic/issues/7713
#  is addressed
class GovTextPipelineStatus(SQSMessage[RAGPipelineStatus]):
    """
    GovText Pipeline Status message extracted from SQS

    Attributes:
        records (List[RAGPipelineStatus]): List of SQS records
                                           collected
    """


class GovTextStatusEnviron(BaseSettings, AWSEnvVars):
    """
    Environment variables for GovTextStatus

    Attributes:
        aws_id (Optional[str]): AWS Account ID, defaults to None
        aws_access_id (str): AWS Access ID, defaults to None
        aws_secret_key (str): AWS Secret Access Key, defaults to None
        aws_region (str): AWS operational region, defaults to ap-southeast-1
        aws_endpoint_url (Optional[AnyUrl]): AWS endpoint URL, defaults to None

        govtext (ServiceEnvVars | None): GovText initialisation parameters,
                                         defaults to None
        aibots (ServiceEnvVars | None): AIBots initialisation parameters,
                                        defaults to None
    """

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_nested_delimiter="__"
    )

    govtext: ServiceEnvVars | None = None
    aibots: ServiceEnvVars | None = None


class GovTextStatusMessage(BaseModel):
    """
    Base Model for GovText Bucket Poller Body

    Attributes:
        knowledge_bases (list[str]): List of knowledge bases
        job_id (str): ID of the Job
    """

    knowledge_bases: list[str]
    job_id: str


class GovTextStatusExecutor:
    """
    Base class for GovTextStatus

    Attributes:
        message (RAGPipelineStatus): Incoming Status message
        engine (GovTextEngine): GovText Engine
        environ (GovTextStatusEnviron): GovText environment variables
        s3 (S3Service): S3 Service
        logger (Any): Logger for logging details
    """

    def __init__(
        self,
        message: RAGPipelineStatus,
        engine: GovTextEngine,
        environ: GovTextStatusEnviron,
        s3: S3Service,
        logger: Any,
    ):
        self.message = message
        self.environ = environ
        self.s3: S3Service = s3
        self.engine: GovTextEngine = engine
        self.is_async: bool = True
        self.logger = logger

    async def __call__(self) -> RAGPipelineStatus:
        """
        Checks the govtext job status

        Returns:
            RAGPipelineStatus: Status of the GovText job
        """
        status_result: StatusResult = self.message.results
        try:
            govtext_pipeline_message: GovTextStatusMessage = (
                GovTextStatusMessage(**status_result.metadata)
            )
        except ValidationError as e:
            raise AtlasRAGException(
                status_code=400,
                message=str(e),
            ) from e

        response: GovTextJobResponse = await self.engine.get_job_status(
            job_id=str(govtext_pipeline_message.job_id)
        )

        return RAGPipelineStatus(
            id=self.message.id,
            agent=self.message.agent,
            rag_config=self.message.rag_config,
            status=ExecutionState.completed,
            knowledge_base=self.message.knowledge_base,
            error=None,
            results=StatusResult(metadata=response.model_dump(mode="json")),
            type=RAGPipelineStages.external,
        )

    def next(self, response: GovTextJobResponse, seen: set[str]) -> None:
        """
        Next function handles the states of the GovTextJob

        Attributes:
            response (GovTextJobResponse): Job response model
            seen (set[str]): Seen set

        Returns:
            None
        """

        def handle_success(
            job: GovTextJobResponse,
            status_message: GovTextStatusMessage,
            key: str,
        ) -> bool:
            """
            Strategy for handling successful scenarios

            Args:
                job (GovTextJobResponse): Response model
                status_message (GovTextStatusMessage): Status Metadata
                key (str): Bucket key

            Returns:
                bool: Indicates if the successful scenario was
                      activated
            """
            if response.status.is_successful():
                self.delete_file_from_bucket(
                    bucket=self.environ.govtext.bucket, key=key
                )
                self.set_kb_state(
                    state=State(state=ExecutionState.completed),
                    agent_id=self.message.agent,
                    kb_id=self.message.knowledge_base,
                    rag_config_id=self.message.rag_config,
                )
                self.set_rag_config_state(
                    state=State(state=ExecutionState.completed),
                    agent_id=self.message.agent,
                    rag_config_id=self.message.rag_config,
                )
                self.logger.info(
                    "Handled successful GovText job",
                    data={"job_id": status_message.job_id},
                )
                return True
            return False

        def handle_failure(
            job: GovTextJobResponse,
            status_message: GovTextStatusMessage,
            key: str,
        ) -> bool:
            """
            Strategy for handling failure scenarios

            Args:
                job (GovTextJobResponse): Response model
                status_message (GovTextStatusMessage): Status Metadata
                key (str): Bucket key

            Returns:
                bool: Indicates if the failure scenario was
                      activated
            """
            if response.status.is_error():
                state: dict[GovTextJobStatus, ExecutionState] = {
                    GovTextJobStatus.FAILED.value: ExecutionState.failed,
                    GovTextJobStatus.CRASHED.value: ExecutionState.crashed,
                    GovTextJobStatus.CANCELLED.value: ExecutionState.cancelled,
                    GovTextJobStatus.CANCELLING.value: ExecutionState.cancelling,  # noqa: E501
                }

                self.delete_file_from_bucket(
                    bucket=self.environ.govtext.bucket, key=key
                )
                self.set_kb_state(
                    state=State(state=state[job.status]),
                    agent_id=self.message.agent,
                    kb_id=self.message.knowledge_base,
                    rag_config_id=self.message.rag_config,
                )
                self.set_rag_config_state(
                    state=State(state=state[job.status]),
                    agent_id=self.message.agent,
                    rag_config_id=self.message.rag_config,
                )
                self.logger.info(
                    "Handled failed GovText job",
                    data={"job_id": status_message.job_id},
                )
                return True
            return False

        def handle_running(
            job: GovTextJobResponse,
            status_message: GovTextStatusMessage,
            key: str,
        ):
            """
            Strategy for handling running scenarios

            Args:
                job (GovTextJobResponse): Response model
                status_message (GovTextStatusMessage): Status Metadata
                key (str): Bucket key

            Returns:
                bool: Indicates if the running scenario was
                      activated
            """
            if response.status.is_running():
                new_state: ExecutionState = response.status.get_aibots_state()

                # check if current govtext status is the same as RAG Pipeline
                # Status JSON status
                if new_state != self.message.status:
                    # if there is a change, update kb & rag config
                    status_message_copy: RAGPipelineStatus = deepcopy(
                        self.message
                    )
                    # set new status
                    status_message_copy.status = new_state
                    # updates bucket RAGPipelineStatus
                    self.update_bucket_rag_config_file(
                        key=key,
                        updated_rag_pipeline_status=status_message_copy,
                    )
                    self.set_kb_state(
                        state=State(state=new_state),
                        agent_id=self.message.agent,
                        kb_id=self.message.knowledge_base,
                        rag_config_id=self.message.rag_config,
                    )
                    self.set_rag_config_state(
                        state=State(state=new_state),
                        agent_id=self.message.agent,
                        rag_config_id=self.message.rag_config,
                    )
                    self.logger.info(
                        "Handled executing GovText job",
                        data={"job_id": govtext_pipeline_message.job_id},
                    )
                else:
                    self.logger.info(
                        "Handled executing GovText job by doing nothing",
                        data={"job_id": govtext_pipeline_message.job_id},
                    )
            return True

        # Check that job has not been handled before
        if response.job_id in seen:
            return

        strategies: list[
            Callable[
                [GovTextJobResponse, GovTextStatusMessage, str],
                bool,
            ]
        ] = [handle_success, handle_failure, handle_running]
        govtext_pipeline_message: GovTextStatusMessage = GovTextStatusMessage(
            **self.message.results.metadata
        )
        bucket_key: str = (
            f"schedule/minute/"
            f"{str(govtext_pipeline_message.job_id)}_"
            f"{self.message.agent}_govtext.json"
        )

        # Iterate over various strategies that handle different scenarios
        #   1. Successful scenarios =>
        #       Removes S3 Pipeline Status JSON,
        #       Updates successful RAG Config status,
        #       Updates successful Knowledge Base Status
        #   2. Unsuccessful scenarios =>
        #       Removes S3 Pipeline Status JSON,
        #       Updates failed RAG Config status,
        #       Updates failed Knowledge Base Status
        #   3. Running scenarios =>
        #       check if the state is different
        #       if different, update S3 JSON,
        #       update Knowledge Base Status * RAG
        #       Config status
        for strategy in strategies:
            seen.add(govtext_pipeline_message.job_id)
            strategy_response = strategy(
                response, govtext_pipeline_message, bucket_key
            )
            if not strategy_response:
                continue

    def delete_file_from_bucket(self, bucket: str, key: str) -> None:
        """
        Deletes a specified file from a given bucket

        Args:
            bucket (str): Bucket name
            key (str): File key

        Returns:
            None

        Raises:
            AtlasRAGException: If errors occur during deletion
        """
        try:
            self.s3.delete_object(Bucket=bucket, Key=key)
        except ClientError as e:
            code: str = e.response["Error"]["Code"]
            message = e.response["Error"]["Message"]
            self.logger.error(
                f"Error occurred with details {code}.{message}",
                data=e.response,
            )
            raise AtlasRAGException(
                status_code=code,
                message=message,
            ) from e

    def set_kb_state(
        self, agent_id: str, kb_id: str, rag_config_id: str, state: State
    ) -> None:
        """
        Updates Knowledge Base embeddings state to specified value

        Attributes:
            agent_id (str): id of the agent
            kb_id (str): id of knowledge base to be updated
            rag_config_id (str): id of rag config
            state (State): state to update knowledge base to

        Raises:
            AtlasRAGException: if there is an error with
                                updating knowledge base
        """
        update_kb: Response = httpx.put(
            url=f"{self.environ.aibots.url}"
            f"{API_VERSION}/agents/{agent_id}/knowledge/bases/"
            f"{kb_id}/statuses",
            headers={"X-ATLAS-Key": self.environ.aibots.auth},
            params={"ragConfig": rag_config_id},
            json=state.model_dump(mode="json"),
            verify=False,
        )
        if not update_kb.is_success:
            raise AtlasRAGException(
                status_code=update_kb.status_code,
                message=update_kb.json()["message"],  # noqa: E501
            )
        self.logger.info(
            "Successfully updated knowledge base status",
            data={
                **state.model_dump(include={"state"}, mode="json"),
                "knowledge_base_id": kb_id,
            },
        )

    def set_rag_config_state(
        self, agent_id: str, rag_config_id: str, state: State
    ):
        """
        Updates RAG config state to specified value

        Attributes:
            agent_id (str): id of the agent
            rag_config_id (str): id of rag config
            state (State): state to update rag config to

        Raises:
            AtlasRAGException: if there is an error with updating RAGConfig
        """

        response: Response = httpx.put(
            url=f"{self.environ.aibots.url}"
            f"{API_VERSION}/agents/{agent_id}/rags/{rag_config_id}/statuses",
            headers={"X-ATLAS-Key": self.environ.aibots.auth},
            json=state.model_dump(mode="json"),
            verify=False,
        )
        if not response.is_success:
            raise AtlasRAGException(
                status_code=response.status_code,
                message=response.json()["message"],
            )
        self.logger.info(
            "Successfully updated rag config status",
            data={
                **state.model_dump(include={"state"}, mode="json"),
                "rag_config_id": rag_config_id,
            },
        )

    def update_bucket_rag_config_file(
        self, key: str, updated_rag_pipeline_status: RAGPipelineStatus
    ) -> None:
        """
        Updates the status of the RAG Config JSON file
        In S3 bucket
        Returns:
            None
        Raises:
            AtlasRAGException: if S3 bucket file upload fails
        """
        try:
            # overwrites current file
            self.s3.upload_fileobj(
                io.BytesIO(
                    json.dumps(
                        {
                            "sqs": self.environ.govtext.sqs,
                            "payload": updated_rag_pipeline_status.model_dump(
                                mode="json"
                            ),
                        }
                    ).encode("utf-8")
                ),
                self.environ.govtext.bucket,
                key,
            )
        except ClientError as e:
            code: str = e.response["Error"]["Code"]
            message = e.response["Error"]["Message"]
            self.logger.error(f"Error occurred with details {code}.{message}")
            raise AtlasRAGException(
                status_code=code,
                message=message,
            ) from e


async def init_lambda() -> None:
    """
    Initialises all the Atlas services used within the
    lambda handler

    Returns:
        None

    Raises:
        RuntimeError: If GovText Parameter does not exist
        RuntimeError: If AIbots Parameter does not exist
    """
    global logging_service
    global environ
    global s3
    global engine

    if logging_service is None:
        logging_service = StructLogService(debug=False)
        logging_service.atlas_init()

    logger: Any = logging_service.get_structlog_logger("status.govtext.init")

    if environ is None:
        environ = GovTextStatusEnviron()

        # Retrieving essential parameters from ssm
        ssm: SSMService = SSMService(**environ.aws_config)
        with ssm:
            if environ.govtext.param:
                govtext_params: dict = ssm.atlas_get_dict(
                    environ.govtext.param, **{"WithDecryption": True}
                )
                environ.govtext.auth = govtext_params["key"]
                environ.govtext.url = AnyUrl(govtext_params["endpoint"])
            else:
                raise RuntimeError("Govtext Parameter Not Found")
            if environ.aibots.auth and environ.aibots:
                logger.info(
                    "AIBots access variables passed by "
                    "environment variables"
                )
            elif environ.aibots.param:
                aibots_params: dict = ssm.atlas_get_dict(
                    environ.aibots.param, **{"WithDecryption": True}
                )
                environ.aibots.auth = aibots_params["key"]
                environ.aibots.url = AnyUrl(aibots_params["endpoint"])
            else:
                raise RuntimeError("AIBots Parameter Not Found")

    logger.info("Loaded environment variables", data=environ.model_dump())

    if s3 is None:
        s3 = S3Service(**environ.aws_config)
        s3.atlas_init(logger)

    logger.info("Initialised S3 service")

    if engine is None:
        engine = GovTextEngine(
            s3_bucket=str(environ.govtext.bucket),
            s3_service=s3,
            endpoint=str(environ.govtext.url),
            headers={
                "accept": "application/json",
                "X-API-KEY": str(environ.govtext.auth),
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) "
                "Gecko/20100101 Firefox/81.0",
            },
            timeout=httpx.Timeout(
                connect=15.0, read=180.0, write=180.0, pool=15.0
            ),
            limits=httpx.Limits(
                max_keepalive_connections=100, max_connections=500
            ),
            transport=httpx.AsyncHTTPTransport(retries=3),
        )
        await engine.atlas_ainit(logger)

    logger.info("Initialised GovText Engine")


async def reset_lambda() -> None:
    """
    Helper function to reset lambda variables

    Returns:
        None
    """
    global environ
    global engine
    global logging_service
    global s3

    if engine:
        # TODO: Fix HttpxService param handling
        # await engine.atlas_aclose()
        engine = None
    if s3:
        s3.atlas_close()
        s3 = None
    if logging_service:
        logging_service.atlas_close()
        logging_service = None
    if environ:
        environ = None


API_VERSION: str = "latest"

environ: GovTextStatusEnviron | None = None
engine: GovTextEngine | None = None
logging_service: StructLogService | None = None
s3: S3Service | None = None


@validate_call
def lambda_handler(event: GovTextPipelineStatus, context: Any) -> None:
    """
    Args:
        event (GovTextPipelineStatus): Event message body containing
                                       list of records
        context (Any): AWS Lambda context

    Returns:
        Dict[str,Any]
    """
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    seen: set[str] = set()

    try:
        loop.run_until_complete(init_lambda())
    except RuntimeError as e:
        print(e)  # noqa: T201
        return

    # iterates through each sqs record, parses the job_id
    # out to check status against Govtext pipeline API
    logger: Any = logging_service.get_structlog_logger(
        "status.govtext.execute"
    )
    logger.info("Received SQS records", data=event.model_dump(mode="json"))
    for _, record in enumerate(event.messages):
        # RAGPipelineStatus will be passed as a string
        # into the SQSMessageRecord

        logger.info(
            "Processing SQS record", data=record.model_dump(mode="json")
        )
        executor = GovTextStatusExecutor(
            message=record,
            environ=environ,
            engine=engine,
            s3=s3,
            logger=logger,
        )

        execute_task = loop.create_task(executor())
        try:
            response: RAGPipelineStatus = loop.run_until_complete(execute_task)
            executor.next(
                response=GovTextJobResponse(**response.results.metadata),
                seen=seen,
            )
        except AtlasRAGException as e:
            logger.error(
                f"Error {e.__class__.__name__}.{e.message} occurred while "
                f"processing record",
                data=record.model_dump(mode="json"),
            )
        except Exception as e:
            logger.error(
                f"Error {e.__class__.__name__}.{str(e)} occurred while "
                f"processing record",
                data=record.model_dump(mode="json"),
            )

    return
