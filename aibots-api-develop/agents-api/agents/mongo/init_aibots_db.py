from __future__ import annotations

from datetime import datetime, timezone
from logging import Logger
from typing import Any

import pymongo
from aibots.constants import (
    DATABASE_NAME,
    DEFAULT_PLAYGROUND_AGENT,
    PRODUCT_ID,
)
from atlas.schemas import UserType
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from agents.constants import INTERNAL_API_KEYS
from agents.models import (
    AgentDB,
    ChatDB,
    ChatMessageDB,
    KnowledgeBaseDB,
    PermissionsDB,
    RAGConfigDB,
    RoleDB,
)

__all__ = (
    "init_db",
    "init_collections",
    "init_defaults",
)


def init_db(
    client: AsyncIOMotorClient,
    logger: Logger | None = None,
) -> None:
    """
    Initialises the aibots database

    Args:
        client (AsyncIOMotorClient): AsyncIO Client
        logger (Logger | None): Logger for logging details,
                                defaults to None

    Returns:
        None
    """
    if logger:
        logger.info(f"Initialising {DATABASE_NAME} database")
    client.get_database(DATABASE_NAME)
    if logger:
        logger.info(f"Initialised {DATABASE_NAME} database")


async def init_collections(
    client: AsyncIOMotorClient, logger: Logger | None = None
) -> None:
    """
    Initialises the necessary collections and their
    associated indexes

    Args:
        client (AsyncIOMotorClient): AsyncIO Client
        logger (Logger | None): Logger for logging details,
                                defaults to None

    Returns:
        None
    """
    db: AsyncIOMotorDatabase = client[DATABASE_NAME]
    existing: list[str] = await db.list_collection_names()
    if "configs" not in existing:
        if logger:
            logger.info("Initialising configs collection")
        await db.create_collection("configs")
    if ChatMessageDB.Settings.name not in existing:
        if logger:
            logger.info(
                f"Initialising {ChatMessageDB.Settings.name} collection"
            )
        collection: AsyncIOMotorCollection = await db.create_collection(
            ChatMessageDB.Settings.name
        )
        await collection.create_index(
            [("chat", pymongo.DESCENDING)],
            name="ChatID",
        )
        await collection.create_index(
            [("model", pymongo.DESCENDING)],
            name="ModelID",
        )
        await collection.create_index(
            [("query.timestamp", pymongo.DESCENDING)],
            name="CreationTime",
        )
        await collection.create_index(
            [("pinned", pymongo.DESCENDING), ("liked", pymongo.DESCENDING)],
            name="IsPinnedOrLiked",
        )
    if ChatDB.Settings.name not in existing:
        if logger:
            logger.info(f"Initialising {ChatDB.Settings.name} collection")
        collection: AsyncIOMotorCollection = await db.create_collection(
            ChatDB.Settings.name
        )
        await collection.create_index(
            [("meta.created", pymongo.DESCENDING)],
            name="CreationTime",
        )
        await collection.create_index(
            [("pinned", pymongo.DESCENDING)], name="IsPinned"
        )
    if KnowledgeBaseDB.Settings.name not in existing:
        if logger:
            logger.info(
                f"Initialising {KnowledgeBaseDB.Settings.name} collection"
            )
        collection: AsyncIOMotorCollection = await db.create_collection(
            KnowledgeBaseDB.Settings.name
        )
        await collection.create_index(
            [("timestamp", pymongo.DESCENDING)],
            name="CreationTime",
        )
        await collection.create_index(
            [("agent", pymongo.DESCENDING)], name="AgentID"
        )
    if RAGConfigDB.Settings.name not in existing:
        if logger:
            logger.info(f"Initialising {RAGConfigDB.Settings.name} collection")
        collection: AsyncIOMotorCollection = await db.create_collection(
            RAGConfigDB.Settings.name
        )
        await collection.create_index(
            [("timestamp", pymongo.DESCENDING)],
            name="CreationTime",
        )
        await collection.create_index(
            [("agent", pymongo.DESCENDING)], name="AgentID"
        )
    if AgentDB.Settings.name not in existing:
        if logger:
            logger.info(f"Initialising {AgentDB.Settings.name} collection")
        collection: AsyncIOMotorCollection = await db.create_collection(
            AgentDB.Settings.name
        )
        await collection.create_index(
            [("meta.created", pymongo.DESCENDING)],
            name="CreationTime",
        )
        await collection.create_index(
            [("agency", pymongo.DESCENDING)],
            name="AgencyID",
        )
    if logger:
        logger.info("Initialised AIBots collections")


async def init_defaults(
    client: AsyncIOMotorClient, logger: Logger | None = None
) -> None:
    """
    Initialises the default values associated with AIBots
    collection

    Args:
        client (AsyncIOMotorClient): AsyncIO Client
        logger (Logger | None): Logger for logging details,
                                defaults to None

    Returns:
        None
    """
    db: AsyncIOMotorDatabase = client[DATABASE_NAME]

    # Insert aibots app config
    if logger:
        logger.info("Inserting AIBots config")
    configs: AsyncIOMotorCollection = db.get_collection("configs")
    if not await configs.find_one({"_id": PRODUCT_ID}):
        await configs.insert_one(
            {
                "_id": PRODUCT_ID,
                "name": "aibots",
                "nous": {
                    "api_key": "nous_prod_e916defb16cb4c972dc31707fda6b1fd_72c0886d80"  # noqa: E501
                },
                "pages": [],
            }
        )

    # Insert default Role values
    if logger:
        logger.info("Inserting default Roles for AIBots")
    roles: AsyncIOMotorCollection = db.get_collection(RoleDB.Settings.name)
    created_time: datetime = datetime.now(timezone.utc)
    if not await roles.find_one({"_id": "f50b63ab9c0a4b1fb14ddee2a4f6e2f9"}):
        await roles.insert_one(
            {
                "_id": "f50b63ab9c0a4b1fb14ddee2a4f6e2f9",
                "name": "AIBots User",
                "description": "Default AIBots role for general "
                "freemium users",
                "default": True,
                "superuser": False,
                "scopes": [
                    # Basic functionality
                    "ui.*:allow",
                    "login.emails:create",
                    "login.sso:create",
                    "login:delete",
                    "login.refresh:create",
                    "login.queries:create,read",
                    "login.users:create",
                    "login.profiles:update",
                    "auth.scopes.format:create",
                    "auth.agencies:read",
                    "events:read,delete",
                    "trackers:create,read",
                    # Features
                    "files:create,read,update,delete",
                    "knowledge_bases:create,read,update,delete",
                    "agents:create,read,update,delete",
                    "agents.approvals:create",
                    "apikeys:create,read,update,delete",
                    "chats:create,read,update,delete",
                    "messages:create,read,update,delete",
                    # Freemium Limits
                ],
                "meta": {
                    "resource_type": "roles",
                    "owner": "ba28efd54f14516faa4665a5d6dcff67",
                    "owner_type": UserType.user,
                    "created": created_time,
                    "last_modified": None,
                    "deleted": None,
                    "archived": None,
                    "location": "https://aibots.gov.sg/latest/roles/f50b63ab9c0a4b1fb14ddee2a4f6e2f9",
                    "version": None,
                },
                "modifications": {
                    "create": {
                        "type": "create",
                        "user_type": UserType.user,
                        "user": "ba28efd54f14516faa4665a5d6dcff67",
                        "details": {},
                        "timestamp": datetime.now(timezone.utc),
                    }
                },
            },
        )
    if not await roles.find_one({"_id": "e0bd11a99ed74360bfd0b4569e7a56bb"}):
        await roles.insert_one(
            {
                "_id": "e0bd11a99ed74360bfd0b4569e7a56bb",
                "name": "Agency Admin",
                "description": "Default AIBots role for Agency Admin users",
                "default": False,
                "superuser": False,
                "scopes": [
                    # Basic functionality
                    "ui.*:allow",
                    "login.*:create,read,update,delete",
                    "auth.scopes.format:create",
                    "events:read,delete",
                    "trackers:create,read",
                    # Features
                    "files:create,read,update,delete",
                    "knowledge_bases:create,read,update,delete",
                    "agents:create,read,update,delete",
                    "agents.approvals:create,read,update",
                    "apikeys:create,read,update,delete",
                    "chats:create,read,update,delete",
                    "messages:create,read,update,delete",
                    "users:create,read,update,delete",
                    "groups:create,read,update,delete",
                    "roles:create,read,update,delete",
                    "auth.scopes:read",
                    "auth.authentications:read,update",
                    "auth.authorizations:update",
                    "auth.permissions:read,update",
                ],
                "meta": {
                    "resource_type": "roles",
                    "owner": "ba28efd54f14516faa4665a5d6dcff67",
                    "owner_type": UserType.user,
                    "created": created_time,
                    "last_modified": None,
                    "deleted": None,
                    "archived": None,
                    "location": "https://aibots.gov.sg/latest/roles/e0bd11a99ed74360bfd0b4569e7a56bb",
                    "version": None,
                },
                "modifications": {
                    "create": {
                        "type": "create",
                        "user_type": UserType.user,
                        "user": "ba28efd54f14516faa4665a5d6dcff67",
                        "details": {},
                        "timestamp": datetime.now(timezone.utc),
                    }
                },
            },
        )
    if not await roles.find_one({"_id": "1bdb052daad54e1b828cd62be05e8fe0"}):
        await roles.insert_one(
            {
                "_id": "1bdb052daad54e1b828cd62be05e8fe0",
                "name": "Agency User",
                "description": "Default AIBots role for onboarded "
                "Agency Users",
                "default": False,
                "superuser": False,
                "scopes": [
                    # Basic functionality
                    "ui.*:allow",
                    "login.emails:create",
                    "login.sso:create",
                    "login:delete",
                    "login.refresh:create",
                    "login.queries:create,read",
                    "login.users:create",
                    "login.profiles:update",
                    "auth.scopes.format:create",
                    "auth.authorizations:update",
                    "events:read,delete",
                    "trackers:create,read",
                    # Features
                    "files:create,read,update,delete",
                    "knowledge_bases:create,read,update,delete",
                    "agents:create,read,update,delete",
                    "agents.approvals:create",
                    "apikeys:create,read,update,delete",
                    "chats:create,read,update,delete",
                    "messages:create,read,update,delete",
                    # Onboarded Agency Limits
                ],
                "meta": {
                    "resource_type": "roles",
                    "owner": "ba28efd54f14516faa4665a5d6dcff67",
                    "owner_type": UserType.user,
                    "created": created_time,
                    "last_modified": None,
                    "deleted": None,
                    "archived": None,
                    "location": "https://aibots.gov.sg/latest/roles/1bdb052daad54e1b828cd62be05e8fe0",
                    "version": None,
                },
                "modifications": {
                    "create": {
                        "type": "create",
                        "user_type": UserType.user,
                        "user": "ba28efd54f14516faa4665a5d6dcff67",
                        "details": {},
                        "timestamp": datetime.now(timezone.utc),
                    }
                },
            },
        )
    if not await roles.find_one({"_id": "bea1828590914df69d7d36cc628ed415"}):
        await roles.insert_one(
            {
                "_id": "bea1828590914df69d7d36cc628ed415",
                "name": "Vendor",
                "description": "Default AIBots role for Vendors",
                "default": False,
                "superuser": False,
                "scopes": [
                    # Basic functionality
                    "ui.*:allow",
                    "login.techpass:create",  # Only allow login via Techpass
                    "login:delete",
                    "login.refresh:create",
                    "login.profiles:update",
                    "auth.scopes.format:create",
                    "trackers:create,read",
                    # Features
                    "chats:create,read,update,delete",
                    "messages:create,read,update,delete",
                    # Vendor Limits
                ],
                "meta": {
                    "resource_type": "roles",
                    "owner": "ba28efd54f14516faa4665a5d6dcff67",
                    "owner_type": UserType.user,
                    "created": created_time,
                    "last_modified": None,
                    "deleted": None,
                    "archived": None,
                    "location": "https://aibots.gov.sg/latest/roles/bea1828590914df69d7d36cc628ed415",
                    "version": None,
                },
                "modifications": {
                    "create": {
                        "type": "create",
                        "user_type": UserType.user,
                        "user": "ba28efd54f14516faa4665a5d6dcff67",
                        "details": {},
                        "timestamp": datetime.now(timezone.utc),
                    }
                },
            },
        )

    # Insert aibots playground agent
    if logger:
        logger.info("Inserting AIBots playground agent")
    agents: AsyncIOMotorCollection = db.get_collection(AgentDB.Settings.name)
    if not await agents.find_one({"_id": DEFAULT_PLAYGROUND_AGENT["_id"]}):
        await agents.insert_one(DEFAULT_PLAYGROUND_AGENT)

    if logger:
        logger.info("Updating AIBots playground agent permissions")
    permissions: AsyncIOMotorCollection = db.get_collection(
        PermissionsDB.Settings.name
    )
    scopes: list[str] = [
        f"agents.{DEFAULT_PLAYGROUND_AGENT['_id']}:read,allow",
        f"chats.{DEFAULT_PLAYGROUND_AGENT['_id']}:create,read,update,delete",
        f"messages.{DEFAULT_PLAYGROUND_AGENT['_id']}:create,read,update,delete",
    ]
    public_permissions: dict[str, Any] | None = await permissions.find_one(
        {"item": "*", "type": "all"}
    )
    if not public_permissions:
        await permissions.insert_one(
            {"item": "*", "type": "all", "scopes": scopes, "groups": []}
        )
    else:
        if not all(s in public_permissions["scopes"] for s in scopes):
            await permissions.update_one(
                {"item": "*", "type": "all"},
                {"$push": {"scopes": {"$each": scopes}}},
            )

    public_permissions: dict[str, Any] | None = await permissions.find_one(
        {"item": "*", "type": "all"}
    )
    if not public_permissions:
        await permissions.insert_one(
            {"item": "*", "type": "all", "scopes": scopes, "groups": []}
        )
    else:
        if not all(s in public_permissions["scopes"] for s in scopes):
            await permissions.update_one(
                {"item": "*", "type": "all"},
                {"$push": {"scopes": {"$each": scopes}}},
            )
    # insert API key:
    if logger:
        logger.info("Inserting API key for internal usage")
    api_keys: AsyncIOMotorCollection = db.get_collection("api_keys")
    for key in INTERNAL_API_KEYS:
        if not await api_keys.find_one({"_id": key["_id"]}):
            await api_keys.insert_one(key)
