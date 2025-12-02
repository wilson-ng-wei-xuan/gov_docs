from __future__ import annotations

import asyncio
import datetime
import json
import os
from getpass import getpass
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

import boto3
import numpy as np
import pandas as pd
import umap
from opensearchpy import (
    AWSV4SignerAuth,
    NotFoundError,
    OpenSearch,
    RequestsHttpConnection,
)
from semantic_chunkers import StatisticalChunker
from semantic_router.encoders import BedrockEncoder
from sklearn.cluster import HDBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from unstructured.chunking.title import chunk_by_title


class BedRockEmbedder:
    def __init__(self):
        self.content_type = "application/json"
        self.bedrock = boto3.client(service_name="bedrock-runtime")
        self.accept = "*/*"

    def create_embeddings(self, text, model="cohere.embed-english-v3"):
        input_type = "search_document"
        body = json.dumps({"texts": [text], "input_type": input_type})
        response = self.bedrock.invoke_model(
            body=body,
            modelId=model,
            accept=self.accept,
            contentType=self.content_type,
        )
        response_body = json.loads(response.get("body").read())
        return response_body["embeddings"][0]

    async def acreate_embeddings(self, text, model="cohere.embed-english-v3"):
        return await asyncio.to_thread(self.create_embeddings, text, model)


def get_last_modified_time(file_path):
    timestamp = Path.stat(file_path).st_mtime
    last_modified_time = datetime.datetime.fromtimestamp(
        timestamp, tz=datetime.timezone.utc
    )
    return last_modified_time.strftime("%Y-%m-%dT%H:%M:%S")


def parse_csv(file_path, header=0):
    df = pd.read_csv(file_path, header=header)
    df_json = df.to_dict(orient="records")
    df_json_with_metadata = []
    filename = file_path.split("/")[-1]
    last_update_date = get_last_modified_time(file_path)
    for row in df_json:
        df_json_with_metadata.append(
            {
                "text": f"File: {filename}, data: {str(row)}",
                "metadata": {
                    "source": filename,
                    "page_number": 0,
                    "last_update_date": last_update_date,
                },
            }
        )
    return df_json_with_metadata


def parse_excel(file_path, header=0):
    xls = pd.ExcelFile(file_path)
    df_json_with_metadata = []
    last_update_date = get_last_modified_time(file_path)
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, header=header, sheet_name=sheet_name)
        df_json = df.to_dict(orient="records")
        for row in df_json:
            filename = file_path.split("/")[-1]
            df_json_with_metadata.append(
                {
                    "text": f"File: {filename}, Sheet: {sheet_name}, data: {str(row)}",  # noqa 501
                    "metadata": {
                        "source": filename,
                        "page_number": sheet_name,
                        "last_update_date": last_update_date,
                    },
                }
            )
    return df_json_with_metadata


def chunk_document(elements, chunk_size):
    if any(el.category == "Title" for el in elements) and len(elements) > 3:
        elements = chunk_by_title(elements, new_after_n_chars=chunk_size)
        documents = []
        for element in elements:
            metadata = element.metadata.to_dict()
            del metadata["languages"]
            metadata["source"] = metadata["filename"]
            documents.append(
                {"text": element.text, "metadata": metadata}
                # Document(page_content=element.text, metadata=metadata)
            )
    else:
        text = "\n".join([el.text for el in elements])
        documents = semantic_chunker(text, 1200)
    print(f"{documents=}")
    return documents


def semantic_chunker(text, chunk_size):
    """
    returns:
        docs (list of langchain object): chunks
    """
    # Create a session using default credentials and config
    session = boto3.Session()

    # Retrieve credentials
    credentials = session.get_credentials()

    try:
        # Access the AWS credentials
        aws_access_key_id = credentials.access_key
        aws_secret_access_key = credentials.secret_key
        aws_session_token = credentials.token

        # Retrieve the region
        aws_region = session.region_name

    except:
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID") or getpass(
            "Enter AWS Access Key ID: "
        )
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY") or getpass(
            "Enter AWS Secret Access Key: "
        )
        aws_session_token = os.getenv("AWS_SESSION_TOKEN") or getpass(
            "Enter AWS Session Token: "
        )
        aws_region = os.getenv("AWS_REGION") or getpass("Enter AWS Region: ")

    encoder = BedrockEncoder(
        # region="ap-southeast-1",
        access_key_id=aws_access_key_id,
        secret_access_key=aws_secret_access_key,
        session_token=aws_session_token,
        region=aws_region,
        name="cohere.embed-english-v3",
        # client = client
    )
    chunker = StatisticalChunker(
        encoder=encoder,
        min_split_tokens=100,
        max_split_tokens=chunk_size // 5,
        dynamic_threshold=False,
    )
    if type(text) == list:
        text = "\n".join(text)

    chunking_results = chunker([text])
    list_of_chunks = ["".join(chunk.splits) for chunk in chunking_results[0]]
    return [{"text": c} for c in list_of_chunks]


def docs_to_json(docs, filename=None, last_modified=None):
    cleaned_json_list = []
    for doc in docs:
        page_number = str(doc.get("metadata", {}).get("page_number", ""))
        text = f"File name: {doc.get('metadata', {}).get('filename', filename)}, page: {page_number}\n{doc.get('text')}"  # noqa E501
        cleaned_json = {
            "text": text,
            "metadata": {
                "source": doc.get("metadata", {}).get("filename", filename),
                "page_number": page_number,
                "last_update_date": doc.get("metadata", {}).get(
                    "last_modified", last_modified
                ),
            },
        }
        cleaned_json_list.append(cleaned_json)
    return cleaned_json_list


def apply_umap(embeddings, n_neighbors=15, min_dist=0.1, n_components=2):
    umap_model = umap.UMAP(
        n_neighbors=n_neighbors, min_dist=min_dist, n_components=n_components
    )
    return umap_model.fit_transform(embeddings)


def clusterchunks(embeddings, min_cluster_size=2):
    reduced_emb = apply_umap(embeddings)
    hdb = HDBSCAN(min_cluster_size=min_cluster_size, store_centers="medoid")
    hdb.fit(reduced_emb)
    medoids = hdb.medoids_
    similarities = cosine_similarity(medoids, reduced_emb)
    medoids_index = np.argmax(similarities, axis=1)
    labels = hdb.labels_
    return labels, medoids_index


def split_long_strings(strings, X, overlap_percent=50):
    """
    Splits a list of strings into substrings of a specified maximum length with overlapping parts.

    Args:
        strings (list of str): The list of strings to be split.
        X (int): The maximum length of each substring.
        overlap_percent (int, optional): The percentage of overlap between consecutive substrings. Defaults to 50%.

    Returns:
        list of str: A list of substrings generated by splitting the input strings. Strings shorter than or equal to X are included as-is.

    """
    result = []
    for s in strings:
        if len(s) > X:
            step = (
                X * (100 - overlap_percent) // 100
            )  # Calculate the step size for overlapping substrings
            for i in range(0, len(s) - X + 1, step):
                result.append(s[i : i + X])
            # Add the final substring if there's remaining part
            if len(s) % X != 0:
                result.append(s[-X:])
        else:
            result.append(s)
    return result


class FileIndexer:
    embedding_sizes = {"cohere": 1024}

    def __init__(self, aoss_host, index_name, embedding_type="cohere"):
        self.index_name = index_name
        region = "ap-southeast-1"
        service = "aoss"
        credentials = boto3.Session().get_credentials()
        self.auth = AWSV4SignerAuth(credentials, region, service)

        if embedding_type == "cohere":
            self.embedder = BedRockEmbedder()
        else:
            raise ValueError(f"Embedding type {embedding_type} not supported")

        if not aoss_host:
            self.client = OpenSearch(
                hosts=[{"host": "localhost", "port": 9200}],
                http_auth=("admin", "ScrappyRAG123"),
                use_ssl=True,
                verify_certs=False,
                connection_class=RequestsHttpConnection,
                pool_maxsize=20,
                timeout=10,
            )
        else:
            self.client = OpenSearch(
                hosts=[{"host": urlparse(aoss_host).hostname, "port": 443}],
                http_auth=self.auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                pool_maxsize=20,
                timeout=10,
            )

    def ensure_index_exists(self, index_name, embedding_type="cohere"):
        if not self.client.indices.exists(index=index_name):
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
                            "dimension": FileIndexer.embedding_sizes[
                                embedding_type
                            ],
                            "method": {
                                "name": "hnsw",
                                "space_type": "innerproduct",
                                "engine": "faiss",
                                "parameters": {"ef_construction": 256},
                            },
                        },
                    }
                },
            }
            self.client.indices.create(index=index_name, body=settings)

    def push_to_index(self, documents):
        # Use bulk add
        # https://github.com/opensearch-project/opensearch-py/blob/main/guides/bulk.md#parallel-bulk

        # bulk_actions = []

        for i, doc in enumerate(documents):
            # print(f"{doc=}")
            start_time = perf_counter()
            document = {
                # "_index": self.index_name,
                "source": doc["metadata"]["source"],
                "page_number": doc["metadata"]["page_number"],
                "last_update_date": doc["metadata"]["last_update_date"],
                "text": doc["text"],
                "chunk": i,
                "embedding": doc["embedding"],
            }

            response = self.client.index(index=self.index_name, body=document)
            end_time = perf_counter()

            print(
                f"Indexing: {document['text']}\nResponse: {response}\n\n",
                "=" * 20,
            )
            print(f"Time taken: {end_time - start_time:.2f} seconds")

            # bulk_actions.append(document)

        # succeeded = []
        # failed = []
        # for success, item in helpers.parallel_bulk(
        #     self.client,
        #     actions=bulk_actions,
        #     chunk_size=10,
        #     raise_on_error=False,
        #     raise_on_exception=False,
        #     max_chunk_bytes=20 * 1024 * 1024,
        #     request_timeout=60,
        # ):
        #     if success:
        #         succeeded.append(item)
        #     else:
        #         failed.append(item)

        # if len(failed) > 0:
        #     print(f"There were {len(failed)} errors:")
        #     for item in failed:
        #         print(
        #             f"{item['index']['error']}: {item['index']['exception']}"
        #         )

        # if len(succeeded) > 0:
        #     print(f"Bulk-inserted {len(succeeded)} items.")

    def delete_file(self, file_name):
        # Use delete by query
        # https://opensearch-project.github.io/opensearch-py/api-ref/clients/opensearch_client.html#opensearchpy.OpenSearch.delete_by_query
        # Update: not supported by aoss
        # - https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-genref.html#serverless-operations)

        query = {"query": {"match": {"source": file_name}}}
        response = self.client.search(
            index=self.index_name, body=query, version=True
        )
        file_deleted = None

        id_list = [q["_id"] for q in response["hits"]["hits"]]
        for id in id_list:
            self.client.delete(index=self.index_name, id=id)
            file_deleted = True
        return file_deleted

    def query(self, query, k=3, include_embeddings=False):
        query_vector = self.embedder.create_embeddings(query)

        # Hybrid search
        payload = {
            "size": k,
            "query": {
                "bool": {
                    "should": [
                        {
                            "script_score": {
                                "query": {"match": {"text": query}},
                                "script": {"source": "_score"},
                            }
                        },
                        {
                            "knn": {
                                "embedding": {"vector": query_vector, "k": k}
                            }
                        },
                    ]
                }
            },
        }

        exclude_properties = []
        if not include_embeddings:
            exclude_properties.append("embedding")

        docs = self.client.search(
            body=payload,
            index=self.index_name,
            _source_excludes=exclude_properties,
        )

        return docs["hits"]["hits"]


async def upsert_file(
    s3_file_path, index_name, aoss_host, embedding_type="cohere"
):
    """
    Upserts a file into an OpenSearch index. Combining parsing,
    chunking, embedding, and storing

    Args:
        s3_file_path (str): S3 URI Location of the file
        index_name (str): OpenSearch index to upsert embeddings into
        aoss_host (str): URL of AWS OpenSearch Service
        embedding_type (str, optional): Embedding model to use.
                                        Defaults to "cohere"

    Returns:
        JSON: JSON response of upsert operation
    """

    # Downloads S3 file
    file_path = download_s3_file(s3_file_path)
    # file_path = s3_file_path
    # Determine file type and parse
    if file_path.endswith(".csv"):
        documents = parse_csv(file_path)
    elif file_path.endswith(".xlsx"):
        documents = parse_excel(file_path)
    elif file_path.endswith(".txt"):
        try:
            with Path.open(file_path, "r") as file:
                file_content = file.read()
            documents = semantic_chunker(file_content, 1200)
        except FileNotFoundError:
            return {"statusCode": 404, "body": "File not found"}
    else:
        if file_path.endswith(".pdf"):
            from unstructured.partition.pdf import partition_pdf

            elements = partition_pdf(
                filename=file_path,
                # strategy="fast",
                pdf_infer_table_structure=True,
                model_name="yolox",
            )
        elif file_path.endswith(".doc"):
            from unstructured.partition.doc import partition_doc

            elements = partition_doc(filename=file_path)
        elif file_path.endswith(".docx"):
            from unstructured.partition.docx import partition_docx

            elements = partition_docx(filename=file_path, strategy="fast")
        elif file_path.endswith(".ppt"):
            from unstructured.partition.ppt import partition_ppt

            elements = partition_ppt(filename=file_path)
        elif file_path.endswith(".pptx"):
            from unstructured.partition.pptx import partition_pptx

            elements = partition_pptx(filename=file_path)
        elif file_path.endswith(".html"):
            from unstructured.partition.html import partition_html

            elements = partition_html(url=file_path)
        else:
            return {"statusCode": 400, "body": "Unsupported file type"}

        elements = [el for el in elements if el.category != "Header"]
        documents = chunk_document(
            elements, chunk_size=1200
        )  # Adjust chunk_size as needed

    # Add metadata
    documents = docs_to_json(
        documents,
        file_path.split("/")[-1],
        get_last_modified_time(file_path),
    )

    for i, doc in enumerate(documents):
        print("Doc", i, ". Length", len(doc["text"]))

    # Generate embeddings
    # Parallelize API calls using asyncio.gather
    embedder = BedRockEmbedder()
    embed_tasks = [
        embedder.acreate_embeddings(doc["text"]) for doc in documents
    ]
    embeddings = await asyncio.gather(*embed_tasks)
    for i, doc in enumerate(documents):
        doc["embedding"] = embeddings[i]

    # if len(documents) > 1:
    #     # Cluster the documents
    #     embeddings = [doc["embedding"] for doc in documents]
    #     cluster_labels, medoids_index = clusterchunks(embeddings)

    #     # Update documents with cluster information
    #     for i, doc in enumerate(documents):
    #         doc["metadata"]["cluster"] = int(cluster_labels[i])
    #         doc["metadata"]["medoids"] = (
    #             int(1) if i in medoids_index else int(0)
    #         )

    # else:
    #     documents[0]["metadata"] = {
    #         "source": file_path.split("/")[-1],
    #         "page_number": 1,
    #         "last_update_date": get_last_modified_time(file_path),
    #         "cluster": 0,
    #         "medoids": 0,
    #     }

    # Push documents to the index
    fileindexer = FileIndexer(aoss_host, index_name, embedding_type)

    # Create index if it doesn't exist
    fileindexer.ensure_index_exists(index_name, embedding_type)

    # Delete all existing entries for the file
    try:
        fileindexer.delete_file(file_path.split("/")[-1])
    except NotFoundError:
        print(f"No existing entries for file: {file_path}")

    fileindexer.push_to_index(documents)

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "success"}),
        "headers": {
            "Content-Type": "application/json",
        },
    }


def query_text(
    text: str,
    index_name: str,
    aoss_host: str,
    embedding_type="cohere",
    top_n=3,
):
    """
    Queries a text on an OpenSearch index. Text is first embedded
    into a vector and then queried

    Args:
        text (str): Text to base query on
        index_name (str): OpenSearch index to use for query
        aoss_host (str): URL of AWS OpenSearch Service
        embedding_type (str, optional): Embedding model to use.
                                        Defaults to "cohere"

    Returns:
        JSON: JSON response of query operation
    """
    fileindexer = FileIndexer(aoss_host, index_name, embedding_type)

    return {
        "statusCode": 200,
        "body": json.dumps(fileindexer.query(text, k=top_n)),
        "headers": {
            "Content-Type": "application/json",
        },
    }


def delete_file(
    file_name: str, index_name: str, aoss_host: str, embedding_type="cohere"
):
    """
    Deletes all entries associated with a filename in an OpenSearch index

    Args:
        file_name (str): Filename to delete entries for
        index_name (str): OpenSearch index to use for delete operation
        aoss_host (str): URL of AWS OpenSearch Service
        embedding_type (str, optional): Embedding model to use.
                                        Defaults to "cohere"

    Returns:
        JSON: JSON response of delete operation
    """

    fileindexer = FileIndexer(aoss_host, index_name, embedding_type)
    deleted = fileindexer.delete_file(file_name)
    if deleted:
        return {
            "statusCode": 200,
            "body": "File deleted successfully.",
            "headers": {
                "Content-Type": "application/json",
            },
        }

    return {
        "statusCode": 404,
        "body": "No file found with the specified name.",
        "headers": {
            "Content-Type": "application/json",
        },
    }


def download_s3_file(s3_file_path: str):
    bucket, key = s3_file_path.replace("s3://", "").split("/", 1)

    file_name = s3_file_path.split("/")[-1]
    local_tmp_file_path = f"/tmp/{file_name}"  # noqa S108

    s3 = boto3.client("s3")
    s3.download_file(bucket, key, local_tmp_file_path)

    return local_tmp_file_path


def lambda_handler(event, context) -> dict[str, Any]:
    loop = asyncio.get_event_loop()

    aoss_host = os.getenv("PROJECT_RAG_OPENSEARCH__URL")

    # TODO: Collection name should be dynamically managed and
    # tracked in KnowledgeBase schema
    collection_name = os.getenv("PROJECT_RAG_OPENSEARCH__NAME")

    # TODO: Deploy a local OpenSearch docker image for testing
    # https://hub.docker.com/r/opensearchproject/opensearch

    flow = event["flow"]

    if flow == "upsert":
        file_path = event["file_path"]
        index_name = event["index_name"]
        embedding_type = event.get("embedding_type", "cohere")

        return loop.run_until_complete(
            upsert_file(file_path, index_name, aoss_host, embedding_type)
        )

    if flow == "query":
        text = event["text"]
        index_name = event["index_name"]
        embedding_type = event.get("embedding_type", "cohere")
        top_n = int(event.get("top_n", 3))

        return query_text(
            text, index_name, aoss_host, embedding_type, top_n=top_n
        )

    if flow == "delete":
        file_path = event["file_path"]
        index_name = event["index_name"]
        embedding_type = event.get("embedding_type", "cohere")

        return delete_file(file_path, index_name, aoss_host, embedding_type)

    return {
        "statusCode": 400,
        "body": "Missing/Invalid flow. Valid flows: upsert, query, delete",
        "headers": {
            "Content-Type": "application/json",
        },
    }


if __name__ == "__main__":
    event = {
        "flow": "upsert",
        "file_path": "story.txt",
        # "file_path": "s3://s3-sitezingress-aibots-471112510129-cloudfront/files/fdff2a60-2b1f-4073-968d-aa949cf14409/alzheimers.txt",  # "alzheimers.txt",
        # "file_path": "s3://s3-sitezingress-aibots-471112510129-cloudfront/files/fdff2a60-2b1f-4073-968d-aa949cf14409/story.txt",
        # "file_path": "s3://s3-sitezingress-aibots-471112510129-cloudfront/files/fdff2a60-2b1f-4073-968d-aa949cf14409/wealthiest_people.docx",
        "file_path": "s3://s3-sitezingress-aibots-471112510129-cloudfront/files/fdff2a60-2b1f-4073-968d-aa949cf14409/computer.pdf",
        "index_name": "test_knowledge_base",
    }
    event2 = {
        "flow": "query",
        "text": "What happen after the long slumber?",
        # "text": "Who are the richest people?",
        # "text": "What is a CPU?",
        "index_name": "test_knowledge_base",
        "top_n": 1,
    }
    event3 = {
        "flow": "delete",
        # "file_path": "s3://s3-sitezingress-aibots-471112510129-cloudfront/files/fdff2a60-2b1f-4073-968d-aa949cf14409/alzheimers.txt",  # "alzheimers.txt",
        "file_path": "story.txt",
        # "file_path": "s3://s3-sitezingress-aibots-471112510129-cloudfront/files/fdff2a60-2b1f-4073-968d-aa949cf14409/wealthiest_people.docx",
        # "file_path": "s3://s3-sitezingress-aibots-471112510129-cloudfront/files/fdff2a60-2b1f-4073-968d-aa949cf14409/computer.pdf",
        "index_name": "test_knowledge_base",
    }
    result = lambda_handler(event, None)
    print(result)
