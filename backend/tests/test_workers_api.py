"""
Tests for Worker Pool Management API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.worker.pool_manager import WorkerType, WorkerStatus, WorkerInfo, ResourceAllocation
from datetime import datetime


class TestWorkersAPI:
    """Test worker pool management API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_pool_manager(self):
        """Mock worker pool manager for testing"""
        with patch('app.api.endpoints.workers.worker_pool_manager') as mock:
            # Mock workers dictionary
            mock.workers = {
                "worker_1": WorkerInfo(
                    id="worker_1",
                    type=WorkerType.GENERAL,
                    status=WorkerStatus.ACTIVE,
                    started_at=datetime.now(),
                    resources=ResourceAllocation(cpu_cores=1.0, memory_gb=2.0),
                    queues=["default"]
                ),
                "worker_2": WorkerInfo(
                    id="worker_2",
                    type=WorkerType.GPU,
                    status=WorkerStatus.IDLE,
                    started_at=datetime.now(),
                    resources=ResourceAllocation(cpu_cores=2.0, memory_gb=4.0, gpu_memory_gb=8.0),
                    queues=["gpu"]
                )
            }
            
            # Mock methods
            mock.get_worker_info = lambda worker_id: mock.workers.get(worker_id)
            mock.spawn_worker = AsyncMock(return_value="new_worker_id")
            mock.terminate_worker = AsyncMock(return_value=True)
            mock.get_worker_metrics = AsyncMock(return_value={
                "total_workers": 2,
                "active_workers": 1,
                "idle_workers": 1,
                "busy_workers": 0,
                "worker_types": {"general": 1, "gpu": 1, "cpu": 0, "io": 0},
                "resource_utilization": {"cpu_percent": 25.0, "memory_percent": 30.0, "gpu_percent": 50.0},
                "queue_depth": 3,
                "scaling_limits": {"min_workers": 1, "max_workers": 10, "scale_up_threshold": 5, "scale_down_threshold": 0}
            })
            mock.get_active_workers = lambda: [w for w in mock.workers.values() if w.status == WorkerStatus.ACTIVE]
            mock.get_idle_workers = lambda: [w for w in mock.workers.values() if w.status == WorkerStatus.IDLE]
            mock.get_busy_workers = lambda: [w for w in mock.workers.values() if w.status == WorkerStatus.BUSY]
            mock.min_workers = 1
            mock.max_workers = 10
            
            # Mock health checker
            mock.health_checker = AsyncMock()
            mock.health_checker.check_worker_health = AsyncMock(return_value=True)
            
            yield mock

    def test_list_workers(self, client, mock_pool_manager):
        """Test listing all workers"""
        response = client.get("/api/v1/workers/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Check worker data structure
        worker = data[0]
        assert "id" in worker
        assert "type" in worker
        assert "status" in worker
        assert "started_at" in worker
        assert "resources" in worker
        assert "queues" in worker

    def test_get_worker_metrics(self, client, mock_pool_manager):
        """Test getting worker pool metrics"""
        response = client.get("/api/v1/workers/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_workers"] == 2
        assert data["active_workers"] == 1
        assert data["idle_workers"] == 1
        assert "resource_utilization" in data
        assert "queue_depth" in data

    def test_get_worker_info_success(self, client, mock_pool_manager):
        """Test getting specific worker info"""
        response = client.get("/api/v1/workers/worker_1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "worker_1"
        assert data["type"] == "general"
        assert data["status"] == "active"

    def test_get_worker_info_not_found(self, client, mock_pool_manager):
        """Test getting info for nonexistent worker"""
        response = client.get("/api/v1/workers/nonexistent")
        assert response.status_code == 404

    def test_spawn_worker_success(self, client, mock_pool_manager):
        """Test spawning a new worker"""
        response = client.post("/api/v1/workers/spawn?worker_type=gpu")
        assert response.status_code == 200
        
        data = response.json()
        assert "worker_id" in data
        assert data["worker_id"] == "new_worker_id"
        mock_pool_manager.spawn_worker.assert_called_once_with(WorkerType.GPU)

    def test_spawn_worker_failure(self, client, mock_pool_manager):
        """Test spawning worker when it fails"""
        mock_pool_manager.spawn_worker.return_value = None
        
        response = client.post("/api/v1/workers/spawn?worker_type=cpu")
        assert response.status_code == 400

    def test_scale_workers_up(self, client, mock_pool_manager):
        """Test scaling workers up"""
        payload = {"worker_type": "general", "action": "scale_up", "count": 2}
        response = client.post("/api/v1/workers/scale", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["action"] == "scale_up"
        assert data["spawned_count"] == 2
        assert len(data["worker_ids"]) == 2

    def test_scale_workers_down(self, client, mock_pool_manager):
        """Test scaling workers down"""
        payload = {"worker_type": "general", "action": "scale_down", "count": 1}
        response = client.post("/api/v1/workers/scale", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["action"] == "scale_down"
        assert data["terminated_count"] == 1

    def test_scale_workers_invalid_action(self, client, mock_pool_manager):
        """Test scaling with invalid action"""
        payload = {"worker_type": "general", "action": "invalid", "count": 1}
        response = client.post("/api/v1/workers/scale", json=payload)
        assert response.status_code == 400

    def test_terminate_worker_success(self, client, mock_pool_manager):
        """Test terminating a specific worker"""
        response = client.delete("/api/v1/workers/worker_1?graceful=true")
        assert response.status_code == 200
        
        data = response.json()
        assert "Successfully terminated" in data["message"]
        mock_pool_manager.terminate_worker.assert_called_once_with("worker_1", True)

    def test_terminate_worker_not_found(self, client, mock_pool_manager):
        """Test terminating nonexistent worker"""
        response = client.delete("/api/v1/workers/nonexistent")
        assert response.status_code == 404

    def test_terminate_worker_min_constraint(self, client, mock_pool_manager):
        """Test terminating worker when it would violate minimum constraint"""
        # Mock only one worker and min_workers = 1
        mock_pool_manager.workers = {"worker_1": mock_pool_manager.workers["worker_1"]}
        
        response = client.delete("/api/v1/workers/worker_1")
        assert response.status_code == 400
        response_data = response.json()
        # Check the error structure from the middleware
        assert "error" in response_data
        assert "minimum worker count" in response_data["error"]["message"]

    def test_check_worker_health(self, client, mock_pool_manager):
        """Test worker health check"""
        response = client.post("/api/v1/workers/worker_1/health-check")
        assert response.status_code == 200
        
        data = response.json()
        assert data["worker_id"] == "worker_1"
        assert data["healthy"] is True

    def test_get_queue_status(self, client, mock_pool_manager):
        """Test getting queue status"""
        response = client.get("/api/v1/workers/queues/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "queues" in data
        assert "total_queued_tasks" in data
        assert "total_consumers" in data

    def test_get_worker_types(self, client, mock_pool_manager):
        """Test getting available worker types"""
        # Mock the resource monitor and queue methods on the mock pool manager
        mock_pool_manager.resource_monitor._get_requirements.return_value = ResourceAllocation(cpu_cores=2.0, memory_gb=4.0)
        mock_pool_manager._get_queues_for_type.return_value = ["default"]
        
        response = client.get("/api/v1/workers/types")
        assert response.status_code == 200
        
        data = response.json()
        assert "general" in data
        assert "gpu" in data
        assert "cpu" in data
        assert "io" in data
        
        # Check structure of worker type info
        general_info = data["general"]
        assert "type" in general_info
        assert "resource_requirements" in general_info
        assert "queues" in general_info
        assert "description" in general_info


if __name__ == "__main__":
    pytest.main([__file__])