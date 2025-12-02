from __future__ import annotations

import json
from contextlib import asynccontextmanager
from logging import Logger, getLogger
from typing import Any, AsyncContextManager

import httpx
from aibots.rags import GovTextEngine, LLMStackEngine
from atlas.boto3.services import CloudfrontService, SecretsService
from atlas.boto3.services.ssm import SSMService
from atlas.fastapi.processors import add_service_from_registry
from atlas.genai.schemas import (
    AIModel,
    AIModelType,
    AIParameter,
    AIParamType,
    SecurityClassificationType,
)
from atlas.nous import NousService
from atlas.schemas import DatabaseConfig
from atlas.services import ServiceManager, ServiceRegistry
from fastapi import FastAPI

from chats.environ import AIBotsChatEnviron
from chats.models import models
from chats.mongo import init_collections, init_db, init_defaults

__doc__ = """
A FastAPI application is structured as an app with associated modules 
that are booted up when the application is started. This package contains 
functionality to configure the FastAPI application via the lifespan function.
"""


__all__ = (
    "aws_lifespan",
    "primary_db_lifespan",
    "llms_lifespan",
    "init_cdn_lifespan",
    "rags_lifespan",
)


@asynccontextmanager
async def aws_lifespan(app: FastAPI) -> AsyncContextManager[None]:
    """
    Lifespan function to initialise AWS resources

    Args:
        app (FastAPI): FastAPI app

    Returns:
        AsyncContextManager[None]: Async context manager
    """
    environ: AIBotsChatEnviron = app.atlas.environ
    logger: Logger = getLogger(environ.loggers["base"])
    service_registry: ServiceRegistry = app.atlas.services
    await service_registry.atlas_services_ainit(logger)

    # Initialise secrets manager to retrieve:
    #   1. DB credentials
    #   2. AI Bots secret values
    #   3. Email API
    secrets: SecretsService = SecretsService(**environ.aws_config)
    with secrets:
        if environ.use_aws:
            # DB credentials
            db_credentials: dict[str, str] = secrets.atlas_get_dict(
                environ.project_db.secret
            )
            environ.db_url = db_credentials["host"]
            environ.db_port = 27017
            environ.db_user = db_credentials["username"]
            environ.db_password = db_credentials["password"]

        # TODO: Update this after environment has been created
        # AI Bots secret values
        jwt: dict[str, str] = secrets.atlas_get_dict(environ.project.secret)
        service_registry.get("jwt").secret = environ.jwt = jwt["JWT"]

        # Email API
        if environ.emails_api.secret:
            environ.emails_api.auth = json.dumps(
                secrets.atlas_get_dict(environ.emails_api.secret)
            )
        else:
            logger.error("EMAILS_API__SECRET not provided")
    service_registry.atlas_add(secrets, "secrets")

    ssm: SSMService = SSMService(**environ.aws_config)
    with ssm:
        # LLMSTACK API
        if environ.llmstack.param:
            llmstack_params: dict = ssm.atlas_get_dict(
                environ.llmstack.param, **{"WithDecryption": True}
            )
            environ.llmstack.auth = llmstack_params["key"]
            environ.llmstack.url = llmstack_params["endpoint"]
        else:
            logger.error("LLMSTACK__PARAM not provided")
        # GOVTEXT API
        if environ.govtext.param:
            govtext_params: dict = ssm.atlas_get_dict(
                environ.govtext.param, **{"WithDecryption": True}
            )
            environ.govtext.auth = govtext_params["key"]
            environ.govtext.url = govtext_params["endpoint"]
        else:
            logger.error("GOVTEXT__PARAM not provided")
    service_registry.atlas_add(ssm, "ssm")
    service_registry.add_from_registry("s3", **environ.aws_config)
    yield


@asynccontextmanager
async def primary_db_lifespan(app: FastAPI) -> AsyncContextManager[None]:
    """
    Lifespan function to initialise the Primary DB

    Args:
        app (FastAPI): FastAPI app

    Returns:
        AsyncContextManager[None]: Async context manager
    """
    environ: AIBotsChatEnviron = app.atlas.environ

    add_service_from_registry(
        app=app,
        service_name="beanie",
        service_key="db",
        **{
            "host": str(environ.db_url),
            "port": environ.db_port,
            "username": environ.db_user,
            "password": environ.db_password,
            "tls": environ.db_tls,
            "retryWrites": False,
            "tz_aware": True,
            "init_db": [
                init_db,
                init_collections,
                init_defaults,
            ],
            "db_config": [
                DatabaseConfig(
                    name=environ.database,
                    datasets=[
                        {"name": m.Settings.name, "schema": m} for m in models
                    ],
                    primary=True,
                ),
            ],
        },
    )
    yield


@asynccontextmanager
async def init_cdn_lifespan(app: FastAPI) -> AsyncContextManager[None]:
    """
    Lifespan function to initialise CDN values

    Args:
        app (FastAPI): FastAPI app

    Returns:
        AsyncContextManager[None]: Async context manager
    """
    environ: AIBotsChatEnviron = app.atlas.environ
    logger: Logger = getLogger(environ.loggers["base"])
    service_registry: ServiceRegistry = app.atlas.services
    secrets: SecretsService | None = service_registry.get("secrets")
    ssm: SSMService | None = service_registry.get("ssm")

    # Initialise the secret if not provided
    if not secrets:
        secrets: SecretsService = SecretsService(**environ.aws_config)
        service_registry.atlas_add(secrets, "secrets")

    # Initialise the ssm if not provided
    if not ssm:
        ssm: SSMService = SSMService(**environ.aws_config)
        service_registry.atlas_add(ssm, "ssm")

    logger.info("Initialising cloudfront service")
    try:
        # Retrieve the secrets manager to retrieve:
        #   1. CDN cert
        # Retrieve the SSM manager to retrieve:
        #   2. Cloudfront public key ID
        with secrets, ssm:
            environ.cdn_cert = secrets.atlas_get(environ.cloudfront.secret)
            if environ.cloudfront.param:
                environ.cloudfront.key = ssm.atlas_get(
                    environ.cloudfront.param, **{"WithDecryption": True}
                )
            else:
                logger.error("CLOUDFRONT__PARAM not provided")

            cloudfront: CloudfrontService = CloudfrontService(
                public_key_id=environ.cloudfront.key,
                private_key_pem=environ.cdn_cert,
                signed_url_lifetime=60,
            )
            service_registry.atlas_add(cloudfront, "cloudfront")

    except AttributeError:
        logger.error(
            "Failed to initialise cloudfront service "
            f"{environ.cloudfront=} {environ.cdn_cert=}"
        )
    yield


@asynccontextmanager
async def llms_lifespan(app: FastAPI) -> AsyncContextManager[None]:
    """
    Lifespan function to initialise LLM Services

    Args:
        app (FastAPI): FastAPI app

    Returns:
        AsyncContextManager[None]: Async context manager
    """
    environ: AIBotsChatEnviron = app.atlas.environ
    logger: Logger = getLogger(environ.loggers["base"])

    # Extracting Nous API Key values from database
    service_registry: ServiceRegistry = app.atlas.services
    await service_registry.atlas_services_ainit(logger)
    config: dict[str, Any] = await app.atlas.db.service[environ.database][
        "configs"
    ].find_one({})
    environ.nous_api.auth = config["nous"]["api_key"]

    nous: NousService = NousService(
        **{
            "configs": [
                AIModel(
                    id="azure~gpt-4o",
                    name="OpenAI GPT-4o",
                    description="Faster, cheapest, data until Oct 2023, larger content capacity (128k tokens context window)",  # noqa E501
                    type=AIModelType.text_gen,
                    security_classification=SecurityClassificationType.restricted,
                    internal=False,
                    streaming=True,
                    specs={
                        "context_size": AIParameter(
                            type=AIParamType.list,
                            default=[128_000, 4096],
                        )
                    },
                ),
                AIModel(
                    id="azure~gpt-4",
                    name="OpenAI GPT-4",
                    description="Most sophisticated but slowest, data until Sep 2021, lowest content capacity (8k tokens context window)",  # noqa E501
                    type=AIModelType.text_gen,
                    security_classification=SecurityClassificationType.restricted,
                    internal=False,
                    streaming=True,
                    specs={
                        "context_size": AIParameter(
                            type=AIParamType.list,
                            default=[8192],
                        )
                    },
                ),
                AIModel(
                    id="azure~gpt-4-turbo",
                    name="OpenAI GPT-4-Turbo",
                    description="Faster, cheaper, training data until Dec 2023, larger content capacity (128k tokens context window)",  # noqa E501
                    type=AIModelType.text_gen,
                    security_classification=SecurityClassificationType.restricted,
                    internal=False,
                    streaming=True,
                    specs={
                        "context_size": AIParameter(
                            type=AIParamType.list,
                            default=[128_000, 4096],
                        )
                    },
                ),
                AIModel(
                    id="azure~gpt-35-turbo",
                    name="OpenAI GPT-3.5-Turbo",
                    description="Fastest but least sophisticated, training data until Sep 2021, low content capacity (16k tokens context window)",  # noqa E501
                    type=AIModelType.text_gen,
                    security_classification=SecurityClassificationType.restricted,
                    internal=False,
                    streaming=True,
                    specs={
                        "context_size": AIParameter(
                            type=AIParamType.list,
                            default=[16_385, 4096],
                        )
                    },
                ),
            ],
            "defaults": environ.llm_defaults,
            "headers": {"X-ATLAS-Key": environ.nous_api.auth},
            "base_url": str(environ.nous_api.url),
            "verify": False,
            "timeout": httpx.Timeout(connect=15, read=180, write=180, pool=15),
            "retry_attempts": 0,
            "limits": httpx.Limits(
                max_keepalive_connections=100, max_connections=500
            ),
        }
    )
    service_registry.atlas_add(nous, "nous")

    # TODO: Integrate automated handshake with Nous to acquire
    #  LLM models
    # add_service_from_registry(
    #     app=app,
    #     service_name="nous",
    #     bind_app=False,
    #     **{
    #         "configs": [
    #             AIModel(
    #                 id="azure~gpt-4",
    #                 name="GPT 4",
    #                 description="OpenAI GPT 4 on Azure",
    #                 type=AIModelType.text_gen,
    #                 security_classification=SecurityClassificationType.restricted, # noqa
    #                 internal=False,
    #                 streaming=True,
    #             ),
    #         ],
    #         "defaults": environ.llm_defaults,
    #         "headers": {"X-ATLAS-Key": environ.nous_api.auth},
    #         "base_url": str(environ.nous_api.url),
    #         "verify": False,
    #         "timeout": 300.0,
    #     },
    # )

    yield


@asynccontextmanager
async def rags_lifespan(app: FastAPI) -> AsyncContextManager[None]:
    """
    Lifespan function to initialise RAG Services

    Args:
        app (FastAPI): FastAPI app

    Returns:
        AsyncContextManager[None]: Async context manager
    """

    environ: AIBotsChatEnviron = app.atlas.environ
    logger: Logger = getLogger(environ.loggers["base"])

    # Extracting Nous API Key values from database
    logger.info("Adding RAG pipelines")
    service_registry: ServiceRegistry = app.atlas.services
    rag_pipelines: ServiceManager = ServiceManager()

    logger.info(f"Adding RAG pipeline {LLMStackEngine.type}")
    rag_pipelines.atlas_add(
        LLMStackEngine(
            endpoint=environ.llmstack.url,
            headers={"Authorization": f"Bearer {environ.llmstack.auth}"},
            timeout=httpx.Timeout(
                connect=15.0, read=180.0, write=180.0, pool=15.0
            ),
            limits=httpx.Limits(
                max_keepalive_connections=100, max_connections=500
            ),
            transport=httpx.AsyncHTTPTransport(retries=3),
        ),
        LLMStackEngine.type,
    )

    logger.info(f"Adding RAG pipeline {GovTextEngine.type}")
    rag_pipelines.atlas_add(
        GovTextEngine(
            s3_bucket=environ.govtext.bucket,
            s3_service=service_registry.get("s3"),
            endpoint=environ.govtext.url,
            headers={
                "accept": "application/json",
                "X-API-KEY": environ.govtext.auth,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0)"
                " Gecko/20100101 Firefox/81.0",
            },
            timeout=httpx.Timeout(
                connect=15.0, read=180.0, write=180.0, pool=15.0
            ),
            limits=httpx.Limits(
                max_keepalive_connections=100, max_connections=500
            ),
            transport=httpx.AsyncHTTPTransport(retries=3),
        ),
        GovTextEngine.type,
    )

    service_registry.atlas_add(rag_pipelines, "rag")
    yield
