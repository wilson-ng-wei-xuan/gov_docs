from pydantic import validate_call
from sklearn.cluster import HDBSCAN
import logging
from typing import List, Dict, Any, Literal, Union
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import boto3
import json
from langchain_community.embeddings import BedrockEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from aibots.aws_lambda.chunker import RAGChunker
from aibots.aws_lambda.sqs_router import RAGSQSRouter
from aibots.aws_lambda.models.rag import SQSRAGPipelineMessage

from aibots.models.rags.base import RAGPipelineExecutor

from aibots.models.rags.api import RAGPipelineStatus

from aibots.models.rags.internal import ChunkResult, Page, ParseResult, SourceResult

from aibots.models.rags.api import ExecutionState, RAGPipelineStages


class BedRockEmbedder:
    def __init__(self):
        """Class to generate all 3 responses from OpenAI"""

        self.content_type = 'application/json'

        self.bedrock = boto3.client(
            service_name='bedrock-runtime', region_name="ap-southeast-1")
        self.accept = '*/*'

    def create_embeddings(self, text, model='cohere.embed-english-v3'):
        input_type = "search_document"
        body = json.dumps({
            "texts": [
                text,
            ],
            "input_type": input_type}
        )
        response = self.bedrock.invoke_model(
            body=body,
            modelId=model,
            accept=self.accept,
            contentType=self.content_type
        )
        response_body = json.loads(response.get('body').read())
        return response_body['embeddings'][0]


class DataframeChunker(RAGPipelineExecutor):
    def __call__(self) -> RAGPipelineStatus:
        try:
            bedrockembed = BedRockEmbedder()
            parsed: ParseResult = self.previous_result
            config = self.message.pipeline.config["chunk"]
            chunk_size, min_cluster_size, analyze_full_excel = config[
                "chunk_size"], config["min_cluster_size"], config["analyze_full_excel"]

            chunk_results: List[Page] = []
            chunk_count: int = 0

            for doc in parsed.pages:
                # chunk results here
                text = doc.text
                chunks = self.semantic_chunker(
                    texts=[text], chunk_size=chunk_size)

                for chunk in chunks:
                    chunk_page = Page(**doc.model_dump())
                    chunk_page.chunk = chunk_count
                    chunk_page.text = chunk
                    chunk_count += 1
                    chunk_results.append(chunk_page)

                # if analyze_full_excel == "True":
                #     create_embeddings = True if len(chunks) > 5 else False
                #     embedding_list = []
                # TODO: refactor this entire thing
                # if create_embeddings:
                #     embedding_list = [bedrockembed.create_embeddings(
                #         result.text) for result in chunk_results]
                #     cluster_centres = self.cluster_text(
                #         embedding_list, min_cluster_size)  # Returns list of medoids
                #     if len(cluster_centres) > 0:
                #         documents = [documents[idx] for idx in cluster_centres]

            self.message.results.append(
                ChunkResult(chunks=chunk_results)
            )

            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.completed,
                knowledge_base=self.message.knowledge_base,
                error=None,
                results=json.dumps([chunk_result.model_dump()
                                    for chunk_result in chunk_results]),
                type=RAGPipelineStages.chunking
            )
        except Exception as e:
            return RAGPipelineStatus(
                agent=self.message.agent,
                pipeline=self.message.id,
                status=ExecutionState.failed,
                knowledge_base=self.message.knowledge_base,
                error=str(e),
                results=None,
                type=RAGPipelineStages.chunking
            )

    def semantic_chunker(self, texts: List[str], chunk_size: int):
        """
        returns:
            docs (list of langchain object): chunks
        """
        # TODO: refactor and rethink this whole thing,
        #  there's an underlying langchain issue and
        #  this code is poorly documented

        embeddings = BedrockEmbeddings(
            region_name="ap-southeast-1",
            model_id='cohere.embed-english-v3'
        )

        text_splitter = SemanticChunker(
            embeddings, number_of_chunks=chunk_size)

        docs = text_splitter.create_documents(texts)
        print("docs", docs)

        list_of_chunks = [doc.page_content for doc in docs]

        return list_of_chunks

    def cluster_text(self, vector_array, min_cluster_size):
        """
        returns:
            docs (list of langchain object): chunks
        """
        hdb = HDBSCAN(min_cluster_size=min_cluster_size,
                      store_centers='medoid')
        hdb.fit(vector_array)
        medoids = hdb.medoids_
        if len(medoids) > 5:
            similarities = cosine_similarity(medoids, vector_array)
            most_similar_indices = np.argmax(similarities, axis=1)

            return most_similar_indices
        else:
            return []

    def chunk_docs(self, docs: List[Dict[str, Any]], chunk_size: int,
                   min_cluster_size: int,
                   analyze_full_excel: Union[Literal["False"], Literal["True"]]) -> List[Dict[str, Any]]:
        bedrockembed = BedRockEmbedder()
        documents = docs
        row_list = [doc["text"]
                    for doc in documents]  # This is a list of dictionary

        row_list_chunked = []
        for row in row_list:
            if len(str(row)) > chunk_size:
                chunks = self.semantic_chunker(str(row), chunk_size)
                for chunk in chunks:
                    row_list_chunked.append(chunk)
            else:
                row_list_chunked.append(str(row))

        # Convert all rows into strings
        if len(row_list_chunked) > 0:
            row_list = row_list_chunked
        else:
            row_list = [str(row) for row in row_list]
        cluster_centres = []
        # Cluster if required
        if analyze_full_excel == "True":
            create_embeddings = True if len(row_list) > 5 else False
            embedding_list = []

            if create_embeddings:
                embedding_list = [bedrockembed.create_embeddings(
                    str(text)) for text in row_list]
                cluster_centres = self.cluster_text(
                    embedding_list, min_cluster_size)  # Returns list of medoids
                if len(cluster_centres) > 0:
                    documents = [documents[idx] for idx in cluster_centres]

        return [{"text": document["text"],
                 **document["metadata"], "chunk": i} for i, document in enumerate(documents)]

    def next(self) -> None:
        stringify = json.dumps(self.message.model_dump(mode="json"))
        # send out stringify message via sqs
        self.sqs.send_message(QueueUrl=str(self.environ.project_rag_store.url), MessageBody=stringify)


def lambda_handler(event, context):
    chunker = RAGChunker(event=event, context=context, chunker=chunk_docs)
    successes, fails = chunker.run()
    sqs_router = RAGSQSRouter()
    logging.getLogger().setLevel(logging.INFO)
    for _, success in enumerate(successes):
        try:
            message: SQSRAGPipelineMessage = SQSRAGPipelineMessage(
                **success["body"])
            sqs_router.send_message_to_rag_chunk_sqs(
                chunk=message.configs.embed.type, message=message.model_dump())
        except Exception as e:
            fails.append(success)
            logging.error(e)
    failed_message_ids = [{"itemIdentifier": fail["messageId"]}
                          for fail in fails]
    return {"batchItemFailures": failed_message_ids}
