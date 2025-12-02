import datetime
import traceback

import boto3 as boto3
from fastapi import APIRouter, HTTPException, Security, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.auth_types import EmailOtpType, EmailType
from app.common.mail_util import find_and_replace_placeholders
from app.common.otp_model import OtpModel
from app.config import (JWT_VALID_HOURS, OTP_VALID_MINUTES,
                        TABLE_LAUNCHPAD_OTP, dynamodb, AWS_REGION_NAME, logger, SNS_SLACK_TOPIC_ARN,
                        DATETIME_MS_FORMAT)
from app.utils.auth_util import (JWT_SECRET, decode_jwt_token, gen_jwt_token,
                                 gen_otp)
from app.utils.ses_util import compose_otp_email, queue_an_email, send_an_email

router = APIRouter()
security_http_bearer = HTTPBearer()

model_otp = OtpModel(dynamodb, TABLE_LAUNCHPAD_OTP)

sns_client = boto3.client(service_name='sns', region_name=AWS_REGION_NAME)


@router.post('/email_otp', summary="Request for an OTP through email")
async def email_otp(payload: EmailType, request: Request):
    """
    Request for an OTP to be sent to an email. Requires a valid API Key.
    """
    email = payload.email
    if payload.ip:
        requester_ip = payload.ip
    else:
        requester_ip = request.client.host

    if payload.app:
        requester_app = payload.app
    else:
        requester_app = 'moonshot'
    event_title = requester_app.capitalize() + ' Login'
    
    logger.info(f"/email_otp: {email} from {requester_app}@{requester_ip}")

    # Generate OTP and save into database
    # Unused OTP records will auto-delete (using TTL attribute) once OTP expires
    response = None
    otp = '0123'
    while not response or response.get('HTTPStatusCode') == 403:
        otp_expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_VALID_MINUTES)

        otp = gen_otp()
        response = model_otp.put_item(email=email, otp=otp,
                                       others={"otp_expire": otp_expire.strftime(DATETIME_MS_FORMAT),
                                       "self_destruct_at": int(otp_expire.timestamp()),
                                       "requester_ip": requester_ip, "requester_app": requester_app})

    if response.get('HTTPStatusCode') != 200:
        logger.error(f'Failed to save data into database. {response}')
        raise HTTPException(status_code=response, detail=str(response))

    # Email OTP
    try:
        placeholders = {'otp': otp, 'event': event_title,
                        'duration': f"{OTP_VALID_MINUTES} minutes",'ip':requester_ip}
        job = compose_otp_email(to_emails=[email],
                                placeholders=placeholders)

        # TODO Queue an email +++++++++++++++++++
        # result = queue_an_email(job)
        # TODO +++++++++++++++++++

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

        logger.info(f'Queued OTP Email: {result}')

        return {
            'message': (f'An OTP has been emailed to you. '
                        f'You should receive it in 3 minutes. '
                        f'The token will be valid for {OTP_VALID_MINUTES} minutes.')}
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


@router.post('/get_jwt_token', summary="Generate a JWT token with email and OTP.")
async def get_jwt_token(payload: EmailOtpType):
    """
    Request for a JWT token. Requires a valid API key. The role in API key will be included in JWT data.
    """
    email, otp = payload.email, payload.otp

    # Find record matches either emails or emp_nums
    response = model_otp.get_item(email, otp)
    user = response.get('Item', None)

    if user is None or user.get('otp', None) != otp:
        raise HTTPException(status_code=401, detail="Invalid Email or OTP")

    # OTP should not expire
    otp_expire = user.get('otp_expire', None)
    if otp_expire:
        dt = datetime.datetime.strptime(otp_expire, DATETIME_MS_FORMAT)
        if dt < datetime.datetime.utcnow():
            raise HTTPException(status_code=401, detail="OTP has expired")

    # Generate JWT which contains user's permissions
    jwt_data = {
        'email': user.get('email'),
        'role': user.get('role', 'public'),
        'permissions': user.get('permissions', []),
        'name': user.get('name', '')
    }
    jwt_token = gen_jwt_token(jwt_data, JWT_SECRET)

    # Extend TTL self-destruct expiry time based on JWT validity duration
    self_destruct = datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_VALID_HOURS)

    # Update/Insert JWT into database
    model_otp.update_item(email=email, otp=otp, attributes={'jwt': str(jwt_token),
                                                "self_destruct_at": int(self_destruct.timestamp())})

    return {'jwt': jwt_token, **jwt_data, 'expires_in': f'{JWT_VALID_HOURS} hours'}


@router.get('/decode_jwt', summary="Decode a JWT token")
async def decode_jwt(credentials: HTTPAuthorizationCredentials = Security(security_http_bearer)):
    """
    Check validity of a JWT token in the Bearer. Returns the decoded data.
    """
    jwt = credentials.credentials
    jwt_sub = decode_jwt_token(jwt)
    return jwt_sub
