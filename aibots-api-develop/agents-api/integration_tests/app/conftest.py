from __future__ import annotations

import os

import pytest


# TODO: Update this when the environment variables are updated
environ_values: dict[str, str] = {
    'EMAIL_SEND__BUCKET': 's3-sitez-sharedsvc-471112510129-email',
    'HOST': '0.0.0.0',
    'PROJECT__SECRET': 'secret-sitezapp-aibots-main-api',
    'PROJECT_DB__SECRET': 'secret-sitezdb-aibots-main',
    'CLOUDFRONT__PARAM': 'param-sitezingress-aibots-cloudfront-publickey',
    'ANALYTICS__PATH': 'aibots/',
    'LLMSTACK__PARAM': 'param-sitez-aibots-llmstack',
    'USE_SSL': '1',
    'EMAIL_SEND__PTE_URL': 'https://email.sit.private-api.aibots.gov.sg:443/send',
    'SUPERUSERS': '["joseph_tan@tech.gov.sg","lim_hock_chuan@tech.gov.sg","kenneth_kw_ong@tech.gov.sg","mindy_lim@tech.gov.sg","nick_tan@tech.gov.sg","ng_yong_kiat@tech.gov.sg","edwin_lee@tech.gov.sg","ryan_tan@tech.gov.sg","wesley_tham@tech.gov.sg","ian_soo@tech.gov.sg","nicole_lee@tech.gov.sg","vincent_ng@tech.gov.sg","leon_lim@tech.gov.sg","kieu_quoc_thang@tech.gov.sg","david_tw_lee@tech.gov.sg","chan_li_shing@tech.gov.sg","glenn_goh@tech.gov.sg","wilson_ng@tech.gov.sg"]',
    'AWS_ID': '471112510129',
    'PROJECT__BUCKET': 's3-sitezapp-aibots-471112510129-project',
    'AWS_REGION': 'ap-southeast-1',
    'PORT': '443',
    'CLOAK__PARAM': 'param-sitez-aibots-cloak',
    'EMAIL_SEND__PATH': 'aibots/',
    'DEBUG': '0',
    'CLOUDFRONT__BUCKET': 's3-sitezingress-aibots-471112510129-cloudfront',
    'EMAIL_SEND__SECRET': 'secret-sitezapp-aibots-smtp-user-no-reply',
    'VECTORDB_OPENSEARCH__NAME': 'aibots-rag-vectordb-opensearch',
    'CLOUDFRONT__SECRET': 'secret-sitezingress-aibots-cloudfront',
    'PROJECT__PUB_URL': 'https://sit.aibots.gov.sg',
    'ANALYTICS__BUCKET': 's3-sitez-sharedsvc-471112510129-analytics',
    'NOUS_API__PTE_URL': 'https://nous-api.sit.private-api.aibots.gov.sg:443',
    'CLOUDFRONT__PUB_URL': 'https://public.sit.aibots.gov.sg:443',
    'COMPONENT': 'aibots-main-api',
}


def pytest_configure(config: pytest.Config) -> None:
    for k, v in environ_values.items():
        os.environ[k] = v


def pytest_unconfigure(config: pytest.Config) -> None:
    for k in environ_values:
        del os.environ[k]
