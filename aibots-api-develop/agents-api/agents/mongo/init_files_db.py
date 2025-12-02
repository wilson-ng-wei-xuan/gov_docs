from __future__ import annotations

from logging import Logger

import pymongo
from aibots.constants import DATABASE_NAME
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from agents.models import FileDB

__all__ = ("init_file_collections",)


async def init_file_collections(
    client: AsyncIOMotorClient, logger: Logger | None = None
) -> None:
    """
    Initialises the attachments DB collections

    Args:
        client (AsyncIOMotorClient): AsyncIO Client
        logger (Logger | None): Logger for logging details,
                                defaults to None

    Returns:
        None
    """
    # TODO: Generalise this
    db: AsyncIOMotorDatabase = client[DATABASE_NAME]
    existing: list[str] = await db.list_collection_names()
    if FileDB.Settings.name not in existing:
        if logger:
            logger.info(f"Initialising {FileDB.Settings.name} collection")
        collection: AsyncIOMotorCollection = await db.create_collection(
            FileDB.Settings.name
        )
        await collection.create_index(
            [("meta.created", pymongo.DESCENDING)],
            name="CreationTime",
        )
    if logger:
        logger.info(f"Initialised {FileDB.Settings.name} collection")
