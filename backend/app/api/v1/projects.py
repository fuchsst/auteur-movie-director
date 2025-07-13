"""
Project API endpoints for comprehensive project management.
Implements STORY-027 requirements with RESTful design.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.schemas.project import (
    ProjectCreate,
    ProjectManifest,
    ProjectStructureValidation,
    ProjectUpdate,
)
from app.services.git import git_service
from app.services.workspace import get_workspace_service
from app.services.takes import takes_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


class ErrorDetail(BaseModel):
    """Error response detail"""

    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Consistent error response format"""

    error: ErrorDetail


class ProjectResponse(BaseModel):
    """Project response with full details"""

    id: str
    name: str
    path: str
    created: datetime
    modified: datetime
    size_bytes: int
    quality: str
    narrative_structure: str
    git_status: str | None = None
    manifest: ProjectManifest


class ProjectListResponse(BaseModel):
    """Project list response with pagination info"""

    projects: list[ProjectResponse]
    total: int
    skip: int
    limit: int


class DeleteResponse(BaseModel):
    """Delete operation response"""

    success: bool
    message: str
    deleted_path: str


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum projects to return"),
    sort_by: str = Query("created", description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    quality: str | None = Query(None, description="Filter by quality level"),
    structure: str | None = Query(None, description="Filter by narrative structure"),
):
    """
    List all projects with metadata and pagination support.

    Supports filtering by quality and narrative structure.
    Sorting available by: name, created, modified.
    """
    try:
        workspace_service = get_workspace_service()
        all_projects = workspace_service.list_projects()

        # Convert to response format
        project_list = []
        for project in all_projects:
            manifest = project["manifest"]

            # Apply filters
            if quality and manifest.get("quality") != quality:
                continue
            if structure and manifest.get("narrative", {}).get("structure") != structure:
                continue

            # Get project size
            project_path = Path(project["path"])
            size_bytes = sum(f.stat().st_size for f in project_path.rglob("*") if f.is_file())

            # Get Git status
            git_status = "uninitialized"
            if project["validation"].git_initialized:
                status = await git_service.get_status(project_path)
                if status.get("is_dirty"):
                    git_status = "modified"
                else:
                    git_status = "clean"

            project_list.append(
                ProjectResponse(
                    id=manifest["id"],
                    name=manifest["name"],
                    path=project["path"],
                    created=datetime.fromisoformat(manifest["created"]),
                    modified=datetime.fromisoformat(manifest["modified"]),
                    size_bytes=size_bytes,
                    quality=manifest["quality"],
                    narrative_structure=manifest["narrative"]["structure"],
                    git_status=git_status,
                    manifest=ProjectManifest(**manifest),
                )
            )

        # Sort projects
        if sort_by == "name":
            project_list.sort(key=lambda p: p.name, reverse=(order == "desc"))
        elif sort_by == "modified":
            project_list.sort(key=lambda p: p.modified, reverse=(order == "desc"))
        else:  # Default to created
            project_list.sort(key=lambda p: p.created, reverse=(order == "desc"))

        # Apply pagination
        paginated = project_list[skip : skip + limit]

        return paginated

    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=list[ProjectResponse])
async def search_projects(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Search projects by name.

    Case-insensitive partial matching on project names.
    """
    try:
        workspace_service = get_workspace_service()
        all_projects = workspace_service.list_projects()

        # Search filter
        search_query = q.lower()
        matching_projects = []

        for project in all_projects:
            manifest = project["manifest"]
            if search_query in manifest["name"].lower():
                # Get project details
                project_path = Path(project["path"])
                size_bytes = sum(f.stat().st_size for f in project_path.rglob("*") if f.is_file())

                git_status = "uninitialized"
                if project["validation"].git_initialized:
                    status = await git_service.get_status(project_path)
                    git_status = "modified" if status.get("is_dirty") else "clean"

                matching_projects.append(
                    ProjectResponse(
                        id=manifest["id"],
                        name=manifest["name"],
                        path=project["path"],
                        created=datetime.fromisoformat(manifest["created"]),
                        modified=datetime.fromisoformat(manifest["modified"]),
                        size_bytes=size_bytes,
                        quality=manifest["quality"],
                        narrative_structure=manifest["narrative"]["structure"],
                        git_status=git_status,
                        manifest=ProjectManifest(**manifest),
                    )
                )

        # Apply pagination
        return matching_projects[skip : skip + limit]

    except Exception as e:
        logger.error(f"Error searching projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """
    Get single project details by ID.

    Returns full project manifest and metadata.
    """
    try:
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)

        if not project_path:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PROJECT_NOT_FOUND",
                        "message": f"Project with ID '{project_id}' not found",
                        "details": {"project_id": project_id},
                    }
                },
            )

        manifest = workspace_service.get_project_manifest(project_path)
        if not manifest:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "MANIFEST_NOT_FOUND",
                        "message": f"Project manifest not found for ID '{project_id}'",
                        "details": {"project_id": project_id},
                    }
                },
            )

        # Get project size
        size_bytes = sum(f.stat().st_size for f in project_path.rglob("*") if f.is_file())

        # Get Git status
        git_status = "uninitialized"
        if (project_path / ".git").exists():
            status = await git_service.get_status(project_path)
            git_status = "modified" if status.get("is_dirty") else "clean"

        return ProjectResponse(
            id=manifest.id,
            name=manifest.name,
            path=str(project_path),
            created=manifest.created,
            modified=manifest.modified,
            size_bytes=size_bytes,
            quality=manifest.quality.value,
            narrative_structure=manifest.narrative.structure.value,
            git_status=git_status,
            manifest=manifest,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate):
    """
    Create a new project with enforced structure.

    Automatically initializes Git repository and creates
    required directory structure.
    """
    try:
        workspace_service = get_workspace_service()

        # Sanitize project name to prevent path traversal
        safe_name = project_data.name.replace("..", "").replace("/", "_").replace("\\", "_")
        if safe_name != project_data.name:
            project_data.name = safe_name

        project_path, manifest = workspace_service.create_project(project_data)

        # Get project size (should be small for new project)
        size_bytes = sum(f.stat().st_size for f in project_path.rglob("*") if f.is_file())

        return ProjectResponse(
            id=manifest.id,
            name=manifest.name,
            path=str(project_path),
            created=manifest.created,
            modified=manifest.modified,
            size_bytes=size_bytes,
            quality=manifest.quality.value,
            narrative_structure=manifest.narrative.structure.value,
            git_status="clean",  # New project starts clean
            manifest=manifest,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, update_data: ProjectUpdate):
    """
    Update project metadata.

    Only updates provided fields. Modifies the project manifest
    and commits changes to Git.
    """
    try:
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)

        if not project_path:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PROJECT_NOT_FOUND",
                        "message": f"Project with ID '{project_id}' not found",
                        "details": {"project_id": project_id},
                    }
                },
            )

        manifest = workspace_service.get_project_manifest(project_path)
        if not manifest:
            raise HTTPException(status_code=404, detail="Project manifest not found")

        # Update fields
        if update_data.name is not None:
            manifest.name = update_data.name

        if update_data.quality is not None:
            manifest.quality = update_data.quality

        if update_data.description is not None:
            manifest.metadata.description = update_data.description

        if update_data.tags is not None:
            manifest.metadata.tags = update_data.tags

        # Update modified time
        manifest.modified = datetime.now()

        # Save manifest
        workspace_service.save_project_manifest(project_path, manifest)

        # Commit changes
        await git_service.commit_changes(
            project_path,
            f"Update project metadata: {', '.join(update_data.dict(exclude_unset=True).keys())}",
            prefix="chore",
        )

        # Get updated project info
        size_bytes = sum(f.stat().st_size for f in project_path.rglob("*") if f.is_file())

        git_status = "clean"
        if (project_path / ".git").exists():
            status = await git_service.get_status(project_path)
            git_status = "modified" if status.get("is_dirty") else "clean"

        return ProjectResponse(
            id=manifest.id,
            name=manifest.name,
            path=str(project_path),
            created=manifest.created,
            modified=manifest.modified,
            size_bytes=size_bytes,
            quality=manifest.quality.value,
            narrative_structure=manifest.narrative.structure.value,
            git_status=git_status,
            manifest=manifest,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", response_model=DeleteResponse)
async def delete_project(
    project_id: str, confirm: bool = Query(False, description="Confirmation required for deletion")
):
    """
    Delete a project with confirmation.

    Requires confirm=true parameter to prevent accidental deletion.
    Permanently removes project directory and all contents.
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "CONFIRMATION_REQUIRED",
                        "message": "Project deletion requires confirmation",
                        "details": {"confirm": False, "project_id": project_id},
                    }
                },
            )

        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)

        if not project_path:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PROJECT_NOT_FOUND",
                        "message": f"Project with ID '{project_id}' not found",
                        "details": {"project_id": project_id},
                    }
                },
            )

        # Get project name before deletion
        manifest = workspace_service.get_project_manifest(project_path)
        project_name = manifest.name if manifest else "Unknown"

        # Delete project directory
        try:
            shutil.rmtree(project_path)
            logger.info(f"Deleted project: {project_name} ({project_id})")

            return DeleteResponse(
                success=True,
                message=f"Project '{project_name}' deleted successfully",
                deleted_path=str(project_path),
            )

        except Exception as e:
            logger.error(f"Failed to delete project directory: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "DELETE_FAILED",
                        "message": f"Failed to delete project: {str(e)}",
                        "details": {"project_id": project_id},
                    }
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/validate", response_model=ProjectStructureValidation)
async def validate_project(project_id: str):
    """
    Validate project directory structure.

    Checks for required directories, Git initialization,
    and manifest validity.
    """
    try:
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)

        if not project_path:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PROJECT_NOT_FOUND",
                        "message": f"Project with ID '{project_id}' not found",
                        "details": {"project_id": project_id},
                    }
                },
            )

        # Validate structure
        validation = workspace_service.validate_project_structure(project_path)

        return validation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/storage", response_model=dict)
async def get_project_storage_metrics(project_id: str):
    """
    Get detailed storage metrics for a project.
    
    Returns breakdown by takes, thumbnails, assets, and quality levels.
    """
    try:
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        
        if not project_path:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PROJECT_NOT_FOUND",
                        "message": f"Project with ID '{project_id}' not found",
                        "details": {"project_id": project_id},
                    }
                },
            )
        
        # Get takes storage metrics
        takes_metrics = await takes_service.get_storage_metrics(project_path)
        
        # Calculate additional storage metrics
        total_size = 0
        assets_size = 0
        exports_size = 0
        
        # Assets directory
        assets_dir = project_path / "01_Assets"
        if assets_dir.exists():
            for file in assets_dir.rglob("*"):
                if file.is_file():
                    assets_size += file.stat().st_size
        
        # Exports directory
        exports_dir = project_path / "06_Exports"
        if exports_dir.exists():
            for file in exports_dir.rglob("*"):
                if file.is_file():
                    exports_size += file.stat().st_size
        
        # Total project size
        for file in project_path.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
        
        return {
            "project_id": project_id,
            "total_size": total_size,
            "breakdown": {
                "takes": takes_metrics["total_size"],
                "media": takes_metrics["media_size"],
                "thumbnails": takes_metrics["thumbnail_size"],
                "assets": assets_size,
                "exports": exports_size,
                "other": total_size - takes_metrics["total_size"] - assets_size - exports_size,
            },
            "takes_details": {
                "count": takes_metrics["total_takes"],
                "by_quality": takes_metrics["by_quality"],
                "by_status": takes_metrics["by_status"],
                "largest": takes_metrics["largest_takes"][:5],  # Top 5 only
            },
            "storage_limit": 10 * 1024 * 1024 * 1024,  # 10GB default limit
            "usage_percentage": round((total_size / (10 * 1024 * 1024 * 1024)) * 100, 2),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting storage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/cleanup")
async def cleanup_project_storage(project_id: str):
    """
    Clean up orphaned files and old deleted takes.
    
    Returns statistics about cleaned up files.
    """
    try:
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        
        if not project_path:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "PROJECT_NOT_FOUND",
                        "message": f"Project with ID '{project_id}' not found",
                        "details": {"project_id": project_id},
                    }
                },
            )
        
        # Run cleanup
        cleanup_stats = await takes_service.cleanup_orphaned_files(project_path)
        
        return {
            "project_id": project_id,
            "cleanup_stats": cleanup_stats,
            "message": f"Cleaned up {cleanup_stats['orphaned_directories']} directories, freed {cleanup_stats['bytes_freed']} bytes",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
