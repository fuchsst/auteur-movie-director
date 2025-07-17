"""
Integration Models

Data models for end-to-end Function Runner integration.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..worker.models import TaskResult, TaskState


class IntegrationStatus(str, Enum):
    """Integration health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class OutputContext:
    """Context for storing function outputs"""
    
    def __init__(self,
                 task_id: str,
                 project_id: str,
                 shot_id: Optional[str] = None,
                 take_number: int = 1,
                 timestamp: Optional[str] = None):
        self.task_id = task_id
        self.project_id = project_id
        self.shot_id = shot_id
        self.take_number = take_number
        self.timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")


@dataclass
class IntegratedTaskRequest:
    """Request for integrated task submission"""
    template_id: str
    inputs: Dict[str, Any]
    quality: str = "standard"
    project_id: Optional[str] = None
    shot_id: Optional[str] = None
    user_id: Optional[str] = None
    canvas_node_id: Optional[str] = None
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResponse:
    """Response from integrated task submission"""
    task_id: str
    tracking_id: str
    status: str
    estimated_completion: Optional[float] = None
    message: Optional[str] = None


@dataclass
class WorkflowResult:
    """Complete workflow execution result"""
    task_id: str
    status: TaskState
    outputs: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'status': self.status.value,
            'outputs': self.outputs,
            'execution_time': self.execution_time,
            'resource_usage': self.resource_usage,
            'error_message': self.error_message,
            'metadata': self.metadata
        }


@dataclass
class StoredFile:
    """Information about a stored file"""
    path: str
    relative_path: str
    size: int
    content_type: str
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceEvent:
    """Event from a service for integration"""
    service: str
    type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WebSocketEvent:
    """Event to send via WebSocket"""
    type: str
    data: Dict[str, Any]
    target: Optional[str] = None  # user_id, project_id, etc.


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: IntegrationStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationHealthReport:
    """Complete integration health report"""
    status: IntegrationStatus
    checks: List[HealthCheck]
    timestamp: datetime
    uptime: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'uptime': self.uptime,
            'checks': [
                {
                    'name': check.name,
                    'status': check.status.value,
                    'message': check.message,
                    'details': check.details
                }
                for check in self.checks
            ]
        }


@dataclass
class CanvasNode:
    """Canvas node representation"""
    id: str
    type: str
    template_id: Optional[str] = None
    position: Dict[str, float] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: str = "idle"
    
    # Event handlers
    on_execute: Optional[Callable] = None
    on_cancel: Optional[Callable] = None
    on_progress: Optional[Callable] = None


@dataclass
class Project:
    """Project representation for integration"""
    id: str
    name: str
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_shot_path(self, shot_id: str) -> str:
        """Get path for a specific shot"""
        return f"{self.path}/03_Renders/{shot_id}"
    
    def get_renders_path(self) -> str:
        """Get renders base path"""
        return f"{self.path}/03_Renders"


@dataclass
class ErrorHandlingResult:
    """Result of error handling attempt"""
    error_handled: bool
    recovery_attempted: bool
    recovery_successful: bool
    user_notified: bool
    retry_suggested: bool = False
    retry_delay: float = 0.0


class IntegrationError(Exception):
    """Base exception for integration errors"""
    pass


class ServiceUnavailableError(IntegrationError):
    """Service is unavailable"""
    pass


class WorkflowExecutionError(IntegrationError):
    """Workflow execution failed"""
    pass


class WorkflowTimeoutError(IntegrationError):
    """Workflow execution timed out"""
    pass


class WorkflowCancelledError(IntegrationError):
    """Workflow was cancelled"""
    pass


class InsufficientResourcesError(IntegrationError):
    """Insufficient resources for execution"""
    pass