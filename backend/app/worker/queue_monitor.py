"""
Queue Monitoring System

Real-time monitoring of task queues with metrics collection,
alerting, and performance analysis.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from redis import Redis
from celery import Celery
from celery.events.state import State

logger = logging.getLogger(__name__)


@dataclass
class QueueMetrics:
    """Queue metrics snapshot"""
    queue_name: str
    depth: int
    processing_rate: float  # tasks per second
    completion_rate: float  # tasks per second
    error_rate: float  # percentage
    avg_processing_time: float  # seconds
    oldest_task_age: int  # seconds
    active_consumers: int
    timestamp: datetime


@dataclass
class AlertConfig:
    """Alert configuration for queue monitoring"""
    max_depth: int = 1000
    max_error_rate: float = 10.0  # percentage
    max_task_age: int = 3600  # seconds
    min_processing_rate: float = 0.1  # tasks per second
    alert_cooldown: int = 300  # seconds between same alerts


class QueueMonitor:
    """Real-time queue monitoring with alerting"""
    
    DEFAULT_ALERT_CONFIGS = {
        'gpu.generation': AlertConfig(max_depth=50, max_error_rate=5.0, max_task_age=300),
        'gpu.processing': AlertConfig(max_depth=100, max_error_rate=8.0, max_task_age=600),
        'cpu.analysis': AlertConfig(max_depth=200, max_error_rate=10.0, max_task_age=1800),
        'cpu.thumbnail': AlertConfig(max_depth=500, max_error_rate=15.0, max_task_age=3600),
        'io.storage': AlertConfig(max_depth=1000, max_error_rate=5.0, max_task_age=7200),
        'priority': AlertConfig(max_depth=10, max_error_rate=1.0, max_task_age=60),
        'dlq': AlertConfig(max_depth=100, max_error_rate=100.0, max_task_age=86400)
    }
    
    def __init__(self, app: Celery, redis_client: Redis, 
                 alert_callback: Optional[Callable] = None):
        self.app = app
        self.redis = redis_client
        self.alert_callback = alert_callback or self._default_alert_handler
        self.alert_configs = self.DEFAULT_ALERT_CONFIGS.copy()
        self.last_alerts = {}  # Track last alert times for cooldown
        
        # Metrics storage
        self.current_metrics = {}
        self.historical_metrics = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        self.state = State()  # Celery event state
        
        # Rate calculation windows
        self.rate_windows = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600
        }
    
    async def start_monitoring(self, interval: float = 1.0):
        """Start queue monitoring"""
        if self.monitoring_active:
            logger.warning("Queue monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        logger.info("Queue monitoring started")
    
    async def stop_monitoring(self):
        """Stop queue monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Queue monitoring stopped")
    
    async def _monitoring_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._collect_metrics()
                await self._check_alerts()
                await self._store_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_metrics(self):
        """Collect metrics for all queues"""
        current_time = datetime.now()
        
        for queue_name in self.DEFAULT_ALERT_CONFIGS.keys():
            try:
                metrics = await self._collect_queue_metrics(queue_name, current_time)
                self.current_metrics[queue_name] = metrics
            except Exception as e:
                logger.error(f"Error collecting metrics for queue {queue_name}: {e}")
    
    async def _collect_queue_metrics(self, queue_name: str, timestamp: datetime) -> QueueMetrics:
        """Collect metrics for a specific queue"""
        # Get queue depth
        depth = self.redis.llen(f"celery:{queue_name}")
        
        # Calculate processing rates
        processing_rate = await self._calculate_processing_rate(queue_name, '1m')
        completion_rate = await self._calculate_completion_rate(queue_name, '1m')
        
        # Calculate error rate
        error_rate = await self._calculate_error_rate(queue_name, '5m')
        
        # Get average processing time
        avg_processing_time = await self._calculate_avg_processing_time(queue_name, '15m')
        
        # Get oldest task age
        oldest_task_age = await self._get_oldest_task_age(queue_name)
        
        # Get active consumers
        active_consumers = await self._get_active_consumers(queue_name)
        
        return QueueMetrics(
            queue_name=queue_name,
            depth=depth,
            processing_rate=processing_rate,
            completion_rate=completion_rate,
            error_rate=error_rate,
            avg_processing_time=avg_processing_time,
            oldest_task_age=oldest_task_age,
            active_consumers=active_consumers,
            timestamp=timestamp
        )
    
    async def _calculate_processing_rate(self, queue_name: str, window: str) -> float:
        """Calculate task processing rate (tasks started per second)"""
        try:
            window_seconds = self.rate_windows[window]
            key = f"queue_processing:{queue_name}"
            
            # Get count of tasks started in the window
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Remove old entries and count recent ones
            self.redis.zremrangebyscore(key, 0, cutoff_timestamp)
            count = self.redis.zcard(key)
            
            # Set expiration to clean up old keys
            self.redis.expire(key, window_seconds * 2)
            
            return count / window_seconds
            
        except Exception as e:
            logger.warning(f"Error calculating processing rate for {queue_name}: {e}")
            return 0.0
    
    async def _calculate_completion_rate(self, queue_name: str, window: str) -> float:
        """Calculate task completion rate (tasks completed per second)"""
        try:
            window_seconds = self.rate_windows[window]
            key = f"queue_completion:{queue_name}"
            
            # Similar to processing rate but for completed tasks
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            cutoff_timestamp = cutoff_time.timestamp()
            
            self.redis.zremrangebyscore(key, 0, cutoff_timestamp)
            count = self.redis.zcard(key)
            self.redis.expire(key, window_seconds * 2)
            
            return count / window_seconds
            
        except Exception as e:
            logger.warning(f"Error calculating completion rate for {queue_name}: {e}")
            return 0.0
    
    async def _calculate_error_rate(self, queue_name: str, window: str) -> float:
        """Calculate error rate as percentage of failed tasks"""
        try:
            window_seconds = self.rate_windows[window]
            
            # Get counts for the window
            completed_key = f"queue_completion:{queue_name}"
            failed_key = f"queue_failures:{queue_name}"
            
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Clean old entries
            self.redis.zremrangebyscore(completed_key, 0, cutoff_timestamp)
            self.redis.zremrangebyscore(failed_key, 0, cutoff_timestamp)
            
            completed_count = self.redis.zcard(completed_key)
            failed_count = self.redis.zcard(failed_key)
            
            total_count = completed_count + failed_count
            if total_count == 0:
                return 0.0
            
            return (failed_count / total_count) * 100.0
            
        except Exception as e:
            logger.warning(f"Error calculating error rate for {queue_name}: {e}")
            return 0.0
    
    async def _calculate_avg_processing_time(self, queue_name: str, window: str) -> float:
        """Calculate average task processing time in seconds"""
        try:
            window_seconds = self.rate_windows[window]
            key = f"queue_processing_times:{queue_name}"
            
            # Get processing times from the window
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Get times within window (score is timestamp, value is processing time)
            times = self.redis.zrangebyscore(key, cutoff_timestamp, '+inf', withscores=False)
            
            if not times:
                return 0.0
            
            # Calculate average
            total_time = sum(float(time) for time in times)
            return total_time / len(times)
            
        except Exception as e:
            logger.warning(f"Error calculating avg processing time for {queue_name}: {e}")
            return 0.0
    
    async def _get_oldest_task_age(self, queue_name: str) -> int:
        """Get age of oldest task in queue"""
        try:
            # Get first task from queue without removing it
            task_data = self.redis.lindex(f"celery:{queue_name}", 0)
            if not task_data:
                return 0
            
            task = json.loads(task_data)
            
            # Extract timestamp from task
            if 'eta' in task and task['eta']:
                from dateutil.parser import parse
                eta = parse(task['eta'])
                age = (datetime.now() - eta).total_seconds()
                return max(0, int(age))
            elif 'timestamp' in task:
                task_time = datetime.fromtimestamp(task['timestamp'])
                age = (datetime.now() - task_time).total_seconds()
                return max(0, int(age))
            
            return 0
            
        except Exception as e:
            logger.warning(f"Could not get oldest task age for {queue_name}: {e}")
            return 0
    
    async def _get_active_consumers(self, queue_name: str) -> int:
        """Get number of active consumers for queue"""
        try:
            # This would query Celery's active workers
            # For now, return a simulated count based on queue depth
            depth = self.redis.llen(f"celery:{queue_name}")
            
            # Simulate consumer scaling based on depth
            if depth == 0:
                return 1  # Minimum consumers
            elif depth < 10:
                return 1
            elif depth < 50:
                return 2
            elif depth < 100:
                return 3
            else:
                return min(5, depth // 20)  # Scale up to 5 consumers
                
        except Exception as e:
            logger.warning(f"Error getting active consumers for {queue_name}: {e}")
            return 0
    
    async def _check_alerts(self):
        """Check metrics against alert thresholds"""
        current_time = datetime.now()
        
        for queue_name, metrics in self.current_metrics.items():
            if queue_name not in self.alert_configs:
                continue
            
            config = self.alert_configs[queue_name]
            alerts = []
            
            # Check depth threshold
            if metrics.depth > config.max_depth:
                alerts.append(f"Queue depth {metrics.depth} exceeds threshold {config.max_depth}")
            
            # Check error rate threshold
            if metrics.error_rate > config.max_error_rate:
                alerts.append(f"Error rate {metrics.error_rate:.1f}% exceeds threshold {config.max_error_rate}%")
            
            # Check task age threshold
            if metrics.oldest_task_age > config.max_task_age:
                alerts.append(f"Oldest task age {metrics.oldest_task_age}s exceeds threshold {config.max_task_age}s")
            
            # Check processing rate threshold
            if metrics.processing_rate < config.min_processing_rate and metrics.depth > 0:
                alerts.append(f"Processing rate {metrics.processing_rate:.2f} below threshold {config.min_processing_rate}")
            
            # Send alerts if any
            for alert in alerts:
                await self._send_alert(queue_name, alert, current_time, config.alert_cooldown)
    
    async def _send_alert(self, queue_name: str, message: str, 
                         current_time: datetime, cooldown: int):
        """Send alert if not in cooldown period"""
        alert_key = f"{queue_name}:{message}"
        
        # Check cooldown
        if alert_key in self.last_alerts:
            last_alert_time = self.last_alerts[alert_key]
            if (current_time - last_alert_time).total_seconds() < cooldown:
                return  # Still in cooldown
        
        # Send alert
        await self.alert_callback(queue_name, message, current_time)
        self.last_alerts[alert_key] = current_time
        
        logger.warning(f"QUEUE ALERT [{queue_name}]: {message}")
    
    async def _default_alert_handler(self, queue_name: str, message: str, timestamp: datetime):
        """Default alert handler - just logs the alert"""
        logger.warning(f"Queue alert for {queue_name}: {message}")
    
    async def _store_metrics(self):
        """Store metrics in Redis for historical analysis"""
        try:
            timestamp = datetime.now()
            minute_key = timestamp.strftime('%Y-%m-%d:%H:%M')
            
            metrics_data = {}
            for queue_name, metrics in self.current_metrics.items():
                metrics_data[queue_name] = {
                    'depth': metrics.depth,
                    'processing_rate': metrics.processing_rate,
                    'completion_rate': metrics.completion_rate,
                    'error_rate': metrics.error_rate,
                    'avg_processing_time': metrics.avg_processing_time,
                    'oldest_task_age': metrics.oldest_task_age,
                    'active_consumers': metrics.active_consumers
                }
            
            # Store in Redis with TTL
            key = f"queue_metrics:{minute_key}"
            self.redis.setex(key, 86400 * 7, json.dumps(metrics_data))  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
    
    def record_task_started(self, queue_name: str, task_id: str):
        """Record that a task started processing"""
        try:
            timestamp = datetime.now().timestamp()
            key = f"queue_processing:{queue_name}"
            self.redis.zadd(key, {task_id: timestamp})
        except Exception as e:
            logger.warning(f"Error recording task start: {e}")
    
    def record_task_completed(self, queue_name: str, task_id: str, processing_time: float):
        """Record that a task completed successfully"""
        try:
            timestamp = datetime.now().timestamp()
            
            # Record completion
            completion_key = f"queue_completion:{queue_name}"
            self.redis.zadd(completion_key, {task_id: timestamp})
            
            # Record processing time
            time_key = f"queue_processing_times:{queue_name}"
            self.redis.zadd(time_key, {processing_time: timestamp})
            
        except Exception as e:
            logger.warning(f"Error recording task completion: {e}")
    
    def record_task_failed(self, queue_name: str, task_id: str, error_type: str):
        """Record that a task failed"""
        try:
            timestamp = datetime.now().timestamp()
            
            # Record failure
            failure_key = f"queue_failures:{queue_name}"
            self.redis.zadd(failure_key, {f"{task_id}:{error_type}": timestamp})
            
        except Exception as e:
            logger.warning(f"Error recording task failure: {e}")
    
    def get_current_metrics(self, queue_name: str = None) -> Dict[str, QueueMetrics]:
        """Get current metrics for all queues or specific queue"""
        if queue_name:
            return {queue_name: self.current_metrics.get(queue_name)}
        return self.current_metrics.copy()
    
    def get_historical_metrics(self, queue_name: str, 
                             hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics for a queue"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            metrics = []
            current_time = start_time
            
            while current_time <= end_time:
                minute_key = current_time.strftime('%Y-%m-%d:%H:%M')
                key = f"queue_metrics:{minute_key}"
                
                data = self.redis.get(key)
                if data:
                    try:
                        all_metrics = json.loads(data)
                        if queue_name in all_metrics:
                            metric_data = all_metrics[queue_name]
                            metric_data['timestamp'] = current_time.isoformat()
                            metrics.append(metric_data)
                    except json.JSONDecodeError:
                        continue
                
                current_time += timedelta(minutes=1)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []
    
    def get_queue_summary(self) -> Dict[str, Any]:
        """Get summary of all queue metrics"""
        summary = {
            'total_queues': len(self.current_metrics),
            'total_depth': sum(m.depth for m in self.current_metrics.values()),
            'average_error_rate': 0.0,
            'queues_with_alerts': 0,
            'last_update': datetime.now().isoformat(),
            'queue_details': {}
        }
        
        if self.current_metrics:
            summary['average_error_rate'] = sum(m.error_rate for m in self.current_metrics.values()) / len(self.current_metrics)
        
        for queue_name, metrics in self.current_metrics.items():
            config = self.alert_configs.get(queue_name, AlertConfig())
            has_alerts = (
                metrics.depth > config.max_depth or
                metrics.error_rate > config.max_error_rate or
                metrics.oldest_task_age > config.max_task_age
            )
            
            if has_alerts:
                summary['queues_with_alerts'] += 1
            
            summary['queue_details'][queue_name] = {
                'depth': metrics.depth,
                'processing_rate': metrics.processing_rate,
                'error_rate': metrics.error_rate,
                'has_alerts': has_alerts
            }
        
        return summary


# Global instance
queue_monitor = None


def get_queue_monitor(app: Celery, redis_client: Redis, 
                     alert_callback: Optional[Callable] = None) -> QueueMonitor:
    """Get or create queue monitor instance"""
    global queue_monitor
    if queue_monitor is None:
        queue_monitor = QueueMonitor(app, redis_client, alert_callback)
    return queue_monitor