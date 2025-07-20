"""
API v1 Router Configuration
"""

from fastapi import APIRouter
from .takes import router as takes_router
from .git import router as git_router
from .git_lfs import router as git_lfs_router
from .breakdown import router as breakdown_router
from .storyboard import router as storyboard_router
from .table_read import router as table_read_router
from .asset_propagation import router as asset_propagation_router
from .scene_breakdown import router as scene_breakdown_router

router = APIRouter(prefix="/v1")
router.include_router(takes_router)
router.include_router(git_router)
router.include_router(git_lfs_router)
router.include_router(breakdown_router)
router.include_router(storyboard_router)
router.include_router(table_read_router)
router.include_router(asset_propagation_router)
router.include_router(scene_breakdown_router)