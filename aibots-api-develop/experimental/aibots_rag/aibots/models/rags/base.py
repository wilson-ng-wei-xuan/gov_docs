from __future__ import annotations

from abc import abstractmethod
from typing import Any

from atlas.environ import BucketEnvVars, ParamEnvVars, ServiceEnvVars
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from .api import RAGPipelineStatus
from .internal import RAGPipelineMessage

__doc__ = """
RAGBase class for Command design pattern in RAG.
Used to execute parser, chunker, embedder & storer
(Note: embedder & storer to be combined)
"""


class ParseStage(BaseModel):
    docx: ServiceEnvVars | None = None
    pptx: ServiceEnvVars | None = None
    xlsx: ServiceEnvVars | None = None
    txt: ServiceEnvVars | None = None
    html: ServiceEnvVars | None = None
    pdf: ServiceEnvVars | None = None
    csv: ServiceEnvVars | None = None


class ChunkStage(BaseModel):
    fixed: ServiceEnvVars | None = None
    dataframe: ServiceEnvVars | None = None
    semantic: ServiceEnvVars | None = None


class RAGPipelineEnviron(BaseSettings):
    cloudfront_bucket: BucketEnvVars = BucketEnvVars(
        bucket="s3-sitezingress-aibots-471112510129-cloudfront"
    )
    bucket: BucketEnvVars = BucketEnvVars(
        bucket="s3-sitezapp-aibots-471112510129-project"
    )
    project_rag_status: ServiceEnvVars = ServiceEnvVars(
        url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/STATUS"
    )
    project_rag_parse: ParseStage = ParseStage(
        docx=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/DOCX"
        ),
        pptx=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/PPTX"
        ),
        xlsx=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/XLSX"
        ),
        txt=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/TXT"
        ),
        html=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/HTML"
        ),
        pdf=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/PDF"
        ),
        csv=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/CSV"
        ),
    )
    project_rag_chunk: ChunkStage = ChunkStage(
        fixed=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/FIXED"
        ),
        dataframe=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/DATAFRAME"
        ),
        semantic=ServiceEnvVars(
            url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/SEMANTIC"
        ),
    )
    project_rag_store: ServiceEnvVars = ServiceEnvVars(
        url="https://sqs.ap-southeast-1.amazonaws.com/123456789012/STORE"
    )
    project_rag_aoss: ParamEnvVars = ParamEnvVars(
        param="param-sitezapp-aibots-rag-aoss-picker"
    )


class RAGPipelineStatusExecutor:
    def __init__(
            self,
            message: RAGPipelineStatus,
            environ: RAGPipelineEnviron,
            **kwargs: Any,
    ) -> None:
        self.message: RAGPipelineStatus = message
        self.environ: RAGPipelineEnviron = environ


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
