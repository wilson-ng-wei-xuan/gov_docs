from __future__ import annotations

import traceback
from logging import Logger, getLogger

import uvicorn

from agents import config

__doc__ = """
    Production setup to serve the AI Bots API

    Attributes:
        logger (Logger): Application logger
"""

logger: Logger = getLogger("atlas")

if __name__ == "__main__":
    try:
        uvicorn.run("agents:web_app", **config)
    except Exception as e:
        logger.exception(
            f"Fatal exception {e.__class__.__name__}.{str(e)} was thrown, "
            f"shutting down application"
        )
        logger.error(traceback.format_exc())
