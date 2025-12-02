import base64
import json
import datetime
import secrets, hashlib
from uuid import uuid4

from typing import Optional
import traceback
import boto3 as boto3

from fastapi import APIRouter, Security, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, constr
from fastapi.responses import RedirectResponse

from app import config
from app.models.apikey.apikey_model import ApikeyModel
from app.utils import llm_util
from app.utils.auth_util import check_token_permission
from app.config import (logger, dynamodb, AWS_REGION_NAME, SNS_SLACK_TOPIC_ARN, DATETIME_TZ_FORMAT, TABLE_MOONSHOT_APIKEY, 
                        COHERE_MODEL_DEFAULT, COHERE_TEMPERATURE_DEFAULT, COHERE_MAX_TOKENS_DEFAULT)

router = APIRouter()
security_http_bearer = HTTPBearer()

model_apikey = ApikeyModel(dynamodb, TABLE_MOONSHOT_APIKEY)

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)

class ApikeyType(BaseModel):
    apikey: Optional[str] = None
    email: Optional[str]
    enabled: Optional[bool] = True
    project: constr(strip_whitespace=True, to_lower=True, min_length=6, max_length=20, regex="^[A-Za-z0-9_-]*$")
    agency: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "project": "launchpad",
            }
        }

def api_key_auth(apikey: str):
    print(f"{apikey=}")

    apihash = f"{apikey[:6]}.{hashlib.sha256(apikey.encode('utf-8')).hexdigest()}"
    response = model_apikey.get_key_owner(apihash)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )
    
    return response

@router.post("/generate")
async def generation(payload: ApikeyType, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Generates a new API key for the calling user and returns it.
    User must save the generated key as it will not be retrievable again.
    Please generate a separate key for each application/project
    Project ID must be unique
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    email = jwt_sub.get('email')
    agency = jwt_sub.get('agency','')

    enabled = payload.enabled
    project = payload.project.lower()
    # agency = payload.agency

    # Check if project ID already exists
    response = model_apikey.get_key_by_project(project)
    if response.get('Items'):
        raise HTTPException(status_code=400, detail="Project ID already exists")

    # Generate a new API key, keep the first 6 characters for easy reference and appending a hash of the full key
    # This means that the full key is never stored in the database
    # Users will need to regenerate a new key if they lose it
    apikey = secrets.token_urlsafe(128)
    apihash = f"{apikey[:6]}.{hashlib.sha256(apikey.encode('utf-8')).hexdigest()}"
    
    # Store apihash and additional params into DynamoDB
    response = model_apikey.put_item(apihash, email, enabled, project, agency)

    if response:
        return apikey
    else:
        return "Error generating API key"

@router.get("/verify")
async def verify(credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):

    owner = api_key_auth(credentials.credentials)

    return {
        "data": f"You used a valid API key: {owner}"
    }

@router.delete("/delete")
async def delete(apikey:str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Deletes an API key
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)

    response = model_apikey.delete_item(apikey)
    print(response)
    if response:
        return "API key deleted"
    else:
        return "Error deleting API key"
    
@router.get("/list_by_email")
async def list_by_email(credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Lists all API keys belonging to the calling user
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    email = jwt_sub.get('email')

    response = model_apikey.get_all_key_by_email(email)

    if response:
        return response
    else:
        return "Error retrieving API keys"