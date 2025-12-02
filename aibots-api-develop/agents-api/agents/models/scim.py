from __future__ import annotations

from typing import Annotated

from atlas.mixins import CUDMixin
from atlas.schemas import (
    ScimAddress as BaseScimAddress,
)
from atlas.schemas import (
    ScimGroup as BaseScimGroup,
)
from atlas.schemas import (
    ScimGroupExtensions as BaseScimGroupExtensions,
)
from atlas.schemas import (
    ScimList,
    ScimStringProperty,
    Uuid,
)
from atlas.schemas import (
    ScimName as BaseScimName,
)
from atlas.schemas import (
    ScimReference as BaseScimReference,
)
from atlas.schemas import (
    ScimUser as BaseScimUser,
)
from atlas.schemas import (
    ScimUserExtensions as BaseScimUserExtensions,
)
from beanie import Document
from pydantic import AnyUrl, Field

__all__ = (
    "ScimReference",
    "ScimGroupExtensions",
    "ScimGroup",
    "ScimGroupDB",
    "ScimName",
    "ScimAddress",
    "ScimUserExtensions",
    "ScimUser",
    "ScimUserDB",
)


class ScimReference(BaseScimReference):
    """
    SCIM reference

    Attributes:
        ref (Optional[str]): URI reference or UUID of the resource,
                             defaults to None
        type (Optional[str]): Type of scim property, defaults to None
        display (Optional[str]): Display value of the reference, defaults
                                 to None
        value (Optional[str]): ID of the reference, defaults to None
    """

    ref: Annotated[str | None, Field(None, validation_alias="$ref")]


class ScimGroupExtensions(BaseScimGroupExtensions):
    """
    Atlas Scim group extensions with validation aliases

    Attributes:
        description (str): Profile description of the user, defaults
                           to None
        agency (str | None): Agency suffix of the group, defaults to
                             None
        domain (str | None): Domain associated with the group, defaults
                             to None
        api_keys (list[ScimReference]): API Keys associated
                                        with the user, defaults
                                        to an empty list
        default (bool): Indicates that the group is a default
                        organisation, defaults to False
        parent (Optional[ScimReference]): Parent group, defaults to
                                          None
        children (list[ScimReference]): Child groups, defaults to
                                        an empty list
        administrators (list[ScimReference]): Administrators of the
                                              group, only applies
                                              to root-level groups,
                                              defaults to an empty
                                              list
        details (dict[str, Any]): Additional details that
                                  describe the group, defaults
                                  to an empty dictionary
        default_role (Optional[Union[str, Uuid]]): Default role for the
                                                   group, defaults to
                                                   None
        allow (bool): Indicates if the user is allowed or blocked,
                      defaults to True
    """

    api_keys: Annotated[
        list[ScimReference], Field([], validation_alias="apiKeys")
    ]
    parent: ScimReference | None = None
    children: list[ScimReference] = []
    administrators: list[ScimReference] = []
    default_role: Annotated[
        Uuid | None, Field(None, validation_alias="defaultRole")
    ]


class ScimGroup(BaseScimGroup):
    """
    Scim representation of a group with validation aliases

    Attributes:
        schemas (list[str]): SCIM resource schema reference
        id (Uuid): Uuid of the SCIM resource
        meta (Meta): Descriptive metadata about the SCIM resource
        display_name (str): Display name of the group
        members (list[ScimReference]): List of members of the group,
                                       defaults to an empty list
        atlas_extensions (ScimGroupExtensions): Atlas extensions to Scim
    """

    display_name: Annotated[str, Field(validation_alias="displayName")]
    members: list[ScimReference] = []
    atlas_extensions: Annotated[
        ScimGroupExtensions,
        Field(
            ScimGroupExtensions(),
            validation_alias="urn:ietf:params:scim:schemas:extensions:atlas:2.0:Group",
        ),
    ]


class ScimGroupDB(ScimGroup, CUDMixin, Document):
    """
    Scim representation of a group

    Attributes:
        schemas (list[str]): SCIM resource schema reference
        id (Uuid): Uuid of the SCIM resource
        meta (Meta): Descriptive metadata about the SCIM resource
        display_name (str): Display name of the group
        members (list[ScimReference]): List of members of the group,
                                       defaults to an empty list
        atlas_extensions (ScimGroupExtensions): Atlas extensions to Scim
    """

    class Settings:
        name: str = "groups"


class ScimName(BaseScimName):
    """
    Scim representation of a user's full name with validation aliases

    Attributes:
       family_name (Optional[str]): Surname of the user, defaults
                                    to None
       given_name (Optional[str]): Name of the user, defaults
                                   to None
       middle_name (Optional[str]): Middle name of the user, defaults
                                    to None
       honorific_prefix (Optional[str]): Honorific prefix of the user,
                                         defaults to None
       honorific_prefix (Optional[str]): Honorific suffix of the user,
                                         defaults to None
    """

    family_name: Annotated[
        str | None, Field(None, validation_alias="familyName")
    ]
    given_name: Annotated[
        str | None, Field(None, validation_alias="givenName")
    ]
    middle_name: Annotated[
        str | None, Field(None, validation_alias="middleName")
    ]
    honorific_prefix: Annotated[
        str | None, Field(None, validation_alias="honorificPrefix")
    ]
    honorific_suffix: Annotated[
        str | None, Field(None, validation_alias="honorificSuffix")
    ]


class ScimAddress(BaseScimAddress):
    """
    Scim representation of a user's Address with validation aliases

    Attributes:
        primary (bool): Indicates if the property is the preferred value
                        amongst others, defaults to False
        type (Optional[str]): Type of scim property, defaults to None
        formatted (Optional[str]): Full mailing Address, defaults to None
        street_address (Optional[str]): Street address, defaults to None
        locality (Optional[str]): City or locality of the Address,
                                  defaults to None
        region (Optional[str]): State or region of the Address,
                                defaults to None
        postal_code (Optional[str]): Postal code of the Address,
                                     defaults to None
        country (Optional[str]): Country of the Address,
                                 defaults to None
    """

    street_address: Annotated[
        str | None, Field(None, validation_alias="streetAddress")
    ]
    postal_code: Annotated[
        str | None, Field(None, validation_alias="postalCode")
    ]


class ScimUserExtensions(BaseScimUserExtensions):
    """
    Atlas Scim group extensions with validation aliases

    Attributes:
        description (str): Profile description of the user, defaults
                           to None
        agency (Optional[str]): Agency suffix of the User, defaults
                                to None
        settings (dict[str, Any]): Settings of the User,
                                   defaults to an empty
                                   dictionary
        favourites (dict[str, list[str]]): Favourite items
                                           that a user has
                                           bookmarked,
                                           defaults to an
                                           empty dictionary
        details (dict[str, Any]): Additional details that
                                  describe the user, defaults
                                  to an empty dictionary
        verified (bool): Indicates if the user has verified
                         their email, defaults to False
        api_keys (list[ScimReference]): API Keys associated
                                        with the user, defaults
                                        to an empty list
        allow (bool): Indicates if the user is allowed or blocked,
                      defaults to True
        active (bool): Indicates if the user is active, defaults to True
        salt (str): Salt used to hash the API Key, defaults to a 16-byte
                    random string
    """

    active: bool = True  # TODO: Remove this when integrated into Atlas
    api_keys: Annotated[
        list[ScimReference], Field([], validation_alias="apiKeys")
    ]


class ScimUser(BaseScimUser):
    """
    SCIM representation of a user with validation aliases

    Attributes:
        schemas (list[str]): SCIM resource schema reference
        id (Uuid): Uuid of the SCIM resource
        meta (Meta): Descriptive metadata about the SCIM resource
        external_id (str): External ID of the user, defaults to ID value
        user_name (Optional[str]): Username of the user, defaults to None
        name (ScimName): Full name of the user, extracted from the display name
        display_name (Optional[str]): Display name of the user, defaults to None
        nick_name (Optional[str]): Nickname of the user, defaults to None
        profile_url (Optional[AnyUrl]): URL of the user's profile, defaults to
                                        None
        title (Optional[str]): Official job title of the user, defaults to None
        user_type (Optional[str]): Used to identify the relationship between the
                                   organization and the user, defaults to None
        preferred_language (str): Preferred language of the user, defaults to en
        locale (str): Preferred locale of the user, defaults to en_SG
        timezone (str): Current timezone of the user, defaults to Singapore
        password (Optional[str]): Password of the user, defaults to None
        emails (ScimList[ScimEmail]): Email addresses of the user, defaults to an
                                  empty list
        phone_numbers (ScimList[ScimStringProperty]): Phone numbers of the user, defaults
                                                      to an empty list
        ims (ScimList[ScimStringProperty]): List of instant messaging handles of the
                                            user, defaults to an empty list
        photos (ScimList[ScimStringProperty]): List of photos of the user, defaults to
                                           an empty list
        addresses (ScimList[ScimAddress]): List of addresses belonging to the user, defaults
                                       to an empty list
        groups (list[ScimReference]): List of groups the user belongs to, defaults
                                      to an empty list
        entitlements (ScimList[ScimStringProperty]): Permissions that the user has,
                                                     defaults to an empty list
        roles (ScimList[ScimStringProperty]): List of roles that the user has, defaults
                                              to an empty list
        x509_certificates (ScimList[ScimStringProperty]): List of X.509 certificates,
                                                          defaults to an empty list
        atlas_extensions (ScimUserExtensions): Atlas extensions to Scim Users, defaults
                                               to ScimUserExtensions values
    """  # noqa: E501

    external_id: Annotated[str, Field(None, validation_alias="externalId")]
    user_name: Annotated[str | None, Field(None, validation_alias="userName")]
    display_name: Annotated[
        str | None, Field(None, validation_alias="displayName")
    ]
    name: Annotated[ScimName | None, Field(None)]
    nick_name: Annotated[str | None, Field(None, validation_alias="nickName")]
    profile_url: Annotated[
        AnyUrl | None, Field(None, validation_alias="profileUrl")
    ]
    user_type: Annotated[str | None, Field(None, validation_alias="userType")]
    preferred_language: Annotated[
        str, Field("en", validation_alias="preferredLanguage")
    ]
    phone_numbers: Annotated[
        ScimList[ScimStringProperty[str]],
        Field(ScimList([]), validation_alias="phoneNumbers"),
    ]
    groups: list[ScimReference] = []
    x509_certificates: Annotated[
        ScimList[ScimStringProperty[str]],
        Field(ScimList([]), validation_alias="x509Certificates"),
    ]
    atlas_extensions: Annotated[
        ScimUserExtensions,
        Field(
            ScimUserExtensions(),
            validation_alias="urn:ietf:params:scim:schemas:extensions:atlas:2.0:User",
        ),
    ]


class ScimUserDB(ScimUser, CUDMixin, Document):
    """
    MongoDB schema for User details

    Attributes:
        schemas (list[str]): SCIM resource schema reference
        id (Uuid): Uuid of the SCIM resource
        meta (Meta): Descriptive metadata about the SCIM resource
        external_id (str): External ID of the user, defaults to ID value
        user_name (Optional[str]): Username of the user, defaults to None
        name (ScimName): Full name of the user, extracted from the display name
        display_name (Optional[str]): Display name of the user, defaults to None
        nick_name (Optional[str]): Nickname of the user, defaults to None
        profile_url (Optional[AnyUrl]): URL of the user's profile, defaults to
                                        None
        title (Optional[str]): Official job title of the user, defaults to None
        user_type (Optional[str]): Used to identify the relationship between the
                                   organization and the user, defaults to None
        preferred_language (str): Preferred language of the user, defaults to en
        locale (str): Preferred locale of the user, defaults to en_SG
        timezone (str): Current timezone of the user, defaults to Singapore
        password (Optional[str]): Password of the user, defaults to None
        emails (ScimList[ScimEmail]): Email addresses of the user, defaults to an
                                  empty list
        phone_numbers (ScimList[ScimStringProperty]): Phone numbers of the user, defaults
                                                      to an empty list
        ims (ScimList[ScimStringProperty]): List of instant messaging handles of the
                                            user, defaults to an empty list
        photos (ScimList[ScimStringProperty]): List of photos of the user, defaults to
                                           an empty list
        addresses (ScimList[ScimAddress]): List of addresses belonging to the user, defaults
                                       to an empty list
        groups (list[ScimReference]): List of groups the user belongs to, defaults
                                      to an empty list
        entitlements (ScimList[ScimStringProperty]): Permissions that the user has,
                                                     defaults to an empty list
        roles (ScimList[ScimStringProperty]): List of roles that the user has, defaults
                                              to an empty list
        x509_certificates (ScimList[ScimStringProperty]): List of X.509 certificates,
                                                          defaults to an empty list
        atlas_extensions (ScimUserExtensions): Atlas extensions to Scim Users, defaults
                                               to ScimUserExtensions values
    """  # noqa: E501

    class Settings:
        name: str = "users"
