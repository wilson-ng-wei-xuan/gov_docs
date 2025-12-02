import base64
import json, os
from typing import Optional

from fastapi import APIRouter, Security, HTTPException, Request, Form, UploadFile, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, AnyHttpUrl
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
from starlette.datastructures import MutableHeaders

import logging

from app.config import boto_config, LLMSTACK_API_SECRET
from app.utils.secret_manager_util import get_json_secret_as_dict

llmstack_secret = get_json_secret_as_dict(
    LLMSTACK_API_SECRET,
    endpoint_url=os.getenv("SECRETS_MGR_ENDPOINT_URL"),
    boto_config=boto_config,
)

class PublishFlowType(BaseModel):
    creator_id: str = Form(...)
    flow_yaml_file: UploadFile = Form(...)
    with_app: Optional[bool] = Form(default=False)
    app_metadata: Optional[str] = Form(...)

    class Config:
        schema_extra = {
            "example": {
                'creator_id': 'gvinto@gmail.com', 
                'flow_yaml_file': 'file contents',
                'with_app': True,
                "app_metadata": {"title": "My App", "description": "My App Description"}
            }
        }

router = APIRouter()
security_http_bearer = HTTPBearer()

@router.post("/get_api_key")
async def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    '''
    Returns a valid API key for use with the LLM Stack API
    '''
    llmstack_api_key = llmstack_secret.get("LLMSTACK_API_KEY")
    return JSONResponse(content={"api_key":llmstack_api_key})


@router.post("/flow/publish")
async def publish_flow(form_data: PublishFlowType = Depends(), credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    '''
    Serves as a proxy to the LLM Stack API's /flow/publish endpoint
    '''
    print(f"{form_data=}")

    flow_publish_endpoint = 'https://api.stack.govtext.gov.sg/v1/flows/publish'
    llmstack_api_key = llmstack_secret.get("LLMSTACK_API_KEY")

    headers = {"Authorization":f"Bearer {llmstack_api_key}"}

    data = {"creator_id":form_data.creator_id, "with_app":form_data.with_app, "app_metadata":form_data.app_metadata}
    files = {"flow_yaml_file": await form_data.flow_yaml_file.read()}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(flow_publish_endpoint, headers=headers, data=data, files=files, timeout=30.0)
        print(f"{response=}")

        response_json = response.json()
        print(f"{response_json=}")

    return JSONResponse(content=response_json, status_code=response.status_code)
