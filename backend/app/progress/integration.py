"""Integration helpers for progress tracking with function runner"""

from typing import Optional, Dict, Any, Callable
import asyncio
from datetime import datetime

from .tracker import ProgressTracker
from .models import StageStatus, TaskStatus


class ProgressCallbackAdapter:
    """Adapter to convert function runner callbacks to progress tracker updates"""
    
    def __init__(self, tracker: ProgressTracker, task_id: str):
        self.tracker = tracker
        self.task_id = task_id
        self.current_stage = 0
        self.stage_mapping = {}
        
    async def on_queue_position(self, position: int, queue_size: int):
        """Handle queue position updates"""
        if position == 0:
            # Starting execution
            await self.tracker.update_stage(
                self.task_id,
                0,  # Queue stage
                StageStatus.COMPLETED,
                progress=1.0
            )
        else:
            # Still in queue
            progress = 1.0 - (position / queue_size) if queue_size > 0 else 0
            await self.tracker.update_stage(
                self.task_id,
                0,
                StageStatus.IN_PROGRESS,
                progress=progress,
                message=f"Position {position} of {queue_size} in queue"
            )
    
    async def on_model_loading(self, model_name: str, progress: float):
        """Handle model loading progress"""
        await self.tracker.update_stage(
            self.task_id,
            1,  # Model loading stage
            StageStatus.IN_PROGRESS,
            progress=progress,
            message=f"Loading {model_name}"
        )
        
        if progress >= 1.0:
            await self.tracker.update_stage(
                self.task_id,
                1,
                StageStatus.COMPLETED,
                progress=1.0
            )
    
    async def on_execution_progress(self, step: int, total_steps: int, 
                                  preview_path: Optional[str] = None):
        """Handle main execution progress"""
        progress = step / total_steps if total_steps > 0 else 0
        
        metadata = {'step': step, 'total_steps': total_steps}
        if preview_path:
            metadata['intermediate_output'] = preview_path
        
        await self.tracker.update_stage(
            self.task_id,
            2,  # Execution stage
            StageStatus.IN_PROGRESS,
            progress=progress,
            message=f"Step {step}/{total_steps}",
            metadata=metadata
        )
    
    async def on_post_processing(self, operation: str, progress: float):
        """Handle post-processing progress"""
        await self.tracker.update_stage(
            self.task_id,
            3,  # Post-processing stage
            StageStatus.IN_PROGRESS,
            progress=progress,
            message=f"Post-processing: {operation}"
        )
    
    async def on_complete(self, output_path: str):
        """Handle task completion"""
        # Complete final stage
        await self.tracker.update_stage(
            self.task_id,
            3,
            StageStatus.COMPLETED,
            progress=1.0,
            message="Completed",
            metadata={'output_path': output_path}
        )
    
    async def on_error(self, error: str, stage: Optional[int] = None):
        """Handle task error"""
        if stage is None:
            # Determine which stage failed based on current progress
            progress = await self.tracker.get_progress(self.task_id)
            if progress:
                stage = progress.current_stage
            else:
                stage = 0
        
        await self.tracker.update_stage(
            self.task_id,
            stage,
            StageStatus.FAILED,
            message=error
        )


def create_progress_callback(tracker: ProgressTracker, task_id: str) -> Callable:
    """Create a progress callback function for function runner"""
    adapter = ProgressCallbackAdapter(tracker, task_id)
    
    async def progress_callback(event_type: str, data: Dict[str, Any]):
        """Universal progress callback"""
        try:
            if event_type == 'queue_position':
                await adapter.on_queue_position(
                    data.get('position', 0),
                    data.get('queue_size', 0)
                )
            elif event_type == 'model_loading':
                await adapter.on_model_loading(
                    data.get('model_name', 'model'),
                    data.get('progress', 0)
                )
            elif event_type == 'execution_progress':
                await adapter.on_execution_progress(
                    data.get('step', 0),
                    data.get('total_steps', 0),
                    data.get('preview_path')
                )
            elif event_type == 'post_processing':
                await adapter.on_post_processing(
                    data.get('operation', 'processing'),
                    data.get('progress', 0)
                )
            elif event_type == 'complete':
                await adapter.on_complete(data.get('output_path', ''))
            elif event_type == 'error':
                await adapter.on_error(
                    data.get('message', 'Unknown error'),
                    data.get('stage')
                )
            elif event_type == 'resource_usage':
                await tracker.update_resource_usage(task_id, data)
            elif event_type == 'log':
                await tracker.add_log_entry(
                    task_id,
                    data.get('level', 'info'),
                    data.get('message', ''),
                    data.get('metadata')
                )
        except Exception as e:
            # Log error but don't fail the task
            print(f"Progress callback error: {e}")
    
    return progress_callback


class ProgressContext:
    """Context manager for automatic progress tracking"""
    
    def __init__(self, tracker: ProgressTracker, task_id: str, 
                 template_id: str, template_category: str = 'default'):
        self.tracker = tracker
        self.task_id = task_id
        self.template_id = template_id
        self.template_category = template_category
        self.progress = None
        
    async def __aenter__(self):
        """Initialize progress tracking"""
        self.progress = await self.tracker.create_task_progress(
            self.task_id,
            self.template_id,
            self.template_category
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finalize progress tracking"""
        if exc_type is not None:
            # Task failed
            await self.tracker.update_stage(
                self.task_id,
                self.progress.current_stage,
                StageStatus.FAILED,
                message=str(exc_val)
            )
        # Cleanup is handled by the tracker
        
    def get_callback(self) -> Callable:
        """Get progress callback for function runner"""
        return create_progress_callback(self.tracker, self.task_id)