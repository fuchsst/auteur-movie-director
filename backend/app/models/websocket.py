"""
WebSocket message models for real-time communication.
Defines structured messages for generation tasks and progress updates.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    """Base WebSocket message"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal[
        "start_generation", "progress", "complete", "error", "ping", "pong", "task_started"
    ]
    project_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StartGenerationMessage(WebSocketMessage):
    """Request to start generation"""

    type: Literal["start_generation"] = "start_generation"
    task_type: str  # e.g., "text_to_image", "image_to_video"
    params: Dict[str, Any]
    quality: str = "standard"
    # Support for composite prompts
    character_refs: Optional[List[str]] = None  # Character asset IDs
    style_refs: Optional[List[str]] = None  # Style asset IDs
    location_ref: Optional[str] = None  # Location asset ID


class ProgressMessage(WebSocketMessage):
    """Progress update from backend"""

    type: Literal["progress"] = "progress"
    task_id: str
    progress: float  # 0.0 to 1.0
    message: Optional[str] = None
    preview_url: Optional[str] = None


class CompleteMessage(WebSocketMessage):
    """Task completion notification"""

    type: Literal["complete"] = "complete"
    task_id: str
    result: Dict[str, Any]
    duration: float  # seconds


class ErrorMessage(WebSocketMessage):
    """Error notification"""

    type: Literal["error"] = "error"
    task_id: Optional[str] = None
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class TaskStartedMessage(WebSocketMessage):
    """Task started acknowledgment"""

    type: Literal["task_started"] = "task_started"
    task_id: str


class PingMessage(WebSocketMessage):
    """Ping message for connection keep-alive"""

    type: Literal["ping"] = "ping"


class PongMessage(WebSocketMessage):
    """Pong response to ping"""

    type: Literal["pong"] = "pong"
