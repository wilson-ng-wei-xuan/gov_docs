import base64
import json
import datetime
from uuid import uuid4

from typing import Optional
import traceback
import boto3 as boto3

from fastapi import APIRouter, Security, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, AnyHttpUrl
from fastapi.responses import RedirectResponse

from app import config
from app.models.cohere.cohere_model import CohereGenerationModel
from app.utils import llm_util
from app.utils.auth_util import check_token_permission
from app.config import (logger, dynamodb, AWS_REGION_NAME, SNS_SLACK_TOPIC_ARN, DATETIME_MS_FORMAT, TABLE_MOONSHOT_LLM, 
                        COHERE_MODEL_DEFAULT, COHERE_TEMPERATURE_DEFAULT, COHERE_MAX_TOKENS_DEFAULT)

from app.utils.ses_util import compose_ai_response_email, send_an_email
from app.common.mail_util import find_and_replace_placeholders

router = APIRouter()
security_http_bearer = HTTPBearer()

model_cohere_generation = CohereGenerationModel(dynamodb, TABLE_MOONSHOT_LLM)

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)


class CohereGenerationType(BaseModel):
    prompt: str

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Say this is a test",
            }
        }


@router.post("/generation")
async def generation(payload: CohereGenerationType, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Calls Cohere with the prompt and returns the response
    """
    prompt = payload.prompt

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    model=COHERE_MODEL_DEFAULT
    temperature=COHERE_TEMPERATURE_DEFAULT
    max_tokens=COHERE_MAX_TOKENS_DEFAULT

    cohere_response = await llm_util.cohere_completion(prompt, model, temperature, max_tokens)
    print(cohere_response)

    if cohere_response: 
        try:
            id = cohere_response.generations[0].id
        except AttributeError as e:
            id = str(uuid4())
        response_text = cohere_response.generations[0].text

        # Store records of Cohere usage by storing user, prompt, model and response
        model_cohere_generation.put_generation_response(id, prompt, model, temperature, response_text, llm_util.encrypt_identity(caller))

        # Return Cohere response
        return {
            "id": id,
            "prompt": prompt,
            "model": model,
            "response": response_text,
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Cohere error for prompt: {prompt}",
        )

@router.post("/emailme")
async def emailme(response_id: str, email:str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Emails the prompt and response to the user who called it
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)

    #TODO check only backend process can call this API

    gpt_response = model_cohere_generation.get_item(response_id=response_id)

    if gpt_response:
        response_item = gpt_response.get('Item')

        prompt = response_item['prompt']
        response = response_item['response']
        created = response_item['created']
        created = datetime.datetime.strptime(created, DATETIME_MS_FORMAT) + datetime.timedelta(hours=8)

        # Email OTP
        try:
            placeholders = {'prompt': prompt,
                            'response': response, 'created':created.strftime(DATETIME_MS_FORMAT)}
            job = compose_ai_response_email(to_emails=[email],
                                    placeholders=placeholders)

            # TODO To be replaced by queue_an_email +++++++++++++++++++
            if job.message_html:
                # Fill placeholders, which is surrounded by {{}}, in message_html with values from placeholders
                job.message_html = find_and_replace_placeholders(
                    job.message_html, placeholders)
            if job.message_text:
                job.message_text = find_and_replace_placeholders(
                    job.message_text, placeholders)
            job.subject = find_and_replace_placeholders(
                job.subject, placeholders)
            result = send_an_email(job)
            # TODO +++++++++++++++++++

            logger.info(f'Queued AI Email: {result}')
            model_cohere_generation.mark_emailed(response_id=response_id)
            return {'message': (f'Your AI response has been emailed to you.')}
        except HTTPException as http_ex:
            raise
        except Exception as ex:
            logger.exception(ex)
            error_msg = (
                f"Failed to send adhoc email\n"
                f"Error: {str(ex)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
                            Subject="Mail Postman: Failed to send email",
                            Message=error_msg)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{str(ex)}")
        
@router.post("/upvote")
async def upvote(response_id: str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Upvote the prompt/response entry based on response_id
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)

    #TODO check only backend process can call this API

    upvote_response = model_cohere_generation.upvote_response(response_id=response_id)

    return upvote_response

@router.post("/downvote")
async def downvote(response_id: str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Downvote the prompt/response entry based on response_id
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)

    #TODO check only backend process can call this API

    downvote_response = model_cohere_generation.downvote_response(response_id=response_id)

    return downvote_response
        