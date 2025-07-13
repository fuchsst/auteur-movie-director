"""
Asset operations API endpoints for project-level asset management.
Implements STORY-031 requirements for copying assets from library to projects.
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.schemas.project import AssetReference, AssetType
from app.services.asset_operations import get_asset_operations_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["asset-operations"])


class AssetCopyRequest(BaseModel):
    """Request to copy an asset from library to project"""

    source_category: AssetType = Field(..., description="Source asset category in library")
    source_asset_id: str = Field(..., description="Source asset ID in library")
    target_name: str | None = Field(None, description="Optional new name for copied asset")
    replace_existing: bool = Field(False, description="Replace existing asset with same name")


class BatchAssetCopyRequest(BaseModel):
    """Request to copy multiple assets from library to project"""

    assets: list[AssetCopyRequest] = Field(..., description="List of assets to copy")
    replace_existing: bool = Field(False, description="Replace existing assets with same names")


class AssetCopyResponse(BaseModel):
    """Response for successful asset copy operation"""

    success: bool
    asset: AssetReference
    message: str


class BatchAssetCopyResponse(BaseModel):
    """Response for batch asset copy operation"""

    success: bool
    copied_assets: list[AssetReference]
    total_requested: int
    total_copied: int
    message: str


class ProjectAssetsResponse(BaseModel):
    """Response for project assets listing"""

    assets: list[AssetReference]
    project_id: str
    category: str | None = None
    total: int


@router.post("/projects/{project_id}/assets/copy", response_model=AssetCopyResponse)
async def copy_asset_to_project(project_id: str, copy_request: AssetCopyRequest):
    """
    Copy a single asset from workspace library to project.

    Creates a copy of the asset in the project's asset directory while
    preserving all metadata and establishing source tracking.
    """
    try:
        operations_service = get_asset_operations_service()

        copied_asset = await operations_service.copy_asset_to_project(
            project_id=project_id,
            source_category=copy_request.source_category,
            source_asset_id=copy_request.source_asset_id,
            target_name=copy_request.target_name,
            replace_existing=copy_request.replace_existing,
        )

        return AssetCopyResponse(
            success=True,
            asset=copied_asset,
            message=f"Successfully copied asset '{copied_asset.name}' to project",
        )

    except Exception as e:
        logger.error(f"Error copying asset to project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/assets/copy-batch", response_model=BatchAssetCopyResponse)
async def copy_multiple_assets_to_project(project_id: str, batch_request: BatchAssetCopyRequest):
    """
    Copy multiple assets from workspace library to project in a batch operation.

    Performs atomic batch copy with rollback on failure to ensure consistency.
    """
    try:
        operations_service = get_asset_operations_service()

        # Convert request format for service
        asset_requests = []
        for asset in batch_request.assets:
            asset_requests.append(
                {
                    "category": asset.source_category.value,
                    "asset_id": asset.source_asset_id,
                    "target_name": asset.target_name,
                }
            )

        copied_assets = await operations_service.copy_multiple_assets_to_project(
            project_id=project_id,
            asset_requests=asset_requests,
            replace_existing=batch_request.replace_existing,
        )

        return BatchAssetCopyResponse(
            success=True,
            copied_assets=copied_assets,
            total_requested=len(batch_request.assets),
            total_copied=len(copied_assets),
            message=f"Successfully copied {len(copied_assets)} assets to project",
        )

    except Exception as e:
        logger.error(f"Error copying batch assets to project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/assets", response_model=ProjectAssetsResponse)
async def list_project_assets(
    project_id: str,
    category: AssetType | None = Query(None, description="Filter by asset category"),
):
    """
    List all assets that have been copied to a specific project.

    Returns assets that exist in the project's asset directory,
    not the workspace library assets.
    """
    try:
        operations_service = get_asset_operations_service()

        project_assets = await operations_service.get_project_assets(
            project_id=project_id, category=category
        )

        return ProjectAssetsResponse(
            assets=project_assets,
            project_id=project_id,
            category=category.value if category else None,
            total=len(project_assets),
        )

    except Exception as e:
        logger.error(f"Error listing project assets for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/assets/{category}", response_model=list[AssetReference])
async def list_project_assets_by_category(project_id: str, category: AssetType):
    """
    List project assets in a specific category.

    Convenience endpoint for category-specific asset browsing.
    """
    try:
        operations_service = get_asset_operations_service()

        project_assets = await operations_service.get_project_assets(
            project_id=project_id, category=category
        )

        return project_assets

    except Exception as e:
        logger.error(f"Error listing {category.value} assets for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}/assets/{category}/{asset_id}")
async def remove_project_asset(project_id: str, category: AssetType, asset_id: str):
    """
    Remove an asset from a project.

    This removes the asset copy from the project but does not affect
    the original asset in the workspace library.
    """
    try:
        operations_service = get_asset_operations_service()

        success = await operations_service.remove_project_asset(
            project_id=project_id, category=category, asset_id=asset_id
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PROJECT_ASSET_NOT_FOUND",
                    "message": f"Asset {asset_id} not found in project {project_id}",
                    "details": {
                        "project_id": project_id,
                        "category": category.value,
                        "asset_id": asset_id,
                    },
                },
            )

        return {
            "success": True,
            "message": f"Successfully removed {category.value} asset {asset_id} from project",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing project asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/assets/{category}/{asset_id}", response_model=AssetReference)
async def get_project_asset(project_id: str, category: AssetType, asset_id: str):
    """
    Get a specific asset from a project.

    Returns the project copy of the asset, not the library original.
    """
    try:
        operations_service = get_asset_operations_service()

        project_assets = await operations_service.get_project_assets(
            project_id=project_id, category=category
        )

        for asset in project_assets:
            if asset.id == asset_id:
                return asset

        raise HTTPException(
            status_code=404,
            detail={
                "error": "PROJECT_ASSET_NOT_FOUND",
                "message": f"Asset {asset_id} not found in project {project_id}",
                "details": {
                    "project_id": project_id,
                    "category": category.value,
                    "asset_id": asset_id,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
