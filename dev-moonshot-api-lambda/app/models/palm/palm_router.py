import base64
import json
import datetime
import uuid

from typing import Optional
import traceback
import boto3 as boto3

from fastapi import APIRouter, Security, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, AnyHttpUrl
from fastapi.responses import RedirectResponse
from typing import List, Dict

from app import config
from app.models.palm.palm_text_model import PalmTextModel
from app.models.palm.palm_chat_model import PalmChatModel
from app.utils import llm_util
from app.utils.auth_util import check_token_permission
from app.config import (logger, dynamodb, AWS_REGION_NAME, SNS_SLACK_TOPIC_ARN, DATETIME_MS_FORMAT, DATETIME_MIN_FORMAT, TABLE_MOONSHOT_LLM, 
                        PALM_TEXT_MODEL_DEFAULT, PALM_CHAT_MODEL_DEFAULT, PALM_TEMPERATURE_DEFAULT, PALM_TOP_P_DEFAULT, 
                        PALM_TOP_K_DEFAULT, PALM_MAX_TOKENS_DEFAULT, PALM_USER_DAILY_TOKEN_QUOTA)

# from app.utils.ses_util import compose_gpt_response_email, send_an_email
from app.common.mail_util import compose_ai_response_email, process_email_task, find_and_replace_placeholders

router = APIRouter()
security_http_bearer = HTTPBearer()

model_palm_text = PalmTextModel(dynamodb, TABLE_MOONSHOT_LLM)
model_palm_chat = PalmChatModel(dynamodb, TABLE_MOONSHOT_LLM)

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)


class PalmTextType(BaseModel):
    prompt: str

    class Config:
        schema_extra = {
            "example": {
                "prompt": "Say this is a test",
            }
        }

class PalmChatType(BaseModel):
    messages: List[Dict]
    conversation_id: Optional[str]
    conversation_title: Optional[str]
    pinned: Optional[bool] = False
    temperature: Optional[float] = 0.5

    class Config:
        schema_extra = {
            "example": {
                "messages": [{"author":"user","content":"Say this is a test"},{"author":"bot","content":"This is a test"}],
                "conversation_id": "conv-id",
                "conversation_title": "",
                "pinned": False,
                "temperature": 0.5
            }
        }

@router.post("/text")
async def text(payload: PalmTextType, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Calls PaLM with the prompt and returns the response
    """
    prompt = payload.prompt

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    model=PALM_TEXT_MODEL_DEFAULT
    temperature=PALM_TEMPERATURE_DEFAULT
    top_p=PALM_TOP_P_DEFAULT
    top_k=PALM_TOP_K_DEFAULT
    max_tokens=PALM_MAX_TOKENS_DEFAULT

    palm_response = await llm_util.palm_text(prompt, model, temperature, top_p, top_k, max_tokens)
    print('palm_response:',palm_response)

    if palm_response:
        id = f"text-{uuid.uuid4().hex}"
        response_text = palm_response.text

        # Store records of PaLM usage by storing user, prompt, model and response
        model_palm_text.put_text_response(id, prompt, model, temperature, top_p, top_k, response_text, llm_util.encrypt_identity(caller))

        # Return PaLM response
        return {
            "id": id,
            "prompt": prompt,
            "model": model,
            "response": response_text,
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"PaLM error for prompt: {prompt}",
        )
    
@router.post("/chat")
async def chat(payload: PalmChatType, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Calls PALM with the prompt and returns the response
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
    response = model_palm_chat.list_tokens_used_by_caller(caller=llm_util.encrypt_identity(caller))
    items = response.get('Items')
    print(items)
    if items:
        tokens_consumed = sum([i.get('tokens_used',0) for i in items])
        print('tokens_consumed',tokens_consumed)
        if tokens_consumed >= PALM_USER_DAILY_TOKEN_QUOTA:
            raise HTTPException(
                status_code=429,
                detail=f"Exceeded daily usage quota",
            )

    model=PALM_CHAT_MODEL_DEFAULT #'gpt-4'
    # temperature=0 #GPT_TEMPERATURE_DEFAULT
    max_tokens=PALM_MAX_TOKENS_DEFAULT
    top_p=PALM_TOP_P_DEFAULT
    top_k=PALM_TOP_K_DEFAULT

    # Structure the prompt int

    palm_response = await llm_util.palm_chat(messages, model, temperature, max_tokens, top_p, top_k)
    print(palm_response)

    if palm_response: 
        response_id = f"chat-{uuid.uuid4().hex}"
        response_text = palm_response.text
        tokens_used = 0

        # New conversations will not have conversation_id and conversation_title
        if not conversation_id:
            conversation_id = uuid.uuid4().hex

        if not conversation_title:
            # Generate a conversation title based on the user prompt
            user_prompt = messages[-1]['content']
            conversation_title = user_prompt.title()

            if len(user_prompt) >= 50:
                title_messages = [{"role": "user","content": f"Generate a short title to describe the following query prompt:\n{user_prompt}\n\nTitle:\n"}]
                title_response = await llm_util.palm_chat(messages=title_messages,temperature=0)
                if title_response:
                    conversation_title = title_response.text
                    # strip quotes if title is encapsulated in quotes
                    if conversation_title.startswith('"') and conversation_title.endswith('"'):
                        conversation_title = conversation_title[1:-1]

        # Store records of GPT usage by storing user, messages, model and response
        model_palm_chat.put_chat_response(response_id, conversation_id, conversation_title, messages, model, temperature, response_text, llm_util.encrypt_identity(caller), tokens_used, pinned)

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
            detail=f"PALM error for messages: {messages}",
        )

@router.post("/emailme")
async def emailme(response_id: str, email: str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Emails the chat to the user who called it
    """

    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)

    #TODO check only backend process can call this API

    gpt_response = model_palm_chat.get_item(response_id=response_id)

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
            model_palm_chat.mark_emailed(response_id=response_id)
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

    response = model_palm_chat.get_conversations(llm_util.encrypt_identity(caller))
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

    response = model_palm_chat.hide_conversation(conversation_id)

    return response

@router.post("/pin_conversation")
async def pin_conversation(conversation_id:str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    '''
    Pins all responses with a matching conversation_id
    '''
    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    response = model_palm_chat.pin_conversation(conversation_id)

    return response

@router.post("/unpin_conversation")
async def unpin_conversation(conversation_id:str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    '''
    Unpins all responses with a matching conversation_id
    '''
    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    response = model_palm_chat.unpin_conversation(conversation_id)

    return response