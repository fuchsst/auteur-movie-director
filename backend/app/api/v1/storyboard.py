"""
Storyboard/Pre-vis API Endpoints
STORY-087 Implementation

REST API endpoints for storyboard and pre-visualization management,
integrating with the professional script breakdown system.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from app.models.storyboard_models import (
    StoryboardSequence, StoryboardShot, StoryboardFrame,
    PrevisGenerationRequest, PrevisGenerationResult, StoryboardTemplate
)
from app.services.storyboard_service import StoryboardService
from app.services.breakdown_service import BreakdownService
from app.core.dependencies import get_asset_registry

router = APIRouter(prefix="/storyboard", tags=["storyboard"])


class StoryboardCreateRequest(BaseModel):
    """Request to create storyboard sequence."""
    project_id: str
    scene_id: str
    template_id: str = "standard"


class FrameUpdateRequest(BaseModel):
    """Request to update storyboard frame."""
    description: Optional[str] = None
    camera_angle: Optional[str] = None
    camera_movement: Optional[str] = None
    composition: Optional[str] = None
    focal_length: Optional[float] = None


class ShotUpdateRequest(BaseModel):
    """Request to update storyboard shot."""
    shot_type: Optional[str] = None
    duration: Optional[float] = None
    camera_setup: Optional[Dict[str, Any]] = None
    lighting_setup: Optional[Dict[str, Any]] = None


# Global service instances (will be properly initialized)
_storyboard_service: Optional[StoryboardService] = None
_breakdown_service: Optional[BreakdownService] = None


def get_storyboard_service() -> StoryboardService:
    """Get storyboard service instance."""
    global _storyboard_service, _breakdown_service
    
    if _storyboard_service is None:
        from pathlib import Path
        from app.services.breakdown_service import BreakdownService
        
        # Initialize services
        asset_registry = get_asset_registry()
        _breakdown_service = BreakdownService(
            project_root=str(Path("workspace")),
            asset_registry=asset_registry
        )
        _storyboard_service = StoryboardService(
            project_root=str(Path("workspace")),
            breakdown_service=_breakdown_service
        )
    
    return _storyboard_service


@router.post("/sequences", response_model=Dict[str, Any])
async def create_sequence(
    request: StoryboardCreateRequest,
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Create storyboard sequence from scene breakdown."""
    try:
        sequence = await service.create_sequence_from_breakdown(
            project_id=request.project_id,
            scene_id=request.scene_id,
            template_id=request.template_id
        )
        return {
            "sequence_id": sequence.sequence_id,
            "message": f"Storyboard sequence created for scene {request.scene_id}",
            "shots": sequence.get_shot_count(),
            "frames": sequence.get_frame_count()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sequences/{sequence_id}", response_model=Dict[str, Any])
async def get_sequence(
    sequence_id: str,
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Get storyboard sequence by ID."""
    sequence = await service.get_sequence(sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    return {
        "sequence": sequence.model_dump(),
        "metadata": {
            "total_shots": sequence.get_shot_count(),
            "total_frames": sequence.get_frame_count(),
            "total_duration": sequence.total_duration
        }
    }


@router.post("/sequences/{sequence_id}/shots", response_model=Dict[str, Any])
async def add_shot(
    sequence_id: str,
    shot_data: Dict[str, Any],
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Add shot to storyboard sequence."""
    sequence = await service.get_sequence(sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    # Create shot manually (simplified for API)
    shot = StoryboardShot(
        shot_id=f"shot_{sequence_id}_{len(sequence.shots)+1}",
        scene_id=sequence.scene_id,
        shot_number=len(sequence.shots)+1,
        **shot_data
    )
    
    sequence.add_shot(shot)
    await service._save_sequence(sequence)
    
    return {
        "shot_id": shot.shot_id,
        "shot_number": shot.shot_number,
        "message": "Shot added successfully"
    }


@router.post("/sequences/{sequence_id}/shots/{shot_id}/frames", response_model=Dict[str, Any])
async def add_frame(
    sequence_id: str,
    shot_id: str,
    frame_data: Dict[str, Any],
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Add frame to storyboard shot."""
    try:
        frame = await service.add_frame(sequence_id, shot_id, frame_data)
        return {
            "frame_id": frame.frame_id,
            "frame_number": frame.frame_number,
            "message": "Frame added successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/sequences/{sequence_id}/shots/{shot_id}/frames/{frame_id}")
async def update_frame(
    sequence_id: str,
    shot_id: str,
    frame_id: str,
    updates: FrameUpdateRequest,
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Update storyboard frame."""
    success = await service.update_frame(
        sequence_id, 
        shot_id, 
        frame_id, 
        updates.model_dump(exclude_unset=True)
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Frame not found")
    
    return {"message": "Frame updated successfully"}


@router.put("/sequences/{sequence_id}/shots/{shot_id}")
async def update_shot(
    sequence_id: str,
    shot_id: str,
    updates: ShotUpdateRequest,
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Update storyboard shot."""
    sequence = await service.get_sequence(sequence_id)
    if not sequence:
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    shot = next((s for s in sequence.shots if s.shot_id == shot_id), None)
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    
    # Update shot attributes
    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(shot, key, value)
    
    await service._save_sequence(sequence)
    return {"message": "Shot updated successfully"}


@router.post("/previs/generate", response_model=Dict[str, Any])
async def generate_previs(
    request: PrevisGenerationRequest,
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Generate pre-visualization for storyboard sequence."""
    try:
        result = await service.generate_previs(request)
        return {
            "result_id": result.result_id,
            "status": result.status,
            "message": "Pre-vis generation started"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/previs/results/{result_id}", response_model=Dict[str, Any])
async def get_previs_result(
    result_id: str,
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Get pre-visualization generation result."""
    result = await service.get_previs_result(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return result.model_dump()


@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_templates(
    service: StoryboardService = Depends(get_storyboard_service)
) -> List[Dict[str, Any]]:
    """Get available storyboard templates."""
    templates = list(service.templates.values())
    return [template.model_dump() for template in templates]


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str,
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Get storyboard template by ID."""
    template = service.templates.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template.model_dump()


@router.post("/sequences/{sequence_id}/export")
async def export_sequence(
    sequence_id: str,
    format: str = "json",
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Export storyboard sequence."""
    try:
        return await service.export_sequence(sequence_id, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sequences/{sequence_id}/sync/shotlist")
async def sync_with_shotlist(
    sequence_id: str,
    shotlist: List[Dict[str, Any]],
    service: StoryboardService = Depends(get_storyboard_service)
) -> Dict[str, Any]:
    """Sync storyboard with generative shot list."""
    try:
        from app.models.generative_shotlist import ShotSpecification
        
        # Convert shotlist data to ShotSpecification objects
        shot_specs = [ShotSpecification(**shot) for shot in shotlist]
        
        success = await service.sync_with_shotlist(sequence_id, shot_specs)
        
        if success:
            return {"message": "Successfully synced with shot list"}
        else:
            raise HTTPException(status_code=404, detail="Sequence not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))