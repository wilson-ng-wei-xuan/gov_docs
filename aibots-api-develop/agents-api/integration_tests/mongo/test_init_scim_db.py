from logging import INFO, getLogger

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from aibots.constants import DATABASE_NAME
from agents.constants import DEFAULT_GROUPS
from agents.models import ScimGroupDB
from agents.mongo import init_scim_collections, init_scim_defaults


class TestInitScimCollections:

    async def test_init_scim_collections_collections_created(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_scim_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 3
        assert caplog.records[0].message == f"Initialising users collection"
        assert caplog.records[1].message == f"Initialising groups collection"
        assert caplog.records[2].message == f"Initialised SCIM collections"

        # Check that collection and indexes were properly created
        assert all(i in ['users', 'groups'] for i in list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['users'].list_indexes())) == ['_id_', 'CreationTime', 'AllowedUsersByAgency']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['groups'].list_indexes())) == ['_id_', 'CreationTime', 'AllowedDomains']

    async def test_init_scim_collections_multiple_inits(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_scim_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 3
        assert caplog.records[0].message == f"Initialising users collection"
        assert caplog.records[1].message == f"Initialising groups collection"
        assert caplog.records[2].message == f"Initialised SCIM collections"

        # Check that collection and indexes were properly created
        assert all(i in ['users', 'groups'] for i in list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['users'].list_indexes())) == ['_id_', 'CreationTime', 'AllowedUsersByAgency']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['groups'].list_indexes())) == ['_id_', 'CreationTime', 'AllowedDomains']

        with caplog.at_level(INFO, "atlas"):
            await init_scim_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 4
        assert caplog.records[0].message == f"Initialising users collection"
        assert caplog.records[1].message == f"Initialising groups collection"
        assert caplog.records[2].message == f"Initialised SCIM collections"
        assert caplog.records[3].message == f"Initialised SCIM collections"


class TestInitScimDefaults:

    async def test_init_scim_defaults_defaults_created(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_scim_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 2
        assert caplog.records[0].message == f"Inserting default Groups"
        assert caplog.records[1].message == f"Inserted default Groups"

        # Check that data was properly inserted
        groups = list(mongo[DATABASE_NAME]['groups'].find({}))
        assert len(groups) == 146
        assert list(map(lambda x: (x['_id'], x['display_name']), groups)) == [
            (g['_id'], g['display_name']) for g in DEFAULT_GROUPS
        ]

    async def test_init_scim_defaults_multiple_inits(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_scim_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 2
        assert caplog.records[0].message == f"Inserting default Groups"
        assert caplog.records[1].message == f"Inserted default Groups"

        # Check that data was properly inserted
        groups = list(mongo[DATABASE_NAME]['groups'].find({}))
        assert len(groups) == 146
        assert list(map(lambda x: (x['_id'], x['display_name']), groups)) == [
            (g['_id'], g['display_name']) for g in DEFAULT_GROUPS
        ]

        with caplog.at_level(INFO, "atlas"):
            await init_scim_defaults(client, logger)
            await init_scim_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 6
        assert caplog.records[0].message == f"Inserting default Groups"
        assert caplog.records[1].message == f"Inserted default Groups"
        assert caplog.records[2].message == f"Inserting default Groups"
        assert caplog.records[3].message == f"Inserted default Groups"
        assert caplog.records[4].message == f"Inserting default Groups"
        assert caplog.records[5].message == f"Inserted default Groups"

    async def test_init_defaults_retrieval_with_beanie(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_scim_defaults(client, logger)

        await init_beanie(database=client[DATABASE_NAME], document_models=[ScimGroupDB])

        group = await ScimGroupDB.find_one({"_id": "7e69e6e9bff251b0946283604ea31786"})

        assert group.display_name == "Yellow Ribbon Singapore (YRSG)"
        assert group.atlas_extensions.agency == "yrsg"
