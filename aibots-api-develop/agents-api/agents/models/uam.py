from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from annotated_types import Ge
from atlas.asgi.schemas import APIGet, APIKey
from atlas.mixins import CUDMixin
from atlas.schemas import (
    Login as BaseLogin,
)
from atlas.schemas import (
    Otp as BaseOtp,
)
from atlas.schemas import (
    Role as BaseRole,
)
from atlas.schemas import (
    UserLogin as BaseUserLogin,
)
from atlas.schemas import (
    Uuid,
)
from atlas.utils import generate_randstr
from beanie import Document
from pydantic import AliasChoices, Field, Strict, StringConstraints

__all__ = (
    "OtpDB",
    "UserLoginGet",
    "LoginDB",
    "RoleDB",
)


class UserLoginGet(APIGet, BaseUserLogin):
    """
    User Login GET schema

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
        start_use (datetime): Timestamp when the Login token
                              can be used from, defaults to
                              the current time
        timestamp (datetime): Timestamp when the Login was
                              generated, defaults to the
                              current time
        expiry (datetime): Expiry timestamp for the user's
                           token
        name (str): Name field with length restriction
        email (EmailStr): Email of the User
        new_user (bool): Indicates that this is the first
                         time a user is logging in, defaults
                         to False
        scopes (List[str]): List of scope strings, defaults
                            to an empty list
        role (Optional[Uuid]): Role of the User, defaults to
                               None
        superuser (bool): Indicates if the user is a superuser
                          defaults to None
        agency (Optional[StrictStr]): Agency details of the user,
                                      defaults to None
    """

    id: Uuid = Field(validation_alias="sub")
    issuer: str = Field(validation_alias="iss")
    product: str = Field(validation_alias="aud")
    access_token: Annotated[
        str,
        StringConstraints(
            strict=True, min_length=32, max_length=32, pattern="^[A-Za-z0-9]+$"
        ),
        Field(
            default_factory=lambda: generate_randstr(16), alias="accessToken"
        ),
    ]
    refresh_token: Annotated[
        str,
        StringConstraints(
            strict=True, min_length=32, max_length=32, pattern="^[A-Za-z0-9]+$"
        ),
        Field(
            default_factory=lambda: generate_randstr(16), alias="refreshToken"
        ),
    ]
    refresh_count: Annotated[
        int, Strict(), Ge(0), Field(0, alias="refreshCount")
    ]
    max_refresh: Annotated[int, Strict(), Ge(0), Field(5, alias="maxRefresh")]
    expiry: datetime = Field(validation_alias="exp")
    start_use: Annotated[
        datetime,
        Field(
            validation_alias="nbf",
            alias="startUse",
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


class APIKeyDB(APIKey, Document):
    """ "
    API Key details for API key

    Attributes:
        id (Uuid): Uuid of the API Key
        name (StrictStr): Name field with no length restriction
        description (StrictStr): Description field, defaults to an empty string
        meta (Meta): Metadata associated with the resource,
                     defaults to the default Meta values
        modifications (ModificationDict): Modification details,
                                          defaults to an empty
                                          dictionary
        type (Literal["test", "prod"]): Type of API Key, defaults to test
        checksum (Optional[str]): Checksum of the API Key,
                                  defaults to None
        key (Optional[str]): Salted API Key value, defaults to None
        expiry (Optional[datetime]): Expiry time of the API Key,
                                     defaults to None
        scopes (list[str]): Scopes associated with API Key, defaults to
                            an empty list
        original_key (Optional[str]): Original API Key value, defaults
                                      to None
    """

    class Settings:
        name: str = "api_keys"


class OtpDB(BaseOtp, Document):
    """
    OTP details for emails and other 2FA authentication

    Attributes:
        id (Uuid): UUID of the Otp, autogenerated, inherited
        user (Uuid): UUID of the User
        email (EmailStr): Email of the User
        otp (str): OTP details, defaults to a randomly
                   generated otp string
        timestamp (datetime): Datetime OTP generated, defaults
                              to the current datetime
        expiry (datetime): Expiry datetime of the OTP
    """

    class Settings:
        name: str = "otps"


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


class RoleDB(BaseRole, CUDMixin, Document):
    """
    MongoDB schema for Role details

    Attributes:
        id (Uuid): UUID string
        name (str): Name field with length restriction
        description (str): Description field, defaults to an
                           empty string
        default (bool): Indicates if the role is a default role,
                        defaults to False
        superuser (bool): Indicates that the user is a superuser,
                          with no restrictions on any resources,
                          defaults to False
        scopes (list[Scope]): List of Scopes that are supported,
                              defaults to an empty list
        meta (Meta): Metadata associated with the resource,
                     defaults to the default Meta values
        modifications (ModificationDict): Modification details,
                                          defaults to an empty
                                          dictionary
    """

    class Settings:
        name: str = "roles"
