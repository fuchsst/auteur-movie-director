"""
Resource management data models
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum


@dataclass
class ResourceSpec:
    """Specification of required resources"""
    cpu_cores: float = 1.0  # Fractional cores supported
    memory_gb: float = 1.0
    gpu_count: int = 0
    gpu_memory_gb: float = 0
    gpu_compute_capability: Optional[str] = None  # e.g., "7.5" for RTX 30xx
    disk_gb: float = 10.0
    network_bandwidth_mbps: Optional[float] = None
    
    def __add__(self, other: 'ResourceSpec') -> 'ResourceSpec':
        """Add resource requirements"""
        return ResourceSpec(
            cpu_cores=self.cpu_cores + other.cpu_cores,
            memory_gb=self.memory_gb + other.memory_gb,
            gpu_count=max(self.gpu_count, other.gpu_count),
            gpu_memory_gb=max(self.gpu_memory_gb, other.gpu_memory_gb),
            gpu_compute_capability=max(self.gpu_compute_capability or "0", 
                                      other.gpu_compute_capability or "0"),
            disk_gb=self.disk_gb + other.disk_gb,
            network_bandwidth_mbps=(self.network_bandwidth_mbps or 0) + (other.network_bandwidth_mbps or 0) if self.network_bandwidth_mbps or other.network_bandwidth_mbps else None
        )
    
    def __sub__(self, other: 'ResourceSpec') -> 'ResourceSpec':
        """Subtract resource requirements"""
        return ResourceSpec(
            cpu_cores=max(0, self.cpu_cores - other.cpu_cores),
            memory_gb=max(0, self.memory_gb - other.memory_gb),
            gpu_count=max(0, self.gpu_count - other.gpu_count),
            gpu_memory_gb=max(0, self.gpu_memory_gb - other.gpu_memory_gb),
            gpu_compute_capability=self.gpu_compute_capability,
            disk_gb=max(0, self.disk_gb - other.disk_gb),
            network_bandwidth_mbps=max(0, (self.network_bandwidth_mbps or 0) - (other.network_bandwidth_mbps or 0)) if self.network_bandwidth_mbps or other.network_bandwidth_mbps else None
        )
    
    def fits_within(self, available: 'ResourceSpec') -> bool:
        """Check if requirements fit within available resources"""
        return (
            self.cpu_cores <= available.cpu_cores and
            self.memory_gb <= available.memory_gb and
            self.gpu_count <= available.gpu_count and
            self.gpu_memory_gb <= available.gpu_memory_gb and
            self.disk_gb <= available.disk_gb and
            (not self.network_bandwidth_mbps or not available.network_bandwidth_mbps or 
             self.network_bandwidth_mbps <= available.network_bandwidth_mbps)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cpu_cores": self.cpu_cores,
            "memory_gb": self.memory_gb,
            "gpu_count": self.gpu_count,
            "gpu_memory_gb": self.gpu_memory_gb,
            "gpu_compute_capability": self.gpu_compute_capability,
            "disk_gb": self.disk_gb,
            "network_bandwidth_mbps": self.network_bandwidth_mbps
        }


@dataclass
class WorkerResources:
    """Available resources on a worker"""
    worker_id: str
    total: ResourceSpec
    allocated: ResourceSpec = field(default_factory=ResourceSpec)
    reserved: ResourceSpec = field(default_factory=ResourceSpec)
    
    @property
    def available(self) -> ResourceSpec:
        """Calculate available resources"""
        return ResourceSpec(
            cpu_cores=max(0, self.total.cpu_cores - self.allocated.cpu_cores - self.reserved.cpu_cores),
            memory_gb=max(0, self.total.memory_gb - self.allocated.memory_gb - self.reserved.memory_gb),
            gpu_count=self.total.gpu_count if self.allocated.gpu_count == 0 else 0,
            gpu_memory_gb=max(0, self.total.gpu_memory_gb - self.allocated.gpu_memory_gb - self.reserved.gpu_memory_gb),
            gpu_compute_capability=self.total.gpu_compute_capability,
            disk_gb=max(0, self.total.disk_gb - self.allocated.disk_gb - self.reserved.disk_gb),
            network_bandwidth_mbps=max(0, (self.total.network_bandwidth_mbps or 0) - (self.allocated.network_bandwidth_mbps or 0) - (self.reserved.network_bandwidth_mbps or 0)) if self.total.network_bandwidth_mbps else None
        )
    
    def can_allocate(self, request: ResourceSpec) -> bool:
        """Check if worker can fulfill request"""
        return request.fits_within(self.available)
    
    @property
    def utilization(self) -> Dict[str, float]:
        """Calculate resource utilization percentages"""
        return {
            'cpu': (self.allocated.cpu_cores / self.total.cpu_cores * 100) if self.total.cpu_cores > 0 else 0,
            'memory': (self.allocated.memory_gb / self.total.memory_gb * 100) if self.total.memory_gb > 0 else 0,
            'gpu': (self.allocated.gpu_count / self.total.gpu_count * 100) if self.total.gpu_count > 0 else 0,
            'gpu_memory': (self.allocated.gpu_memory_gb / self.total.gpu_memory_gb * 100) if self.total.gpu_memory_gb > 0 else 0,
            'disk': (self.allocated.disk_gb / self.total.disk_gb * 100) if self.total.disk_gb > 0 else 0
        }


@dataclass
class ResourceAllocation:
    """Active resource allocation"""
    id: str
    worker_id: str
    task_id: str
    resources: ResourceSpec
    allocated_at: datetime
    expires_at: Optional[datetime] = None
    gpu_devices: List[int] = field(default_factory=list)
    
    @property
    def is_expired(self) -> bool:
        """Check if allocation has expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at


@dataclass
class ResourceReservation:
    """Resource reservation before allocation"""
    id: str
    worker_id: str
    resources: ResourceSpec
    reserved_at: datetime
    expires_at: datetime
    priority: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if reservation has expired"""
        return datetime.now() > self.expires_at


@dataclass
class ResourceConstraints:
    """Constraints for resource allocation"""
    preferred_worker: Optional[str] = None
    exclude_workers: Optional[List[str]] = None
    require_gpu_type: Optional[str] = None  # e.g., "nvidia-rtx-3090"
    require_compute_capability: Optional[str] = None
    max_network_latency_ms: Optional[float] = None
    locality: Optional[str] = None  # e.g., "same-rack", "same-datacenter"


@dataclass
class GPUDevice:
    """GPU device information"""
    index: int
    name: str
    memory_total_gb: float
    memory_free_gb: float
    compute_capability: str
    utilization_percent: float = 0.0
    temperature_c: Optional[float] = None
    power_draw_w: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "index": self.index,
            "name": self.name,
            "memory_total_gb": self.memory_total_gb,
            "memory_free_gb": self.memory_free_gb,
            "compute_capability": self.compute_capability,
            "utilization_percent": self.utilization_percent,
            "temperature_c": self.temperature_c,
            "power_draw_w": self.power_draw_w
        }


@dataclass
class GPUAllocation:
    """GPU allocation tracking"""
    device_index: int
    memory_gb: float
    tasks: List[str] = field(default_factory=list)
    allocated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ResourceMetrics:
    """Real-time resource usage metrics"""
    timestamp: datetime
    worker_id: str
    cpu_percent: float
    memory_used_gb: float
    memory_percent: float
    gpu_utilization: Optional[float] = None
    gpu_memory_used_gb: Optional[float] = None
    gpu_memory_percent: Optional[float] = None
    io_read_mbps: float = 0.0
    io_write_mbps: float = 0.0
    network_rx_mbps: float = 0.0
    network_tx_mbps: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "worker_id": self.worker_id,
            "cpu_percent": self.cpu_percent,
            "memory_used_gb": self.memory_used_gb,
            "memory_percent": self.memory_percent,
            "gpu_utilization": self.gpu_utilization,
            "gpu_memory_used_gb": self.gpu_memory_used_gb,
            "gpu_memory_percent": self.gpu_memory_percent,
            "io_read_mbps": self.io_read_mbps,
            "io_write_mbps": self.io_write_mbps,
            "network_rx_mbps": self.network_rx_mbps,
            "network_tx_mbps": self.network_tx_mbps
        }


@dataclass
class ResourcePrediction:
    """Predicted future resource needs"""
    task_type: str
    predicted_resources: ResourceSpec
    confidence: float  # 0-1
    based_on_samples: int
    prediction_window_seconds: int
    predicted_duration_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_type": self.task_type,
            "predicted_resources": self.predicted_resources.to_dict(),
            "confidence": self.confidence,
            "based_on_samples": self.based_on_samples,
            "prediction_window_seconds": self.prediction_window_seconds,
            "predicted_duration_seconds": self.predicted_duration_seconds
        }


class AllocationStrategy(Enum):
    """Resource allocation strategies"""
    BEST_FIT = "best_fit"  # Minimize wasted resources
    FIRST_FIT = "first_fit"  # Fastest allocation
    LOAD_BALANCE = "load_balance"  # Distribute load evenly
    PACK = "pack"  # Consolidate to fewer workers
    SPREAD = "spread"  # Spread across many workers