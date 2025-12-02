from fastapi import APIRouter

from app.api_v1 import auth, common

routers = APIRouter()

routers.include_router(auth.router, prefix="/auth", tags=["Auth"])
