from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from aibots.aws_lambda.models.rag.pipeline import SQSRAGPipelineMessage


class RAGParser:
    """
    class for wrapping lambda parsing handling
    """

    def __init__(
        self,
        event: Dict[str, Any],
        context: Any,
        parser: Callable[[str, str, str, Optional[str]], List[Dict[str, Any]]],
    ) -> None:
        # TODO: create a base model for event object
        # TODO: create a base model for parse lambda record
        self.event = event
        self.context = context
        self.records: List[Dict[str, Any]] = event["Records"]
        # list of successful parses
        self.parsed: List[Dict[str, Any]] = []
        # list of failed parses
        self.failed: List[Dict[str, Any]] = []
        self.logger = logging
        self.logger.getLogger().setLevel(logging.INFO)
        self.parser: Callable[
            [str, str, str, Optional[str]], Dict[str, Any]
        ] = parser

    def run(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Runs parser for every record
        """
        # for every record, parse the record, and then result of self.parsed
        # will be sent in bulk to the next stage of the pipeline
        for _, record in enumerate(self.records):
            sqs_body = SQSRAGPipelineMessage(**json.loads(record["body"]))
            try:
                # runs parser
                parse_args = {
                    k: v
                    for k, v in sqs_body.configs.parse.model_dump().items()
                    if k != "type"
                }
                response = self.parser(**parse_args)
                # adds successful parse
                # TODO: standardise parser response to List[Dict[str,Any]]
                sqs_body.set_parse_results(results=response)
                self.parsed.append(
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
        success = self.parsed
        failed = self.failed
        # returns success, failed parsing
        return success, failed
