import logging

import boto3

from app import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

sns_client = boto3.client('sns', region_name=config.AWS_REGION_NAME)


def send_sms(phones, subject, message, sender_id='WhoAmI'):
    """
    Send SMS
    """
    sns_client.set_sms_attributes(
        attributes={
            'DefaultSenderID': sender_id
        }
    )
    for phone in phones:
        if not phone.startswith('+'):
            phone = '+65' + phone
        # print(phone)

        try:
            sns_client.publish(
                PhoneNumber=phone,
                Message=message,
                Subject=subject
            )
        except Exception as ex:
            print(f'Failed to send SMS to {phone}: {str(ex)}')


def slack_developer(subject: str, message: str, sns_client=None, topic_arn: str = None):
    """
    Publish a message to a SNS topic, which will be posted to a slack channel.
    """
    try:
        if topic_arn is None:
            topic_arn = config.SNS_SLACK_TOPIC_ARN
        if sns_client is None:
            sns_client = boto3.client(service_name='sns')
        sns_client.publish(TopicArn=topic_arn,
                           Subject=subject,
                           Message=message)
    except Exception as ex:
        logger.exception(f'Failed to slack developer: {str(ex)}')
