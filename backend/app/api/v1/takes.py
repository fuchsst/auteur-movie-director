"""
API endpoints for takes management.
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.redis_client import redis_client
from app.schemas.takes import (
    CreateTakeRequest,
    CreateTakeResponse,
    DeleteTakeResponse,
    SetActiveTakeRequest,
    TakeCleanupRequest,
    TakeCleanupResponse,
    TakeExportRequest,
    TakeExportResponse,
    TakeListResponse,
    TakeMetadata,
)
from app.services.takes import takes_service
from app.services.workspace import get_workspace_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/takes", tags=["takes"])


@router.post("/projects/{project_id}/shots/{shot_id}/takes", response_model=CreateTakeResponse)
async def create_take(project_id: str, shot_id: str, request: CreateTakeRequest):
    """
    Create a new take for a shot.

    This initiates the generation process and returns immediately with a task ID.
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get next take number
        take_number = await takes_service.get_next_take_number(project_path, shot_id)
        take_id = f"take_{str(take_number).zfill(3)}"

        # Create take directory
        take_dir = await takes_service.create_take_directory(project_path, shot_id, take_number)

        # Save initial metadata
        await takes_service.save_take_metadata(
            take_dir=take_dir,
            take_id=take_id,
            shot_id=shot_id,
            generation_params=request.generation_params.dict(),
            quality=request.quality,
        )

        # For now, we'll create a placeholder task
        # In the future, this will dispatch to the actual generation pipeline
        task_id = f"{project_id}:take:{shot_id}:{take_id}"

        # Simulate task creation
        await redis_client.publish_progress(
            project_id,
            task_id,
            {
                "progress": 0.0,
                "message": f"Creating {take_id} for {shot_id}",
            },
        )

        # If this is the first take, make it active
        existing_takes = await takes_service.list_takes(project_path, shot_id)
        if len(existing_takes) == 1:  # Just created
            await takes_service.set_active_take(project_path, shot_id, take_id)

        return CreateTakeResponse(
            take_id=take_id,
            take_number=take_number,
            status="queued",
            task_id=task_id,
        )

    except Exception as e:
        logger.error(f"Error creating take: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/projects/{project_id}/shots/{shot_id}/takes", response_model=TakeListResponse)
async def list_takes(
    project_id: str,
    shot_id: str,
    include_failed: bool = Query(True, description="Include failed takes"),
):
    """
    List all takes for a shot.

    Returns takes sorted by creation date (newest first).
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get takes
        takes = await takes_service.list_takes(project_path, shot_id)

        # Filter out failed if requested
        if not include_failed:
            takes = [t for t in takes if t.get("status") != "failed"]

        # Sort by creation date
        takes.sort(key=lambda t: t.get("created", ""), reverse=True)

        # Get active take
        active_take_id = await takes_service.get_active_take(project_path, shot_id)

        # Convert to response models
        take_models = []
        for take in takes:
            try:
                take_models.append(TakeMetadata(**take))
            except Exception as e:
                logger.warning(f"Invalid take metadata: {e}")
                continue

        return TakeListResponse(
            takes=take_models,
            active_take_id=active_take_id,
            total=len(take_models),
        )

    except Exception as e:
        logger.error(f"Error listing takes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/projects/{project_id}/shots/{shot_id}/takes/{take_id}", response_model=TakeMetadata)
async def get_take(project_id: str, shot_id: str, take_id: str):
    """
    Get details for a specific take.
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get takes and find the specific one
        takes = await takes_service.list_takes(project_path, shot_id)
        take = next((t for t in takes if t.get("id") == take_id), None)

        if not take:
            raise HTTPException(status_code=404, detail="Take not found")

        return TakeMetadata(**take)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting take: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/projects/{project_id}/shots/{shot_id}/active-take")
async def set_active_take(project_id: str, shot_id: str, request: SetActiveTakeRequest):
    """
    Set the active take for a shot.

    The active take is the one used in the final edit.
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Set active take
        success = await takes_service.set_active_take(project_path, shot_id, request.take_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to set active take")

        return {"success": True, "message": f"Set active take to {request.take_id}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting active take: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/projects/{project_id}/shots/{shot_id}/takes/{take_id}",
    response_model=DeleteTakeResponse,
)
async def delete_take(project_id: str, shot_id: str, take_id: str):
    """
    Delete a take (soft delete).

    The take is marked as deleted but files are kept for recovery.
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if this is the active take
        active_take = await takes_service.get_active_take(project_path, shot_id)
        was_active = active_take == take_id

        # Delete take
        success = await takes_service.delete_take(project_path, shot_id, take_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete take")

        # Get new active take if needed
        new_active_take_id = None
        if was_active:
            new_active_take_id = await takes_service.get_active_take(project_path, shot_id)

        return DeleteTakeResponse(
            success=True,
            message=f"Deleted take {take_id}",
            new_active_take_id=new_active_take_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting take: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/projects/{project_id}/shots/{shot_id}/takes/export",
    response_model=TakeExportResponse,
)
async def export_take(project_id: str, shot_id: str, request: TakeExportRequest):
    """
    Export a take to the exports directory.

    Copies the take file and optionally its metadata to the exports folder.
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Export directory
        export_dir = project_path / "06_Exports"

        # Export take
        export_path = await takes_service.export_take(
            project_path, shot_id, request.take_id, export_dir
        )

        if not export_path:
            raise HTTPException(status_code=400, detail="Failed to export take")

        return TakeExportResponse(
            success=True,
            export_path=str(export_path.relative_to(project_path)),
            message=f"Exported take {request.take_id}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting take: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/projects/{project_id}/shots/{shot_id}/takes/cleanup",
    response_model=TakeCleanupResponse,
)
async def cleanup_takes(project_id: str, shot_id: str, request: TakeCleanupRequest):
    """
    Clean up old takes for a shot.

    Keeps the most recent takes and deletes older ones.
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get current take count
        takes = await takes_service.list_takes(project_path, shot_id)
        initial_count = len(takes)

        # Cleanup
        deleted_count = await takes_service.cleanup_old_takes(
            project_path, shot_id, request.keep_count
        )

        return TakeCleanupResponse(
            deleted_count=deleted_count,
            remaining_count=initial_count - deleted_count,
            message=f"Cleaned up {deleted_count} old takes",
        )

    except Exception as e:
        logger.error(f"Error cleaning up takes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
