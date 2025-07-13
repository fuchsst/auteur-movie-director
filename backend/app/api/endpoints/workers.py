"""
Worker Pool Management API Endpoints

Provides REST API for monitoring and managing the worker pool,
including scaling operations and health monitoring.
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel

from app.worker.pool_manager import (
    worker_pool_manager,
    WorkerType,
    WorkerStatus,
    WorkerInfo
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workers", tags=["workers"])


class WorkerScaleRequest(BaseModel):
    """Request to manually scale workers"""
    worker_type: WorkerType = WorkerType.GENERAL
    action: str  # "scale_up" or "scale_down"
    count: int = 1


class WorkerTerminateRequest(BaseModel):
    """Request to terminate specific worker"""
    worker_id: str
    graceful: bool = True


class WorkerMetricsResponse(BaseModel):
    """Worker pool metrics response"""
    total_workers: int
    active_workers: int
    idle_workers: int
    busy_workers: int
    worker_types: Dict[str, int]
    resource_utilization: Dict[str, float]
    queue_depth: int
    scaling_limits: Dict[str, int]


@router.get("/", response_model=List[Dict[str, Any]])
async def list_workers():
    """Get list of all workers with their status"""
    try:
        workers = []
        for worker_id, worker_info in worker_pool_manager.workers.items():
            workers.append({
                "id": worker_info.id,
                "type": worker_info.type.value,
                "status": worker_info.status.value,
                "started_at": worker_info.started_at.isoformat(),
                "last_heartbeat": worker_info.last_heartbeat.isoformat() if worker_info.last_heartbeat else None,
                "tasks_completed": worker_info.tasks_completed,
                "tasks_failed": worker_info.tasks_failed,
                "current_task_id": worker_info.current_task_id,
                "resources": worker_info.resources.model_dump(),
                "queues": worker_info.queues,
                "idle_since": worker_info.idle_since.isoformat() if worker_info.idle_since else None
            })
        
        return workers
        
    except Exception as e:
        logger.error(f"Error listing workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=WorkerMetricsResponse)
async def get_worker_metrics():
    """Get comprehensive worker pool metrics"""
    try:
        metrics = await worker_pool_manager.get_worker_metrics()
        return WorkerMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Error getting worker metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{worker_id}")
async def get_worker_info(worker_id: str):
    """Get detailed information about a specific worker"""
    try:
        worker_info = worker_pool_manager.get_worker_info(worker_id)
        
        if not worker_info:
            raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")
        
        return {
            "id": worker_info.id,
            "type": worker_info.type.value,
            "status": worker_info.status.value,
            "pid": worker_info.pid,
            "started_at": worker_info.started_at.isoformat(),
            "last_heartbeat": worker_info.last_heartbeat.isoformat() if worker_info.last_heartbeat else None,
            "tasks_completed": worker_info.tasks_completed,
            "tasks_failed": worker_info.tasks_failed,
            "current_task_id": worker_info.current_task_id,
            "resources": worker_info.resources.model_dump(),
            "queues": worker_info.queues,
            "idle_since": worker_info.idle_since.isoformat() if worker_info.idle_since else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting worker info for {worker_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/spawn")
async def spawn_worker(worker_type: WorkerType = WorkerType.GENERAL):
    """Manually spawn a new worker"""
    try:
        worker_id = await worker_pool_manager.spawn_worker(worker_type)
        
        if not worker_id:
            raise HTTPException(
                status_code=400, 
                detail="Failed to spawn worker. Check resource availability and scaling limits."
            )
        
        return {
            "message": f"Successfully spawned {worker_type.value} worker",
            "worker_id": worker_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error spawning worker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scale")
async def scale_workers(request: WorkerScaleRequest):
    """Manually scale workers up or down"""
    try:
        if request.action == "scale_up":
            worker_ids = []
            for _ in range(request.count):
                worker_id = await worker_pool_manager.spawn_worker(request.worker_type)
                if worker_id:
                    worker_ids.append(worker_id)
            
            return {
                "action": "scale_up",
                "worker_type": request.worker_type.value,
                "requested_count": request.count,
                "spawned_count": len(worker_ids),
                "worker_ids": worker_ids
            }
            
        elif request.action == "scale_down":
            # Get workers of the requested type that can be terminated
            target_workers = [
                w for w in worker_pool_manager.workers.values()
                if w.type == request.worker_type and w.status in [WorkerStatus.IDLE, WorkerStatus.ACTIVE]
            ]
            
            # Sort by idle time (terminate longest idle first)
            target_workers.sort(key=lambda w: w.idle_since or w.started_at)
            
            terminated_count = 0
            terminated_ids = []
            
            for worker in target_workers[:request.count]:
                if len(worker_pool_manager.workers) > worker_pool_manager.min_workers:
                    success = await worker_pool_manager.terminate_worker(worker.id)
                    if success:
                        terminated_count += 1
                        terminated_ids.append(worker.id)
            
            return {
                "action": "scale_down",
                "worker_type": request.worker_type.value,
                "requested_count": request.count,
                "terminated_count": terminated_count,
                "terminated_worker_ids": terminated_ids
            }
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'scale_up' or 'scale_down'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scaling workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{worker_id}")
async def terminate_worker(worker_id: str, graceful: bool = True):
    """Terminate a specific worker"""
    try:
        # Check if worker exists
        worker_info = worker_pool_manager.get_worker_info(worker_id)
        if not worker_info:
            raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")
        
        # Check minimum worker constraint
        if len(worker_pool_manager.workers) <= worker_pool_manager.min_workers:
            raise HTTPException(
                status_code=400, 
                detail="Cannot terminate worker: minimum worker count would be violated"
            )
        
        success = await worker_pool_manager.terminate_worker(worker_id, graceful)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to terminate worker {worker_id}")
        
        return {
            "message": f"Successfully terminated worker {worker_id}",
            "graceful": graceful
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error terminating worker {worker_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{worker_id}/health-check")
async def check_worker_health(worker_id: str):
    """Trigger health check for specific worker"""
    try:
        worker_info = worker_pool_manager.get_worker_info(worker_id)
        if not worker_info:
            raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")
        
        health_status = await worker_pool_manager.health_checker.check_worker_health(worker_id)
        
        return {
            "worker_id": worker_id,
            "healthy": health_status,
            "checked_at": worker_info.last_heartbeat.isoformat() if worker_info.last_heartbeat else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking health for worker {worker_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queues/status")
async def get_queue_status():
    """Get status of all task queues"""
    try:
        # This would query Celery queues in a real implementation
        # For now, return simulated queue status
        queue_status = {
            "default": {"length": 0, "consumers": 1},
            "gpu": {"length": 2, "consumers": 1},
            "cpu": {"length": 1, "consumers": 2},
            "io": {"length": 0, "consumers": 1}
        }
        
        return {
            "queues": queue_status,
            "total_queued_tasks": sum(q["length"] for q in queue_status.values()),
            "total_consumers": sum(q["consumers"] for q in queue_status.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pool/start")
async def start_worker_pool():
    """Start the worker pool manager"""
    try:
        await worker_pool_manager.start()
        return {"message": "Worker pool started successfully"}
        
    except Exception as e:
        logger.error(f"Error starting worker pool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pool/stop")
async def stop_worker_pool():
    """Stop the worker pool manager"""
    try:
        await worker_pool_manager.stop()
        return {"message": "Worker pool stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping worker pool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_worker_types():
    """Get available worker types and their configurations"""
    try:
        worker_types = {}
        
        for worker_type in WorkerType:
            # Get resource requirements for each type
            requirements = worker_pool_manager.resource_monitor._get_requirements(worker_type)
            queues = worker_pool_manager._get_queues_for_type(worker_type)
            
            worker_types[worker_type.value] = {
                "type": worker_type.value,
                "resource_requirements": requirements.model_dump(),
                "queues": queues,
                "description": _get_worker_type_description(worker_type)
            }
        
        return worker_types
        
    except Exception as e:
        logger.error(f"Error getting worker types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_worker_type_description(worker_type: WorkerType) -> str:
    """Get description for worker type"""
    descriptions = {
        WorkerType.GENERAL: "General purpose workers for basic tasks",
        WorkerType.GPU: "GPU-accelerated workers for AI generation tasks",
        WorkerType.CPU: "CPU-intensive workers for processing tasks",
        WorkerType.IO: "I/O optimized workers for file operations"
    }
    return descriptions.get(worker_type, "Unknown worker type")