"""
Project import API endpoints.

Handles uploading and importing project archives with validation and progress tracking.
"""

import asyncio
import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Query, UploadFile

from app.schemas.project import ImportOptions, ValidationResult
from app.services.import_ import import_service
from app.services.websocket import manager as websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/upload")
async def upload_archive(
    file: UploadFile = File(..., description="Project archive to import"),
    client_id: str | None = Query(None, description="WebSocket client ID for progress updates"),
) -> dict[str, Any]:
    """
    Upload a project archive for import.

    Args:
        file: Archive file to upload
        client_id: Optional WebSocket client ID

    Returns:
        Upload information with temporary file path
    """
    try:
        # Validate file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in [".zip", ".gz"] and not file.filename.endswith(".tar.gz"):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Only ZIP and TAR.GZ archives are supported.",
            )

        # Create temporary file
        temp_dir = Path(tempfile.gettempdir()) / "auteur-uploads"
        temp_dir.mkdir(exist_ok=True)

        temp_path = temp_dir / f"upload_{asyncio.get_event_loop().time()}_{file.filename}"

        # Save uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate archive structure
        validation = await import_service.validate_archive(str(temp_path))

        return {
            "filename": file.filename,
            "size": temp_path.stat().st_size,
            "temp_path": str(temp_path),
            "validation": validation.dict(),
        }

    except Exception as e:
        logger.error(f"Failed to upload archive: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/")
async def import_project(
    temp_path: str = Form(..., description="Temporary path from upload"),
    target_name: str = Form(..., description="Target project name"),
    options: str = Form("{}", description="Import options as JSON"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    client_id: str | None = Query(None, description="WebSocket client ID for progress updates"),
) -> dict[str, Any]:
    """
    Import a project from an uploaded archive.

    Args:
        temp_path: Path to uploaded archive
        target_name: Target project name
        options: Import options as JSON string
        background_tasks: FastAPI background tasks
        client_id: Optional WebSocket client ID

    Returns:
        Import task information
    """
    try:
        # Parse options
        import json

        options_dict = json.loads(options)
        import_options = ImportOptions(**options_dict)

        # Verify temp file exists
        temp_file = Path(temp_path)
        if not temp_file.exists():
            raise HTTPException(status_code=404, detail="Upload file not found")

        # Define progress callback
        async def progress_callback(progress: float, message: str):
            if client_id:
                await websocket_manager.send_personal_message(
                    {"type": "import_progress", "progress": progress, "message": message}, client_id
                )

        # Start import in background
        import_id = f"import_{target_name}_{asyncio.get_event_loop().time()}"

        async def run_import():
            try:
                result = await import_service.import_archive(
                    str(temp_file), target_name, import_options, progress_callback
                )

                # Send completion notification
                if client_id:
                    await websocket_manager.send_personal_message(
                        {
                            "type": "import_complete",
                            "import_id": import_id,
                            "result": result.dict(),
                        },
                        client_id,
                    )

                # Cleanup temp file
                temp_file.unlink(missing_ok=True)

            except Exception as e:
                logger.error(f"Import failed: {str(e)}")
                if client_id:
                    await websocket_manager.send_personal_message(
                        {"type": "import_error", "import_id": import_id, "error": str(e)}, client_id
                    )
                # Cleanup temp file even on error
                temp_file.unlink(missing_ok=True)

        # Add to background tasks
        background_tasks.add_task(run_import)

        return {
            "import_id": import_id,
            "status": "started",
            "message": "Import started in background",
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid options format") from None
    except Exception as e:
        logger.error(f"Failed to start import: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.post("/validate")
async def validate_archive(
    file: UploadFile = File(..., description="Archive to validate"),
) -> ValidationResult:
    """
    Validate a project archive without importing.

    Args:
        file: Archive file to validate

    Returns:
        Validation result
    """
    temp_path = None
    try:
        # Save to temp file
        temp_dir = Path(tempfile.gettempdir()) / "auteur-validate"
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / f"validate_{asyncio.get_event_loop().time()}_{file.filename}"

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate
        result = await import_service.validate_archive(str(temp_path))
        return result

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from None
    finally:
        # Cleanup temp file
        if temp_path and temp_path.exists():
            temp_path.unlink()


@router.delete("/cleanup")
async def cleanup_temp_files(
    days: int = Query(1, ge=0, le=7, description="Delete files older than days"),
) -> dict[str, Any]:
    """
    Clean up old temporary upload files.

    Args:
        days: Number of days to keep files

    Returns:
        Cleanup result
    """
    try:
        temp_dirs = [
            Path(tempfile.gettempdir()) / "auteur-uploads",
            Path(tempfile.gettempdir()) / "auteur-imports",
            Path(tempfile.gettempdir()) / "auteur-validate",
        ]

        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        for temp_dir in temp_dirs:
            if temp_dir.exists():
                for file in temp_dir.iterdir():
                    if file.is_file() and file.stat().st_mtime < cutoff:
                        file.unlink()
                        deleted_count += 1

        return {
            "status": "success",
            "deleted_files": deleted_count,
            "message": f"Cleaned up {deleted_count} temporary files older than {days} days",
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from None
