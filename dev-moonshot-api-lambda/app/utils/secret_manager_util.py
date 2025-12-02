import json
import logging

import boto3
from botocore.config import Config

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def get_json_secret_as_dict(secret_name: str, endpoint_url: str = None, boto_config: Config = None) -> dict:
    """Retrieve secret from AWS Secrets Manager.

    :param secret_name: Name of the secret to retrieve.
    :param endpoint_url: VPC endpoint URL to access secret manager
    :param boto_config: Boto3 config
    :returns: The secret converted into Python Dictionary.
    """
    logger.info("Retrieving secret from Secrets Manager")
    secrets_mgr = boto3.client('secretsmanager', endpoint_url=endpoint_url, config=boto_config)
    secret_response = secrets_mgr.get_secret_value(SecretId=secret_name)
    secret = json.loads(secret_response["SecretString"])
    return secret
