"""
Main API router that combines all endpoints.
"""

from fastapi import APIRouter

from app.api.endpoints import health, system, upload, workspace
from app.api.v1 import (
    asset_operations,
    assets,
    export,
    git,
    git_lfs,
    git_performance,
    projects,
    takes,
)
from app.api.v1 import import_ as import_api

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workspace.router, tags=["workspace"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(assets.router, tags=["assets"])
api_router.include_router(asset_operations.router, prefix="/api/v1", tags=["asset-operations"])
api_router.include_router(system.router, tags=["system"])
api_router.include_router(git.router, tags=["git"])
api_router.include_router(git_lfs.router, tags=["git-lfs"])
api_router.include_router(git_performance.router, tags=["git-performance"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(takes.router, tags=["takes"])
api_router.include_router(export.router, tags=["export"])
api_router.include_router(import_api.router, tags=["import"])
