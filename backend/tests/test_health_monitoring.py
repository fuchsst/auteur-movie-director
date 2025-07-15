"""
Tests for Worker Health Monitoring System
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.worker.health_monitor import (
    WorkerHealthMonitor, HeartbeatCheck, ResourceCheck, TaskPerformanceCheck,
    HealthCheckResult, HealthStatus, WorkerMetrics, TaskStats
)
from app.worker.metrics_collector import MetricsCollector


class TestHealthChecks:
    """Test individual health check implementations"""
    
    @pytest.mark.asyncio
    async def test_heartbeat_check_healthy(self):
        """Test heartbeat check with healthy worker"""
        check = HeartbeatCheck()
        
        # Mock Redis response with recent heartbeat
        with patch.object(check.redis, 'get') as mock_get:
            mock_get.return_value = datetime.now().isoformat()
            
            result = await check.execute('worker-1')
            
            assert result.status == HealthStatus.HEALTHY
            assert "normal" in result.message.lower()
            assert result.metrics['last_heartbeat_seconds'] < 30
    
    @pytest.mark.asyncio
    async def test_heartbeat_check_warning(self):
        """Test heartbeat check with delayed heartbeat"""
        check = HeartbeatCheck()
        
        # Mock Redis response with old heartbeat (45 seconds ago)
        with patch.object(check.redis, 'get') as mock_get:
            old_time = datetime.now() - timedelta(seconds=45)
            mock_get.return_value = old_time.isoformat()
            
            result = await check.execute('worker-1')
            
            assert result.status == HealthStatus.WARNING
            assert "delayed" in result.message.lower()
            assert 40 < result.metrics['last_heartbeat_seconds'] < 50
    
    @pytest.mark.asyncio
    async def test_heartbeat_check_critical(self):
        """Test heartbeat check with no recent heartbeat"""
        check = HeartbeatCheck()
        
        # Mock Redis response with very old heartbeat
        with patch.object(check.redis, 'get') as mock_get:
            old_time = datetime.now() - timedelta(seconds=120)
            mock_get.return_value = old_time.isoformat()
            
            result = await check.execute('worker-1')
            
            assert result.status == HealthStatus.CRITICAL
            assert "No heartbeat" in result.message
            assert result.metrics['last_heartbeat_seconds'] > 60
    
    @pytest.mark.asyncio
    async def test_resource_check_healthy(self):
        """Test resource check with healthy metrics"""
        check = ResourceCheck()
        
        # Mock healthy metrics
        healthy_metrics = WorkerMetrics(
            cpu_percent=45.0,
            memory_percent=60.0,
            memory_mb=4096.0,
            disk_usage_percent=70.0,
            gpu_memory_percent=50.0,
            gpu_utilization=40.0
        )
        
        with patch.object(check, 'get_worker_metrics', return_value=healthy_metrics):
            result = await check.execute('worker-1')
            
            assert result.status == HealthStatus.HEALTHY
            assert "normal" in result.message.lower()
            assert result.metrics['cpu_percent'] == 45.0
            assert result.metrics['memory_percent'] == 60.0
    
    @pytest.mark.asyncio
    async def test_resource_check_warning(self):
        """Test resource check with high resource usage"""
        check = ResourceCheck()
        
        # Mock high resource usage
        high_metrics = WorkerMetrics(
            cpu_percent=87.0,
            memory_percent=88.0,
            memory_mb=7168.0,
            disk_usage_percent=92.0,
            gpu_memory_percent=93.0,
            gpu_utilization=85.0
        )
        
        with patch.object(check, 'get_worker_metrics', return_value=high_metrics):
            result = await check.execute('worker-1')
            
            assert result.status == HealthStatus.WARNING
            assert "High" in result.message
            assert result.metrics['cpu_percent'] == 87.0
    
    @pytest.mark.asyncio
    async def test_resource_check_critical(self):
        """Test resource check with critical resource usage"""
        check = ResourceCheck()
        
        # Mock critical resource usage
        critical_metrics = WorkerMetrics(
            cpu_percent=98.0,
            memory_percent=96.0,
            memory_mb=8000.0,
            disk_usage_percent=98.0,
            gpu_memory_percent=97.0,
            gpu_utilization=95.0
        )
        
        with patch.object(check, 'get_worker_metrics', return_value=critical_metrics):
            result = await check.execute('worker-1')
            
            assert result.status == HealthStatus.CRITICAL
            assert "Critical" in result.message
    
    @pytest.mark.asyncio
    async def test_task_performance_check_healthy(self):
        """Test task performance check with good metrics"""
        check = TaskPerformanceCheck()
        
        # Mock good task stats
        good_stats = TaskStats(
            total=100,
            completed=95,
            failed=2,
            in_progress=3,
            total_duration=950.0,  # 10s average
            expected_duration=30.0,
            throughput=20.0
        )
        
        with patch.object(check, 'get_task_stats', return_value=good_stats):
            result = await check.execute('worker-1')
            
            assert result.status == HealthStatus.HEALTHY
            assert "normal" in result.message.lower()
            assert result.metrics['error_rate'] < 0.05  # < 5%
            assert result.metrics['avg_duration_seconds'] == 10.0
    
    @pytest.mark.asyncio
    async def test_task_performance_check_high_error_rate(self):
        """Test task performance check with high error rate"""
        check = TaskPerformanceCheck()
        
        # Mock high error rate
        bad_stats = TaskStats(
            total=100,
            completed=75,
            failed=25,
            in_progress=0,
            total_duration=750.0,
            expected_duration=30.0,
            throughput=15.0
        )
        
        with patch.object(check, 'get_task_stats', return_value=bad_stats):
            result = await check.execute('worker-1')
            
            assert result.status == HealthStatus.CRITICAL
            assert "error rate" in result.message.lower()
            assert result.metrics['error_rate'] == 0.25  # 25%


class TestHealthMonitor:
    """Test WorkerHealthMonitor functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.monitor = WorkerHealthMonitor(check_interval=5)
    
    @pytest.mark.asyncio
    async def test_calculate_health_score(self):
        """Test health score calculation"""
        # All healthy
        results = [
            HealthCheckResult('heartbeat', HealthStatus.HEALTHY, 'OK', {}),
            HealthCheckResult('resources', HealthStatus.HEALTHY, 'OK', {}),
            HealthCheckResult('task_performance', HealthStatus.HEALTHY, 'OK', {})
        ]
        score = self.monitor.calculate_health_score(results)
        assert score > 0.9
        
        # Mixed health
        results = [
            HealthCheckResult('heartbeat', HealthStatus.HEALTHY, 'OK', {}),
            HealthCheckResult('resources', HealthStatus.WARNING, 'High CPU', {}),
            HealthCheckResult('task_performance', HealthStatus.CRITICAL, 'High errors', {})
        ]
        score = self.monitor.calculate_health_score(results)
        assert 0.4 < score < 0.7
        
        # All critical
        results = [
            HealthCheckResult('heartbeat', HealthStatus.CRITICAL, 'No heartbeat', {}),
            HealthCheckResult('resources', HealthStatus.CRITICAL, 'Out of memory', {}),
            HealthCheckResult('task_performance', HealthStatus.ERROR, 'Check failed', {})
        ]
        score = self.monitor.calculate_health_score(results)
        assert score < 0.3
    
    @pytest.mark.asyncio
    async def test_run_health_checks(self):
        """Test running all health checks"""
        # Mock health checks
        mock_checks = [
            MagicMock(name='check1', execute=AsyncMock(return_value=HealthCheckResult(
                'check1', HealthStatus.HEALTHY, 'OK', {}
            ))),
            MagicMock(name='check2', execute=AsyncMock(return_value=HealthCheckResult(
                'check2', HealthStatus.WARNING, 'Warning', {}
            )))
        ]
        
        self.monitor.health_checks = mock_checks
        results = await self.monitor.run_health_checks('worker-1')
        
        assert len(results) == 2
        assert results[0].status == HealthStatus.HEALTHY
        assert results[1].status == HealthStatus.WARNING
        
        # Verify all checks were called
        for check in mock_checks:
            check.execute.assert_called_once_with('worker-1')
    
    @pytest.mark.asyncio
    async def test_handle_unhealthy_worker(self):
        """Test handling of unhealthy worker"""
        critical_results = [
            HealthCheckResult('heartbeat', HealthStatus.CRITICAL, 'No heartbeat', {}),
            HealthCheckResult('resources', HealthStatus.WARNING, 'High CPU', {})
        ]
        
        with patch.object(self.monitor, 'send_health_alert') as mock_alert:
            with patch('app.worker.health_monitor.worker_pool_manager') as mock_pool:
                mock_pool.restart_worker = AsyncMock()
                
                await self.monitor.handle_unhealthy_worker(
                    'worker-1', critical_results, 0.3
                )
                
                # Should restart worker due to heartbeat failure
                mock_pool.restart_worker.assert_called_once_with('worker-1')
                
                # Should send alert
                mock_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self):
        """Test start/stop monitoring lifecycle"""
        with patch('app.worker.health_monitor.worker_pool_manager') as mock_pool:
            mock_pool.get_all_workers = AsyncMock(return_value=[
                MagicMock(id='worker-1'),
                MagicMock(id='worker-2')
            ])
            
            # Start monitoring
            await self.monitor.start_monitoring()
            await asyncio.sleep(0.1)  # Let tasks start
            
            assert len(self.monitor.monitoring_tasks) == 2
            assert 'worker-1' in self.monitor.monitoring_tasks
            assert 'worker-2' in self.monitor.monitoring_tasks
            
            # Stop monitoring
            await self.monitor.stop_monitoring()
            
            assert len(self.monitor.monitoring_tasks) == 0


class TestMetricsCollector:
    """Test metrics collection functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.collector = MetricsCollector()
    
    @pytest.mark.asyncio
    async def test_update_worker_health_metrics(self):
        """Test updating Prometheus metrics from health results"""
        results = [
            HealthCheckResult('resources', HealthStatus.HEALTHY, 'OK', {
                'cpu_percent': 45.0,
                'memory_mb': 4096.0,
                'gpu_memory_percent': 60.0
            }),
            HealthCheckResult('task_performance', HealthStatus.WARNING, 'Slow', {
                'in_progress_tasks': 5,
                'error_rate': 0.05
            })
        ]
        
        await self.collector.update_worker_health('worker-1', 0.85, results)
        
        # Verify metrics were updated (would need to check Prometheus registry)
        # In real tests, we'd verify the actual metric values
    
    def test_record_task_metrics(self):
        """Test recording task execution metrics"""
        # Start task
        self.collector.record_task_start('worker-1', 'generate_image')
        
        # Complete task
        self.collector.record_task_complete(
            'worker-1', 'generate_image', 
            duration_seconds=45.3, success=True
        )
        
        # Record error
        self.collector.record_task_error(
            'worker-1', 'generate_image', 'OutOfMemoryError'
        )
        
        # Verify counters incremented (would check Prometheus metrics)
    
    def test_generate_metrics(self):
        """Test generating Prometheus format metrics"""
        metrics_data = self.collector.generate_metrics()
        
        assert isinstance(metrics_data, bytes)
        assert b'auteur_worker_health_score' in metrics_data
        assert b'auteur_task_total' in metrics_data


class TestHealthMonitorAPI:
    """Test health monitoring API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    @patch('app.api.endpoints.health_monitor.worker_health_monitor')
    @patch('app.api.endpoints.health_monitor.worker_pool_manager')
    async def test_get_worker_health_summary(self, mock_pool, mock_monitor):
        """Test getting health summary for all workers"""
        # Mock data
        mock_monitor.get_all_workers_health.return_value = {
            'worker-1': {
                'health_score': 0.95,
                'timestamp': datetime.now().isoformat(),
                'checks': [
                    {
                        'check_name': 'heartbeat',
                        'status': 'healthy',
                        'message': 'OK',
                        'metrics': {}
                    }
                ]
            }
        }
        
        mock_pool.get_all_workers = AsyncMock(return_value=[
            MagicMock(id='worker-1'),
            MagicMock(id='worker-2')  # No health data
        ])
        
        response = self.client.get("/api/v1/health/workers")
        assert response.status_code == 200
        
        data = response.json()
        assert data['total_workers'] == 2
        assert data['healthy_workers'] == 1
        assert data['unknown_workers'] == 1
    
    @patch('app.api.endpoints.health_monitor.worker_health_monitor')
    def test_get_worker_health_details(self, mock_monitor):
        """Test getting detailed health for specific worker"""
        mock_monitor.get_worker_health.return_value = {
            'worker_id': 'worker-1',
            'health_score': 0.85,
            'timestamp': datetime.now().isoformat(),
            'checks': [
                {
                    'check_name': 'resources',
                    'status': 'warning',
                    'message': 'High CPU',
                    'metrics': {'cpu_percent': 87.0}
                }
            ]
        }
        
        response = self.client.get("/api/v1/health/workers/worker-1")
        assert response.status_code == 200
        
        data = response.json()
        assert data['worker_id'] == 'worker-1'
        assert data['health_score'] == 0.85
        assert data['overall_status'] == 'healthy'  # 0.85 >= 0.8
        assert len(data['checks']) == 1
    
    def test_get_prometheus_metrics(self):
        """Test Prometheus metrics endpoint"""
        response = self.client.get("/api/v1/health/metrics")
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('text/plain')
        assert b'auteur_' in response.content  # Check for metric prefix
    
    @patch('app.api.endpoints.health_monitor.worker_pool_manager')
    async def test_restart_worker(self, mock_pool):
        """Test worker restart endpoint"""
        mock_pool.get_worker = AsyncMock(return_value=MagicMock(id='worker-1'))
        mock_pool.restart_worker = AsyncMock(return_value=True)
        
        response = self.client.post(
            "/api/v1/health/workers/worker-1/restart",
            json={"reason": "manual_restart", "force": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'restart initiated' in data['message']
        
        mock_pool.restart_worker.assert_called_once_with('worker-1', force=False)


if __name__ == "__main__":
    pytest.main([__file__])