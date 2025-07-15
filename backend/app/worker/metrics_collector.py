"""
Metrics Collection System

Collects and exports worker metrics for monitoring systems like Prometheus.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry
)

from app.worker.health_monitor import HealthCheckResult, HealthStatus

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and export worker metrics for Prometheus"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        
        # Worker health metrics
        self.worker_health_gauge = Gauge(
            'auteur_worker_health_score',
            'Overall worker health score (0-1)',
            ['worker_id'],
            registry=self.registry
        )
        
        self.worker_status_gauge = Gauge(
            'auteur_worker_status',
            'Worker status (1=healthy, 0.6=warning, 0.2=critical, 0=down)',
            ['worker_id', 'check_name'],
            registry=self.registry
        )
        
        # Resource metrics
        self.worker_cpu_gauge = Gauge(
            'auteur_worker_cpu_percent',
            'Worker CPU usage percentage',
            ['worker_id'],
            registry=self.registry
        )
        
        self.worker_memory_gauge = Gauge(
            'auteur_worker_memory_mb',
            'Worker memory usage in MB',
            ['worker_id'],
            registry=self.registry
        )
        
        self.worker_gpu_memory_gauge = Gauge(
            'auteur_worker_gpu_memory_percent',
            'Worker GPU memory usage percentage',
            ['worker_id', 'gpu_index'],
            registry=self.registry
        )
        
        self.worker_gpu_utilization_gauge = Gauge(
            'auteur_worker_gpu_utilization',
            'Worker GPU utilization percentage',
            ['worker_id', 'gpu_index'],
            registry=self.registry
        )
        
        self.worker_disk_usage_gauge = Gauge(
            'auteur_worker_disk_usage_percent',
            'Worker disk usage percentage',
            ['worker_id', 'mount_point'],
            registry=self.registry
        )
        
        # Task metrics
        self.task_counter = Counter(
            'auteur_task_total',
            'Total tasks processed',
            ['worker_id', 'task_type', 'status'],
            registry=self.registry
        )
        
        self.task_duration_histogram = Histogram(
            'auteur_task_duration_seconds',
            'Task execution duration in seconds',
            ['worker_id', 'task_type'],
            buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600),
            registry=self.registry
        )
        
        self.task_error_counter = Counter(
            'auteur_task_errors_total',
            'Total task errors',
            ['worker_id', 'task_type', 'error_type'],
            registry=self.registry
        )
        
        self.task_in_progress_gauge = Gauge(
            'auteur_task_in_progress',
            'Number of tasks currently in progress',
            ['worker_id', 'task_type'],
            registry=self.registry
        )
        
        # Queue metrics
        self.queue_depth_gauge = Gauge(
            'auteur_queue_depth',
            'Number of tasks in queue',
            ['queue_name'],
            registry=self.registry
        )
        
        self.queue_processing_rate_gauge = Gauge(
            'auteur_queue_processing_rate',
            'Queue processing rate (tasks/minute)',
            ['queue_name'],
            registry=self.registry
        )
        
        # Model metrics
        self.model_load_time_histogram = Histogram(
            'auteur_model_load_duration_seconds',
            'Model loading duration',
            ['worker_id', 'model_name'],
            buckets=(1, 5, 10, 30, 60, 120, 300),
            registry=self.registry
        )
        
        self.model_loaded_gauge = Gauge(
            'auteur_model_loaded',
            'Whether model is loaded (1=yes, 0=no)',
            ['worker_id', 'model_name'],
            registry=self.registry
        )
        
        # Performance metrics
        self.worker_uptime_counter = Counter(
            'auteur_worker_uptime_seconds_total',
            'Total worker uptime in seconds',
            ['worker_id'],
            registry=self.registry
        )
        
        self.worker_restarts_counter = Counter(
            'auteur_worker_restarts_total',
            'Total worker restarts',
            ['worker_id', 'reason'],
            registry=self.registry
        )
        
        # Alert metrics
        self.health_alerts_counter = Counter(
            'auteur_health_alerts_total',
            'Total health alerts triggered',
            ['worker_id', 'severity', 'check_name'],
            registry=self.registry
        )
        
        # Network metrics
        self.network_sent_bytes_counter = Counter(
            'auteur_network_sent_bytes_total',
            'Total bytes sent over network',
            ['worker_id'],
            registry=self.registry
        )
        
        self.network_recv_bytes_counter = Counter(
            'auteur_network_received_bytes_total',
            'Total bytes received over network',
            ['worker_id'],
            registry=self.registry
        )
    
    async def update_worker_health(self, worker_id: str, health_score: float,
                                  check_results: List[HealthCheckResult]):
        """Update Prometheus metrics from health check results"""
        try:
            # Update overall health score
            self.worker_health_gauge.labels(worker_id=worker_id).set(health_score)
            
            # Update individual check statuses
            status_values = {
                HealthStatus.HEALTHY: 1.0,
                HealthStatus.WARNING: 0.6,
                HealthStatus.CRITICAL: 0.2,
                HealthStatus.ERROR: 0.0,
                HealthStatus.UNKNOWN: 0.5
            }
            
            for result in check_results:
                status_value = status_values.get(result.status, 0.5)
                self.worker_status_gauge.labels(
                    worker_id=worker_id,
                    check_name=result.check_name
                ).set(status_value)
                
                # Update specific metrics based on check type
                if result.check_name == "resources":
                    self._update_resource_metrics(worker_id, result.metrics)
                elif result.check_name == "task_performance":
                    self._update_task_metrics(worker_id, result.metrics)
                elif result.check_name == "queue_connection":
                    self._update_queue_metrics(result.metrics)
                elif result.check_name == "model_loading":
                    self._update_model_metrics(worker_id, result.metrics)
                elif result.check_name == "disk_space":
                    self._update_disk_metrics(worker_id, result.metrics)
                
                # Track alerts
                if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                    severity = "warning" if result.status == HealthStatus.WARNING else "critical"
                    self.health_alerts_counter.labels(
                        worker_id=worker_id,
                        severity=severity,
                        check_name=result.check_name
                    ).inc()
            
        except Exception as e:
            logger.error(f"Error updating worker health metrics: {e}")
    
    def _update_resource_metrics(self, worker_id: str, metrics: Dict[str, Any]):
        """Update resource usage metrics"""
        if 'cpu_percent' in metrics:
            self.worker_cpu_gauge.labels(worker_id=worker_id).set(metrics['cpu_percent'])
        
        if 'memory_mb' in metrics:
            self.worker_memory_gauge.labels(worker_id=worker_id).set(metrics['memory_mb'])
        
        if 'gpu_memory_percent' in metrics and metrics['gpu_memory_percent'] is not None:
            self.worker_gpu_memory_gauge.labels(
                worker_id=worker_id,
                gpu_index="0"
            ).set(metrics['gpu_memory_percent'])
        
        if 'gpu_utilization' in metrics and metrics['gpu_utilization'] is not None:
            self.worker_gpu_utilization_gauge.labels(
                worker_id=worker_id,
                gpu_index="0"
            ).set(metrics['gpu_utilization'])
        
        if 'network_sent_mb' in metrics:
            # Convert MB to bytes for counter
            sent_bytes = metrics['network_sent_mb'] * 1024 * 1024
            self.network_sent_bytes_counter.labels(worker_id=worker_id)._value.set(sent_bytes)
        
        if 'network_recv_mb' in metrics:
            # Convert MB to bytes for counter
            recv_bytes = metrics['network_recv_mb'] * 1024 * 1024
            self.network_recv_bytes_counter.labels(worker_id=worker_id)._value.set(recv_bytes)
    
    def _update_task_metrics(self, worker_id: str, metrics: Dict[str, Any]):
        """Update task performance metrics"""
        # Note: In a real implementation, these would be updated as tasks complete
        # Here we're updating gauges based on current snapshot
        
        if 'in_progress_tasks' in metrics:
            self.task_in_progress_gauge.labels(
                worker_id=worker_id,
                task_type="all"
            ).set(metrics['in_progress_tasks'])
    
    def _update_queue_metrics(self, metrics: Dict[str, Any]):
        """Update queue-related metrics"""
        if 'queue_depths' in metrics:
            for queue_name, depth in metrics['queue_depths'].items():
                self.queue_depth_gauge.labels(queue_name=queue_name).set(depth)
    
    def _update_model_metrics(self, worker_id: str, metrics: Dict[str, Any]):
        """Update model loading metrics"""
        if 'loaded_models' in metrics:
            for model_name in metrics['loaded_models']:
                self.model_loaded_gauge.labels(
                    worker_id=worker_id,
                    model_name=model_name
                ).set(1)
        
        if 'failed_models' in metrics:
            for model_name in metrics['failed_models']:
                self.model_loaded_gauge.labels(
                    worker_id=worker_id,
                    model_name=model_name
                ).set(0)
    
    def _update_disk_metrics(self, worker_id: str, metrics: Dict[str, Any]):
        """Update disk usage metrics"""
        if 'main_disk_percent' in metrics:
            self.worker_disk_usage_gauge.labels(
                worker_id=worker_id,
                mount_point="/"
            ).set(metrics['main_disk_percent'])
        
        if 'temp_disk_percent' in metrics:
            self.worker_disk_usage_gauge.labels(
                worker_id=worker_id,
                mount_point="/tmp"
            ).set(metrics['temp_disk_percent'])
    
    def record_task_start(self, worker_id: str, task_type: str):
        """Record task start"""
        self.task_in_progress_gauge.labels(
            worker_id=worker_id,
            task_type=task_type
        ).inc()
    
    def record_task_complete(self, worker_id: str, task_type: str, 
                           duration_seconds: float, success: bool = True):
        """Record task completion"""
        # Update counters
        status = "success" if success else "failed"
        self.task_counter.labels(
            worker_id=worker_id,
            task_type=task_type,
            status=status
        ).inc()
        
        # Update duration histogram
        self.task_duration_histogram.labels(
            worker_id=worker_id,
            task_type=task_type
        ).observe(duration_seconds)
        
        # Update in-progress gauge
        self.task_in_progress_gauge.labels(
            worker_id=worker_id,
            task_type=task_type
        ).dec()
    
    def record_task_error(self, worker_id: str, task_type: str, error_type: str):
        """Record task error"""
        self.task_error_counter.labels(
            worker_id=worker_id,
            task_type=task_type,
            error_type=error_type
        ).inc()
    
    def record_model_load(self, worker_id: str, model_name: str, 
                         duration_seconds: float, success: bool = True):
        """Record model loading metrics"""
        if success:
            self.model_load_time_histogram.labels(
                worker_id=worker_id,
                model_name=model_name
            ).observe(duration_seconds)
            
            self.model_loaded_gauge.labels(
                worker_id=worker_id,
                model_name=model_name
            ).set(1)
        else:
            self.model_loaded_gauge.labels(
                worker_id=worker_id,
                model_name=model_name
            ).set(0)
    
    def record_worker_restart(self, worker_id: str, reason: str):
        """Record worker restart"""
        self.worker_restarts_counter.labels(
            worker_id=worker_id,
            reason=reason
        ).inc()
    
    def update_queue_metrics(self, queue_metrics: Dict[str, Dict[str, Any]]):
        """Update queue-level metrics"""
        for queue_name, metrics in queue_metrics.items():
            if 'depth' in metrics:
                self.queue_depth_gauge.labels(queue_name=queue_name).set(metrics['depth'])
            
            if 'processing_rate' in metrics:
                self.queue_processing_rate_gauge.labels(
                    queue_name=queue_name
                ).set(metrics['processing_rate'])
    
    def generate_metrics(self) -> bytes:
        """Generate metrics in Prometheus format"""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get content type for metrics endpoint"""
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
metrics_collector = MetricsCollector()