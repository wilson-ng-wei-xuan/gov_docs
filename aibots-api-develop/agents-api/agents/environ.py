from __future__ import annotations

import secrets
from functools import lru_cache
from textwrap import dedent
from typing import Annotated, Any

from aibots.constants import (
    DATABASE_NAME,
    DEFAULT_AGENT_WELCOME_MESSAGE,
    DEFAULT_LLM_MODEL_ID,
    DEFAULT_RAG_PIPELINE_TYPE,
    DEFAULT_SYSTEM_PROMPT_TEMPLATE,
    DEFAULT_SYSTEM_PROMPT_VARIABLES,
    PRODUCT_ID,
)
from atlas.environ import (
    AppEnviron,
    AWSEnvVars,
    BucketEnvVars,
    DBEnvVars,
    ServiceEnvVars,
)
from atlas.genai.schemas import AtlasLLMInteractionBase, PromptTemplate
from atlas.schemas import Email, Uuid
from pydantic import AliasChoices, AnyUrl, Field, field_validator

from agents.constants import (
    DEFAULT_APP_MESSAGES,
    INTERNAL_API_KEYS,
)

__doc__ = """
Contains all application-wide constants imported from environment 
variables, managed in the AppEnviron structure
"""  # noqa: E501

__all__ = ("AIBotsAgentEnviron", "get_environ")


class AIBotsAgentEnviron(
    AppEnviron,
    AWSEnvVars,
    DBEnvVars,
    default_app_messages=DEFAULT_APP_MESSAGES,
):
    """
    Contains all application-wide constants from API to Logging

    Attributes:
        component (str): Component name
        timezone (str): Timezone value used in API retrieved from TIMEZONE
                        environment variable, defaults to Singapore
        debug (bool): Debug flag to indicate that local debugging functionality
                      should be initialised
        logging_level (int): Logging level retrieved from environment variable,
                             defaults to 20
        email (Email): Email environment variables, defaults to default
                       Email variables
        jwt (Optional[str]): JWT secret value, defaults to None
        issuer (str): JWT Issuer, defaults to GovTech
        expiry (ExpiryDurationsEnvVars): Expiry durations, defaults to the default
                                         ExpiryDurations value
        pub_url (Optional[AnyUrl]): Service public URL, defaults to None
        host (str): Host parameter retrieved from HOST environment variable,
                    defaults to 127.0.0.1
        port (int): Host port retrieved from PORT environment variable,
                    defaults to 443
        access_log (bool): Uvicorn access log parameters, defaults to True
        use_ssl (bool): Indicates if SSL should be used
        ssl_keyfile (str): SSL private key file, defaults to localhost.pem
        ssl_certfile (str): SSL certificate, defaults to localhost.crt
        cdn_cert (Optional[str]): CDN certificate, defaults to None
        messages (dict[str, dict[str, str]]): Messages to be loaded
        users (Optional[list[UserCreation]]): Users to be created, defaults to an
                                              empty list
        superusers (Optional[list[EmailStr]]): Superusers to be added, defaults to
                                               an empty list

        project (SecretEnvVars | None): Project secret variable, defaults to None

        db_url (AnyUrl | None): Database connection URL
        db_user (str | None): Database connection user, defaults to None
        db_password (str | None): Database connection password, defaults to
                                  None
        db_port (int | None): Database connection port, defaults to None
        db_tls (bool): Indicates that TLS should be used, defaults to True
        project_db (AWSSecretEnvVars | None): Project database secret variable,
                                              defaults to None

        aws_id (str | None): AWS Account ID, defaults to None
        aws_access_id (str): AWS Access ID, defaults to None
        aws_secret_key (str): AWS Secret Access Key, defaults to None
        aws_region (str): AWS operational region, defaults to ap-southeast-1
        aws_endpoint_url (AnyUrl | None): AWS endpoint URL, defaults to None

        cloudfront (ServiceEnvVars | None): Cloudfront service env vars
    """  # noqa: E501

    # Application level constants
    component: str = "aibots"
    pub_url: AnyUrl | None = "https://aibots.gov.sg"
    issuer: str = "GovTech"
    jwt: Annotated[str, Field(default_factory=lambda: secrets.token_hex(16))]
    cdn_cert: str | None = None  # TODO: Move to Attachments
    project: ServiceEnvVars | None = None

    use_aws: bool = True
    analytics: BucketEnvVars | None = None

    llm_defaults: AtlasLLMInteractionBase = AtlasLLMInteractionBase(
        model=DEFAULT_LLM_MODEL_ID,
        system_prompt={
            "template": DEFAULT_SYSTEM_PROMPT_TEMPLATE,
            "variables": DEFAULT_SYSTEM_PROMPT_VARIABLES,
        },
    )

    nous_api: Annotated[
        ServiceEnvVars | None,
        Field(None, validation_alias=AliasChoices("NOUS_API", "NOUS-API")),
    ]
    emails_api: Annotated[
        ServiceEnvVars | None,
        Field(
            None,
            validation_alias=AliasChoices(
                "EMAIL-SEND", "EMAIL_SEND", "EMAILS_API"
            ),
        ),
    ]
    project_api: ServiceEnvVars | None = None
    cloudfront: ServiceEnvVars | None = None
    llmstack: ServiceEnvVars | None = None
    govtext: ServiceEnvVars | None = None

    @field_validator("db_url", mode="before")
    @classmethod
    def validate_db_url(cls, v: AnyUrl | None) -> AnyUrl | None:
        """
        Prepends the MongoDB scheme to the URL if not provided

        Args:
            v (AnyUrl | None): MongoDB URL

        Returns:
            AnyUrl | None: MongoDB Scheme appended URL
        """
        if v is not None and "://" not in v:
            return AnyUrl(f"mongodb://{str(v)}")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: dict[str, Any] | None) -> Email:
        """
        Validate email variables provided

        Args:
            v (dict[str, Any] | None): Unvalidated email variables

        Returns:
            Email | None: Validated email variables
        """
        return Email(
            **{
                # TODO: Change default sender when product.gov.sg
                #  is registered
                "name": "The AIBots Team",
                "sender": "no-reply@sit.aibots.gov.sg",
                "subject": "One-Time Password (OTP) for ${product}",
                "html": dedent(
                    """\
                    <html>
                    <head></head>
                    <body>
                      <h4>Your OTP is: <b>${otp}</b></h4>
                      <p>This will expire in ${duration}.</p>
                      <p></p>
                      <p>If your OTP does not work, please request for a new 
                      OTP at ${domain}.</p>
                      <p></p>
                      <p>AIBots Support Team</p>
                    </body>
                    </html>
                    """
                ),
                "text": dedent(
                    """\
                    Your OTP is ${otp} \r\n
                    It will expire in ${duration}.\r\n
                    If your OTP does not work, please request for a new
                    OTP at ${domain}.\r\n
                    AIBots Support Team
                    """
                ),
                **(v or {}),
            }
        )

    @property
    def database(self) -> str:
        """
        Convenience function for retrieving the primary database

        Returns:
            str: Primary database
        """
        return DATABASE_NAME

    @property
    def product_id(self) -> str:
        """
        Convenience function for retrieving the product ID

        Returns:
            str: Product UUID
        """
        return PRODUCT_ID

    @property
    def default_system_prompt(self) -> PromptTemplate:
        """
        Convenience function for retrieving the default user prompt
        template

        Returns:
            PromptTemplate: User prompt template
        """
        return PromptTemplate(
            template=DEFAULT_SYSTEM_PROMPT_TEMPLATE,
            variables=DEFAULT_SYSTEM_PROMPT_VARIABLES,
        )

    @property
    def default_welcome_message(self) -> str:
        """
        Convenience function for retrieving the default bot
        welcome message

        Returns:
            str: Bot welcome message
        """
        return DEFAULT_AGENT_WELCOME_MESSAGE

    @property
    def default_rag_type(self) -> str:
        """
        Convenience function for retrieving the default RAG
        pipeline type

        Returns:
            str: RAG pipeline type
        """
        return DEFAULT_RAG_PIPELINE_TYPE

    @property
    def default_user_settings(self) -> dict[str, Any]:
        """
        Convenience function for retrieving default user
        settings

        Returns:
            dict[str, Any]: Default user settings
        """
        return {}

    @property
    def internal_api_keys(self) -> list[Uuid]:
        """
        Convenience function for retrieving internal
        API Keys

        Returns:
            list[Uuid]: List of internal API Keys
        """
        return [i["key"] for i in INTERNAL_API_KEYS]


environ: AIBotsAgentEnviron | None = None


@lru_cache
def get_environ() -> AIBotsAgentEnviron:
    """
    Convenience function to retrieve a cached version
    of the AppEnviron setting

    Returns:
        AIBotsAgentEnviron: Application environment variables
    """
    global environ
    if not environ:
        environ = AIBotsAgentEnviron()
    return environ
