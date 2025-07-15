"""
Resource monitoring and prediction system
"""

import asyncio
import logging
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Deque, Any
import statistics

from .models import ResourceMetrics, ResourcePrediction, ResourceSpec
from .mapper import ResourceMapper

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor and track resource usage"""
    
    def __init__(self, 
                 resource_mapper: ResourceMapper,
                 history_size: int = 1000,
                 collection_interval: int = 10):
        """
        Initialize resource monitor.
        
        Args:
            resource_mapper: Resource mapper instance
            history_size: Number of historical data points to keep
            collection_interval: Metrics collection interval in seconds
        """
        self.resource_mapper = resource_mapper
        self.history: Deque[Dict[str, ResourceMetrics]] = deque(maxlen=history_size)
        self.task_history: Dict[str, List[ResourceMetrics]] = defaultdict(list)
        self.collection_interval = collection_interval
        self._monitor_task = None
        self._psutil_available = False
        self._init_psutil()
    
    def _init_psutil(self):
        """Initialize psutil for system monitoring"""
        try:
            import psutil
            self._psutil_available = True
            logger.info("psutil initialized for resource monitoring")
        except ImportError:
            logger.warning("psutil not available - limited resource monitoring")
    
    async def start(self):
        """Start resource monitoring"""
        if not self._monitor_task:
            self._monitor_task = asyncio.create_task(self.collect_metrics())
    
    async def stop(self):
        """Stop resource monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def collect_metrics(self):
        """Collect resource metrics from all workers"""
        while True:
            try:
                await asyncio.sleep(self.collection_interval)
                
                timestamp = datetime.now()
                metrics = {}
                
                # Collect metrics for each worker
                for worker_id, worker_resources in self.resource_mapper.workers.items():
                    # Get real-time usage (simplified - would need worker agent in production)
                    usage = await self._get_worker_usage(worker_id)
                    
                    if usage:
                        metrics[worker_id] = usage
                        
                        # Track by task type if possible
                        for alloc_id, allocation in self.resource_mapper.allocations.items():
                            if allocation.worker_id == worker_id:
                                task_type = self._extract_task_type(allocation.task_id)
                                if task_type:
                                    self.task_history[task_type].append(usage)
                
                # Store metrics
                if metrics:
                    self.history.append(metrics)
                    await self._check_alerts(metrics)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _get_worker_usage(self, worker_id: str) -> Optional[ResourceMetrics]:
        """Get real-time usage from worker"""
        # In production, this would query the actual worker
        # For now, simulate based on allocations
        
        if not self._psutil_available:
            return None
        
        try:
            import psutil
            
            # Get system-wide metrics (would be per-worker in production)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Get GPU metrics if available
            gpu_util = None
            gpu_memory_gb = None
            gpu_memory_percent = None
            
            # Network I/O
            net_io = psutil.net_io_counters()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            
            worker = self.resource_mapper.workers.get(worker_id)
            if not worker:
                return None
            
            # Calculate based on allocations
            allocated_percent = worker.utilization
            
            return ResourceMetrics(
                timestamp=datetime.now(),
                worker_id=worker_id,
                cpu_percent=min(100, cpu_percent * allocated_percent['cpu'] / 100),
                memory_used_gb=worker.allocated.memory_gb,
                memory_percent=allocated_percent['memory'],
                gpu_utilization=gpu_util,
                gpu_memory_used_gb=worker.allocated.gpu_memory_gb if worker.allocated.gpu_count > 0 else None,
                gpu_memory_percent=allocated_percent.get('gpu_memory', 0) if worker.allocated.gpu_count > 0 else None,
                io_read_mbps=0.0,  # Would calculate from disk_io
                io_write_mbps=0.0,
                network_rx_mbps=0.0,  # Would calculate from net_io
                network_tx_mbps=0.0
            )
            
        except Exception as e:
            logger.error(f"Failed to get worker {worker_id} usage: {e}")
            return None
    
    async def predict_resource_needs(self, 
                                   task_type: str,
                                   confidence_threshold: float = 0.7,
                                   min_samples: int = 5) -> Optional[ResourcePrediction]:
        """
        Predict future resource needs based on history.
        
        Args:
            task_type: Type of task to predict for
            confidence_threshold: Minimum confidence level
            min_samples: Minimum historical samples needed
            
        Returns:
            Resource prediction or None if insufficient data
        """
        history = self.task_history.get(task_type, [])
        
        if len(history) < min_samples:
            logger.debug(f"Insufficient history for {task_type}: {len(history)} < {min_samples}")
            return None
        
        # Use recent history (last 50 samples)
        recent_history = history[-50:]
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_history if m.cpu_percent is not None]
        memory_values = [m.memory_used_gb for m in recent_history]
        gpu_memory_values = [m.gpu_memory_used_gb for m in recent_history if m.gpu_memory_used_gb is not None]
        
        # Predict using 90th percentile to be safe
        predicted_cpu = statistics.quantiles(cpu_values, n=10)[8] if cpu_values else 1.0
        predicted_memory = statistics.quantiles(memory_values, n=10)[8] if memory_values else 1.0
        predicted_gpu_memory = statistics.quantiles(gpu_memory_values, n=10)[8] if gpu_memory_values else 0.0
        
        # Calculate confidence based on variance
        cpu_variance = statistics.variance(cpu_values) if len(cpu_values) > 1 else 100
        memory_variance = statistics.variance(memory_values) if len(memory_values) > 1 else 100
        
        # Simple confidence calculation (lower variance = higher confidence)
        confidence = max(0.0, min(1.0, 1.0 - (cpu_variance + memory_variance) / 200))
        
        if confidence < confidence_threshold:
            logger.debug(f"Low confidence prediction for {task_type}: {confidence:.2f}")
        
        # Estimate duration from historical data
        # Would need actual task completion times in production
        estimated_duration = 300  # Default 5 minutes
        
        predicted_resources = ResourceSpec(
            cpu_cores=max(0.1, predicted_cpu / 100 * 4),  # Assuming 4 cores max
            memory_gb=predicted_memory,
            gpu_count=1 if gpu_memory_values else 0,
            gpu_memory_gb=predicted_gpu_memory,
            disk_gb=10.0  # Default
        )
        
        return ResourcePrediction(
            task_type=task_type,
            predicted_resources=predicted_resources,
            confidence=confidence,
            based_on_samples=len(recent_history),
            prediction_window_seconds=self.collection_interval * len(recent_history),
            predicted_duration_seconds=estimated_duration
        )
    
    async def get_worker_metrics(self, 
                               worker_id: str,
                               duration_minutes: int = 60) -> List[ResourceMetrics]:
        """Get historical metrics for a worker"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        metrics = []
        for snapshot in self.history:
            if worker_id in snapshot:
                metric = snapshot[worker_id]
                if metric.timestamp >= cutoff_time:
                    metrics.append(metric)
        
        return metrics
    
    async def get_utilization_summary(self) -> Dict[str, Any]:
        """Get current utilization summary"""
        if not self.history:
            return {"error": "No metrics available"}
        
        # Get latest metrics
        latest = self.history[-1]
        
        # Calculate averages
        total_cpu = 0.0
        total_memory = 0.0
        total_gpu = 0.0
        gpu_count = 0
        
        for worker_id, metrics in latest.items():
            total_cpu += metrics.cpu_percent
            total_memory += metrics.memory_percent
            if metrics.gpu_utilization is not None:
                total_gpu += metrics.gpu_utilization
                gpu_count += 1
        
        worker_count = len(latest)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "workers": worker_count,
            "average_cpu_percent": total_cpu / worker_count if worker_count > 0 else 0,
            "average_memory_percent": total_memory / worker_count if worker_count > 0 else 0,
            "average_gpu_percent": total_gpu / gpu_count if gpu_count > 0 else 0,
            "gpu_workers": gpu_count,
            "metrics_collected": len(self.history)
        }
    
    async def _check_alerts(self, metrics: Dict[str, ResourceMetrics]):
        """Check for resource alerts"""
        for worker_id, metric in metrics.items():
            # High CPU alert
            if metric.cpu_percent > 90:
                logger.warning(f"High CPU usage on {worker_id}: {metric.cpu_percent:.1f}%")
            
            # High memory alert
            if metric.memory_percent > 85:
                logger.warning(f"High memory usage on {worker_id}: {metric.memory_percent:.1f}%")
            
            # GPU temperature alert
            if metric.gpu_utilization is not None and metric.gpu_utilization > 95:
                logger.warning(f"High GPU utilization on {worker_id}: {metric.gpu_utilization:.1f}%")
    
    def _extract_task_type(self, task_id: str) -> Optional[str]:
        """Extract task type from task ID"""
        # Simple extraction - would be more sophisticated in production
        if "image_gen" in task_id:
            return "image_generation"
        elif "video_gen" in task_id:
            return "video_generation"
        elif "audio_gen" in task_id:
            return "audio_generation"
        return None
    
    async def get_resource_trends(self, 
                                duration_minutes: int = 60) -> Dict[str, Any]:
        """Get resource utilization trends"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        # Collect data points
        cpu_trend = []
        memory_trend = []
        gpu_trend = []
        
        for snapshot in self.history:
            if not snapshot:
                continue
                
            # Get first metric timestamp
            first_metric = next(iter(snapshot.values()))
            if first_metric.timestamp < cutoff_time:
                continue
            
            # Calculate snapshot averages
            cpu_values = [m.cpu_percent for m in snapshot.values()]
            memory_values = [m.memory_percent for m in snapshot.values()]
            gpu_values = [m.gpu_utilization for m in snapshot.values() if m.gpu_utilization is not None]
            
            timestamp = first_metric.timestamp.isoformat()
            
            if cpu_values:
                cpu_trend.append({
                    "timestamp": timestamp,
                    "value": statistics.mean(cpu_values)
                })
            
            if memory_values:
                memory_trend.append({
                    "timestamp": timestamp,
                    "value": statistics.mean(memory_values)
                })
            
            if gpu_values:
                gpu_trend.append({
                    "timestamp": timestamp,
                    "value": statistics.mean(gpu_values)
                })
        
        return {
            "duration_minutes": duration_minutes,
            "trends": {
                "cpu": cpu_trend,
                "memory": memory_trend,
                "gpu": gpu_trend
            }
        }