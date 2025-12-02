from logging import INFO, getLogger

from motor.motor_asyncio import AsyncIOMotorClient

from aibots.constants import PRODUCT_ID, DATABASE_NAME
from chats.mongo import (
    init_collections,
    init_db,
    init_defaults,
)


class TestInitDB:

    def test_init_db_db_initialised(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            init_db(client, logger)

        assert len(caplog.records) == 2
        assert caplog.records[0].message == f"Initialising {DATABASE_NAME} database"
        assert caplog.records[1].message == f"Initialised {DATABASE_NAME} database"

    def test_init_db_db_initialised_multiple_times(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            init_db(client, logger)
            init_db(client, logger)

        assert len(caplog.records) == 4
        assert caplog.records[0].message == f"Initialising {DATABASE_NAME} database"
        assert caplog.records[1].message == f"Initialised {DATABASE_NAME} database"
        assert caplog.records[2].message == f"Initialising {DATABASE_NAME} database"
        assert caplog.records[3].message == f"Initialised {DATABASE_NAME} database"


class TestInitCollections:

    async def test_init_collections_collections_created(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 2
        assert caplog.records[0].message == f"Initialising configs collection"
        assert caplog.records[1].message == f"Initialised AIBots collections"

        # Check that collection and indexes were properly created
        assert all(i in ['configs'] for i in list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['configs'].list_indexes())) == ['_id_']

    async def test_init_collections_multiple_inits(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 2
        assert caplog.records[0].message == f"Initialising configs collection"
        assert caplog.records[1].message == f"Initialised AIBots collections"

        # Check that collection and indexes were properly created
        assert all(i in ['configs'] for i in list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['configs'].list_indexes())) == ['_id_']

        with caplog.at_level(INFO, "atlas"):
            await init_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 3
        assert caplog.records[0].message == f"Initialising configs collection"
        assert caplog.records[1].message == f"Initialised AIBots collections"
        assert caplog.records[2].message == f"Initialised AIBots collections"


class TestInitDefaults:

    async def test_init_defaults_defaults_created(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 1
        assert caplog.records[0].message == f"Inserting AIBots config"

        # Check that data was properly inserted
        configs = list(mongo[DATABASE_NAME]['configs'].find({}))
        assert len(configs) == 1
        assert list(map(lambda x: (x['_id'], x['name']), configs)) == [
            (PRODUCT_ID, 'aibots'),
        ]

    async def test_init_defaults_multiple_inits(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 1
        assert caplog.records[0].message == f"Inserting AIBots config"

        # Check that data was properly inserted
        configs = list(mongo[DATABASE_NAME]['configs'].find({}))
        assert len(configs) == 1
        assert list(map(lambda x: (x['_id'], x['name']), configs)) == [
            (PRODUCT_ID, 'aibots'),
        ]

        with caplog.at_level(INFO, "atlas"):
            await init_defaults(client, logger)
            await init_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 3
        assert caplog.records[0].message == f"Inserting AIBots config"
        assert caplog.records[1].message == f"Inserting AIBots config"
        assert caplog.records[2].message == f"Inserting AIBots config"
