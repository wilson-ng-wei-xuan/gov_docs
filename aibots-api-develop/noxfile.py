from contextlib import contextmanager
from os import chdir, environ
from pathlib import Path

import nox_poetry

IMAGE_COMPONENTS = [
    "agents-api",
    "chats-api",
]
RAG_COMPONENTS = ["rag"]
AIBOTS_PACKAGE = ["aibots"]
COMPONENTS = AIBOTS_PACKAGE + IMAGE_COMPONENTS + RAG_COMPONENTS


@contextmanager
def run_component(component):
    original_dir, path = Path.cwd(), Path(component)
    chdir(path.absolute())
    print(f"Switching to {component} in " f"directory {Path('.').absolute()}")
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
    for component in COMPONENTS:
        with run_component(component):
            session.run("nox", "-t", lint.__name__, external=True)


@nox_poetry.session(tags=["dev", "install"], python=False)
def py_dependencies(session: nox_poetry.Session):
    """
    Installs all Python dependencies

    Args:
        session (nox_poetry.Session): Nox session
    """
    print(f"Installing dependencies for {AIBOTS_PACKAGE + IMAGE_COMPONENTS}")
    for component in AIBOTS_PACKAGE + IMAGE_COMPONENTS:
        with run_component(component):
            session.run("nox", "-s", py_dependencies.__name__, external=True)


@nox_poetry.session(tags=["dev", "update"], python=False)
def poetry_lock(session: nox_poetry.Session):
    """
    Updates the poetry.lock files

    Args:
        session (nox_poetry.Session): Nox session
    """
    print(f"Updating poetry.lock files for {COMPONENTS}")
    for component in COMPONENTS:
        with run_component(component):
            session.run("nox", "-s", poetry_lock.__name__, external=True)


@nox_poetry.session(tags=["build"], reuse_venv=True)
def build(session: nox_poetry.Session):
    """
    Builds a full distributable version of Atlas

    Args:
        session (nox_poetry.Session): Nox session
    """
    print(f"Building components {AIBOTS_PACKAGE + IMAGE_COMPONENTS}")
    for component in AIBOTS_PACKAGE + IMAGE_COMPONENTS:
        with run_component(component):
            session.run("nox", "-s", build.__name__, external=True)


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
    for component in COMPONENTS:
        with run_component(component):
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
    for component in COMPONENTS:
        with run_component(component):
            session.run(
                "nox",
                "-s",
                integration_tests.__name__,
                env={
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

    if "AWS_ACCESS_ID" not in environ:
        raise RuntimeError(
            "AWS_ACCESS_ID environment variable was not provided"
        )
    if "AWS_SECRET_KEY" not in environ:
        raise RuntimeError(
            "AWS_SECRET_KEY environment variable was not provided"
        )
    if "AWS_SESSION_TOKEN" not in environ:
        raise RuntimeError(
            "AWS_SESSION_TOKEN environment variable was not provided"
        )

    atlas_registry: str = environ.get(
        "ATLAS_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/atlas/python/atlas/",
    )
    moonshot_registry: str = environ.get(
        "MOONSHOT_REGISTRY",
        "registry.sgts.gitlab-dedicated.com/wog/gvt/dsaid-st/moonshot/",
    )

    print(f"Running postman tests for {IMAGE_COMPONENTS}")
    for component in IMAGE_COMPONENTS:
        with run_component(component):
            session.run(
                "nox",
                "-s",
                postman_tests.__name__,
                env={
                    "REGISTRY": "",
                    "ATLAS_REGISTRY": atlas_registry,
                    "MOONSHOT_REGISTRY": moonshot_registry,
                    "AWS_ACCESS_ID": environ["AWS_ACCESS_ID"],
                    "AWS_SECRET_KEY": environ["AWS_SECRET_KEY"],
                    "AWS_SESSION_TOKEN": environ["AWS_SESSION_TOKEN"],
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
    command = ["nox", "-s", build_docker_image.__name__]
    if session.posargs:
        command.extend(["--", *session.posargs])

    print(f"Build images for {IMAGE_COMPONENTS + RAG_COMPONENTS}")
    for component in IMAGE_COMPONENTS + RAG_COMPONENTS:
        with run_component(component):
            session.run(*command, external=True, env=environ,)


@nox_poetry.session(tags=["run", "start", "dev"], python=False)
def start_dev_env(session: nox_poetry.Session):
    """
    Runs the dev environment

    Args:
        session (nox_poetry.Session): Nox session
    """
    if not session.posargs:
        raise RuntimeError("Component not specified")
    if session.posargs[0] not in IMAGE_COMPONENTS + RAG_COMPONENTS:
        raise RuntimeError("Unsupported component")

    component = session.posargs[0]
    additional_args = []
    if len(session.posargs) > 1:
        additional_args = session.posargs[1:]

    print(f"Starting dev environment for {component}")
    with run_component(component):
        session.run(
            "nox",
            "-s",
            start_dev_env.__name__,
            "--",
            *additional_args,
            external=True,
            env=environ,
        )


@nox_poetry.session(tags=["run", "stop", "dev"], python=False)
def stop_dev_env(session: nox_poetry.Session):
    """
    Stops the dev environment

    Args:
        session (nox_poetry.Session): Nox session
    """
    if not session.posargs:
        raise RuntimeError("Component not specified")
    if session.posargs[0] not in IMAGE_COMPONENTS + RAG_COMPONENTS:
        raise RuntimeError("Unsupported component")

    component = session.posargs[0]
    additional_args = []
    if len(session.posargs) > 1:
        additional_args = session.posargs[1:]

    print(f"Stopping dev environment for {component}")
    with run_component(component):
        session.run(
            "nox",
            "-s",
            stop_dev_env.__name__,
            "--",
            *additional_args,
            external=True,
            env=environ,
        )


@nox_poetry.session(tags=["dev", "tag"], python=False)
def tag(session: nox_poetry.Session):
    """
    Tags the codebase based on the version in pyproject.toml

    Args:
        session (nox_poetry.Session): Nox session
    """
    print(f"Tagging {COMPONENTS}")
    with run_component("agents-api"):
        session.run("nox", "-t", tag.__name__, external=True)


@nox_poetry.session(tags=["dev", "untag"], python=False)
def untag(session: nox_poetry.Session):
    """
    Untag the codebase based on the version in pyproject.toml

    Args:
        session (nox_poetry.Session): Nox session
    """
    print(f"Untagging {COMPONENTS}")
    with run_component("agents-api"):
        session.run("nox", "-t", untag.__name__, external=True)
