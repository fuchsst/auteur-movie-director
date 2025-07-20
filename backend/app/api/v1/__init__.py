"""
API v1 Router Configuration
"""

from fastapi import APIRouter
from .takes import router as takes_router
from .git import router as git_router
from .git_lfs import router as git_lfs_router
from .breakdown import router as breakdown_router
from .storyboard import router as storyboard_router

router = APIRouter(prefix="/v1")
router.include_router(takes_router)
router.include_router(git_router)
router.include_router(git_lfs_router)
router.include_router(breakdown_router)
router.include_router(storyboard_router)