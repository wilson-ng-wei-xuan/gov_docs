from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from logging import Logger, getLogger
from typing import AsyncContextManager

import httpx
from aibots.rags import GovTextEngine, LLMStackEngine
from atlas.beanie import BeanieDataset, BeanieService
from atlas.boto3.services import CloudfrontService, SecretsService
from atlas.boto3.services.ssm import SSMService
from atlas.fastapi.processors import add_service_from_registry
from atlas.schemas import DatabaseConfig, ScimStringProperty
from atlas.services import ServiceManager, ServiceRegistry
from fastapi import FastAPI

from agents.environ import AIBotsAgentEnviron
from agents.models import RoleDB, ScimUserDB, models
from agents.mongo import (
    init_collections,
    init_db,
    init_defaults,
    init_file_collections,
    init_permissions_collections,
    init_permissions_defaults,
    init_scim_collections,
    init_scim_defaults,
)

__doc__ = """
A FastAPI application is structured as an app with associated modules 
that are booted up when the application is started. This package contains 
functionality to configure the FastAPI application via the lifespan function.
"""


__all__ = (
    "aws_lifespan",
    "primary_db_lifespan",
    "init_cdn_lifespan",
    "init_defaults_lifespan",
    "init_users_lifespan",
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
    environ: AIBotsAgentEnviron = app.atlas.environ
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
    environ: AIBotsAgentEnviron = app.atlas.environ

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
                init_file_collections,
                init_scim_collections,
                init_permissions_collections,
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
    environ: AIBotsAgentEnviron = app.atlas.environ
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
async def init_defaults_lifespan(app: FastAPI) -> AsyncContextManager[None]:
    """
    Lifespan function to initialise default values within the DB

    Args:
        app (FastAPI): FastAPI app

    Returns:
        AsyncContextManager[None]: Async context manager
    """
    db: BeanieService = app.atlas.db
    db.add_init_db(
        [init_scim_defaults, init_permissions_defaults, init_defaults]
    )
    yield


@asynccontextmanager
async def init_users_lifespan(app: FastAPI) -> AsyncContextManager[None]:
    """
    Lifespan function to initialise default values within the DB

    Args:
        app (FastAPI): FastAPI app

    Returns:
        AsyncContextManager[None]: Async context manager
    """
    # TODO: Improve with Atlas User
    environ: AIBotsAgentEnviron = app.atlas.environ
    db: BeanieService = app.atlas.db
    logger: Logger = getLogger(environ.loggers["base"])

    # Initialise the database
    service_registry: ServiceRegistry = app.atlas.services
    await service_registry.atlas_services_ainit(logger)

    logger.info("Initialising users and superusers")
    if environ.users:
        logger.info("Initialising users")
        users_col: BeanieDataset = db.atlas_dataset(ScimUserDB.Settings.name)
        roles: BeanieDataset = db.atlas_dataset(RoleDB.Settings.name)
        for u in environ.users:
            try:
                user_id: str = str(uuid.uuid5(uuid.NAMESPACE_DNS, u["email"]))
                role: RoleDB = await roles.get_item(RoleDB.name == u["role"])
                user: ScimUserDB = ScimUserDB.create_schema(
                    uid=user_id,
                    user=user_id,
                    resource_type=ScimUserDB.Settings.name,
                    location=str(environ.project.pub_url) + f"users/{user_id}",
                    version=1,
                    **{
                        **u,
                        "roles": [
                            ScimStringProperty[str](
                                value=role.id,
                                primary=True,
                                type="rbac",
                                display=role.name,
                            )
                        ],
                    },
                )
                logger.info(f"Preloading user {user.model_dump()}")
                await users_col.create_item(user)
            except Exception as e:
                logger.debug(
                    f"Error {e.__class__.__name__}.{str(e)} occurred when "
                    f"creating user {u}"
                )
                continue
    if environ.superusers:
        environ.superusers = [u.lower() for u in environ.superusers]
        logger.info(
            f"Users in the following list {environ.superusers} "
            f"will be initialised as superusers when they login"
        )
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

    environ: AIBotsAgentEnviron = app.atlas.environ
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
