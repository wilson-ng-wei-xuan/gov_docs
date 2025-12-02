from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, Union

from pydantic import AliasChoices, BaseModel, Field, validate_call

from aibots.models.rags.internal import RAGPipelineMessage

__all__ = (
    "SQSMessageRecord",
    "SQSMessage",
)

SM = TypeVar("SM", bound=Union[str, BaseModel])


class SQSMessageRecord(BaseModel, Generic[SM]):
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
    body: SM
    attributes: Dict[str, Any]
    message_attributes: Dict[str, Any] = Field(alias="messageAttributes")
    md5_of_message_attributes: Optional[str] = Field(
        None, alias="md5OfMessageAttributes"
    )
    md5_of_body: Optional[str] = Field(None, alias="md5OfBody")
    event_source: str = Field(alias="eventSource")
    event_source_arn: str = Field(alias="eventSourceARN")
    aws_region: str = Field(alias="awsRegion")


class SQSMessage(BaseModel):
    """
    model for sqs message
    attributes:
        records (List[SQSMessageRecord]): list of sqs records collected
    """

    records: List[SQSMessageRecord[RAGPipelineMessage]] = Field(
        [], validation_alias=AliasChoices("Records")
    )


class SQSMessageHandler:
    @validate_call
    def validate_inner(
        self, event: SQSMessageRecord, context: Any
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        validates the typings of incoming sqs message
        args:
            event (SQSMessageRecord): incoming event
            context (Any): incoming context
        """
        # TODO: add context valdidation
        return SQSMessage(**event).model_dump(), context
