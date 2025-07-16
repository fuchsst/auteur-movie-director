"""API endpoints for progress tracking"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, WebSocket, Depends, Query

from .models import ProgressResponse, LogsResponse, LogEntry, BatchProgress
from .tracker import ProgressTracker
from .websocket_handler import ProgressWebSocketHandler
from ..core.dependencies import get_progress_tracker, get_ws_manager


router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/tasks/{task_id}")
async def get_task_progress(
    task_id: str,
    tracker: ProgressTracker = Depends(get_progress_tracker)
) -> ProgressResponse:
    """Get current progress for a task"""
    progress = await tracker.get_progress(task_id)
    
    if not progress:
        raise HTTPException(404, f"Task {task_id} not found")
    
    # Calculate elapsed time
    elapsed_time = None
    if progress.started_at:
        if progress.completed_at:
            elapsed_time = (progress.completed_at - progress.started_at).total_seconds()
        else:
            elapsed_time = (datetime.now() - progress.started_at).total_seconds()
    
    return ProgressResponse(
        task_id=task_id,
        status=progress.status,
        overall_progress=progress.overall_progress,
        current_stage=progress.current_stage,
        stages=[
            {
                'id': stage_id,
                'name': stage.name,
                'status': stage.status.value,
                'progress': stage.progress,
                'message': stage.message,
                'duration': stage.duration.total_seconds() if stage.duration else None,
                'metadata': stage.metadata
            }
            for stage_id, stage in progress.stages.items()
        ],
        eta=progress.eta,
        preview_url=progress.preview_url,
        elapsed_time=elapsed_time,
        resource_usage=progress.resource_usage
    )


@router.get("/tasks/{task_id}/logs")
async def get_task_logs(
    task_id: str,
    since: Optional[datetime] = Query(None, description="Get logs since this timestamp"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    tracker: ProgressTracker = Depends(get_progress_tracker)
) -> LogsResponse:
    """Get execution logs for a task"""
    progress = await tracker.get_progress(task_id)
    
    if not progress:
        raise HTTPException(404, f"Task {task_id} not found")
    
    # Filter logs
    logs = progress.logs
    total_count = len(logs)
    
    if since:
        logs = [
            log for log in logs 
            if datetime.fromisoformat(log['timestamp']) > since
        ]
    
    if level:
        logs = [log for log in logs if log.get('level') == level]
    
    filtered_count = len(logs)
    
    # Apply limit
    if len(logs) > limit:
        logs = logs[-limit:]  # Get most recent logs
    
    # Convert to LogEntry objects
    log_entries = [
        LogEntry(
            timestamp=datetime.fromisoformat(log['timestamp']),
            level=log.get('level', 'info'),
            message=log.get('message', ''),
            task_id=task_id,
            stage=log.get('stage'),
            metadata=log.get('metadata', {})
        )
        for log in logs
    ]
    
    return LogsResponse(
        task_id=task_id,
        logs=log_entries,
        total_count=total_count,
        filtered_count=filtered_count
    )


@router.get("/batch/{batch_id}")
async def get_batch_progress(
    batch_id: str,
    task_ids: List[str] = Query(..., description="Task IDs in the batch"),
    tracker: ProgressTracker = Depends(get_progress_tracker)
) -> BatchProgress:
    """Get aggregated progress for a batch of tasks"""
    return await tracker.get_batch_progress(batch_id, task_ids)


@router.get("/tasks/{task_id}/history")
async def get_task_history(
    task_id: str,
    tracker: ProgressTracker = Depends(get_progress_tracker)
) -> dict:
    """Get complete history for a task including all stage transitions"""
    progress = await tracker.get_progress(task_id)
    
    if not progress:
        raise HTTPException(404, f"Task {task_id} not found")
    
    # Build stage history
    stage_history = []
    for stage_id, stage in progress.stages.items():
        history_entry = {
            'stage_id': stage_id,
            'name': stage.name,
            'status': stage.status.value,
            'final_progress': stage.progress,
            'started_at': stage.started_at.isoformat() if stage.started_at else None,
            'completed_at': stage.completed_at.isoformat() if stage.completed_at else None,
            'duration': stage.duration.total_seconds() if stage.duration else None,
            'message': stage.message,
            'metadata': stage.metadata
        }
        stage_history.append(history_entry)
    
    return {
        'task_id': task_id,
        'template_id': progress.template_id,
        'status': progress.status.value,
        'created_at': progress.created_at.isoformat(),
        'started_at': progress.started_at.isoformat() if progress.started_at else None,
        'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
        'total_duration': progress.total_duration.total_seconds() if progress.total_duration else None,
        'final_progress': progress.overall_progress,
        'stage_history': stage_history,
        'error': progress.error,
        'resource_usage': progress.resource_usage
    }


@router.get("/previews/{filename}")
async def get_preview_image(
    filename: str,
    tracker: ProgressTracker = Depends(get_progress_tracker)
):
    """Get preview image by filename"""
    # TODO: Implement preview image serving
    # This would serve the actual preview images from the preview directory
    raise HTTPException(501, "Preview serving not implemented")


@router.websocket("/ws")
async def websocket_progress(
    websocket: WebSocket,
    client_id: str = Query(..., description="Unique client identifier"),
    tracker: ProgressTracker = Depends(get_progress_tracker),
    ws_manager = Depends(get_ws_manager)
):
    """WebSocket endpoint for real-time progress updates"""
    handler = ProgressWebSocketHandler(tracker, ws_manager)
    await handler.handle_connection(websocket, client_id)