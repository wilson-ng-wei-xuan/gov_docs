from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from time import sleep
from typing import Any, Dict, Optional

import pytest
from pydantic import BaseModel, ConfigDict, field_validator

__all__ = ["PostmanScenario", "get_postman_tests"]


@pytest.fixture(scope="session")
def app_environ():
    return {
        'EMAIL_SEND__BUCKET': 's3-sitez-sharedsvc-471112510129-email',
        'HOST': '0.0.0.0',
        'PROJECT__SECRET': 'secret-sitezapp-aibots-main-api',
        'PROJECT_DB__SECRET': 'secret-sitezdb-aibots-main',
        'CLOUDFRONT__PARAM': 'param-sitezingress-aibots-cloudfront-publickey',
        'ANALYTICS__PATH': 'aibots/',
        'LLMSTACK__PARAM': 'param-sitez-aibots-llmstack',
        'USE_SSL': '1',
        'EMAIL_SEND__PTE_URL': 'https://email.sit.private-api.aibots.gov.sg:443/send',
        'AWS_ID': '471112510129',
        'PROJECT__BUCKET': 's3-sitezapp-aibots-471112510129-project',
        'AWS_REGION': 'ap-southeast-1',
        'PORT': '443',
        'CLOAK__PARAM': 'param-sitez-aibots-cloak',
        'EMAIL_SEND__PATH': 'aibots/',
        'DEBUG': '0',
        'CLOUDFRONT__BUCKET': 's3-sitezingress-aibots-471112510129-cloudfront',
        'EMAIL_SEND__SECRET': 'secret-sitezapp-aibots-smtp-user-no-reply',
        'VECTORDB_OPENSEARCH__NAME': 'aibots-rag-vectordb-opensearch',
        'CLOUDFRONT__SECRET': 'secret-sitezingress-aibots-cloudfront',
        'PROJECT__PUB_URL': 'https://sit.aibots.gov.sg',
        'ANALYTICS__BUCKET': 's3-sitez-sharedsvc-471112510129-analytics',
        'NOUS_API__PTE_URL': 'https://nous-api.sit.private-api.aibots.gov.sg:443',
        'CLOUDFRONT__PUB_URL': 'https://public.sit.aibots.gov.sg:443',
        'COMPONENT': 'aibots-main-api',
        'TAG': os.environ.get('TAG', 'latest'),
        'MAIN_TAG': os.environ.get('MAIN_TAG', 'latest'),
        'ATLAS_REGISTRY': os.environ['ATLAS_REGISTRY'],
        'AWS_ACCESS_ID': os.environ['AWS_ACCESS_ID'],
        'AWS_SECRET_KEY': os.environ['AWS_SECRET_KEY'],
        'AWS_SESSION_TOKEN': os.environ['AWS_SESSION_TOKEN'],
        'SUPERUSERS': json.dumps(['davidtwlee@dsaid.gov.sg']),
        **os.environ,
    }


class PostmanScenario(BaseModel):
    """
    Test Scenario for structuring imports from file

    Attributes:
        name (str): Name of the scenario, defaults to an empty name
        collection (str): Path to collection file, defaults to
                          collection.json
        global_vars (str): Path to global variables file, defaults to
                           globals.json
        environment (str): Path to Postman environment file, defaults
                           to environment.json
    """

    model_config: ConfigDict = ConfigDict(extra="allow")

    name: str = ""
    test_folder: str = ""
    collection: str = "collection.json"
    global_vars: str = "globals.json"
    environment: str = "environment.json"

    @field_validator("name")
    def validate_scenario_name(cls, value: str) -> str:
        """
        Extracts and formats the Scenario name

        Args:
            value (str): Scenario name

        Returns:
            str: Formatted scenario name
        """
        return " ".join(
            [s.capitalize() for s in value.split(".")[0].split("_")]
        )


def data_folder(directory: Path, func_name: str) -> Path:
    """
    Returns the test data folder where the current function
    is being executed

    Args:
        directory (Path): Path to directory
        func_name (str): Name of test function

    Returns:
        Path: Folder path of test data
    """
    return directory / func_name


def get_postman_tests(
        directory: Path, func_name: str, api_version: Optional[str] = None
) -> PostmanScenario:
    """
    Loads a postman test scenario

    Args:
        directory (Path): Path to test directory
        func_name (str): Name of test function
        api_version (Optional[str]): API version, defaults to None

    Returns:
        PostmanScenario: Postman scenario loaded
    """

    if api_version:
        scenario_file: Path = (
                directory / "version" / api_version / func_name / "scenario.json"
        )
    else:
        scenario_file: Path = directory / func_name / "scenario.json"
    if scenario_file.exists():
        with scenario_file.open() as f:
            return PostmanScenario(
                name=func_name,
                test_folder=scenario_file.parent.as_posix(),
                **json.load(f),
            )
    else:
        return PostmanScenario(
            name=func_name, test_folder=scenario_file.parent.as_posix()
        )


@pytest.fixture(scope="function")
def postman_env(request, app_environ):
    os.chdir(request.fspath.dirname)
    subprocess.run(shlex.split("docker compose up -d"), env=app_environ)
    sleep(0.25)
    yield
    subprocess.run(shlex.split("docker compose down -v"), env=app_environ)
    os.chdir(request.config.invocation_params.dir)


def pytest_generate_tests(metafunc: pytest.Metafunc):
    pm_scenario = get_postman_tests(
        metafunc.definition.path.parent,
        metafunc.definition.name,
        (
            metafunc.cls.api_version
            if hasattr(metafunc.cls, "api_version")
            else None
        ),
    )
    details: Dict[str, Any] = pm_scenario.model_dump(exclude={"name"})
    metafunc.parametrize(
        argnames=list(details.keys()),
        argvalues=[list(details.values())],
        ids=[pm_scenario.name],
        scope="function",
    )
