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

from .agents import router as agents_router
from .files import router as files_router
from .auth import permissions_router
from .logins import (
    agencies_router,
    email_otps_router,
    login_router,
    refresh_router,
    sso_router,
    login_users_router,
)
from .groups import groups_router as groups_router
from .users import users_router as users_router

routers: list[APIRouter] = [
    email_otps_router,
    sso_router,
    login_router,
    refresh_router,
    login_users_router,
    agencies_router,
    users_router,
    groups_router,
    permissions_router,
    files_router,
    agents_router,
]
