from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from annotated_types import Ge
from atlas.schemas import (
    Login as BaseLogin,
)
from atlas.schemas import (
    Uuid,
)
from atlas.utils import generate_randstr
from beanie import Document
from pydantic import AliasChoices, Field, Strict, StringConstraints

__all__ = ("LoginDB",)


# TODO: LoginDB creation should come together with
#  add_jwt_auth lifespan
class LoginDB(BaseLogin, Document):
    """
    MongoDB schema for User Login details

    Attributes:
        id (Uuid): UUID of the User
        issuer (str): Issuer of the Login token
        product (str): Product domain to be used
        token (Optional[str]): JWT token value issued to
                               a user, defaults to None
        access_token (str): JWT access token value, defaults
                            to a randomly generated hexadecimal
                            string
        refresh_token (str): Refresh token used to generate a
                             JWT token, defaults to a randomly
                             generated hexadecimal string
        refresh_count (int): Refresh count, defaults to 0
        max_refresh (int): Maximum refresh attempts, defaults
                           to 5
        expiry (datetime): Expiry timestamp for the user's
                           token
        start_use (datetime): Timestamp when the Login token
                              can be used from, defaults to
                              the current time
        timestamp (datetime): Timestamp when the Login was
                              generated, defaults to the
                              current time
    """

    id: Uuid = Field(validation_alias=AliasChoices("_id", "sub"))
    issuer: str = Field(validation_alias="iss")
    product: str = Field(validation_alias="aud")
    access_token: Annotated[
        str,
        StringConstraints(
            strict=True, min_length=32, max_length=32, pattern="^[A-Za-z0-9]+$"
        ),
        Field(
            default_factory=lambda: generate_randstr(16),
            validation_alias="accessToken",
        ),
    ]
    refresh_token: Annotated[
        str,
        StringConstraints(
            strict=True, min_length=32, max_length=32, pattern="^[A-Za-z0-9]+$"
        ),
        Field(
            default_factory=lambda: generate_randstr(16),
            validation_alias="refreshToken",
        ),
    ]
    refresh_count: Annotated[
        int, Strict(), Ge(0), Field(0, validation_alias="refreshCount")
    ]
    max_refresh: Annotated[
        int, Strict(), Ge(0), Field(5, validation_alias="maxRefresh")
    ]
    expiry: datetime = Field(validation_alias="exp")
    start_use: Annotated[
        datetime,
        Field(
            validation_alias="nbf",
            default_factory=lambda: datetime.now(timezone.utc),
        ),
    ]
    timestamp: Annotated[
        datetime,
        Field(
            validation_alias="iat",
            default_factory=lambda: datetime.now(timezone.utc),
        ),
    ]

    class Settings:
        name: str = "logins"
