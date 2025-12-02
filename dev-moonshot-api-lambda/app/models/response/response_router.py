import base64
import json
import datetime
from typing import Optional
import traceback
import boto3 as boto3

from fastapi import APIRouter, Security, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, AnyHttpUrl
from fastapi.responses import RedirectResponse

from app import config
from app.models.response.response_model import GptResponseModel
from app.utils import llm_util
from app.utils.auth_util import check_token_permission
from app.config import (logger, dynamodb, AWS_REGION_NAME, SNS_SLACK_TOPIC_ARN, DATETIME_MS_FORMAT, TABLE_MOONSHOT_LLM, 
                        GPT_MODEL_DEFAULT, GPT_TEMPERATURE_DEFAULT, GPT_MAX_TOKENS_DEFAULT, 
                        GPT_TOP_P_DEFAULT, GPT_FREQUENCY_PENALTY_DEFAULT, GPT_PRESENSE_PENALTY_DEFAULT, 
                        GPT_USER_DAILY_TOKEN_QUOTA)



router = APIRouter()
security_http_bearer = HTTPBearer()

model_gpt_response = GptResponseModel(dynamodb, TABLE_MOONSHOT_LLM)

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)


class GptPromptType(BaseModel):
    prompt: str

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Say this is a test",
            }
        }


@router.post("/prompt")
async def prompt(payload: GptPromptType, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Calls GPT with the prompt and returns the response
    """
    prompt = payload.prompt

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    # Check if caller has exceeded daily quota
    response = model_gpt_response.list_tokens_used_by_caller(caller=llm_util.encrypt_identity(caller))
    items = response.get('Items')
    print(items)
    if items:
        tokens_consumed = sum([i.get('tokens_used',0) for i in items])
        print('tokens_consumed',tokens_consumed)
        if tokens_consumed >= GPT_USER_DAILY_TOKEN_QUOTA:
            raise HTTPException(
                status_code=429,
                detail=f"Exceeded daily usage quota",
            )

    model=GPT_MODEL_DEFAULT
    temperature=GPT_TEMPERATURE_DEFAULT
    max_tokens=GPT_MAX_TOKENS_DEFAULT
    top_p=GPT_TOP_P_DEFAULT
    frequency_penalty=GPT_FREQUENCY_PENALTY_DEFAULT
    presence_penalty=GPT_PRESENSE_PENALTY_DEFAULT

    gpt_response = await llm_util.gpt_completion(prompt, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
    print(gpt_response)

    if gpt_response: 
        id = gpt_response.get("id")
        model = gpt_response.get("model")
        created = gpt_response.get("created")
        response_text = gpt_response.get("choices")[0]["text"]
        tokens_used = gpt_response.get("usage").get("total_tokens")

        # Store records of GPT usage by storing user, prompt, model and response
        model_gpt_response.put_gpt_response(id, prompt, model, temperature, response_text, llm_util.encrypt_identity(caller), tokens_used, created)

        # Return GPT response
        return {
            "id": id,
            "prompt": prompt,
            "model": model,
            "response": response_text,
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI error for prompt: {prompt}",
        )
    
        
@router.post("/upvote")
async def upvote(response_id: str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Upvote the prompt/response entry based on response_id
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)

    #TODO check only backend process can call this API

    upvote_response = model_gpt_response.upvote_response(response_id=response_id)

    return upvote_response

@router.post("/downvote")
async def downvote(response_id: str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Downvote the prompt/response entry based on response_id
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)

    #TODO check only backend process can call this API

    downvote_response = model_gpt_response.downvote_response(response_id=response_id)

    return downvote_response