"""
Tests for resource mapping functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.resources import (
    ResourceMapper,
    ResourceSpec,
    WorkerResources,
    ResourceConstraints,
    AllocationStrategy,
    InsufficientResourcesError,
    ResourceConflictError
)


@pytest.fixture
def resource_mapper():
    """Create a resource mapper instance"""
    return ResourceMapper()


@pytest.fixture
def sample_resources():
    """Sample resource specifications"""
    return {
        "small": ResourceSpec(cpu_cores=1.0, memory_gb=2.0),
        "medium": ResourceSpec(cpu_cores=2.0, memory_gb=4.0),
        "large": ResourceSpec(cpu_cores=4.0, memory_gb=8.0),
        "gpu": ResourceSpec(cpu_cores=2.0, memory_gb=8.0, gpu_count=1, gpu_memory_gb=8.0)
    }


@pytest.fixture
async def mapper_with_workers(resource_mapper, sample_resources):
    """Resource mapper with registered workers"""
    await resource_mapper.start()
    
    # Register workers
    await resource_mapper.register_worker("worker-cpu-1", sample_resources["medium"])
    await resource_mapper.register_worker("worker-cpu-2", sample_resources["large"])
    await resource_mapper.register_worker("worker-gpu-1", sample_resources["gpu"])
    
    yield resource_mapper
    
    await resource_mapper.stop()


class TestResourceMapper:
    """Test ResourceMapper functionality"""
    
    @pytest.mark.asyncio
    async def test_register_worker(self, resource_mapper, sample_resources):
        """Test worker registration"""
        await resource_mapper.register_worker("worker-1", sample_resources["medium"])
        
        assert "worker-1" in resource_mapper.workers
        worker = resource_mapper.workers["worker-1"]
        assert worker.total.cpu_cores == 2.0
        assert worker.total.memory_gb == 4.0
    
    @pytest.mark.asyncio
    async def test_unregister_worker(self, mapper_with_workers):
        """Test worker unregistration"""
        await mapper_with_workers.unregister_worker("worker-cpu-1")
        
        assert "worker-cpu-1" not in mapper_with_workers.workers
    
    @pytest.mark.asyncio
    async def test_unregister_worker_with_allocations(self, mapper_with_workers, sample_resources):
        """Test unregistering worker with active allocations fails"""
        # Create allocation
        allocation = await mapper_with_workers.allocate(
            worker_id="worker-cpu-1",
            requirements=sample_resources["small"],
            task_id="test-task"
        )
        
        # Should fail to unregister
        with pytest.raises(ResourceConflictError):
            await mapper_with_workers.unregister_worker("worker-cpu-1")
    
    @pytest.mark.asyncio
    async def test_find_worker_success(self, mapper_with_workers, sample_resources):
        """Test finding suitable worker"""
        worker_id = await mapper_with_workers.find_worker(sample_resources["small"])
        
        assert worker_id is not None
        assert worker_id in mapper_with_workers.workers
    
    @pytest.mark.asyncio
    async def test_find_worker_insufficient_resources(self, mapper_with_workers):
        """Test finding worker when requirements too large"""
        huge_requirements = ResourceSpec(cpu_cores=16.0, memory_gb=64.0)
        
        worker_id = await mapper_with_workers.find_worker(huge_requirements)
        
        assert worker_id is None
    
    @pytest.mark.asyncio
    async def test_find_worker_with_constraints(self, mapper_with_workers, sample_resources):
        """Test finding worker with constraints"""
        constraints = ResourceConstraints(preferred_worker="worker-cpu-2")
        
        worker_id = await mapper_with_workers.find_worker(
            sample_resources["small"],
            constraints
        )
        
        assert worker_id == "worker-cpu-2"
    
    @pytest.mark.asyncio
    async def test_allocation_strategies(self, mapper_with_workers, sample_resources):
        """Test different allocation strategies"""
        # Test FIRST_FIT
        mapper_with_workers.strategy = AllocationStrategy.FIRST_FIT
        worker1 = await mapper_with_workers.find_worker(sample_resources["small"])
        
        # Test BEST_FIT
        mapper_with_workers.strategy = AllocationStrategy.BEST_FIT
        worker2 = await mapper_with_workers.find_worker(sample_resources["small"])
        
        # Results may differ based on strategy
        assert worker1 is not None
        assert worker2 is not None
    
    @pytest.mark.asyncio
    async def test_allocate_resources(self, mapper_with_workers, sample_resources):
        """Test resource allocation"""
        allocation = await mapper_with_workers.allocate(
            worker_id="worker-cpu-1",
            requirements=sample_resources["small"],
            task_id="test-task"
        )
        
        assert allocation.worker_id == "worker-cpu-1"
        assert allocation.task_id == "test-task"
        assert allocation.id in mapper_with_workers.allocations
        
        # Check worker resources updated
        worker = mapper_with_workers.workers["worker-cpu-1"]
        assert worker.allocated.cpu_cores == 1.0
        assert worker.allocated.memory_gb == 2.0
    
    @pytest.mark.asyncio
    async def test_allocate_insufficient_resources(self, mapper_with_workers):
        """Test allocation with insufficient resources"""
        huge_requirements = ResourceSpec(cpu_cores=16.0, memory_gb=64.0)
        
        with pytest.raises(InsufficientResourcesError):
            await mapper_with_workers.allocate(
                worker_id="worker-cpu-1",
                requirements=huge_requirements,
                task_id="test-task"
            )
    
    @pytest.mark.asyncio
    async def test_release_allocation(self, mapper_with_workers, sample_resources):
        """Test releasing allocation"""
        # Create allocation
        allocation = await mapper_with_workers.allocate(
            worker_id="worker-cpu-1",
            requirements=sample_resources["small"],
            task_id="test-task"
        )
        
        # Release it
        await mapper_with_workers.release(allocation.id)
        
        assert allocation.id not in mapper_with_workers.allocations
        
        # Check worker resources freed
        worker = mapper_with_workers.workers["worker-cpu-1"]
        assert worker.allocated.cpu_cores == 0.0
        assert worker.allocated.memory_gb == 0.0
    
    @pytest.mark.asyncio
    async def test_reserve_resources(self, mapper_with_workers, sample_resources):
        """Test resource reservation"""
        reservation_id = await mapper_with_workers.reserve_resources(
            worker_id="worker-cpu-1",
            requirements=sample_resources["small"],
            duration_seconds=300
        )
        
        assert reservation_id in mapper_with_workers.reservations
        
        # Check worker reserved resources
        worker = mapper_with_workers.workers["worker-cpu-1"]
        assert worker.reserved.cpu_cores == 1.0
        assert worker.reserved.memory_gb == 2.0
    
    @pytest.mark.asyncio
    async def test_allocation_with_reservation(self, mapper_with_workers, sample_resources):
        """Test allocation using existing reservation"""
        # Create reservation
        reservation_id = await mapper_with_workers.reserve_resources(
            worker_id="worker-cpu-1",
            requirements=sample_resources["small"]
        )
        
        # Allocate using reservation
        allocation = await mapper_with_workers.allocate(
            worker_id="worker-cpu-1",
            requirements=sample_resources["small"],
            task_id="test-task",
            reservation_id=reservation_id
        )
        
        assert allocation.worker_id == "worker-cpu-1"
        assert reservation_id not in mapper_with_workers.reservations
        
        # Check resources moved from reserved to allocated
        worker = mapper_with_workers.workers["worker-cpu-1"]
        assert worker.reserved.cpu_cores == 0.0
        assert worker.allocated.cpu_cores == 1.0
    
    @pytest.mark.asyncio
    async def test_get_resource_status(self, mapper_with_workers, sample_resources):
        """Test getting resource status"""
        # Create some allocations
        await mapper_with_workers.allocate(
            worker_id="worker-cpu-1",
            requirements=sample_resources["small"],
            task_id="test-task-1"
        )
        
        status = await mapper_with_workers.get_resource_status()
        
        assert "summary" in status
        assert "workers" in status
        assert status["active_allocations"] == 1
        assert len(status["workers"]) == 3  # 3 registered workers
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_reservations(self, mapper_with_workers, sample_resources):
        """Test cleanup of expired reservations"""
        # Create short-lived reservation
        reservation_id = await mapper_with_workers.reserve_resources(
            worker_id="worker-cpu-1",
            requirements=sample_resources["small"],
            duration_seconds=1  # 1 second
        )
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Trigger cleanup manually
        await mapper_with_workers._cleanup_expired()
        
        assert reservation_id not in mapper_with_workers.reservations
        
        # Check resources freed
        worker = mapper_with_workers.workers["worker-cpu-1"]
        assert worker.reserved.cpu_cores == 0.0


class TestResourceSpec:
    """Test ResourceSpec operations"""
    
    def test_resource_addition(self):
        """Test adding resource specs"""
        spec1 = ResourceSpec(cpu_cores=1.0, memory_gb=2.0)
        spec2 = ResourceSpec(cpu_cores=2.0, memory_gb=4.0)
        
        result = spec1 + spec2
        
        assert result.cpu_cores == 3.0
        assert result.memory_gb == 6.0
    
    def test_resource_subtraction(self):
        """Test subtracting resource specs"""
        spec1 = ResourceSpec(cpu_cores=4.0, memory_gb=8.0)
        spec2 = ResourceSpec(cpu_cores=2.0, memory_gb=4.0)
        
        result = spec1 - spec2
        
        assert result.cpu_cores == 2.0
        assert result.memory_gb == 4.0
    
    def test_fits_within(self):
        """Test checking if resources fit within available"""
        required = ResourceSpec(cpu_cores=2.0, memory_gb=4.0)
        available = ResourceSpec(cpu_cores=4.0, memory_gb=8.0)
        
        assert required.fits_within(available)
        assert not available.fits_within(required)
    
    def test_fits_within_gpu(self):
        """Test checking GPU requirements"""
        required = ResourceSpec(cpu_cores=1.0, memory_gb=2.0, gpu_count=1, gpu_memory_gb=4.0)
        available_with_gpu = ResourceSpec(cpu_cores=2.0, memory_gb=4.0, gpu_count=1, gpu_memory_gb=8.0)
        available_without_gpu = ResourceSpec(cpu_cores=2.0, memory_gb=4.0, gpu_count=0)
        
        assert required.fits_within(available_with_gpu)
        assert not required.fits_within(available_without_gpu)


class TestWorkerResources:
    """Test WorkerResources functionality"""
    
    def test_worker_resources_available(self):
        """Test calculating available resources"""
        total = ResourceSpec(cpu_cores=4.0, memory_gb=8.0)
        allocated = ResourceSpec(cpu_cores=2.0, memory_gb=4.0)
        reserved = ResourceSpec(cpu_cores=1.0, memory_gb=2.0)
        
        worker = WorkerResources(
            worker_id="test-worker",
            total=total,
            allocated=allocated,
            reserved=reserved
        )
        
        available = worker.available
        assert available.cpu_cores == 1.0  # 4 - 2 - 1
        assert available.memory_gb == 2.0  # 8 - 4 - 2
    
    def test_can_allocate(self):
        """Test checking if worker can allocate resources"""
        total = ResourceSpec(cpu_cores=4.0, memory_gb=8.0)
        worker = WorkerResources(worker_id="test-worker", total=total)
        
        small_request = ResourceSpec(cpu_cores=2.0, memory_gb=4.0)
        large_request = ResourceSpec(cpu_cores=8.0, memory_gb=16.0)
        
        assert worker.can_allocate(small_request)
        assert not worker.can_allocate(large_request)
    
    def test_utilization_calculation(self):
        """Test utilization percentage calculation"""
        total = ResourceSpec(cpu_cores=4.0, memory_gb=8.0, gpu_count=1)
        allocated = ResourceSpec(cpu_cores=2.0, memory_gb=4.0, gpu_count=1)
        
        worker = WorkerResources(
            worker_id="test-worker",
            total=total,
            allocated=allocated
        )
        
        utilization = worker.utilization
        assert utilization['cpu'] == 50.0  # 2/4 * 100
        assert utilization['memory'] == 50.0  # 4/8 * 100
        assert utilization['gpu'] == 100.0  # 1/1 * 100