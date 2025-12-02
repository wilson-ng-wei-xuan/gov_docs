import json
import os
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict

import boto3
import pytest

from aibots.models.rags.base import RAGPipelineEnviron

from aibots.models.rags import RAGPipelineMessage, SourceResult, ParseResult

from aibots.models import RAGConfig
from ..lambda_function import SemanticRAGChunker


class TestSemanticChunker:
    @pytest.mark.parametrize(
        argnames=["parsed", "source_result_key"],
        argvalues=[
            pytest.param(
                "pptx_parse_result", "tests/exampledoc.pptx",
                id="test_pptx_parse"
            ), pytest.param(
                "pdf_parse_result", "tests/exampledoc.pdf",
                id="test_pdf_parse"
            ), pytest.param(
                "docx_parse_result", "tests/exampledoc.docx",
                id="test_docx_parse"
            ), pytest.param(
                "html_parse_result", "tests/exampledoc.html",
                id="test_html_parse"
            ), pytest.param(
                "xlsx_parse_result", "tests/exampleexcel.xlsx",
                id="test_xlsx_parse"
            ), pytest.param(
                "txt_parse_result", "tests/exampledoc.txt",
                id="test_txt_parse"
            ), pytest.param(
                "csv_parse_result", "tests/examplecsv.csv",
                id="test_csv_parse"
            ),
        ]
    )
    def test_semantic_chunker_next_success(self, request, parsed, source_result_key) -> None:
        """tests lambda function output"""
        mock_aws_infra: boto3.Session = request.getfixturevalue("mock_aws_infra")
        dataframe_chunk_config: Dict[str, Any] = request.getfixturevalue("semantic_chunk_config")
        message: RAGPipelineMessage = deepcopy(request.getfixturevalue("rag_pipeline_message"))
        source_result: SourceResult = SourceResult(key=source_result_key)
        parse_result: ParseResult = request.getfixturevalue(parsed)
        parse_config: Dict[str, Any] = request.getfixturevalue("parsed_config")

        message.pipeline = RAGConfig(config={**dataframe_chunk_config, **parse_config})
        environ: RAGPipelineEnviron = RAGPipelineEnviron()
        sqs = mock_aws_infra.client("sqs", region_name="ap-southeast-1")

        # add in source and parse results
        message.results += [source_result, parse_result]

        # instantiate dataframe chunker
        chunker = SemanticRAGChunker(message, sqs, environ)

        executor = chunker()
        assert executor.status == "completed"

        chunker.next()

        store_queue = sqs.receive_message(QueueUrl=str(environ.project_rag_store.url))
        messages = store_queue["Messages"]

        assert isinstance(messages, list)
        assert len(messages) == 1

        for message in messages:
            body = json.loads(message["Body"])
            RAGPipelineMessage.model_validate(body)
            updated_pipeline_message = RAGPipelineMessage(**body)
            assert len(updated_pipeline_message.results) == 3
