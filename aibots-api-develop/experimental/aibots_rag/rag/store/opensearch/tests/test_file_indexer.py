import shlex
import os
import subprocess
from time import sleep

from ..lambda_function import FileIndexer, OpenSearchCohereEmbeddingDocument


class TestFileIndexer:
    def test_file_indexer_push_to_index_success(self, request) -> None:
        # starts opensearch docker container
        os.chdir(request.fspath.dirname)

        subprocess.run(
            shlex.split("docker compose up -d"),
            env={**os.environ,
                 "OPENSEARCH_INITIAL_ADMIN_PASSWORD": os.environ["OPENSEARCH_INITIAL_ADMIN_PASSWORD"]
                 }
        )
        # waits for opensearch to complete booting up
        sleep(10)
        file_indexer = FileIndexer(host="localhost", port=9200, collection="pytest", is_local=True)
        example_opensearch_document: OpenSearchCohereEmbeddingDocument = request.getfixturevalue(
            "example_opensearch_document")
        example_opensearch_document_dict = example_opensearch_document.model_dump(mode="json")
        response = file_indexer.push_to_index(documents=[example_opensearch_document_dict])

        assert response[0] == "created"

        index_name, source = file_indexer.index_name, example_opensearch_document.source

        opensearch_response = file_indexer.client.search(
            index=index_name, body={"query": {"match": {"source": source}}}, version=True
        )

        queried = opensearch_response["hits"]["hits"][0]["_source"]
        assert queried["source"] == source
        assert queried["chunk"] == example_opensearch_document.chunk
        assert queried["text"] == example_opensearch_document.text
        assert queried["embedding"] == example_opensearch_document.embedding
        assert queried["page_number"] == example_opensearch_document.page_number
        assert queried["last_update_date"] == example_opensearch_document.last_update_date
        file_indexer.delete_file(source)
        subprocess.run(
            shlex.split("docker compose down -v"),
            env={
                **os.environ}
        )
        os.chdir(request.config.invocation_params.dir)
