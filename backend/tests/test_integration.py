"""
Tests for Function Runner Integration System (STORY-051)

Tests the complete end-to-end integration functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.integration import (
    FunctionRunnerOrchestrator,
    IntegratedTaskSubmissionHandler,
    WebSocketIntegrationLayer
)
from app.integration.models import (
    IntegratedTaskRequest,
    TaskResponse,
    WorkflowResult,
    ServiceEvent,
    WebSocketEvent,
    Project
)
from app.worker.models import TaskState
from app.templates.base import FunctionTemplate


class TestFunctionRunnerOrchestrator:
    """Test the main orchestrator"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = FunctionRunnerOrchestrator()
        
        # Mock dependencies
        orchestrator.worker_pool.initialize = AsyncMock()
        orchestrator.template_registry.initialize = AsyncMock()
        orchestrator.quality_manager.initialize = AsyncMock()
        orchestrator.progress_tracker.initialize = AsyncMock()
        
        await orchestrator.initialize()
        
        # Verify all components initialized
        orchestrator.worker_pool.initialize.assert_called_once()
        orchestrator.template_registry.initialize.assert_called_once()
        orchestrator.quality_manager.initialize.assert_called_once()
        orchestrator.progress_tracker.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test complete workflow execution"""
        orchestrator = FunctionRunnerOrchestrator()
        
        # Mock template
        template = Mock(spec=FunctionTemplate)
        template.id = "test_template"
        template.resources.estimated_time_seconds = 30.0
        template.validate_inputs = AsyncMock(return_value={"prompt": "test"})
        
        # Mock dependencies
        orchestrator.template_registry.get_template = AsyncMock(return_value=template)
        orchestrator.quality_manager.apply_preset = AsyncMock(
            return_value={"prompt": "test", "quality": "standard"}
        )
        orchestrator.worker_pool.submit_task = AsyncMock()
        orchestrator.progress_tracker.start_tracking = AsyncMock()
        orchestrator.progress_tracker.get_status = AsyncMock(
            return_value=Mock(
                state=TaskState.COMPLETED,
                outputs={"image": "test_output.png"},
                execution_time=25.0,
                resource_usage={"gpu": 6.0},
                metadata={}
            )
        )
        orchestrator.takes_service.create_take = AsyncMock()
        
        # Mock resource check
        orchestrator._check_resource_availability = AsyncMock(
            return_value={"available": True}
        )
        
        # Execute workflow
        result = await orchestrator.execute_workflow(
            template_id="test_template",
            inputs={"prompt": "test", "quality": "standard"},
            metadata={"user_id": "test_user"}
        )
        
        # Verify result
        assert result.task_id is not None
        assert result.status == TaskState.COMPLETED
        assert result.outputs == {"image": "test_output.png"}
        assert result.execution_time == 25.0
    
    @pytest.mark.asyncio
    async def test_task_cancellation(self):
        """Test task cancellation"""
        orchestrator = FunctionRunnerOrchestrator()
        
        # Mock active task
        task_id = "test_task_123"
        orchestrator._active_tasks[task_id] = Mock()
        
        # Mock cancellation
        orchestrator.worker_pool.cancel_task = AsyncMock(return_value=True)
        orchestrator.progress_tracker.update_status = AsyncMock()
        orchestrator._cleanup_task = AsyncMock()
        
        # Cancel task
        result = await orchestrator.cancel_task(task_id)
        
        assert result is True
        orchestrator.worker_pool.cancel_task.assert_called_once_with(task_id)
        orchestrator.progress_tracker.update_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resource_availability_check(self):
        """Test resource availability checking"""
        orchestrator = FunctionRunnerOrchestrator()
        
        template = Mock(spec=FunctionTemplate)
        template.resources = Mock(vram_gb=8.0, cpu_cores=4)
        
        # Mock worker pool response
        orchestrator.worker_pool.check_resource_availability = AsyncMock(
            return_value=Mock(
                available=True,
                reason=None,
                estimated_wait_time=0
            )
        )
        
        result = await orchestrator._check_resource_availability(template, {})
        
        assert result["available"] is True
        assert result["reason"] is None


class TestIntegratedTaskSubmissionHandler:
    """Test the integrated task submission handler"""
    
    @pytest.mark.asyncio
    async def test_task_submission(self):
        """Test complete task submission flow"""
        handler = IntegratedTaskSubmissionHandler()
        
        # Mock dependencies
        handler.orchestrator.submit_task_async = AsyncMock(
            return_value=TaskResponse(
                task_id="test_task",
                tracking_id="test_tracking",
                status="submitted",
                estimated_completion=30.0
            )
        )
        
        # Mock project validation
        handler._validate_project_context = AsyncMock(
            return_value=Project(
                id="test_project",
                name="Test Project",
                path="/test/path"
            )
        )
        
        # Mock asset resolution
        handler._resolve_asset_references = AsyncMock(
            return_value={"prompt": "test", "image": "/path/to/image.png"}
        )
        
        # Mock tracking creation
        handler._create_task_tracking = AsyncMock()
        handler._send_task_notification = AsyncMock()
        
        # Submit task
        request = IntegratedTaskRequest(
            template_id="test_template",
            inputs={"prompt": "test", "image": "asset://test_image"},
            quality="standard",
            project_id="test_project",
            user_id="test_user"
        )
        
        response = await handler.submit_task(request)
        
        # Verify response
        assert response.task_id == "test_task"
        assert response.status == "submitted"
        
        # Verify asset resolution was called
        handler._resolve_asset_references.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_asset_reference_resolution(self):
        """Test asset reference resolution"""
        handler = IntegratedTaskSubmissionHandler()
        
        project = Project(id="test_project", name="Test", path="/test")
        
        # Mock workspace service
        handler.workspace_service.resolve_asset = AsyncMock(
            return_value="/actual/path/to/asset.png"
        )
        
        inputs = {
            "prompt": "test prompt",
            "image": "asset://test_image_123",
            "nested": {
                "background": "asset://bg_image_456"
            }
        }
        
        resolved = await handler._resolve_asset_references(inputs, project)
        
        # Verify resolution
        assert resolved["prompt"] == "test prompt"
        assert resolved["image"] == "/actual/path/to/asset.png"
        assert resolved["nested"]["background"] == "/actual/path/to/asset.png"
        
        # Verify workspace service calls
        assert handler.workspace_service.resolve_asset.call_count == 2
    
    @pytest.mark.asyncio
    async def test_task_completion_handling(self):
        """Test task completion handling"""
        handler = IntegratedTaskSubmissionHandler()
        
        # Mock dependencies
        handler._store_outputs = AsyncMock(return_value={"image": "/stored/path"})
        handler._create_take = AsyncMock(return_value=Mock(id="take_123"))
        handler._update_canvas_node = AsyncMock()
        handler._commit_outputs_to_git = AsyncMock()
        handler._send_task_notification = AsyncMock()
        
        # Create test data
        project = Project(id="test_project", name="Test", path="/test")
        request = IntegratedTaskRequest(
            template_id="test_template",
            inputs={"prompt": "test"},
            canvas_node_id="node_123"
        )
        result = WorkflowResult(
            task_id="test_task",
            status=TaskState.COMPLETED,
            outputs={"image": "http://temp/image.png"},
            execution_time=30.0
        )
        
        # Handle completion
        await handler._handle_task_completion(result, project, request)
        
        # Verify all steps executed
        handler._store_outputs.assert_called_once()
        handler._create_take.assert_called_once()
        handler._update_canvas_node.assert_called_once()
        handler._commit_outputs_to_git.assert_called_once()
        handler._send_task_notification.assert_called()


class TestWebSocketIntegrationLayer:
    """Test WebSocket integration"""
    
    @pytest.mark.asyncio
    async def test_event_routing(self):
        """Test event routing to WebSocket"""
        ws_manager = Mock()
        ws_manager.send_to_user = AsyncMock()
        
        integration = WebSocketIntegrationLayer(ws_manager)
        
        # Create test event
        event = ServiceEvent(
            service="task",
            type="progress",
            data={
                "task_id": "test_task",
                "progress": 0.5,
                "stage": "processing",
                "message": "Processing image..."
            },
            metadata={"user_id": "test_user"}
        )
        
        # Route event
        await integration.route_event(event)
        
        # Verify WebSocket message sent
        ws_manager.send_to_user.assert_called_once()
        call_args = ws_manager.send_to_user.call_args
        assert call_args[0][0] == "test_user"  # user_id
        
        message = call_args[0][1]
        assert message["type"] == "generation.progress"
        assert message["data"]["taskId"] == "test_task"
        assert message["data"]["progress"] == 0.5
    
    @pytest.mark.asyncio
    async def test_task_completion_event(self):
        """Test task completion event handling"""
        ws_manager = Mock()
        ws_manager.send_to_user = AsyncMock()
        
        integration = WebSocketIntegrationLayer(ws_manager)
        
        event = ServiceEvent(
            service="task",
            type="completed",
            data={
                "task_id": "test_task",
                "outputs": {"image": "/path/to/image.png"},
                "execution_time": 30.0,
                "take_id": "take_123"
            },
            metadata={"user_id": "test_user"}
        )
        
        await integration.route_event(event)
        
        # Verify completion message
        ws_manager.send_to_user.assert_called_once()
        message = ws_manager.send_to_user.call_args[0][1]
        assert message["type"] == "generation.completed"
        assert message["data"]["taskId"] == "test_task"
        assert message["data"]["takeId"] == "take_123"
    
    @pytest.mark.asyncio
    async def test_client_subscriptions(self):
        """Test client subscription management"""
        ws_manager = Mock()
        integration = WebSocketIntegrationLayer(ws_manager)
        
        # Subscribe client to channels
        await integration.subscribe_client("client_123", ["task.test_task", "project.test_project"])
        
        # Verify subscriptions
        subscriptions = await integration.get_client_subscriptions("client_123")
        assert "task.test_task" in subscriptions
        assert "project.test_project" in subscriptions
        
        # Test channel subscribers
        subscribers = await integration.get_channel_subscribers("task.test_task")
        assert "client_123" in subscribers
        
        # Unsubscribe
        await integration.unsubscribe_client("client_123", ["task.test_task"])
        
        subscriptions = await integration.get_client_subscriptions("client_123")
        assert "task.test_task" not in subscriptions
        assert "project.test_project" in subscriptions


# Additional tests would go here for other integration components


class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """Test complete workflow from submission to completion"""
        
        # Setup all components
        orchestrator = FunctionRunnerOrchestrator()
        handler = IntegratedTaskSubmissionHandler()
        ws_integration = WebSocketIntegrationLayer(Mock())
        
        # Mock all dependencies for orchestrator
        orchestrator.worker_pool = Mock()
        orchestrator.template_registry = Mock()
        orchestrator.quality_manager = Mock()
        orchestrator.progress_tracker = Mock()
        orchestrator.takes_service = Mock()
        
        # Mock template
        template = Mock(spec=FunctionTemplate)
        template.id = "test_template"
        template.validate_inputs = AsyncMock(return_value={"prompt": "test"})
        template.resources.estimated_time_seconds = 30.0
        
        orchestrator.template_registry.get_template = AsyncMock(return_value=template)
        orchestrator.quality_manager.apply_preset = AsyncMock(
            return_value={"prompt": "test", "steps": 30}
        )
        orchestrator.worker_pool.submit_task = AsyncMock()
        orchestrator.progress_tracker.start_tracking = AsyncMock()
        orchestrator.progress_tracker.get_status = AsyncMock(
            return_value=Mock(
                state=TaskState.COMPLETED,
                outputs={"image": "output.png"},
                execution_time=25.0,
                resource_usage={},
                metadata={}
            )
        )
        orchestrator._check_resource_availability = AsyncMock(
            return_value={"available": True}
        )
        orchestrator.takes_service.create_take = AsyncMock()
        
        # Mock handler dependencies
        handler.orchestrator = orchestrator
        handler._validate_project_context = AsyncMock(return_value=None)
        handler._resolve_asset_references = AsyncMock(
            return_value={"prompt": "test"}
        )
        handler._create_task_tracking = AsyncMock()
        handler._send_task_notification = AsyncMock()
        
        # Submit integrated task
        request = IntegratedTaskRequest(
            template_id="test_template",
            inputs={"prompt": "test"},
            quality="standard",
            user_id="test_user"
        )
        
        response = await handler.submit_task(request)
        
        # Verify response
        assert response.task_id is not None
        assert response.status == "submitted"
        
        # Verify orchestrator was called
        orchestrator.template_registry.get_template.assert_called_with("test_template")
        orchestrator.worker_pool.submit_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test error propagation through integration layers"""
        
        orchestrator = FunctionRunnerOrchestrator()
        
        # Mock failure scenario
        orchestrator.template_registry = Mock()
        orchestrator.template_registry.get_template = AsyncMock(return_value=None)
        
        # Test that template not found error propagates
        with pytest.raises(Exception):
            await orchestrator.execute_workflow(
                template_id="nonexistent_template",
                inputs={"prompt": "test"},
                metadata={}
            )
    
    @pytest.mark.asyncio
    async def test_concurrent_task_handling(self):
        """Test handling multiple concurrent tasks"""
        
        orchestrator = FunctionRunnerOrchestrator()
        
        # Mock for successful execution
        template = Mock(spec=FunctionTemplate)
        template.validate_inputs = AsyncMock(return_value={"prompt": "test"})
        template.resources.estimated_time_seconds = 30.0
        
        orchestrator.template_registry = Mock()
        orchestrator.template_registry.get_template = AsyncMock(return_value=template)
        orchestrator.quality_manager = Mock()
        orchestrator.quality_manager.apply_preset = AsyncMock(
            return_value={"prompt": "test", "steps": 30}
        )
        orchestrator.worker_pool = Mock()
        orchestrator.worker_pool.submit_task = AsyncMock()
        orchestrator.progress_tracker = Mock()
        orchestrator.progress_tracker.start_tracking = AsyncMock()
        orchestrator.progress_tracker.get_status = AsyncMock(
            return_value=Mock(
                state=TaskState.COMPLETED,
                outputs={"image": "output.png"},
                execution_time=25.0,
                resource_usage={},
                metadata={}
            )
        )
        orchestrator._check_resource_availability = AsyncMock(
            return_value={"available": True}
        )
        orchestrator.takes_service = Mock()
        orchestrator.takes_service.create_take = AsyncMock()
        
        # Submit multiple concurrent tasks
        tasks = []
        for i in range(5):
            task = orchestrator.execute_workflow(
                template_id="test_template",
                inputs={"prompt": f"test {i}"},
                metadata={"user_id": f"user_{i}"}
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        
        # Verify all completed
        assert len(results) == 5
        for result in results:
            assert result.status == TaskState.COMPLETED
        
        # Verify worker pool got all submissions
        assert orchestrator.worker_pool.submit_task.call_count == 5