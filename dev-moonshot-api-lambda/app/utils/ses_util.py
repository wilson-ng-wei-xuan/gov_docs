import json
import logging
import os
import uuid
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import List, Dict

import boto3

from app.common.mail_task_type import MailTaskType
from app.config import QUEUE_URL_EMAIL_JOBS, AWS_REGION_NAME

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger()

CHARSET = 'utf8'
ADMIN_EMAIL = os.environ.get('EMAIL_ADMIN', 'data@tech.gov.sg')
ADMIN_NAME = os.environ.get('ADMIN_NAME', 'CapDev DSAID')

sqs_client = boto3.client(service_name='sqs', region_name=AWS_REGION_NAME)


def send_raw_email(ses_client, msg: MIMEMultipart, from_email: str, to_emails: List[str], configSetName=None):
    logger.info(
        f"Sending email from {from_email} to {to_emails} using configSet {configSetName}")
    del msg['To']
    msg['To'] = ','.join(to_emails)
    # Provide the contents of the email
    response = ses_client.send_raw_email(
        Source=from_email,
        Destinations=to_emails,
        RawMessage={
            'Data': msg.as_string(),
        },
        ConfigurationSetName=configSetName
    )
    logger.info(f"Email sent: Message ID = {response['MessageId']}")
    return response


def send_emails(ses_client, to_emails: List[str], subject: str, from_email: str,
                message_text: str = None, message_html: str = None):
    try:
        message = {
            'Subject': {
                'Data': subject,
                'Charset': CHARSET
            },
            'Body': {
            }
        }
        if message_text:
            message['Body']['Text'] = {
                'Data': message_text,
                'Charset': CHARSET
            }
        if message_html:
            message['Body']['Html'] = {
                'Charset': CHARSET,
                'Data': message_html,
            }
        resp = ses_client.send_email(
            Source=from_email,
            Destination={
                'ToAddresses': to_emails
            },
            Message=message,
            ReplyToAddresses=[from_email]
        )
        logger.info(resp['MessageId'])
    except Exception as e:
        raise Exception('Error in sending email:', str(e))
    return True


def send_otp_email(otp, email_address, name='welcome', duration='5 minutes', from_address=None):
    # The subject line for the email.
    subject = f'OTP to Whitespace Project - {otp}'

    # The email body for recipients with non-HTML email clients.
    body_text = (f"Hi {name},\r\n"
                 f"Your OTP is {otp} \r\n"
                 f"It will expire in {duration}.")

    # The HTML body of the email.
    body_html = f"""<html>
    <head></head>
    <body>
        <p>Hi {name},</p>
      <h2>Your OTP is {otp}</h2>
      <p>It will expire in {duration}.</p>
    </body>
    </html>
    """

    if from_address is None:
        from_address = formataddr((ADMIN_NAME, ADMIN_EMAIL))

    ses_client = boto3.client('ses')
    send_emails(ses_client, [email_address], subject,
                from_address, body_text, body_html)


def compose_otp_email(to_emails: List,
                      placeholders: Dict,
                      from_email=ADMIN_EMAIL) -> MailTaskType:
    """
    Compose parts for an OTP email
    """
    job = MailTaskType(to_emails=to_emails, from_email=from_email, subject='OTP for {{event}} - {{otp}}')
    job.placeholders = placeholders

    # The email body for recipients with non-HTML email clients.
    job.message_text = """OTP for {{event}}\r\n
    Your OTP is {{otp}} \r\n
    It will expire in {{duration}}.\r\n
    Requested from IP: {{ip}}."""

    # The HTML body of the email.
    job.message_html = """<html>
    <head></head>
    <body>
      <p>OTP for {{event}},</p>
      <br/>
      <p>Your OTP is <h2>{{otp}}</h2></p>
      <p>It will expire in {{duration}}.</p>
      <br/>
      <p>Requested from IP: {{ip}}.</p>
    </body>
    </html>
    """

    logger.info(f'Composed OTP Email: {job}')
    return job

def send_an_email(mail: MailTaskType):
    """
    Send an email using SES directly.
    """
    ses_client = boto3.client('ses')
    send_emails(ses_client, mail.to_emails, mail.subject,
                mail.from_email, mail.message_text, mail.message_html)


def queue_an_email(job: MailTaskType) -> Dict:
    """
    Add an email job to Mail Postman queue for sending.
    """
    # Generate task_group and task_id if not set
    if not job.task_group:
        job.task_group = uuid.uuid1().hex
    if not job.task_id:
        job.task_id = uuid.uuid1().hex

    logger.info(f'Add email job to queue: {job.dict()}')
    sqs_client.send_message(QueueUrl=QUEUE_URL_EMAIL_JOBS,
                            MessageBody=json.dumps(job.dict()),
                            MessageGroupId=uuid.uuid1().hex)

    return job.dict(include={'task_group', 'task_id'})
