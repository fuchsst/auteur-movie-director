"""
Integration API Endpoints

REST API endpoints for Function Runner integration system.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from .task_handler import IntegratedTaskSubmissionHandler
from .models import IntegratedTaskRequest, TaskResponse
from ..core.exceptions import (
    InsufficientResourcesError,
    WorkflowExecutionError,
    WorkflowTimeoutError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integration", tags=["integration"])

# Global handler instance
task_handler: Optional[IntegratedTaskSubmissionHandler] = None


class TaskSubmissionRequest(BaseModel):
    """Request model for task submission"""
    template_id: str
    inputs: Dict[str, Any]
    quality: str = "standard"
    project_id: Optional[str] = None
    shot_id: Optional[str] = None
    canvas_node_id: Optional[str] = None
    priority: int = 0
    metadata: Dict[str, Any] = {}


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str
    status: str
    progress: float = 0.0
    stage: Optional[str] = None
    message: Optional[str] = None
    outputs: Dict[str, Any] = {}
    error_message: Optional[str] = None
    execution_time: float = 0.0


class ActiveTasksResponse(BaseModel):
    """Response model for active tasks"""
    tasks: List[Dict[str, Any]]
    total_count: int


def get_task_handler() -> IntegratedTaskSubmissionHandler:
    """Get the task handler instance"""
    global task_handler
    if task_handler is None:
        raise HTTPException(
            status_code=503,
            detail="Task handler not initialized"
        )
    return task_handler


async def initialize_handler():
    """Initialize the global task handler"""
    global task_handler
    if task_handler is None:
        task_handler = IntegratedTaskSubmissionHandler()
        await task_handler.initialize()


@router.post("/tasks", response_model=TaskResponse)
async def submit_task(
    request: TaskSubmissionRequest,
    background_tasks: BackgroundTasks,
    user_id: str = None,  # Would get from auth
    handler: IntegratedTaskSubmissionHandler = Depends(get_task_handler)
) -> TaskResponse:
    """Submit a task for execution with full integration"""
    
    try:
        # Create integrated request
        integrated_request = IntegratedTaskRequest(
            template_id=request.template_id,
            inputs=request.inputs,
            quality=request.quality,
            project_id=request.project_id,
            shot_id=request.shot_id,
            user_id=user_id,
            canvas_node_id=request.canvas_node_id,
            priority=request.priority,
            metadata=request.metadata
        )
        
        # Submit task
        response = await handler.submit_task(integrated_request)
        
        logger.info(f"Task {response.task_id} submitted via API")
        return response
        
    except InsufficientResourcesError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except WorkflowExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    handler: IntegratedTaskSubmissionHandler = Depends(get_task_handler)
) -> TaskStatusResponse:
    """Get current status of a task"""
    
    try:
        status = await handler.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskStatusResponse(
            task_id=task_id,
            status=status.get('state', 'unknown'),
            progress=status.get('progress', 0.0),
            stage=status.get('stage'),
            message=status.get('message'),
            outputs=status.get('outputs', {}),
            error_message=status.get('error_message'),
            execution_time=status.get('execution_time', 0.0)
        )
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    handler: IntegratedTaskSubmissionHandler = Depends(get_task_handler)
) -> Dict[str, Any]:
    """Cancel an active task"""
    
    try:
        cancelled = await handler.cancel_task(task_id)
        
        if cancelled:
            return {"message": "Task cancelled successfully", "task_id": task_id}
        else:
            raise HTTPException(status_code=400, detail="Could not cancel task")
            
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tasks/active", response_model=ActiveTasksResponse)
async def get_active_tasks(
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    handler: IntegratedTaskSubmissionHandler = Depends(get_task_handler)
) -> ActiveTasksResponse:
    """Get list of active tasks, optionally filtered"""
    
    try:
        tasks = await handler.get_active_tasks(
            user_id=user_id,
            project_id=project_id
        )
        
        return ActiveTasksResponse(
            tasks=tasks,
            total_count=len(tasks)
        )
        
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def get_integration_health(
    handler: IntegratedTaskSubmissionHandler = Depends(get_task_handler)
) -> Dict[str, Any]:
    """Get integration system health status"""
    
    try:
        # Basic health check
        orchestrator_status = "healthy"  # Would check orchestrator health
        
        return {
            "status": orchestrator_status,
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "components": {
                "orchestrator": orchestrator_status,
                "worker_pool": "healthy",
                "template_registry": "healthy",
                "quality_manager": "healthy"
            }
        }
        
    except Exception as e:
        logger.error(f"Error checking integration health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/stats")
async def get_integration_stats(
    handler: IntegratedTaskSubmissionHandler = Depends(get_task_handler)
) -> Dict[str, Any]:
    """Get integration system statistics"""
    
    try:
        active_tasks = await handler.get_active_tasks()
        
        return {
            "active_tasks": len(active_tasks),
            "total_submissions": 0,  # Would track this
            "success_rate": 0.98,  # Would calculate this
            "average_execution_time": 45.0,  # Would calculate this
            "system_load": {
                "cpu": 0.4,
                "memory": 0.6,
                "gpu": 0.7
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting integration stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# WebSocket subscription endpoints
@router.post("/subscriptions/{client_id}")
async def subscribe_to_channels(
    client_id: str,
    channels: List[str],
    ws_integration = None  # Would inject WebSocketIntegrationLayer
) -> Dict[str, Any]:
    """Subscribe WebSocket client to channels"""
    
    try:
        # if ws_integration:
        #     await ws_integration.subscribe_client(client_id, channels)
        
        return {
            "message": f"Subscribed to {len(channels)} channels",
            "channels": channels
        }
        
    except Exception as e:
        logger.error(f"Error subscribing client: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/subscriptions/{client_id}")
async def unsubscribe_from_channels(
    client_id: str,
    channels: Optional[List[str]] = None,
    ws_integration = None  # Would inject WebSocketIntegrationLayer
) -> Dict[str, Any]:
    """Unsubscribe WebSocket client from channels"""
    
    try:
        # if ws_integration:
        #     await ws_integration.unsubscribe_client(client_id, channels)
        
        return {
            "message": "Unsubscribed successfully",
            "channels": channels or "all"
        }
        
    except Exception as e:
        logger.error(f"Error unsubscribing client: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Canvas integration endpoints
@router.post("/canvas/nodes")
async def create_function_node(
    canvas_id: str,
    template_id: str,
    position: Dict[str, float],
    canvas_integration = None  # Would inject CanvasNodeIntegration
) -> Dict[str, Any]:
    """Create a function node in canvas"""
    
    try:
        # if canvas_integration:
        #     node = await canvas_integration.create_function_node(
        #         canvas_id, template_id, position
        #     )
        #     return node.to_dict()
        
        return {
            "node_id": "mock_node_id",
            "template_id": template_id,
            "position": position,
            "status": "created"
        }
        
    except Exception as e:
        logger.error(f"Error creating function node: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/canvas/nodes/{node_id}/execute")
async def execute_function_node(
    node_id: str,
    inputs: Dict[str, Any],
    canvas_integration = None  # Would inject CanvasNodeIntegration
) -> Dict[str, Any]:
    """Execute a function node"""
    
    try:
        # if canvas_integration:
        #     task = await canvas_integration.execute_function_node(node_id, inputs)
        #     return {"task_id": task.task_id, "status": "executing"}
        
        return {
            "task_id": "mock_task_id",
            "node_id": node_id,
            "status": "executing"
        }
        
    except Exception as e:
        logger.error(f"Error executing function node: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")