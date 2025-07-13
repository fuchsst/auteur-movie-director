"""
Git API endpoints for repository management.
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.git import git_service, auto_commit_manager
from app.services.workspace import get_workspace_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/git", tags=["git"])


class CommitRequest(BaseModel):
    """Request model for committing changes"""

    project_id: str = Field(description="Project UUID")
    message: str = Field(description="Commit message")
    prefix: str | None = Field(None, description="Semantic prefix (feat, fix, etc.)")
    files: list[str] | None = Field(None, description="Specific files to commit")


class GitStatus(BaseModel):
    """Git repository status"""

    initialized: bool
    branch: str | None = None
    is_dirty: bool | None = None
    untracked_files: list[str] = []
    modified_files: list[str] = []
    staged_files: list[str] = []
    lfs_files: list[str] | None = None
    lfs_patterns: list[str] | None = None
    error: str | None = None


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
    issues: list[str] = []
    warnings: list[str] = []


class GitConfig(BaseModel):
    """Git configuration information"""

    user_name: str | None = None
    user_email: str | None = None
    lfs_enabled: bool = False
    lfs_version: str | None = None
    git_version: str | None = None
    tracked_patterns: list[str] = []


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


@router.get("/{project_id}/history", response_model=list[CommitInfo])
async def get_commit_history(
    project_id: str,
    limit: int = Query(20, description="Maximum number of commits to return"),
    file_path: str | None = Query(None, description="Get history for specific file"),
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


@router.get("/{project_id}/config", response_model=GitConfig)
async def get_repository_config(project_id: str):
    """
    Get Git configuration for a project.

    Returns:
    - User name and email
    - LFS status and version
    - Git version
    - Tracked LFS patterns
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get config
        config = await git_service.get_config(project_path)
        return GitConfig(**config)

    except Exception as e:
        logger.error(f"Error getting repository config: {e}")
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


class EnhancedCommitInfo(BaseModel):
    """Enhanced commit information with diffs"""
    
    hash: str
    short_hash: str
    message: str
    author: str
    email: str
    date: str
    stats: dict
    files: list[dict]
    parent_hashes: list[str]


class RollbackRequest(BaseModel):
    """Request to rollback to a commit"""
    
    commit_hash: str = Field(description="Hash of commit to rollback to")
    mode: str = Field("soft", description="Rollback mode: soft, mixed, or hard")


class TagRequest(BaseModel):
    """Request to create a tag"""
    
    tag_name: str = Field(description="Name for the tag")
    message: str | None = Field(None, description="Optional tag message")


@router.get("/{project_id}/history/enhanced", response_model=list[EnhancedCommitInfo])
async def get_enhanced_history(
    project_id: str,
    limit: int = Query(50, description="Maximum number of commits to return"),
    file_path: str | None = Query(None, description="Get history for specific file"),
):
    """
    Get enhanced commit history with diff statistics.
    
    Returns detailed information including:
    - Commit statistics (additions, deletions, files changed)
    - List of changed files with diff counts
    - Parent commit hashes for navigation
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get enhanced history
        history = await git_service.get_enhanced_history(project_path, limit, file_path)
        return [EnhancedCommitInfo(**commit) for commit in history]
    
    except Exception as e:
        logger.error(f"Error getting enhanced history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/rollback")
async def rollback_to_commit(project_id: str, request: RollbackRequest):
    """
    Rollback repository to a specific commit.
    
    Modes:
    - soft: Move HEAD only (keeps changes staged)
    - mixed: Move HEAD and index (unstages changes)
    - hard: Move HEAD, index, and working tree (discards all changes)
    
    Note: Hard reset will fail if there are uncommitted changes.
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Validate mode
        if request.mode not in ["soft", "mixed", "hard"]:
            raise HTTPException(status_code=400, detail="Invalid rollback mode")
        
        # Perform rollback
        success = await git_service.rollback(project_path, request.commit_hash, request.mode)
        
        if not success:
            raise HTTPException(status_code=400, detail="Rollback failed")
        
        return {
            "success": True,
            "message": f"Rolled back to commit {request.commit_hash} ({request.mode} mode)",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during rollback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/tags")
async def create_tag(project_id: str, request: TagRequest):
    """
    Create a tag at the current HEAD.
    
    Creates either:
    - Lightweight tag (no message)
    - Annotated tag (with message)
    
    Tags are useful for marking release versions or milestones.
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create tag
        success = await git_service.create_tag(project_path, request.tag_name, request.message)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create tag")
        
        return {
            "success": True,
            "message": f"Created tag '{request.tag_name}'",
            "type": "annotated" if request.message else "lightweight",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/auto-commit/{file_path:path}")
async def track_file_change(project_id: str, file_path: str):
    """
    Track a file change for auto-commit batching.
    
    Changes are batched for up to 5 minutes or 50 files.
    Auto-commits use descriptive messages based on changed files.
    """
    try:
        # Get project path
        workspace_service = get_workspace_service()
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Track change
        await auto_commit_manager.track_change(project_id, project_path, file_path)
        
        return {
            "success": True,
            "message": f"Tracked change to {file_path}",
        }
    
    except Exception as e:
        logger.error(f"Error tracking change: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-commit/force-all")
async def force_auto_commit_all():
    """
    Force commit all pending auto-commit batches.
    
    Useful for ensuring all changes are committed before:
    - Shutdown
    - Export
    - Major operations
    """
    try:
        await auto_commit_manager.force_commit_all()
        return {
            "success": True,
            "message": "Forced commit of all pending changes",
        }
    
    except Exception as e:
        logger.error(f"Error forcing commits: {e}")
        raise HTTPException(status_code=500, detail=str(e))
