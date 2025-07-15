"""
Resource management system for function runner.

Provides automatic mapping between function requirements and available worker
resources with support for CPU, GPU, memory allocation and quality-based scaling.
"""

from .models import (
    ResourceSpec,
    WorkerResources,
    ResourceAllocation,
    ResourceReservation,
    ResourceConstraints,
    GPUDevice,
    GPUAllocation,
    ResourceMetrics,
    ResourcePrediction,
    AllocationStrategy
)
from .mapper import ResourceMapper
from .gpu_manager import GPUResourceManager
from .quality_scaler import QualityResourceScaler
from .monitor import ResourceMonitor
from .exceptions import (
    ResourceAllocationError,
    InsufficientResourcesError,
    ResourceConflictError
)

__all__ = [
    # Models
    "ResourceSpec",
    "WorkerResources",
    "ResourceAllocation",
    "ResourceReservation",
    "ResourceConstraints",
    "GPUDevice",
    "GPUAllocation",
    "ResourceMetrics",
    "ResourcePrediction",
    "AllocationStrategy",
    
    # Core components
    "ResourceMapper",
    "GPUResourceManager",
    "QualityResourceScaler",
    "ResourceMonitor",
    
    # Exceptions
    "ResourceAllocationError",
    "InsufficientResourcesError",
    "ResourceConflictError"
]