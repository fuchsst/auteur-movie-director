"""
Asset Propagation API Endpoints
STORY-089 Implementation

REST API endpoints for managing asset propagation across story hierarchy.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.asset_propagation import AssetPropagationService, AssetPropagationRule, AssetReference
from app.models.asset_types import AssetType, PropagationMode

router = APIRouter(prefix="/api/v1/asset-propagation", tags=["asset-propagation"])


class AssetPropagationRequest(BaseModel):
    """Request model for asset propagation operations."""
    project_id: str
    level: str
    level_id: str
    asset_id: str
    asset_type: AssetType
    override_data: Optional[Dict[str, Any]] = None


class PropagationRuleRequest(BaseModel):
    """Request model for creating propagation rules."""
    asset_type: AssetType
    source_level: str
    target_level: str
    propagation_mode: PropagationMode
    conditions: Optional[Dict[str, Any]] = None
    priority: int = 0


class AssetResolutionResponse(BaseModel):
    """Response model for asset resolution."""
    project_id: str
    level: str
    level_id: str
    resolved_assets: Dict[str, List[Dict[str, Any]]]
    total_assets: int
    asset_types: Dict[str, int]


class AssetUsageResponse(BaseModel):
    """Response model for asset usage tracking."""
    asset_id: str
    usage_count: int
    usage_locations: List[Dict[str, Any]]


# Global service instance
_propagation_service = None


def get_propagation_service() -> AssetPropagationService:
    """Get or create propagation service instance."""
    global _propagation_service
    if _propagation_service is None:
        from app.config import settings
        _propagation_service = AssetPropagationService(str(settings.workspace_root))
    return _propagation_service


@router.post("/assets")
async def add_asset_to_context(request: AssetPropagationRequest) -> Dict[str, Any]:
    """Add an asset to a specific hierarchy level."""
    service = get_propagation_service()
    
    try:
        asset_ref = service.add_asset_to_context(
            project_id=request.project_id,
            level=request.level,
            level_id=request.level_id,
            asset_id=request.asset_id,
            asset_type=request.asset_type,
            override_data=request.override_data
        )
        
        # Track usage
        service.track_asset_usage(
            project_id=request.project_id,
            asset_id=request.asset_id,
            level=request.level,
            level_id=request.level_id,
            usage_context=request.override_data
        )
        
        return {
            "success": True,
            "asset_reference": asset_ref.model_dump(),
            "message": f"Asset {request.asset_id} added to {request.level}:{request.level_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resolve/{project_id}/{level}/{level_id}")
async def resolve_assets(
    project_id: str,
    level: str,
    level_id: str,
    asset_type: Optional[AssetType] = Query(None, description="Filter by asset type")
) -> AssetResolutionResponse:
    """Resolve all assets for a specific hierarchy level."""
    service = get_propagation_service()
    
    try:
        if asset_type:
            assets = service.get_all_assets_for_level(project_id, level, level_id)
            typed_assets = assets.get(asset_type.value, [])
            resolved_assets = {asset_type.value: [asset.model_dump() for asset in typed_assets]}
            total_assets = len(typed_assets)
            asset_types = {asset_type.value: len(typed_assets)}
        else:
            assets = service.get_all_assets_for_level(project_id, level, level_id)
            resolved_assets = {
                asset_type: [asset.model_dump() for asset in asset_list]
                for asset_type, asset_list in assets.items()
            }
            total_assets = sum(len(asset_list) for asset_list in assets.values())
            asset_types = {asset_type: len(asset_list) for asset_type, asset_list in assets.items()}
        
        return AssetResolutionResponse(
            project_id=project_id,
            level=level,
            level_id=level_id,
            resolved_assets=resolved_assets,
            total_assets=total_assets,
            asset_types=asset_types
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resolve/generation/{project_id}/{level}/{level_id}")
async def resolve_for_generation(
    project_id: str,
    level: str,
    level_id: str
) -> Dict[str, Any]:
    """Resolve assets formatted for generative processes."""
    service = get_propagation_service()
    
    try:
        resolver = service.propagation_resolver
        generation_context = resolver.resolve_for_generation(project_id, level, level_id)
        return generation_context
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rules")
async def add_propagation_rule(request: PropagationRuleRequest) -> Dict[str, Any]:
    """Add a custom propagation rule."""
    service = get_propagation_service()
    
    try:
        rule = AssetPropagationRule(
            asset_type=request.asset_type,
            source_level=request.source_level,
            target_level=request.target_level,
            propagation_mode=request.propagation_mode,
            conditions=request.conditions or {},
            priority=request.priority
        )
        
        service.add_propagation_rule(rule)
        
        return {
            "success": True,
            "rule": rule.model_dump(),
            "message": "Propagation rule added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usage/{project_id}/{asset_id}")
async def get_asset_usage(project_id: str, asset_id: str) -> AssetUsageResponse:
    """Get usage information for a specific asset."""
    service = get_propagation_service()
    
    try:
        usage = service.get_asset_usage(project_id, asset_id)
        return AssetUsageResponse(
            asset_id=asset_id,
            usage_count=len(usage),
            usage_locations=usage
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/validate/{project_id}")
async def validate_consistency(project_id: str) -> Dict[str, Any]:
    """Validate asset consistency across the project."""
    service = get_propagation_service()
    
    try:
        validation = service.validate_asset_consistency(project_id)
        return validation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hierarchy/levels")
async def get_hierarchy_levels() -> Dict[str, List[str]]:
    """Get available hierarchy levels."""
    service = get_propagation_service()
    return {
        "levels": service.HIERARCHY_LEVELS,
        "description": "Asset propagation hierarchy from general to specific"
    }


@router.post("/save/{project_id}")
async def save_propagation_state(project_id: str) -> Dict[str, Any]:
    """Save the current propagation state for a project."""
    service = get_propagation_service()
    
    try:
        service.save_state(project_id)
        return {
            "success": True,
            "message": f"Propagation state saved for project {project_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load/{project_id}")
async def load_propagation_state(project_id: str) -> Dict[str, Any]:
    """Load propagation state for a project."""
    service = get_propagation_service()
    
    try:
        service.load_state(project_id)
        return {
            "success": True,
            "message": f"Propagation state loaded for project {project_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{project_id}")
async def export_propagation_state(project_id: str) -> Dict[str, Any]:
    """Export complete propagation state for a project."""
    service = get_propagation_service()
    
    try:
        export_data = service.export_propagation_state(project_id)
        return export_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))