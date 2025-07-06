"""
Main API router that combines all endpoints.
"""

from fastapi import APIRouter

from app.api.endpoints import health, upload, workspace
from app.api.v1 import git, git_lfs, takes

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(workspace.router, tags=["workspace"])
api_router.include_router(git.router, tags=["git"])
api_router.include_router(git_lfs.router, tags=["git-lfs"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(takes.router, tags=["takes"])
