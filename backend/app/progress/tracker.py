"""Main progress tracking implementation"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from redis import asyncio as aioredis

from .models import (
    TaskProgress, StageProgress, TaskStatus, StageStatus,
    ProgressUpdate, BatchProgress, TaskHistory
)
from .stage_manager import StageManager
from .eta_predictor import ETAPredictor
from .preview_generator import PreviewGenerator
from ..services.websocket import WebSocketManager


class ProgressTracker:
    """Comprehensive progress tracking for function execution"""
    
    def __init__(
        self, 
        redis_client: aioredis.Redis,
        ws_manager: WebSocketManager,
        preview_dir: Optional[str] = None
    ):
        self.redis = redis_client
        self.ws_manager = ws_manager
        self.eta_predictor = ETAPredictor()
        self.preview_generator = PreviewGenerator(preview_dir)
        self.progress_cache: Dict[str, TaskProgress] = {}
        self._lock = asyncio.Lock()
        
    async def create_task_progress(
        self, 
        task_id: str, 
        template_id: str,
        template_category: str = 'default',
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskProgress:
        """Initialize progress tracking for a task"""
        # Get stages for this template
        stages = StageManager.get_stages_for_template(template_id, template_category)
        stage_progress = StageManager.create_stage_progress(stages)
        
        progress = TaskProgress(
            task_id=task_id,
            template_id=template_id,
            status=TaskStatus.QUEUED,
            current_stage=0,
            total_stages=len(stages),
            stages=stage_progress,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add metadata if provided
        if metadata:
            progress.logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': 'info',
                'message': 'Task created',
                'metadata': metadata
            })
        
        # Store in Redis with 24 hour TTL
        await self._save_progress(progress)
        
        # Send initial progress
        await self._broadcast_progress(progress)
        
        return progress
    
    async def update_stage(
        self, 
        task_id: str, 
        stage: int, 
        status: StageStatus,
        progress: float = 0.0,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update progress for a specific stage"""
        async with self._lock:
            task_progress = await self.get_progress(task_id)
            if not task_progress:
                raise ValueError(f"Task {task_id} not found")
            
            # Update stage
            if stage not in task_progress.stages:
                raise ValueError(f"Invalid stage {stage} for task {task_id}")
            
            stage_data = task_progress.stages[stage]
            stage_data.status = status
            stage_data.progress = min(max(progress, 0.0), 1.0)  # Clamp to 0-1
            
            if message:
                stage_data.message = message
            
            if metadata:
                stage_data.metadata.update(metadata)
            
            # Update timestamps
            now = datetime.now()
            if status == StageStatus.IN_PROGRESS and not stage_data.started_at:
                stage_data.started_at = now
                # Update task start time on first stage start
                if task_progress.started_at is None:
                    task_progress.started_at = now
                    task_progress.status = TaskStatus.PREPARING
            elif status in [StageStatus.COMPLETED, StageStatus.FAILED]:
                if not stage_data.completed_at:
                    stage_data.completed_at = now
            
            # Update overall task status
            task_progress.current_stage = stage
            task_progress.status = self._determine_task_status(task_progress)
            task_progress.overall_progress = self._calculate_overall_progress(task_progress)
            task_progress.updated_at = now
            
            # Add log entry
            task_progress.logs.append({
                'timestamp': now.isoformat(),
                'level': 'info' if status != StageStatus.FAILED else 'error',
                'message': f"Stage '{stage_data.name}' {status.value}",
                'stage': stage,
                'metadata': {'progress': progress}
            })
            
            # Calculate ETA for in-progress stages
            if status == StageStatus.IN_PROGRESS:
                task_progress.eta = await self.eta_predictor.predict(
                    template_id=task_progress.template_id,
                    current_stage=stage,
                    stage_progress=progress,
                    total_stages=task_progress.total_stages,
                    quality=metadata.get('quality', 'standard') if metadata else 'standard'
                )
            
            # Generate preview if applicable
            if stage_data.name in ['generation', 'frame_generation', 'execution']:
                preview_url = await self.preview_generator.generate_preview(
                    task_id=task_id,
                    task_data=metadata or {},
                    stage_progress=progress,
                    stage_name=stage_data.name
                )
                if preview_url:
                    task_progress.preview_url = preview_url
            
            # Check if task completed
            if task_progress.status == TaskStatus.COMPLETED:
                task_progress.completed_at = now
                await self._record_completion(task_progress)
            elif task_progress.status == TaskStatus.FAILED:
                task_progress.completed_at = now
                if stage_data.message:
                    task_progress.error = stage_data.message
            
            # Save and broadcast
            await self._save_progress(task_progress)
            await self._broadcast_progress(task_progress)
    
    async def update_resource_usage(
        self, 
        task_id: str, 
        resource_usage: Dict[str, float]
    ):
        """Update resource usage metrics"""
        task_progress = await self.get_progress(task_id)
        if not task_progress:
            return
        
        task_progress.resource_usage = resource_usage
        task_progress.updated_at = datetime.now()
        
        await self._save_progress(task_progress)
        await self._broadcast_progress(task_progress)
    
    async def add_log_entry(
        self, 
        task_id: str, 
        level: str, 
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a log entry to task progress"""
        task_progress = await self.get_progress(task_id)
        if not task_progress:
            return
        
        task_progress.logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'metadata': metadata or {}
        })
        
        # Limit log size
        if len(task_progress.logs) > 1000:
            task_progress.logs = task_progress.logs[-1000:]
        
        await self._save_progress(task_progress)
    
    async def get_progress(self, task_id: str) -> Optional[TaskProgress]:
        """Get current progress for a task"""
        # Check cache first
        if task_id in self.progress_cache:
            return self.progress_cache[task_id]
        
        # Load from Redis
        data = await self.redis.get(f"progress:{task_id}")
        if not data:
            return None
        
        progress = TaskProgress.model_validate_json(data)
        self.progress_cache[task_id] = progress
        return progress
    
    async def get_batch_progress(
        self, 
        batch_id: str, 
        task_ids: List[str]
    ) -> BatchProgress:
        """Get aggregated progress for a batch of tasks"""
        task_progresses = []
        
        for task_id in task_ids:
            progress = await self.get_progress(task_id)
            if progress:
                task_progresses.append(progress)
        
        return self._aggregate_batch_progress(batch_id, task_progresses)
    
    def _determine_task_status(self, progress: TaskProgress) -> TaskStatus:
        """Determine overall task status from stage statuses"""
        # Check for failures
        for stage in progress.stages.values():
            if stage.status == StageStatus.FAILED:
                return TaskStatus.FAILED
        
        # Check if all completed
        all_completed = all(
            stage.status in [StageStatus.COMPLETED, StageStatus.SKIPPED] 
            for stage in progress.stages.values()
        )
        if all_completed:
            return TaskStatus.COMPLETED
        
        # Determine status based on current stage
        current_stage_name = progress.stages[progress.current_stage].name
        
        if 'queue' in current_stage_name:
            return TaskStatus.QUEUED
        elif current_stage_name in ['preparation', 'model_loading', 'context_loading']:
            return TaskStatus.PREPARING
        elif current_stage_name in ['generation', 'frame_generation', 'synthesis', 'execution']:
            return TaskStatus.EXECUTING
        elif current_stage_name in ['finalization', 'post_processing', 'video_encoding', 'normalization']:
            return TaskStatus.FINALIZING
        
        return TaskStatus.EXECUTING
    
    def _calculate_overall_progress(self, task_progress: TaskProgress) -> float:
        """Calculate overall progress across all stages"""
        stages = StageManager.get_stages_for_template(
            task_progress.template_id
        )
        weights = StageManager.calculate_stage_weights(stages)
        
        weighted_progress = 0.0
        
        for stage_id, stage in task_progress.stages.items():
            weight = weights.get(stage_id, 0.25)
            
            if stage.status == StageStatus.COMPLETED:
                weighted_progress += weight
            elif stage.status == StageStatus.IN_PROGRESS:
                weighted_progress += weight * stage.progress
            elif stage.status == StageStatus.SKIPPED:
                weighted_progress += weight  # Count skipped as completed
        
        return weighted_progress * 100  # Convert to percentage
    
    def _aggregate_batch_progress(
        self, 
        batch_id: str,
        task_progresses: List[TaskProgress]
    ) -> BatchProgress:
        """Calculate aggregated progress for a batch"""
        if not task_progresses:
            return BatchProgress(batch_id=batch_id)
        
        total_tasks = len(task_progresses)
        completed_tasks = sum(1 for p in task_progresses if p.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for p in task_progresses if p.status == TaskStatus.FAILED)
        
        # Calculate overall progress
        total_progress = sum(p.overall_progress for p in task_progresses)
        overall_progress = total_progress / total_tasks if total_tasks > 0 else 0
        
        # Find latest ETA
        etas = [p.eta for p in task_progresses if p.eta and p.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]]
        batch_eta = max(etas) if etas else None
        
        # Create task summaries
        task_summaries = [
            {
                'task_id': p.task_id,
                'status': p.status.value,
                'progress': p.overall_progress,
                'current_stage': p.current_stage,
                'eta': p.eta.isoformat() if p.eta else None
            }
            for p in task_progresses
        ]
        
        return BatchProgress(
            batch_id=batch_id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            overall_progress=overall_progress,
            eta=batch_eta,
            task_summaries=task_summaries
        )
    
    async def _save_progress(self, progress: TaskProgress):
        """Save progress to Redis"""
        key = f"progress:{progress.task_id}"
        await self.redis.setex(
            key,
            86400,  # 24 hour TTL
            progress.model_dump_json()
        )
        
        # Update cache
        self.progress_cache[progress.task_id] = progress
    
    async def _broadcast_progress(self, progress: TaskProgress):
        """Broadcast progress update via WebSocket"""
        update = ProgressUpdate(
            task_id=progress.task_id,
            status=progress.status,
            current_stage=progress.current_stage,
            overall_progress=progress.overall_progress,
            eta=progress.eta,
            stages={
                str(k): {
                    'name': v.name,
                    'status': v.status.value,
                    'progress': v.progress,
                    'message': v.message
                } for k, v in progress.stages.items()
            },
            preview_url=progress.preview_url,
            resource_usage=progress.resource_usage,
            message=progress.stages[progress.current_stage].message
        )
        
        await self.ws_manager.broadcast({
            'type': 'progress.update',
            'task_id': progress.task_id,
            'data': update.model_dump()
        })
    
    async def _record_completion(self, progress: TaskProgress):
        """Record completed task for ETA prediction"""
        if progress.started_at and progress.completed_at:
            total_duration = (progress.completed_at - progress.started_at).total_seconds()
            stage_durations = progress.get_stage_durations()
            
            await self.eta_predictor.record_completion(
                task_id=progress.task_id,
                template_id=progress.template_id,
                quality=progress.logs[0].get('metadata', {}).get('quality', 'standard') if progress.logs else 'standard',
                stage_durations=stage_durations,
                total_duration=total_duration,
                resource_config=progress.resource_usage
            )
        
        # Clean up preview resources
        await self.preview_generator.cleanup_task_previews(progress.task_id)