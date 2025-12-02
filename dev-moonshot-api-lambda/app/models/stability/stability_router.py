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
from fastapi.responses import StreamingResponse, RedirectResponse

from app import config
from app.common.aws import dynamodb, s3_client
from app.models.stability.stability_model import StabilityGenerationModel
from app.utils import s3_util, img_gen_util, llm_util
from app.utils.auth_util import check_token_permission
from app.config import (logger, dynamodb, AWS_REGION_NAME, SNS_SLACK_TOPIC_ARN, DATETIME_MS_FORMAT, TABLE_MOONSHOT_LLM, BUCKET_GENAI_USERDATA,
                        STABILITY_MODEL_DEFAULT, STABILITY_CFG_SCALE_DEFAULT, STABILITY_STEPS_DEFAULT)

# from app.utils.ses_util import compose_ai_response_email, send_an_email
# from app.common.mail_util import find_and_replace_placeholders
from io import BytesIO
from PIL import Image

router = APIRouter()
security_http_bearer = HTTPBearer()

model_stability_generation = StabilityGenerationModel(dynamodb, TABLE_MOONSHOT_LLM)

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)


class StabilityGenerationType(BaseModel):
    prompt: str
    samples: int = 1
    steps: int = 15
    width: Optional[int] = 512
    height: Optional[int] = 512
    style: Optional[str] = None
    model: Optional[str] = STABILITY_MODEL_DEFAULT
    cfg_scale: Optional[int] = STABILITY_CFG_SCALE_DEFAULT

    class Config:
        schema_extra = {
            "example": {
                "prompt": "A lighthouse on a cliff",
                "samples" : 1,
                "steps" : 15,
                "width" : 512,
                "height" : 512,
                "style" : "enhance"
            }
        }


@router.post("/generation")
async def generation(payload: StabilityGenerationType, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Calls Stability with the prompt and returns the response
    """
    # Get logged in user ID from JWT
    jwt_sub = check_token_permission(credentials.credentials)
    caller = jwt_sub.get('email')

    stability_response = img_gen_util.bedrock_stability_generation(**payload.dict())
    # print("stability_response")
    # print(stability_response)

    if stability_response: 
        id = uuid4().hex

        img_urls = []

        for i in range(len(stability_response["artifacts"])):
            image = stability_response["artifacts"][i]
            filename = f"/tmp/v1_txt2img_{i}.png"
            with open(filename, "wb") as f:
                f.write(base64.b64decode(image["base64"]))
            
            img_id = uuid4().hex
            s3_key = f"stability/{id}-{img_id}.png"

            #save images to S3
            s3_util.upload_file_to_bucket(s3_client,filename,BUCKET_GENAI_USERDATA,s3_key)
            
            img_urls.append(f"https://genai-user-data.launchpad.tech.gov.sg/{s3_key}")

        print(img_urls)

        # Store records of Stability usage by storing user, prompt, model and response
        model_stability_generation.put_generation_response(**payload.dict(), response_id=id, img_urls=img_urls, caller=llm_util.encrypt_identity(caller))

        # Return fastapi streamingresponse
        # gen_image = Image.open(img_urls[0])

        # temp_img = BytesIO()
        # gen_image.save(temp_img, "PNG")
        # temp_img.seek(0)

        # return StreamingResponse(temp_img, media_type="image/png")
    
        return img_urls

        
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Stability error for prompt: {payload.prompt}",
        )

# @router.post("/emailme")
# async def emailme(response_id: str, email:str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
#     """
#     Emails the prompt and response to the user who called it
#     """

#     # Get logged in user ID from JWT
#     jwt_sub = check_token_permission(credentials.credentials)

#     #TODO check only backend process can call this API

#     gpt_response = model_stability_generation.get_item(response_id=response_id)

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
#             model_stability_generation.mark_emailed(response_id=response_id)
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

#     upvote_response = model_stability_generation.upvote_response(response_id=response_id)

#     return upvote_response

# @router.post("/downvote")
# async def downvote(response_id: str, credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
#     """
#     Downvote the prompt/response entry based on response_id
#     """

#     # Get logged in user ID from JWT
#     jwt_sub = check_token_permission(credentials.credentials)

#     #TODO check only backend process can call this API

#     downvote_response = model_stability_generation.downvote_response(response_id=response_id)

#     return downvote_response
        