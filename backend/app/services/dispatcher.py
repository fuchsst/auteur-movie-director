"""
Task Dispatcher Service for Function Runner Architecture

Routes tasks to appropriate pipelines based on quality settings and provides
the foundation for containerized AI model execution.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class QualityTier(str, Enum):
    """Quality tiers for pipeline selection"""

    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"
    PREMIUM = "premium"


class PipelineConfig(BaseModel):
    """Configuration for AI pipeline execution"""

    pipeline_id: str
    container_image: str  # For future container orchestration
    target_vram: int  # Target VRAM usage in GB
    optimizations: list[str]  # Optimization flags
    max_concurrent: int  # Maximum concurrent tasks
    timeout_seconds: int  # Task timeout


class TaskDispatcher:
    """Routes tasks to appropriate pipelines based on quality settings"""

    # Quality-to-pipeline mapping configuration
    QUALITY_PIPELINE_MAPPING = {
        QualityTier.LOW: PipelineConfig(
            pipeline_id="auteur-flux:1.0-low-vram",
            container_image="auteur/flux-low:latest",  # Future container
            target_vram=12,
            optimizations=["cpu_offloading", "sequential", "low_res"],
            max_concurrent=1,
            timeout_seconds=300,
        ),
        QualityTier.STANDARD: PipelineConfig(
            pipeline_id="auteur-flux:1.0-standard",
            container_image="auteur/flux-standard:latest",  # Future container
            target_vram=16,
            optimizations=["moderate_parallel", "standard_res"],
            max_concurrent=2,
            timeout_seconds=180,
        ),
        QualityTier.HIGH: PipelineConfig(
            pipeline_id="auteur-flux:1.0-high-fidelity",
            container_image="auteur/flux-high:latest",  # Future container
            target_vram=24,
            optimizations=["full_parallel", "high_res"],
            max_concurrent=3,
            timeout_seconds=120,
        ),
        QualityTier.PREMIUM: PipelineConfig(
            pipeline_id="auteur-flux:1.0-premium",
            container_image="auteur/flux-premium:latest",  # Future container
            target_vram=48,
            optimizations=["multi_gpu", "max_quality"],
            max_concurrent=4,
            timeout_seconds=90,
        ),
    }

    def __init__(self):
        self.active_tasks: dict[str, dict[str, Any]] = {}
        logger.info("Task dispatcher initialized with quality mappings")

    async def dispatch_task(self, node_type: str, quality: str, parameters: dict[str, Any]) -> str:
        """
        Dispatch task to appropriate pipeline based on quality tier

        Args:
            node_type: Type of node (e.g., 'image_generation', 'video_generation')
            quality: Quality tier ('low', 'standard', 'high', 'premium')
            parameters: Task parameters including node_id, project_id, etc.

        Returns:
            str: Task ID for tracking
        """
        try:
            pipeline_config = self.get_pipeline_config(quality)

            # Prepare task payload for Celery worker
            task_payload = {
                "pipeline_id": pipeline_config.pipeline_id,
                "node_type": node_type,
                "parameters": parameters,
                "config": pipeline_config.dict(),
                "workspace_path": "/workspace",
                "created_at": datetime.utcnow().isoformat(),
            }

            # Submit to Celery (import here to avoid circular imports)
            from app.core.dispatcher import task_dispatcher

            # Use existing task dispatcher to submit generation task
            task_id = await task_dispatcher.submit_task(
                "generation", task_payload, priority=self._get_priority_for_quality(quality)
            )

            # Track active task
            self.active_tasks[task_id] = {
                "node_type": node_type,
                "quality": quality,
                "pipeline_config": pipeline_config,
                "created_at": datetime.utcnow(),
                "status": "queued",
            }

            logger.info(
                f"Task {task_id} dispatched to pipeline {pipeline_config.pipeline_id} "
                f"(quality: {quality}, node_type: {node_type})"
            )

            return task_id

        except Exception as e:
            logger.error(f"Failed to dispatch task: {e}")
            raise

    def get_pipeline_config(self, quality: str) -> PipelineConfig:
        """
        Get pipeline configuration for quality tier

        Args:
            quality: Quality tier string

        Returns:
            PipelineConfig: Configuration for the quality tier
        """
        try:
            tier = QualityTier(quality.lower())
            config = self.QUALITY_PIPELINE_MAPPING[tier]
            logger.debug(f"Retrieved config for quality '{quality}': {config.pipeline_id}")
            return config
        except (ValueError, KeyError):
            # Default to standard if unknown quality
            logger.warning(f"Unknown quality tier '{quality}', defaulting to standard")
            return self.QUALITY_PIPELINE_MAPPING[QualityTier.STANDARD]

    def _get_priority_for_quality(self, quality: str) -> int:
        """Get task priority based on quality tier"""
        priority_mapping = {
            QualityTier.LOW: 3,  # Lower priority
            QualityTier.STANDARD: 2,  # Normal priority
            QualityTier.HIGH: 1,  # High priority
            QualityTier.PREMIUM: 0,  # Highest priority
        }

        try:
            tier = QualityTier(quality.lower())
            return priority_mapping[tier]
        except (ValueError, KeyError):
            return priority_mapping[QualityTier.STANDARD]

    def get_active_tasks(self) -> dict[str, dict[str, Any]]:
        """Get all active tasks"""
        return self.active_tasks.copy()

    def get_task_info(self, task_id: str) -> dict[str, Any] | None:
        """Get information about a specific task"""
        return self.active_tasks.get(task_id)

    def mark_task_completed(self, task_id: str, result: dict[str, Any] | None = None):
        """Mark a task as completed and clean up tracking"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["completed_at"] = datetime.utcnow()
            if result:
                self.active_tasks[task_id]["result"] = result

            logger.info(f"Task {task_id} marked as completed")

    def mark_task_failed(self, task_id: str, error: str):
        """Mark a task as failed"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["failed_at"] = datetime.utcnow()
            self.active_tasks[task_id]["error"] = error

            logger.error(f"Task {task_id} marked as failed: {error}")

    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks"""
        now = datetime.utcnow()
        to_remove = []

        for task_id, task_info in self.active_tasks.items():
            if task_info["status"] in ["completed", "failed"]:
                completed_at = task_info.get("completed_at") or task_info.get("failed_at")
                if completed_at and (now - completed_at).total_seconds() > max_age_hours * 3600:
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self.active_tasks[task_id]
            logger.debug(f"Cleaned up old task {task_id}")


# Global dispatcher instance
task_dispatcher_service = TaskDispatcher()
