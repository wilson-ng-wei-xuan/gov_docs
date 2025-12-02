from __future__ import annotations

from logging import Logger

from aibots.constants import DATABASE_NAME, PRODUCT_ID
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
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
