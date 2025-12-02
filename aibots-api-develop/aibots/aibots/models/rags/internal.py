from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from enum import Enum
from typing import (
    Annotated,
    Any,
    Dict,
    Generic,
    Optional,
    TypeVar,
    get_args,
)

from atlas.schemas import AtlasID, ExecutionState, Uuid
from atlas.utils import generate_curr_datetime, generate_uuid
from pydantic import BaseModel, ConfigDict, Field

from aibots.models import KnowledgeBase, RAGConfig

__all__ = (
    "RAGPipelineStages",
    "Page",
    "BaseResult",
    "StatusResult",
    "SourceResult",
    "ParseResult",
    "ChunkResult",
    "RAGPipelineMessage",
    "RAGPipelineStatus",
    "SQSMessageRecord",
    "SQSMessage",
    "RAGPipelineExecutor",
)


class RAGPipelineStages(str, Enum):
    """
    RAG Pipeline Stages

    source (str): Importing data from various sources
    extraction (str): Extracting text and info from the data sources
    chunking (str): Generating chunks from the extracted text
    embeddings (str): Generating embeddings and
                    storing embeddings in storage layer
    external (str): External pipelines integrations
    """

    source = "source"
    extraction = "extraction"
    chunking = "chunking"
    embeddings = "embeddings"
    external = "external"


class BaseResult(BaseModel):
    """
    Stores parsed data for each pipeline stage

    Attributes:
        metadata (dict[str, Any]): Metadata to be added, defaults
                                   to an empty dictionary
    """

    metadata: dict[str, Any] = {}


class StatusResult(BaseResult):
    """
    Generic container for storing pipeline specific status result

    Attributes:
        metadata (dict[str, Any]): Metadata to be added, defaults
                                   to an empty dictionary
    """

    model_config: ConfigDict = ConfigDict(extra="allow")


class SourceResult(BaseResult):
    """
    Result output for the Source pipeline stage

    Attributes:
        key (str): S3 bucket file key
    """

    key: str


class Page(BaseModel):
    """
    Page output for parse pipeline stage

    Attributes:
        chunk (int): ID of the Chunk
        text (str): Text string
        page_number (int): Page number details, defaults
                           to 0
        section (str | None): Section details, defaults
                              to None
    """

    chunk: int = 0
    text: str
    page_number: int = 0
    section: str | None = None


class ParseResult(BaseResult):
    """
    Result output for the Parse pipeline stage

    Attributes:
        pages (list[Page]): List of pages, defaults
                            to an empty list
    """

    pages: list[Page] = []


class ChunkResult(BaseResult):
    """
    Result output for the Chunk pipeline stage

    Attributes:
        chunks (list[Page]): List of chunks, defaults
                             to an empty list
    """

    chunks: list[Page] = []


class RAGPipelineMessage(AtlasID):
    """
    Model for RAG pipeline message

    Attributes:
        id (Uuid): ID of the pipeline run
        agent (Uuid): ID of the Agent
        knowledge_base (Uuid): ID of Knowledge Base
        knowledge_bases (list[KnowledgeBase]): List of Knowledge Bases,
                                               defaults to an empty list
        pipeline (AgentRAGConfig): RAG pipeline configuration details
        results (
            list[
                SourceResult |
                ParseResult |
                ChunkResult |
                BaseResult
            ]
        ): Results for each node of the pipeline, defaults to an empty list
        supported_pipelines (list[dict[str, Any]]):
            List of supported pipelines, defaults to an empty list
    """

    # TODO: compress setters to singular method, use discriminator to route
    # TODO: rename document_id, remove last updated, execution status TBC
    agent: Uuid
    knowledge_base: Uuid
    knowledge_bases: list[KnowledgeBase] = []
    pipeline: RAGConfig
    results: list[
        SourceResult | ParseResult | ChunkResult | StatusResult | BaseResult
    ] = []
    supported_pipelines: list[dict[str, Any]] = []


class RAGPipelineStatus(BaseModel):
    """
    Generic representation of the state details of a stage
    in the RAG Pipeline

    Attributes:
        id (Uuid): ID of the pipeline job
        rag_config (Uuid): RAG Config ID
        agent (Uuid): ID of the Agent
        knowledge_base (Uuid): ID of the Knowledge Base
        type (RAGPipelineStages): Type of RAG pipeline stage
        status (ExecutionState): RAG Pipeline execution status
        error (dict[str, Any] | None): Error details if any,
                                       defaults to None
        results (StatusResult | None): Output from the stage
        timestamp (datetime): Creation timestamp, defaults to
                              the current datetime
    """

    model_config: ConfigDict = ConfigDict(
        extra="allow",
        use_enum_values=True,
    )

    id: Uuid = Field(default_factory=generate_uuid)
    rag_config: Uuid
    agent: Uuid
    knowledge_base: Uuid
    type: RAGPipelineStages
    status: ExecutionState
    error: dict[str, Any] | None = None
    results: StatusResult | None
    timestamp: Annotated[
        datetime, Field(default_factory=generate_curr_datetime)
    ]


# TODO: Shift this into Atlas
class SQSMessageRecord(BaseModel):
    """
    Generic model for SQS Record

    Attributes:
       message_id (str): id of message
       receipt_handler (str): aws sqs message receipt handler
       body (SM): Stringified message body of SQSRAGPipelineMessage
       attributes (Dict[str,Any]): attributes of record
       message_attributes (Dict[str,Any]): message attributes
       md5_of_message_attributes (str): md5 hash of message attributes
       md5_of_body (str): mdf hash of body
       event_source (str): source of sqs event
       event_source_arn (str): amazon reference name of event osurce
       aws_region (str): aws region source
    """

    message_id: str = Field(alias="messageId")
    receipt_handler: str = Field(alias="receiptHandle")
    body: str
    attributes: Dict[str, Any]
    message_attributes: Dict[str, Any] = Field(alias="messageAttributes")
    md5_of_message_attributes: Optional[str] = Field(
        None, alias="md5OfMessageAttributes"
    )
    md5_of_body: Optional[str] = Field(None, alias="md5OfBody")
    event_source: str = Field(alias="eventSource")
    event_source_arn: str = Field(alias="eventSourceARN")
    aws_region: str = Field(alias="awsRegion")


M = TypeVar("M", bound=BaseModel)


# TODO: Shift this into Atlas
# TODO: The correct way to do this is to push the Generics into the
#   SQSMessageRecord class and use Pydantic to serialise it there
class SQSMessage(Generic[M], BaseModel):
    """
    Pipeline RAG message over SQS

    Attributes:
        records (List[SQSMessageRecord]): List of SQS records
                                          collected
    """

    records: list[SQSMessageRecord] = Field([], alias="Records")

    @property
    def messages(self) -> list[M]:
        """
        Convenience function for retrieving a list of serialised
        messages

        Returns:
            list[M]): List of messages
        """
        message_type: type[BaseModel] = get_args(type(self).__orig_bases__[0])[
            0
        ]

        return [message_type.model_validate_json(r.body) for r in self.records]


class RAGPipelineExecutor:
    """
    Class for abstracting execution logic a RAG pipeline stage

    Attributes:
        type (str): Pipeline type
        stage (str): Stage of the pipeline
        message (RAGPipelineMessage): RAG Pipeline message
    """

    type: str = ""
    stage: str = ""

    def __init__(
        self,
        message: RAGPipelineMessage,
        sqs: Any,
        environ: Any,
    ) -> None:
        self.message: RAGPipelineMessage = message
        self.sqs: Any = sqs
        self.environ: Any = environ

    @property
    def previous_result(self) -> Any:
        """
        Convenience method for retrieving the previous result
        from the RAGPipelineMessage

        Returns:
            Any
        """
        return self.message.results[-1]

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> RAGPipelineStatus:
        """
        Executable that handle the parsing of a specified record

        Args:
            *args (Any): Additional arguments per record
            **kwargs (Any): Additional keyword arguments per record

        Returns:
           RAGPipelineStatus: Status of the pipeline execution
        """

    def send_status(self, status: RAGPipelineStatus) -> None:
        """
        Convenience method to send a RAGPipelineStatus message

        Args:
            status (RAGPipelineStatus): RAGPipelineStatus message

        Returns:
            None
        """
        self.sqs.send_message(
            QueueUrl=str(self.environ.project_rag_status.url),
            MessageBody=status.model_dump_json(),
        )

    @abstractmethod
    def next(self, *args, **kwargs) -> Any:
        """
        Abstract method that forwards the RAGPipelineMessage to the
        next method in the RAGPipeline

        Returns:
            Any
        """
