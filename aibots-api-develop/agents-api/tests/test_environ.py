import os
import secrets
from unittest.mock import Mock

import pytest
from atlas.asgi.constants import DEFAULT_ATLAS_MESSAGES
from pydantic import AnyUrl

from aibots.constants import (
    DEFAULT_LLM_MODEL_ID,
    DEFAULT_SYSTEM_PROMPT_TEMPLATE,
    DEFAULT_SYSTEM_PROMPT_VARIABLES
)
from agents.constants import DEFAULT_APP_MESSAGES
from agents.environ import AIBotsAgentEnviron


@pytest.fixture()
def jwt_token():
    return "567f8a512476b9ed8d673f6b6d25164a"


@pytest.fixture()
def mock_secrets(monkeypatch, jwt_token):
    mock = Mock(return_value=jwt_token)
    monkeypatch.setattr(secrets, "token_hex", mock)


@pytest.fixture()
def mock_environ():
    os.environ["EMAIL_SEND__BUCKET"] = "s3-sitez-sharedsvc-471112510129-email"
    os.environ["HOST"] = "0.0.0.0"
    os.environ["PROJECT__SECRET"] = "secret-sitezapp-aibots-main-api"
    os.environ["PROJECT_DB__SECRET"] = "secret-sitezdb-aibots-main"
    os.environ["CLOUDFRONT__PARAM"] = "param-sitezingress-aibots-cloudfront-publickey"
    os.environ["ANALYTICS__PATH"] = "aibots/"
    os.environ["LLMSTACK__PARAM"] = "param-sitez-aibots-llmstack"
    os.environ["USE_SSL"] = "1"
    os.environ["EMAIL_SEND__PTE_URL"] = "https://email.internal.sit.aibots.gov.sg/send"
    os.environ["SUPERUSERS"] = "[\"louisa_ong@tech.gov.sg\",\"david_tw_lee@tech.gov.sg\",\"Leon_lim@tech.gov.sg\",\"vincent_ng@tech.gov.sg\",\"kieu_quoc_thang@tech.gov.sg\",\"wilson_ng@tech.gov.sg\",\"Glenn_goh@tech.gov.sg\",\"Alex_ng@tech.gov.sg\",\"chadin_anuwattanaporn@tech.gov.sg\",\"Yeo_yong_kiat@tech.gov.sg\",\"Steven_koh@tech.gov.sg\"]"
    os.environ["PROJECT_API__PTE_URL"] = "https://api.internal.sit.aibots.gov.sg"
    os.environ["AWS_ID"] = "471112510129"
    os.environ["PROJECT__BUCKET"] = "s3-sitezapp-aibots-471112510129-project"
    os.environ["AWS_REGION"] = "ap-southeast-1"
    os.environ["GOVTEXT__PARAM"] = "param-sitez-aibots-govtext"
    os.environ["PORT"] = "443"
    os.environ["EMAIL_SEND__PATH"] = "aibots/"
    os.environ["DEBUG"] = "0"
    os.environ["CLOUDFRONT__BUCKET"] = "s3-sitezingress-aibots-471112510129-cloudfront"
    os.environ["EMAIL_SEND__SECRET"] = "secret-sitezapp-aibots-smtp-user-no-reply"
    os.environ["CLOUDFRONT__SECRET"] = "secret-sitezingress-aibots-cloudfront"
    os.environ["PROJECT__PUB_URL"] = "https://sit.aibots.gov.sg"
    os.environ["ANALYTICS__BUCKET"] = "s3-sitez-sharedsvc-471112510129-analytics"
    os.environ["NOUS_API__PTE_URL"] = "https://nous-api.internal.sit.aibots.gov.sg"
    os.environ["PROJECT_API__PUB_URL"] = "https://api.sit.aibots.gov.sg"
    os.environ["CLOUDFRONT__PUB_URL"] = "https://public.sit.aibots.gov.sg"
    os.environ["COMPONENT"] = "aibots-main-api"
    os.environ["GOVTEXT__BUCKET"] = "s3-sitez-sharedsvc-471112510129-scheduler"

    yield os.environ

    for i in [
        'EMAIL_SEND__BUCKET',
        'HOST',
        'PROJECT__SECRET',
        'PROJECT_DB__SECRET',
        'CLOUDFRONT__PARAM',
        'ANALYTICS__PATH',
        'LLMSTACK__PARAM',
        'USE_SSL',
        'EMAIL_SEND__PTE_URL',
        'SUPERUSERS',
        'PROJECT_API__PTE_URL',
        'AWS_ID',
        'PROJECT__BUCKET',
        'AWS_REGION',
        'GOVTEXT__PARAM',
        'PORT',
        'EMAIL_SEND__PATH',
        'DEBUG',
        'CLOUDFRONT__BUCKET',
        'EMAIL_SEND__SECRET',
        'CLOUDFRONT__SECRET',
        'PROJECT__PUB_URL',
        'ANALYTICS__BUCKET',
        'NOUS_API__PTE_URL',
        'PROJECT_API__PUB_URL',
        'CLOUDFRONT__PUB_URL',
        'COMPONENT',
        'GOVTEXT__BUCKET',

    ]:
        del os.environ[i]


class TestAIBotsAgentsEnviron:
    def test_aibots_agents_environ_loading_default_env_vars(
            self, mock_secrets, jwt_token
    ):
        environ = AIBotsAgentEnviron()
        assert environ.model_dump() == {
            "access_log": True,
            "analytics": None,
            "aws_access_id": None,
            "aws_endpoint_url": None,
            "aws_id": "1400465454",
            "aws_region": "ap-southeast-1",
            "aws_secret_key": None,
            "aws_session_token": None,
            "cdn_cert": None,
            "cloudfront": None,
            "component": "aibots",
            "db_password": None,
            "db_port": None,
            "db_tls": True,
            "db_url": None,
            "db_user": None,
            "debug": False,
            "email": {
                "sender": "no-reply@sit.aibots.gov.sg",
                "subject": "One-Time Password (OTP) for ${product}",
                "bcc": [],
                "cc": [],
                "reply_to": [],
                "text": "Your OTP is ${otp} \r\n"
                        "\n"
                        "It will expire in ${duration}.\r\n"
                        "\n"
                        "If your OTP does not work, please request for a new\n"
                        "OTP at ${domain}.\r\n"
                        "\n"
                        "AIBots Support Team\n",
                "to": [],
                "encoding": "UTF-8",
                "html": "<html>\n"
                        "<head></head>\n"
                        "<body>\n"
                        "  <h4>Your OTP is: <b>${otp}</b></h4>\n"
                        "  <p>This will expire in ${duration}.</p>\n"
                        "  <p></p>\n"
                        "  <p>If your OTP does not work, please request for a new \n"
                        "  OTP at ${domain}.</p>\n"
                        "  <p></p>\n"
                        "  <p>AIBots Support Team</p>\n"
                        "</body>\n"
                        "</html>\n",
                "name": "The AIBots Team",
            },
            "emails_api": None,
            "expiry": {"api_key": 365.0, "jwt": 2.0, "otp": 10.0},
            'govtext': None,
            "host": "127.0.0.1",
            "issuer": "GovTech",
            "jwt": jwt_token,
            "llm_defaults": {
                "model": DEFAULT_LLM_MODEL_ID,
                "params": {},
                "properties": {},
                "system_prompt": {
                    "placeholders": [
                        "personality",
                        "instructions",
                        "guardrails",
                        "knowledgeBase",
                    ],
                    "template": DEFAULT_SYSTEM_PROMPT_TEMPLATE,
                    "variables": {
                        **DEFAULT_SYSTEM_PROMPT_VARIABLES,
                    },
                },
            },
            'llmstack': None,
            "logging_level": 20,
            "messages": {
                "atlas": DEFAULT_ATLAS_MESSAGES,
                **DEFAULT_APP_MESSAGES
            },
            "nous_api": None,
            "port": 443,
            "project": None,
            'project_api': None,
            "project_db": None,
            "pub_url": None,
            "ssl_certfile": "localhost.crt",
            "ssl_keyfile": "localhost.pem",
            "superusers": [],
            "timezone": "Singapore",
            "url": None,
            "use_aws": True,
            "use_ssl": True,
            "users": [],
        }

    def test_aibots_agents_environ_loading_infra_aligned_env_vars(
            self, mock_secrets, mock_environ, jwt_token
    ):
        environ = AIBotsAgentEnviron()
        assert environ.model_dump() == {
            "access_log": True,
            "analytics": {
                "bucket": "s3-sitez-sharedsvc-471112510129-analytics",
                "path": "aibots/",
            },
            "aws_access_id": None,
            "aws_endpoint_url": None,
            "aws_id": "471112510129",
            "aws_region": "ap-southeast-1",
            "aws_secret_key": None,
            "aws_session_token": None,
            "cdn_cert": None,
            "cloudfront": {
                "auth": None,
                "bucket": "s3-sitezingress-aibots-471112510129-cloudfront",
                "param": "param-sitezingress-aibots-cloudfront-publickey",
                "path": None,
                "pub_url": AnyUrl("https://public.sit.aibots.gov.sg/"),
                "secret": "secret-sitezingress-aibots-cloudfront",
                "url": None,
            },
            "component": "aibots-main-api",
            "db_password": None,
            "db_port": None,
            "db_tls": True,
            "db_url": None,
            "db_user": None,
            "debug": False,
            "email": {
                "sender": "no-reply@sit.aibots.gov.sg",
                "subject": "One-Time Password (OTP) for ${product}",
                "bcc": [],
                "cc": [],
                "reply_to": [],
                "text": "Your OTP is ${otp} \r\n"
                        "\n"
                        "It will expire in ${duration}.\r\n"
                        "\n"
                        "If your OTP does not work, please request for a new\n"
                        "OTP at ${domain}.\r\n"
                        "\n"
                        "AIBots Support Team\n",
                "to": [],
                "encoding": "UTF-8",
                "html": "<html>\n"
                        "<head></head>\n"
                        "<body>\n"
                        "  <h4>Your OTP is: <b>${otp}</b></h4>\n"
                        "  <p>This will expire in ${duration}.</p>\n"
                        "  <p></p>\n"
                        "  <p>If your OTP does not work, please request for a new \n"
                        "  OTP at ${domain}.</p>\n"
                        "  <p></p>\n"
                        "  <p>AIBots Support Team</p>\n"
                        "</body>\n"
                        "</html>\n",
                "name": "The AIBots Team",
            },
            "emails_api": {
                "pub_url": None,
                "url": AnyUrl(
                    "https://email.internal.sit.aibots.gov.sg/send"
                ),
                "auth": None,
                "bucket": "s3-sitez-sharedsvc-471112510129-email",
                "secret": "secret-sitezapp-aibots-smtp-user-no-reply",
                "path": "aibots/",
                "param": None,
            },
            "expiry": {"api_key": 365.0, "jwt": 2.0, "otp": 10.0},
            "host": "0.0.0.0",
            'govtext': {
                "pub_url": None,
                "url": None,
                "auth": None,
                'bucket': 's3-sitez-sharedsvc-471112510129-scheduler',
                'param': 'param-sitez-aibots-govtext',
                "secret": None,
                "path": None,
            },
            "issuer": "GovTech",
            "jwt": jwt_token,
            "llm_defaults": {
                "model": DEFAULT_LLM_MODEL_ID,
                "params": {},
                "properties": {},
                "system_prompt": {
                    "placeholders": [
                        "personality",
                        "instructions",
                        "guardrails",
                        "knowledgeBase",
                    ],
                    "template": DEFAULT_SYSTEM_PROMPT_TEMPLATE,
                    "variables": {
                        **DEFAULT_SYSTEM_PROMPT_VARIABLES,
                    },
                },
            },
            'llmstack': {
                'auth': None,
                'bucket': None,
                'param': 'param-sitez-aibots-llmstack',
                'path': None,
                'pub_url': None,
                'secret': None,
                'url': None
            },
            "logging_level": 20,
            "messages": {
                "atlas": DEFAULT_ATLAS_MESSAGES,
                **DEFAULT_APP_MESSAGES,
            },
            "nous_api": {
                "pub_url": None,
                "url": AnyUrl(
                    "https://nous-api.internal.sit.aibots.gov.sg/"
                ),
                "auth": None,
                "bucket": None,
                "secret": None,
                "path": None,
                "param": None,
            },
            "port": 443,
            "project": {
                "pub_url": AnyUrl('https://sit.aibots.gov.sg/'),
                "url": None,
                "auth": None,
                "secret": "secret-sitezapp-aibots-main-api",
                "bucket": "s3-sitezapp-aibots-471112510129-project",
                "path": None,
                "param": None,
            },
            "project_api": {
                "auth": None,
                "bucket": None,
                "param": None,
                "path": None,
                "pub_url": AnyUrl("https://api.sit.aibots.gov.sg/"),
                "secret": None,
                "url": AnyUrl("https://api.internal.sit.aibots.gov.sg/")
            },
            "project_db": {"secret": "secret-sitezdb-aibots-main"},
            "pub_url": None,
            "ssl_certfile": "localhost.crt",
            "ssl_keyfile": "localhost.pem",
            "superusers": [
                'louisa_ong@tech.gov.sg',
                'david_tw_lee@tech.gov.sg',
                'Leon_lim@tech.gov.sg',
                'vincent_ng@tech.gov.sg',
                'kieu_quoc_thang@tech.gov.sg',
                'wilson_ng@tech.gov.sg',
                'Glenn_goh@tech.gov.sg',
                'Alex_ng@tech.gov.sg',
                'chadin_anuwattanaporn@tech.gov.sg',
                'Yeo_yong_kiat@tech.gov.sg',
                'Steven_koh@tech.gov.sg'
            ],
            "timezone": "Singapore",
            "url": None,
            "use_aws": True,
            "use_ssl": True,
            "users": []
        }
