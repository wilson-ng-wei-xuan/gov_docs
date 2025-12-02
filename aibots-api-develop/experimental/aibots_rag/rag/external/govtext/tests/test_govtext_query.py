from lambda_function import lambda_handler
import os
import requests

class TestLambdaHandlerQuery:
    def test_query(self):
        dataset_id = "29a35cc9-4f1d-4808-b711-b9736b22d0a1"
        event = {
            "action": "query",
            "dataset_id": dataset_id,
            "text": "what happen in season 2?",
            "top_k": 1
        }
        result = lambda_handler(event, None)
        print(result.json())
        assert result.status_code == 200

    def test_query_2(self):
        dataset_id = "29a35cc9-4f1d-4808-b711-b9736b22d0a1"
        event = {
            "action": "query",
            "dataset_id": dataset_id,
            "text": "who is the Clarke?",
            "top_k": 3
        }
        result = lambda_handler(event, None)
        print(result.json())
        assert result.status_code == 200

    def test_get_job(self):
        job_id = "f2df5464-543c-4c8b-b56b-a27a399b876c"
        event = {
            "action": "job",
            "id": job_id
        }
        result = lambda_handler(event, None)
        print(result.json())
        assert result.status_code == 200