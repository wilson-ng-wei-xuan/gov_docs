from __future__ import annotations

import json
from typing import Any, Dict, List

import boto3
from aibots.models.rags.api import (
    ExecutionState,
    RAGPipelineStages,
    RAGPipelineStatus,
)
from aibots.models.rags.base import RAGPipelineEnviron, RAGPipelineExecutor
from aibots.models.rags.internal import (
    AIBotsPipelineMessage,
    ChunkResult,
    SourceResult,
    SQSMessageRecord,
)
from boto3 import client
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection
from pydantic import BaseModel, Field, validate_call


class OpenSearchCohereEmbeddingDocument(BaseModel):
    """
    model for each opensearch document to be added to index
    """

    source: str
    page_number: int
    last_update_date: str
    text: str
    chunk: int
    embedding: List[float] = Field(min_length=1024, max_length=1024)


class BedRockEmbedder:
    def __init__(self):
        """Class to generate all 3 responses from OpenAI"""

        self.content_type = "application/json"

        self.bedrock = boto3.client(
            service_name="bedrock-runtime", region_name="ap-southeast-1"
        )

        self.accept = "*/*"

    def create_embeddings(
        self, texts: List[str], model="cohere.embed-english-v3"
    ) -> List[List[float]]:
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


class FileIndexer:
    def __init__(
        self,
        host: str,
        collection: str,
        port: int = 443,
        region: str = "ap-southeast-1",
        service: str = "aoss",
        embedding_type="cohere",
        is_local: bool = False,
    ):
        """Upload files"""
        # Initialize index
        self.index_name = collection
        # Initialize dictionary of sizes
        embedding_sizes = {"cohere": 1024}

        # create an opensearch client and use the request-signer
        self.client = (
            self.__get_local_opensearch_client(host, port)
            if is_local
            else self.__get_aws_opensearch_client(
                host=host, port=port, region=region, service=service
            )
        )

        # Check if index exist, if not, create one
        if not self.client.indices.exists(index=self.index_name):
            settings = {
                "settings": {
                    "index": {
                        "knn": True,
                    }
                },
                "mappings": {
                    "properties": {
                        "source": {"type": "text"},
                        "page_number": {"type": "text"},
                        "last_update_date": {"type": "text"},
                        "text": {"type": "text"},
                        "chunk": {"type": "integer"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": embedding_sizes[embedding_type],
                            "method": {
                                "name": "hnsw",
                                "space_type": "innerproduct",
                                # "engine": "faiss",
                                "parameters": {"ef_construction": 256},
                            },
                        },
                    }
                },
            }
            self.client.indices.create(index=self.index_name, body=settings)

    def push_to_index(self, documents: List[Dict[str, Any]]):
        """
        args:
            documents(list): list of dictionaries of documents
        """

        # Iterate and push to index
        response_results = []
        for i, doc in enumerate(documents):
            response = self.client.index(
                index=self.index_name, body=doc, refresh=True
            )
            response_results.append(response["result"])
        return response_results

    def delete_file(self, source: str):
        query = {"query": {"match": {"source": source}}}
        response = self.client.search(
            index=self.index_name, body=query, version=True
        )
        file_deleted = None

        id_list = [q["_id"] for q in response["hits"]["hits"]]
        for id in id_list:
            self.client.delete(index=self.index_name, id=id)
            file_deleted = True
        return file_deleted

    def __get_aws_opensearch_client(
        self,
        host: str,
        region: str = "ap-southeast-1",
        service: str = "aoss",
        port: int = 443,
    ) -> OpenSearch:
        """
        creates aws opensearch client
        args:
            host (str): hostname,
            region (str): region name,
            service (str): service name,
            port (int): port number
        """
        credentials = boto3.Session().get_credentials()
        self.auth = AWSV4SignerAuth(credentials, region, service)
        return OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=self.auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            pool_maxsize=20,
            timeout=10,
        )

    def __get_local_opensearch_client(
        self,
        host: str = "localhost",
        port: int = 9200,
        username: str = "admin",
        password: str = "GovTech300%",
    ) -> OpenSearch:
        """
        creates opensearch client for local docker image of opensearch
        args:
            host (str): host of local docker opensearch
            port (int): port of local docker opensearch image
            username (str): string of username
            password (str): string of password
        """
        return OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=(username, password),
            use_ssl=False,
            verify_certs=False,
            connection_class=RequestsHttpConnection,
        )


class OpenSearchStorer(RAGPipelineExecutor):
    def __call__(self, *args, **kwargs) -> RAGPipelineStatus:
        try:
            chunked: ChunkResult = self.previous_result
            print("chunked", chunked)
            source: SourceResult = self.message.results[0]
            source_config = self.message.pipeline.config["source"]
            embedder = BedRockEmbedder()
            indexer = FileIndexer(
                host=source_config["host"],
                port=source_config["port"],
                collection=source_config["collection"],
                is_local=source_config["is_local"],
            )
            documents: List[Dict[str, Any]] = []

            embeddings = embedder.create_embeddings(
                [chunk.text for chunk in chunked.chunks]
            )

            # iterate and add documents
            for i, embedding in enumerate(embeddings):
                chunk = chunked.chunks[i]
                document: Dict[str, Any] = OpenSearchCohereEmbeddingDocument(
                    source=source.key,
                    page_number=chunk.page_number,
                    text=chunk.text,
                    chunk=chunk.chunk,
                    embedding=embedding,
                    last_update_date=chunked.metadata["last_updated_date"],
                ).model_dump()
                documents.append(document)
            # push to opensearch
            indexer.push_to_index(documents=documents)
            # Update message here
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.completed,
                knowledge_base=self.message.knowledge_base,
                error=None,
                results=json.dumps({"uploaded": True}),
                type=RAGPipelineStages.embeddings,
            )
        except Exception as e:
            # TODO: change if output is not correct
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.failed,
                knowledge_base=self.message.knowledge_base,
                error=str(e),
                results=json.dumps({"uploaded": False}),
                type=RAGPipelineStages.embeddings,
            )

    def next(self) -> None:
        # update db when opensearch upload succeeds
        pass


environ: RAGPipelineEnviron = RAGPipelineEnviron()
sqs = client("sqs", region_name="ap-southeast-1")


@validate_call
def lambda_handler(event: AIBotsPipelineMessage, context):
    failed: List[SQSMessageRecord] = []
    for i, message in enumerate(event.pipeline_messages):
        executor: RAGPipelineExecutor = OpenSearchStorer(message, sqs, environ)
        status: RAGPipelineStatus = executor()
        if status.error:
            # takes in failed sqs message record
            failed.append(event.records[i])
            continue
        executor.send_status(status=status)
        executor.next()

    return {
        "batchItemFailures": [
            {"itemIdentifier": fail.message_id} for fail in failed
        ]
    }
