"""
Resource management API endpoints
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.core.dependencies import get_resource_mapper, get_gpu_manager, get_resource_monitor
from app.resources import (
    ResourceSpec,
    ResourceConstraints,
    AllocationStrategy,
    QualityResourceScaler,
    InsufficientResourcesError,
    ResourceConflictError
)

router = APIRouter(prefix="/api/v1/resources")


# Request/Response Models
class ResourceRequirements(BaseModel):
    """Resource requirements specification"""
    cpu_cores: float = Field(default=1.0, ge=0.1, le=64.0)
    memory_gb: float = Field(default=1.0, ge=0.1, le=512.0)
    gpu_count: int = Field(default=0, ge=0, le=8)
    gpu_memory_gb: float = Field(default=0, ge=0, le=80.0)
    gpu_compute_capability: Optional[str] = None
    disk_gb: float = Field(default=10.0, ge=0, le=1000.0)
    network_bandwidth_mbps: Optional[float] = None


class AllocationConstraints(BaseModel):
    """Resource allocation constraints"""
    preferred_worker: Optional[str] = None
    exclude_workers: Optional[List[str]] = None
    require_gpu_type: Optional[str] = None
    require_compute_capability: Optional[str] = None
    max_network_latency_ms: Optional[float] = None
    locality: Optional[str] = None


class ResourceAllocationRequest(BaseModel):
    """Resource allocation request"""
    requirements: ResourceRequirements
    task_id: str
    quality: Optional[str] = "standard"
    task_type: Optional[str] = None
    constraints: Optional[AllocationConstraints] = None
    duration_estimate: Optional[int] = Field(None, ge=1, le=86400)
    strategy: Optional[AllocationStrategy] = None


class ResourceAllocationResponse(BaseModel):
    """Resource allocation response"""
    success: bool
    allocation_id: Optional[str] = None
    worker_id: Optional[str] = None
    resources: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


class ResourceReleaseRequest(BaseModel):
    """Resource release request"""
    allocation_id: str


class WorkerRegistrationRequest(BaseModel):
    """Worker registration request"""
    worker_id: str
    resources: ResourceRequirements


# Endpoints
@router.post("/allocate")
async def allocate_resources(
    request: ResourceAllocationRequest,
    resource_mapper=Depends(get_resource_mapper),
    gpu_manager=Depends(get_gpu_manager)
) -> ResourceAllocationResponse:
    """Allocate resources for a task"""
    
    try:
        # Convert requirements
        base_requirements = ResourceSpec(**request.requirements.dict())
        
        # Scale for quality if specified
        if request.quality:
            scaler = QualityResourceScaler()
            requirements = scaler.scale_requirements(
                base_requirements,
                request.quality,
                request.task_type
            )
        else:
            requirements = base_requirements
        
        # Convert constraints
        constraints = None
        if request.constraints:
            constraints = ResourceConstraints(**request.constraints.dict())
        
        # Find suitable worker
        worker_id = await resource_mapper.find_worker(
            requirements,
            constraints,
            request.strategy
        )
        
        if not worker_id:
            return ResourceAllocationResponse(
                success=False,
                error="No suitable worker found for requirements"
            )
        
        # Allocate GPU if needed
        gpu_devices = []
        if requirements.gpu_count > 0:
            gpu_count, memory_per_gpu = gpu_manager.estimate_gpu_requirements(requirements)
            
            gpu_devices = await gpu_manager.allocate_multi_gpu(
                count=gpu_count,
                memory_per_gpu_gb=memory_per_gpu,
                compute_capability=requirements.gpu_compute_capability
            )
            
            if not gpu_devices:
                return ResourceAllocationResponse(
                    success=False,
                    error="No suitable GPU devices available"
                )
        
        # Create allocation
        allocation = await resource_mapper.allocate(
            worker_id=worker_id,
            requirements=requirements,
            task_id=request.task_id,
            duration_estimate=request.duration_estimate
        )
        
        # Add GPU devices to allocation
        allocation.gpu_devices = gpu_devices
        
        return ResourceAllocationResponse(
            success=True,
            allocation_id=allocation.id,
            worker_id=worker_id,
            resources=requirements.to_dict(),
            expires_at=allocation.expires_at
        )
        
    except InsufficientResourcesError as e:
        return ResourceAllocationResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/release")
async def release_resources(
    request: ResourceReleaseRequest,
    resource_mapper=Depends(get_resource_mapper),
    gpu_manager=Depends(get_gpu_manager)
) -> Dict[str, Any]:
    """Release allocated resources"""
    
    try:
        # Get allocation details
        allocation = resource_mapper.allocations.get(request.allocation_id)
        
        if allocation:
            # Release GPU devices
            for device_idx in allocation.gpu_devices:
                await gpu_manager.release_gpu(
                    device_idx,
                    allocation.resources.gpu_memory_gb / len(allocation.gpu_devices)
                )
        
        # Release allocation
        await resource_mapper.release(request.allocation_id)
        
        return {
            "success": True,
            "message": f"Released allocation {request.allocation_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_resource_status(
    resource_mapper=Depends(get_resource_mapper),
    gpu_manager=Depends(get_gpu_manager)
) -> Dict[str, Any]:
    """Get current resource utilization status"""
    
    try:
        # Get resource status
        resource_status = await resource_mapper.get_resource_status()
        
        # Get GPU status
        gpu_status = await gpu_manager.get_gpu_status()
        
        return {
            "resources": resource_status,
            "gpus": gpu_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workers")
async def list_workers(
    resource_mapper=Depends(get_resource_mapper)
) -> Dict[str, Any]:
    """List all registered workers and their resources"""
    
    workers = []
    for worker_id, worker_resources in resource_mapper.workers.items():
        workers.append({
            "worker_id": worker_id,
            "total": worker_resources.total.to_dict(),
            "allocated": worker_resources.allocated.to_dict(),
            "reserved": worker_resources.reserved.to_dict(),
            "available": worker_resources.available.to_dict(),
            "utilization": worker_resources.utilization
        })
    
    return {
        "workers": workers,
        "total_workers": len(workers)
    }


@router.post("/workers/register")
async def register_worker(
    request: WorkerRegistrationRequest,
    resource_mapper=Depends(get_resource_mapper)
) -> Dict[str, Any]:
    """Register a new worker with its resources"""
    
    try:
        resources = ResourceSpec(**request.resources.dict())
        await resource_mapper.register_worker(request.worker_id, resources)
        
        return {
            "success": True,
            "message": f"Registered worker {request.worker_id}",
            "resources": resources.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workers/{worker_id}")
async def unregister_worker(
    worker_id: str,
    resource_mapper=Depends(get_resource_mapper)
) -> Dict[str, Any]:
    """Unregister a worker"""
    
    try:
        await resource_mapper.unregister_worker(worker_id)
        
        return {
            "success": True,
            "message": f"Unregistered worker {worker_id}"
        }
        
    except ResourceConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/{quality}")
async def get_quality_info(quality: str) -> Dict[str, Any]:
    """Get information about a quality level"""
    
    scaler = QualityResourceScaler()
    return scaler.get_quality_info(quality)


@router.post("/quality/recommend")
async def recommend_quality(
    available: ResourceRequirements,
    required: ResourceRequirements,
    preferred: str = Query("standard", description="Preferred quality if possible")
) -> Dict[str, Any]:
    """Recommend best quality level based on available resources"""
    
    scaler = QualityResourceScaler()
    
    available_spec = ResourceSpec(**available.dict())
    required_spec = ResourceSpec(**required.dict())
    
    recommended = scaler.recommend_quality(
        available_spec,
        required_spec,
        preferred
    )
    
    # Get scaled requirements
    scaled = scaler.scale_requirements(required_spec, recommended)
    
    return {
        "recommended_quality": recommended,
        "scaled_requirements": scaled.to_dict(),
        "fits_within_available": scaled.fits_within(available_spec)
    }


@router.get("/metrics")
async def get_resource_metrics(
    duration_minutes: int = Query(60, ge=1, le=1440),
    resource_monitor=Depends(get_resource_monitor)
) -> Dict[str, Any]:
    """Get resource utilization metrics"""
    
    try:
        summary = await resource_monitor.get_utilization_summary()
        trends = await resource_monitor.get_resource_trends(duration_minutes)
        
        return {
            "summary": summary,
            "trends": trends
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/{task_type}")
async def predict_resources(
    task_type: str,
    resource_monitor=Depends(get_resource_monitor)
) -> Dict[str, Any]:
    """Predict resource needs for a task type"""
    
    try:
        prediction = await resource_monitor.predict_resource_needs(task_type)
        
        if not prediction:
            return {
                "success": False,
                "error": f"Insufficient historical data for task type: {task_type}"
            }
        
        return {
            "success": True,
            "prediction": prediction.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))