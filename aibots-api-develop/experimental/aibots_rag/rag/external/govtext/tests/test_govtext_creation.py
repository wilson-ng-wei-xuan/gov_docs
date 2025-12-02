from lambda_function import lambda_handler
import httpx
import os
import requests

class TestLambdaHandler:

    def test_dataset_creation(self):
        base_url = os.environ["BASE_URL"]
        api_key = os.environ["API_KEY"]
        headers = {
            'accept': 'application/json',
            'X-API-KEY': api_key,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0'
        }
        endpoint = f"{base_url}/datasets"
        response = httpx.post(endpoint, headers=headers)
        print(response.json()['dataset_id'])
        os.environ["DATASET_ID"] = response.json()['dataset_id']
        assert response.status_code==200

    def test_delete_successfully(self):
        dataset_id = os.environ["DATASET_ID"]
        event = {
            "action": "delete",
            "id": dataset_id,
        }
        result = lambda_handler(event, None)
        print(result)
        assert result.status_code == 200

    def test_delete_deleted_dataset(self):
        dataset_id = "60911588-ae25-4e03-9c70-ab170b4e78ac"
        event = {
            "action": "delete",
            "id": dataset_id,
        }
        result = lambda_handler(event, None).json()
        assert result["error"]["type"] == "Not Found"
        assert result["error"]["status"] == 404
        assert result["error"]["message"] == "Dataset not found."

    def test_delete_non_existing_id(self):
        dataset_id = "a1118332-36f5-471c-b9d9-2b52811e09a0"
        event = {
            "action": "delete",
            "id": dataset_id,
        }
        result = lambda_handler(event, None).json()
        assert result["error"]["type"] == "Not Found"
        assert result["error"]["status"] == 404
        assert result["error"]["message"] == "Dataset not found."


    def test_upsert_zip(self):
        event = {
            "action": "post",
            "file_paths": ["Archive.zip"],
            'chunk_strategy': 'FIXED_SIZE',
            'chunk_size': '300',
            'chunk_overlap': '30',
            'chunk_separators': [],
            'parse_output_format': 'TEXT',
        }
        result = lambda_handler(event, None).json()
        os.environ["DATASET_ID"] = result["dataset_id"]
        os.environ["JOB_ID"] = result["job_id"]
        os.environ["CSV_DOCUMENT_ID"] = result["upsert_document_ids"]["Archive/test1.csv"]

    def test_patch_pdf(self):
        dataset_id = os.environ["DATASET_ID"]
        csv_document_id = os.environ["CSV_DOCUMENT_ID"]
        event = {
            "action": "patch",
            "id": dataset_id,
            "file_paths": ['Archive.zip'
            ],
            "delete_document_ids": [csv_document_id],
            "chunk_strategy": "FIXED_SIZE",
            "chunk_size": "100",
            "chunk_overlap": "10",
            "chunk_separators": [],
            "parse_output_format": "TEXT"
        }
        result = lambda_handler(event,None)
        print(result.json())
        assert result.status_code == 200

    def test_job(self):
        job_id = os.environ["JOB_ID"]
        event = {
            "action": "job",
            "id": job_id
        }
        result = lambda_handler(event, None).json()
        print(result)
