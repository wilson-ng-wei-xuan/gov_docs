from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Tuple

from aibots.aws_lambda.models.rag.pipeline import (
    SQSRAGPipelineMessage,
)


class RAGStorer:
    """
    class for wrapping lambda storer
    """

    def __init__(
        self,
        event: Dict[str, Any],
        context: Any,
        storer: Callable[[List[Dict[str, Any]]], Dict[str, Any]],
    ) -> None:
        self.event = event
        self.context = context
        self.records: List[Dict[str, Any]] = event["Records"]
        # list of successful store
        self.stored: List[Dict[str, Any]] = []
        # list of failed store
        self.failed: List[Dict[str, Any]] = []
        self.logger = logging
        self.logger.getLogger().setLevel(logging.INFO)
        self.storer: Callable[[List[Dict[str, Any]]], Dict[str, Any]] = storer

    def run(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        for _, record in enumerate(self.records):
            sqs_body = SQSRAGPipelineMessage(**json.loads(record["body"]))
            try:
                # documents = [
                #     res.model_dump() for res in sqs_body.results.embed
                # ]
                self.storer(sqs_body)
                # TODO: add proper arguments using pydantic, and enums
                sqs_body.add_store_results(result={"status": "success"})
                self.stored.append(
                    {**record, "body": json.dumps(sqs_body.model_dump())}
                )
            except Exception as e:
                # logs error
                self.logger.error(
                    "{} >> error processing sqs message >> {}".format(
                        self.context.function_name, json.dumps(str(e))
                    )
                )
                # takes the record of the failed parse
                self.failed.append(record)
        success = self.stored
        failed = self.failed
        return success, failed
