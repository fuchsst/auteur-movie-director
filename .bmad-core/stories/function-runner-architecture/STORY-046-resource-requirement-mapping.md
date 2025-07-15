# Story: Resource Requirement Mapping

**Story ID**: STORY-046  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Feature  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description
As a resource manager, I want automatic mapping between function requirements and available worker resources, so that tasks are efficiently allocated to workers with appropriate CPU, memory, and GPU capabilities, maximizing throughput while preventing resource exhaustion.

## Acceptance Criteria

### Functional Requirements
- [ ] Map function resource requirements to worker capabilities
- [ ] Support heterogeneous worker pools (CPU-only, GPU, multi-GPU)
- [ ] Dynamic resource allocation based on current utilization
- [ ] Resource reservation system prevents overcommitment
- [ ] Quality-based resource scaling (draft vs ultra quality)
- [ ] Resource pooling for efficient GPU sharing
- [ ] Automatic fallback to CPU when GPU unavailable
- [ ] Resource usage tracking and reporting

### Technical Requirements
- [ ] Implement `ResourceMapper` with allocation strategies
- [ ] Create resource inventory tracking system
- [ ] Build GPU device management with CUDA support
- [ ] Implement resource reservation with timeout
- [ ] Add resource monitoring with real-time updates
- [ ] Create resource allocation API
- [ ] Implement fair-share scheduling algorithm
- [ ] Add resource prediction based on historical data

### Quality Requirements
- [ ] Resource allocation decision < 10ms
- [ ] GPU utilization > 80% under load
- [ ] Zero resource conflicts or double allocation
- [ ] Resource tracking accuracy > 99%
- [ ] Support for 8+ GPU devices per node
- [ ] Memory allocation granularity of 100MB
- [ ] Automatic resource reclamation within 30s

## Implementation Notes

### Resource Model
```python
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
            disk_gb=self.disk_gb + other.disk_gb
        )
    
    def fits_within(self, available: 'ResourceSpec') -> bool:
        """Check if requirements fit within available resources"""
        return (
            self.cpu_cores <= available.cpu_cores and
            self.memory_gb <= available.memory_gb and
            self.gpu_count <= available.gpu_count and
            self.gpu_memory_gb <= available.gpu_memory_gb and
            self.disk_gb <= available.disk_gb
        )

@dataclass
class WorkerResources:
    """Available resources on a worker"""
    worker_id: str
    total: ResourceSpec
    allocated: ResourceSpec
    reserved: ResourceSpec
    
    @property
    def available(self) -> ResourceSpec:
        """Calculate available resources"""
        return ResourceSpec(
            cpu_cores=self.total.cpu_cores - self.allocated.cpu_cores - self.reserved.cpu_cores,
            memory_gb=self.total.memory_gb - self.allocated.memory_gb - self.reserved.memory_gb,
            gpu_count=self.total.gpu_count if self.allocated.gpu_count == 0 else 0,
            gpu_memory_gb=self.total.gpu_memory_gb - self.allocated.gpu_memory_gb,
            disk_gb=self.total.disk_gb - self.allocated.disk_gb
        )
    
    def can_allocate(self, request: ResourceSpec) -> bool:
        """Check if worker can fulfill request"""
        return request.fits_within(self.available)
```

### Resource Mapper
```python
class ResourceMapper:
    """Maps function requirements to worker resources"""
    
    def __init__(self):
        self.workers: Dict[str, WorkerResources] = {}
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.reservations: Dict[str, ResourceReservation] = {}
        self._lock = asyncio.Lock()
        
    async def find_worker(self, 
                         requirements: ResourceSpec,
                         constraints: Optional[ResourceConstraints] = None) -> Optional[str]:
        """Find suitable worker for requirements"""
        async with self._lock:
            # Get candidate workers
            candidates = self._get_candidates(requirements, constraints)
            
            if not candidates:
                return None
            
            # Apply allocation strategy
            selected = self._select_worker(candidates, requirements)
            
            # Reserve resources
            if selected:
                await self._reserve_resources(selected, requirements)
            
            return selected
    
    def _get_candidates(self, 
                       requirements: ResourceSpec,
                       constraints: Optional[ResourceConstraints]) -> List[str]:
        """Get workers that can fulfill requirements"""
        candidates = []
        
        for worker_id, resources in self.workers.items():
            # Check basic resource availability
            if not resources.can_allocate(requirements):
                continue
            
            # Check constraints
            if constraints:
                if constraints.preferred_worker and worker_id != constraints.preferred_worker:
                    continue
                if constraints.exclude_workers and worker_id in constraints.exclude_workers:
                    continue
                if constraints.require_gpu_type:
                    # Check GPU type matches
                    pass
            
            candidates.append(worker_id)
        
        return candidates
    
    def _select_worker(self, candidates: List[str], requirements: ResourceSpec) -> str:
        """Select best worker from candidates"""
        # Score each candidate
        scores = []
        
        for worker_id in candidates:
            resources = self.workers[worker_id]
            score = self._calculate_allocation_score(resources, requirements)
            scores.append((score, worker_id))
        
        # Sort by score (higher is better)
        scores.sort(reverse=True)
        
        return scores[0][1] if scores else None
    
    def _calculate_allocation_score(self, 
                                   resources: WorkerResources,
                                   requirements: ResourceSpec) -> float:
        """Calculate allocation score for load balancing"""
        available = resources.available
        
        # Factors:
        # 1. Resource fit (prefer workers with just enough resources)
        # 2. Current utilization (prefer less loaded workers)
        # 3. Resource fragmentation (prefer keeping resources together)
        
        # Resource fit score (0-1, where 1 is perfect fit)
        cpu_fit = 1.0 - abs(available.cpu_cores - requirements.cpu_cores) / available.cpu_cores
        mem_fit = 1.0 - abs(available.memory_gb - requirements.memory_gb) / available.memory_gb
        fit_score = (cpu_fit + mem_fit) / 2
        
        # Utilization score (0-1, where 1 is low utilization)
        cpu_util = resources.allocated.cpu_cores / resources.total.cpu_cores
        mem_util = resources.allocated.memory_gb / resources.total.memory_gb
        util_score = 1.0 - (cpu_util + mem_util) / 2
        
        # GPU bonus (prefer GPU workers for GPU tasks)
        gpu_bonus = 0.2 if requirements.gpu_count > 0 and resources.total.gpu_count > 0 else 0
        
        return fit_score * 0.4 + util_score * 0.6 + gpu_bonus
```

### GPU Resource Management
```python
class GPUResourceManager:
    """Manages GPU device allocation"""
    
    def __init__(self):
        self.devices = self._discover_devices()
        self.allocations: Dict[int, GPUAllocation] = {}
        
    def _discover_devices(self) -> List[GPUDevice]:
        """Discover available GPU devices"""
        devices = []
        
        try:
            import pynvml
            pynvml.nvmlInit()
            
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # Get device info
                name = pynvml.nvmlDeviceGetName(handle).decode()
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                compute_capability = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
                
                devices.append(GPUDevice(
                    index=i,
                    name=name,
                    memory_total_gb=memory.total / (1024**3),
                    memory_free_gb=memory.free / (1024**3),
                    compute_capability=f"{compute_capability[0]}.{compute_capability[1]}"
                ))
                
        except Exception as e:
            logger.warning(f"GPU discovery failed: {e}")
        
        return devices
    
    async def allocate_gpu(self, 
                          memory_gb: float,
                          compute_capability: Optional[str] = None) -> Optional[int]:
        """Allocate GPU device for task"""
        
        # Find suitable device
        for device in self.devices:
            if device.index in self.allocations:
                allocated = self.allocations[device.index].memory_gb
                free = device.memory_total_gb - allocated
            else:
                free = device.memory_total_gb
            
            # Check requirements
            if free >= memory_gb:
                if compute_capability and device.compute_capability < compute_capability:
                    continue
                
                # Allocate
                if device.index not in self.allocations:
                    self.allocations[device.index] = GPUAllocation(
                        device_index=device.index,
                        memory_gb=memory_gb,
                        tasks=[]
                    )
                else:
                    self.allocations[device.index].memory_gb += memory_gb
                
                return device.index
        
        return None
    
    async def release_gpu(self, device_index: int, memory_gb: float):
        """Release GPU allocation"""
        if device_index in self.allocations:
            self.allocations[device_index].memory_gb -= memory_gb
            
            if self.allocations[device_index].memory_gb <= 0:
                del self.allocations[device_index]
```

### Quality-Based Resource Scaling
```python
class QualityResourceScaler:
    """Scale resources based on quality settings"""
    
    # Base resource multipliers for quality levels
    QUALITY_MULTIPLIERS = {
        'draft': {
            'cpu': 0.5,
            'memory': 0.7,
            'gpu_memory': 0.8,
            'time': 0.5
        },
        'standard': {
            'cpu': 1.0,
            'memory': 1.0,
            'gpu_memory': 1.0,
            'time': 1.0
        },
        'high': {
            'cpu': 1.5,
            'memory': 1.3,
            'gpu_memory': 1.2,
            'time': 2.0
        },
        'ultra': {
            'cpu': 2.0,
            'memory': 1.5,
            'gpu_memory': 1.4,
            'time': 4.0
        }
    }
    
    def scale_requirements(self, 
                          base_requirements: ResourceSpec,
                          quality: str,
                          task_specific_scaling: Optional[Dict] = None) -> ResourceSpec:
        """Scale resource requirements based on quality"""
        
        multipliers = self.QUALITY_MULTIPLIERS.get(quality, self.QUALITY_MULTIPLIERS['standard'])
        
        # Apply task-specific scaling if provided
        if task_specific_scaling:
            multipliers = {**multipliers, **task_specific_scaling}
        
        return ResourceSpec(
            cpu_cores=base_requirements.cpu_cores * multipliers['cpu'],
            memory_gb=base_requirements.memory_gb * multipliers['memory'],
            gpu_count=base_requirements.gpu_count,  # Don't scale GPU count
            gpu_memory_gb=base_requirements.gpu_memory_gb * multipliers['gpu_memory'],
            disk_gb=base_requirements.disk_gb  # Disk usually doesn't scale with quality
        )
    
    def estimate_duration(self, base_duration: float, quality: str) -> float:
        """Estimate task duration based on quality"""
        multiplier = self.QUALITY_MULTIPLIERS.get(quality, {}).get('time', 1.0)
        return base_duration * multiplier
```

### Resource Allocation API
```python
@router.post("/resources/allocate")
async def allocate_resources(request: ResourceAllocationRequest) -> ResourceAllocationResponse:
    """Allocate resources for a task"""
    
    # Parse requirements
    base_requirements = ResourceSpec(**request.requirements)
    
    # Scale for quality if specified
    if request.quality:
        scaler = QualityResourceScaler()
        requirements = scaler.scale_requirements(base_requirements, request.quality)
    else:
        requirements = base_requirements
    
    # Find suitable worker
    worker_id = await resource_mapper.find_worker(
        requirements,
        ResourceConstraints(
            preferred_worker=request.preferred_worker,
            exclude_workers=request.exclude_workers,
            require_gpu_type=request.gpu_type
        )
    )
    
    if not worker_id:
        return ResourceAllocationResponse(
            success=False,
            error="No suitable worker found for requirements"
        )
    
    # Create allocation
    allocation = await resource_mapper.allocate(
        worker_id=worker_id,
        requirements=requirements,
        task_id=request.task_id,
        duration_estimate=request.duration_estimate
    )
    
    return ResourceAllocationResponse(
        success=True,
        allocation_id=allocation.id,
        worker_id=worker_id,
        resources=requirements.dict(),
        expires_at=allocation.expires_at
    )

@router.get("/resources/status")
async def get_resource_status() -> ResourceStatusResponse:
    """Get current resource utilization"""
    
    workers = []
    total_resources = ResourceSpec()
    allocated_resources = ResourceSpec()
    
    for worker_id, resources in resource_mapper.workers.items():
        workers.append(WorkerResourceStatus(
            worker_id=worker_id,
            total=resources.total,
            allocated=resources.allocated,
            available=resources.available,
            utilization={
                'cpu': resources.allocated.cpu_cores / resources.total.cpu_cores * 100,
                'memory': resources.allocated.memory_gb / resources.total.memory_gb * 100,
                'gpu': resources.allocated.gpu_count / resources.total.gpu_count * 100 if resources.total.gpu_count > 0 else 0
            }
        ))
        
        total_resources = total_resources + resources.total
        allocated_resources = allocated_resources + resources.allocated
    
    return ResourceStatusResponse(
        workers=workers,
        summary=ResourceSummary(
            total=total_resources,
            allocated=allocated_resources,
            available=total_resources - allocated_resources,
            overall_utilization={
                'cpu': allocated_resources.cpu_cores / total_resources.cpu_cores * 100,
                'memory': allocated_resources.memory_gb / total_resources.memory_gb * 100,
                'gpu': allocated_resources.gpu_count / total_resources.gpu_count * 100 if total_resources.gpu_count > 0 else 0
            }
        )
    )
```

### Resource Monitoring
```python
class ResourceMonitor:
    """Monitor and track resource usage"""
    
    def __init__(self):
        self.metrics = {}
        self.history = deque(maxlen=1000)  # Keep last 1000 data points
        
    async def collect_metrics(self):
        """Collect resource metrics from all workers"""
        while True:
            timestamp = datetime.now()
            metrics = {}
            
            for worker_id, resources in resource_mapper.workers.items():
                # Get real-time usage from worker
                usage = await self._get_worker_usage(worker_id)
                
                metrics[worker_id] = ResourceMetrics(
                    timestamp=timestamp,
                    cpu_percent=usage.cpu_percent,
                    memory_used_gb=usage.memory_gb,
                    gpu_utilization=usage.gpu_utilization,
                    gpu_memory_used_gb=usage.gpu_memory_gb,
                    io_read_mbps=usage.io_read_mbps,
                    io_write_mbps=usage.io_write_mbps
                )
            
            self.history.append(metrics)
            await self._check_alerts(metrics)
            
            await asyncio.sleep(10)  # Collect every 10 seconds
    
    async def predict_resource_needs(self, 
                                   task_type: str,
                                   time_window: int = 3600) -> ResourcePrediction:
        """Predict future resource needs based on history"""
        # Analyze historical data for task type
        # Use simple moving average for now, could use ML later
        pass
```

## Dependencies
- **STORY-041**: Worker Pool Management - provides worker inventory
- **STORY-044**: Function Template Registry - provides resource requirements
- **STORY-045**: Template Validation System - validates resource specs
- pynvml for GPU management
- psutil for system resource monitoring

## Testing Criteria
- [ ] Unit tests for resource allocation algorithms
- [ ] Integration tests with worker pool
- [ ] GPU allocation and release tests
- [ ] Quality-based scaling tests
- [ ] Load tests with 100+ concurrent allocations
- [ ] Resource conflict prevention tests
- [ ] API endpoint tests
- [ ] Performance tests for allocation speed

## Definition of Done
- [ ] ResourceMapper with allocation strategies
- [ ] GPU resource management implemented
- [ ] Quality-based scaling working
- [ ] Resource monitoring collecting metrics
- [ ] API endpoints documented
- [ ] Fair-share scheduling implemented
- [ ] Resource prediction algorithm
- [ ] Performance meets requirements
- [ ] Documentation includes resource guide
- [ ] Code review passed with test coverage > 85%

## Story Links
- **Depends On**: STORY-041 (Worker Pool Management), STORY-044 (Function Template Registry)
- **Blocks**: STORY-047 (API Client Layer)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/resources/allocation_strategy.md