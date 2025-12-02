from typing import Any

from fastapi import FastAPI

from agents.app import create_app

__all__ = ("web_app", "config")

__doc__ = """
    This package contains the code that is used to manage AIBots API. 
    Generates a prepared system along with functionality to start a debugging
    server for testing purposes. 

    Attributes:
        web_app (FastAPI): FastAPI application
        config (dict[str, Any]): Configuration dictionary that specifies 
                                 how application should be served
"""  # noqa: E501


web_app: FastAPI = create_app()
config: dict[str, Any] = web_app.atlas.environ.uvicorn_config
