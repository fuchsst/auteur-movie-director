"""
Comprehensive metrics collection for performance testing.

Provides real-time collection of application, system, and custom metrics
during performance test execution.
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import json

logger = logging.getLogger(__name__)


@dataclass
class TestMetrics:
    """Metrics collected during performance testing."""
    
    scenario_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    throughput_per_second: float = 0.0
    error_rate: float = 0.0
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    error_details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AppMetrics:
    """Application-level metrics."""
    
    task_submit_rate: float = 0.0
    task_complete_rate: float = 0.0
    task_error_rate: float = 0.0
    
    submit_latency_p50: float = 0.0
    submit_latency_p95: float = 0.0
    submit_latency_p99: float = 0.0
    
    queue_depth: int = 0
    active_workers: int = 0
    worker_utilization: float = 0.0
    
    active_tasks: int = 0
    pending_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0


@dataclass
class SystemMetrics:
    """System-level metrics."""
    
    cpu_usage: float = 0.0
    cpu_cores: int = 0
    memory_usage: float = 0.0
    memory_total: int = 0
    memory_available: int = 0
    
    disk_io_read: int = 0
    disk_io_write: int = 0
    disk_usage: float = 0.0
    
    network_io_sent: int = 0
    network_io_recv: int = 0
    
    gpu_usage: Optional[float] = None
    gpu_memory_usage: Optional[float] = None
    gpu_memory_total: Optional[int] = None


@dataclass
class CustomMetrics:
    """Custom metrics specific to the Function Runner."""
    
    template_usage: Dict[str, int] = field(default_factory=dict)
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    worker_pool_size: int = 0
    autoscaler_events: int = 0
    
    cache_hit_rate: float = 0.0
    cache_size: int = 0
    
    api_response_times: Dict[str, List[float]] = field(default_factory=dict)
    websocket_connections: int = 0
    
    redis_memory_usage: float = 0.0
    redis_connected_clients: int = 0


@dataclass
class TestMetrics:
    """Complete metrics data for a test scenario."""
    
    scenario_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    app_metrics: List[AppMetrics] = field(default_factory=list)
    system_metrics: List[SystemMetrics] = field(default_factory=list)
    custom_metrics: List[CustomMetrics] = field(default_factory=list)
    
    timestamps: List[datetime] = field(default_factory=list)
    
    def add_data_point(self, 
                      timestamp: datetime,
                      app_metrics: AppMetrics,
                      system_metrics: SystemMetrics,
                      custom_metrics: CustomMetrics):
        """Add a new metrics data point."""
        self.timestamps.append(timestamp)
        self.app_metrics.append(app_metrics)
        self.system_metrics.append(system_metrics)
        self.custom_metrics.append(custom_metrics)
    
    def get_max(self, metric_name: str) -> float:
        """Get maximum value for a specific metric."""
        values = self._extract_metric_values(metric_name)
        return max(values) if values else 0.0
    
    def get_average(self, metric_name: str) -> float:
        """Get average value for a specific metric."""
        values = self._extract_metric_values(metric_name)
        return sum(values) / len(values) if values else 0.0
    
    def get_percentile(self, metric_name: str, percentile: int) -> float:
        """Get percentile value for a specific metric."""
        values = self._extract_metric_values(metric_name)
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _extract_metric_values(self, metric_name: str) -> List[float]:
        """Extract values for a specific metric across all data points."""
        values = []
        
        # Check app metrics
        for metric in self.app_metrics:
            if hasattr(metric, metric_name):
                values.append(getattr(metric, metric_name))
        
        # Check system metrics
        for metric in self.system_metrics:
            if hasattr(metric, metric_name):
                values.append(getattr(metric, metric_name))
        
        # Check custom metrics
        for metric in self.custom_metrics:
            if hasattr(metric, metric_name):
                value = getattr(metric, metric_name)
                if isinstance(value, (int, float)):
                    values.append(float(value))
        
        return values


class PrometheusClient:
    """Client for querying Prometheus metrics."""
    
    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url
        self.session = aiohttp.ClientSession()
    
    async def query(self, query: str, time_param: Optional[float] = None) -> Dict[str, Any]:
        """Query Prometheus for metrics."""
        
        params = {'query': query}
        if time_param:
            params['time'] = time_param
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/query", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.warning(f"Prometheus query failed: {resp.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return {}
    
    async def query_range(self, query: str, start: float, end: float, step: str = "15s") -> Dict[str, Any]:
        """Query Prometheus for metrics over a time range."""
        
        params = {
            'query': query,
            'start': start,
            'end': end,
            'step': step
        }
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/query_range", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.warning(f"Prometheus range query failed: {resp.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error querying Prometheus range: {e}")
            return {}
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.close()


class SystemMonitor:
    """Monitor system-level metrics."""
    
    def __init__(self):
        self.initial_disk_io = psutil.disk_io_counters()
        self.initial_net_io = psutil.net_io_counters()
    
    def get_current_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk_io = psutil.disk_io_counters()
        disk_usage = psutil.disk_usage('/')
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Calculate deltas
        disk_read_delta = disk_io.read_bytes - self.initial_disk_io.read_bytes
        disk_write_delta = disk_io.write_bytes - self.initial_disk_io.write_bytes
        
        net_sent_delta = net_io.bytes_sent - self.initial_net_io.bytes_sent
        net_recv_delta = net_io.bytes_recv - self.initial_net_io.bytes_recv
        
        # GPU metrics (if available)
        gpu_usage = None
        gpu_memory_usage = None
        gpu_memory_total = None
        
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            gpu_info = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_usage = gpu_info.gpu
            
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_memory_usage = (memory_info.used / memory_info.total) * 100
            gpu_memory_total = memory_info.total
            
        except (ImportError, Exception):
            # GPU monitoring not available
            pass
        
        return SystemMetrics(
            cpu_usage=cpu_percent,
            cpu_cores=cpu_count,
            memory_usage=memory.percent,
            memory_total=memory.total,
            memory_available=memory.available,
            disk_io_read=disk_read_delta,
            disk_io_write=disk_write_delta,
            disk_usage=(disk_usage.used / disk_usage.total) * 100,
            network_io_sent=net_sent_delta,
            network_io_recv=net_recv_delta,
            gpu_usage=gpu_usage,
            gpu_memory_usage=gpu_memory_usage,
            gpu_memory_total=gpu_memory_total
        )


class MetricsCollector:
    """Collect comprehensive metrics during performance testing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the metrics collector.
        
        Args:
            config: Configuration for metrics collection
        """
        self.config = config or {}
        self.prometheus_client = PrometheusClient(
            self.config.get('prometheus_url', 'http://localhost:9090')
        )
        self.system_monitor = SystemMonitor()
        
        # Configuration
        self.collection_interval = self.config.get('collection_interval', 5)
        self.enable_prometheus = self.config.get('enable_prometheus', True)
        self.enable_system = self.config.get('enable_system', True)
        self.enable_custom = self.config.get('enable_custom', True)
    
    async def collect_during_test(self, scenario) -> TestMetrics:
        """
        Collect metrics throughout test execution.
        
        Args:
            scenario: The load scenario being executed
            
        Returns:
            Complete test metrics
        """
        
        metrics = TestMetrics(
            scenario_name=scenario.name,
            start_time=datetime.now()
        )
        
        logger.info(f"Starting metrics collection for {scenario.name}")
        
        try:
            while True:
                # Check if scenario is complete (this would be set externally)
                if hasattr(scenario, '_complete') and scenario._complete:
                    break
                
                timestamp = datetime.now()
                
                # Collect application metrics
                app_metrics = await self._collect_app_metrics()
                
                # Collect system metrics
                system_metrics = self.system_monitor.get_current_metrics()
                
                # Collect custom metrics
                custom_metrics = await self._collect_custom_metrics()
                
                # Add data point
                metrics.add_data_point(
                    timestamp=timestamp,
                    app_metrics=app_metrics,
                    system_metrics=system_metrics,
                    custom_metrics=custom_metrics
                )
                
                await asyncio.sleep(self.collection_interval)
                
        except asyncio.CancelledError:
            logger.info("Metrics collection cancelled")
        except Exception as e:
            logger.error(f"Error during metrics collection: {e}")
        finally:
            metrics.end_time = datetime.now()
            logger.info(f"Metrics collection completed for {scenario.name}")
            
            # Close connections
            await self.prometheus_client.close()
        
        return metrics
    
    async def _collect_app_metrics(self) -> AppMetrics:
        """Collect application-level metrics from Prometheus."""
        
        if not self.enable_prometheus:
            return AppMetrics()
        
        try:
            # Define Prometheus queries
            queries = {
                'task_submit_rate': 'rate(task_submitted_total[1m])',
                'task_complete_rate': 'rate(task_completed_total[1m])',
                'task_error_rate': 'rate(task_errors_total[1m])',
                'submit_latency_p50': 'histogram_quantile(0.5, task_submit_latency_seconds)',
                'submit_latency_p95': 'histogram_quantile(0.95, task_submit_latency_seconds)',
                'submit_latency_p99': 'histogram_quantile(0.99, task_submit_latency_seconds)',
                'queue_depth': 'celery_queue_length',
                'active_workers': 'worker_pool_active_count',
                'worker_utilization': 'avg(worker_cpu_usage_percent)',
                'active_tasks': 'celery_active_tasks',
                'pending_tasks': 'celery_pending_tasks',
                'completed_tasks': 'celery_completed_tasks_total',
                'failed_tasks': 'celery_failed_tasks_total'
            }
            
            results = {}
            for metric_name, query in queries.items():
                result = await self.prometheus_client.query(query)
                value = self._extract_value(result)
                results[metric_name] = value
            
            return AppMetrics(**results)
            
        except Exception as e:
            logger.error(f"Error collecting app metrics: {e}")
            return AppMetrics()
    
    async def _collect_custom_metrics(self) -> CustomMetrics:
        """Collect custom metrics specific to the Function Runner."""
        
        if not self.enable_custom:
            return CustomMetrics()
        
        # Mock implementation - in real scenario, these would query actual services
        return CustomMetrics(
            template_usage={'image_generation_v1': 100, 'text_generation_v1': 50},
            quality_distribution={'standard': 120, 'high': 30},
            worker_pool_size=4,
            cache_hit_rate=0.85,
            websocket_connections=10
        )
    
    def _extract_value(self, prometheus_result: Dict[str, Any]) -> float:
        """Extract value from Prometheus query result."""
        
        try:
            data = prometheus_result.get('data', {})
            result = data.get('result', [])
            
            if result and len(result) > 0:
                value = result[0].get('value', [0, 0])[1]
                return float(value)
            
            return 0.0
            
        except (KeyError, IndexError, ValueError):
            return 0.0