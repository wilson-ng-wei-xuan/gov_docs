from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Literal, Tuple, Union

from aibots.aws_lambda.models.rag import ParsedPage, SQSRAGPipelineMessage


class RAGChunker:
    """
    class for wrapping lambda chunking handling
    """

    FixedChunkerFunc = Callable[
        [List[ParsedPage], int, str, int], List[Dict[str, Any]]
    ]
    DataframeChunkerFunc = Callable[
        [List[ParsedPage], int, int, Union[Literal["False"], Literal["True"]]],
        List[Dict[str, Any]],
    ]
    SemanticChunkerFunc = Callable[
        [List[ParsedPage], int], List[Dict[str, Any]]
    ]

    def __init__(
        self,
        event: Dict[str, Any],
        context: Any,
        chunker: Union[
            FixedChunkerFunc, DataframeChunkerFunc, SemanticChunkerFunc
        ],
    ) -> None:
        self.event = event
        self.context = context
        self.records = event["Records"]
        self.logger = logging
        self.chunker = chunker
        self.chunked = []
        self.failed = []

    def run(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        runs chunking pipeline
        """
        for _, record in enumerate(self.records):
            sqs_body = SQSRAGPipelineMessage(**json.loads(record["body"]))
            try:
                # gets results from parse
                parsed_docs: List[ParsedPage] = [
                    page.model_dump() for page in sqs_body.results.parse
                ]
                # remove chunking type, gets dictionary of other arguments
                chunk_args = {
                    k: v
                    for k, v in sqs_body.configs.chunk.model_dump().items()
                    if k != "type"
                }
                # apply arguments to chunker
                chunks = self.chunker(**{"docs": parsed_docs, **chunk_args})
                sqs_body.set_chunk_results(results=chunks)
                self.chunked.append(
                    {**record, "body": json.dumps(sqs_body.model_dump())}
                )
            except Exception as e:
                # logs error
                self.logger.error(
                    "{} >> error processing sqs message >> {}".format(
                        self.context.function_name, json.dumps(str(e))
                    )
                )
                # takes the record of the failed chunk
                self.failed.append(record)
        success = self.chunked
        failed = self.failed
        return success, failed
