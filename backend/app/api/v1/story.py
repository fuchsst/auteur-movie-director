from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.database import get_db
from app.models.story_models import (
    SceneTimeline, StoryBeat, CharacterArc, 
    NarrativeAnalytics, StoryStructureValidation
)
from app.services.story_service import StoryService
from app.schemas.story_schemas import (
    SceneTimelineResponse, StoryBeatResponse, CharacterArcResponse,
    NarrativeAnalyticsResponse, StructureValidationResponse,
    SceneUpdateRequest, BeatAnalysisRequest
)

router = APIRouter(prefix="/story", tags=["story"])

@router.get("/{project_id}/timeline", response_model=SceneTimelineResponse)
async def get_story_timeline(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get complete story timeline with scenes, beats, and character arcs."""
    try:
        service = StoryService(db)
        timeline_data = await service.generate_timeline(project_id)
        return SceneTimelineResponse(**timeline_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/beats", response_model=StoryBeatResponse)
async def get_story_beats(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get all story beats organized by framework."""
    try:
        service = StoryService(db)
        beats = await service.get_story_beats(project_id)
        return StoryBeatResponse(beats=beats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/validate-structure", response_model=StructureValidationResponse)
async def validate_story_structure(
    project_id: str,
    framework: str = "three_act",
    db: Session = Depends(get_db)
):
    """Validate story structure against selected framework."""
    try:
        service = StoryService(db)
        validation = await service.validate_structure(project_id, framework)
        return StructureValidationResponse(**validation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/characters/{project_id}/arcs", response_model=CharacterArcResponse)
async def get_character_arcs(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get character arc data for all characters."""
    try:
        service = StoryService(db)
        arcs = await service.get_character_arcs(project_id)
        return CharacterArcResponse(character_arcs=arcs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{scene_id}/beat-analysis")
async def update_scene_beat(
    scene_id: str,
    request: BeatAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Update beat analysis for a specific scene."""
    try:
        service = StoryService(db)
        updated_scene = await service.update_scene_beat(scene_id, request)
        return {"scene": updated_scene}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/optimize-pacing")
async def optimize_story_pacing(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Optimize story pacing based on narrative analysis."""
    try:
        service = StoryService(db)
        optimization = await service.optimize_pacing(project_id)
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/narrative-quality", response_model=NarrativeAnalyticsResponse)
async def get_narrative_analytics(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get comprehensive narrative analytics."""
    try:
        service = StoryService(db)
        analytics = await service.get_narrative_analytics(project_id)
        return NarrativeAnalyticsResponse(analytics=analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/export-story-report")
async def export_story_report(
    project_id: str,
    format: str = "pdf",
    db: Session = Depends(get_db)
):
    """Export comprehensive story report."""
    try:
        service = StoryService(db)
        report_url = await service.export_story_report(project_id, format)
        return {"url": report_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))