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
from typing import List, Dict
from fastapi.responses import RedirectResponse

from app import config
# from app.models.lightgpt.lightgpt_model import LightGPTGenerationModel
from app.utils import llm_util
from app.utils.auth_util import check_token_permission
from app.config import (logger, dynamodb, AWS_REGION_NAME, SNS_SLACK_TOPIC_ARN, DATETIME_MS_FORMAT, TABLE_MOONSHOT_LLM)

from app.common.mail_util import compose_ai_response_email, process_email_task, find_and_replace_placeholders

router = APIRouter()
security_http_bearer = HTTPBearer()

# model_lightgpt_generation = LightGPTGenerationModel(dynamodb, TABLE_MOONSHOT_LLM)

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)


class LightGPTGenerationType(BaseModel):
    prompt: str

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Say this is a test",
            }
        }

class LightGPTChatType(BaseModel):
    messages: List[Dict]

    class Config:
        schema_extra = {
            "example": {
                "messages": [{"role":"user","content":"I have a dream"},
                             {"role":"assistant","content":"What is the dream about?"},
                             {"role":"user","content":"Make a guess"},],
            }
        }

@router.post("/lightgpt_chat")
async def lightgpt_chat(payload: LightGPTChatType):
    """
    Calls LightGPT with the prompt and returns the response
    """
    messages = payload.messages

    # Get logged in user ID from JWT
    # jwt_sub = check_token_permission(credentials.credentials)
    # caller = jwt_sub.get('email')

    temperature=0.5
    max_tokens=200

    lightgpt_response = await llm_util.lightgpt_chat(messages, temperature, max_tokens)
    print(lightgpt_response)

    if lightgpt_response:
        # Generate a unique ID for this response
        id = str(uuid4())

        response_text = lightgpt_response

        # Store records of lightgpt usage by storing user, prompt, model and response
        # model_lightgpt_generation.put_generation_response(id, prompt, model, temperature, response_text, llm_util.encrypt_identity(caller))

        # Return lightgpt response
        return {
            "id": id,
            "messages": messages,
            "response": response_text,
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"lightgpt error for messages: {messages}",
        )
    
# @router.post("/emailme")
# async def emailme(response_id: str, email:str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
#     """
#     Emails the prompt and response to the user who called it
#     """

#     # Get logged in user ID from JWT
#     jwt_sub = check_token_permission(credentials.credentials)

#     #TODO check only backend process can call this API

#     gpt_response = model_lightgpt_generation.get_item(response_id=response_id)

#     if gpt_response:
#         response_item = gpt_response.get('Item')

#         prompt = response_item['prompt']
#         response = response_item['response']
#         created = response_item['created']
#         created = datetime.datetime.strptime(created, DATETIME_MS_FORMAT) + datetime.timedelta(hours=8)

#         # Email OTP
#         try:
#             placeholders = {'prompt': prompt,
#                             'response': response, 'created':created.strftime(DATETIME_MS_FORMAT)}
#             job = compose_ai_response_email(to_emails=[email],
#                                     placeholders=placeholders)

#             # TODO To be replaced by queue_an_email +++++++++++++++++++
#             if job.message_html:
#                 # Fill placeholders, which is surrounded by {{}}, in message_html with values from placeholders
#                 job.message_html = find_and_replace_placeholders(
#                     job.message_html, placeholders)
#             if job.message_text:
#                 job.message_text = find_and_replace_placeholders(
#                     job.message_text, placeholders)
#             job.subject = find_and_replace_placeholders(
#                 job.subject, placeholders)
#             result = send_an_email(job)
#             # TODO +++++++++++++++++++

#             logger.info(f'Queued AI Email: {result}')
#             model_lightgpt_generation.mark_emailed(response_id=response_id)
#             return {'message': (f'Your AI response has been emailed to you.')}
#         except HTTPException as http_ex:
#             raise
#         except Exception as ex:
#             logger.exception(ex)
#             error_msg = (
#                 f"Failed to send adhoc email\n"
#                 f"Error: {str(ex)}\n"
#                 f"Traceback: {traceback.format_exc()}"
#             )
#             sns_client.publish(TopicArn=SNS_SLACK_TOPIC_ARN,
#                             Subject="Mail Postman: Failed to send email",
#                             Message=error_msg)
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                                 detail=f"{str(ex)}")
        
# @router.post("/upvote")
# async def upvote(response_id: str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
#     """
#     Upvote the prompt/response entry based on response_id
#     """

#     # Get logged in user ID from JWT
#     jwt_sub = check_token_permission(credentials.credentials)

#     #TODO check only backend process can call this API

#     upvote_response = model_lightgpt_generation.upvote_response(response_id=response_id)

#     return upvote_response

# @router.post("/downvote")
# async def downvote(response_id: str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
#     """
#     Downvote the prompt/response entry based on response_id
#     """

#     # Get logged in user ID from JWT
#     jwt_sub = check_token_permission(credentials.credentials)

#     #TODO check only backend process can call this API

#     downvote_response = model_lightgpt_generation.downvote_response(response_id=response_id)

#     return downvote_response
        