from fastapi import APIRouter

from app.api.api_v1.endpoints import base

api_router = APIRouter()
api_router.include_router(base.router)
