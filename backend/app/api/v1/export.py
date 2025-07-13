"""
Project export API endpoints.

Handles exporting projects as portable archives with progress tracking.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse

from app.schemas.project import ExportOptions
from app.services.export import export_service
from app.services.websocket import manager as websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/{project_id}")
async def export_project(
    project_id: str,
    options: ExportOptions,
    background_tasks: BackgroundTasks,
    client_id: str | None = Query(None, description="WebSocket client ID for progress updates"),
) -> dict[str, Any]:
    """
    Export a project as a portable archive.

    Args:
        project_id: Project identifier
        options: Export configuration options
        background_tasks: FastAPI background tasks
        client_id: Optional WebSocket client ID for progress updates

    Returns:
        Export task information
    """
    try:
        # Define progress callback if client_id provided
        async def progress_callback(progress: float, message: str):
            if client_id:
                await websocket_manager.send_personal_message(
                    {
                        "type": "export_progress",
                        "project_id": project_id,
                        "progress": progress,
                        "message": message,
                    },
                    client_id,
                )

        # Start export in background
        export_id = f"export_{project_id}_{asyncio.get_event_loop().time()}"

        async def run_export():
            try:
                archive_path = await export_service.export_project(
                    project_id, options, progress_callback
                )

                # Send completion notification
                if client_id:
                    await websocket_manager.send_personal_message(
                        {
                            "type": "export_complete",
                            "project_id": project_id,
                            "export_id": export_id,
                            "archive_path": str(archive_path),
                            "filename": Path(archive_path).name,
                        },
                        client_id,
                    )
            except Exception as e:
                logger.error(f"Export failed for project {project_id}: {str(e)}")
                if client_id:
                    await websocket_manager.send_personal_message(
                        {
                            "type": "export_error",
                            "project_id": project_id,
                            "export_id": export_id,
                            "error": str(e),
                        },
                        client_id,
                    )

        # Add to background tasks
        background_tasks.add_task(run_export)

        return {
            "export_id": export_id,
            "project_id": project_id,
            "status": "started",
            "message": "Export started in background",
        }

    except Exception as e:
        logger.error(f"Failed to start export for {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/{project_id}/download/{filename}")
async def download_export(project_id: str, filename: str) -> FileResponse:
    """
    Download an exported project archive.

    Args:
        project_id: Project identifier
        filename: Archive filename

    Returns:
        File download response
    """
    # Verify file exists and belongs to project
    file_path = export_service.temp_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")

    # Verify filename matches project
    if not filename.startswith(f"{project_id}_export_"):
        raise HTTPException(status_code=403, detail="Invalid export file")

    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")


@router.get("/list")
async def list_exports() -> dict[str, Any]:
    """
    List available export files.

    Returns:
        List of export files with metadata
    """
    try:
        exports = export_service.list_exports()
        return {"exports": exports, "count": len(exports)}
    except Exception as e:
        logger.error(f"Failed to list exports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.delete("/cleanup")
async def cleanup_exports(days: int = Query(7, ge=1, le=30)) -> dict[str, Any]:
    """
    Clean up old export files.

    Args:
        days: Number of days to keep exports (default: 7)

    Returns:
        Cleanup result
    """
    try:
        export_service.cleanup_old_exports(days)
        return {"status": "success", "message": f"Cleaned up exports older than {days} days"}
    except Exception as e:
        logger.error(f"Failed to cleanup exports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from None
