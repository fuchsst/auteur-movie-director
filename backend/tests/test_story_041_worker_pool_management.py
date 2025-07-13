"""
Tests for STORY-041: Worker Pool Management

Comprehensive test suite for worker pool management functionality including
scaling, health monitoring, and resource allocation.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.worker.pool_manager import (
    WorkerPoolManager,
    WorkerType,
    WorkerStatus,
    WorkerInfo,
    ResourceAllocation,
    ResourceMonitor,
    HealthChecker
)
from app.worker.celery_config import WorkerTypeConfig, create_worker_command


class TestWorkerPoolManager:
    """Test worker pool management functionality"""

    @pytest.fixture
    def pool_manager(self):
        """Create worker pool manager for testing"""
        return WorkerPoolManager(
            min_workers=1,
            max_workers=5,
            scale_up_threshold=3,
            scale_down_threshold=1,
            idle_timeout=60
        )

    @pytest.fixture
    def mock_resource_monitor(self):
        """Mock resource monitor"""
        monitor = Mock(spec=ResourceMonitor)
        monitor.can_spawn_worker = AsyncMock(return_value=True)
        monitor.allocate_resources = AsyncMock(return_value=ResourceAllocation(
            cpu_cores=2.0,
            memory_gb=4.0,
            gpu_memory_gb=8.0
        ))
        monitor.deallocate_resources = AsyncMock()
        monitor.get_total_resources = AsyncMock(return_value=ResourceAllocation(
            cpu_cores=16.0,
            memory_gb=32.0,
            gpu_memory_gb=24.0
        ))
        monitor.get_allocated_resources = AsyncMock(return_value=ResourceAllocation(
            cpu_cores=4.0,
            memory_gb=8.0,
            gpu_memory_gb=16.0
        ))
        return monitor

    @pytest.mark.asyncio
    async def test_spawn_worker_success(self, pool_manager, mock_resource_monitor):
        """Test successful worker spawning"""
        pool_manager.resource_monitor = mock_resource_monitor
        
        with patch.object(pool_manager, '_start_worker_process', new_callable=AsyncMock) as mock_start, \
             patch.object(pool_manager, '_register_worker_with_redis', new_callable=AsyncMock) as mock_register:
            
            worker_id = await pool_manager.spawn_worker(WorkerType.GPU)
            
            assert worker_id is not None
            assert worker_id in pool_manager.workers
            
            worker_info = pool_manager.workers[worker_id]
            assert worker_info.type == WorkerType.GPU
            assert worker_info.status == WorkerStatus.ACTIVE
            assert len(worker_info.queues) > 0
            
            mock_start.assert_called_once()
            mock_register.assert_called_once()

    @pytest.mark.asyncio
    async def test_spawn_worker_max_limit(self, pool_manager):
        """Test worker spawning respects maximum limit"""
        # Fill up to max workers
        pool_manager.workers = {
            f"worker_{i}": WorkerInfo(
                id=f"worker_{i}",
                type=WorkerType.GENERAL,
                status=WorkerStatus.ACTIVE,
                started_at=datetime.now(),
                resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
                queues=["default"]
            )
            for i in range(pool_manager.max_workers)
        }
        
        worker_id = await pool_manager.spawn_worker(WorkerType.GENERAL)
        assert worker_id is None

    @pytest.mark.asyncio
    async def test_spawn_worker_insufficient_resources(self, pool_manager, mock_resource_monitor):
        """Test worker spawning when resources are insufficient"""
        mock_resource_monitor.can_spawn_worker.return_value = False
        pool_manager.resource_monitor = mock_resource_monitor
        
        worker_id = await pool_manager.spawn_worker(WorkerType.GPU)
        assert worker_id is None

    @pytest.mark.asyncio
    async def test_terminate_worker_success(self, pool_manager):
        """Test successful worker termination"""
        # Add a worker
        worker_info = WorkerInfo(
            id="test_worker",
            type=WorkerType.GENERAL,
            status=WorkerStatus.ACTIVE,
            started_at=datetime.now(),
            resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
            queues=["default"]
        )
        pool_manager.workers["test_worker"] = worker_info
        
        with patch.object(pool_manager, '_stop_worker_process', new_callable=AsyncMock) as mock_stop, \
             patch.object(pool_manager, '_unregister_worker_from_redis', new_callable=AsyncMock) as mock_unregister, \
             patch.object(pool_manager.resource_monitor, 'deallocate_resources', new_callable=AsyncMock) as mock_deallocate:
            
            success = await pool_manager.terminate_worker("test_worker", graceful=True)
            
            assert success is True
            assert "test_worker" not in pool_manager.workers
            
            mock_stop.assert_called_once()
            mock_unregister.assert_called_once()
            mock_deallocate.assert_called_once()

    @pytest.mark.asyncio
    async def test_terminate_nonexistent_worker(self, pool_manager):
        """Test terminating a worker that doesn't exist"""
        success = await pool_manager.terminate_worker("nonexistent", graceful=True)
        assert success is False

    @pytest.mark.asyncio
    async def test_scaling_up(self, pool_manager, mock_resource_monitor):
        """Test automatic scaling up based on queue depth"""
        pool_manager.resource_monitor = mock_resource_monitor
        
        # Mock high queue depth
        with patch.object(pool_manager, '_get_queue_depth', return_value=10), \
             patch.object(pool_manager, 'spawn_worker', new_callable=AsyncMock) as mock_spawn:
            
            await pool_manager.scale_workers()
            mock_spawn.assert_called_once()

    @pytest.mark.asyncio
    async def test_scaling_down(self, pool_manager):
        """Test automatic scaling down with idle workers"""
        # Add idle workers
        for i in range(3):
            worker_info = WorkerInfo(
                id=f"idle_worker_{i}",
                type=WorkerType.GENERAL,
                status=WorkerStatus.IDLE,
                started_at=datetime.now(),
                resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
                queues=["default"],
                idle_since=datetime.now()
            )
            pool_manager.workers[f"idle_worker_{i}"] = worker_info
        
        # Mock low queue depth
        with patch.object(pool_manager, '_get_queue_depth', return_value=0), \
             patch.object(pool_manager, '_terminate_idle_worker', new_callable=AsyncMock) as mock_terminate:
            
            await pool_manager.scale_workers()
            mock_terminate.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_worker_metrics(self, pool_manager, mock_resource_monitor):
        """Test worker metrics collection"""
        pool_manager.resource_monitor = mock_resource_monitor
        
        # Add some workers with different statuses
        pool_manager.workers = {
            "active_worker": WorkerInfo(
                id="active_worker",
                type=WorkerType.GENERAL,
                status=WorkerStatus.ACTIVE,
                started_at=datetime.now(),
                resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
                queues=["default"]
            ),
            "idle_worker": WorkerInfo(
                id="idle_worker",
                type=WorkerType.GPU,
                status=WorkerStatus.IDLE,
                started_at=datetime.now(),
                resources=ResourceAllocation(cpu_cores=2.0, memory_gb=4.0),
                queues=["gpu"]
            ),
            "busy_worker": WorkerInfo(
                id="busy_worker",
                type=WorkerType.CPU,
                status=WorkerStatus.BUSY,
                started_at=datetime.now(),
                resources=ResourceAllocation(cpu_cores=2.0, memory_gb=3.0),
                queues=["cpu"]
            )
        }
        
        with patch.object(pool_manager, '_get_queue_depth', return_value=5):
            metrics = await pool_manager.get_worker_metrics()
            
            assert metrics["total_workers"] == 3
            assert metrics["active_workers"] == 1
            assert metrics["idle_workers"] == 1
            assert metrics["busy_workers"] == 1
            assert metrics["queue_depth"] == 5
            assert "resource_utilization" in metrics
            assert "worker_types" in metrics

    def test_get_active_workers(self, pool_manager):
        """Test getting active workers"""
        # Add workers with different statuses
        pool_manager.workers = {
            "active1": WorkerInfo(
                id="active1",
                type=WorkerType.GENERAL,
                status=WorkerStatus.ACTIVE,
                started_at=datetime.now(),
                resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
                queues=["default"]
            ),
            "idle1": WorkerInfo(
                id="idle1",
                type=WorkerType.GENERAL,
                status=WorkerStatus.IDLE,
                started_at=datetime.now(),
                resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
                queues=["default"]
            ),
            "active2": WorkerInfo(
                id="active2",
                type=WorkerType.GPU,
                status=WorkerStatus.ACTIVE,
                started_at=datetime.now(),
                resources=ResourceAllocation(cpu_cores=2.0, memory_gb=4.0),
                queues=["gpu"]
            )
        }
        
        active_workers = pool_manager.get_active_workers()
        assert len(active_workers) == 2
        assert all(w.status == WorkerStatus.ACTIVE for w in active_workers)

    def test_queues_for_worker_type(self, pool_manager):
        """Test queue assignment for different worker types"""
        gpu_queues = pool_manager._get_queues_for_type(WorkerType.GPU)
        assert "gpu" in gpu_queues
        assert "generation" in gpu_queues
        
        cpu_queues = pool_manager._get_queues_for_type(WorkerType.CPU)
        assert "cpu" in cpu_queues
        assert "processing" in cpu_queues
        
        io_queues = pool_manager._get_queues_for_type(WorkerType.IO)
        assert "io" in io_queues
        assert "file_operations" in io_queues


class TestResourceMonitor:
    """Test resource monitoring functionality"""

    @pytest.fixture
    def resource_monitor(self):
        """Create resource monitor for testing"""
        with patch('psutil.cpu_count', return_value=8), \
             patch('psutil.virtual_memory') as mock_memory:
            
            mock_memory.return_value.total = 32 * 1024**3  # 32GB
            return ResourceMonitor()

    @pytest.mark.asyncio
    async def test_can_spawn_worker_success(self, resource_monitor):
        """Test successful resource availability check"""
        # Reset allocated resources
        resource_monitor.allocated_resources = ResourceAllocation(
            cpu_cores=2.0,
            memory_gb=4.0,
            gpu_memory_gb=0.0
        )
        
        can_spawn = await resource_monitor.can_spawn_worker(WorkerType.GENERAL)
        assert can_spawn is True

    @pytest.mark.asyncio
    async def test_can_spawn_worker_insufficient_cpu(self, resource_monitor):
        """Test resource check with insufficient CPU"""
        # Allocate most CPU
        resource_monitor.allocated_resources = ResourceAllocation(
            cpu_cores=7.5,
            memory_gb=4.0,
            gpu_memory_gb=0.0
        )
        
        can_spawn = await resource_monitor.can_spawn_worker(WorkerType.CPU)
        assert can_spawn is False

    @pytest.mark.asyncio
    async def test_can_spawn_worker_insufficient_memory(self, resource_monitor):
        """Test resource check with insufficient memory"""
        # Allocate most memory
        resource_monitor.allocated_resources = ResourceAllocation(
            cpu_cores=2.0,
            memory_gb=30.0,
            gpu_memory_gb=0.0
        )
        
        can_spawn = await resource_monitor.can_spawn_worker(WorkerType.GENERAL)
        assert can_spawn is False

    @pytest.mark.asyncio
    async def test_allocate_resources(self, resource_monitor):
        """Test resource allocation"""
        initial_cpu = resource_monitor.allocated_resources.cpu_cores
        initial_memory = resource_monitor.allocated_resources.memory_gb
        
        allocation = await resource_monitor.allocate_resources(WorkerType.GPU)
        
        assert allocation.cpu_cores > 0
        assert allocation.memory_gb > 0
        assert allocation.gpu_memory_gb > 0
        
        # Check that allocated tracking was updated
        assert resource_monitor.allocated_resources.cpu_cores > initial_cpu
        assert resource_monitor.allocated_resources.memory_gb > initial_memory

    @pytest.mark.asyncio
    async def test_deallocate_resources(self, resource_monitor):
        """Test resource deallocation"""
        # Allocate some resources first
        allocation = await resource_monitor.allocate_resources(WorkerType.CPU)
        
        initial_cpu = resource_monitor.allocated_resources.cpu_cores
        initial_memory = resource_monitor.allocated_resources.memory_gb
        
        await resource_monitor.deallocate_resources(allocation)
        
        # Check that allocated tracking was reduced
        assert resource_monitor.allocated_resources.cpu_cores < initial_cpu
        assert resource_monitor.allocated_resources.memory_gb < initial_memory

    def test_get_requirements_for_types(self, resource_monitor):
        """Test resource requirements for different worker types"""
        general_req = resource_monitor._get_requirements(WorkerType.GENERAL)
        assert general_req.cpu_cores == 1.0
        assert general_req.memory_gb == 2.0
        assert general_req.gpu_memory_gb == 0.0
        
        gpu_req = resource_monitor._get_requirements(WorkerType.GPU)
        assert gpu_req.cpu_cores == 2.0
        assert gpu_req.memory_gb == 4.0
        assert gpu_req.gpu_memory_gb == 8.0
        
        cpu_req = resource_monitor._get_requirements(WorkerType.CPU)
        assert cpu_req.cpu_cores == 2.0
        assert cpu_req.memory_gb == 3.0
        assert cpu_req.gpu_memory_gb == 0.0
        
        io_req = resource_monitor._get_requirements(WorkerType.IO)
        assert io_req.cpu_cores == 0.5
        assert io_req.memory_gb == 1.0
        assert io_req.gpu_memory_gb == 0.0


class TestHealthChecker:
    """Test health checking functionality"""

    @pytest.fixture
    def pool_manager_mock(self):
        """Mock pool manager for health checker"""
        manager = Mock()
        manager.workers = {}
        return manager

    @pytest.fixture
    def health_checker(self, pool_manager_mock):
        """Create health checker for testing"""
        return HealthChecker(pool_manager_mock)

    @pytest.mark.asyncio
    async def test_check_worker_health_success(self, health_checker, pool_manager_mock):
        """Test successful health check"""
        worker_info = WorkerInfo(
            id="test_worker",
            type=WorkerType.GENERAL,
            status=WorkerStatus.ACTIVE,
            started_at=datetime.now(),
            last_heartbeat=datetime.now(),
            tasks_completed=10,
            tasks_failed=1,
            resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
            queues=["default"]
        )
        
        pool_manager_mock.workers = {"test_worker": worker_info}
        
        health_status = await health_checker.check_worker_health("test_worker")
        assert health_status is True
        assert worker_info.last_heartbeat is not None

    @pytest.mark.asyncio
    async def test_check_worker_health_stale_heartbeat(self, health_checker, pool_manager_mock):
        """Test health check with stale heartbeat"""
        from datetime import timedelta
        
        worker_info = WorkerInfo(
            id="test_worker",
            type=WorkerType.GENERAL,
            status=WorkerStatus.ACTIVE,
            started_at=datetime.now(),
            last_heartbeat=datetime.now() - timedelta(minutes=5),  # 5 minutes ago
            tasks_completed=10,
            tasks_failed=1,
            resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
            queues=["default"]
        )
        
        pool_manager_mock.workers = {"test_worker": worker_info}
        
        with patch.object(health_checker, '_handle_unhealthy_worker', new_callable=AsyncMock) as mock_handle:
            health_status = await health_checker.check_worker_health("test_worker")
            
            assert health_status is False
            mock_handle.assert_called_once_with("test_worker", "stale_heartbeat")

    @pytest.mark.asyncio
    async def test_check_worker_health_high_error_rate(self, health_checker, pool_manager_mock):
        """Test health check with high error rate"""
        worker_info = WorkerInfo(
            id="test_worker",
            type=WorkerType.GENERAL,
            status=WorkerStatus.ACTIVE,
            started_at=datetime.now(),
            last_heartbeat=datetime.now(),
            tasks_completed=5,
            tasks_failed=8,  # High failure rate
            resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
            queues=["default"]
        )
        
        pool_manager_mock.workers = {"test_worker": worker_info}
        
        with patch.object(health_checker, '_handle_unhealthy_worker', new_callable=AsyncMock) as mock_handle:
            health_status = await health_checker.check_worker_health("test_worker")
            
            assert health_status is False
            mock_handle.assert_called_once_with("test_worker", "high_error_rate")

    @pytest.mark.asyncio
    async def test_check_nonexistent_worker(self, health_checker, pool_manager_mock):
        """Test health check for nonexistent worker"""
        pool_manager_mock.workers = {}
        
        health_status = await health_checker.check_worker_health("nonexistent")
        assert health_status is False

    @pytest.mark.asyncio
    async def test_handle_unhealthy_worker(self, health_checker, pool_manager_mock):
        """Test handling of unhealthy worker"""
        worker_info = WorkerInfo(
            id="unhealthy_worker",
            type=WorkerType.GENERAL,
            status=WorkerStatus.ACTIVE,
            started_at=datetime.now(),
            resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
            queues=["default"]
        )
        
        pool_manager_mock.workers = {"unhealthy_worker": worker_info}
        pool_manager_mock.terminate_worker = AsyncMock()
        pool_manager_mock.spawn_worker = AsyncMock()
        pool_manager_mock.min_workers = 1
        
        await health_checker._handle_unhealthy_worker("unhealthy_worker", "test_reason")
        
        assert worker_info.status == WorkerStatus.FAILED
        pool_manager_mock.terminate_worker.assert_called_once_with("unhealthy_worker", graceful=False)
        pool_manager_mock.spawn_worker.assert_called_once_with(WorkerType.GENERAL)


class TestCeleryConfiguration:
    """Test Celery configuration functionality"""

    def test_worker_type_configs(self):
        """Test worker type configurations"""
        gpu_config = WorkerTypeConfig.get_gpu_worker_config()
        assert "gpu" in gpu_config["queues"]
        assert gpu_config["concurrency"] == 1
        assert "CUDA_VISIBLE_DEVICES" in gpu_config["environment"]
        
        cpu_config = WorkerTypeConfig.get_cpu_worker_config()
        assert "cpu" in cpu_config["queues"]
        assert cpu_config["concurrency"] == 4
        assert "OMP_NUM_THREADS" in cpu_config["environment"]
        
        io_config = WorkerTypeConfig.get_io_worker_config()
        assert "io" in io_config["queues"]
        assert cpu_config["concurrency"] > io_config["concurrency"]  # IO workers more concurrent

    def test_create_worker_command(self):
        """Test worker command creation"""
        gpu_command = create_worker_command("gpu")
        assert "gpu@%h" in gpu_command
        assert "--queues gpu,priority" in gpu_command
        assert "--concurrency 1" in gpu_command
        
        cpu_command = create_worker_command("cpu")
        assert "cpu@%h" in cpu_command
        assert "--queues cpu,default" in cpu_command
        assert "--concurrency 4" in cpu_command

    def test_unknown_worker_type_defaults_to_general(self):
        """Test that unknown worker type defaults to general"""
        unknown_command = create_worker_command("unknown")
        general_command = create_worker_command("general")
        
        # Should be same as general worker
        assert "general@%h" in unknown_command
        assert "--queues default" in unknown_command


class TestIntegration:
    """Integration tests for worker pool management"""

    @pytest.mark.asyncio
    async def test_full_worker_lifecycle(self):
        """Test complete worker lifecycle from spawn to terminate"""
        pool_manager = WorkerPoolManager(min_workers=0, max_workers=3)
        
        with patch.object(pool_manager, '_start_worker_process', new_callable=AsyncMock), \
             patch.object(pool_manager, '_stop_worker_process', new_callable=AsyncMock), \
             patch.object(pool_manager, '_register_worker_with_redis', new_callable=AsyncMock), \
             patch.object(pool_manager, '_unregister_worker_from_redis', new_callable=AsyncMock), \
             patch.object(pool_manager.resource_monitor, 'can_spawn_worker', new_callable=AsyncMock, return_value=True), \
             patch.object(pool_manager.resource_monitor, 'allocate_resources', new_callable=AsyncMock) as mock_allocate, \
             patch.object(pool_manager.resource_monitor, 'deallocate_resources', new_callable=AsyncMock) as mock_deallocate:
            
            mock_allocate.return_value = ResourceAllocation(cpu_cores=2.0, memory_gb=4.0)
            
            # Spawn worker
            worker_id = await pool_manager.spawn_worker(WorkerType.GPU)
            assert worker_id is not None
            assert len(pool_manager.workers) == 1
            
            # Check worker info
            worker_info = pool_manager.get_worker_info(worker_id)
            assert worker_info is not None
            assert worker_info.type == WorkerType.GPU
            assert worker_info.status == WorkerStatus.ACTIVE
            
            # Terminate worker
            success = await pool_manager.terminate_worker(worker_id)
            assert success is True
            assert len(pool_manager.workers) == 0
            
            # Verify resource deallocation
            mock_deallocate.assert_called_once()

    @pytest.mark.asyncio
    async def test_scaling_with_resource_constraints(self):
        """Test scaling behavior with resource constraints"""
        pool_manager = WorkerPoolManager(min_workers=1, max_workers=5, scale_up_threshold=2)
        
        with patch.object(pool_manager, '_start_worker_process', new_callable=AsyncMock), \
             patch.object(pool_manager, '_register_worker_with_redis', new_callable=AsyncMock), \
             patch.object(pool_manager, '_get_queue_depth', return_value=10):  # High queue depth
            
            # Mock resource availability that changes over time
            resource_calls = [True, True, False, False]  # Can spawn 2 workers, then no more
            pool_manager.resource_monitor.can_spawn_worker = AsyncMock(side_effect=resource_calls)
            pool_manager.resource_monitor.allocate_resources = AsyncMock(return_value=ResourceAllocation(cpu_cores=2.0, memory_gb=4.0))
            
            # First scaling should spawn worker
            await pool_manager.scale_workers()
            assert len(pool_manager.workers) == 1
            
            # Second scaling should spawn another worker
            await pool_manager.scale_workers()
            assert len(pool_manager.workers) == 2
            
            # Third scaling should not spawn (no resources)
            await pool_manager.scale_workers()
            assert len(pool_manager.workers) == 2  # No change

    @pytest.mark.asyncio
    async def test_worker_pool_manager_start_stop(self):
        """Test worker pool manager start and stop"""
        pool_manager = WorkerPoolManager(min_workers=2, max_workers=5)
        
        with patch.object(pool_manager, 'spawn_worker', new_callable=AsyncMock) as mock_spawn, \
             patch.object(pool_manager, '_stop_all_workers', new_callable=AsyncMock) as mock_stop:
            
            # Start pool manager
            await pool_manager.start()
            
            # Should spawn minimum workers
            assert mock_spawn.call_count == 2
            
            # Stop pool manager
            await pool_manager.stop()
            
            # Should stop all workers
            mock_stop.assert_called_once()
            assert pool_manager._shutdown is True


if __name__ == "__main__":
    pytest.main([__file__])