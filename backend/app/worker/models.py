"""
Worker Models

Data models for the worker system.
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskState(str, Enum):
    """Task execution states"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WorkerStatus(str, Enum):
    """Worker status states"""
    IDLE = "idle"
    BUSY = "busy"
    STARTING = "starting"
    STOPPING = "stopping"
    FAILED = "failed"
    OFFLINE = "offline"


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    state: TaskState
    outputs: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'state': self.state.value,
            'outputs': self.outputs,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'resource_usage': self.resource_usage,
            'metadata': self.metadata,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class WorkerTask:
    """Task to be executed by worker"""
    id: str
    template_id: str
    inputs: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'template_id': self.template_id,
            'inputs': self.inputs,
            'metadata': self.metadata,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None
        }


@dataclass
class WorkerInfo:
    """Information about a worker"""
    id: str
    status: WorkerStatus
    current_task: Optional[str] = None
    load: float = 0.0
    capabilities: List[str] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'status': self.status.value,
            'current_task': self.current_task,
            'load': self.load,
            'capabilities': self.capabilities,
            'resource_usage': self.resource_usage,
            'last_heartbeat': self.last_heartbeat.isoformat()
        }


@dataclass
class ResourceAvailability:
    """Resource availability check result"""
    available: bool
    reason: Optional[str] = None
    estimated_wait_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'available': self.available,
            'reason': self.reason,
            'estimated_wait_time': self.estimated_wait_time
        }