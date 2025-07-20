"""
Breakdown API Endpoints
STORY-086 Implementation

REST API endpoints for the professional script breakdown interface,
providing script parsing, element management, and export capabilities.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
import asyncio

from app.models.breakdown_models import (
    ScriptBreakdown, SceneBreakdown, BreakdownElement, 
    BreakdownExportRequest, BreakdownExportFormat, ElementCategory,
    BreakdownElementStatus
)
from app.services.breakdown_service import BreakdownService
from app.services.script_parser import ScriptParserService
from app.services.asset_registry import AssetRegistry
from app.core.dependencies import get_asset_registry


router = APIRouter(prefix="/breakdown", tags=["breakdown"])


class BreakdownResponse(BaseModel):
    """Response wrapper for breakdown operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ElementUpdateRequest(BaseModel):
    """Request for updating breakdown element status."""
    status: BreakdownElementStatus
    notes: Optional[str] = None
    estimated_cost: Optional[float] = None


class CustomElementRequest(BaseModel):
    """Request for adding custom elements."""
    element_type: ElementCategory
    name: str
    description: str
    quantity: int = 1
    notes: Optional[str] = None
    estimated_cost: Optional[float] = 0.0


@router.post("/parse-script", response_model=BreakdownResponse)
async def parse_script_file(
    project_id: str = Form(...),
    project_name: str = Form(...),
    file: UploadFile = File(...)
):
    """Parse a script file and create a breakdown."""
    try:
        # Read file content
        content = await file.read()
        
        # Get services
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        # Create breakdown
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id=project_id,
            project_name=project_name,
            script_path=file.filename,
            script_content=content
        )
        
        return BreakdownResponse(
            success=True,
            message=f"Successfully parsed script with {breakdown.total_scenes} scenes",
            data={"breakdown": breakdown.model_dump()}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/breakdown/{project_id}", response_model=BreakdownResponse)
async def get_breakdown(project_id: str):
    """Get the complete breakdown for a project."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        breakdown = await breakdown_service.get_breakdown(project_id)
        if not breakdown:
            raise HTTPException(status_code=404, detail="Breakdown not found")
        
        return BreakdownResponse(
            success=True,
            message="Breakdown retrieved successfully",
            data={"breakdown": breakdown.model_dump()}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenes/{project_id}", response_model=BreakdownResponse)
async def get_scenes(project_id: str):
    """Get all scenes for a project."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        breakdown = await breakdown_service.get_breakdown(project_id)
        if not breakdown:
            raise HTTPException(status_code=404, detail="Breakdown not found")
        
        scenes_data = {
            scene_id: scene.model_dump()
            for scene_id, scene in breakdown.scenes.items()
        }
        
        return BreakdownResponse(
            success=True,
            message=f"Retrieved {len(scenes_data)} scenes",
            data={"scenes": scenes_data}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scene/{project_id}/{scene_id}", response_model=BreakdownResponse)
async def get_scene_breakdown(project_id: str, scene_id: str):
    """Get breakdown for a specific scene."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        breakdown = await breakdown_service.get_breakdown(project_id)
        if not breakdown or scene_id not in breakdown.scenes:
            raise HTTPException(status_code=404, detail="Scene not found")
        
        scene = breakdown.scenes[scene_id]
        
        return BreakdownResponse(
            success=True,
            message="Scene breakdown retrieved",
            data={"scene": scene.model_dump()}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/element/{project_id}/{scene_id}/{element_id}", response_model=BreakdownResponse)
async def update_element_status(
    project_id: str,
    scene_id: str,
    element_id: str,
    request: ElementUpdateRequest
):
    """Update the status of a breakdown element."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        success = await breakdown_service.update_element_status(
            project_id=project_id,
            scene_id=scene_id,
            element_id=element_id,
            new_status=request.status
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Element not found")
        
        return BreakdownResponse(
            success=True,
            message="Element status updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/element/{project_id}/{scene_id}", response_model=BreakdownResponse)
async def add_custom_element(
    project_id: str,
    scene_id: str,
    request: CustomElementRequest
):
    """Add a custom element to a scene breakdown."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        element = await breakdown_service.add_custom_element(
            project_id=project_id,
            scene_id=scene_id,
            element_data=request.model_dump()
        )
        
        return BreakdownResponse(
            success=True,
            message="Custom element added successfully",
            data={"element": element.model_dump()}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/{project_id}", response_model=BreakdownResponse)
async def export_breakdown(
    project_id: str,
    export_request: BreakdownExportRequest
):
    """Export breakdown data in requested format."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        export_data = await breakdown_service.export_breakdown(project_id, export_request)
        
        return BreakdownResponse(
            success=True,
            message=f"Breakdown exported successfully in {export_request.export_format.value} format",
            data={"export": export_data}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/elements/{project_id}/{category}", response_model=BreakdownResponse)
async def get_elements_by_category(project_id: str, category: ElementCategory):
    """Get all elements of a specific category across all scenes."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        breakdown = await breakdown_service.get_breakdown(project_id)
        if not breakdown:
            raise HTTPException(status_code=404, detail="Breakdown not found")
        
        all_elements = []
        for scene in breakdown.scenes.values():
            elements = scene.elements.get(category, [])
            for element in elements:
                element_data = element.model_dump()
                element_data["scene_number"] = scene.scene_number
                element_data["scene_heading"] = scene.scene_heading
                all_elements.append(element_data)
        
        return BreakdownResponse(
            success=True,
            message=f"Retrieved {len(all_elements)} {category.value} elements",
            data={"elements": all_elements}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{project_id}", response_model=BreakdownResponse)
async def get_breakdown_summary(project_id: str):
    """Get summary statistics for the breakdown."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        breakdown = await breakdown_service.get_breakdown(project_id)
        if not breakdown:
            raise HTTPException(status_code=404, detail="Breakdown not found")
        
        summary = {
            "total_scenes": breakdown.total_scenes,
            "total_elements": breakdown.total_elements,
            "total_estimated_cost": breakdown.total_estimated_cost,
            "total_estimated_duration": breakdown.total_estimated_duration,
            "element_counts": breakdown.element_counts,
            "all_characters": breakdown.all_characters,
            "all_locations": breakdown.all_locations
        }
        
        return BreakdownResponse(
            success=True,
            message="Breakdown summary retrieved",
            data={"summary": summary}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/{project_id}", response_model=BreakdownResponse)
async def validate_breakdown(project_id: str):
    """Validate the complete breakdown."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        breakdown = await breakdown_service.get_breakdown(project_id)
        if not breakdown:
            raise HTTPException(status_code=404, detail="Breakdown not found")
        
        is_valid = breakdown.validate_breakdown()
        
        return BreakdownResponse(
            success=is_valid,
            message="Breakdown validation completed",
            data={
                "is_valid": is_valid,
                "errors": breakdown.validation_errors
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-canvas/{project_id}", response_model=BreakdownResponse)
async def sync_with_canvas(
    project_id: str,
    background_tasks: BackgroundTasks,
    canvas_data: Dict[str, Any]
):
    """Sync breakdown data with Production Canvas."""
    try:
        asset_registry = get_asset_registry()
        breakdown_service = BreakdownService(f"workspace/{project_id}", asset_registry)
        
        # Run sync in background
        background_tasks.add_task(
            breakdown_service.sync_with_canvas,
            project_id,
            canvas_data
        )
        
        return BreakdownResponse(
            success=True,
            message="Canvas sync initiated in background"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))