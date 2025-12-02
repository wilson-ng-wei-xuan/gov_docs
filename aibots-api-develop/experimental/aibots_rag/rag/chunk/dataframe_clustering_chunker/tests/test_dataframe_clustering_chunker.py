import json
import os
from copy import deepcopy
from typing import Dict, Any

import boto3
import pytest
from aibots.models import RAGConfig
from aibots.models.rags import RAGPipelineMessage, RAGPipelineEnviron, SourceResult, ParseResult, ChunkResult

from aibots.models.rags import Page
from ..lambda_function import DataframeChunker


class TestDataframeChunkerFunc:
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
    def test_dataframe_chunker_results(self, request, parsed, source_result_key) -> None:
        """tests lambda function output"""
        semantic_chunk_config: Dict[str, Any] = request.getfixturevalue("dataframe_chunk_config")
        message: RAGPipelineMessage = deepcopy(request.getfixturevalue("rag_pipeline_message"))
        source_result: SourceResult = SourceResult(key=source_result_key)
        parse_result: ParseResult = request.getfixturevalue(parsed)
        parse_config: Dict[str, Any] = request.getfixturevalue("parsed_config")

        message: RAGPipelineMessage = deepcopy(request.getfixturevalue("rag_pipeline_message"))
        message.pipeline = RAGConfig(config={**semantic_chunk_config, **parse_config})
        message.results += [source_result, parse_result]
        environ: RAGPipelineEnviron = RAGPipelineEnviron()
        sqs = boto3.client("sqs", region_name="ap-southeast-1")

        chunker = DataframeChunker(message, sqs, environ)
        executor = chunker()
        results = json.loads(executor.results)
        assert executor.status == "completed"
        for result in results:
            Page.model_validate(result)
