"""
Tests for GPU resource management
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch

from app.resources import GPUResourceManager, GPUDevice, ResourceSpec


@pytest.fixture
def gpu_manager():
    """Create GPU manager instance"""
    return GPUResourceManager()


@pytest.fixture
def mock_gpu_devices():
    """Mock GPU devices for testing"""
    return [
        GPUDevice(
            index=0,
            name="NVIDIA RTX 3090",
            memory_total_gb=24.0,
            memory_free_gb=24.0,
            compute_capability="8.6",
            utilization_percent=0.0
        ),
        GPUDevice(
            index=1,
            name="NVIDIA RTX 3080",
            memory_total_gb=10.0,
            memory_free_gb=10.0,
            compute_capability="8.6",
            utilization_percent=0.0
        ),
        GPUDevice(
            index=2,
            name="NVIDIA GTX 1080",
            memory_total_gb=8.0,
            memory_free_gb=8.0,
            compute_capability="6.1",
            utilization_percent=0.0
        )
    ]


class TestGPUResourceManager:
    """Test GPU resource management"""
    
    @pytest.mark.asyncio
    async def test_gpu_discovery_no_nvml(self, gpu_manager):
        """Test GPU discovery when NVML not available"""
        # Should handle missing NVML gracefully
        devices = await gpu_manager._discover_devices()
        
        # Without NVML, should return empty list
        assert devices == []
    
    @pytest.mark.asyncio
    async def test_allocate_gpu_success(self, gpu_manager, mock_gpu_devices):
        """Test successful GPU allocation"""
        gpu_manager.devices = mock_gpu_devices
        
        device_index = await gpu_manager.allocate_gpu(memory_gb=8.0)
        
        assert device_index is not None
        assert device_index in gpu_manager.allocations
        assert gpu_manager.allocations[device_index].memory_gb == 8.0
    
    @pytest.mark.asyncio
    async def test_allocate_gpu_insufficient_memory(self, gpu_manager, mock_gpu_devices):
        """Test GPU allocation with insufficient memory"""
        gpu_manager.devices = mock_gpu_devices
        
        # Try to allocate more memory than any device has
        device_index = await gpu_manager.allocate_gpu(memory_gb=32.0)
        
        assert device_index is None
    
    @pytest.mark.asyncio
    async def test_allocate_gpu_compute_capability(self, gpu_manager, mock_gpu_devices):
        """Test GPU allocation with compute capability requirement"""
        gpu_manager.devices = mock_gpu_devices
        
        # Require high compute capability (only RTX cards have 8.6)
        device_index = await gpu_manager.allocate_gpu(
            memory_gb=4.0,
            compute_capability="8.0"
        )
        
        assert device_index in [0, 1]  # Should be RTX 3090 or 3080
        
        # Require lower compute capability (all devices qualify)
        device_index2 = await gpu_manager.allocate_gpu(
            memory_gb=4.0,
            compute_capability="6.0"
        )
        
        assert device_index2 is not None
    
    @pytest.mark.asyncio
    async def test_allocate_gpu_preferred_device(self, gpu_manager, mock_gpu_devices):
        """Test GPU allocation with preferred device"""
        gpu_manager.devices = mock_gpu_devices
        
        # Prefer specific device
        device_index = await gpu_manager.allocate_gpu(
            memory_gb=4.0,
            preferred_device=1
        )
        
        assert device_index == 1
    
    @pytest.mark.asyncio
    async def test_allocate_gpu_preferred_device_unavailable(self, gpu_manager, mock_gpu_devices):
        """Test GPU allocation when preferred device unavailable"""
        gpu_manager.devices = mock_gpu_devices
        
        # Allocate all memory on device 1
        await gpu_manager.allocate_gpu(memory_gb=10.0, preferred_device=1)
        
        # Try to allocate more on device 1
        device_index = await gpu_manager.allocate_gpu(
            memory_gb=4.0,
            preferred_device=1
        )
        
        # Should allocate on different device
        assert device_index != 1
    
    @pytest.mark.asyncio
    async def test_allocate_multi_gpu_success(self, gpu_manager, mock_gpu_devices):
        """Test multi-GPU allocation"""
        gpu_manager.devices = mock_gpu_devices
        
        device_indices = await gpu_manager.allocate_multi_gpu(
            count=2,
            memory_per_gpu_gb=4.0
        )
        
        assert len(device_indices) == 2
        assert len(set(device_indices)) == 2  # Should be different devices
        
        for idx in device_indices:
            assert idx in gpu_manager.allocations
            assert gpu_manager.allocations[idx].memory_gb == 4.0
    
    @pytest.mark.asyncio
    async def test_allocate_multi_gpu_insufficient(self, gpu_manager, mock_gpu_devices):
        """Test multi-GPU allocation with insufficient devices"""
        gpu_manager.devices = mock_gpu_devices
        
        # Try to allocate more GPUs than available
        device_indices = await gpu_manager.allocate_multi_gpu(
            count=5,
            memory_per_gpu_gb=4.0
        )
        
        assert device_indices is None
        assert len(gpu_manager.allocations) == 0  # Should rollback
    
    @pytest.mark.asyncio
    async def test_allocate_multi_gpu_partial_rollback(self, gpu_manager, mock_gpu_devices):
        """Test multi-GPU allocation rollback on partial failure"""
        gpu_manager.devices = mock_gpu_devices
        
        # Allocate most memory on devices
        await gpu_manager.allocate_gpu(memory_gb=20.0, preferred_device=0)
        await gpu_manager.allocate_gpu(memory_gb=8.0, preferred_device=1)
        
        # Try to allocate 2 GPUs requiring 8GB each (only device 2 has enough)
        device_indices = await gpu_manager.allocate_multi_gpu(
            count=2,
            memory_per_gpu_gb=8.0
        )
        
        assert device_indices is None
        # Original allocations should remain
        assert 0 in gpu_manager.allocations
        assert 1 in gpu_manager.allocations
    
    @pytest.mark.asyncio
    async def test_release_gpu(self, gpu_manager, mock_gpu_devices):
        """Test GPU release"""
        gpu_manager.devices = mock_gpu_devices
        
        # Allocate GPU
        device_index = await gpu_manager.allocate_gpu(memory_gb=8.0)
        assert device_index in gpu_manager.allocations
        
        # Release GPU
        await gpu_manager.release_gpu(device_index, 8.0)
        
        # Should be removed from allocations
        assert device_index not in gpu_manager.allocations
    
    @pytest.mark.asyncio
    async def test_release_gpu_partial(self, gpu_manager, mock_gpu_devices):
        """Test partial GPU memory release"""
        gpu_manager.devices = mock_gpu_devices
        
        # Allocate GPU
        device_index = await gpu_manager.allocate_gpu(memory_gb=16.0)
        
        # Release part of memory
        await gpu_manager.release_gpu(device_index, 8.0)
        
        # Should still be in allocations with reduced memory
        assert device_index in gpu_manager.allocations
        assert gpu_manager.allocations[device_index].memory_gb == 8.0
    
    @pytest.mark.asyncio
    async def test_get_gpu_status(self, gpu_manager, mock_gpu_devices):
        """Test getting GPU status"""
        gpu_manager.devices = mock_gpu_devices
        
        # Allocate some memory
        await gpu_manager.allocate_gpu(memory_gb=8.0, preferred_device=0)
        await gpu_manager.allocate_gpu(memory_gb=4.0, preferred_device=1)
        
        status = await gpu_manager.get_gpu_status()
        
        assert "devices" in status
        assert "summary" in status
        assert len(status["devices"]) == 3
        
        # Check device 0 allocation
        device_0_status = next(d for d in status["devices"] if d["index"] == 0)
        assert device_0_status["memory_allocated_gb"] == 8.0
        assert device_0_status["memory_free_gb"] == 16.0  # 24 - 8
        
        # Check summary
        summary = status["summary"]
        assert summary["device_count"] == 3
        assert summary["allocated_memory_gb"] == 12.0  # 8 + 4
        assert summary["total_memory_gb"] == 42.0  # 24 + 10 + 8
    
    def test_estimate_gpu_requirements(self, gpu_manager):
        """Test estimating GPU requirements from resource spec"""
        # Single GPU requirement
        spec1 = ResourceSpec(gpu_count=1, gpu_memory_gb=8.0)
        count1, memory1 = gpu_manager.estimate_gpu_requirements(spec1)
        assert count1 == 1
        assert memory1 == 8.0
        
        # Multi-GPU requirement
        spec2 = ResourceSpec(gpu_count=2, gpu_memory_gb=16.0)
        count2, memory2 = gpu_manager.estimate_gpu_requirements(spec2)
        assert count2 == 2
        assert memory2 == 8.0  # 16 / 2
        
        # No GPU requirement
        spec3 = ResourceSpec(gpu_count=0)
        count3, memory3 = gpu_manager.estimate_gpu_requirements(spec3)
        assert count3 == 0
        assert memory3 == 0
    
    @pytest.mark.asyncio
    async def test_gpu_selection_preference(self, gpu_manager, mock_gpu_devices):
        """Test GPU selection preferences larger memory first"""
        gpu_manager.devices = mock_gpu_devices
        
        # Should prefer device with more memory (RTX 3090)
        device_index = await gpu_manager.allocate_gpu(memory_gb=4.0)
        
        # Should be device 0 (RTX 3090 with 24GB)
        assert device_index == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_allocation(self, gpu_manager, mock_gpu_devices):
        """Test concurrent GPU allocations"""
        gpu_manager.devices = mock_gpu_devices
        
        # Simulate concurrent allocations
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                gpu_manager.allocate_gpu(memory_gb=4.0)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Should get valid allocations (some may be None if insufficient resources)
        successful_allocations = [r for r in results if r is not None]
        assert len(successful_allocations) > 0
        
        # No duplicate allocations
        assert len(successful_allocations) == len(set(successful_allocations))


class TestGPUDevice:
    """Test GPUDevice model"""
    
    def test_device_creation(self):
        """Test creating GPU device"""
        device = GPUDevice(
            index=0,
            name="Test GPU",
            memory_total_gb=8.0,
            memory_free_gb=6.0,
            compute_capability="7.5",
            utilization_percent=50.0,
            temperature_c=75.0,
            power_draw_w=250.0
        )
        
        assert device.index == 0
        assert device.name == "Test GPU"
        assert device.memory_total_gb == 8.0
        assert device.memory_free_gb == 6.0
        assert device.compute_capability == "7.5"
        assert device.utilization_percent == 50.0
        assert device.temperature_c == 75.0
        assert device.power_draw_w == 250.0
    
    def test_device_to_dict(self):
        """Test converting device to dictionary"""
        device = GPUDevice(
            index=0,
            name="Test GPU",
            memory_total_gb=8.0,
            memory_free_gb=6.0,
            compute_capability="7.5"
        )
        
        device_dict = device.to_dict()
        
        assert device_dict["index"] == 0
        assert device_dict["name"] == "Test GPU"
        assert device_dict["memory_total_gb"] == 8.0
        assert device_dict["compute_capability"] == "7.5"