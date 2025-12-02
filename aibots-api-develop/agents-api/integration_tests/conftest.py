from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from time import sleep

import pymongo
import pytest

COMPOSE_FILE: str = "compose.yaml"


@pytest.fixture(scope="package")
def testdir(request: pytest.FixtureRequest) -> Path:
    """
    Retrieves the test home directory

    Args:
        request (pytest.FixtureRequest): Request fixture

    Returns:
        Path: Test home directory
    """
    path = Path(request.path).resolve()
    while path.name != "integration_tests":
        path = path.parent
    return path


@pytest.fixture(scope="function")
def mongo(request: pytest.FixtureRequest, admin_user, admin_password):
    os.chdir(request.fspath.dirname)
    subprocess.run(
        shlex.split("docker compose up -d"),
        env={
            **os.environ,
            "ATLAS_REGISTRY": os.environ.get("ATLAS_REGISTRY", ""),
            "MOONSHOT_REGISTRY": os.environ.get("MOONSHOT_REGISTRY", ""),
        },
    )
    sleep(0.25)
    yield pymongo.MongoClient(username=admin_user, password=admin_password)
    subprocess.run(
        shlex.split("docker compose down -v"),
        env={
            **os.environ,
            "ATLAS_REGISTRY": os.environ.get("ATLAS_REGISTRY", ""),
            "MOONSHOT_REGISTRY": os.environ.get("MOONSHOT_REGISTRY", ""),
        },
    )
    os.chdir(request.config.invocation_params.dir)


@pytest.fixture(scope="function")
def admin_user():
    return os.environ.get("DB_USER", "admin")


@pytest.fixture(scope="function")
def admin_password():
    return os.environ.get("DB_PASSWORD", "dsa1d-st")


@pytest.fixture(scope="function")
def admin_db():
    return os.environ.get("ATLAS_ADMIN_DB", "admin")


@pytest.fixture(scope="function")
def user():
    return "hello_world"


@pytest.fixture(scope="function")
def password():
    return "this_is_a_test"
