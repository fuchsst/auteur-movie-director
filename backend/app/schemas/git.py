"""
Pydantic schemas for Git and Git LFS operations.
"""

from pydantic import BaseModel, Field


class GitCommit(BaseModel):
    """Git commit information"""

    hash: str = Field(..., description="Commit hash (short)")
    message: str = Field(..., description="Commit message")
    author: str = Field(..., description="Author name")
    email: str = Field(..., description="Author email")
    date: str = Field(..., description="Commit date in ISO format")
    files_changed: int = Field(..., description="Number of files changed")


class GitStatus(BaseModel):
    """Git repository status"""

    initialized: bool = Field(..., description="Whether repository is initialized")
    branch: str | None = Field(None, description="Current branch name")
    is_dirty: bool | None = Field(None, description="Whether repository has uncommitted changes")
    untracked_files: list[str] | None = Field(None, description="List of untracked files")
    modified_files: list[str] | None = Field(None, description="List of modified files")
    staged_files: list[str] | None = Field(None, description="List of staged files")
    lfs_files: list[str] | None = Field(None, description="List of LFS-tracked files")
    lfs_patterns: list[str] | None = Field(None, description="List of LFS tracking patterns")
    error: str | None = Field(None, description="Error message if any")


class LFSFile(BaseModel):
    """Git LFS tracked file information"""

    oid: str = Field(..., description="Object ID")
    size: int = Field(..., description="File size in bytes")
    path: str = Field(..., description="File path")


class LFSStatus(BaseModel):
    """Git LFS status for a project"""

    enabled: bool = Field(..., description="Whether LFS is enabled")
    installed: bool = Field(..., description="Whether LFS is installed")
    initialized: bool | None = Field(None, description="Whether LFS is initialized in project")
    tracked_patterns: list[str] | None = Field(None, description="Patterns tracked by LFS")
    tracked_files: list[LFSFile] | None = Field(None, description="Files tracked by LFS")
    file_count: int | None = Field(None, description="Number of LFS-tracked files")
    total_size: int | None = Field(None, description="Total size of LFS-tracked files")
    error: str | None = Field(None, description="Error message if any")


class LFSTrackRequest(BaseModel):
    """Request to track a file pattern with Git LFS"""

    pattern: str = Field(..., description="File pattern to track (e.g., *.mp4)")


class LFSValidation(BaseModel):
    """Git LFS installation validation result"""

    git_installed: bool = Field(..., description="Whether Git is installed")
    lfs_installed: bool = Field(..., description="Whether Git LFS is installed")
    git_version: str | None = Field(None, description="Git version string")
    lfs_version: str | None = Field(None, description="Git LFS version string")
    issues: list[str] = Field(default_factory=list, description="List of issues found")


class CommitRequest(BaseModel):
    """Request to commit changes"""

    message: str = Field(..., description="Commit message")
    prefix: str | None = Field(None, description="Semantic commit prefix (feat, fix, etc.)")
    files: list[str] | None = Field(None, description="Specific files to commit")


class RepositoryValidation(BaseModel):
    """Repository validation result"""

    valid: bool = Field(..., description="Whether repository is valid")
    issues: list[str] = Field(default_factory=list, description="Critical issues found")
    warnings: list[str] = Field(default_factory=list, description="Warnings found")
