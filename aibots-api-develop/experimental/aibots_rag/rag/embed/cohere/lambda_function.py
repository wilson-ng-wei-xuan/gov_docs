
from __future__ import annotations
import logging
from typing import List
import json
from aibots.aws_lambda.embedder import RAGEmbedder
from aibots.aws_lambda.models.rag import SQSRAGPipelineMessage
from aibots.aws_lambda.sqs_router import RAGSQSRouter
import boto3


class BedRockEmbedder:
    def __init__(self):
        """Class to generate all 3 responses from OpenAI"""

        self.content_type = "application/json"

        self.bedrock = boto3.client(
            service_name="bedrock-runtime", region_name="ap-southeast-1")
        self.accept = "*/*"

    def create_embeddings(self, texts: List[str], model="cohere.embed-english-v3") -> List[List[float]]:
        input_type = "search_document"
        body = json.dumps(
            {
                "texts": texts,
                "input_type": input_type,
            }
        )
        response = self.bedrock.invoke_model(
            body=body,
            modelId=model,
            accept=self.accept,
            contentType=self.content_type,
        )
        response_body = json.loads(response.get("body").read())
        return response_body["embeddings"]


def lambda_handler(event, context):
    bedrock = BedRockEmbedder()
    embedder = RAGEmbedder(event=event, context=context,
                           embedder=bedrock.create_embeddings)
    sqs_router = RAGSQSRouter()
    successes, fails = embedder.run()
    logging.getLogger().setLevel(logging.INFO)
    for _, success in enumerate(successes):
        try:
            message: SQSRAGPipelineMessage = SQSRAGPipelineMessage(
                **success["body"])
            sqs_router.send_message_to_rag_chunk_sqs(
                chunk=message.configs.store.type, message=message.model_dump())
        except Exception as e:
            fails.append(success)
            logging.error(e)
    failed_message_ids = [{"itemIdentifier": fail["messageId"]}
                          for fail in fails]
    return {"batchItemFailures": failed_message_ids}
