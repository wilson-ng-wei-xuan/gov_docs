from typing import List

from ..lambda_function import BedRockEmbedder


class TestBedrockEmbedder:
    def test_bedrock_embedder_create_embeddings_success(self, request) -> None:
        example_texts: List[str] = request.getfixturevalue("example_texts")
        embedder = BedRockEmbedder()
        embeddings = embedder.create_embeddings(example_texts)
        assert len(example_texts) == len(embeddings)
        assert all(isinstance(embedding, list) for embedding in embeddings)
