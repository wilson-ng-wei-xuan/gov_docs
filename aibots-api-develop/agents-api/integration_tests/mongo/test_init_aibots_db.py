from logging import INFO, getLogger

import pytest
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from aibots.constants import PRODUCT_ID, DATABASE_NAME
from agents.models import RoleDB
from agents.mongo import (
    init_permissions_defaults, init_permissions_collections,
    init_collections,
    init_db,
    init_defaults,
)


@pytest.fixture()
def mock_id():
    return "087f7cfad52f4836a5f318a0ba707a83"


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
        assert len(records) == 7
        assert caplog.records[0].message == f"Initialising configs collection"
        assert caplog.records[1].message == f"Initialising messages collection"
        assert caplog.records[2].message == f"Initialising chats collection"
        assert caplog.records[3].message == f"Initialising knowledge_bases collection"
        assert caplog.records[4].message == f"Initialising rag_configs collection"
        assert caplog.records[5].message == f"Initialising agents collection"
        assert caplog.records[6].message == f"Initialised AIBots collections"

        # Check that collection and indexes were properly created
        assert all(i in ['configs', 'messages', 'chats', 'knowledge_bases', 'rag_configs', 'agents'] for i in
                   list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['configs'].list_indexes())) == ['_id_']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['messages'].list_indexes())) == ['_id_', 'ChatID',
                                                                                                   'ModelID',
                                                                                                   'CreationTime',
                                                                                                   'IsPinnedOrLiked']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['chats'].list_indexes())) == ['_id_', 'CreationTime',
                                                                                                'IsPinned']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['knowledge_bases'].list_indexes())) == ['_id_',
                                                                                                          'CreationTime',
                                                                                                          'AgentID']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['rag_configs'].list_indexes())) == ['_id_',
                                                                                                      'CreationTime',
                                                                                                      'AgentID']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['agents'].list_indexes())) == ['_id_', 'CreationTime',
                                                                                                 'AgencyID']

    async def test_init_collections_multiple_inits(self, mongo, caplog, admin_user, admin_password, admin_db):
        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 7
        assert caplog.records[0].message == f"Initialising configs collection"
        assert caplog.records[1].message == f"Initialising messages collection"
        assert caplog.records[2].message == f"Initialising chats collection"
        assert caplog.records[3].message == f"Initialising knowledge_bases collection"
        assert caplog.records[4].message == f"Initialising rag_configs collection"
        assert caplog.records[5].message == f"Initialising agents collection"
        assert caplog.records[6].message == f"Initialised AIBots collections"

        # Check that collection and indexes were properly created
        assert all(i in ['configs', 'messages', 'chats', 'knowledge_bases', 'rag_configs', 'agents'] for i in
                   list(map(lambda x: x['name'], mongo[DATABASE_NAME].list_collections())))
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['configs'].list_indexes())) == ['_id_']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['messages'].list_indexes())) == ['_id_', 'ChatID',
                                                                                                   'ModelID',
                                                                                                   'CreationTime',
                                                                                                   'IsPinnedOrLiked']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['chats'].list_indexes())) == ['_id_', 'CreationTime',
                                                                                                'IsPinned']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['knowledge_bases'].list_indexes())) == ['_id_',
                                                                                                          'CreationTime',
                                                                                                          'AgentID']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['rag_configs'].list_indexes())) == ['_id_',
                                                                                                      'CreationTime',
                                                                                                      'AgentID']
        assert list(map(lambda x: x['name'], mongo[DATABASE_NAME]['agents'].list_indexes())) == ['_id_', 'CreationTime',
                                                                                                 'AgencyID']

        with caplog.at_level(INFO, "atlas"):
            await init_collections(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 8
        assert caplog.records[0].message == f"Initialising configs collection"
        assert caplog.records[1].message == f"Initialising messages collection"
        assert caplog.records[2].message == f"Initialising chats collection"
        assert caplog.records[3].message == f"Initialising knowledge_bases collection"
        assert caplog.records[4].message == f"Initialising rag_configs collection"
        assert caplog.records[5].message == f"Initialising agents collection"
        assert caplog.records[6].message == f"Initialised AIBots collections"
        assert caplog.records[7].message == f"Initialised AIBots collections"


class TestInitDefaults:

    async def test_init_defaults_defaults_created(self, mongo, caplog, admin_user, admin_password, admin_db):
        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]

        assert len(records) == 5
        assert caplog.records[0].message == f"Inserting AIBots config"
        assert caplog.records[1].message == f"Inserting default Roles for AIBots"
        assert caplog.records[2].message == f"Inserting AIBots playground agent"
        assert caplog.records[3].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[4].message == f"Inserting API key for internal usage"
        # Check that data was properly inserted
        configs = list(mongo[DATABASE_NAME]['configs'].find({}))
        assert len(configs) == 1
        assert list(map(lambda x: (x['_id'], x['name']), configs)) == [
            (PRODUCT_ID, 'aibots'),
        ]
        roles = list(mongo[DATABASE_NAME]['roles'].find({}))
        assert len(roles) == 4
        assert list(map(lambda x: (x['name'], x['superuser']), roles)) == [
            ('AIBots User', False),
            ('Agency Admin', False),
            ('Agency User', False),
            ('Vendor', False),
        ]
        permissions = list(mongo[DATABASE_NAME]['permissions'].find({}))
        assert len(permissions) == 1
        assert list(map(lambda x: (x['item'], x['type'], x['scopes']), permissions)) == [
            ('*', 'all', [
                'agents.804885b4423e485cb21592c7dfa8baa8:read,allow',
                'chats.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete',
                'messages.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete'
            ])
        ]

    async def test_init_defaults_defaults_created_after_init_permissions_run(self, mongo, caplog, admin_user,
                                                                             admin_password, admin_db):
        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_permissions_collections(client, logger)
            await init_permissions_defaults(client, logger)
            await init_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 12
        assert caplog.records[0].message == f"Initialising roles collection"
        assert caplog.records[1].message == f"Initialising permissions collection"
        assert caplog.records[2].message == f"Initialised Permissions collections"
        assert caplog.records[3].message == f"Inserting default Roles"
        assert caplog.records[4].message == f"Inserted default Roles"
        assert caplog.records[5].message == f"Inserting default Permissions"
        assert caplog.records[6].message == f"Inserted default Permissions"
        assert caplog.records[7].message == f"Inserting AIBots config"
        assert caplog.records[8].message == f"Inserting default Roles for AIBots"
        assert caplog.records[9].message == f"Inserting AIBots playground agent"
        assert caplog.records[10].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[11].message == f"Inserting API key for internal usage"

        # Check that data was properly inserted
        configs = list(mongo[DATABASE_NAME]['configs'].find({}))
        assert len(configs) == 1
        assert list(map(lambda x: (x['_id'], x['name']), configs)) == [
            (PRODUCT_ID, 'aibots'),
        ]
        roles = list(mongo[DATABASE_NAME]['roles'].find({}))
        assert len(roles) == 5
        assert list(map(lambda x: (x['name'], x['superuser']), roles)) == [
            ('Superuser', True),
            ('AIBots User', False),
            ('Agency Admin', False),
            ('Agency User', False),
            ('Vendor', False),
        ]
        permissions = list(mongo[DATABASE_NAME]['permissions'].find({}))
        assert len(permissions) == 147
        assert list(map(lambda x: (x['item'], x['type'], x['scopes']), permissions)) == [
            ('*', 'all', [
                'agents.804885b4423e485cb21592c7dfa8baa8:read,allow',
                'chats.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete',
                'messages.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete',

            ]),
            ('3f2757d733d25917be1acf493b206968', 'group', []),
            ('997b6d0054415d2380b56faa823e895b', 'group', []),
            ('1240d5f56a385dca9a3dab457aa8c7a8', 'group', []),
            ('ed835f35412d5fc4aa3429d41a49ef6a', 'group', []),
            ('fd43972a48a257eabb039fe097aaaf4f', 'group', []),
            ('f448e4d086955683bbba2db457a646dd', 'group', []),
            ('cbcec463356d5536ac514c0582c6ee9c', 'group', []),
            ('a28dbdfa1679590498301c9e94264a4d', 'group', []),
            ('5bcfcec634815583824683d86114d0ee', 'group', []),
            ('1dcb609b3b0c59a59d6c9c02453eae93', 'group', []),
            ('a6ea029e7e135deeadde4073171fb491', 'group', []),
            ('f19c961f20175de09ed8c6b7593eca21', 'group', []),
            ('efa4da0c31265719a1248a2befb4fb2c', 'group', []),
            ('7165b0686d245b8b840c7b3516fb44ac', 'group', []),
            ('11a7566c1ea15a2f86a46d473e579d96', 'group', []),
            ('41625dbd13ba522ea47a2190fa9fd6e1', 'group', []),
            ('6ed2a8d24e025f66b780c2ba65e06ee0', 'group', []),
            ('89f0cd8358a25d16a65db198630af038', 'group', []),
            ('bebf2be2fda15e4bab0b3456b1373816', 'group', []),
            ('2380f51c7dcd5182a94ce991b3930b35', 'group', []),
            ('d39c64c0067559f79cbfbd96f2d09080', 'group', []),
            ('41c81673c4d8525fb33f2381d474f0fa', 'group', []),
            ('ce0211bfac835751b17ea106d0d5946c', 'group', []),
            ('26e5b1eadd565651b96901fda3a3380a', 'group', []),
            ('0b81bb361e4a5902be26c3b909b3eafd', 'group', []),
            ('888b7359b3fe5148b6a721bc05b7b69e', 'group', []),
            ('35d53cbcbd245a3ea1ba513e0e6ca3eb', 'group', []),
            ('420f07b005ee5296b209563d4076031b', 'group', []),
            ('5393f855826050c2b09eb35e8bb347d9', 'group', []),
            ('6827e23d95845514b77f59ec7b6126e8', 'group', []),
            ('f3fe92b948c05d4d8c3cbcd0727c520e', 'group', []),
            ('681cd44776ae5d70acea5de4846fea5e', 'group', []),
            ('8fd93c362fd951a29ca892b91d4b47bc', 'group', []),
            ('7ea0f30245d250d381fdebf1fdba6d19', 'group', []),
            ('1d880382bb2757b69c52a8657e8929b9', 'group', []),
            ('701a21b13f2d58d39914e23b01ea0ce7', 'group', []),
            ('65e139b6f759520080fcd95e6e2fd015', 'group', []),
            ('2520505b352e575f8e621062a75b53a3', 'group', []),
            ('63ee8ed40f345296a3ada66c35b2d705', 'group', []),
            ('a7cf08fe147b5fafaa7f19162c334950', 'group', []),
            ('b24bb4946ffa5e9abae772e223adac49', 'group', []),
            ('f891c5b724fb5f8aa2243dbe8436b3fd', 'group', []),
            ('b12467fb69c457e2a6987db96f32bcb6', 'group', []),
            ('df9076925bd65713ac19f8d5c41ce87a', 'group', []),
            ('cb41d1699e485ad58cb07823a4dadf9e', 'group', []),
            ('78c8a5598ce85c9295b15e8b73e516ee', 'group', []),
            ('ce7cd528581957a398c80fa1c67fb0f2', 'group', []),
            ('d4a5c3fd90475820ac8179aafc7ceabf', 'group', []),
            ('e0dd531972c45dd0ae708032db3b1cf4', 'group', []),
            ('45479ce336025e1c8974ef75a9af34be', 'group', []),
            ('f8277df18ca95fec88c1c35e8bda1d69', 'group', []),
            ('4808a9e257305cbd91ee6bffe01f87d2', 'group', []),
            ('351533491d2959afa55113b31d74b0e8', 'group', []),
            ('704653a9f2ab59a99c26777010d8f3c8', 'group', []),
            ('6adaf2ff70db5279980fbcb1fbc26bbb', 'group', []),
            ('47b9af6659ca5426bb50bb4f6bbbce3a', 'group', []),
            ('eff07856f1775521a1eebd20374ddcbe', 'group', []),
            ('3233b4d0d5d05c9fbae7b19358a834ac', 'group', []),
            ('34daffd8823e54f8a40d4208ca6a0701', 'group', []),
            ('2e769c9fdf785a55b0adc24bffd7e0d0', 'group', []),
            ('ab571246fbf15014a628be124cff9bdd', 'group', []),
            ('c40e38a67a325b3caab705477d8b0186', 'group', []),
            ('955169678bcc5a34a5df12726f514547', 'group', []),
            ('ac06602d6e8a51a1a145df42bb90f7ea', 'group', []),
            ('2b976a4d7e3d5b8bb9b5ba27dd62a655', 'group', []),
            ('1ccd42c581cd537e8bc569338eb8688a', 'group', []),
            ('74a6ad8e9b0f594ab05f4c1c2430e42b', 'group', []),
            ('35fd608a21d659b491b9ef8e62f7b437', 'group', []),
            ('35f3d1f339ce53d5985f92188fa910e2', 'group', []),
            ('92128bca16a256f48b8419c9d33d6737', 'group', []),
            ('2dd5275a4bac511189328a8991b3a44e', 'group', []),
            ('57451a92ec26570295941a4975395e15', 'group', []),
            ('5acd221933c256e29a1fe401a1f488e0', 'group', []),
            ('afb7b352f25a5e959795964df1c603fe', 'group', []),
            ('3e0d8e4fa83d5a449f947948c63f17a6', 'group', []),
            ('3ae7c655cbb75b01979940cb4a5b8be0', 'group', []),
            ('fccc4beb5cc151f999996a6ad57d5a15', 'group', []),
            ('f6cf68c86c3e5e74b569a1670365cd7f', 'group', []),
            ('73ce8eed6fb65f6cb089c41a211302b7', 'group', []),
            ('0647444514245049946bc74be3cb5e50', 'group', []),
            ('f46c3fd10d7f59faaf127f925ccac5f5', 'group', []),
            ('5ceadb2b7a3d5291b824c2d82b90fa66', 'group', []),
            ('2b7e1c4c08d55ad789c2947c04ebeaad', 'group', []),
            ('8a863d0cf2ce5b1080548eab838b3167', 'group', []),
            ('b3d6f44a85215f02af07dfb63aa6e902', 'group', []),
            ('8989d26815b5561abd8db20b808d5b4b', 'group', []),
            ('099be511eb3958b5b3e33dc4679c6f86', 'group', []),
            ('8f229344be405551b48d5c7d44d2db9b', 'group', []),
            ('70da339e57225895b14ec73aa3fc1867', 'group', []),
            ('f8cfd51177cd50b7abeb524fb62cddce', 'group', []),
            ('7bb1fa0d9a7e5315838fedd7dd8bf94f', 'group', []),
            ('2fefc3105c835bdaab1b1294b6114ecf', 'group', []),
            ('c520085c7aeb55d0adf9fde985dfe8cc', 'group', []),
            ('b5bbd303da78518aae446538c53dd4ff', 'group', []),
            ('d41998e24a1f5c6491c2064e2e3380a8', 'group', []),
            ('0f85810e5df15e1d9e2d4a4b15a3e67e', 'group', []),
            ('6aa208e6c4b05fe78a591c8b8dcddffb', 'group', []),
            ('ce8e0f47a77653f1993292431548f363', 'group', []),
            ('d8f391fb40e45ad1b149bc0cc0989e4f', 'group', []),
            ('08e961b8ba0c54c2a5c2b69c8a83c8cc', 'group', []),
            ('dd1544c900f85701b06250817c79e704', 'group', []),
            ('ffceedfbcf445c96aa081b5613faf81b', 'group', []),
            ('58f647763e0859a89f82d8dac6a866c3', 'group', []),
            ('7e69e6e9bff251b0946283604ea31786', 'group', []),
            ('626357a3c51e53d39bbcdbf51500a91b', 'group', []),
            ('5c6a7cedaa975879b98c478fec386201', 'group', []),
            ('5915c20e108c53d681979ffe36834a7c', 'group', []),
            ('e9851c1e507a5f8a9c355400293a183a', 'group', []),
            ('38f7c90fcc0d515786602cdeaa4e47cc', 'group', []),
            ('cb67de7527925a56b1b41180a11458fb', 'group', []),
            ('4023af03bc925584a2c28dd8a4171a33', 'group', []),
            ('dfbb14dd4205523eaece4aed91c7ed02', 'group', []),
            ('d28d8f8f2c935beb8132447b6e52bedc', 'group', []),
            ('867ae5933af15fbdad843f1b801f6ead', 'group', []),
            ('e281966371d153fa894cfc1d9b9d01cb', 'group', []),
            ('aabfb4b0ea6e5bfdacd1378c87b5c3ba', 'group', []),
            ('07dc089b3823567590af9febbab249a9', 'group', []),
            ('aebe8fa9680950c298599ee20831a8da', 'group', []),
            ('1900227e133254d7b26e9b52a975d5fc', 'group', []),
            ('f6f323d8c62656f8aa79138b29e40a44', 'group', []),
            ('324ddd0bd3905963bd3c198cfb465a14', 'group', []),
            ('47e9139fe637576199804fd7d4b704b3', 'group', []),
            ('71223effca455e59bf7011753b8fd18a', 'group', []),
            ('59e42ced55815c98b19a2ac80634fdcb', 'group', []),
            ('9712cecbd5c15310b5f6b9dfe963abe4', 'group', []),
            ('ed21ff5e9aeb5143ab117fceead1a511', 'group', []),
            ('0b11fa1aee0c5ce7b5c32d8fefeccb35', 'group', []),
            ('af354758d0b05c7eb8e004d5d7fa6371', 'group', []),
            ('da2e67bde9eb50eeb5237c92958f0c8b', 'group', []),

            ('1dfd8f2f064c5c3ababd996011e164d9', 'group', []),
            ('80d93c9357aa5e62bc0f47808307cf6b', 'group', []),
            ('65064af5c7f4549cbb838ba757eff26a', 'group', []),
            ('7a3b6df3f12c52b9abdfcc11f7695d0d', 'group', []),
            ('9474bfe0cfa15599942fe0af77344a8a', 'group', []),
            ('3f9cb707832a5839abf004da52afe220', 'group', []),
            ('4f922859bbec5f0a84f77901d0e445e9', 'group', []),
            ('c72f78561fe258a2bbc64d52e0c60d37', 'group', []),
            ('7b2ba4d6a7505492a64e579822cbb92e', 'group', []),
            ('94ad20b5abe55b01aa1642774b13c335', 'group', []),
            ('0d5f2856ff575e0e8b2ad5ad8a4ff749', 'group', []),
            ('7c87901beef2535f9f13a11d7692109e', 'group', []),
            ('23064a9ebadd5bf6957303e01a5be12c', 'group', []),
            ('8629d9c286ca564b8598530fc90a1636', 'group', []),
            ('204b20306a9456d0bdf3000f39b46e42', 'group', []),
            ('0d99d0c485ec5150baa9914a9bfd5b9a', 'group', []),
            ('0456d2ee8c23539f88b59fcdebb6c56c', 'group', [])
        ]

    async def test_init_defaults_multiple_inits(self, mongo, caplog, admin_user, admin_password, admin_db):
        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 5
        assert caplog.records[0].message == f"Inserting AIBots config"
        assert caplog.records[1].message == f"Inserting default Roles for AIBots"
        assert caplog.records[2].message == f"Inserting AIBots playground agent"
        assert caplog.records[3].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[4].message == f"Inserting API key for internal usage"

        # Check that data was properly inserted
        configs = list(mongo[DATABASE_NAME]['configs'].find({}))
        assert len(configs) == 1
        assert list(map(lambda x: (x['_id'], x['name']), configs)) == [
            (PRODUCT_ID, 'aibots'),
        ]
        roles = list(mongo[DATABASE_NAME]['roles'].find({}))
        assert len(roles) == 4
        assert list(map(lambda x: (x['name'], x['superuser']), roles)) == [
            ('AIBots User', False),
            ('Agency Admin', False),
            ('Agency User', False),
            ('Vendor', False),
        ]
        permissions = list(mongo[DATABASE_NAME]['permissions'].find({}))
        assert len(permissions) == 1
        assert list(map(lambda x: (x['item'], x['type'], x['scopes']), permissions)) == [
            ('*', 'all', [
                'agents.804885b4423e485cb21592c7dfa8baa8:read,allow',
                'chats.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete',
                'messages.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete'
            ])
        ]

        with caplog.at_level(INFO, "atlas"):
            await init_defaults(client, logger)
            await init_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 15
        assert caplog.records[0].message == f"Inserting AIBots config"
        assert caplog.records[1].message == f"Inserting default Roles for AIBots"
        assert caplog.records[2].message == f"Inserting AIBots playground agent"
        assert caplog.records[3].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[4].message == f"Inserting API key for internal usage"
        assert caplog.records[5].message == f"Inserting AIBots config"
        assert caplog.records[6].message == f"Inserting default Roles for AIBots"
        assert caplog.records[7].message == f"Inserting AIBots playground agent"
        assert caplog.records[8].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[9].message == f"Inserting API key for internal usage"
        assert caplog.records[10].message == f"Inserting AIBots config"
        assert caplog.records[11].message == f"Inserting default Roles for AIBots"
        assert caplog.records[12].message == f"Inserting AIBots playground agent"
        assert caplog.records[13].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[14].message == f"Inserting API key for internal usage"

    async def test_init_defaults_aib_523_public_permissions_not_overwritten(
            self, mongo, caplog, admin_user, admin_password, admin_db, mock_id
    ):
        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 5
        assert caplog.records[0].message == f"Inserting AIBots config"
        assert caplog.records[1].message == f"Inserting default Roles for AIBots"
        assert caplog.records[2].message == f"Inserting AIBots playground agent"
        assert caplog.records[3].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[4].message == f"Inserting API key for internal usage"

        # Check that data was properly inserted
        configs = list(mongo[DATABASE_NAME]['configs'].find({}))
        assert len(configs) == 1
        assert list(map(lambda x: (x['_id'], x['name']), configs)) == [
            (PRODUCT_ID, 'aibots'),
        ]
        roles = list(mongo[DATABASE_NAME]['roles'].find({}))
        assert len(roles) == 4
        assert list(map(lambda x: (x['name'], x['superuser']), roles)) == [
            ('AIBots User', False),
            ('Agency Admin', False),
            ('Agency User', False),
            ('Vendor', False),
        ]
        permissions = list(mongo[DATABASE_NAME]['permissions'].find({}))
        assert len(permissions) == 1
        assert list(map(lambda x: (x['item'], x['type'], x['scopes']), permissions)) == [
            ('*', 'all', [
                'agents.804885b4423e485cb21592c7dfa8baa8:read,allow',
                'chats.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete',
                'messages.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete'
            ])
        ]

        mongo[DATABASE_NAME]['permissions'].update_one(
            {"item": "*", "type": "all"},
            {"$push": {"scopes": {"$each": [
                f"agents.{mock_id}:read,allow",
                f"chats.{mock_id}:create,read,update,delete",
                f"messages.{mock_id}:create,read,update,delete",
            ]}}}
        )

        with caplog.at_level(INFO, "atlas"):
            await init_defaults(client, logger)
            await init_defaults(client, logger)

        records = [r for r in caplog.records if "suitable server" not in r.message]
        assert len(records) == 15
        assert caplog.records[0].message == f"Inserting AIBots config"
        assert caplog.records[1].message == f"Inserting default Roles for AIBots"
        assert caplog.records[2].message == f"Inserting AIBots playground agent"
        assert caplog.records[3].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[4].message == f"Inserting API key for internal usage"
        assert caplog.records[5].message == f"Inserting AIBots config"
        assert caplog.records[6].message == f"Inserting default Roles for AIBots"
        assert caplog.records[7].message == f"Inserting AIBots playground agent"
        assert caplog.records[8].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[9].message == f"Inserting API key for internal usage"
        assert caplog.records[10].message == f"Inserting AIBots config"
        assert caplog.records[11].message == f"Inserting default Roles for AIBots"
        assert caplog.records[12].message == f"Inserting AIBots playground agent"
        assert caplog.records[13].message == f"Updating AIBots playground agent permissions"
        assert caplog.records[14].message == f"Inserting API key for internal usage"

        permissions = list(mongo[DATABASE_NAME]['permissions'].find({}))
        assert len(permissions) == 1
        assert list(map(lambda x: (x['item'], x['type'], x['scopes']), permissions)) == [
            ('*', 'all', [
                'agents.804885b4423e485cb21592c7dfa8baa8:read,allow',
                'chats.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete',
                'messages.804885b4423e485cb21592c7dfa8baa8:create,read,update,delete',
                f"agents.{mock_id}:read,allow",
                f"chats.{mock_id}:create,read,update,delete",
                f"messages.{mock_id}:create,read,update,delete",
            ])
        ]

    async def test_init_defaults_retrieval_with_beanie(self, mongo, caplog, admin_user, admin_password, admin_db):
        client = AsyncIOMotorClient(username=admin_user, password=admin_password, authSource=admin_db)
        logger = getLogger("atlas")

        with caplog.at_level(INFO, "atlas"):
            await init_defaults(client, logger)

        await init_beanie(database=client[DATABASE_NAME], document_models=[RoleDB])

        role = await RoleDB.find_one({"_id": "f50b63ab9c0a4b1fb14ddee2a4f6e2f9"})

        assert role.name == "AIBots User"
        assert role.description == "Default AIBots role for general freemium users"
