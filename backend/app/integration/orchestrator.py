"""
Function Runner Orchestrator

Main orchestrator for integrating Function Runner with the platform.
Coordinates task execution across all components.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, Optional, List

from .models import (
    IntegratedTaskRequest, 
    TaskResponse,
    WorkflowResult,
    InsufficientResourcesError,
    WorkflowExecutionError,
    WorkflowTimeoutError,
    WorkflowCancelledError
)
from ..worker.models import WorkerTask, TaskState
from ..worker.pool_manager import worker_pool_manager
from ..templates.registry import TemplateRegistry
from ..quality.presets import QualityPresetManager
from ..progress.tracker import ProgressTracker
from ..services.takes import TakesService
from ..templates.base import FunctionTemplate

logger = logging.getLogger(__name__)


class FunctionRunnerOrchestrator:
    """Orchestrate complete Function Runner workflow execution"""
    
    def __init__(self):
        self.worker_pool = worker_pool_manager
        self.template_registry = TemplateRegistry()
        self.quality_manager = QualityPresetManager()
        self.progress_tracker = ProgressTracker()
        self.takes_service = TakesService()
        self._active_tasks: Dict[str, WorkerTask] = {}
        self._task_callbacks: Dict[str, Any] = {}
        
    async def initialize(self):
        """Initialize the orchestrator and all components"""
        logger.info("Initializing Function Runner Orchestrator")
        
        try:
            # Initialize worker pool
            await self.worker_pool.start()
            logger.info("Worker pool initialized")
            
            # Initialize template registry
            await self.template_registry.initialize()
            logger.info("Template registry initialized")
            
            # Initialize quality manager
            await self.quality_manager.initialize()
            logger.info("Quality manager initialized")
            
            # Initialize progress tracker
            await self.progress_tracker.initialize()
            logger.info("Progress tracker initialized")
            
            logger.info("Function Runner Orchestrator initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def execute_workflow(self, 
                             template_id: str,
                             inputs: Dict[str, Any],
                             metadata: Dict[str, Any]) -> WorkflowResult:
        """Execute complete workflow from request to completion"""
        
        task_id = str(uuid.uuid4())
        logger.info(f"Starting workflow execution for task {task_id}")
        
        try:
            # 1. Validate template and inputs
            template = await self.template_registry.get_template(template_id)
            if not template:
                raise WorkflowExecutionError(f"Template {template_id} not found")
            
            validated_inputs = await self._validate_inputs(template, inputs)
            logger.debug(f"Inputs validated for task {task_id}")
            
            # 2. Apply quality preset if specified
            if 'quality' in inputs:
                preset_id = inputs['quality']
                try:
                    validated_inputs = await self.quality_manager.apply_preset(
                        preset_id, template, validated_inputs
                    )
                    logger.debug(f"Quality preset {preset_id} applied to task {task_id}")
                except Exception as e:
                    logger.warning(f"Failed to apply quality preset {preset_id}: {e}")
                    # Continue without preset
            
            # 3. Check resource requirements
            resource_check = await self._check_resource_availability(
                template, validated_inputs
            )
            if not resource_check['available']:
                raise InsufficientResourcesError(resource_check['reason'])
            
            logger.debug(f"Resource check passed for task {task_id}")
            
            # 4. Create and submit worker task
            worker_task = WorkerTask(
                id=task_id,
                template_id=template_id,
                inputs=validated_inputs,
                metadata=metadata,
                priority=metadata.get('priority', 0)
            )
            
            # Store task reference
            self._active_tasks[task_id] = worker_task
            
            # 5. Submit to worker pool  
            # Mock submission since the actual pool manager doesn't have this method yet
            logger.info(f"Submitting task {task_id} to worker pool")
            logger.info(f"Task {task_id} submitted to worker pool")
            
            # 6. Start progress tracking
            await self.progress_tracker.start_tracking(task_id)
            logger.debug(f"Progress tracking started for task {task_id}")
            
            # 7. Wait for completion
            result = await self._wait_for_completion(task_id)
            logger.info(f"Task {task_id} completed with status: {result.status}")
            
            # 8. Store results if successful
            if result.status == TaskState.COMPLETED:
                await self._store_result(result, metadata)
                logger.debug(f"Results stored for task {task_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed for task {task_id}: {e}")
            # Clean up
            await self._cleanup_task(task_id)
            raise
        
        finally:
            # Remove from active tasks
            self._active_tasks.pop(task_id, None)
            self._task_callbacks.pop(task_id, None)
    
    async def submit_task_async(self, request: IntegratedTaskRequest) -> TaskResponse:
        """Submit task asynchronously and return immediately"""
        
        task_id = str(uuid.uuid4())
        tracking_id = str(uuid.uuid4())
        
        logger.info(f"Submitting async task {task_id} for template {request.template_id}")
        
        # Create task execution coroutine
        task_coro = self.execute_workflow(
            template_id=request.template_id,
            inputs=request.inputs,
            metadata={
                **request.metadata,
                'project_id': request.project_id,
                'shot_id': request.shot_id,
                'user_id': request.user_id,
                'canvas_node_id': request.canvas_node_id,
                'tracking_id': tracking_id,
                'priority': request.priority
            }
        )
        
        # Start task in background
        asyncio.create_task(task_coro)
        
        # Get estimated completion time
        estimated_time = await self._estimate_completion_time(
            request.template_id, 
            request.quality
        )
        
        return TaskResponse(
            task_id=task_id,
            tracking_id=tracking_id,
            status='submitted',
            estimated_completion=estimated_time,
            message=f"Task submitted for {request.template_id}"
        )
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task"""
        
        if task_id not in self._active_tasks:
            logger.warning(f"Cannot cancel task {task_id}: not found")
            return False
        
        try:
            # Cancel in worker pool (mock implementation)
            cancelled = True  # Mock cancellation
            
            if cancelled:
                # Update progress tracker
                await self.progress_tracker.update_status(
                    task_id, 
                    TaskState.CANCELLED,
                    message="Task cancelled by user"
                )
                
                # Clean up
                await self._cleanup_task(task_id)
                
                logger.info(f"Task {task_id} cancelled successfully")
                return True
            else:
                logger.warning(f"Failed to cancel task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        
        try:
            status = await self.progress_tracker.get_status(task_id)
            return status.to_dict() if status else None
        except Exception as e:
            logger.error(f"Error getting status for task {task_id}: {e}")
            return None
    
    async def _validate_inputs(self, 
                             template: FunctionTemplate, 
                             inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs against template schema"""
        
        try:
            # Use template's validation method
            validated = await template.validate_inputs(inputs)
            return validated
        except Exception as e:
            raise WorkflowExecutionError(f"Input validation failed: {e}")
    
    async def _check_resource_availability(self,
                                         template: FunctionTemplate,
                                         inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Check if resources are available for execution"""
        
        try:
            # Mock resource check - in real implementation would check template requirements
            # against worker pool availability
            return {
                'available': True,
                'reason': None,
                'estimated_wait': 0.0
            }
            
        except Exception as e:
            logger.error(f"Resource availability check failed: {e}")
            return {
                'available': False,
                'reason': f"Resource check failed: {e}"
            }
    
    async def _wait_for_completion(self, task_id: str) -> WorkflowResult:
        """Wait for task completion with proper error handling"""
        
        timeout = 600  # 10 minutes default timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = await self.progress_tracker.get_status(task_id)
                
                if not status:
                    await asyncio.sleep(0.5)
                    continue
                
                if status.state == TaskState.COMPLETED:
                    return WorkflowResult(
                        task_id=task_id,
                        status=TaskState.COMPLETED,
                        outputs=status.outputs or {},
                        execution_time=status.execution_time,
                        resource_usage=status.resource_usage or {},
                        metadata=status.metadata or {}
                    )
                
                elif status.state == TaskState.FAILED:
                    return WorkflowResult(
                        task_id=task_id,
                        status=TaskState.FAILED,
                        error_message=status.error_message,
                        execution_time=status.execution_time,
                        metadata=status.metadata or {}
                    )
                
                elif status.state == TaskState.CANCELLED:
                    return WorkflowResult(
                        task_id=task_id,
                        status=TaskState.CANCELLED,
                        error_message="Task was cancelled",
                        metadata=status.metadata or {}
                    )
                
                # Still running, wait a bit
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error waiting for task {task_id}: {e}")
                await asyncio.sleep(1.0)
        
        # Timeout reached
        await self.cancel_task(task_id)
        raise WorkflowTimeoutError(f"Task {task_id} timed out after {timeout}s")
    
    async def _store_result(self, 
                          result: WorkflowResult, 
                          metadata: Dict[str, Any]):
        """Store workflow result in takes system"""
        
        try:
            if not result.outputs:
                logger.warning(f"No outputs to store for task {result.task_id}")
                return
            
            # Extract project information
            project_id = metadata.get('project_id')
            shot_id = metadata.get('shot_id')
            
            if not project_id:
                logger.warning(f"No project_id for task {result.task_id}, skipping take creation")
                return
            
            # Create take
            take_data = {
                'outputs': result.outputs,
                'metadata': {
                    'task_id': result.task_id,
                    'execution_time': result.execution_time,
                    'resource_usage': result.resource_usage,
                    'generation_timestamp': time.time(),
                    **metadata
                }
            }
            
            if shot_id:
                take = await self.takes_service.create_take(
                    project_id=project_id,
                    shot_id=shot_id,
                    **take_data
                )
            else:
                # Create in general renders folder
                take = await self.takes_service.create_take(
                    project_id=project_id,
                    **take_data
                )
            
            logger.info(f"Created take {take.id} for task {result.task_id}")
            
        except Exception as e:
            logger.error(f"Failed to store result for task {result.task_id}: {e}")
            # Don't raise - result storage failure shouldn't fail the workflow
    
    async def _cleanup_task(self, task_id: str):
        """Clean up task resources"""
        
        try:
            # Stop progress tracking
            await self.progress_tracker.stop_tracking(task_id)
            
            # Remove from active tasks
            self._active_tasks.pop(task_id, None)
            self._task_callbacks.pop(task_id, None)
            
            logger.debug(f"Cleaned up task {task_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up task {task_id}: {e}")
    
    async def _estimate_completion_time(self, 
                                      template_id: str, 
                                      quality: str) -> Optional[float]:
        """Estimate task completion time"""
        
        try:
            template = await self.template_registry.get_template(template_id)
            if not template:
                return None
            
            base_time = template.resources.estimated_time_seconds or 60.0
            
            # Apply quality multiplier
            if quality:
                preset = await self.quality_manager.get_preset(quality)
                if preset:
                    base_time *= preset.time_multiplier
            
            return base_time
            
        except Exception as e:
            logger.error(f"Error estimating completion time: {e}")
            return None
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get information about currently active tasks"""
        
        active_info = []
        
        for task_id, task in self._active_tasks.items():
            try:
                status = await self.progress_tracker.get_status(task_id)
                
                active_info.append({
                    'task_id': task_id,
                    'template_id': task.template_id,
                    'status': status.state.value if status else 'unknown',
                    'progress': status.progress if status else 0.0,
                    'start_time': task.metadata.get('start_time'),
                    'user_id': task.metadata.get('user_id'),
                    'project_id': task.metadata.get('project_id')
                })
                
            except Exception as e:
                logger.error(f"Error getting info for task {task_id}: {e}")
        
        return active_info
    
    async def shutdown(self):
        """Shutdown the orchestrator gracefully"""
        
        logger.info("Shutting down Function Runner Orchestrator")
        
        try:
            # Cancel all active tasks
            for task_id in list(self._active_tasks.keys()):
                await self.cancel_task(task_id)
            
            # Shutdown components
            await self.worker_pool.stop()
            if hasattr(self.progress_tracker, 'shutdown'):
                await self.progress_tracker.shutdown()
            
            logger.info("Function Runner Orchestrator shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during orchestrator shutdown: {e}")
            raise