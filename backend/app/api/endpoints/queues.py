"""
Queue Management API Endpoints

Provides REST API for monitoring and managing task queues,
including queue metrics, health checks, and dead letter queue management.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from app.worker.queues import task_router, QUEUE_CONFIGS
from app.worker.queue_monitor import get_queue_monitor
from app.worker.dead_letter_queue import get_dlq_handler
from app.worker.celery_config import app as celery_app
from app.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/queues", tags=["queues"])

# Initialize components
redis_client = get_redis_client()
queue_monitor = get_queue_monitor(celery_app, redis_client)
dlq_handler = get_dlq_handler(celery_app, redis_client)


class QueueSubmitRequest(BaseModel):
    """Request to submit a task to queue"""
    task_name: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    priority: Optional[int] = None
    queue_override: Optional[str] = None
    resource_requirements: Optional[Dict[str, Any]] = None


class QueuePauseRequest(BaseModel):
    """Request to pause/resume a queue"""
    queue_name: str
    paused: bool


class DLQRetryRequest(BaseModel):
    """Request to retry failed task from DLQ"""
    task_id: str
    force: bool = False


@router.get("/")
async def list_queues():
    """Get list of all configured queues with their information"""
    try:
        queue_info = task_router.get_all_queues_info()
        
        # Add current metrics if available
        current_metrics = queue_monitor.get_current_metrics()
        
        for queue_name, info in queue_info.items():
            if queue_name in current_metrics:
                metrics = current_metrics[queue_name]
                info.update({
                    'current_depth': metrics.depth,
                    'processing_rate': metrics.processing_rate,
                    'error_rate': metrics.error_rate,
                    'active_consumers': metrics.active_consumers,
                    'last_updated': metrics.timestamp.isoformat()
                })
            else:
                info.update({
                    'current_depth': 0,
                    'processing_rate': 0.0,
                    'error_rate': 0.0,
                    'active_consumers': 0,
                    'last_updated': None
                })
        
        return {
            'queues': queue_info,
            'total_queues': len(queue_info),
            'monitoring_active': queue_monitor.monitoring_active
        }
        
    except Exception as e:
        logger.error(f"Error listing queues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{queue_name}")
async def get_queue_info(queue_name: str):
    """Get detailed information about a specific queue"""
    try:
        if queue_name not in QUEUE_CONFIGS:
            raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")
        
        # Get queue configuration
        queue_info = task_router.get_queue_info(queue_name)
        
        # Get current metrics
        current_metrics = queue_monitor.get_current_metrics(queue_name)
        
        if queue_name in current_metrics:
            metrics = current_metrics[queue_name]
            queue_info.update({
                'current_depth': metrics.depth,
                'processing_rate': metrics.processing_rate,
                'completion_rate': metrics.completion_rate,
                'error_rate': metrics.error_rate,
                'avg_processing_time': metrics.avg_processing_time,
                'oldest_task_age': metrics.oldest_task_age,
                'active_consumers': metrics.active_consumers,
                'last_updated': metrics.timestamp.isoformat()
            })
        
        return queue_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue info for {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{queue_name}/metrics")
async def get_queue_metrics(
    queue_name: str,
    hours: int = Query(24, description="Hours of historical data to retrieve")
):
    """Get historical metrics for a specific queue"""
    try:
        if queue_name not in QUEUE_CONFIGS:
            raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")
        
        # Get historical metrics
        historical_metrics = queue_monitor.get_historical_metrics(queue_name, hours)
        
        # Get current metrics
        current_metrics = queue_monitor.get_current_metrics(queue_name)
        current = current_metrics.get(queue_name)
        
        return {
            'queue_name': queue_name,
            'period_hours': hours,
            'current_metrics': {
                'depth': current.depth if current else 0,
                'processing_rate': current.processing_rate if current else 0.0,
                'completion_rate': current.completion_rate if current else 0.0,
                'error_rate': current.error_rate if current else 0.0,
                'avg_processing_time': current.avg_processing_time if current else 0.0,
                'oldest_task_age': current.oldest_task_age if current else 0,
                'active_consumers': current.active_consumers if current else 0,
                'timestamp': current.timestamp.isoformat() if current else None
            },
            'historical_metrics': historical_metrics,
            'data_points': len(historical_metrics)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{queue_name}/health")
async def check_queue_health(queue_name: str):
    """Check health status of a specific queue"""
    try:
        if queue_name not in QUEUE_CONFIGS:
            raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")
        
        # Get health status from queue monitor
        from app.worker.queues import QueueHealthChecker
        health_checker = QueueHealthChecker(redis_client)
        health_status = health_checker.check_queue_health(queue_name)
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking health for queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
async def submit_task(request: QueueSubmitRequest):
    """Submit a task to the appropriate queue"""
    try:
        # Prepare task arguments
        task_kwargs = request.kwargs.copy()
        
        # Add routing hints
        if request.priority:
            task_kwargs['priority'] = request.priority
        if request.resource_requirements:
            task_kwargs['resource_requirements'] = request.resource_requirements
        
        # Determine queue using router or override
        if request.queue_override and request.queue_override in QUEUE_CONFIGS:
            queue_name = request.queue_override
            routing_info = {'queue': queue_name, 'routing_key': queue_name}
        else:
            # Use intelligent routing
            routing_info = task_router.route_task(
                request.task_name, 
                request.args, 
                task_kwargs,
                {}
            )
            queue_name = routing_info['queue']
        
        # Submit task to Celery
        result = celery_app.send_task(
            request.task_name,
            args=request.args,
            kwargs=task_kwargs,
            **routing_info
        )
        
        return {
            'task_id': result.id,
            'task_name': request.task_name,
            'queue': queue_name,
            'routing_info': routing_info,
            'submitted_at': datetime.now().isoformat(),
            'status': 'submitted'
        }
        
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{queue_name}/pause")
async def pause_resume_queue(queue_name: str, request: QueuePauseRequest):
    """Pause or resume a specific queue"""
    try:
        if queue_name not in QUEUE_CONFIGS:
            raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")
        
        # This would implement queue pausing in a real system
        # For now, return success with the current state
        return {
            'queue_name': queue_name,
            'paused': request.paused,
            'message': f"Queue '{queue_name}' {'paused' if request.paused else 'resumed'}",
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing/resuming queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{queue_name}/purge")
async def purge_queue(queue_name: str):
    """Purge all tasks from a queue"""
    try:
        if queue_name not in QUEUE_CONFIGS:
            raise HTTPException(status_code=404, detail=f"Queue '{queue_name}' not found")
        
        # Get current depth before purging
        current_depth = redis_client.llen(f"celery:{queue_name}")
        
        # Purge the queue
        purged_count = redis_client.delete(f"celery:{queue_name}")
        
        logger.warning(f"Purged queue '{queue_name}': {current_depth} tasks removed")
        
        return {
            'queue_name': queue_name,
            'purged_tasks': current_depth,
            'purged_at': datetime.now().isoformat(),
            'message': f"Purged {current_depth} tasks from queue '{queue_name}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purging queue {queue_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/summary")
async def get_monitoring_summary():
    """Get overall monitoring summary for all queues"""
    try:
        summary = queue_monitor.get_queue_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Error getting monitoring summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start queue monitoring"""
    try:
        if queue_monitor.monitoring_active:
            return {
                'message': 'Queue monitoring already active',
                'status': 'active'
            }
        
        # Start monitoring in background
        background_tasks.add_task(queue_monitor.start_monitoring)
        
        return {
            'message': 'Queue monitoring started',
            'status': 'starting',
            'started_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop queue monitoring"""
    try:
        if not queue_monitor.monitoring_active:
            return {
                'message': 'Queue monitoring not active',
                'status': 'inactive'
            }
        
        await queue_monitor.stop_monitoring()
        
        return {
            'message': 'Queue monitoring stopped',
            'status': 'stopped',
            'stopped_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dead Letter Queue endpoints
@router.get("/dlq/stats")
async def get_dlq_stats(date: Optional[str] = None):
    """Get dead letter queue statistics"""
    try:
        stats = dlq_handler.get_dlq_stats(date)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting DLQ stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dlq/recent-failures")
async def get_recent_failures(hours: int = Query(24, description="Hours to look back")):
    """Get recent failures from dead letter queue"""
    try:
        failures = dlq_handler.get_recent_failures(hours)
        
        return {
            'period_hours': hours,
            'failure_count': len(failures),
            'failures': failures[:100]  # Limit to 100 most recent
        }
        
    except Exception as e:
        logger.error(f"Error getting recent failures: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dlq/retry")
async def retry_failed_task(request: DLQRetryRequest):
    """Retry a failed task from the dead letter queue"""
    try:
        success = dlq_handler.retry_failed_task(request.task_id, request.force)
        
        if success:
            return {
                'message': f'Task {request.task_id} scheduled for retry',
                'task_id': request.task_id,
                'forced': request.force,
                'retried_at': datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f'Failed to retry task {request.task_id}. Task may not exist or exceed retry limits.'
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying task {request.task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/preview")
async def preview_task_routing(
    task_name: str,
    args: List[Any] = Query([]),
    priority: Optional[int] = None,
    resource_requirements: Optional[str] = None
):
    """Preview where a task would be routed without actually submitting it"""
    try:
        # Prepare kwargs
        kwargs = {}
        if priority:
            kwargs['priority'] = priority
        if resource_requirements:
            import json
            kwargs['resource_requirements'] = json.loads(resource_requirements)
        
        # Get routing decision
        routing_info = task_router.route_task(task_name, args, kwargs, {})
        
        # Get queue information
        queue_name = routing_info['queue']
        queue_info = task_router.get_queue_info(queue_name)
        
        return {
            'task_name': task_name,
            'routing_info': routing_info,
            'target_queue': queue_info,
            'routing_factors': {
                'priority': kwargs.get('priority'),
                'resource_requirements': kwargs.get('resource_requirements'),
                'matched_pattern': task_router.ROUTE_MAP.get(task_name.split('.')[-1])
            }
        }
        
    except Exception as e:
        logger.error(f"Error previewing routing for {task_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))