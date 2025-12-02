import json
import os
import subprocess
from time import sleep
from copy import deepcopy
import shlex
from typing import Any, Dict

import boto3
from aibots.models.rags import RAGPipelineStatus
from aibots.models.rags.internal import (
    ParseResult,
    RAGPipelineMessage,
    SourceResult,
    ChunkResult)

from aibots.models import RAGConfig

from aibots.models.rags.base import RAGPipelineEnviron
import pytest

from ..lambda_function import OpenSearchStorer, FileIndexer, BedRockEmbedder

from boto3 import client


class TestOpenSearchStorer:
    @pytest.mark.parametrize(
        # TODO: add more test parameters
        argnames=["source_config", "parse_config", "chunk_config", "source_result", "parse_result", "chunk_result"],
        argvalues=[
            pytest.param(
                "csv_source_config",
                "csv_parse_config",
                "fixed_chunk_config",
                "csv_source_result",
                "csv_parse_result",
                "csv_chunk_result",
                id="source_csv_fixed_opensearch"
            )
        ])
    def test_opensearch_storer_success_call(self,
                                            request,
                                            source_config,
                                            parse_config,
                                            chunk_config,
                                            source_result,
                                            parse_result,
                                            chunk_result) -> None:
        os.chdir(request.fspath.dirname)

        subprocess.run(
            shlex.split("docker compose up -d"),
            env={**os.environ,
                 "OPENSEARCH_INITIAL_ADMIN_PASSWORD": os.environ["OPENSEARCH_INITIAL_ADMIN_PASSWORD"]
                 }
        )
        # waits for opensearch to complete booting up
        sleep(10)
        source_config: Dict[str, Any] = request.getfixturevalue(source_config)
        parse_config: Dict[str, Any] = request.getfixturevalue(parse_config)
        chunk_config: Dict[str, Any] = request.getfixturevalue(chunk_config)
        source_result: SourceResult = request.getfixturevalue(source_result)
        parse_result: ParseResult = request.getfixturevalue(parse_result)
        chunk_result: ChunkResult = request.getfixturevalue(chunk_result)
        environ: RAGPipelineEnviron = RAGPipelineEnviron()
        config: RAGConfig = RAGConfig(config={**source_config, **parse_config, **chunk_config})
        message: RAGPipelineMessage = deepcopy(request.getfixturevalue("rag_pipeline_message"))
        message.results += [source_result, parse_result, chunk_result]
        message.pipeline = config
        sqs = boto3.client(service_name="sqs", region_name="ap-southeast-1")
        executor: OpenSearchStorer = OpenSearchStorer(message, sqs, environ)
        result: RAGPipelineStatus = executor()
        assert result.status == "completed"
        assert json.loads(result.results)["uploaded"] is True
        subprocess.run(
            shlex.split("docker compose down -v"),
            env={
                **os.environ}
        )
        os.chdir(request.config.invocation_params.dir)
