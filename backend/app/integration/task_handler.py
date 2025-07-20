"""
Integrated Task Submission Handler

Handles complete task submission flow with platform integration.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from functools import partial

from app.integration.models import (
    IntegratedTaskRequest,
    TaskResponse,
    WorkflowResult,
    Project,
    OutputContext
)
from app.integration.orchestrator import FunctionRunnerOrchestrator
from app.services.workspace import WorkspaceService
from app.services.takes import TakesService
from app.services.git import GitService

logger = logging.getLogger(__name__)


class IntegratedTaskSubmissionHandler:
    """Handle complete task submission flow with full platform integration"""
    
    def __init__(self):
        self.orchestrator = FunctionRunnerOrchestrator()
        self.workspace_service = WorkspaceService()
        self.takes_service = TakesService()
        self.git_service = GitService()
        self._completion_callbacks: Dict[str, callable] = {}
    
    async def initialize(self):
        """Initialize the handler and all dependencies"""
        logger.info("Initializing Integrated Task Submission Handler")
        
        await self.orchestrator.initialize()
        logger.info("Task submission handler initialized")
    
    async def submit_task(self, request: IntegratedTaskRequest) -> TaskResponse:
        """Submit task with full integration"""
        
        task_id = str(uuid.uuid4())
        tracking_id = str(uuid.uuid4())
        
        logger.info(f"Submitting integrated task {task_id} for template {request.template_id}")
        
        try:
            # 1. Validate project context
            project = await self._validate_project_context(request.project_id)
            logger.debug(f"Project context validated for task {task_id}")
            
            # 2. Resolve asset references
            resolved_inputs = await self._resolve_asset_references(
                request.inputs,
                project
            )
            logger.debug(f"Asset references resolved for task {task_id}")
            
            # 3. Create task tracking
            await self._create_task_tracking(
                task_id=task_id,
                tracking_id=tracking_id,
                project_id=request.project_id,
                user_id=request.user_id,
                task_type=request.template_id
            )
            
            # 4. Submit to function runner orchestrator
            response = await self.orchestrator.submit_task_async(
                IntegratedTaskRequest(
                    template_id=request.template_id,
                    inputs=resolved_inputs,
                    quality=request.quality,
                    project_id=request.project_id,
                    shot_id=request.shot_id,
                    user_id=request.user_id,
                    canvas_node_id=request.canvas_node_id,
                    priority=request.priority,
                    metadata={
                        **request.metadata,
                        'tracking_id': tracking_id,
                        'submission_time': time.time()
                    }
                )
            )
            
            # 5. Set up result handling
            self._completion_callbacks[response.task_id] = partial(
                self._handle_task_completion,
                project=project,
                request=request
            )
            
            # 6. Send initial notification
            await self._send_task_notification(
                'task_submitted',
                task_id=response.task_id,
                project_id=request.project_id,
                estimated_time=response.estimated_completion
            )
            
            logger.info(f"Task {task_id} submitted successfully")
            
            return TaskResponse(
                task_id=response.task_id,
                tracking_id=tracking_id,
                status='submitted',
                estimated_completion=response.estimated_completion,
                message=f"Task submitted for {request.template_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to submit task {task_id}: {e}")
            raise
    
    async def _validate_project_context(self, project_id: Optional[str]) -> Optional[Project]:
        """Validate and retrieve project context"""
        
        if not project_id:
            logger.debug("No project_id provided, continuing without project context")
            return None
        
        try:
            # Get project from workspace service
            project_data = await self.workspace_service.get_project(project_id)
            
            if not project_data:
                raise ValueError(f"Project {project_id} not found")
            
            return Project(
                id=project_data['id'],
                name=project_data['name'],
                path=project_data['path'],
                metadata=project_data.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Failed to validate project context: {e}")
            raise
    
    async def _resolve_asset_references(self, 
                                      inputs: Dict[str, Any],
                                      project: Optional[Project]) -> Dict[str, Any]:
        """Resolve asset references to actual file paths"""
        
        if not project:
            return inputs
        
        resolved = inputs.copy()
        
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith('asset://'):
                # Resolve asset reference
                asset_id = value[8:]  # Remove 'asset://' prefix
                try:
                    asset_path = await self.workspace_service.resolve_asset(
                        project.id,
                        asset_id
                    )
                    resolved[key] = asset_path
                    logger.debug(f"Resolved asset {asset_id} to {asset_path}")
                except Exception as e:
                    logger.warning(f"Failed to resolve asset {asset_id}: {e}")
                    # Keep original value
                    
            elif isinstance(value, dict):
                # Recursively resolve nested references
                resolved[key] = await self._resolve_asset_references(
                    value, project
                )
        
        return resolved
    
    async def _create_task_tracking(self,
                                  task_id: str,
                                  tracking_id: str,
                                  project_id: Optional[str],
                                  user_id: Optional[str],
                                  task_type: str):
        """Create task tracking record"""
        
        try:
            # Create tracking record in database/storage
            tracking_data = {
                'task_id': task_id,
                'tracking_id': tracking_id,
                'project_id': project_id,
                'user_id': user_id,
                'task_type': task_type,
                'status': 'submitted',
                'created_at': time.time()
            }
            
            # Store tracking data (implementation depends on storage backend)
            # For now, just log it
            logger.info(f"Created task tracking: {tracking_data}")
            
        except Exception as e:
            logger.error(f"Failed to create task tracking: {e}")
            # Don't fail the task submission for tracking issues
    
    async def _handle_task_completion(self,
                                    result: WorkflowResult,
                                    project: Optional[Project],
                                    request: IntegratedTaskRequest):
        """Handle completed task with full integration"""
        
        task_id = result.task_id
        logger.info(f"Handling completion for task {task_id}")
        
        try:
            if result.status.value == 'completed':
                # 1. Store outputs in project structure
                if project:
                    stored_outputs = await self._store_outputs(
                        result.outputs,
                        project,
                        OutputContext(
                            task_id=task_id,
                            project_id=project.id,
                            shot_id=request.shot_id
                        )
                    )
                    logger.debug(f"Outputs stored for task {task_id}")
                else:
                    stored_outputs = result.outputs
                
                # 2. Create take record
                if project:
                    take = await self._create_take(
                        project_id=project.id,
                        shot_id=request.shot_id,
                        outputs=stored_outputs,
                        metadata={
                            'task_id': task_id,
                            'template_id': request.template_id,
                            'quality': request.quality,
                            'generation_time': result.execution_time,
                            'user_id': request.user_id
                        }
                    )
                    logger.debug(f"Created take {take.id} for task {task_id}")
                
                # 3. Update canvas node if applicable
                if request.canvas_node_id:
                    await self._update_canvas_node(
                        request.canvas_node_id,
                        take_id=take.id if project else None,
                        outputs=stored_outputs
                    )
                    logger.debug(f"Updated canvas node {request.canvas_node_id}")
                
                # 4. Commit to Git with LFS
                if project:
                    await self._commit_outputs_to_git(
                        project, take, stored_outputs
                    )
                    logger.debug(f"Committed outputs to Git for task {task_id}")
                
                # 5. Send completion notification
                await self._send_task_notification(
                    'task_completed',
                    task_id=task_id,
                    project_id=project.id if project else None,
                    take_id=take.id if project else None,
                    outputs=stored_outputs
                )
                
                logger.info(f"Task {task_id} completion handled successfully")
                
            else:
                # Handle failure
                await self._send_task_notification(
                    'task_failed',
                    task_id=task_id,
                    project_id=project.id if project else None,
                    error=result.error_message
                )
                logger.warning(f"Task {task_id} failed: {result.error_message}")
            
        except Exception as e:
            logger.error(f"Failed to handle task completion for {task_id}: {e}")
            await self._send_task_notification(
                'task_handling_failed',
                task_id=task_id,
                error=str(e)
            )
        
        finally:
            # Clean up callback
            self._completion_callbacks.pop(task_id, None)
    
    async def _store_outputs(self,
                           outputs: Dict[str, Any],
                           project: Project,
                           context: OutputContext) -> Dict[str, Any]:
        """Store function outputs in project structure"""
        
        # This would typically use the StorageIntegration class
        # For now, return the outputs as-is
        logger.debug(f"Storing outputs for task {context.task_id} in project {project.id}")
        
        # In a real implementation, this would:
        # 1. Download files from URLs
        # 2. Store them in the correct project paths
        # 3. Update paths to local storage
        # 4. Track large files with Git LFS
        
        return outputs
    
    async def _create_take(self,
                         project_id: str,
                         shot_id: Optional[str],
                         outputs: Dict[str, Any],
                         metadata: Dict[str, Any]) -> Any:
        """Create take record in takes system"""
        
        try:
            if shot_id:
                take = await self.takes_service.create_take(
                    project_id=project_id,
                    shot_id=shot_id,
                    outputs=outputs,
                    metadata=metadata
                )
            else:
                # Create in general renders
                take = await self.takes_service.create_take(
                    project_id=project_id,
                    outputs=outputs,
                    metadata=metadata
                )
            
            return take
            
        except Exception as e:
            logger.error(f"Failed to create take: {e}")
            raise
    
    async def _update_canvas_node(self,
                                canvas_node_id: str,
                                take_id: Optional[str],
                                outputs: Dict[str, Any]):
        """Update canvas node with results"""
        
        try:
            # Update node state and outputs
            # This would integrate with the canvas system
            logger.debug(f"Updating canvas node {canvas_node_id} with take {take_id}")
            
            # In a real implementation, this would:
            # 1. Get the canvas node
            # 2. Update its output ports with the results
            # 3. Set node state to completed
            # 4. Trigger node graph updates
            
        except Exception as e:
            logger.error(f"Failed to update canvas node {canvas_node_id}: {e}")
            # Don't raise - node update failure shouldn't fail the workflow
    
    async def _commit_outputs_to_git(self,
                                   project: Project,
                                   take: Any,
                                   outputs: Dict[str, Any]):
        """Commit outputs to Git with LFS"""
        
        try:
            # Commit the new take and outputs
            commit_message = f"Add take {take.id} - {take.metadata.get('template_id', 'generation')}"
            
            await self.git_service.commit_changes(
                project.id,
                message=commit_message,
                include_patterns=[f"**/take_{take.number:03d}/*"]
            )
            
            logger.debug(f"Committed take {take.id} to Git")
            
        except Exception as e:
            logger.error(f"Failed to commit outputs to Git: {e}")
            # Don't raise - Git commit failure shouldn't fail the workflow
    
    async def _send_task_notification(self,
                                    event_type: str,
                                    task_id: str,
                                    **kwargs):
        """Send task notification via WebSocket or other channels"""
        
        try:
            notification_data = {
                'type': event_type,
                'task_id': task_id,
                'timestamp': time.time(),
                **kwargs
            }
            
            # This would integrate with the WebSocket system
            logger.debug(f"Sending notification: {notification_data}")
            
            # In a real implementation, this would:
            # 1. Send via WebSocket to interested clients
            # 2. Send via email if configured
            # 3. Log to audit trail
            # 4. Update task tracking records
            
        except Exception as e:
            logger.error(f"Failed to send task notification: {e}")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        return await self.orchestrator.get_task_status(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task"""
        
        try:
            cancelled = await self.orchestrator.cancel_task(task_id)
            
            if cancelled:
                await self._send_task_notification(
                    'task_cancelled',
                    task_id=task_id
                )
            
            return cancelled
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    async def get_active_tasks(self, 
                             user_id: Optional[str] = None,
                             project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active tasks, optionally filtered by user or project"""
        
        try:
            all_tasks = await self.orchestrator.get_active_tasks()
            
            # Apply filters
            filtered_tasks = []
            for task in all_tasks:
                if user_id and task.get('user_id') != user_id:
                    continue
                if project_id and task.get('project_id') != project_id:
                    continue
                filtered_tasks.append(task)
            
            return filtered_tasks
            
        except Exception as e:
            logger.error(f"Error getting active tasks: {e}")
            return []
    
    async def shutdown(self):
        """Shutdown the handler gracefully"""
        
        logger.info("Shutting down Integrated Task Submission Handler")
        
        try:
            await self.orchestrator.shutdown()
            self._completion_callbacks.clear()
            
            logger.info("Task submission handler shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during handler shutdown: {e}")
            raise