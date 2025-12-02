from logging import INFO, getLogger

from motor.motor_asyncio import AsyncIOMotorClient

from aibots.constants import DATABASE_NAME
from agents.mongo import init_file_collections


class TestInitFileCollections:

    async def test_init_file_collections_collections_created(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_file_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 2
        assert caplog.records[0].message == f"Initialising files collection"
        assert caplog.records[1].message == f"Initialised files collection"

        # Check that collection and indexes were properly created
        assert all(i in ['files'] for i in list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['files'].list_indexes())) == ['_id_', 'CreationTime']

    async def test_init_file_collections_multiple_inits(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_file_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 2
        assert caplog.records[0].message == f"Initialising files collection"
        assert caplog.records[1].message == f"Initialised files collection"

        # Check that collection and indexes were properly created
        assert all(i in ['files'] for i in list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['files'].list_indexes())) == ['_id_', 'CreationTime']

        with caplog.at_level(INFO, "atlas"):
            await init_file_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 3
        assert caplog.records[0].message == f"Initialising files collection"
        assert caplog.records[1].message == f"Initialised files collection"
        assert caplog.records[2].message == f"Initialised files collection"
