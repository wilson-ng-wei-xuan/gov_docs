import json
from copy import deepcopy
from io import BufferedIOBase, BytesIO
from typing import Dict, Any, Optional, Mapping, Tuple, List

from pydantic import BaseModel, AnyUrl, Field

from public.exceptions import LPException, LPEmbeddingsException

from .base import EmbeddingsEngine, Embeddings


try:
    import aiohttp
except ImportError as e:
    # TODO: Raise more informative error
    raise LPException("Imports not satisfied")


LLM_STACK_BASE_URL: str = "https://api.stack.govtext.gov.sg"


class LLMStackMetadata(BaseModel):
    """
    Metadata class for storing LLM Stack metadata

    Attributes:
        url (AnyUrl): Presigned S3 URL
        s3_url (AnyUrl): S3 Object URL to store file
        key (str): Flow key
        access_key (str): AWS Access Key
        security_token (str): AWS security token
        policy (str): AWS S3 policy
        signature (str): Signature of the Lambda function to be invoked
    """

    url: AnyUrl
    s3_url: AnyUrl = Field(alias="s3_object_url")
    key: str
    access_key: str = Field(alias="AWSAccessKeyId")
    security_token: str = Field(alias="x-amz-security-token")
    policy: str
    signature: str

    class Config:
        allow_population_by_field_name: bool = True


class LLMStackEngine(EmbeddingsEngine):
    """
    Class for wrapping embeddings functionality provided from LLM Stack

    """

    def __init__(self, **session: Mapping[str, Any]):
        """
        Creates an LLMStackEngine

        Attributes:
            **session (Mapping[str, Any]): Session details for interacting with LLM Stack APIs
        """
        super().__init__()
        self.client: aiohttp.ClientSession = aiohttp.ClientSession(
            base_url=LLM_STACK_BASE_URL, **session
        )
        self.s3_client: aiohttp.ClientSession = aiohttp.ClientSession()

    async def close(self, *args, **kwargs):
        """
        Closes the underlying sessions
        """
        await self.client.close()
        await self.s3_client.close()

    async def generate(
        self,
        collection: str,
        file: BytesIO,
        flow_id: str,
        user: str,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Convenience function for wrapping embeddings generation with the LLM stack

        Args:
            collection (str): Collection name
            file (BytesIO): File to be uploaded
            flow_id (str): ID of the flow
            user (str): User details
            filename (str): Name of the file

        Returns:
            Dict[str, Any]: Generated output
        """
        # Retrieve presigned S3 URL
        resp: aiohttp.ClientResponse = await self.client.get(
            "/v1/flows/upload-file-url",
            params={"flow_id": flow_id, "filename": filename},
        )
        output: Dict[str, Any] = json.loads(await resp.text())

        # Validate output
        if output["status"] != "success":
            raise LPEmbeddingsException(
                "Unable to generate embeddings using LLM Stack"
            )

        # Upload file to S3
        metadata: LLMStackMetadata = LLMStackMetadata(
            **{
                "url": output["data"]["url"],
                "s3_url": output["data"]["s3_object_url"],
                **output["data"]["fields"],
            }
        )
        form: aiohttp.FormData = aiohttp.FormData(
            metadata.dict(by_alias=True, exclude={"url", "s3_url"})
        )
        form.add_field("file", bytes(file.getvalue()), filename=filename)
        resp: aiohttp.ClientResponse = await self.s3_client.post(
            metadata.url, data=form
        )

        if not resp.ok:
            raise LPEmbeddingsException(
                "Unable to generate embeddings using LLM Stack"
            )

        # Trigger flow to generate embeddings on document
        resp: aiohttp.ClientResponse = await self.client.post(
            "/v1/flows/execute",
            json={
                "flow_id": flow_id,
                "user_id": user,
                "inputs": [
                    {
                        "urls": [],
                        "file_urls": [metadata.s3_url],
                        "separators": ["\n\n"],
                        "chunk_size": 1200,
                        "collection_name": collection,
                        "number_of_returned_documents": 100,
                    }
                ],
            },
        )
        output: Dict[str, Any] = json.loads(await resp.text())

        # Validate output
        if output["status"] != "success":
            raise LPEmbeddingsException(
                "Unable to generate embeddings using LLM Stack"
            )

        # Structure return values
        embeddings: Embeddings = Embeddings(
            collection=collection,
            metadata=metadata.dict(),
        )
        embeddings.metadata.update(
            {"documents": output["data"][0].get("documents")}
        )

        return embeddings.dict()

    async def query(
        self, prompt: str, user: str, collection: str, **params
    ) -> str:
        """ """
        query_params: Dict[str, Any] = deepcopy(params)
        query_params["inputs"] = [
            {"question": prompt, "collection_name": collection}
        ]
        query_params["user_id"] = user
        print(f"{query_params=}")
        resp: aiohttp.ClientResponse = await self.client.post(
            "/v1/flows/execute", json=query_params
        )
        print(f"{await resp.text()=}")
        output: str = "\n".join(
            [
                i["content"]
                for i in (json.loads(await resp.text()))
                .get("data", [{"documents": []}])[0]
                .get("documents", [])
            ]
        )

        return output

    async def delete(
        self,
        collection: str,
        flow_id: str,
        user: str,
        filename: str,
    ) -> Dict[str, Any]:
        """ """

        resp: aiohttp.ClientResponse = await self.client.post(
            "/v1/flows/execute",
            json={
                "flow_id": flow_id,
                "user_id": user,
                "inputs": [
                    {
                        "collection_name": collection,
                        "document_names": [filename],
                    }
                ],
            },
        )

        return json.loads(await resp.text())

    async def list(
        self, collection: str, flow_id: str, user: str, filename: str = None
    ) -> Dict[str, Any]:
        """ """
        if filename:
            documents = [filename]
        else:
            documents = []

        # print("calling LLMstack with:", flow_id, user, collection, documents)
        resp: aiohttp.ClientResponse = await self.client.post(
            "/v1/flows/execute",
            json={
                "flow_id": flow_id,
                "user_id": user,
                "inputs": [
                    {
                        "collection_name": collection,
                        "document_names": documents,
                    }
                ],
            },
        )

        return json.loads(await resp.text())




async def lambda_handler(event, context):
    for record in event['Records']:
        pass