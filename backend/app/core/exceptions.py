"""
Custom exceptions for the application.
Provides structured error handling with consistent format.
"""

from typing import Any


class AppException(Exception):
    """Base exception for application errors"""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


class ResourceNotFoundException(AppException):
    """Raised when a requested resource is not found"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ValidationException(AppException):
    """Raised when validation fails"""

    def __init__(self, message: str, field: str | None = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=400, details=details)


class TaskException(AppException):
    """Raised when a task fails"""

    def __init__(self, task_id: str, message: str):
        super().__init__(
            message=f"Task failed: {message}",
            code="TASK_ERROR",
            status_code=500,
            details={"task_id": task_id},
        )


class WebSocketException(AppException):
    """Raised for WebSocket errors"""

    def __init__(self, message: str, project_id: str | None = None):
        details = {}
        if project_id:
            details["project_id"] = project_id
        super().__init__(message=message, code="WEBSOCKET_ERROR", status_code=400, details=details)
