"""
Tests for Integration Models (STORY-051)

Tests just the data models without complex import dependencies.
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# Import models directly to avoid complex dependency chain
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from integration.models import (
    IntegratedTaskRequest,
    TaskResponse, 
    WorkflowResult,
    ServiceEvent,
    WebSocketEvent,
    Project,
    OutputContext,
    StoredFile,
    ErrorHandlingResult,
    IntegrationStatus
)
from worker.models import TaskState


class TestIntegrationModels:
    """Test integration data models"""
    
    def test_integrated_task_request(self):
        """Test IntegratedTaskRequest model"""
        request = IntegratedTaskRequest(
            template_id="test_template",
            inputs={"prompt": "test"},
            quality="standard",
            project_id="test_project",
            user_id="test_user"
        )
        
        assert request.template_id == "test_template"
        assert request.inputs == {"prompt": "test"}
        assert request.quality == "standard"
        assert request.project_id == "test_project"
        assert request.user_id == "test_user"
        assert request.priority == 0
        assert isinstance(request.metadata, dict)
    
    def test_task_response(self):
        """Test TaskResponse model"""
        response = TaskResponse(
            task_id="test_task",
            tracking_id="test_tracking",
            status="submitted",
            estimated_completion=30.0,
            message="Task submitted successfully"
        )
        
        assert response.task_id == "test_task"
        assert response.tracking_id == "test_tracking"
        assert response.status == "submitted"
        assert response.estimated_completion == 30.0
        assert response.message == "Task submitted successfully"
    
    def test_workflow_result(self):
        """Test WorkflowResult model"""
        result = WorkflowResult(
            task_id="test_task",
            status=TaskState.COMPLETED,
            outputs={"image": "output.png"},
            execution_time=25.0,
            resource_usage={"gpu": 6.0, "memory": 8.0},
            metadata={"user_id": "test_user"}
        )
        
        assert result.task_id == "test_task"
        assert result.status == TaskState.COMPLETED
        assert result.outputs == {"image": "output.png"}
        assert result.execution_time == 25.0
        assert result.resource_usage == {"gpu": 6.0, "memory": 8.0}
        assert result.metadata == {"user_id": "test_user"}
        
        # Test serialization
        data = result.to_dict()
        assert data["task_id"] == "test_task"
        assert data["status"] == "completed"
        assert data["outputs"] == {"image": "output.png"}
        assert data["execution_time"] == 25.0
        assert data["resource_usage"] == {"gpu": 6.0, "memory": 8.0}
        assert data["metadata"] == {"user_id": "test_user"}
    
    def test_service_event(self):
        """Test ServiceEvent model"""
        event = ServiceEvent(
            service="task",
            type="progress",
            data={"task_id": "test", "progress": 0.5},
            metadata={"user_id": "test_user"}
        )
        
        assert event.service == "task"
        assert event.type == "progress"
        assert event.data["task_id"] == "test"
        assert event.data["progress"] == 0.5
        assert event.metadata["user_id"] == "test_user"
        assert isinstance(event.timestamp, datetime)
    
    def test_websocket_event(self):
        """Test WebSocketEvent model"""
        event = WebSocketEvent(
            type="generation.progress",
            data={"taskId": "test", "progress": 0.5},
            target="user_123"
        )
        
        assert event.type == "generation.progress"
        assert event.data["taskId"] == "test"
        assert event.data["progress"] == 0.5
        assert event.target == "user_123"
    
    def test_project_model(self):
        """Test Project model"""
        project = Project(
            id="test_project",
            name="Test Project",
            path="/workspace/test_project",
            metadata={"created_by": "test_user"}
        )
        
        assert project.id == "test_project"
        assert project.name == "Test Project"
        assert project.path == "/workspace/test_project"
        assert project.metadata["created_by"] == "test_user"
        
        # Test path methods
        assert project.get_shot_path("shot_001") == "/workspace/test_project/03_Renders/shot_001"
        assert project.get_renders_path() == "/workspace/test_project/03_Renders"
    
    def test_output_context(self):
        """Test OutputContext model"""
        context = OutputContext(
            task_id="test_task",
            project_id="test_project",
            shot_id="shot_001",
            take_number=3,
            timestamp="20240101_120000"
        )
        
        assert context.task_id == "test_task"
        assert context.project_id == "test_project"
        assert context.shot_id == "shot_001"
        assert context.take_number == 3
        assert context.timestamp == "20240101_120000"
    
    def test_stored_file(self):
        """Test StoredFile model"""
        stored_file = StoredFile(
            path="/full/path/to/file.png",
            relative_path="renders/take_001/file.png",
            size=1024,
            content_type="image/png",
            checksum="abc123",
            metadata={"task_id": "test_task"}
        )
        
        assert stored_file.path == "/full/path/to/file.png"
        assert stored_file.relative_path == "renders/take_001/file.png"
        assert stored_file.size == 1024
        assert stored_file.content_type == "image/png"
        assert stored_file.checksum == "abc123"
        assert stored_file.metadata["task_id"] == "test_task"
    
    def test_error_handling_result(self):
        """Test ErrorHandlingResult model"""
        result = ErrorHandlingResult(
            error_handled=True,
            recovery_attempted=True,
            recovery_successful=False,
            user_notified=True,
            retry_suggested=True,
            retry_delay=5.0
        )
        
        assert result.error_handled is True
        assert result.recovery_attempted is True
        assert result.recovery_successful is False
        assert result.user_notified is True
        assert result.retry_suggested is True
        assert result.retry_delay == 5.0
    
    def test_integration_status_enum(self):
        """Test IntegrationStatus enum"""
        assert IntegrationStatus.HEALTHY == "healthy"
        assert IntegrationStatus.DEGRADED == "degraded"
        assert IntegrationStatus.UNHEALTHY == "unhealthy"


class TestIntegrationWorkflowConcept:
    """Test the conceptual integration workflow logic"""
    
    def test_task_lifecycle_states(self):
        """Test task lifecycle through different states"""
        
        # Initial request
        request = IntegratedTaskRequest(
            template_id="image_generation_v1",
            inputs={"prompt": "A beautiful sunset", "width": 512, "height": 512},
            quality="standard",
            project_id="test_project",
            user_id="test_user"
        )
        
        # Task submission response
        response = TaskResponse(
            task_id="task_123",
            tracking_id="tracking_456", 
            status="submitted",
            estimated_completion=30.0
        )
        
        # Progress events
        progress_events = [
            ServiceEvent(
                service="task",
                type="progress",
                data={"task_id": "task_123", "progress": 0.25, "stage": "preprocessing"},
                metadata={"user_id": "test_user"}
            ),
            ServiceEvent(
                service="task",
                type="progress", 
                data={"task_id": "task_123", "progress": 0.75, "stage": "generation"},
                metadata={"user_id": "test_user"}
            )
        ]
        
        # Final result
        result = WorkflowResult(
            task_id="task_123",
            status=TaskState.COMPLETED,
            outputs={"image": "/project/renders/take_001/output.png"},
            execution_time=25.0,
            metadata={"quality": "standard"}
        )
        
        # Verify lifecycle
        assert request.template_id == "image_generation_v1"
        assert response.task_id == "task_123"
        assert response.status == "submitted"
        
        assert len(progress_events) == 2
        assert progress_events[0].data["progress"] == 0.25
        assert progress_events[1].data["progress"] == 0.75
        
        assert result.status == TaskState.COMPLETED
        assert "image" in result.outputs
        assert result.execution_time > 0
    
    def test_error_handling_workflow(self):
        """Test error handling workflow"""
        
        # Failed task result
        failed_result = WorkflowResult(
            task_id="task_456",
            status=TaskState.FAILED,
            error_message="Insufficient VRAM for generation",
            execution_time=5.0
        )
        
        # Error handling result
        error_handling = ErrorHandlingResult(
            error_handled=True,
            recovery_attempted=True,
            recovery_successful=False,
            user_notified=True,
            retry_suggested=True,
            retry_delay=60.0
        )
        
        # Error event
        error_event = ServiceEvent(
            service="task",
            type="failed",
            data={
                "task_id": "task_456",
                "error": "Insufficient VRAM for generation",
                "recoverable": True
            },
            metadata={"user_id": "test_user"}
        )
        
        # Verify error handling
        assert failed_result.status == TaskState.FAILED
        assert "VRAM" in failed_result.error_message
        
        assert error_handling.error_handled is True
        assert error_handling.retry_suggested is True
        assert error_handling.retry_delay == 60.0
        
        assert error_event.data["recoverable"] is True
    
    def test_storage_integration_workflow(self):
        """Test storage integration workflow"""
        
        # Output context
        context = OutputContext(
            task_id="task_789",
            project_id="test_project",
            shot_id="shot_001",
            take_number=1
        )
        
        # Stored file
        stored_file = StoredFile(
            path="/workspace/test_project/03_Renders/shot_001/take_001/output.png",
            relative_path="03_Renders/shot_001/take_001/output.png",
            size=2048576,  # 2MB
            content_type="image/png",
            checksum="def456",
            metadata={
                "task_id": "task_789",
                "quality": "standard",
                "generation_time": 25.0
            }
        )
        
        # Verify storage workflow
        assert context.task_id == "task_789"
        assert context.shot_id == "shot_001"
        assert context.take_number == 1
        
        assert stored_file.size > 1024 * 1024  # Over 1MB
        assert stored_file.content_type == "image/png"
        assert stored_file.metadata["task_id"] == context.task_id
        assert stored_file.relative_path.startswith("03_Renders")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])