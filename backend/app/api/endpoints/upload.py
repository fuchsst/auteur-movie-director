"""
File upload endpoints with automatic organization and Git LFS tracking.
"""

import logging
import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.dispatcher import task_dispatcher
from app.redis_client import redis_client
from app.services.git import git_service
from app.services.workspace import get_workspace_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# File type categories
FILE_CATEGORIES = {
    "character": {
        "extensions": [".png", ".jpg", ".jpeg", ".safetensors", ".pt", ".pth"],
        "directory": "01_Assets/Characters",
        "metadata_required": ["character_name"],
    },
    "style": {
        "extensions": [".safetensors", ".ckpt", ".pt", ".pth", ".png", ".jpg"],
        "directory": "01_Assets/Styles",
        "metadata_required": ["style_name"],
    },
    "location": {
        "extensions": [".png", ".jpg", ".jpeg", ".exr", ".hdr"],
        "directory": "01_Assets/Locations",
        "metadata_required": ["location_name"],
    },
    "music": {
        "extensions": [".mp3", ".wav", ".aiff", ".flac", ".ogg"],
        "directory": "01_Assets/Music",
        "metadata_required": [],
    },
    "script": {
        "extensions": [".txt", ".md", ".pdf", ".docx", ".fountain"],
        "directory": "01_Assets/Scripts",
        "metadata_required": [],
    },
    "model": {
        "extensions": [".safetensors", ".ckpt", ".pt", ".pth"],
        "directory": "04_Project_Files/ComfyUI/models",
        "metadata_required": ["model_type"],
    },
}


@router.post("/{project_id}/{category}")
async def upload_file(
    project_id: str,
    category: str,
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
    auto_commit: bool = Form(True),
):
    """
    Upload a file to the project with automatic organization.

    - Validates file type based on category
    - Organizes file into correct directory
    - Tracks large files with Git LFS
    - Optionally commits the file to Git
    """
    try:
        # Validate category
        if category not in FILE_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {list(FILE_CATEGORIES.keys())}",
            )

        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        allowed_exts = FILE_CATEGORIES[category]["extensions"]

        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed for category {category}. "
                f"Allowed types: {', '.join(allowed_exts)}",
            )

        # Parse metadata
        import json

        try:
            file_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            file_metadata = {}

        # Validate required metadata
        required_fields = FILE_CATEGORIES[category]["metadata_required"]
        missing_fields = [f for f in required_fields if f not in file_metadata]

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required metadata fields: {', '.join(missing_fields)}",
            )

        # Create task ID for progress tracking
        task_id = f"{project_id}:upload:{file.filename}:{int(os.urandom(4).hex(), 16)}"

        # Start progress
        await redis_client.publish_progress(
            project_id,
            task_id,
            {"progress": 0.1, "message": f"Uploading {file.filename}"},
        )

        # Determine target directory
        target_dir = project_path / FILE_CATEGORIES[category]["directory"]

        # Handle special cases
        if category == "character" and "character_name" in file_metadata:
            # Create character-specific directory
            char_name = file_metadata["character_name"]
            target_dir = workspace_service.create_character_structure(project_path, char_name)

            # Determine subdirectory based on file type
            if file_ext in [".safetensors", ".pt", ".pth"]:
                target_dir = target_dir / "lora"
            elif file_ext in [".png", ".jpg", ".jpeg"] and "is_base_face" in file_metadata:
                target_dir = target_dir / "base"

        # Ensure directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename if exists
        target_path = target_dir / file.filename
        if target_path.exists():
            base_name = target_path.stem
            extension = target_path.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{base_name}_{counter}{extension}"
                counter += 1

        # Save file with progress tracking
        await redis_client.publish_progress(
            project_id,
            task_id,
            {"progress": 0.3, "message": "Writing file to disk"},
        )

        # Read and write in chunks
        chunk_size = 1024 * 1024  # 1MB chunks
        total_size = 0

        with open(target_path, "wb") as f:
            while chunk := await file.read(chunk_size):
                f.write(chunk)
                total_size += len(chunk)

                # Update progress based on estimated size
                if file.size and file.size > 0:
                    progress = 0.3 + (0.5 * (total_size / file.size))
                    await redis_client.publish_progress(
                        project_id,
                        task_id,
                        {
                            "progress": progress,
                            "message": f"Writing {total_size / 1024 / 1024:.1f}MB",
                        },
                    )

        # Get file info
        file_stats = target_path.stat()
        file_size_mb = file_stats.st_size / (1024 * 1024)

        # Track with Git LFS if large
        await redis_client.publish_progress(
            project_id,
            task_id,
            {"progress": 0.8, "message": "Checking Git LFS requirements"},
        )

        if file_size_mb > settings.git_lfs_threshold_mb:
            relative_path = target_path.relative_to(project_path)
            await git_service.track_large_file(project_path, str(relative_path))

        # Auto-commit if requested
        if auto_commit:
            await redis_client.publish_progress(
                project_id,
                task_id,
                {"progress": 0.9, "message": "Committing to Git"},
            )

            relative_path = target_path.relative_to(project_path)
            commit_message = f"Add {category} asset: {file.filename}"

            await git_service.commit_changes(
                project_path,
                commit_message,
                prefix="asset",
                files=[str(relative_path)],
            )

        # Complete
        await redis_client.publish_progress(
            project_id,
            task_id,
            {
                "progress": 1.0,
                "message": "Upload complete",
                "result": {
                    "filename": target_path.name,
                    "path": str(target_path.relative_to(project_path)),
                    "size": file_stats.st_size,
                    "category": category,
                    "metadata": file_metadata,
                },
            },
        )

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "filename": target_path.name,
                "path": str(target_path.relative_to(project_path)),
                "size": file_stats.st_size,
                "size_mb": round(file_size_mb, 2),
                "git_lfs": file_size_mb > settings.git_lfs_threshold_mb,
                "task_id": task_id,
            },
        )

    except Exception as e:
        logger.error(f"Upload error: {e}")

        # Send error progress
        if "task_id" in locals():
            await redis_client.publish_progress(
                project_id,
                task_id,
                {"error": str(e), "message": "Upload failed"},
            )

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/batch/{category}")
async def upload_files_batch(
    project_id: str,
    category: str,
    files: List[UploadFile] = File(...),
    metadata: str = Form("{}"),
    auto_commit: bool = Form(True),
):
    """
    Upload multiple files at once.

    Useful for uploading character variations or style collections.
    """
    try:
        results = []

        for file in files:
            # Upload each file
            result = await upload_file(
                project_id=project_id,
                category=category,
                file=file,
                metadata=metadata,
                auto_commit=False,  # Don't commit each file individually
            )

            results.append(result.body)

        # Commit all files at once if requested
        if auto_commit and results:
            workspace_service = get_workspace_service()
            project_path = workspace_service.get_project_path(project_id)
            if project_path:
                file_paths = [r["path"] for r in results if "path" in r]
                commit_message = f"Add {len(files)} {category} assets"

                await git_service.commit_changes(
                    project_path,
                    commit_message,
                    prefix="asset",
                    files=file_paths,
                )

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "uploaded": len(results),
                "files": results,
            },
        )

    except Exception as e:
        logger.error(f"Batch upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_upload_categories():
    """
    Get available upload categories and their configurations.
    """
    return {
        category: {
            "extensions": info["extensions"],
            "directory": info["directory"],
            "required_metadata": info["metadata_required"],
        }
        for category, info in FILE_CATEGORIES.items()
    }
