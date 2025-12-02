import os
from os import environ
from pathlib import Path

import nox_poetry


@nox_poetry.session(tags=["dev", "lint"], python=False)
def lint(session: nox_poetry.Session):
    """
    Runs formatters and linters on the code based on
    the configurations stored in the pyproject.toml

    Args:
        session (nox_poetry.Session): Nox session
    """
    print("Running formatters and linters")
    session.run("ruff", "format", ".")
    session.run("ruff", "check", ".", "--show-fixes", "--fix")


@nox_poetry.session(tags=["dev", "install"], python=False)
def py_dependencies(session: nox_poetry.Session):
    """
    Installs all Python dependencies

    Args:
        session (nox_poetry.Session): Nox session
    """
    import certifi

    if "ATLAS_USER" not in environ:
        raise RuntimeError("ATLAS_USER environment variable was not provided")
    if "ATLAS_TOKEN" not in environ:
        raise RuntimeError("ATLAS_TOKEN environment variable was not provided")

    atlas_user: str = environ["ATLAS_USER"]
    atlas_token: str = environ["ATLAS_TOKEN"]

    print("Installing Python dependencies")
    session.run_always(
        "poetry",
        "config",
        "http-basic.atlas",
        atlas_user,
        atlas_token,
        external=True,
    )
    session.run_always(
        "poetry",
        "install",
        external=True,
        env={
            "REQUESTS_CA_BUNDLE": certifi.where(),
            "SSL_CERT_FILE": certifi.where(),
        },
    )


@nox_poetry.session(tags=["dev", "update"], python=False)
def poetry_lock(session: nox_poetry.Session):
    """
    Updates the poetry.lock files

    Args:
        session (nox_poetry.Session): Nox session
    """
    print(f"Updating poetry.lock files for aibots")
    session.run("poetry", "lock", "--no-update", external=True)


@nox_poetry.session(tags=["build"], reuse_venv=True)
def build(session: nox_poetry.Session):
    """
    Builds a full distributable version of Atlas

    Args:
        session (nox_poetry.Session): Nox session
    """
    print(f"Building AIBots library")
    session.run("poetry", "build", external=True)


@nox_poetry.session(tags=["tests", "lint"], reuse_venv=True)
def lint_check(session: nox_poetry.Session):
    """
    Runs formatters and linters based on the
    configurations stored in the pyproject.toml and
    checks if there are any formatting issues

    Args:
        session (nox_poetry.Session): Nox session
    """
    print("Running lint checks")
    session.install("ruff")
    session.run("ruff", "format", ".", "--check", "--diff")
    session.run("ruff", "check", ".", "--show-fixes")


@nox_poetry.session(
    tags=["tests", "unittests"],
    reuse_venv=True,
)
def unittests(session: nox_poetry.Session):
    """
    Runs all Python unittests

    Args:
        session (nox_poetry.Session): Nox session
    """
    py_dependencies(session)

    path: Path = Path("tests")
    if not (path.exists() and path.is_dir()):
        print("No unit tests to run")
        return

    if "GOVTEXT_API_KEY" not in environ:
        raise RuntimeError("GOVTEXT_API_KEY environment variable was not provided")

    print("Running unit tests")
    session.run(
        "coverage",
        "run",
        f"--context={session.name}",
        "-m",
        "pytest",
        path.name,
    )
    session.run("coverage", "report", "-m")
    session.run("coverage", "json")


@nox_poetry.session(
    tags=["tests", "integration"],
    reuse_venv=True,
)
def integration_tests(session: nox_poetry.Session):
    """
    Runs all integration tests

    Args:
        session (nox_poetry.Session): Nox session
    """

    py_dependencies(session)

    path: Path = Path("integration_tests")
    if not (path.exists() and path.is_dir()):
        print("No integration tests to run")
        return

    if "AWS_ACCESS_ID" not in environ:
        raise RuntimeError("AWS_ACCESS_ID environment variable was not provided")
    if "AWS_SECRET_KEY" not in environ:
        raise RuntimeError("AWS_SECRET_KEY environment variable was not provided")

    print("Running integration tests")
    atlas_registry: str = environ.get(
        "ATLAS_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/",
    )
    moonshot_registry: str = environ.get(
        "MOONSHOT_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/moonshot/",
    )
    session.run(
        "coverage",
        "run",
        f"--context={session.name}",
        "-m",
        "pytest",
        path.name,
        env={
            "REGISTRY": "",
            "ATLAS_REGISTRY": atlas_registry,
            "MOONSHOT_REGISTRY": moonshot_registry,
            "AWS_ACCESS_ID": environ['AWS_ACCESS_ID'],
            "AWS_SECRET_KEY": environ['AWS_SECRET_KEY']
        },
    )
    session.run("coverage", "report", "-m")
    session.run("coverage", "json")


@nox_poetry.session(
    tags=["tests", "postman"],
    reuse_venv=True,
)
def postman_tests(session: nox_poetry.Session):
    """
    Runs all Postman tests

    Args:
        session (nox_poetry.Session): Nox session
    """

    py_dependencies(session)
    build_docker_image(session)

    path: Path = Path("postman_tests")
    if not (path.exists() and path.is_dir()):
        print("No Postman tests to run")
        return

    if "AWS_ACCESS_ID" not in environ:
        raise RuntimeError("AWS_ACCESS_ID environment variable was not provided")
    if "AWS_SECRET_KEY" not in environ:
        raise RuntimeError("AWS_SECRET_KEY environment variable was not provided")

    print("Running postman tests")
    atlas_registry: str = environ.get(
        "ATLAS_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/",
    )
    moonshot_registry: str = environ.get(
        "MOONSHOT_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/moonshot/",
    )
    session.run(
        "pytest",
        path.name,
        env={
            "REGISTRY": "",
            "ATLAS_REGISTRY": atlas_registry,
            "MOONSHOT_REGISTRY": moonshot_registry,
            "AWS_ACCESS_ID": environ['AWS_ACCESS_ID'],
            "AWS_SECRET_KEY": environ['AWS_SECRET_KEY']
        },
    )


@nox_poetry.session(tags=["build"], python=False)
def login_docker(session: nox_poetry.Session):
    """
    This function authenticates the Docker engine
    with the image repository

    Args:
        session (nox_poetry.Session): Nox Session
    """
    if "ATLAS_USER" not in environ:
        raise RuntimeError("ATLAS_USER environment variable was not provided")
    if "ATLAS_TOKEN" not in environ:
        raise RuntimeError("ATLAS_TOKEN environment variable was not provided")

    atlas_user: str = environ["ATLAS_USER"]
    atlas_token: str = environ["ATLAS_TOKEN"]
    atlas_registry: str = environ.get(
        "ATLAS_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/",
    )

    if atlas_registry:
        session.run(
            "docker",
            "login",
            "--username",
            atlas_user,
            "--password",
            atlas_token,
            atlas_registry,
            external=True,
        )


@nox_poetry.session(tags=["build"], reuse_venv=True)
def build(session: nox_poetry.Session):
    """
    Builds a full distributable version of AIBots shared package

    Args:
        session (nox_poetry.Session): Nox session
    """
    print("Building AIBots library")
    session.run("poetry", "build", external=True)


@nox_poetry.session(tags=["install"], python=False)
def install(session: nox_poetry.Session):
    """
    Installs a full distributable version of AIBots shared package

    Args:
        session (nox_poetry.Session): Nox session
    """

    from urllib.parse import ParseResult, urlparse

    import certifi

    build(session)

    wheel: Path = list(Path("dist").glob("*.whl"))[0]
    registry: ParseResult = urlparse(session.poetry.poetry.config._config['source'][0]['url'])

    if "ATLAS_USER" not in environ:
        raise RuntimeError("ATLAS_USER environment variable was not provided")
    if "ATLAS_TOKEN" not in environ:
        raise RuntimeError("ATLAS_TOKEN environment variable was not provided")

    print("Installing AIBots library")

    session.run(
        "pip",
        "install",
        "-U",
        "--force-reinstall",
        str(wheel),
        "--extra-index-url",
        f"{registry.scheme}://{environ['ATLAS_USER']}:{environ['ATLAS_TOKEN']}@{registry.netloc}{registry.path}",
        env={
            "REQUESTS_CA_BUNDLE": certifi.where(),
            "SSL_CERT_FILE": certifi.where(),
        },
        external=True,
    )


@nox_poetry.session(tags=["build"], python=False)
def build_docker_image(session: nox_poetry.Session):
    """
    Builds a docker image, accepts docker compose build arguments
    as follows:

    `nox -t build -- --no-cache`

    Args:
        session (nox_poetry.Session): Nox session
    """
    import uuid
    from datetime import datetime
    from os import environ
    from zoneinfo import ZoneInfo

    login_docker(session)

    atlas_tag: str = session.poetry.poetry.config._config["version"]
    command = [
        "docker",
        "compose",
        "-f",
        "compose.build.yaml",
        "build",
    ]
    if session.posargs:
        command.extend(session.posargs)
    env_vars = {
        "ATLAS_TOKEN": environ["ATLAS_TOKEN"],
        "ATLAS_USER": environ["ATLAS_USER"],
        "ATLAS_BASE_IMAGE": environ.get(
            "ATLAS_IMAGE",
            "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/atlas-base",
        ),
        "ATLAS_BASE_IMAGE_TAG": environ.get("ATLAS_BASE_IMAGE_TAG", "latest"),
        "ATLAS_REGISTRY": environ.get(
            "ATLAS_REGISTRY",
            "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/"
        ),
        "GIT_BRANCH": environ.get(
            "CI_COMMIT_BRANCH",
            session.run(
                "git",
                "rev-parse",
                "--abbrev-ref",
                "HEAD",
                external=True,
                silent=True,
            ).strip(),
        ),
        "GIT_COMMIT_HASH": environ.get(
            "CI_COMMIT_REF_SLUG",
            session.run(
                "git", "rev-parse", "HEAD", external=True, silent=True
            ).strip(),
        ),
        "KEY_PASS": environ.get("KEY_PASS", str(uuid.uuid4())),
        "RELEASE_DATE": environ.get(
            "RELEASE_DATE",
            datetime.now(tz=ZoneInfo("Asia/Singapore")).isoformat(),
        ),
        "VERSION": environ.get("CI_COMMIT_REF_NAME", f"v{atlas_tag}"),
    }
    print(
        f"Building docker image with the following parameters: {command} {env_vars}"
    )
    session.run(*command, external=True, env=env_vars)


@nox_poetry.session(tags=["run", "start", "dev"], python=False)
def start_dev_env(session: nox_poetry.Session):
    """
    Runs the dev environment

    Args:
        session (nox_poetry.Session): Nox session
    """
    login_docker(session)
    atlas_registry: str = environ.get(
        "ATLAS_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/",
    )
    moonshot_registry: str = environ.get(
        "MOONSHOT_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/moonshot/",
    )
    if session.posargs:
        compose: str = session.posargs[0]
    else:
        compose: str = "compose.dev.yaml"
    print(f"Running the dev environment")
    session.run(
        "docker",
        "compose",
        "-f",
        compose,
        "up",
        "-d",
        external=True,
        env={
            **environ,
            "ATLAS_REGISTRY": atlas_registry,
            "MOONSHOT_REGISTRY": moonshot_registry
        },
    )


@nox_poetry.session(tags=["run", "stop", "dev"], python=False)
def stop_dev_env(session: nox_poetry.Session):
    """
    Stops the dev environment

    Args:
        session (nox_poetry.Session): Nox session
    """
    login_docker(session)
    atlas_registry: str = environ.get(
        "ATLAS_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/",
    )
    moonshot_registry: str = environ.get(
        "MOONSHOT_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/moonshot/",
    )
    if session.posargs:
        compose: str = session.posargs[0]
    else:
        compose: str = "compose.dev.yaml"
    print(f"Stopping the dev environment")
    session.run(
        "docker",
        "compose",
        "-f",
        compose,
        "down",
        "-v",
        external=True,
        env={
            "ATLAS_REGISTRY": atlas_registry,
            "MOONSHOT_REGISTRY": moonshot_registry
        },
    )


@nox_poetry.session(tags=["dev", "publish"], reuse_venv=True)
def publish(session: nox_poetry.Session):
    """
    Builds a full distributable version of AIBots to the
    package registry at specified URL, requires the following arguments

    1. PyPI Package Registry
    2. User login to package registry
    3. Password to package registry

    `nox -t publish -- https://gitlab.example.com/api/v4/projects/28012/packages/pypi gitlab-ci-token tokenvalue`

    Args:
        session (nox_poetry.Session): Nox session
    """  # noqa: E501
    package_registry: str = session.posargs[0]
    user: str = session.posargs[1]
    password: str = session.posargs[2]

    print(f"Publishing AIBots library to {package_registry}")
    session.install("twine")
    session.run(
        "python",
        "-m",
        "twine",
        "upload",
        "--repository-url",
        package_registry,
        "dist/*",
        env={
            'TWINE_PASSWORD': user,
            'TWINE_USERNAME': password
        },
        external=True
    )
