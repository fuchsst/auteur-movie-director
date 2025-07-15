"""
Health Monitoring API Endpoints

Provides REST API for worker health monitoring, metrics collection,
and health dashboard functionality.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel

from app.worker.health_monitor import worker_health_monitor, HealthStatus
from app.worker.metrics_collector import metrics_collector
from app.worker.pool_manager import worker_pool_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health-monitoring"])


class WorkerHealthInfo(BaseModel):
    """Worker health information"""
    worker_id: str
    status: str
    health_score: float
    last_check: str
    issues: List[str]
    metrics: Dict[str, Any]


class WorkerHealthSummary(BaseModel):
    """Summary of all worker health"""
    total_workers: int
    healthy_workers: int
    warning_workers: int
    critical_workers: int
    unknown_workers: int
    average_health_score: float
    workers: List[WorkerHealthInfo]
    timestamp: str


class HealthCheckDetails(BaseModel):
    """Detailed health check results"""
    check_name: str
    status: str
    message: str
    metrics: Dict[str, Any]
    timestamp: str


class WorkerHealthDetails(BaseModel):
    """Detailed health information for a worker"""
    worker_id: str
    health_score: float
    overall_status: str
    checks: List[HealthCheckDetails]
    last_update: str
    uptime_seconds: Optional[int] = None
    restart_count: int = 0


class HealthAlert(BaseModel):
    """Health alert information"""
    worker_id: str
    severity: str
    check_name: str
    message: str
    timestamp: str
    acknowledged: bool = False


class RestartRequest(BaseModel):
    """Worker restart request"""
    reason: str = "manual_restart"
    force: bool = False


@router.get("/workers")
async def get_worker_health_summary() -> WorkerHealthSummary:
    """Get health summary for all workers"""
    try:
        # Get all worker health data
        all_health = worker_health_monitor.get_all_workers_health()
        
        # Get worker information
        workers = await worker_pool_manager.get_all_workers()
        worker_map = {w.id: w for w in workers}
        
        # Process health data
        summaries = []
        total_score = 0.0
        status_counts = {
            'healthy': 0,
            'warning': 0,
            'critical': 0,
            'unknown': 0
        }
        
        for worker_id, health_data in all_health.items():
            # Determine overall status
            health_score = health_data.get('health_score', 0.0)
            total_score += health_score
            
            if health_score >= 0.8:
                overall_status = 'healthy'
                status_counts['healthy'] += 1
            elif health_score >= 0.6:
                overall_status = 'warning'
                status_counts['warning'] += 1
            elif health_score > 0:
                overall_status = 'critical'
                status_counts['critical'] += 1
            else:
                overall_status = 'unknown'
                status_counts['unknown'] += 1
            
            # Extract issues
            issues = []
            if 'checks' in health_data:
                for check in health_data['checks']:
                    if check['status'] in ['warning', 'critical', 'error']:
                        issues.append(f"{check['check_name']}: {check['message']}")
            
            # Get metrics summary
            metrics_summary = {}
            if 'checks' in health_data:
                for check in health_data['checks']:
                    if check['check_name'] == 'resources':
                        metrics_summary.update({
                            'cpu_percent': check['metrics'].get('cpu_percent', 0),
                            'memory_percent': check['metrics'].get('memory_percent', 0),
                            'gpu_memory_percent': check['metrics'].get('gpu_memory_percent')
                        })
                    elif check['check_name'] == 'task_performance':
                        metrics_summary.update({
                            'tasks_per_minute': check['metrics'].get('tasks_per_minute', 0),
                            'error_rate': check['metrics'].get('error_rate', 0)
                        })
            
            summaries.append(WorkerHealthInfo(
                worker_id=worker_id,
                status=overall_status,
                health_score=round(health_score, 3),
                last_check=health_data.get('timestamp', 'unknown'),
                issues=issues,
                metrics=metrics_summary
            ))
        
        # Add workers with no health data
        for worker in workers:
            if worker.id not in all_health:
                status_counts['unknown'] += 1
                summaries.append(WorkerHealthInfo(
                    worker_id=worker.id,
                    status='unknown',
                    health_score=0.0,
                    last_check='never',
                    issues=['No health data available'],
                    metrics={}
                ))
        
        avg_score = total_score / len(all_health) if all_health else 0.0
        
        return WorkerHealthSummary(
            total_workers=len(summaries),
            healthy_workers=status_counts['healthy'],
            warning_workers=status_counts['warning'],
            critical_workers=status_counts['critical'],
            unknown_workers=status_counts['unknown'],
            average_health_score=round(avg_score, 3),
            workers=summaries,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting worker health summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/{worker_id}")
async def get_worker_health_details(worker_id: str) -> WorkerHealthDetails:
    """Get detailed health information for a specific worker"""
    try:
        # Get health data
        health_data = worker_health_monitor.get_worker_health(worker_id)
        
        if not health_data:
            raise HTTPException(status_code=404, detail=f"No health data for worker {worker_id}")
        
        # Get worker info for uptime
        try:
            worker = await worker_pool_manager.get_worker(worker_id)
            if worker and worker.started_at:
                uptime_seconds = int((datetime.now() - worker.started_at).total_seconds())
            else:
                uptime_seconds = None
        except Exception:
            uptime_seconds = None
        
        # Determine overall status
        health_score = health_data.get('health_score', 0.0)
        if health_score >= 0.8:
            overall_status = 'healthy'
        elif health_score >= 0.6:
            overall_status = 'warning'
        elif health_score > 0:
            overall_status = 'critical'
        else:
            overall_status = 'unknown'
        
        # Convert checks
        checks = []
        if 'checks' in health_data:
            for check in health_data['checks']:
                checks.append(HealthCheckDetails(
                    check_name=check['check_name'],
                    status=check['status'],
                    message=check['message'],
                    metrics=check['metrics'],
                    timestamp=check.get('timestamp', health_data.get('timestamp', 'unknown'))
                ))
        
        return WorkerHealthDetails(
            worker_id=worker_id,
            health_score=round(health_score, 3),
            overall_status=overall_status,
            checks=checks,
            last_update=health_data.get('timestamp', 'unknown'),
            uptime_seconds=uptime_seconds,
            restart_count=0  # TODO: Track restart count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting worker health details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers/{worker_id}/history")
async def get_worker_health_history(
    worker_id: str,
    hours: int = Query(24, description="Hours of history to retrieve", ge=1, le=168)
):
    """Get historical health data for a worker"""
    try:
        history = await worker_health_monitor.get_health_history(worker_id, hours)
        
        if not history:
            return {
                'worker_id': worker_id,
                'period_hours': hours,
                'data_points': 0,
                'history': []
            }
        
        # Process history for response
        processed_history = []
        for entry in history:
            processed_history.append({
                'timestamp': entry.get('timestamp'),
                'health_score': entry.get('health_score', 0.0),
                'status': 'healthy' if entry.get('health_score', 0) >= 0.8 else 'warning',
                'check_summary': {
                    check['check_name']: check['status']
                    for check in entry.get('checks', [])
                }
            })
        
        return {
            'worker_id': worker_id,
            'period_hours': hours,
            'data_points': len(processed_history),
            'history': processed_history
        }
        
    except Exception as e:
        logger.error(f"Error getting worker health history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workers/{worker_id}/restart")
async def restart_worker(worker_id: str, request: RestartRequest):
    """Manually restart a worker"""
    try:
        # Check if worker exists
        worker = await worker_pool_manager.get_worker(worker_id)
        if not worker:
            raise HTTPException(status_code=404, detail=f"Worker {worker_id} not found")
        
        # Record restart in metrics
        metrics_collector.record_worker_restart(worker_id, request.reason)
        
        # Restart worker
        success = await worker_pool_manager.restart_worker(
            worker_id,
            force=request.force
        )
        
        if success:
            return {
                'message': f'Worker {worker_id} restart initiated',
                'worker_id': worker_id,
                'reason': request.reason,
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to restart worker {worker_id}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting worker {worker_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_health_alerts(
    hours: int = Query(24, description="Hours of alerts to retrieve", ge=1, le=168),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    worker_id: Optional[str] = Query(None, description="Filter by worker ID")
):
    """Get recent health alerts"""
    try:
        from app.redis_client import get_redis_client
        redis = get_redis_client()
        
        # Get alerts from Redis
        alerts_data = redis.lrange("health_alerts", 0, -1)
        
        alerts = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for alert_json in alerts_data:
            try:
                import json
                alert_data = json.loads(alert_json)
                
                # Parse timestamp
                alert_time = datetime.fromisoformat(alert_data['timestamp'])
                if alert_time < cutoff_time:
                    continue
                
                # Apply filters
                if severity and alert_data.get('severity') != severity:
                    continue
                if worker_id and alert_data.get('worker_id') != worker_id:
                    continue
                
                # Extract alert info
                for issue in alert_data.get('issues', []):
                    alerts.append(HealthAlert(
                        worker_id=alert_data['worker_id'],
                        severity=issue['status'],
                        check_name=issue['check'],
                        message=issue['message'],
                        timestamp=alert_data['timestamp'],
                        acknowledged=False
                    ))
                    
            except Exception as e:
                logger.warning(f"Error parsing alert: {e}")
                continue
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return {
            'period_hours': hours,
            'total_alerts': len(alerts),
            'filters': {
                'severity': severity,
                'worker_id': worker_id
            },
            'alerts': alerts[:100]  # Limit to 100 most recent
        }
        
    except Exception as e:
        logger.error(f"Error getting health alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_prometheus_metrics():
    """Get metrics in Prometheus format"""
    try:
        metrics_data = metrics_collector.generate_metrics()
        return Response(
            content=metrics_data,
            media_type=metrics_collector.get_content_type()
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start")
async def start_health_monitoring(background_tasks: BackgroundTasks):
    """Start health monitoring for all workers"""
    try:
        # Check if already monitoring
        if worker_health_monitor.monitoring_tasks:
            return {
                'message': 'Health monitoring already active',
                'monitored_workers': list(worker_health_monitor.monitoring_tasks.keys())
            }
        
        # Start monitoring in background
        background_tasks.add_task(worker_health_monitor.start_monitoring)
        
        return {
            'message': 'Health monitoring started',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting health monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
async def stop_health_monitoring():
    """Stop health monitoring"""
    try:
        monitored_workers = list(worker_health_monitor.monitoring_tasks.keys())
        
        await worker_health_monitor.stop_monitoring()
        
        return {
            'message': 'Health monitoring stopped',
            'previously_monitored': monitored_workers,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping health monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/status")
async def get_monitoring_status():
    """Get current monitoring status"""
    try:
        return {
            'monitoring_active': bool(worker_health_monitor.monitoring_tasks),
            'monitored_workers': list(worker_health_monitor.monitoring_tasks.keys()),
            'check_interval': worker_health_monitor.check_interval,
            'health_checks': [check.name for check in worker_health_monitor.health_checks],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checks/{worker_id}")
async def run_health_check(worker_id: str, check_name: Optional[str] = None):
    """Run health check(s) for a specific worker on demand"""
    try:
        if check_name:
            # Run specific check
            check = next(
                (c for c in worker_health_monitor.health_checks if c.name == check_name),
                None
            )
            if not check:
                raise HTTPException(status_code=404, detail=f"Check '{check_name}' not found")
            
            result = await check.execute(worker_id)
            return {
                'worker_id': worker_id,
                'check_result': result.to_dict()
            }
        else:
            # Run all checks
            results = await worker_health_monitor.run_health_checks(worker_id)
            health_score = worker_health_monitor.calculate_health_score(results)
            
            return {
                'worker_id': worker_id,
                'health_score': round(health_score, 3),
                'check_results': [r.to_dict() for r in results],
                'timestamp': datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))