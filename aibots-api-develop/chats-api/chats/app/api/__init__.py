__doc__ = """
    Python package that contains all API routes supported by AI Bots API
    
    Attributes:
        routers (list[APIRouter]): List of supported routers to be initialised 
                                   by FastAPI
"""


__all__ = ("routers",)
from atlas.fastapi import AtlasApp

AtlasApp.atlas_init()

from fastapi import APIRouter

from .chats import router as chats_router
from .rags import router as rags_router
from .schemas import router as schemas_router

routers: list[APIRouter] = [
    chats_router,
    rags_router,
    schemas_router,
]
