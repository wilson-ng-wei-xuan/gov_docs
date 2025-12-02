import logging
from typing import Any, Callable, Dict, List, Union
from aibots.aws_lambda.models.rag import (
    ParseConfig,
    FixedChunker,
    DataframeChunker,
    SemanticChunker,
    StoreConfig,
)


__doc__ = """
RAGBase class for Command design pattern in RAG.
Used to execute parser, chunker, embedder & storer 
(Note: embedder & storer to be combined)
"""


class RAGBase:
    """
    Class for running parser, chunker, embedder & storer
    Attributes:
        func (Callable[[FuncInputConfig], Dict[str,Any]]): function to execute
    """

    FuncInputConfig = Union[
        ParseConfig,
        FixedChunker,
        DataframeChunker,
        SemanticChunker,
        StoreConfig,
    ]

    def __init__(
        self, func: Callable[[FuncInputConfig], List[Dict[str, Any]]]
    ) -> None:
        self.func = func
        self.logger = logging
        self.logger.getLogger().setLevel(logging.INFO)

    def run(self, message: FuncInputConfig) -> List[Dict[str, Any]]:
        """
        runs function defined
        Args:
            message (FuncInputConfig): SQS RAG configs
        """
        # removes type to be passed others as args
        function_args = {
            k: v for k, v in message.model_dump().items() if k != "type"
        }
        return self.func(**function_args)

    def log(self, log: str) -> None:
        """
        logs error message
        log (str): message to be logged
        """
        self.logger.error(
            f"{self.func.__name__} >> error processing sqs message >> {log}"
        )
