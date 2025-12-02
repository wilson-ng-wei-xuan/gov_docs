from __future__ import annotations

from datetime import datetime
from logging import Logger

import pymongo
from aibots.constants import DATABASE_NAME
from atlas.schemas import UserType, Uuid
from atlas.utils import generate_curr_datetime, generate_uuid
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from agents.constants import DEFAULT_GROUPS
from agents.models import PermissionsDB, RoleDB

__all__ = (
    "init_permissions_collections",
    "init_permissions_defaults",
)


async def init_permissions_collections(
    client: AsyncIOMotorClient, logger: Logger | None = None
) -> None:
    """
    Initialises the Permissions DB collections

    Args:
        client (AsyncIOMotorClient): AsyncIO Client
        logger (Logger | None): Logger for logging details,
                                defaults to None

    Returns:
        None
    """
    db: AsyncIOMotorDatabase = client[DATABASE_NAME]
    existing: list[str] = await db.list_collection_names()

    if RoleDB.Settings.name not in existing:
        if logger:
            logger.info(f"Initialising {RoleDB.Settings.name} collection")
        collection: AsyncIOMotorCollection = await db.create_collection(
            RoleDB.Settings.name
        )
        await collection.create_index(
            [("meta.created", pymongo.DESCENDING)],
            name="CreationTime",
        )
        await collection.create_index(
            [("superuser", pymongo.DESCENDING)],
            name="Superuser",
        )
        await collection.create_index(
            [("default", pymongo.DESCENDING)],
            name="Default",
        )
    if PermissionsDB.Settings.name not in existing:
        if logger:
            logger.info(
                f"Initialising {PermissionsDB.Settings.name} collection"
            )
        collection: AsyncIOMotorCollection = await db.create_collection(
            PermissionsDB.Settings.name
        )
        await collection.create_index(
            [("type", pymongo.DESCENDING)],
            name="PermissionType",
        )
    if logger:
        logger.info("Initialised Permissions collections")


async def init_permissions_defaults(
    client: AsyncIOMotorClient, logger: Logger | None = None
) -> None:
    """
    Initialises the default values associated with the Permissions
    collection

    Args:
        client (AsyncIOMotorClient): AsyncIO Client
        logger (Logger | None): Logger for logging details,
                                defaults to None

    Returns:
        None
    """
    db: AsyncIOMotorDatabase = client[DATABASE_NAME]

    if logger:
        logger.info("Inserting default Roles")

    roles: AsyncIOMotorCollection = db.get_collection(RoleDB.Settings.name)
    if not await roles.find_one({"superuser": True}):
        uuid: Uuid = generate_uuid()
        created_time: datetime = generate_curr_datetime()
        await roles.insert_one(
            {
                "_id": uuid,
                "name": "Superuser",
                "description": "Default role for Superusers",
                "default": False,
                "superuser": True,
                "scopes": ["*"],
                "meta": {
                    "resource_type": "roles",
                    "owner": "ba28efd54f14516faa4665a5d6dcff67",
                    "owner_type": UserType.user,
                    "created": created_time,
                    "last_modified": None,
                    "deleted": None,
                    "archived": None,
                    "location": f"https://aibots.gov.sg/latest/roles/{uuid}",
                    "version": None,
                },
                "modifications": {
                    "create": {
                        "type": "create",
                        "user_type": UserType.user,
                        "user": "ba28efd54f14516faa4665a5d6dcff67",
                        "details": {},
                        "timestamp": created_time,
                    }
                },
            },
        )
    if logger:
        logger.info("Inserted default Roles")

    if logger:
        logger.info("Inserting default Permissions")

    permissions: AsyncIOMotorCollection = db.get_collection(
        PermissionsDB.Settings.name
    )
    if not await permissions.find_one({"item": "*", "type": "all"}):
        await permissions.insert_one(
            {
                "type": "all",
                "item": "*",
                "scopes": [],
                "groups": [],
            }
        )

    # TODO: Add recursive reference to root node in groups field
    for group in DEFAULT_GROUPS:
        if not await permissions.find_one(
            {"item": group["_id"], "type": "group"}
        ):
            await permissions.insert_one(
                {
                    "type": "group",
                    "item": group["_id"],
                    "scopes": [],
                    "groups": [],
                }
            )

    if logger:
        logger.info("Inserted default Permissions")
