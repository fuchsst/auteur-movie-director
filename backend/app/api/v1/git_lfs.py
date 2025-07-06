"""
Git LFS API endpoints for managing large file storage.
"""

from fastapi import APIRouter, HTTPException
from fastapi import Path as FastAPIPath

from app.schemas.git import LFSFile, LFSStatus, LFSTrackRequest, LFSValidation
from app.services.git_lfs import git_lfs_service
from app.services.workspace import workspace_service

router = APIRouter(prefix="/git/lfs", tags=["git-lfs"])


@router.get("/validate", response_model=LFSValidation)
async def validate_lfs_setup():
    """Validate Git LFS installation"""
    validation = git_lfs_service.validate_lfs_setup()

    if not validation["lfs_installed"]:
        raise HTTPException(
            status_code=424,
            detail="Git LFS is not installed. Please install Git LFS to use this feature.",
        )

    return validation


@router.post("/projects/{project_id}/initialize")
async def initialize_project_lfs(project_id: str = FastAPIPath(..., description="Project ID")):
    """Initialize Git LFS for a project"""
    project_path = workspace_service.get_project_path(project_id)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        git_lfs_service.initialize_lfs(project_path)
        return {"message": "Git LFS initialized successfully"}
    except RuntimeError as e:
        raise HTTPException(status_code=424, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize LFS: {str(e)}")


@router.get("/projects/{project_id}/status", response_model=LFSStatus)
async def get_project_lfs_status(project_id: str = FastAPIPath(..., description="Project ID")):
    """Get LFS status for a project"""
    project_path = workspace_service.get_project_path(project_id)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    return git_lfs_service.get_lfs_status(project_path)


@router.post("/projects/{project_id}/track")
async def track_file_pattern(
    project_id: str = FastAPIPath(..., description="Project ID"), request: LFSTrackRequest = ...
):
    """Track a file pattern with Git LFS"""
    project_path = workspace_service.get_project_path(project_id)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        success = git_lfs_service.track_file(project_path, request.pattern)
        if success:
            return {"message": f"Pattern '{request.pattern}' is now tracked by Git LFS"}
        else:
            raise HTTPException(status_code=400, detail="Failed to track pattern")
    except RuntimeError as e:
        raise HTTPException(status_code=424, detail=str(e))


@router.post("/projects/{project_id}/untrack")
async def untrack_file_pattern(
    project_id: str = FastAPIPath(..., description="Project ID"), request: LFSTrackRequest = ...
):
    """Untrack a file pattern from Git LFS"""
    project_path = workspace_service.get_project_path(project_id)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        success = git_lfs_service.untrack_file(project_path, request.pattern)
        if success:
            return {"message": f"Pattern '{request.pattern}' is no longer tracked by Git LFS"}
        else:
            raise HTTPException(status_code=400, detail="Failed to untrack pattern")
    except RuntimeError as e:
        raise HTTPException(status_code=424, detail=str(e))


@router.get("/projects/{project_id}/files", response_model=list[LFSFile])
async def get_lfs_tracked_files(project_id: str = FastAPIPath(..., description="Project ID")):
    """Get list of files tracked by Git LFS in a project"""
    project_path = workspace_service.get_project_path(project_id)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    return git_lfs_service.get_lfs_files(project_path)
