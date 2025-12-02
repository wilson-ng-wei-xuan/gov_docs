import json
import os

import pytest
from starlette.testclient import TestClient

from aibots.constants import DATABASE_NAME
from agents.models import ScimUserDB


@pytest.fixture
def users():
    return [
        {
            "name": "David Lee",
            "role": "Moonshot Admin User",
            "email": "davidtwlee@dsaid.gov.sg",
            "agency": "govtech",
        },
        {
            "name": "Chan Li Shing",
            "role": "Moonshot Admin User",
            "email": "chanlishing@dsaid.gov.sg",
            "agency": "govtech",
        },
        {
            "name": "Vincent Ng",
            "role": "Agency User",
            "email": "vincentng@dsaid.gov.sg",
            "agency": "govtech",
        },
    ]


@pytest.fixture
def users_environ(users):
    os.environ['USERS'] = json.dumps(users)
    yield os.environ
    del os.environ['USERS']


@pytest.fixture
def superusers_environ(mock_environ):
    superusers = ["david_tw_lee@tech.gov.sg"]
    os.environ['SUPERUSERS'] = json.dumps(superusers)
    yield os.environ
    del os.environ['SUPERUSERS']


# class TestAIBotsApp:
#     def test_aibots_app_creation_of_users_via_env_vars(self, users, users_environ, mongo):
#         app = aibots.create_app()
#         with TestClient(app):
#             users = mongo[DATABASE_NAME][UserDB.Settings.name]
#             output = users.find({})
#             assert len(output) == 3
#             for user, test_output in zip(users, output):
#                 assert user["email"] == test_output['email']
#                 assert user["name"] == test_output['name']
#                 assert user["agency"] == test_output['agency']
