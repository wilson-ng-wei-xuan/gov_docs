import boto3
import os

from app.config import AWS_REGION_NAME

AWS_ENDPOINT = os.environ.get('AWS_ENDPOINT', None)


SETTINGS = {
    'region_name': AWS_REGION_NAME,
    'endpoint_url': AWS_ENDPOINT}

s3_client = boto3.client(service_name='s3', **SETTINGS)
sqs_client = boto3.client(service_name='sqs', **SETTINGS)
sns_client = boto3.client(service_name='sns', **SETTINGS)
lambda_client = boto3.client(service_name='lambda', **SETTINGS)
dynamodb = boto3.resource(service_name="dynamodb", **SETTINGS)

s3_resource = boto3.resource(service_name='s3', **SETTINGS)
