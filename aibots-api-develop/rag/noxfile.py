import uuid
from contextlib import contextmanager
from datetime import datetime
from os import environ, chdir, listdir
from pathlib import Path
from zoneinfo import ZoneInfo

import nox_poetry

IGNORED = ["__pycache__", ".pytest_cache", ".nox",]
AIBOTS_PACKAGE = Path('../aibots').resolve()
STAGES = [i for i in listdir() if Path(i).is_dir() and i not in IGNORED]
COMPONENTS = {
    s: [
        i for i in listdir(Path(f"./{s}").resolve())
        if Path(f"{s}/{i}").is_dir()
           and any(Path(f"{s}/{i}").iterdir())
    ]
    for s in STAGES
}


@contextmanager
def run_component(component):
    original_dir, path = Path.cwd(), Path(component)
    chdir(path.absolute())
    print(
        f"Switching to {component} in "
        f"directory {path.absolute()}"
    )
    yield path
    chdir(original_dir.absolute())


@nox_poetry.session(tags=["dev", "lint"], python=False)
def lint(session: nox_poetry.Session):
    """
    Runs formatters and linters on the code based on
    the configurations stored in the pyproject.toml

    Args:
        session (nox_poetry.Session): Nox session
    """
    print(f"Running formatters and linters for {COMPONENTS}")
    for stage, components in COMPONENTS.items():
        for component in components:
            with run_component(f"{stage}/{component}"):
                print(f"Running formatters and linters for component {stage}/{component}")
                session.run("ruff", "format", ".")
                session.run("ruff", "check", ".", "--show-fixes", "--fix")


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
    for stage, components in COMPONENTS.items():
        for component in components:
            with run_component(f"{stage}/{component}"):
                print(f"Running formatters and linters for component {stage}/{component}")
                session.install("ruff")
                session.run("ruff", "format", ".", "--check", "--diff")
                session.run("ruff", "check", ".", "--show-fixes")


@nox_poetry.session(tags=["dev", "update"], python=False)
def poetry_lock(session: nox_poetry.Session):
    """
    Updates the poetry.lock files

    Args:
        session (nox_poetry.Session): Nox session
    """
    print(f"Updating poetry.lock files for {COMPONENTS}")
    for stage, components in COMPONENTS.items():
        for component in components:
            with run_component(f"{stage}/{component}"):
                session.run("poetry", "lock", "--no-update", external=True)


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
    print(f"Running unittests for {COMPONENTS}")
    for stage, components in COMPONENTS.items():
        for component in components:
            with run_component(f"{stage}/{component}"):
                print(f"Running unittests for {stage}/{component}")

                path: Path = Path("noxfile.py")
                if not (path.exists() and path.is_file()):
                    print("No nox runner")
                    continue

                session.run("nox", "-s", unittests.__name__, external=True)


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
    atlas_registry: str = environ.get(
        "ATLAS_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/",
    )
    moonshot_registry: str = environ.get(
        "MOONSHOT_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/moonshot/",
    )

    print(f"Running integration tests for {COMPONENTS}")
    for stage, components in COMPONENTS.items():
        for component in components:
            with run_component(f"{stage}/{component}"):
                print(f"Running integration tests for {stage}/{component}")

                path: Path = Path("noxfile.py")
                if not (path.exists() and path.is_file()):
                    print("No nox runner")
                    continue

                session.run(
                    "nox", "-s", integration_tests.__name__,
                    env={
                        **environ,
                        "REGISTRY": "",
                        "ATLAS_REGISTRY": atlas_registry,
                        "MOONSHOT_REGISTRY": moonshot_registry,
                    },
                    external=True,
                )


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

    build_docker_image(session)

    atlas_registry: str = environ.get(
        "ATLAS_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/",
    )
    moonshot_registry: str = environ.get(
        "MOONSHOT_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/moonshot/",
    )

    print(f"Running postman tests for {COMPONENTS}")
    for stage, components in COMPONENTS.items():
        for component in components:
            with run_component(f"{stage}/{component}"):
                print(f"Running postman tests for {stage}/{component}")

                path: Path = Path("noxfile.py")
                if not (path.exists() and path.is_file()):
                    print("No nox runner")
                    continue

                session.run(
                    "nox", "-s", postman_tests.__name__,
                    env={
                        **environ,
                        "REGISTRY": "",
                        "ATLAS_REGISTRY": atlas_registry,
                        "MOONSHOT_REGISTRY": moonshot_registry,
                    },
                    external=True,
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


@nox_poetry.session(tags=["run", "start", "dev"], python=False)
def start_dev_env(session: nox_poetry.Session):
    """
    Runs the dev environment

    Args:
        session (nox_poetry.Session): Nox session
    """
    login_docker(session)
    if len(session.posargs) >= 3:
        stage, component, compose = session.posargs
    else:
        stage, component = session.posargs
        compose = "compose.test.yaml"
    with run_component(f"{stage}/{component}"):
        print(f"Running dev environment for {stage}/{component}")

        path: Path = Path("noxfile.py")
        if not (path.exists() and path.is_file()):
            print("No nox runner")

        session.run(
            "nox", "-s", start_dev_env.__name__, "--", compose,
            env={**environ},
            external=True,
        )


@nox_poetry.session(tags=["run", "stop", "dev"], python=False)
def stop_dev_env(session: nox_poetry.Session):
    """
    Stops the dev environment

    Args:
        session (nox_poetry.Session): Nox session
    """
    login_docker(session)
    if len(session.posargs) >= 3:
        stage, component, compose = session.posargs
    else:
        stage, component = session.posargs
        compose = "compose.test.yaml"
    with run_component(f"{stage}/{component}"):
        print(f"Stopping dev environment for {stage}/{component}")

        path: Path = Path("noxfile.py")
        if not (path.exists() and path.is_file()):
            print("No nox runner")

        session.run(
            "nox", "-s", stop_dev_env.__name__, "--", compose,
            env={**environ},
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
    command = ["nox", "-s", build_docker_image.__name__, ]
    if session.posargs:
        command.extend(["--", session.posargs])

    login_docker(session)

    print(f"Build images for {COMPONENTS}")
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
        "VERSION": environ.get("CI_COMMIT_REF_NAME", "latest"),
    }
    print(
        f"Building docker image with the following parameters: {command} {env_vars}"
    )
    session.run(*command, external=True, env=env_vars)
