"""
Pydantic schemas for takes system.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GenerationParams(BaseModel):
    """Parameters for content generation"""

    model: str = Field(..., description="Model used for generation")
    seed: int = Field(..., description="Random seed for reproducibility")
    prompt: str = Field(..., description="Generation prompt")
    negative_prompt: str | None = Field(None, description="Negative prompt")
    steps: int = Field(..., description="Number of generation steps")
    cfg: float = Field(..., description="Classifier-free guidance scale")
    # Allow additional model-specific parameters
    extra: dict[str, Any] = Field(default_factory=dict, description="Additional parameters")


class Resolution(BaseModel):
    """Media resolution"""

    width: int = Field(..., description="Width in pixels")
    height: int = Field(..., description="Height in pixels")


class ResourceUsage(BaseModel):
    """Resource usage for generation"""

    quality: str = Field(..., description="Quality level: draft, standard, high")
    vram_used: float = Field(0, description="Peak VRAM usage in MB")
    generation_time: float = Field(0, description="Generation time in seconds")


class TakeMetadata(BaseModel):
    """Complete metadata for a take"""

    id: str = Field(..., description="Take ID (e.g., take_001)")
    shot_id: str = Field(..., description="Shot ID")
    created: datetime = Field(..., description="Creation timestamp")
    duration: float | None = Field(None, description="Video duration in seconds")
    resolution: Resolution | None = Field(None, description="Media resolution")
    generation_params: GenerationParams = Field(..., description="Generation parameters")
    resources: ResourceUsage = Field(..., description="Resource usage")
    status: str = Field(..., description="Status: generating, complete, failed")
    error: str | None = Field(None, description="Error message if failed")
    file_path: str | None = Field(None, description="Relative path to media file")
    file_size: int | None = Field(None, description="File size in bytes")
    thumbnail_path: str | None = Field(None, description="Relative path to thumbnail")


class CreateTakeRequest(BaseModel):
    """Request to create a new take"""

    generation_params: GenerationParams = Field(..., description="Generation parameters")
    quality: str = Field("standard", description="Quality level")


class CreateTakeResponse(BaseModel):
    """Response after creating a take"""

    take_id: str = Field(..., description="Generated take ID")
    take_number: int = Field(..., description="Take number")
    status: str = Field("queued", description="Initial status")
    task_id: str | None = Field(None, description="Task ID for tracking")


class TakeListResponse(BaseModel):
    """Response with list of takes"""

    takes: list[TakeMetadata] = Field(..., description="List of takes")
    active_take_id: str | None = Field(None, description="Currently active take")
    total: int = Field(..., description="Total number of takes")


class SetActiveTakeRequest(BaseModel):
    """Request to set active take"""

    take_id: str = Field(..., description="Take ID to make active")


class DeleteTakeResponse(BaseModel):
    """Response after deleting a take"""

    success: bool = Field(..., description="Whether deletion succeeded")
    message: str = Field(..., description="Status message")
    new_active_take_id: str | None = Field(
        None, description="New active take if the deleted one was active"
    )


class TakeExportRequest(BaseModel):
    """Request to export a take"""

    take_id: str = Field(..., description="Take ID to export")
    include_metadata: bool = Field(True, description="Include metadata file")


class TakeExportResponse(BaseModel):
    """Response after exporting a take"""

    success: bool = Field(..., description="Whether export succeeded")
    export_path: str | None = Field(None, description="Path to exported file")
    message: str = Field(..., description="Status message")


class TakeCleanupRequest(BaseModel):
    """Request to cleanup old takes"""

    keep_count: int = Field(10, description="Number of recent takes to keep", ge=1, le=100)
    include_failed: bool = Field(True, description="Also cleanup failed takes")


class TakeCleanupResponse(BaseModel):
    """Response after cleaning up takes"""

    deleted_count: int = Field(..., description="Number of takes deleted")
    remaining_count: int = Field(..., description="Number of takes remaining")
    message: str = Field(..., description="Status message")
