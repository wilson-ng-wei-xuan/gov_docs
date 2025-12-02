import base64
import json, os
from uuid import uuid4
import datetime
from decimal import Decimal
from typing import Optional
import traceback
import boto3 as boto3

from fastapi import APIRouter, Security, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import List, Dict
from fastapi.responses import RedirectResponse

from app import config
from app.models.gpt.gpt_model import GptChatModel
from app.utils import llm_util
from app.utils.auth_util import check_token_permission
from app.config import (logger, dynamodb, AWS_REGION_NAME, SNS_SLACK_TOPIC_ARN, DATETIME_MS_FORMAT, DATETIME_MIN_FORMAT, TABLE_MOONSHOT_LLM, 
                        GPT_CHAT_MODEL_DEFAULT, GPT_TEMPERATURE_DEFAULT, GPT_MAX_TOKENS_DEFAULT,
                        GPT_FREQUENCY_PENALTY_DEFAULT, GPT_PRESENSE_PENALTY_DEFAULT, GPT_TOP_P_DEFAULT,
                        GPT_USER_DAILY_TOKEN_QUOTA)

from app.common.mail_util import compose_ai_response_email, process_email_task, find_and_replace_placeholders

router = APIRouter()
security_http_bearer = HTTPBearer()

model_gpt_chat = GptChatModel(dynamodb, TABLE_MOONSHOT_LLM)

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)


class GptChatType(BaseModel):
    messages: List[Dict]
    conversation_id: Optional[str]
    conversation_title: Optional[str]
    pinned: Optional[bool] = False
    temperature: Optional[float] = 0.5

    class Config:
        schema_extra = {
            "example": {
                "messages": [{"role":"user","content":"Say this is a test"}],
                "conversation_id": "conv-id",
                "conversation_title": "",
                "pinned": False,
                "temperature": 0.5
            }
        }


@router.post("/chat")
async def chat(payload: GptChatType, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Calls GPT with the prompt and returns the response
    """
    messages = payload.messages
    conversation_id = payload.conversation_id
    conversation_title = payload.conversation_title
    temperature = payload.temperature
    pinned = payload.pinned

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    # Check if caller has exceeded daily quota
    response = model_gpt_chat.list_tokens_used_by_caller(caller=llm_util.encrypt_identity(caller))
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

    model=GPT_CHAT_MODEL_DEFAULT #'gpt-4'
    # temperature=0 #GPT_TEMPERATURE_DEFAULT
    max_tokens=GPT_MAX_TOKENS_DEFAULT
    top_p=GPT_TOP_P_DEFAULT
    frequency_penalty=GPT_FREQUENCY_PENALTY_DEFAULT
    presence_penalty=GPT_PRESENSE_PENALTY_DEFAULT

    # Structure the prompt int

    gpt_response = await llm_util.gpt_chat_completion(messages, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
    print(gpt_response)

    if gpt_response: 
        response_id = gpt_response.get("id")
        model = gpt_response.get("model")
        # created = gpt_response.get("created")
        response_text = gpt_response.get("choices")[0]["message"]
        tokens_used = gpt_response.get("usage").get("total_tokens")

        # New conversations will not have conversation_id and conversation_title
        if not conversation_id:
            conversation_id = str(uuid4())

        if not conversation_title:
            # Generate a conversation title based on the user prompt
            user_prompt = messages[-1]['content']
            conversation_title = user_prompt.title()

            if len(user_prompt) >= 50:
                title_messages = [{"role": "user","content": f"Generate a short title to describe the following query prompt:\n{user_prompt}\n\nTitle:\n"}]
                title_response = await llm_util.gpt_chat_completion(messages=title_messages,temperature=0)
                if title_response:
                    conversation_title = title_response.get("choices")[0]["message"]['content']
                    # strip quotes if title is encapsulated in quotes
                    if conversation_title.startswith('"') and conversation_title.endswith('"'):
                        conversation_title = conversation_title[1:-1]

        # Store records of GPT usage by storing user, messages, model and response
        model_gpt_chat.put_chat_response(response_id, conversation_id, conversation_title, messages, model, temperature, response_text, llm_util.encrypt_identity(caller), tokens_used, pinned)

        # Return GPT response
        return {
            "id": response_id,
            "conversation_id": conversation_id,
            "conversation_title": conversation_title,
            "messages": messages,
            "model": model,
            "response": response_text,
            "pinned": pinned
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI error for messages: {messages}",
        )

@router.post("/emailme")
async def emailme(response_id: str, email: str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Emails the chat to the user who called it
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)

    #TODO check only backend process can call this API

    gpt_response = model_gpt_chat.get_item(response_id=response_id)

    if gpt_response:
        response_item = gpt_response.get('Item')

        messages = response_item['messages']
        response = response_item['response']
        created = response_item['created']
        try:
            created = datetime.datetime.strptime(created, DATETIME_MS_FORMAT) + datetime.timedelta(hours=8)
        except:
            created = datetime.datetime.now()

        chat_history = ""
        # messages is a list of dict {"role":"assistant","content":"prompt text"}
        for msg in messages:
            if msg['role'] == 'user':
                chat_history += f"You:\n{msg['content']}\n\n"
            elif msg['role'] == 'assistant':
                chat_history += f"AI Assistant:\n{msg['content']}\n\n"

        # Email conversation
        try:
            placeholders = {'prompt': chat_history, 'messages':messages,
                            'response': response['content'], 'created':created.strftime(DATETIME_MIN_FORMAT)}
            job = compose_ai_response_email(to_email=email,
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
            # result = send_an_email(job)
            # TODO +++++++++++++++++++

            result = process_email_task(job,"mail-postman-config")

            logger.info(f'Queued AI Email: {result}')
            model_gpt_chat.mark_emailed(response_id=response_id)
            return {'message': (f'Your AI conversation has been emailed to you.')}
        except HTTPException as http_ex:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{str(http_ex)}")
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
        
@router.post("/conversation_history")
async def conversation_history(limit:int=10, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Returns a list of past conversations with chatGPT, based on user identity
    """
    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    response = model_gpt_chat.get_conversations(llm_util.encrypt_identity(caller))
    conversations = response.get("Items",[])

    # print(conversations)

    if conversations:
        unique_conversations = []
        result = []

        # Pick out only the lastest entry for each conversation to return (list is reverse sorted by created)
        for conv in conversations:
            # print(f"{unique_conversations=}")
            if conv['conversation_id'] not in unique_conversations:
                unique_conversations.append(conv['conversation_id'])
                conv['messages'].append(conv['response'])
                del conv['response']
                result.append(conv)

        conversations = result[:limit]

    return {
        "conversations":conversations
    }

@router.post("/hide_conversation")
async def hide_conversation(conversation_id:str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    '''
    Hides all the responses with a matching conversation_id
    '''
    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    response = model_gpt_chat.hide_conversation(conversation_id)

    return response

@router.post("/pin_conversation")
async def pin_conversation(conversation_id:str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    '''
    Pins all responses with a matching conversation_id
    '''
    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    response = model_gpt_chat.pin_conversation(conversation_id)

    return response

@router.post("/unpin_conversation")
async def unpin_conversation(conversation_id:str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    '''
    Unpins all responses with a matching conversation_id
    '''
    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    response = model_gpt_chat.unpin_conversation(conversation_id)

    return response