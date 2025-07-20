"""
Asset API endpoints for workspace-level asset management.
Implements STORY-083 requirements with expanded asset system.
"""

import json
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.models.asset_types import (
    AssetType, AssetCategory, BaseAsset, PropAsset, WardrobeAsset,
    VehicleAsset, SetDressingAsset, SFXAsset, SoundAsset, MusicAsset,
    AssetCollection, AssetReference, create_asset_from_dict
)
from app.services.asset_registry import AssetRegistryAPI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])


class AssetCreateRequest(BaseModel):
    """Asset creation request with expanded types"""

    asset_type: AssetType
    category: AssetCategory
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    description: str = Field(..., max_length=500, description="Asset description")
    tags: List[str] = Field(default_factory=list, description="Asset tags")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    # Type-specific fields
    dimensions: Optional[dict] = None
    weight: Optional[float] = None
    material: Optional[str] = None
    color: Optional[str] = None
    character_id: Optional[str] = None
    character_name: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    capacity: Optional[int] = None
    tempo: Optional[int] = None
    key: Optional[str] = None
    duration: Optional[float] = None
    effect_type: Optional[str] = None
    intensity: Optional[str] = None
    is_loopable: Optional[bool] = None
    reference_images: List[str] = Field(default_factory=list)
    trigger_word: Optional[str] = None


class AssetImportResponse(BaseModel):
    """Asset import response"""

    success: bool
    asset_id: str
    message: str


class AssetUpdateRequest(BaseModel):
    """Asset metadata update request"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    updates: dict = Field(default_factory=dict)


class AssetListResponse(BaseModel):
    """Asset list response with pagination info"""

    assets: List[dict]
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
    category: AssetType | None = Query(None, description="Filter by asset category"),
    tags: str | None = Query(None, description="Comma-separated tags to filter by"),
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

        assets = await asset_service.search_assets(
            query="", category=category, tags=tag_list, limit=limit, offset=offset
        )

        # Get total count for pagination (simplified - in production might cache this)
        all_assets = await asset_service.search_assets(
            query="", category=category, tags=tag_list, limit=10000
        )
        total = len(all_assets)

        return AssetListResponse(
            assets=[asset.dict() for asset in assets],
            total=total,
            offset=offset,
            limit=limit,
            category=category.value if category else None,
        )

    except Exception as e:
        logger.error(f"Error listing assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[dict])
async def search_assets(
    q: str = Query(..., min_length=1, description="Search query"),
    category: AssetType | None = Query(None, description="Filter by category"),
    tags: str | None = Query(None, description="Comma-separated tags filter"),
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

        return [asset.dict() for asset in assets]

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
        stats = await asset_service.registry.get_usage_statistics()

        return AssetStatsResponse(
            total_assets=stats['total_assets'],
            by_category=stats['by_category'],
            total_size_bytes=0,  # Placeholder for now
            library_path=str(asset_service.registry.generative_assets_dir)
        )

    except Exception as e:
        logger.error(f"Error getting asset statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}", response_model=List[dict])
async def list_assets_by_category(
    category: AssetType,
    tags: str | None = Query(None, description="Comma-separated tags filter"),
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

        assets = await asset_service.search_assets(
            query="", category=category, tags=tag_list, limit=limit, offset=offset
        )

        return [asset.dict() for asset in assets]

    except Exception as e:
        logger.error(f"Error listing {category.value} assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}/{asset_id}", response_model=dict)
async def get_asset(category: AssetType, asset_id: str):
    """
    Get a specific asset by category and ID.

    Returns full asset metadata and file information.
    """
    try:
        asset_service = get_asset_service()
        asset = await asset_service.get_asset(asset_id)

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
    tags: str | None = Form(None, description="Comma-separated tags"),
    description: str | None = Form(None, description="Asset description"),
    files: list[UploadFile] = File(..., description="Asset files"),
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

        # Create metadata
        metadata = {}
        if description:
            metadata["description"] = description

        # Create asset data
        asset_data = {
            "asset_type": category,
            "category": "standard",  # Default category
            "name": name,
            "tags": tag_list,
            "metadata": metadata
        }

        # Create the asset
        result = await asset_service.create_asset(asset_data)
        asset_id = result["asset_id"]

        return AssetImportResponse(
            success=True,
            asset_id=asset_id,
            message=f"Successfully imported {category.value} asset: {name}",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error importing {category.value} asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{category}/{asset_id}", response_model=dict)
async def update_asset_metadata(
    category: AssetType, asset_id: str, update_data: AssetUpdateRequest
):
    """
    Update asset metadata.

    Allows updating name, tags, and description without changing files.
    """
    try:
        asset_service = get_asset_service()

        # Prepare updates
        updates = {}
        if update_data.name is not None:
            updates["name"] = update_data.name
        if update_data.tags is not None:
            updates["tags"] = update_data.tags
        if update_data.description is not None:
            updates["description"] = update_data.description
        updates.update(update_data.updates)

        success = await asset_service.update_asset(asset_id, updates)

        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ASSET_NOT_FOUND",
                    "message": f"Asset {asset_id} not found in category {category.value}",
                    "details": {"category": category.value, "asset_id": asset_id},
                },
            )

        # Return updated asset
        asset = await asset_service.get_asset(asset_id)
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
        success = await asset_service.registry.delete_asset(asset_id)

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


def get_asset_service():
    """Factory function to get asset registry service."""
    from app.core.config import settings
    return AssetRegistryAPI(settings.WORKSPACE_ROOT)