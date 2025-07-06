"""
Task dispatcher for routing generation tasks to appropriate handlers.
Foundation for Function Runner integration.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from app.config import settings
from app.redis_client import redis_client

logger = logging.getLogger(__name__)


class TaskHandler(ABC):
    """Abstract base for task handlers"""

    @abstractmethod
    async def can_handle(self, task_type: str) -> bool:
        """Check if this handler can process the task type"""
        pass

    @abstractmethod
    async def process(self, task_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """Process the task and return result"""
        pass


class TaskDispatcher:
    """Routes tasks to appropriate handlers with quality-based configuration"""

    def __init__(self):
        self.handlers: dict[str, TaskHandler] = {}
        self.active_tasks: dict[str, asyncio.Task] = {}

    def register_handler(self, name: str, handler: TaskHandler):
        """Register a task handler"""
        self.handlers[name] = handler
        logger.info(f"Registered handler: {name}")

    async def dispatch(
        self, project_id: str, task_type: str, params: dict[str, Any], quality: str = "standard"
    ) -> str:
        """Dispatch task to appropriate handler"""
        # Generate task ID
        task_id = f"{project_id}:{task_type}:{int(asyncio.get_event_loop().time() * 1000)}"

        # Apply quality settings
        quality_params = settings.quality_presets.get(quality, {})
        params = {**quality_params, **params}

        # Log task dispatch
        logger.info(f"Dispatching task {task_id} with quality {quality}")

        # Find handler
        handler = None
        for name, h in self.handlers.items():
            if await h.can_handle(task_type):
                handler = h
                logger.debug(f"Task {task_id} will be handled by {name}")
                break

        if not handler:
            error_msg = f"No handler found for task type: {task_type}"
            logger.error(error_msg)
            # Publish error to Redis
            await redis_client.publish_progress(
                project_id, task_id, {"error": error_msg, "message": "Task failed"}
            )
            raise ValueError(error_msg)

        # Create async task
        task = asyncio.create_task(self._run_task(task_id, project_id, handler, params))
        self.active_tasks[task_id] = task

        return task_id

    async def _run_task(
        self, task_id: str, project_id: str, handler: TaskHandler, params: dict[str, Any]
    ):
        """Run task with progress tracking"""
        try:
            # Notify start
            await redis_client.publish_progress(
                project_id, task_id, {"progress": 0.0, "message": "Task started"}
            )

            # Process task
            result = await handler.process(task_id, params)

            # Notify completion
            await redis_client.publish_progress(
                project_id,
                task_id,
                {"progress": 1.0, "message": "Task completed", "result": result},
            )

        except asyncio.CancelledError:
            logger.info(f"Task {task_id} was cancelled")
            await redis_client.publish_progress(
                project_id, task_id, {"error": "Task cancelled", "message": "Task was cancelled"}
            )
            raise

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            await redis_client.publish_progress(
                project_id, task_id, {"error": str(e), "message": "Task failed"}
            )
        finally:
            self.active_tasks.pop(task_id, None)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task"""
        task = self.active_tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled task {task_id}")
            return True
        return False

    def get_active_tasks(self) -> list[str]:
        """Get list of active task IDs"""
        return list(self.active_tasks.keys())

    async def shutdown(self):
        """Cancel all active tasks for graceful shutdown"""
        logger.info(f"Cancelling {len(self.active_tasks)} active tasks")
        for _, task in self.active_tasks.items():
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)


# Global dispatcher instance
task_dispatcher = TaskDispatcher()


# Example handler for testing (will be replaced with actual handlers)
class EchoTaskHandler(TaskHandler):
    """Simple echo handler for testing"""

    async def can_handle(self, task_type: str) -> bool:
        return task_type == "echo"

    async def process(self, task_id: str, params: dict[str, Any]) -> dict[str, Any]:
        # Simulate some work
        await asyncio.sleep(2)
        return {"echo": params.get("message", "Hello World"), "task_id": task_id}
