"""
Scene Breakdown API Endpoints
=============================

REST API endpoints for scene-by-scene breakdown visualization system.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
import uuid
import json
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.schemas.scene_breakdown import (
    SceneBreakdown,
    SceneSummary,
    SceneReorderRequest,
    SceneBulkUpdate,
    SceneAnalysis,
    SceneStatus
)
from backend.app.services.scene_breakdown_service import SceneBreakdownService

router = APIRouter(prefix="/scene-breakdown", tags=["scene-breakdown"])


@router.get("/project/{project_id}/scenes", response_model=List[SceneSummary])
async def get_project_scenes(
    project_id: str = Path(..., description="Project identifier"),
    act_number: Optional[int] = Query(None, ge=1, le=3, description="Filter by act number"),
    chapter_number: Optional[int] = Query(None, description="Filter by chapter number"),
    status: Optional[SceneStatus] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get all scenes for a project with optional filtering."""
    service = SceneBreakdownService(db)
    return await service.get_project_scenes(project_id, act_number, chapter_number, status)


@router.post("/project/{project_id}/scenes", response_model=SceneBreakdown)
async def create_scene(
    project_id: str = Path(..., description="Project identifier"),
    scene_data: dict = {},
    db: Session = Depends(get_db)
):
    """Create a new scene breakdown."""
    service = SceneBreakdownService(db)
    scene_id = str(uuid.uuid4())
    return await service.create_scene(project_id, scene_id, scene_data)


@router.get("/scene/{scene_id}", response_model=SceneBreakdown)
async def get_scene(
    scene_id: str = Path(..., description="Scene identifier"),
    db: Session = Depends(get_db)
):
    """Get complete scene breakdown details."""
    service = SceneBreakdownService(db)
    scene = await service.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.put("/scene/{scene_id}", response_model=SceneBreakdown)
async def update_scene(
    scene_id: str = Path(..., description="Scene identifier"),
    updates: dict = {},
    db: Session = Depends(get_db)
):
    """Update scene breakdown details."""
    service = SceneBreakdownService(db)
    scene = await service.update_scene(scene_id, updates)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.delete("/scene/{scene_id}")
async def delete_scene(
    scene_id: str = Path(..., description="Scene identifier"),
    db: Session = Depends(get_db)
):
    """Delete a scene breakdown."""
    service = SceneBreakdownService(db)
    success = await service.delete_scene(scene_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"message": "Scene deleted successfully"}


@router.post("/scene/{scene_id}/reorder", response_model=List[SceneSummary])
async def reorder_scene(
    scene_id: str = Path(..., description="Scene identifier"),
    reorder_request: SceneReorderRequest = Body(...),
    db: Session = Depends(get_db)
):
    """Reorder scenes (drag and drop)."""
    service = SceneBreakdownService(db)
    return await service.reorder_scene(scene_id, reorder_request)


@router.post("/scenes/bulk-update")
async def bulk_update_scenes(
    bulk_update: SceneBulkUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Update multiple scenes at once."""
    service = SceneBreakdownService(db)
    return await service.bulk_update_scenes(bulk_update)


@router.get("/scene/{scene_id}/analysis", response_model=SceneAnalysis)
async def analyze_scene(
    scene_id: str = Path(..., description="Scene identifier"),
    db: Session = Depends(get_db)
):
    """Get scene analysis including pacing and story progression."""
    service = SceneBreakdownService(db)
    analysis = await service.analyze_scene(scene_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Scene not found")
    return analysis


@router.get("/project/{project_id}/analysis", response_model=List[SceneAnalysis])
async def analyze_project(
    project_id: str = Path(..., description="Project identifier"),
    db: Session = Depends(get_db)
):
    """Analyze all scenes in a project."""
    service = SceneBreakdownService(db)
    return await service.analyze_project(project_id)


@router.get("/project/{project_id}/canvas")
async def get_canvas_data(
    project_id: str = Path(..., description="Project identifier"),
    db: Session = Depends(get_db)
):
    """Get scene data formatted for canvas visualization."""
    service = SceneBreakdownService(db)
    return await service.get_canvas_data(project_id)


@router.post("/project/{project_id}/canvas/save")
async def save_canvas_layout(
    project_id: str = Path(..., description="Project identifier"),
    layout_data: dict = {},
    db: Session = Depends(get_db)
):
    """Save scene positions and connections for canvas view."""
    service = SceneBreakdownService(db)
    return await service.save_canvas_layout(project_id, layout_data)


@router.get("/project/{project_id}/story-circle")
async def get_story_circle_mapping(
    project_id: str = Path(..., description="Project identifier"),
    db: Session = Depends(get_db)
):
    """Get story circle mapping for scenes."""
    service = SceneBreakdownService(db)
    return await service.get_story_circle_mapping(project_id)


@router.post("/scene/{scene_id}/character")
async def add_scene_character(
    scene_id: str = Path(..., description="Scene identifier"),
    character_data: dict = {},
    db: Session = Depends(get_db)
):
    """Add a character to a scene."""
    service = SceneBreakdownService(db)
    return await service.add_scene_character(scene_id, character_data)


@router.delete("/scene/{scene_id}/character/{character_id}")
async def remove_scene_character(
    scene_id: str = Path(..., description="Scene identifier"),
    character_id: str = Path(..., description="Character identifier"),
    db: Session = Depends(get_db)
):
    """Remove a character from a scene."""
    service = SceneBreakdownService(db)
    success = await service.remove_scene_character(scene_id, character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found in scene")
    return {"message": "Character removed from scene"}


@router.post("/scene/{scene_id}/asset")
async def add_scene_asset(
    scene_id: str = Path(..., description="Scene identifier"),
    asset_data: dict = {},
    db: Session = Depends(get_db)
):
    """Add an asset to a scene."""
    service = SceneBreakdownService(db)
    return await service.add_scene_asset(scene_id, asset_data)


@router.delete("/scene/{scene_id}/asset/{asset_id}")
async def remove_scene_asset(
    scene_id: str = Path(..., description="Scene identifier"),
    asset_id: str = Path(..., description="Asset identifier"),
    db: Session = Depends(get_db)
):
    """Remove an asset from a scene."""
    service = SceneBreakdownService(db)
    success = await service.remove_scene_asset(scene_id, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found in scene")
    return {"message": "Asset removed from scene"}


@router.post("/scene/{scene_id}/story-beat")
async def add_story_beat(
    scene_id: str = Path(..., description="Scene identifier"),
    beat_data: dict = {},
    db: Session = Depends(get_db)
):
    """Add a story beat to a scene."""
    service = SceneBreakdownService(db)
    return await service.add_story_beat(scene_id, beat_data)


@router.delete("/scene/{scene_id}/story-beat/{beat_id}")
async def remove_story_beat(
    scene_id: str = Path(..., description="Scene identifier"),
    beat_id: str = Path(..., description="Beat identifier"),
    db: Session = Depends(get_db)
):
    """Remove a story beat from a scene."""
    service = SceneBreakdownService(db)
    success = await service.remove_story_beat(scene_id, beat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Story beat not found")
    return {"message": "Story beat removed"}


@router.get("/project/{project_id}/export")
async def export_breakdown(
    project_id: str = Path(..., description="Project identifier"),
    format: str = Query("json", description="Export format: json, csv, pdf"),
    db: Session = Depends(get_db)
):
    """Export scene breakdown data."""
    service = SceneBreakdownService(db)
    return await service.export_breakdown(project_id, format)