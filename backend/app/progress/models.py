"""Progress tracking models for function execution"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field


class StageStatus(str, Enum):
    """Status of a stage in task execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStatus(str, Enum):
    """Overall task status"""
    QUEUED = "queued"
    PREPARING = "preparing"
    EXECUTING = "executing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StageProgress:
    """Progress information for a single stage"""
    name: str
    status: StageStatus = StageStatus.PENDING
    progress: float = 0.0  # 0-1
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate stage duration if completed"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def elapsed(self) -> Optional[timedelta]:
        """Calculate elapsed time since stage started"""
        if self.started_at:
            end = self.completed_at or datetime.now()
            return end - self.started_at
        return None


@dataclass
class Stage:
    """Stage definition with metadata"""
    name: str
    description: str
    weight: float = 0.25
    optional: bool = False


class TaskProgress(BaseModel):
    """Complete progress tracking for a task"""
    task_id: str
    template_id: str
    status: TaskStatus = TaskStatus.QUEUED
    current_stage: int = 0
    total_stages: int = 4
    stages: Dict[int, StageProgress] = Field(default_factory=dict)
    overall_progress: float = 0.0
    eta: Optional[datetime] = None
    preview_url: Optional[str] = None
    resource_usage: Dict[str, float] = Field(default_factory=dict)
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    @property
    def total_duration(self) -> Optional[timedelta]:
        """Calculate total task duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def elapsed_time(self) -> Optional[timedelta]:
        """Calculate elapsed time since task started"""
        if self.started_at:
            end = self.completed_at or datetime.now()
            return end - self.started_at
        return None
    
    def get_stage_durations(self) -> Dict[int, float]:
        """Get duration in seconds for each stage"""
        durations = {}
        for stage_id, stage in self.stages.items():
            if stage.duration:
                durations[stage_id] = stage.duration.total_seconds()
        return durations


class TaskHistory(BaseModel):
    """Historical task data for ETA prediction"""
    task_id: str
    template_id: str
    stage_durations: Dict[int, float]  # Stage ID -> duration in seconds
    total_duration: float
    quality: str
    resource_config: Dict[str, Any]
    completed_at: datetime
    success: bool = True


class ProgressUpdate(BaseModel):
    """Progress update message"""
    task_id: str
    status: TaskStatus
    current_stage: int
    overall_progress: float
    eta: Optional[datetime] = None
    stages: Dict[str, Dict[str, Any]]
    preview_url: Optional[str] = None
    resource_usage: Optional[Dict[str, float]] = None
    message: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)


class BatchProgress(BaseModel):
    """Aggregated progress for batch operations"""
    batch_id: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    overall_progress: float = 0.0
    eta: Optional[datetime] = None
    task_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.now)


class LogEntry(BaseModel):
    """Log entry for task execution"""
    timestamp: datetime
    level: str
    message: str
    task_id: Optional[str] = None
    stage: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProgressResponse(BaseModel):
    """API response for progress query"""
    task_id: str
    status: TaskStatus
    overall_progress: float
    current_stage: int
    stages: List[Dict[str, Any]]
    eta: Optional[datetime] = None
    preview_url: Optional[str] = None
    elapsed_time: Optional[float] = None
    resource_usage: Optional[Dict[str, float]] = None


class LogsResponse(BaseModel):
    """API response for logs query"""
    task_id: str
    logs: List[LogEntry]
    total_count: int
    filtered_count: int