"""
Git API endpoints for repository management.
"""

import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings
from app.services.git import git_service
from app.services.workspace import get_workspace_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/git", tags=["git"])


class CommitRequest(BaseModel):
    """Request model for committing changes"""

    project_id: str = Field(description="Project UUID")
    message: str = Field(description="Commit message")
    prefix: Optional[str] = Field(None, description="Semantic prefix (feat, fix, etc.)")
    files: Optional[List[str]] = Field(None, description="Specific files to commit")


class GitStatus(BaseModel):
    """Git repository status"""

    initialized: bool
    branch: Optional[str] = None
    is_dirty: Optional[bool] = None
    untracked_files: List[str] = []
    modified_files: List[str] = []
    staged_files: List[str] = []
    lfs_files: Optional[List[str]] = None
    lfs_patterns: Optional[List[str]] = None
    error: Optional[str] = None


class CommitInfo(BaseModel):
    """Information about a commit"""

    hash: str
    message: str
    author: str
    email: str
    date: str
    files_changed: int


class ValidationResult(BaseModel):
    """Repository validation results"""

    valid: bool
    issues: List[str] = []
    warnings: List[str] = []


@router.get("/{project_id}/status", response_model=GitStatus)
async def get_repository_status(project_id: str):
    """
    Get Git repository status for a project.

    Includes information about:
    - Repository initialization state
    - Current branch
    - Modified/staged/untracked files
    - Git LFS tracking status
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get status
        status = await git_service.get_status(project_path)
        return GitStatus(**status)

    except Exception as e:
        logger.error(f"Error getting repository status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/commit")
async def commit_changes(project_id: str, request: CommitRequest):
    """
    Commit changes to the project repository.

    Supports:
    - Semantic commit prefixes (feat, fix, asset, etc.)
    - Selective file commits
    - Automatic staging of all changes
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(request.project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Ensure repository is initialized
        if not (project_path / ".git").exists():
            success = await git_service.initialize_repository(project_path)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to initialize repository")

        # Commit changes
        success = await git_service.commit_changes(
            project_path, request.message, request.prefix, request.files
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to commit changes")

        return {"success": True, "message": "Changes committed successfully"}

    except Exception as e:
        logger.error(f"Error committing changes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/history", response_model=List[CommitInfo])
async def get_commit_history(
    project_id: str,
    limit: int = Query(20, description="Maximum number of commits to return"),
    file_path: Optional[str] = Query(None, description="Get history for specific file"),
):
    """
    Get commit history for the project.

    Can retrieve:
    - Full project history
    - History for a specific file
    - Limited number of recent commits
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if repository exists
        if not (project_path / ".git").exists():
            return []

        # Get history
        history = await git_service.get_history(project_path, limit, file_path)
        return [CommitInfo(**commit) for commit in history]

    except Exception as e:
        logger.error(f"Error getting commit history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/track-lfs/{file_path:path}")
async def track_file_with_lfs(project_id: str, file_path: str):
    """
    Ensure a large file is tracked by Git LFS.

    Automatically called when:
    - Files larger than 50MB are added
    - Specific file types need LFS tracking
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Track file
        success = await git_service.track_large_file(project_path, file_path)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to track file with LFS")

        return {"success": True, "message": f"File {file_path} tracked with Git LFS"}

    except Exception as e:
        logger.error(f"Error tracking file with LFS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/validate", response_model=ValidationResult)
async def validate_repository(project_id: str):
    """
    Validate repository health and configuration.

    Checks:
    - Repository initialization
    - Git LFS configuration
    - Uncommitted changes
    - Required files (.gitattributes)
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate
        results = await git_service.validate_repository(project_path)
        return ValidationResult(**results)

    except Exception as e:
        logger.error(f"Error validating repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-lfs")
async def check_lfs_installation():
    """
    Check if Git LFS is installed on the system.

    Used during startup to verify LFS availability.
    """
    try:
        installed = await git_service.check_lfs_installed()
        return {
            "installed": installed,
            "message": "Git LFS is available" if installed else "Git LFS not found",
        }
    except Exception as e:
        logger.error(f"Error checking LFS: {e}")
        return {"installed": False, "error": str(e)}
