import json
import boto3
import pytest
from boto3 import client
from typing import Dict, Any, List

from aibots.models.rags.base import RAGPipelineEnviron

from aibots.models.rags.internal import RAGPipelineMessage

from aibots.models import RAGConfig

from aibots.models.rags.internal import SourceResult

from aibots.models.knowledge_bases import KnowledgeBase

from aibots.models.rags import ParseResult
from ..lambda_function import DocxParser


class TestDocxParser:

    def test_docx_parser_result_success(self, request) -> None:
        """tests"""
        parse_config: Dict[str, Any] = request.getfixturevalue("docx_parse_config")
        mock_aws_infra: boto3.Session = request.getfixturevalue("mock_aws_infra")
        docx_knowledge_base: KnowledgeBase = request.getfixturevalue("docx_knowledge_base")
        message: RAGPipelineMessage = request.getfixturevalue("rag_pipeline_message")
        source_result: SourceResult = request.getfixturevalue("source_result")
        bucket_configs: tuple = request.getfixturevalue("bucket_configs")
        message.pipeline = RAGConfig(config={**parse_config})

        message.knowledge_bases.append(docx_knowledge_base)

        message.results.append(source_result)

        environ: RAGPipelineEnviron = RAGPipelineEnviron()

        sqs = mock_aws_infra.client("sqs", region_name="ap-southeast-1")

        private_bucket_name, cloudfront_bucket_name, _ = bucket_configs

        environ.bucket.bucket, environ.cloudfront_bucket.bucket = private_bucket_name, cloudfront_bucket_name

        parser = DocxParser(message, sqs, environ)

        executor = parser()
        print(executor)
        assert executor.status == "completed"

        results = json.loads(executor.results)
        assert isinstance(results, list)
        assert all(ParseResult.model_validate(result) for result in results)

    @pytest.mark.parametrize(
        argnames=["chunker"],
        argvalues=[
            pytest.param(
                "fixed_chunk_config",
                id="test_fixed_chunk"
            ),
            pytest.param(
                "dataframe_chunk_config",
                id="test_dataframe_chunk"
            ),
            pytest.param(
                "semantic_chunk_config",
                id="test_semantic_chunk"
            ),
        ]
    )
    def test_docx_parser_next_success(self, request, chunker) -> None:
        """test next() function & received queue message"""
        chunk_config: Dict[str, Any] = request.getfixturevalue(chunker)
        parse_config: Dict[str, Any] = request.getfixturevalue("docx_parse_config")
        mock_aws_infra: boto3.Session = request.getfixturevalue("mock_aws_infra")
        docx_knowledge_base: KnowledgeBase = request.getfixturevalue("docx_knowledge_base")
        message: RAGPipelineMessage = request.getfixturevalue("rag_pipeline_message")
        source_result: SourceResult = request.getfixturevalue("source_result")
        bucket_configs: tuple = request.getfixturevalue("bucket_configs")

        message.pipeline = RAGConfig(config={**chunk_config, **parse_config})

        message.knowledge_bases.append(docx_knowledge_base)

        chunk_type = message.pipeline.config["chunk"]["type"]

        message.results.append(source_result)

        environ: RAGPipelineEnviron = RAGPipelineEnviron()

        sqs = mock_aws_infra.client("sqs", region_name="ap-southeast-1")

        private_bucket_name, cloudfront_bucket_name, _ = bucket_configs

        environ.bucket.bucket, environ.cloudfront_bucket.bucket = private_bucket_name, cloudfront_bucket_name

        parser = DocxParser(message, sqs, environ)

        executor = parser()

        assert executor.status == "completed"
        
        parser.next()

        url = getattr(environ.project_rag_chunk, chunk_type).url
        # read pushed message from chunk queue
        chunk_queue = sqs.receive_message(
            QueueUrl=str(url))

        messages = chunk_queue["Messages"]
        for message in messages:
            rag_pipeline_message = RAGPipelineMessage(**json.loads(message["Body"]))
            results = rag_pipeline_message.results

            # assert property types
            assert isinstance(results, list)
            assert isinstance(results[0], SourceResult)
            assert isinstance(results[1], ParseResult)
            assert all(isinstance(kb, KnowledgeBase) for kb in rag_pipeline_message.knowledge_bases)
