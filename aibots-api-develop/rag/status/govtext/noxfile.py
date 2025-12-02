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
        "--no-root",
        external=True,
        env={
            "REQUESTS_CA_BUNDLE": certifi.where(),
            "SSL_CERT_FILE": certifi.where(),
        },
    )


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

    # if "AWS_ACCESS_ID" not in environ:
    #     raise RuntimeError("AWS_ACCESS_ID environment variable was not provided")
    # if "AWS_SECRET_KEY" not in environ:
    #     raise RuntimeError("AWS_SECRET_KEY environment variable was not provided")

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
            # "AWS_ACCESS_ID": environ['AWS_ACCESS_ID'],
            # "AWS_SECRET_KEY": environ['AWS_SECRET_KEY']
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


@nox_poetry.session(tags=["run", "start", "dev"], python=False)
def start_dev_env(session: nox_poetry.Session):
    """
    Runs the dev environment

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