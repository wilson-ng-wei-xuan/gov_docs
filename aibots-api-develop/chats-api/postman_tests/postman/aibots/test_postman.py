import os
import shlex
import subprocess
from pathlib import Path
from time import sleep
from typing import Any, Dict, List, Optional

import pytest


def newman(
    test_dir: Path,
    collection: str,
    environment: Optional[str] = None,
    global_vars: Optional[str] = None,
    env_vars: Optional[Dict[str, Any]] = None,
    **subprocess_kwargs: Dict[str, Any],
):
    image_name: str = "postman/newman"
    subprocess.run(shlex.split(f"docker pull {image_name}"))
    test_path = Path("/etc/newman")
    cmd: List[str] = [
        "docker",
        "run",
        "--network",
        "host",
        "-v",
        f"{test_dir}:{test_path.as_posix()}",
        "--name",
        test_dir.name,
        image_name,
        "run",
        collection,
    ]
    if environment and (test_dir / environment).exists():
        cmd.extend([f"-e", environment])
    if global_vars and (test_dir / global_vars).exists():
        cmd.extend([f"-g", global_vars])
    if env_vars:
        for k, v in env_vars.items():
            cmd.append("--env-var")
            cmd.append(f"{k}={v}")

    cmd.extend(["--insecure", "--verbose", "--bail"])

    print(f"Running Postman command {cmd}")
    output = subprocess.run(cmd, env=subprocess_kwargs)
    subprocess.run(shlex.split(f"docker rm -f {test_dir.name}"))
    return output


class TestPostman:

    def test_heartbeat(
        self,
        test_folder,
        collection,
        environment,
        global_vars,
        postman_env,
    ):
        sleep(20.0)
        assert (
            newman(
                Path(test_folder),
                collection,
                environment,
                global_vars,
                **dict(os.environ),
            ).returncode
            == 0
        )


# @pytest.fixture(scope="class")
# def uam_environ():
#     os.environ["EXPIRY__OTP"] = "0.2"
#     yield
#     del os.environ["EXPIRY__OTP"]
#
#
# @pytest.fixture(scope="class")
# def uam_env_vars():
#     return {
#         "TEST_EMAIL_ADDRESS1": "davidtwlee@dsaid.gov.sg",
#         "TEST_EMAIL_ADDRESS2": "david_tw_lee@tech.gov.sg",
#     }
#
#
# class TestPostmanLatest:
#     api_version: str = "latest"
#
#     def test_logins(
#         self,
#         test_folder,
#         collection,
#         environment,
#         global_vars,
#         postman_env,
#         uam_env_vars,
#         uam_environ,
#     ):
#         sleep(20.0)
#         assert (
#             newman(
#                 Path(test_folder),
#                 collection,
#                 environment,
#                 global_vars,
#                 uam_env_vars,
#                 **dict(os.environ),
#             ).returncode
#             == 0
#         )
#
#     def test_uam(
#         self,
#         test_folder,
#         collection,
#         environment,
#         global_vars,
#         postman_env,
#         uam_env_vars,
#         uam_environ,
#     ):
#         sleep(20.0)
#         assert (
#             newman(
#                 Path(test_folder),
#                 collection,
#                 environment,
#                 global_vars,
#                 uam_env_vars,
#                 **dict(os.environ),
#             ).returncode
#             == 0
#         )
#
#
# class TestPostmanV10:
#     api_version: str = "v1.0"
#
#     def test_logins(
#         self,
#         test_folder,
#         collection,
#         environment,
#         global_vars,
#         postman_env,
#         uam_env_vars,
#         uam_environ,
#     ):
#         sleep(20.0)
#         assert (
#             newman(
#                 Path(test_folder),
#                 collection,
#                 environment,
#                 global_vars,
#                 uam_env_vars,
#                 **dict(os.environ),
#             ).returncode
#             == 0
#         )
#
#     def test_uam(
#         self,
#         test_folder,
#         collection,
#         environment,
#         global_vars,
#         postman_env,
#         uam_env_vars,
#         uam_environ,
#     ):
#         sleep(20.0)
#         assert (
#             newman(
#                 Path(test_folder),
#                 collection,
#                 environment,
#                 global_vars,
#                 uam_env_vars,
#                 **dict(os.environ),
#             ).returncode
#             == 0
#         )
