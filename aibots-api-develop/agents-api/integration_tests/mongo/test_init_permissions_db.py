from logging import INFO, getLogger

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from aibots.constants import DATABASE_NAME
from agents.models import PermissionsDB
from agents.mongo import init_permissions_collections, init_permissions_defaults


class TestInitPermissionsCollections:

    async def test_init_permissions_collections_collections_created(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_permissions_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 3
        assert caplog.records[0].message == f"Initialising roles collection"
        assert caplog.records[1].message == f"Initialising permissions collection"
        assert caplog.records[2].message == f"Initialised Permissions collections"

        # Check that collection and indexes were properly created
        assert all(i in ['roles', 'permissions'] for i in list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['roles'].list_indexes())) == ['_id_', 'CreationTime', 'Superuser', 'Default']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['permissions'].list_indexes())) == ['_id_', 'PermissionType']

    async def test_init_permissions_collections_multiple_inits(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_permissions_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 3
        assert caplog.records[0].message == f"Initialising roles collection"
        assert caplog.records[1].message == f"Initialising permissions collection"
        assert caplog.records[2].message == f"Initialised Permissions collections"

        # Check that collection and indexes were properly created
        assert all(i in ['roles', 'permissions'] for i in list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['roles'].list_indexes())) == ['_id_', 'CreationTime', 'Superuser', 'Default']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['permissions'].list_indexes())) == ['_id_', 'PermissionType']

        with caplog.at_level(INFO, "atlas"):
            await init_permissions_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 4
        assert caplog.records[0].message == f"Initialising roles collection"
        assert caplog.records[1].message == f"Initialising permissions collection"
        assert caplog.records[2].message == f"Initialised Permissions collections"
        assert caplog.records[3].message == f"Initialised Permissions collections"


class TestInitPermissionsDefaults:

    async def test_init_permissions_defaults_defaults_created(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_permissions_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 4
        assert caplog.records[0].message == f"Inserting default Roles"
        assert caplog.records[1].message == f"Inserted default Roles"
        assert caplog.records[2].message == f"Inserting default Permissions"
        assert caplog.records[3].message == f"Inserted default Permissions"

        # Check that data was properly inserted
        roles = list(mongo[DATABASE_NAME]['roles'].find({}))
        assert len(roles) == 1
        assert list(map(lambda x: (x['name'], x['superuser']), roles)) == [
            ('Superuser', True),
        ]
        permissions = list(mongo[DATABASE_NAME]['permissions'].find({}))
        assert len(permissions) == 147

    async def test_init_permissions_defaults_multiple_inits(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_permissions_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 4
        assert caplog.records[0].message == f"Inserting default Roles"
        assert caplog.records[1].message == f"Inserted default Roles"
        assert caplog.records[2].message == f"Inserting default Permissions"
        assert caplog.records[3].message == f"Inserted default Permissions"

        # Check that data was properly inserted
        roles = list(mongo[DATABASE_NAME]['roles'].find({}))
        assert len(roles) == 1
        assert list(map(lambda x: (x['name'], x['superuser']), roles)) == [
            ('Superuser', True),
        ]
        permissions = list(mongo[DATABASE_NAME]['permissions'].find({}))
        assert len(permissions) == 147

        with caplog.at_level(INFO, "atlas"):
            await init_permissions_defaults(client, logger)
            await init_permissions_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 12
        assert caplog.records[0].message == f"Inserting default Roles"
        assert caplog.records[1].message == f"Inserted default Roles"
        assert caplog.records[2].message == f"Inserting default Permissions"
        assert caplog.records[3].message == f"Inserted default Permissions"
        assert caplog.records[4].message == f"Inserting default Roles"
        assert caplog.records[5].message == f"Inserted default Roles"
        assert caplog.records[6].message == f"Inserting default Permissions"
        assert caplog.records[7].message == f"Inserted default Permissions"
        assert caplog.records[8].message == f"Inserting default Roles"
        assert caplog.records[9].message == f"Inserted default Roles"
        assert caplog.records[10].message == f"Inserting default Permissions"
        assert caplog.records[11].message == f"Inserted default Permissions"

    async def test_init_permissions_defaults_retrieval_with_beanie(self, mongo, caplog, admin_user, admin_password, admin_db):

        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_permissions_defaults(client, logger)

        await init_beanie(database=client[DATABASE_NAME], document_models=[PermissionsDB])

        permissions = await PermissionsDB.find_one({"item": "*"})

        assert permissions.type == "all"
        assert permissions.scopes == []

        permissions = await PermissionsDB.find_one({"item": "997b6d0054415d2380b56faa823e895b"})

        assert permissions.type == "group"
        assert permissions.scopes == []
