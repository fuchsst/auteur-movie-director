"""
Custom Autoscaler for Function Runner Workers

Implements intelligent scaling based on queue depth, resource availability,
and worker performance metrics.
"""

import logging
import time
from typing import Dict, Any, Tuple, Optional

import psutil
from celery.worker.autoscale import Autoscaler

logger = logging.getLogger(__name__)


class FunctionRunnerAutoscaler(Autoscaler):
    """
    Custom autoscaler that considers resource availability and queue characteristics
    when scaling workers.
    """

    def __init__(self, pool, max_concurrency, min_concurrency=0, 
                 keepalive=30, mutex=None):
        super().__init__(pool, max_concurrency, min_concurrency, keepalive, mutex)
        
        # Scaling configuration
        self.scale_up_threshold = 2.0  # Scale up when queue depth > processes * threshold
        self.scale_down_threshold = 0.5  # Scale down when queue depth < processes * threshold
        self.min_idle_time = 60  # Minimum idle time before scaling down (seconds)
        self.resource_utilization_threshold = 0.8  # Max resource utilization before stopping scale-up
        
        # Metrics tracking
        self.last_scale_action = time.time()
        self.scale_cooldown = 30  # Minimum time between scaling actions (seconds)
        self.metrics_history = []
        self.max_history_size = 100
        
        logger.info(f"FunctionRunnerAutoscaler initialized: min={min_concurrency}, max={max_concurrency}")

    def scale(self):
        """
        Main scaling logic that considers multiple factors:
        - Queue depth and growth rate
        - Resource availability (CPU, memory, GPU)
        - Worker performance metrics
        - Recent scaling history
        """
        current_time = time.time()
        
        # Check cooldown period
        if current_time - self.last_scale_action < self.scale_cooldown:
            logger.debug("Scaling cooldown active, skipping scale check")
            return
        
        try:
            # Collect current metrics
            metrics = self._collect_metrics()
            self.metrics_history.append(metrics)
            
            # Keep history bounded
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)
            
            # Determine scaling action
            scaling_decision = self._make_scaling_decision(metrics)
            
            if scaling_decision['action'] == 'scale_up':
                self._scale_up(scaling_decision)
            elif scaling_decision['action'] == 'scale_down':
                self._scale_down(scaling_decision)
            else:
                logger.debug(f"No scaling action needed: {scaling_decision['reason']}")
                
        except Exception as e:
            logger.error(f"Error in autoscaler: {e}")

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive metrics for scaling decisions"""
        inspector = self.pool.app.control.inspect()
        
        # Get queue information
        active_queues = inspector.active_queues() or {}
        reserved_tasks = inspector.reserved() or {}
        scheduled_tasks = inspector.scheduled() or {}
        
        # Calculate queue depths
        total_queue_depth = 0
        queue_depths = {}
        
        for worker, queues in active_queues.items():
            for queue_info in queues:
                queue_name = queue_info['name']
                # In a real implementation, we'd query the broker for actual queue depth
                # For now, we estimate based on reserved + scheduled tasks
                reserved_count = len(reserved_tasks.get(worker, []))
                scheduled_count = len(scheduled_tasks.get(worker, []))
                queue_depth = reserved_count + scheduled_count
                
                queue_depths[queue_name] = queue_depths.get(queue_name, 0) + queue_depth
                total_queue_depth += queue_depth
        
        # Get resource utilization
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Get current worker count
        current_processes = len(self.pool._pool)
        
        metrics = {
            'timestamp': time.time(),
            'total_queue_depth': total_queue_depth,
            'queue_depths': queue_depths,
            'current_processes': current_processes,
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            'active_tasks': sum(len(tasks) for tasks in reserved_tasks.values()),
            'scheduled_tasks': sum(len(tasks) for tasks in scheduled_tasks.values()),
        }
        
        # Add GPU metrics if available
        try:
            gpu_metrics = self._get_gpu_metrics()
            metrics.update(gpu_metrics)
        except Exception:
            # GPU monitoring not available
            pass
            
        logger.debug(f"Collected metrics: {metrics}")
        return metrics

    def _make_scaling_decision(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Make intelligent scaling decision based on metrics"""
        current_processes = metrics['current_processes']
        queue_depth = metrics['total_queue_depth']
        cpu_percent = metrics['cpu_percent']
        memory_percent = metrics['memory_percent']
        
        # Calculate queue pressure
        queue_pressure = queue_depth / max(current_processes, 1)
        
        # Check resource constraints
        resource_constrained = (
            cpu_percent > self.resource_utilization_threshold * 100 or
            memory_percent > self.resource_utilization_threshold * 100
        )
        
        # Analyze trends
        trend_info = self._analyze_trends()
        
        # Scale up conditions
        if (queue_pressure > self.scale_up_threshold and 
            current_processes < self.max_concurrency and
            not resource_constrained):
            
            # Calculate how many processes to add
            target_processes = min(
                self.max_concurrency,
                current_processes + max(1, int(queue_pressure - self.scale_up_threshold))
            )
            
            return {
                'action': 'scale_up',
                'target_processes': target_processes,
                'current_processes': current_processes,
                'reason': f'Queue pressure {queue_pressure:.2f} > {self.scale_up_threshold}, resources available'
            }
        
        # Scale down conditions
        elif (queue_pressure < self.scale_down_threshold and 
              current_processes > self.min_concurrency and
              trend_info['sustained_low_load']):
            
            # Calculate how many processes to remove
            target_processes = max(
                self.min_concurrency,
                current_processes - 1  # Scale down conservatively
            )
            
            return {
                'action': 'scale_down',
                'target_processes': target_processes,
                'current_processes': current_processes,
                'reason': f'Queue pressure {queue_pressure:.2f} < {self.scale_down_threshold}, sustained low load'
            }
        
        # No scaling needed
        reason_parts = []
        if resource_constrained:
            reason_parts.append("resource constrained")
        if queue_pressure <= self.scale_up_threshold:
            reason_parts.append(f"queue pressure {queue_pressure:.2f} <= {self.scale_up_threshold}")
        if queue_pressure >= self.scale_down_threshold:
            reason_parts.append(f"queue pressure {queue_pressure:.2f} >= {self.scale_down_threshold}")
        if not trend_info['sustained_low_load']:
            reason_parts.append("load not sustained")
            
        return {
            'action': 'none',
            'current_processes': current_processes,
            'reason': ', '.join(reason_parts) if reason_parts else 'conditions not met'
        }

    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze recent metrics trends"""
        if len(self.metrics_history) < 5:
            return {'sustained_low_load': False, 'load_trend': 'insufficient_data'}
        
        # Look at recent queue pressures
        recent_metrics = self.metrics_history[-5:]
        queue_pressures = []
        
        for metrics in recent_metrics:
            pressure = metrics['total_queue_depth'] / max(metrics['current_processes'], 1)
            queue_pressures.append(pressure)
        
        # Check for sustained low load
        sustained_low_load = all(p < self.scale_down_threshold for p in queue_pressures)
        
        # Calculate trend
        if len(queue_pressures) >= 2:
            if queue_pressures[-1] > queue_pressures[0]:
                load_trend = 'increasing'
            elif queue_pressures[-1] < queue_pressures[0]:
                load_trend = 'decreasing'
            else:
                load_trend = 'stable'
        else:
            load_trend = 'unknown'
        
        return {
            'sustained_low_load': sustained_low_load,
            'load_trend': load_trend,
            'recent_queue_pressures': queue_pressures
        }

    def _scale_up(self, decision: Dict[str, Any]):
        """Execute scale up action"""
        current = decision['current_processes']
        target = decision['target_processes']
        
        logger.info(f"Scaling up from {current} to {target} processes: {decision['reason']}")
        
        # Calculate how many processes to add
        processes_to_add = target - current
        
        for _ in range(processes_to_add):
            if len(self.pool._pool) < self.max_concurrency:
                self.pool.grow()
                
        self.last_scale_action = time.time()

    def _scale_down(self, decision: Dict[str, Any]):
        """Execute scale down action"""
        current = decision['current_processes']
        target = decision['target_processes']
        
        logger.info(f"Scaling down from {current} to {target} processes: {decision['reason']}")
        
        # Calculate how many processes to remove
        processes_to_remove = current - target
        
        for _ in range(processes_to_remove):
            if len(self.pool._pool) > self.min_concurrency:
                self.pool.shrink()
                
        self.last_scale_action = time.time()

    def _get_gpu_metrics(self) -> Dict[str, Any]:
        """Get GPU utilization metrics (placeholder implementation)"""
        # In a real implementation, this would use nvidia-ml-py or similar
        # to get actual GPU metrics
        return {
            'gpu_count': 0,
            'gpu_utilization': 0.0,
            'gpu_memory_used': 0.0,
            'gpu_memory_total': 0.0
        }

    def info(self) -> Dict[str, Any]:
        """Get autoscaler information"""
        current_metrics = self.metrics_history[-1] if self.metrics_history else {}
        
        return {
            'type': 'FunctionRunnerAutoscaler',
            'min_concurrency': self.min_concurrency,
            'max_concurrency': self.max_concurrency,
            'current_processes': len(self.pool._pool),
            'scale_up_threshold': self.scale_up_threshold,
            'scale_down_threshold': self.scale_down_threshold,
            'last_scale_action': self.last_scale_action,
            'scale_cooldown': self.scale_cooldown,
            'metrics_history_size': len(self.metrics_history),
            'current_metrics': current_metrics
        }