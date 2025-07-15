"""
Worker Health Monitoring System

Comprehensive health monitoring for function runner workers with real-time metrics,
alerting, and automatic recovery mechanisms.
"""

import asyncio
import logging
import psutil
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from app.redis_client import get_redis_client
from app.worker.pool_manager import worker_pool_manager

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    check_name: str
    status: HealthStatus
    message: str
    metrics: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'check_name': self.check_name,
            'status': self.status.value,
            'message': self.message,
            'metrics': self.metrics,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class WorkerMetrics:
    """Worker resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage_percent: float
    gpu_memory_percent: Optional[float] = None
    gpu_utilization: Optional[float] = None
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    open_files: int = 0
    threads: int = 0


@dataclass
class TaskStats:
    """Task execution statistics"""
    total: int = 0
    completed: int = 0
    failed: int = 0
    in_progress: int = 0
    total_duration: float = 0.0
    expected_duration: float = 30.0
    throughput: float = 0.0  # tasks per minute


class HealthCheck(ABC):
    """Abstract base class for health checks"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Health check name"""
        pass
    
    @abstractmethod
    async def execute(self, worker_id: str) -> HealthCheckResult:
        """Execute the health check"""
        pass


class HeartbeatCheck(HealthCheck):
    """Verify worker is responsive"""
    
    @property
    def name(self) -> str:
        return "heartbeat"
    
    def __init__(self):
        self.redis = get_redis_client()
    
    async def execute(self, worker_id: str) -> HealthCheckResult:
        """Check worker heartbeat"""
        try:
            last_heartbeat = self.redis.get(f"worker:{worker_id}:heartbeat")
            
            if not last_heartbeat:
                return HealthCheckResult(
                    check_name=self.name,
                    status=HealthStatus.CRITICAL,
                    message="No heartbeat received",
                    metrics={"last_seen": None}
                )
            
            # Parse timestamp
            try:
                if isinstance(last_heartbeat, dict):
                    heartbeat_time = datetime.fromisoformat(last_heartbeat['timestamp'])
                else:
                    heartbeat_time = datetime.fromisoformat(last_heartbeat)
            except (ValueError, TypeError, KeyError):
                return HealthCheckResult(
                    check_name=self.name,
                    status=HealthStatus.ERROR,
                    message="Invalid heartbeat format",
                    metrics={"raw_value": str(last_heartbeat)}
                )
            
            time_since = datetime.now() - heartbeat_time
            seconds_since = time_since.total_seconds()
            
            if seconds_since > 60:
                status = HealthStatus.CRITICAL
                message = f"No heartbeat for {int(seconds_since)}s"
            elif seconds_since > 30:
                status = HealthStatus.WARNING
                message = f"Delayed heartbeat: {int(seconds_since)}s"
            else:
                status = HealthStatus.HEALTHY
                message = "Heartbeat normal"
            
            return HealthCheckResult(
                check_name=self.name,
                status=status,
                message=message,
                metrics={
                    "last_heartbeat_seconds": seconds_since,
                    "timestamp": heartbeat_time.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Heartbeat check failed: {e}")
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.ERROR,
                message=f"Check failed: {str(e)}",
                metrics={}
            )


class ResourceCheck(HealthCheck):
    """Monitor resource usage"""
    
    @property
    def name(self) -> str:
        return "resources"
    
    def __init__(self):
        self.redis = get_redis_client()
    
    async def get_worker_metrics(self, worker_id: str) -> WorkerMetrics:
        """Get current resource metrics for worker"""
        try:
            # Get process info from Redis (stored by worker)
            metrics_data = self.redis.get(f"worker:{worker_id}:metrics")
            
            if metrics_data:
                # Use reported metrics if available
                return WorkerMetrics(**metrics_data)
            
            # Fallback to local system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network stats
            net_io = psutil.net_io_counters()
            net_sent_mb = net_io.bytes_sent / (1024 * 1024)
            net_recv_mb = net_io.bytes_recv / (1024 * 1024)
            
            # GPU metrics (if available)
            gpu_memory_percent = None
            gpu_utilization = None
            
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                if device_count > 0:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_memory_percent = (mem_info.used / mem_info.total) * 100
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_utilization = util.gpu
            except Exception:
                pass  # GPU monitoring not available
            
            return WorkerMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_mb=memory.used / (1024 * 1024),
                disk_usage_percent=disk.percent,
                gpu_memory_percent=gpu_memory_percent,
                gpu_utilization=gpu_utilization,
                network_sent_mb=net_sent_mb,
                network_recv_mb=net_recv_mb,
                open_files=len(psutil.Process().open_files()),
                threads=psutil.Process().num_threads()
            )
            
        except Exception as e:
            logger.error(f"Failed to get worker metrics: {e}")
            # Return safe defaults
            return WorkerMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_mb=0.0,
                disk_usage_percent=0.0
            )
    
    async def execute(self, worker_id: str) -> HealthCheckResult:
        """Check resource usage"""
        try:
            metrics = await self.get_worker_metrics(worker_id)
            
            issues = []
            status = HealthStatus.HEALTHY
            
            # CPU check
            if metrics.cpu_percent > 95:
                issues.append("Critical CPU usage")
                status = HealthStatus.CRITICAL
            elif metrics.cpu_percent > 85:
                issues.append("High CPU usage")
                status = HealthStatus.WARNING
            
            # Memory check
            if metrics.memory_percent > 95:
                issues.append("Critical memory usage")
                status = HealthStatus.CRITICAL
            elif metrics.memory_percent > 85:
                issues.append("High memory usage")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
            
            # Disk check
            if metrics.disk_usage_percent > 95:
                issues.append("Critical disk usage")
                status = HealthStatus.CRITICAL
            elif metrics.disk_usage_percent > 90:
                issues.append("High disk usage")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
            
            # GPU check (if applicable)
            if metrics.gpu_memory_percent is not None:
                if metrics.gpu_memory_percent > 95:
                    issues.append("Critical GPU memory usage")
                    status = HealthStatus.CRITICAL
                elif metrics.gpu_memory_percent > 90:
                    issues.append("High GPU memory usage")
                    if status == HealthStatus.HEALTHY:
                        status = HealthStatus.WARNING
            
            return HealthCheckResult(
                check_name=self.name,
                status=status,
                message=", ".join(issues) if issues else "Resources normal",
                metrics={
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                    "memory_mb": metrics.memory_mb,
                    "disk_usage_percent": metrics.disk_usage_percent,
                    "gpu_memory_percent": metrics.gpu_memory_percent,
                    "gpu_utilization": metrics.gpu_utilization,
                    "network_sent_mb": metrics.network_sent_mb,
                    "network_recv_mb": metrics.network_recv_mb,
                    "open_files": metrics.open_files,
                    "threads": metrics.threads
                }
            )
            
        except Exception as e:
            logger.error(f"Resource check failed: {e}")
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.ERROR,
                message=f"Check failed: {str(e)}",
                metrics={}
            )


class TaskPerformanceCheck(HealthCheck):
    """Monitor task execution performance"""
    
    @property
    def name(self) -> str:
        return "task_performance"
    
    def __init__(self):
        self.redis = get_redis_client()
    
    async def get_task_stats(self, worker_id: str, window_minutes: int = 5) -> TaskStats:
        """Get task statistics for time window"""
        try:
            stats = TaskStats()
            
            # Get task history from Redis
            cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
            
            # Count completed tasks
            completed_key = f"worker:{worker_id}:completed_tasks"
            completed_tasks = self.redis.zrangebyscore(
                completed_key,
                cutoff_time.timestamp(),
                '+inf',
                withscores=True
            )
            
            stats.completed = len(completed_tasks)
            
            # Calculate total duration and throughput
            for task_data, timestamp in completed_tasks:
                try:
                    task_info = json.loads(task_data)
                    if 'duration' in task_info:
                        stats.total_duration += task_info['duration']
                except Exception:
                    pass
            
            # Count failed tasks
            failed_key = f"worker:{worker_id}:failed_tasks"
            failed_count = self.redis.zcount(failed_key, cutoff_time.timestamp(), '+inf')
            stats.failed = failed_count
            
            # Get in-progress tasks
            in_progress_key = f"worker:{worker_id}:in_progress"
            stats.in_progress = self.redis.scard(in_progress_key)
            
            # Calculate totals
            stats.total = stats.completed + stats.failed + stats.in_progress
            
            # Calculate throughput (tasks per minute)
            if window_minutes > 0:
                stats.throughput = stats.completed / window_minutes
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get task stats: {e}")
            return TaskStats()
    
    async def execute(self, worker_id: str) -> HealthCheckResult:
        """Check task performance"""
        try:
            stats = await self.get_task_stats(worker_id, window_minutes=5)
            
            # Calculate error rate
            error_rate = 0.0
            if stats.total > 0:
                error_rate = stats.failed / stats.total
            
            # Calculate average duration
            avg_duration = 0.0
            if stats.completed > 0:
                avg_duration = stats.total_duration / stats.completed
            
            # Determine health status
            if error_rate > 0.20:  # >20% error rate
                status = HealthStatus.CRITICAL
                message = f"Critical error rate: {error_rate:.1%}"
            elif error_rate > 0.10:  # >10% error rate
                status = HealthStatus.WARNING
                message = f"High error rate: {error_rate:.1%}"
            elif stats.total == 0:
                status = HealthStatus.WARNING
                message = "No recent tasks"
            elif avg_duration > stats.expected_duration * 3:
                status = HealthStatus.WARNING
                message = f"Very slow task execution: {avg_duration:.1f}s avg"
            elif avg_duration > stats.expected_duration * 2:
                status = HealthStatus.WARNING
                message = f"Slow task execution: {avg_duration:.1f}s avg"
            else:
                status = HealthStatus.HEALTHY
                message = f"Performance normal ({stats.completed} tasks)"
            
            return HealthCheckResult(
                check_name=self.name,
                status=status,
                message=message,
                metrics={
                    "total_tasks": stats.total,
                    "completed_tasks": stats.completed,
                    "failed_tasks": stats.failed,
                    "in_progress_tasks": stats.in_progress,
                    "error_rate": round(error_rate, 3),
                    "avg_duration_seconds": round(avg_duration, 2),
                    "tasks_per_minute": round(stats.throughput, 2)
                }
            )
            
        except Exception as e:
            logger.error(f"Task performance check failed: {e}")
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.ERROR,
                message=f"Check failed: {str(e)}",
                metrics={}
            )


class QueueConnectionCheck(HealthCheck):
    """Verify queue connectivity"""
    
    @property
    def name(self) -> str:
        return "queue_connection"
    
    def __init__(self):
        self.redis = get_redis_client()
    
    async def execute(self, worker_id: str) -> HealthCheckResult:
        """Check queue connection status"""
        try:
            # Check if worker is registered in active queues
            worker_info = self.redis.get(f"worker:{worker_id}:info")
            
            if not worker_info:
                return HealthCheckResult(
                    check_name=self.name,
                    status=HealthStatus.CRITICAL,
                    message="Worker not registered",
                    metrics={"registered": False}
                )
            
            # Check queue assignments
            assigned_queues = worker_info.get('queues', [])
            if not assigned_queues:
                return HealthCheckResult(
                    check_name=self.name,
                    status=HealthStatus.WARNING,
                    message="No queues assigned",
                    metrics={"queue_count": 0, "queues": []}
                )
            
            # Check queue depths
            total_tasks = 0
            queue_depths = {}
            
            for queue in assigned_queues:
                depth = self.redis.llen(f"celery:{queue}")
                queue_depths[queue] = depth
                total_tasks += depth
            
            # Determine status
            if total_tasks > 1000:
                status = HealthStatus.WARNING
                message = f"High queue backlog: {total_tasks} tasks"
            else:
                status = HealthStatus.HEALTHY
                message = f"Connected to {len(assigned_queues)} queues"
            
            return HealthCheckResult(
                check_name=self.name,
                status=status,
                message=message,
                metrics={
                    "registered": True,
                    "queue_count": len(assigned_queues),
                    "queues": assigned_queues,
                    "queue_depths": queue_depths,
                    "total_queued_tasks": total_tasks
                }
            )
            
        except Exception as e:
            logger.error(f"Queue connection check failed: {e}")
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.ERROR,
                message=f"Check failed: {str(e)}",
                metrics={}
            )


class ModelLoadingCheck(HealthCheck):
    """Check AI model loading status"""
    
    @property
    def name(self) -> str:
        return "model_loading"
    
    def __init__(self):
        self.redis = get_redis_client()
    
    async def execute(self, worker_id: str) -> HealthCheckResult:
        """Check model loading status"""
        try:
            # Get model status from worker
            model_status = self.redis.get(f"worker:{worker_id}:models")
            
            if not model_status:
                return HealthCheckResult(
                    check_name=self.name,
                    status=HealthStatus.WARNING,
                    message="No model status available",
                    metrics={"models_loaded": 0}
                )
            
            loaded_models = model_status.get('loaded', [])
            failed_models = model_status.get('failed', [])
            loading_time = model_status.get('total_loading_time', 0)
            
            # Determine status
            if failed_models:
                status = HealthStatus.CRITICAL
                message = f"{len(failed_models)} models failed to load"
            elif not loaded_models:
                status = HealthStatus.WARNING
                message = "No models loaded"
            elif loading_time > 300:  # 5 minutes
                status = HealthStatus.WARNING
                message = f"Slow model loading: {loading_time:.1f}s"
            else:
                status = HealthStatus.HEALTHY
                message = f"{len(loaded_models)} models loaded"
            
            return HealthCheckResult(
                check_name=self.name,
                status=status,
                message=message,
                metrics={
                    "models_loaded": len(loaded_models),
                    "models_failed": len(failed_models),
                    "loaded_models": loaded_models,
                    "failed_models": failed_models,
                    "total_loading_time": loading_time,
                    "last_update": model_status.get('timestamp', 'unknown')
                }
            )
            
        except Exception as e:
            logger.error(f"Model loading check failed: {e}")
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.ERROR,
                message=f"Check failed: {str(e)}",
                metrics={}
            )


class DiskSpaceCheck(HealthCheck):
    """Monitor disk space availability"""
    
    @property
    def name(self) -> str:
        return "disk_space"
    
    async def execute(self, worker_id: str) -> HealthCheckResult:
        """Check disk space"""
        try:
            # Check main disk
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024 ** 3)
            
            # Check temp directory
            import tempfile
            temp_disk = psutil.disk_usage(tempfile.gettempdir())
            temp_free_gb = temp_disk.free / (1024 ** 3)
            
            issues = []
            status = HealthStatus.HEALTHY
            
            # Main disk checks
            if free_gb < 1:
                issues.append("Critical: <1GB free on main disk")
                status = HealthStatus.CRITICAL
            elif free_gb < 5:
                issues.append("Warning: <5GB free on main disk")
                status = HealthStatus.WARNING
            
            # Temp disk checks
            if temp_free_gb < 0.5:
                issues.append("Critical: <500MB free in temp")
                status = HealthStatus.CRITICAL
            elif temp_free_gb < 2:
                issues.append("Warning: <2GB free in temp")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
            
            message = ", ".join(issues) if issues else f"Disk space normal ({free_gb:.1f}GB free)"
            
            return HealthCheckResult(
                check_name=self.name,
                status=status,
                message=message,
                metrics={
                    "main_disk_free_gb": round(free_gb, 2),
                    "main_disk_percent": disk.percent,
                    "temp_disk_free_gb": round(temp_free_gb, 2),
                    "temp_disk_percent": temp_disk.percent
                }
            )
            
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return HealthCheckResult(
                check_name=self.name,
                status=HealthStatus.ERROR,
                message=f"Check failed: {str(e)}",
                metrics={}
            )


class WorkerHealthMonitor:
    """Comprehensive health monitoring for function runners"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.redis = get_redis_client()
        self.health_checks = [
            HeartbeatCheck(),
            ResourceCheck(),
            TaskPerformanceCheck(),
            QueueConnectionCheck(),
            ModelLoadingCheck(),
            DiskSpaceCheck()
        ]
        self.monitoring_tasks = {}
        self.health_cache = {}
    
    async def start_monitoring(self):
        """Start monitoring all workers"""
        logger.info("Starting worker health monitoring")
        
        # Monitor existing workers
        workers = await worker_pool_manager.get_all_workers()
        for worker in workers:
            if worker.id not in self.monitoring_tasks:
                task = asyncio.create_task(self.monitor_worker(worker.id))
                self.monitoring_tasks[worker.id] = task
    
    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        logger.info("Stopping worker health monitoring")
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        # Wait for cancellation
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        
        self.monitoring_tasks.clear()
    
    async def monitor_worker(self, worker_id: str):
        """Continuous health monitoring for a worker"""
        logger.info(f"Starting health monitoring for worker {worker_id}")
        
        while True:
            try:
                # Run all health checks
                results = await self.run_health_checks(worker_id)
                
                # Calculate overall health score
                health_score = self.calculate_health_score(results)
                
                # Store results
                await self.store_health_data(worker_id, health_score, results)
                
                # Check for issues
                if health_score < 0.7:
                    await self.handle_unhealthy_worker(worker_id, results, health_score)
                
                # Update cache
                self.health_cache[worker_id] = {
                    'score': health_score,
                    'results': results,
                    'timestamp': datetime.now()
                }
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info(f"Health monitoring cancelled for worker {worker_id}")
                break
            except Exception as e:
                logger.error(f"Health monitoring error for worker {worker_id}: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def run_health_checks(self, worker_id: str) -> List[HealthCheckResult]:
        """Execute all health checks for a worker"""
        results = []
        
        for check in self.health_checks:
            try:
                result = await check.execute(worker_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Health check {check.name} failed for {worker_id}: {e}")
                results.append(HealthCheckResult(
                    check_name=check.name,
                    status=HealthStatus.ERROR,
                    message=f"Check failed: {str(e)}",
                    metrics={}
                ))
        
        return results
    
    def calculate_health_score(self, results: List[HealthCheckResult]) -> float:
        """Calculate overall health score (0.0 to 1.0)"""
        if not results:
            return 0.0
        
        # Weight different checks
        weights = {
            'heartbeat': 2.0,
            'resources': 1.5,
            'task_performance': 1.5,
            'queue_connection': 1.0,
            'model_loading': 1.0,
            'disk_space': 1.0
        }
        
        # Status scores
        status_scores = {
            HealthStatus.HEALTHY: 1.0,
            HealthStatus.WARNING: 0.6,
            HealthStatus.CRITICAL: 0.2,
            HealthStatus.ERROR: 0.1,
            HealthStatus.UNKNOWN: 0.5
        }
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for result in results:
            weight = weights.get(result.check_name, 1.0)
            score = status_scores.get(result.status, 0.5)
            
            weighted_score += weight * score
            total_weight += weight
        
        if total_weight > 0:
            return weighted_score / total_weight
        
        return 0.5
    
    async def store_health_data(self, worker_id: str, health_score: float, 
                               results: List[HealthCheckResult]):
        """Store health data in Redis"""
        try:
            # Store current health
            health_data = {
                'worker_id': worker_id,
                'health_score': health_score,
                'timestamp': datetime.now().isoformat(),
                'checks': [r.to_dict() for r in results]
            }
            
            self.redis.setex(
                f"worker:{worker_id}:health",
                300,  # 5 minutes TTL
                health_data
            )
            
            # Add to time series for history
            history_key = f"worker:{worker_id}:health_history"
            self.redis.zadd(
                history_key,
                {json.dumps(health_data): datetime.now().timestamp()}
            )
            
            # Trim old history (keep 7 days)
            cutoff = (datetime.now() - timedelta(days=7)).timestamp()
            self.redis.zremrangebyscore(history_key, 0, cutoff)
            
        except Exception as e:
            logger.error(f"Failed to store health data: {e}")
    
    async def handle_unhealthy_worker(self, worker_id: str, 
                                    results: List[HealthCheckResult],
                                    health_score: float):
        """Handle unhealthy worker"""
        logger.warning(f"Worker {worker_id} unhealthy (score: {health_score:.2f})")
        
        # Find critical issues
        critical_issues = [r for r in results if r.status == HealthStatus.CRITICAL]
        
        if critical_issues:
            logger.error(f"Critical issues for worker {worker_id}: "
                        f"{[r.message for r in critical_issues]}")
            
            # Check if auto-recovery is appropriate
            if any(r.check_name == 'heartbeat' for r in critical_issues):
                # Worker not responding - restart
                logger.info(f"Attempting to restart unresponsive worker {worker_id}")
                await worker_pool_manager.restart_worker(worker_id)
            
            # Alert about critical issues
            await self.send_health_alert(worker_id, critical_issues, health_score)
    
    async def send_health_alert(self, worker_id: str, 
                              issues: List[HealthCheckResult],
                              health_score: float):
        """Send health alert (placeholder for alert system)"""
        alert_data = {
            'worker_id': worker_id,
            'health_score': health_score,
            'issues': [
                {
                    'check': r.check_name,
                    'status': r.status.value,
                    'message': r.message
                }
                for r in issues
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        # Store alert
        self.redis.lpush(
            "health_alerts",
            json.dumps(alert_data)
        )
        
        # Trim old alerts
        self.redis.ltrim("health_alerts", 0, 999)
        
        logger.error(f"Health alert for worker {worker_id}: {alert_data}")
    
    def get_worker_health(self, worker_id: str) -> Optional[dict]:
        """Get current health data for a worker"""
        if worker_id in self.health_cache:
            cache_data = self.health_cache[worker_id]
            # Check if cache is fresh (< 60 seconds)
            if (datetime.now() - cache_data['timestamp']).seconds < 60:
                return {
                    'worker_id': worker_id,
                    'health_score': cache_data['score'],
                    'checks': [r.to_dict() for r in cache_data['results']],
                    'timestamp': cache_data['timestamp'].isoformat()
                }
        
        # Try Redis
        health_data = self.redis.get(f"worker:{worker_id}:health")
        return health_data
    
    def get_all_workers_health(self) -> Dict[str, dict]:
        """Get health data for all monitored workers"""
        health_summary = {}
        
        for worker_id in self.monitoring_tasks.keys():
            health_data = self.get_worker_health(worker_id)
            if health_data:
                health_summary[worker_id] = health_data
        
        return health_summary
    
    async def get_health_history(self, worker_id: str, hours: int = 24) -> List[dict]:
        """Get historical health data"""
        try:
            cutoff = (datetime.now() - timedelta(hours=hours)).timestamp()
            history_key = f"worker:{worker_id}:health_history"
            
            history_data = self.redis.zrangebyscore(
                history_key,
                cutoff,
                '+inf'
            )
            
            return [json.loads(data) for data in history_data]
            
        except Exception as e:
            logger.error(f"Failed to get health history: {e}")
            return []


# Global instance
worker_health_monitor = WorkerHealthMonitor()