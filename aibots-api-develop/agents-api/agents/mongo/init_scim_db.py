from __future__ import annotations

from logging import Logger

import pymongo
from aibots.constants import DATABASE_NAME
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from agents.constants import DEFAULT_GROUPS
from agents.models import ScimGroupDB, ScimUserDB

__all__ = (
    "init_scim_collections",
    "init_scim_defaults",
)


async def init_scim_collections(
    client: AsyncIOMotorClient, logger: Logger | None = None
) -> None:
    """
    Initialises the SCIM DB collections

    Args:
        client (AsyncIOMotorClient): AsyncIO Client
        logger (Logger | None): Logger for logging details,
                                defaults to None

    Returns:
        None
    """
    db: AsyncIOMotorDatabase = client[DATABASE_NAME]
    existing: list[str] = await db.list_collection_names()

    if ScimUserDB.Settings.name not in existing:
        if logger:
            logger.info(f"Initialising {ScimUserDB.Settings.name} collection")
        collection: AsyncIOMotorCollection = await db.create_collection(
            ScimUserDB.Settings.name
        )
        await collection.create_index(
            [("meta.created", pymongo.DESCENDING)],
            name="CreationTime",
        )
        await collection.create_index(
            [
                ("atlas_extensions.agency", pymongo.DESCENDING),
                ("atlas_extensions.allow", pymongo.DESCENDING),
            ],
            name="AllowedUsersByAgency",
        )
    if ScimGroupDB.Settings.name not in existing:
        if logger:
            logger.info(f"Initialising {ScimGroupDB.Settings.name} collection")
        collection: AsyncIOMotorCollection = await db.create_collection(
            ScimGroupDB.Settings.name
        )
        await collection.create_index(
            [("meta.created", pymongo.DESCENDING)],
            name="CreationTime",
        )
        await collection.create_index(
            [
                ("atlas_extensions.domain", pymongo.DESCENDING),
                ("atlas_extensions.allow", pymongo.DESCENDING),
            ],
            name="AllowedDomains",
        )
    if logger:
        logger.info("Initialised SCIM collections")


async def init_scim_defaults(
    client: AsyncIOMotorClient, logger: Logger | None = None
) -> None:
    """
    Initialises the default values associated with ScimGroups
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
        logger.info("Inserting default Groups")

    groups: AsyncIOMotorCollection = db.get_collection(
        ScimGroupDB.Settings.name
    )
    for group in DEFAULT_GROUPS:
        if not await groups.find_one({"_id": group["_id"]}):
            await groups.insert_one(group)

    if logger:
        logger.info("Inserted default Groups")
