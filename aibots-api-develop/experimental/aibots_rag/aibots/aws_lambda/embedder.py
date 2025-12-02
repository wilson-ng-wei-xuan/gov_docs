from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Tuple

from aibots.aws_lambda.models.rag import (
    ChunkDocument,
    SQSRAGPipelineMessage,
    StoreDocument,
)


class RAGEmbedder:
    """
    class for wrapping rag embedding
    """

    def __init__(
        self,
        event: Dict[str, Any],
        context: Any,
        embedder: Callable[[List[str]], List[List[float]]],
    ) -> None:
        self.event = event
        self.context = context
        self.records = event["Records"]
        self.logger = logging
        self.embedder = embedder
        self.embedded = []
        self.failed = []

    def run(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        for _, record in enumerate(self.records):
            sqs_body = SQSRAGPipelineMessage(**json.loads(record["body"]))
            try:
                # gets results from parse
                chunked_docs: List[ChunkDocument] = list(
                    sqs_body.results.chunk
                )

                # remove chunking type, gets dictionary of other arguments
                texts_to_embed = [doc.text for doc in chunked_docs]
                # apply arguments to embedder
                embeddings = self.embedder(texts_to_embed)

                embedded_docs: List[Dict[str, Any]] = [
                    StoreDocument(
                        text=chunked_docs[i].text,
                        page_number=chunked_docs[i].page_number,
                        last_update_date=chunked_docs[i].last_update_date,
                        embedding=embed,
                        chunk=chunked_docs[i].chunk,
                        source=f"{sqs_body.configs.parse.bot}/{sqs_body.configs.parse.file_key}",
                    ).model_dump()
                    for i, embed in enumerate(embeddings)
                ]
                sqs_body.set_embed_results(results=embedded_docs)
                self.embedded.append(
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
        success = self.embedded
        failed = self.failed
        return success, failed
