
from os import environ
from pathlib import Path

import nox_poetry


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

    print(f"Running unittests for {Path('.').resolve().stem}")
    path: Path = Path("tests")
    if not (path.exists() and path.is_dir()):
        print("No unit tests to run")
        return

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

    print(f"Running integration tests for {Path('.').resolve().stem}")
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