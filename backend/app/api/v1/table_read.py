"""
Table Read API Endpoints
STORY-088 Implementation

REST API endpoints for digital table read analysis and creative bible generation.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
import logging

from app.models.table_read_models import (
    TableReadRequest, TableReadSession, CreativeBible, 
    TableReadExportRequest, AudioGenerationRequest
)
from app.services.table_read_service import TableReadService
from app.services.breakdown_service import BreakdownService
from app.core.dependencies import get_breakdown_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/table-read", tags=["table-read"])


# Dependency to get table read service
def get_table_read_service(
    breakdown_service: BreakdownService = Depends(get_breakdown_service)
) -> TableReadService:
    """Get table read service instance."""
    from app.core.config import settings
    return TableReadService(
        project_root=settings.WORKSPACE_ROOT,
        breakdown_service=breakdown_service
    )


class TableReadResponse(BaseModel):
    """Response model for table read operations."""
    session_id: str
    project_id: str
    bible_id: str
    status: str
    progress: float
    message: Optional[str] = None


class CreativeBibleResponse(BaseModel):
    """Response model for creative bible."""
    bible_id: str
    title: str
    logline: str
    synopsis: str
    total_characters: int
    total_scenes: int
    created_at: str
    updated_at: str


@router.post("/sessions", response_model=TableReadResponse)
async def create_table_read_session(
    request: TableReadRequest,
    background_tasks: BackgroundTasks,
    service: TableReadService = Depends(get_table_read_service)
) -> TableReadResponse:
    """
    Create a new digital table read session.
    
    This endpoint initiates AI-powered script analysis using Dan Harmon's Story Circle
    and generates a comprehensive creative bible.
    
    Args:
        request: TableReadRequest with script content and analysis parameters
        
    Returns:
        TableReadResponse with session details
    """
    try:
        session = await service.create_table_read_session(request)
        
        return TableReadResponse(
            session_id=session.session_id,
            project_id=session.project_id,
            bible_id=session.bible_id,
            status=session.status,
            progress=session.progress,
            message=f"Analysis session {session.session_id} created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating table read session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=TableReadResponse)
async def get_session_status(
    session_id: str,
    service: TableReadService = Depends(get_table_read_service)
) -> TableReadResponse:
    """
    Get the status of a table read session.
    
    Args:
        session_id: The session ID to check
        
    Returns:
        TableReadResponse with current session status
    """
    session = await service.get_session_status(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return TableReadResponse(
        session_id=session.session_id,
        project_id=session.project_id,
        bible_id=session.bible_id,
        status=session.status,
        progress=session.progress,
        message=session.current_analysis or session.error_message
    )


@router.get("/sessions/{session_id}/results", response_model=CreativeBible)
async def get_table_read_results(
    session_id: str,
    service: TableReadService = Depends(get_table_read_service)
) -> CreativeBible:
    """
    Get the completed table read results and creative bible.
    
    Args:
        session_id: The session ID to retrieve results for
        
    Returns:
        Complete CreativeBible with all analysis results
    """
    session = await service.get_session_status(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != "completed":
        raise HTTPException(
            status_code=202, 
            detail=f"Analysis in progress: {session.progress * 100:.1f}%"
        )
    
    if not session.results:
        raise HTTPException(status_code=404, detail="Results not available")
    
    return session.results


@router.get("/bibles/{bible_id}", response_model=CreativeBibleResponse)
async def get_creative_bible_summary(
    bible_id: str,
    service: TableReadService = Depends(get_table_read_service)
) -> CreativeBibleResponse:
    """
    Get a summary of the creative bible.
    
    Args:
        bible_id: The bible ID to retrieve
        
    Returns:
        CreativeBibleResponse with summary information
    """
    bible = await service.get_creative_bible(bible_id)
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")
    
    return CreativeBibleResponse(
        bible_id=bible.bible_id,
        title=bible.title,
        logline=bible.logline,
        synopsis=bible.synopsis,
        total_characters=len(bible.character_bios),
        total_scenes=len(bible.scene_analyses),
        created_at=bible.created_at.isoformat(),
        updated_at=bible.updated_at.isoformat()
    )


@router.get("/bibles/{bible_id}/full", response_model=CreativeBible)
async def get_creative_bible_full(
    bible_id: str,
    service: TableReadService = Depends(get_table_read_service)
) -> CreativeBible:
    """
    Get the complete creative bible with all details.
    
    Args:
        bible_id: The bible ID to retrieve
        
    Returns:
        Complete CreativeBible with full details
    """
    bible = await service.get_creative_bible(bible_id)
    if not bible:
        raise HTTPException(status_code=404, detail="Bible not found")
    
    return bible


@router.post("/bibles/{bible_id}/export")
async def export_creative_bible(
    bible_id: str,
    request: TableReadExportRequest,
    service: TableReadService = Depends(get_table_read_service)
) -> Dict[str, Any]:
    """
    Export creative bible in specified format.
    
    Args:
        bible_id: The bible ID to export
        request: Export format and options
        
    Returns:
        Export result with file information
    """
    try:
        result = await service.export_bible(bible_id, request.format)
        return result
    except Exception as e:
        logger.error(f"Error exporting bible {bible_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[TableReadResponse])
async def list_sessions(
    project_id: Optional[str] = None,
    service: TableReadService = Depends(get_table_read_service)
) -> List[TableReadResponse]:
    """
    List all table read sessions.
    
    Args:
        project_id: Optional project ID to filter sessions
        
    Returns:
        List of TableReadResponse objects
    """
    sessions = await service.list_sessions(project_id or "")
    
    return [
        TableReadResponse(
            session_id=session.session_id,
            project_id=session.project_id,
            bible_id=session.bible_id,
            status=session.status,
            progress=session.progress
        )
        for session in sessions
    ]


@router.post("/bibles/{bible_id}/audio")
async def generate_audio_table_read(
    bible_id: str,
    request: AudioGenerationRequest,
    service: TableReadService = Depends(get_table_read_service)
) -> Dict[str, str]:
    """
    Generate audio table read from creative bible.
    
    Args:
        bible_id: The bible ID to generate audio for
        request: Audio generation parameters
        
    Returns:
        Audio generation task ID
    """
    # This would integrate with audio generation services
    # For now, return a placeholder response
    return {
        "message": "Audio generation not yet implemented",
        "bible_id": bible_id,
        "session_id": request.session_id
    }


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "table-read"}

