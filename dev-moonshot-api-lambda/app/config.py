import logging
import os

import boto3
from dotenv import find_dotenv, load_dotenv

from botocore.config import Config as BotoConfig

# Boto3 configuration
boto_config = BotoConfig(
    region_name="ap-southeast-1",
    connect_timeout=3,
    retries={"max_attempts": 3, "mode": "standard"},
)

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger()

load_dotenv(find_dotenv())

AWS_ACCOUNT_ID = boto3.client('sts').get_caller_identity().get('Account')
AWS_REGION_NAME = boto3.session.Session().region_name
LOCAL_FOLDER = '/tmp'
# FOR DEBUGGING
# LOCAL_FOLDER = 'D:/tmp'

# Security
OTP_VALID_MINUTES = 10
JWT_VALID_HOURS = 24 * 31

# DynamoDB
DYNAMO_SETTINGS = {
    # FOR DEBUGGING
    # "endpoint_url": r'http://localhost:8000/',
    "region_name": AWS_REGION_NAME
}
dynamodb = boto3.resource("dynamodb", **DYNAMO_SETTINGS)

TABLE_MOONSHOT_LLM = os.environ.get('TABLE_MOONSHOT_LLM', '')
TABLE_MOONSHOT_APIKEY = os.environ.get('TABLE_MOONSHOT_APIKEY', '')
TABLE_LAUNCHPAD_OTP = os.environ.get('TABLE_LAUNCHPAD_OTP', '')

BUCKET_GENAI_USERDATA = os.environ.get('BUCKET_GENAI_USERDATA', '')

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATETIME_MS_FORMAT = '%Y-%m-%dT%H:%M:%S'
DATETIME_TZ_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
DATETIME_MIN_FORMAT = '%Y-%m-%dT%H:%M'
DATETIME_MIN_TZ_FORMAT = '%Y-%m-%dT%H:%M%z'

# Load Environment Variables
APP_CODE = os.environ['APP_CODE']

# Postman
EMAIL_ADMIN = os.environ.get('EMAIL_ADMIN', 'data@tech.gov.sg')
QUEUE_EMAIL_JOBS = os.environ['QUEUE_EMAIL_JOBS']
QUEUE_URL_EMAIL_JOBS = f'https://sqs.{AWS_REGION_NAME}.amazonaws.com/{AWS_ACCOUNT_ID}/{QUEUE_EMAIL_JOBS}'
LAMBDA_POSTMAN_SEND_EMAIL = os.environ.get('LAMBDA_POSTMAN_SEND_EMAIL', '')

# For developers' alerts
SNS_SLACK_TOPIC_ARN = os.environ.get('SNS_SLACK_TOPIC_ARN', '')

FIELD_DELIMITOR = ";"
VALUE_DELIMITOR = ","

# Name of the secret in Secret Manager
OPENAI_API_SECRET = "OPENAI_API_KEY"
AIPF_API_SECRET = "AIPF_API_KEY"
COHERE_API_SECRET = "COHERE_API_KEY"
GOOGLE_API_SECRET = "GOOGLE_API_KEY"
STABILITY_API_SECRET = "STABILITY_API_KEY"
LLMSTACK_API_SECRET = "LLMSTACK_API_KEY"

# OpenAI ref: https://platform.openai.com/docs/api-reference/completions/create
GPT_MODEL_DEFAULT = 'moonshot-launchpad-chatgpt' #"text-davinci-003"  # https://platform.openai.com/docs/models/gpt-3
GPT_CHAT_MODEL_DEFAULT = os.environ.get('GPT_CHAT_MODEL_DEFAULT', 'moonshot-launchpad-chatgpt') #'moonshot-launchpad-chatgpt' #'gpt-3.5-turbo'
GPT_TEMPERATURE_DEFAULT = 0.7 # 0=> lowest creativity, 1=> most creative
GPT_MAX_TOKENS_DEFAULT = 4000 # most models max of 2048, text-davinci-003 max 4096
GPT_TOP_P_DEFAULT = 0.95
GPT_FREQUENCY_PENALTY_DEFAULT = 0.0
GPT_PRESENSE_PENALTY_DEFAULT = 0.0
GPT_USER_DAILY_TOKEN_QUOTA = int(os.environ.get('GPT_USER_DAILY_TOKEN_QUOTA', 50000))

# Cohere.ai ref https://docs.cohere.ai/reference/generate
COHERE_MODEL_DEFAULT = "command-xlarge-nightly"
COHERE_TEMPERATURE_DEFAULT = 0.75 # 0=> lowest creativity, 5.0=> most creative
COHERE_MAX_TOKENS_DEFAULT = 512 # https://docs.cohere.ai/docs/tokens

# PaLM ref: https://console.cloud.google.com/vertex-ai/publishers/google/model-garden/chat-bison
PALM_TEXT_MODEL_DEFAULT = "text-bison@001"
PALM_CHAT_MODEL_DEFAULT = "chat-bison@001"
PALM_TEMPERATURE_DEFAULT = 0.2
PALM_MAX_TOKENS_DEFAULT = 1024
PALM_TOP_P_DEFAULT = 0.8
PALM_TOP_K_DEFAULT = 40
PALM_USER_DAILY_TOKEN_QUOTA = int(os.environ.get('PALM_USER_DAILY_TOKEN_QUOTA', 50000))

STABILITY_MODEL_DEFAULT = "stable-diffusion-v1-5"
STABILITY_CFG_SCALE_DEFAULT = 7
STABILITY_STEPS_DEFAULT = 15