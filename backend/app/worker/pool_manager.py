"""
Worker Pool Management System

Manages lifecycle of function runner workers with dynamic scaling,
health monitoring, and resource allocation.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil
from pydantic import BaseModel

from app.config import settings
from app.redis_client import redis_client

logger = logging.getLogger(__name__)


class WorkerType(str, Enum):
    """Types of workers available"""
    GENERAL = "general"
    GPU = "gpu" 
    CPU = "cpu"
    IO = "io"


class WorkerStatus(str, Enum):
    """Worker status states"""
    STARTING = "starting"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    STOPPING = "stopping"
    FAILED = "failed"


class ResourceAllocation(BaseModel):
    """Resource allocation for a worker"""
    cpu_cores: float
    memory_gb: float
    gpu_memory_gb: Optional[float] = None
    gpu_count: int = 0


class WorkerInfo(BaseModel):
    """Information about a worker instance"""
    id: str
    type: WorkerType
    status: WorkerStatus
    pid: Optional[int] = None
    started_at: datetime
    last_heartbeat: Optional[datetime] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    current_task_id: Optional[str] = None
    resources: ResourceAllocation
    queues: List[str]
    idle_since: Optional[datetime] = None


class SystemResources(BaseModel):
    """System resource information"""
    cpu_cores: int
    memory_gb: float
    gpu_count: int = 0
    gpu_memory_gb: float = 0.0


class WorkerPoolManager:
    """Manages lifecycle of function runner workers"""

    def __init__(
        self,
        min_workers: int = 1,
        max_workers: int = 10,
        scale_up_threshold: int = 5,
        scale_down_threshold: int = 0,
        idle_timeout: int = 300,
        health_check_interval: int = 30,
    ):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.idle_timeout = idle_timeout
        self.health_check_interval = health_check_interval
        
        self.workers: Dict[str, WorkerInfo] = {}
        self.resource_monitor = ResourceMonitor()
        self.health_checker = HealthChecker(self)
        self._scaling_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def start(self):
        """Start the worker pool manager"""
        logger.info("Starting worker pool manager")
        
        # Initialize minimum workers
        for _ in range(self.min_workers):
            await self.spawn_worker(WorkerType.GENERAL)
        
        # Start background tasks
        self._scaling_task = asyncio.create_task(self._scaling_loop())
        self._health_task = asyncio.create_task(self._health_monitoring_loop())
        
        logger.info(f"Worker pool manager started with {len(self.workers)} workers")

    async def stop(self):
        """Stop the worker pool manager"""
        logger.info("Stopping worker pool manager")
        self._shutdown = True
        
        # Cancel background tasks
        if self._scaling_task:
            self._scaling_task.cancel()
        if self._health_task:
            self._health_task.cancel()
        
        # Gracefully stop all workers
        await self._stop_all_workers()
        
        logger.info("Worker pool manager stopped")

    async def spawn_worker(
        self, 
        worker_type: WorkerType = WorkerType.GENERAL,
        resources: Optional[ResourceAllocation] = None
    ) -> Optional[str]:
        """Spawn new worker with resource allocation"""
        
        if len(self.workers) >= self.max_workers:
            logger.warning("Cannot spawn worker: maximum workers reached")
            return None
        
        if not await self.resource_monitor.can_spawn_worker(worker_type):
            logger.warning(f"Insufficient resources for {worker_type} worker")
            return None
        
        worker_id = f"worker_{worker_type.value}_{uuid.uuid4().hex[:8]}"
        
        if not resources:
            resources = await self.resource_monitor.allocate_resources(worker_type)
        
        # Create worker info
        worker_info = WorkerInfo(
            id=worker_id,
            type=worker_type,
            status=WorkerStatus.STARTING,
            started_at=datetime.now(),
            resources=resources,
            queues=self._get_queues_for_type(worker_type)
        )
        
        self.workers[worker_id] = worker_info
        
        try:
            # Start worker process (simulated for now)
            await self._start_worker_process(worker_info)
            
            # Register with Redis
            await self._register_worker_with_redis(worker_info)
            
            worker_info.status = WorkerStatus.ACTIVE
            logger.info(f"Spawned {worker_type} worker {worker_id}")
            
            return worker_id
            
        except Exception as e:
            logger.error(f"Failed to spawn worker {worker_id}: {e}")
            self.workers.pop(worker_id, None)
            await self.resource_monitor.deallocate_resources(resources)
            return None

    async def terminate_worker(self, worker_id: str, graceful: bool = True) -> bool:
        """Terminate a specific worker"""
        worker = self.workers.get(worker_id)
        if not worker:
            return False
        
        logger.info(f"Terminating worker {worker_id} (graceful={graceful})")
        
        worker.status = WorkerStatus.STOPPING
        
        try:
            if graceful:
                # Wait for current task to complete
                if worker.current_task_id:
                    await self._wait_for_task_completion(worker.current_task_id, timeout=60)
            
            # Stop worker process
            await self._stop_worker_process(worker)
            
            # Unregister from Redis
            await self._unregister_worker_from_redis(worker)
            
            # Deallocate resources
            await self.resource_monitor.deallocate_resources(worker.resources)
            
            # Remove from tracking
            self.workers.pop(worker_id, None)
            
            logger.info(f"Worker {worker_id} terminated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error terminating worker {worker_id}: {e}")
            return False

    async def scale_workers(self):
        """Dynamic scaling based on queue depth and resources"""
        if self._shutdown:
            return
        
        queue_depth = await self._get_queue_depth()
        active_workers = len(self.get_active_workers())
        idle_workers = len(self.get_idle_workers())
        
        logger.debug(f"Scaling check: queue={queue_depth}, active={active_workers}, idle={idle_workers}")
        
        # Scale up if needed
        if queue_depth > self.scale_up_threshold * active_workers and active_workers < self.max_workers:
            worker_type = self._determine_worker_type_for_queue()
            await self.spawn_worker(worker_type)
        
        # Scale down if idle workers exist
        elif idle_workers > 0 and queue_depth <= self.scale_down_threshold:
            await self._terminate_idle_worker()

    async def get_worker_metrics(self) -> Dict[str, Any]:
        """Get comprehensive worker pool metrics"""
        active_workers = self.get_active_workers()
        idle_workers = self.get_idle_workers()
        busy_workers = self.get_busy_workers()
        
        total_resources = await self.resource_monitor.get_total_resources()
        allocated_resources = await self.resource_monitor.get_allocated_resources()
        
        return {
            "total_workers": len(self.workers),
            "active_workers": len(active_workers),
            "idle_workers": len(idle_workers),
            "busy_workers": len(busy_workers),
            "worker_types": {
                worker_type.value: len([w for w in self.workers.values() if w.type == worker_type])
                for worker_type in WorkerType
            },
            "resource_utilization": {
                "cpu_percent": (allocated_resources.cpu_cores / total_resources.cpu_cores) * 100 if total_resources.cpu_cores > 0 else 0,
                "memory_percent": (allocated_resources.memory_gb / total_resources.memory_gb) * 100 if total_resources.memory_gb > 0 else 0,
                "gpu_percent": (allocated_resources.gpu_memory_gb / total_resources.gpu_memory_gb) * 100 if total_resources.gpu_memory_gb > 0 else 0,
            },
            "queue_depth": await self._get_queue_depth(),
            "scaling_limits": {
                "min_workers": self.min_workers,
                "max_workers": self.max_workers,
                "scale_up_threshold": self.scale_up_threshold,
                "scale_down_threshold": self.scale_down_threshold,
            }
        }

    def get_active_workers(self) -> List[WorkerInfo]:
        """Get list of active workers"""
        return [w for w in self.workers.values() if w.status == WorkerStatus.ACTIVE]

    def get_idle_workers(self) -> List[WorkerInfo]:
        """Get list of idle workers"""
        return [w for w in self.workers.values() if w.status == WorkerStatus.IDLE]

    def get_busy_workers(self) -> List[WorkerInfo]:
        """Get list of busy workers"""
        return [w for w in self.workers.values() if w.status == WorkerStatus.BUSY]

    def get_worker_info(self, worker_id: str) -> Optional[WorkerInfo]:
        """Get information about a specific worker"""
        return self.workers.get(worker_id)

    async def _scaling_loop(self):
        """Background task for continuous scaling"""
        while not self._shutdown:
            try:
                await self.scale_workers()
                await asyncio.sleep(10)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scaling loop: {e}")
                await asyncio.sleep(5)

    async def _health_monitoring_loop(self):
        """Background task for health monitoring"""
        while not self._shutdown:
            try:
                await self.health_checker.check_all_workers()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _terminate_idle_worker(self):
        """Terminate an idle worker"""
        idle_workers = self.get_idle_workers()
        if not idle_workers or len(self.workers) <= self.min_workers:
            return
        
        # Find worker that's been idle longest
        oldest_idle = min(idle_workers, key=lambda w: w.idle_since or w.started_at)
        
        if oldest_idle.idle_since:
            idle_duration = (datetime.now() - oldest_idle.idle_since).total_seconds()
            if idle_duration >= self.idle_timeout:
                await self.terminate_worker(oldest_idle.id)

    async def _start_worker_process(self, worker_info: WorkerInfo):
        """Start worker process (simulated implementation)"""
        # In a real implementation, this would start a Celery worker process
        # For now, we simulate it
        worker_info.pid = 12345  # Fake PID
        worker_info.last_heartbeat = datetime.now()
        logger.info(f"Started worker process for {worker_info.id}")

    async def _stop_worker_process(self, worker_info: WorkerInfo):
        """Stop worker process (simulated implementation)"""
        # In a real implementation, this would terminate the Celery worker
        logger.info(f"Stopped worker process for {worker_info.id}")

    async def _register_worker_with_redis(self, worker_info: WorkerInfo):
        """Register worker in Redis for tracking"""
        worker_data = {
            "id": worker_info.id,
            "type": worker_info.type.value,
            "status": worker_info.status.value,
            "started_at": worker_info.started_at.isoformat(),
            "resources": worker_info.resources.dict(),
            "queues": worker_info.queues
        }
        
        await redis_client.set_with_expiry(
            f"worker:{worker_info.id}", 
            worker_data, 
            expiry_seconds=300
        )

    async def _unregister_worker_from_redis(self, worker_info: WorkerInfo):
        """Unregister worker from Redis"""
        await redis_client.delete(f"worker:{worker_info.id}")

    async def _get_queue_depth(self) -> int:
        """Get total depth across all queues"""
        # This would query Celery queues in a real implementation
        # For now, return a simulated value
        return len(self.get_busy_workers()) * 2

    async def _wait_for_task_completion(self, task_id: str, timeout: int = 60):
        """Wait for a task to complete"""
        # This would monitor task status in a real implementation
        await asyncio.sleep(1)  # Simulate brief wait

    def _get_queues_for_type(self, worker_type: WorkerType) -> List[str]:
        """Get queue names for worker type"""
        queue_mapping = {
            WorkerType.GENERAL: ["default"],
            WorkerType.GPU: ["gpu", "generation"],
            WorkerType.CPU: ["cpu", "processing"],
            WorkerType.IO: ["io", "file_operations"]
        }
        return queue_mapping.get(worker_type, ["default"])

    def _determine_worker_type_for_queue(self) -> WorkerType:
        """Determine what type of worker to spawn based on queue contents"""
        # Simple heuristic - in reality would analyze queue contents
        return WorkerType.GENERAL

    async def _stop_all_workers(self):
        """Stop all workers gracefully"""
        tasks = []
        for worker_id in list(self.workers.keys()):
            tasks.append(self.terminate_worker(worker_id, graceful=True))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


class ResourceMonitor:
    """Monitor and allocate system resources"""

    def __init__(self):
        self.total_resources = self._detect_system_resources()
        self.allocated_resources = ResourceAllocation(cpu_cores=0, memory_gb=0, gpu_memory_gb=0)

    def _detect_system_resources(self) -> SystemResources:
        """Detect available CPU, memory, and GPU resources"""
        cpu_cores = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # GPU detection would be more complex in reality
        gpu_count = 0
        gpu_memory_gb = 0.0
        
        return SystemResources(
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            gpu_count=gpu_count,
            gpu_memory_gb=gpu_memory_gb
        )

    async def can_spawn_worker(self, worker_type: WorkerType) -> bool:
        """Check if resources available for worker type"""
        required = self._get_requirements(worker_type)
        available = await self._get_available_resources()
        
        return (
            available.cpu_cores >= required.cpu_cores and
            available.memory_gb >= required.memory_gb and
            (required.gpu_memory_gb == 0 or available.gpu_memory_gb >= required.gpu_memory_gb)
        )

    async def allocate_resources(self, worker_type: WorkerType) -> ResourceAllocation:
        """Allocate resources for worker type"""
        allocation = self._get_requirements(worker_type)
        
        # Update allocated tracking
        self.allocated_resources.cpu_cores += allocation.cpu_cores
        self.allocated_resources.memory_gb += allocation.memory_gb
        if allocation.gpu_memory_gb:
            self.allocated_resources.gpu_memory_gb += allocation.gpu_memory_gb
        
        return allocation

    async def deallocate_resources(self, allocation: ResourceAllocation):
        """Deallocate resources"""
        self.allocated_resources.cpu_cores -= allocation.cpu_cores
        self.allocated_resources.memory_gb -= allocation.memory_gb
        if allocation.gpu_memory_gb:
            self.allocated_resources.gpu_memory_gb -= allocation.gpu_memory_gb

    async def get_total_resources(self) -> ResourceAllocation:
        """Get total system resources"""
        return ResourceAllocation(
            cpu_cores=self.total_resources.cpu_cores,
            memory_gb=self.total_resources.memory_gb,
            gpu_memory_gb=self.total_resources.gpu_memory_gb
        )

    async def get_allocated_resources(self) -> ResourceAllocation:
        """Get currently allocated resources"""
        return self.allocated_resources

    async def _get_available_resources(self) -> ResourceAllocation:
        """Get available resources"""
        return ResourceAllocation(
            cpu_cores=self.total_resources.cpu_cores - self.allocated_resources.cpu_cores,
            memory_gb=self.total_resources.memory_gb - self.allocated_resources.memory_gb,
            gpu_memory_gb=self.total_resources.gpu_memory_gb - self.allocated_resources.gpu_memory_gb
        )

    def _get_requirements(self, worker_type: WorkerType) -> ResourceAllocation:
        """Get resource requirements for worker type"""
        requirements = {
            WorkerType.GENERAL: ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
            WorkerType.GPU: ResourceAllocation(cpu_cores=2.0, memory_gb=4.0, gpu_memory_gb=8.0),
            WorkerType.CPU: ResourceAllocation(cpu_cores=2.0, memory_gb=3.0),
            WorkerType.IO: ResourceAllocation(cpu_cores=0.5, memory_gb=1.0)
        }
        return requirements.get(worker_type, requirements[WorkerType.GENERAL])


class HealthChecker:
    """Monitor worker health and performance"""

    def __init__(self, pool_manager: WorkerPoolManager):
        self.pool_manager = pool_manager

    async def check_all_workers(self):
        """Check health of all workers"""
        for worker_id, worker_info in self.pool_manager.workers.items():
            try:
                await self.check_worker_health(worker_id)
            except Exception as e:
                logger.error(f"Health check failed for worker {worker_id}: {e}")

    async def check_worker_health(self, worker_id: str) -> bool:
        """Check health of specific worker"""
        worker = self.pool_manager.workers.get(worker_id)
        if not worker:
            return False

        # Check heartbeat
        if worker.last_heartbeat:
            heartbeat_age = (datetime.now() - worker.last_heartbeat).total_seconds()
            if heartbeat_age > 120:  # 2 minutes
                logger.warning(f"Worker {worker_id} heartbeat is stale ({heartbeat_age}s)")
                await self._handle_unhealthy_worker(worker_id, "stale_heartbeat")
                return False

        # Check task completion rate
        if worker.tasks_completed + worker.tasks_failed > 10:
            error_rate = worker.tasks_failed / (worker.tasks_completed + worker.tasks_failed)
            if error_rate > 0.5:  # 50% error rate
                logger.warning(f"Worker {worker_id} has high error rate: {error_rate:.2%}")
                await self._handle_unhealthy_worker(worker_id, "high_error_rate")
                return False

        # Update heartbeat
        worker.last_heartbeat = datetime.now()
        return True

    async def _handle_unhealthy_worker(self, worker_id: str, reason: str):
        """Handle an unhealthy worker"""
        logger.info(f"Handling unhealthy worker {worker_id} (reason: {reason})")
        
        # Mark as failed
        worker = self.pool_manager.workers.get(worker_id)
        if worker:
            worker.status = WorkerStatus.FAILED
        
        # Restart worker
        await self.pool_manager.terminate_worker(worker_id, graceful=False)
        
        # Spawn replacement if needed
        if len(self.pool_manager.workers) < self.pool_manager.min_workers:
            await self.pool_manager.spawn_worker(WorkerType.GENERAL)


# Global worker pool manager instance
worker_pool_manager = WorkerPoolManager(
    min_workers=getattr(settings, 'MIN_WORKERS', 1),
    max_workers=getattr(settings, 'MAX_WORKERS', 10),
    scale_up_threshold=getattr(settings, 'SCALE_UP_THRESHOLD', 5),
    scale_down_threshold=getattr(settings, 'SCALE_DOWN_THRESHOLD', 0),
    idle_timeout=getattr(settings, 'WORKER_IDLE_TIMEOUT', 300)
)