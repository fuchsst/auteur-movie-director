"""
Asset API endpoints for workspace-level asset management.
Implements STORY-029 requirements with RESTful design.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.schemas.project import AssetReference, AssetType
from app.services.assets import get_asset_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])


class AssetImportRequest(BaseModel):
    """Asset import request"""

    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    category: AssetType = Field(..., description="Asset category")
    tags: Optional[List[str]] = Field(default=None, description="Asset tags")
    description: Optional[str] = Field(default=None, description="Asset description")


class AssetImportResponse(BaseModel):
    """Asset import response"""

    success: bool
    asset: AssetReference
    message: str


class AssetUpdateRequest(BaseModel):
    """Asset metadata update request"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tags: Optional[List[str]] = None
    description: Optional[str] = None


class AssetListResponse(BaseModel):
    """Asset list response with pagination info"""

    assets: List[AssetReference]
    total: int
    offset: int
    limit: int
    category: Optional[str] = None


class AssetStatsResponse(BaseModel):
    """Asset statistics response"""

    total_assets: int
    by_category: dict
    total_size_bytes: int
    library_path: str


class ErrorResponse(BaseModel):
    """Error response format"""

    error: str
    message: str
    details: dict = Field(default_factory=dict)


@router.get("", response_model=AssetListResponse)
async def list_assets(
    category: Optional[AssetType] = Query(None, description="Filter by asset category"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum assets to return"),
    offset: int = Query(0, ge=0, description="Number of assets to skip"),
):
    """
    List all assets with optional filtering.

    Supports filtering by category and tags with pagination.
    """
    try:
        asset_service = get_asset_service()

        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        assets = await asset_service.list_assets(
            category=category, tags=tag_list, limit=limit, offset=offset
        )

        # Get total count for pagination (simplified - in production might cache this)
        all_assets = await asset_service.list_assets(category=category, tags=tag_list, limit=10000)
        total = len(all_assets)

        return AssetListResponse(
            assets=assets,
            total=total,
            offset=offset,
            limit=limit,
            category=category.value if category else None,
        )

    except Exception as e:
        logger.error(f"Error listing assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[AssetReference])
async def search_assets(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[AssetType] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Comma-separated tags filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
):
    """
    Search assets by name, description, and tags.

    Performs case-insensitive search across asset metadata.
    """
    try:
        asset_service = get_asset_service()

        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        assets = await asset_service.search_assets(
            query=q, category=category, tags=tag_list, limit=limit
        )

        return assets

    except Exception as e:
        logger.error(f"Error searching assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AssetStatsResponse)
async def get_asset_statistics():
    """
    Get workspace asset statistics.

    Returns counts and storage information by category.
    """
    try:
        asset_service = get_asset_service()
        stats = asset_service.get_asset_statistics()

        return AssetStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting asset statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}", response_model=List[AssetReference])
async def list_assets_by_category(
    category: AssetType,
    tags: Optional[str] = Query(None, description="Comma-separated tags filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum assets to return"),
    offset: int = Query(0, ge=0, description="Number of assets to skip"),
):
    """
    List assets in a specific category.

    More convenient endpoint for category-specific browsing.
    """
    try:
        asset_service = get_asset_service()

        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        assets = await asset_service.list_assets(
            category=category, tags=tag_list, limit=limit, offset=offset
        )

        return assets

    except Exception as e:
        logger.error(f"Error listing {category.value} assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}/{asset_id}", response_model=AssetReference)
async def get_asset(category: AssetType, asset_id: str):
    """
    Get a specific asset by category and ID.

    Returns full asset metadata and file information.
    """
    try:
        asset_service = get_asset_service()
        asset = await asset_service.get_asset(category, asset_id)

        if not asset:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ASSET_NOT_FOUND",
                    "message": f"Asset {asset_id} not found in category {category.value}",
                    "details": {"category": category.value, "asset_id": asset_id},
                },
            )

        return asset

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting asset {category.value}/{asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{category}", response_model=AssetImportResponse)
async def import_asset(
    category: AssetType,
    name: str = Form(..., description="Asset name"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    description: Optional[str] = Form(None, description="Asset description"),
    files: List[UploadFile] = File(..., description="Asset files"),
):
    """
    Import a new asset into the workspace library.

    Accepts multiple files and automatically generates previews.
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="At least one file must be provided")

        asset_service = get_asset_service()

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Organize files by type (simplified logic - could be more sophisticated)
        file_dict = {}
        for file in files:
            filename = file.filename.lower()

            # Determine file type based on extension
            if filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
                file_dict["image"] = file
            elif filename.endswith((".safetensors", ".ckpt", ".pt")):
                file_dict["model"] = file
            elif filename.endswith((".json", ".yaml", ".yml")):
                file_dict["config"] = file
            elif filename.endswith((".wav", ".mp3", ".ogg", ".flac", ".aac")):
                file_dict["audio"] = file
            elif filename.endswith((".obj", ".fbx", ".glb", ".gltf")):
                file_dict["model"] = file
            else:
                # Default to first available type for the category
                supported_types = asset_service.SUPPORTED_FILE_TYPES.get(category, {})
                if supported_types:
                    default_type = list(supported_types.keys())[0]
                    file_dict[default_type] = file

        # Create metadata
        metadata = {}
        if description:
            metadata["description"] = description

        # Import the asset
        asset = await asset_service.import_asset(
            category=category, name=name, files=file_dict, metadata=metadata, tags=tag_list
        )

        return AssetImportResponse(
            success=True,
            asset=asset,
            message=f"Successfully imported {category.value} asset: {name}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing {category.value} asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{category}/{asset_id}", response_model=AssetReference)
async def update_asset_metadata(
    category: AssetType, asset_id: str, update_data: AssetUpdateRequest
):
    """
    Update asset metadata.

    Allows updating name, tags, and description without changing files.
    """
    try:
        asset_service = get_asset_service()

        # Prepare metadata update
        metadata_update = {}
        if update_data.description is not None:
            metadata_update["description"] = update_data.description

        asset = await asset_service.update_asset_metadata(
            category=category,
            asset_id=asset_id,
            name=update_data.name,
            tags=update_data.tags,
            metadata=metadata_update if metadata_update else None,
        )

        if not asset:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ASSET_NOT_FOUND",
                    "message": f"Asset {asset_id} not found in category {category.value}",
                    "details": {"category": category.value, "asset_id": asset_id},
                },
            )

        return asset

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating asset {category.value}/{asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{category}/{asset_id}")
async def delete_asset(category: AssetType, asset_id: str):
    """
    Delete an asset from the workspace library.

    Permanently removes the asset and all associated files.
    """
    try:
        asset_service = get_asset_service()
        success = await asset_service.delete_asset(category, asset_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ASSET_NOT_FOUND",
                    "message": f"Asset {asset_id} not found in category {category.value}",
                    "details": {"category": category.value, "asset_id": asset_id},
                },
            )

        return {
            "success": True,
            "message": f"Successfully deleted {category.value} asset {asset_id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting asset {category.value}/{asset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
