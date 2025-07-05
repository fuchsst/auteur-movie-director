"""
Main API router that combines all endpoints.
"""

from fastapi import APIRouter

from app.api.endpoints import health, workspace

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workspace.router, tags=["workspace"])
