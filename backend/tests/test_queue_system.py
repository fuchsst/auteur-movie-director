"""
Tests for Task Queue Configuration System
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.worker.queues import (
    TaskRouter, TaskDeduplicator, QueueHealthChecker,
    QUEUE_CONFIGS, create_queues
)
from app.worker.dead_letter_queue import (
    DeadLetterQueueHandler, BackoffConfig, RetryPolicy, BackoffStrategy
)
from app.worker.queue_monitor import QueueMonitor, QueueMetrics, AlertConfig


class TestTaskRouter:
    """Test intelligent task routing"""
    
    def setup_method(self):
        """Setup test environment"""
        self.router = TaskRouter()
    
    def test_route_by_task_name_pattern(self):
        """Test routing based on task name patterns"""
        # GPU generation tasks
        route = self.router.route_task('generate_image', [], {}, {})
        assert route['queue'] == 'gpu.generation'
        
        route = self.router.route_task('create_comfyui_workflow', [], {}, {})
        assert route['queue'] == 'gpu.generation'
        
        # GPU processing tasks
        route = self.router.route_task('apply_style_transfer', [], {}, {})
        assert route['queue'] == 'gpu.processing'
        
        # CPU analysis tasks
        route = self.router.route_task('analyze_scene', [], {}, {})
        assert route['queue'] == 'cpu.analysis'
        
        # CPU thumbnail tasks
        route = self.router.route_task('generate_thumbnail', [], {}, {})
        assert route['queue'] == 'cpu.thumbnail'
        
        # IO storage tasks
        route = self.router.route_task('save_to_storage', [], {}, {})
        assert route['queue'] == 'io.storage'
    
    def test_route_by_resource_requirements(self):
        """Test routing based on resource requirements"""
        # High VRAM requirement -> GPU generation
        route = self.router.route_task('custom_task', [], {
            'resource_requirements': {'gpu': True, 'vram_gb': 12}
        }, {})
        assert route['queue'] == 'gpu.generation'
        
        # Low VRAM requirement -> GPU processing
        route = self.router.route_task('custom_task', [], {
            'resource_requirements': {'gpu': True, 'vram_gb': 4}
        }, {})
        assert route['queue'] == 'gpu.processing'
        
        # CPU intensive -> CPU analysis
        route = self.router.route_task('custom_task', [], {
            'resource_requirements': {'cpu_intensive': True}
        }, {})
        assert route['queue'] == 'cpu.analysis'
        
        # IO intensive -> IO storage
        route = self.router.route_task('custom_task', [], {
            'resource_requirements': {'io_intensive': True}
        }, {})
        assert route['queue'] == 'io.storage'
    
    def test_priority_task_routing(self):
        """Test priority task routing"""
        route = self.router.route_task('any_task', [], {'priority_task': True}, {})
        assert route['queue'] == 'priority'
        assert route['priority'] == 10
    
    def test_priority_calculation(self):
        """Test priority calculation logic"""
        # Base priority
        route = self.router.route_task('generate_image', [], {}, {})
        base_priority = route['priority']
        
        # User initiated boost
        route = self.router.route_task('generate_image', [], {'user_initiated': True}, {})
        assert route['priority'] > base_priority
        
        # Batch operation penalty
        route = self.router.route_task('generate_image', [], {'batch_operation': True}, {})
        assert route['priority'] < base_priority
        
        # Large batch size penalty
        route = self.router.route_task('generate_image', [], {'batch_size': 25}, {})
        assert route['priority'] < base_priority
    
    def test_task_name_analysis_fallback(self):
        """Test fallback task name analysis"""
        # GPU keywords
        route = self.router.route_task('my_generate_function', [], {}, {})
        assert route['queue'] == 'gpu.processing'
        
        # CPU keywords
        route = self.router.route_task('my_analyze_function', [], {}, {})
        assert route['queue'] == 'cpu.analysis'
        
        # Thumbnail keywords
        route = self.router.route_task('my_thumbnail_function', [], {}, {})
        assert route['queue'] == 'cpu.thumbnail'
        
        # IO keywords
        route = self.router.route_task('my_save_function', [], {}, {})
        assert route['queue'] == 'io.storage'
        
        # Unknown task -> default
        route = self.router.route_task('unknown_task', [], {}, {})
        assert route['queue'] == 'cpu.analysis'
    
    def test_queue_info_retrieval(self):
        """Test queue information retrieval"""
        info = self.router.get_queue_info('gpu.generation')
        assert info['name'] == 'gpu.generation'
        assert info['resource_type'] == 'gpu'
        assert info['priority'] == 10
        
        all_info = self.router.get_all_queues_info()
        assert len(all_info) == len(QUEUE_CONFIGS)
        assert 'gpu.generation' in all_info


class TestTaskDeduplicator:
    """Test task deduplication"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_redis = MagicMock()
        self.deduplicator = TaskDeduplicator(self.mock_redis, ttl=3600)
    
    def test_task_hash_generation(self):
        """Test task hash generation for deduplication"""
        hash1 = self.deduplicator.generate_task_hash(
            'test_task', 
            ('arg1', 'arg2'), 
            {'param1': 'value1', 'param2': 'value2'}
        )
        
        # Same task should generate same hash
        hash2 = self.deduplicator.generate_task_hash(
            'test_task', 
            ('arg1', 'arg2'), 
            {'param1': 'value1', 'param2': 'value2'}
        )
        assert hash1 == hash2
        
        # Different task should generate different hash
        hash3 = self.deduplicator.generate_task_hash(
            'test_task', 
            ('arg1', 'arg3'), 
            {'param1': 'value1', 'param2': 'value2'}
        )
        assert hash1 != hash3
        
        # Parameter order should not matter
        hash4 = self.deduplicator.generate_task_hash(
            'test_task', 
            ('arg1', 'arg2'), 
            {'param2': 'value2', 'param1': 'value1'}
        )
        assert hash1 == hash4
    
    def test_duplicate_detection(self):
        """Test duplicate task detection"""
        self.mock_redis.exists.return_value = True
        assert self.deduplicator.is_duplicate('some_hash') is True
        
        self.mock_redis.exists.return_value = False
        assert self.deduplicator.is_duplicate('some_hash') is False
    
    def test_task_processing_tracking(self):
        """Test task processing state tracking"""
        self.mock_redis.setex.return_value = True
        result = self.deduplicator.mark_processing('some_hash')
        assert result is True
        
        self.deduplicator.mark_completed('some_hash')
        self.mock_redis.delete.assert_called_with('task_dedupe:some_hash')


class TestBackoffStrategy:
    """Test retry backoff strategies"""
    
    def test_exponential_backoff(self):
        """Test exponential backoff calculation"""
        config = BackoffConfig(
            policy=RetryPolicy.EXPONENTIAL,
            base_delay=60,
            max_delay=3600,
            max_retries=5,
            factor=2.0,
            jitter=False
        )
        
        assert BackoffStrategy.exponential(0, config) == 60
        assert BackoffStrategy.exponential(1, config) == 120
        assert BackoffStrategy.exponential(2, config) == 240
        assert BackoffStrategy.exponential(3, config) == 480
        
        # Should respect max_delay
        assert BackoffStrategy.exponential(10, config) == 3600
    
    def test_linear_backoff(self):
        """Test linear backoff calculation"""
        config = BackoffConfig(
            policy=RetryPolicy.LINEAR,
            base_delay=30,
            max_delay=600,
            max_retries=5
        )
        
        assert BackoffStrategy.linear(0, config) == 30
        assert BackoffStrategy.linear(1, config) == 60
        assert BackoffStrategy.linear(2, config) == 90
        
        # Should respect max_delay
        assert BackoffStrategy.linear(20, config) == 600
    
    def test_fibonacci_backoff(self):
        """Test fibonacci backoff calculation"""
        config = BackoffConfig(
            policy=RetryPolicy.FIBONACCI,
            base_delay=10,
            max_delay=1000,
            max_retries=8
        )
        
        assert BackoffStrategy.fibonacci(0, config) == 10
        assert BackoffStrategy.fibonacci(1, config) == 10
        assert BackoffStrategy.fibonacci(2, config) == 20
        assert BackoffStrategy.fibonacci(3, config) == 30
        assert BackoffStrategy.fibonacci(4, config) == 50
    
    def test_fixed_backoff(self):
        """Test fixed backoff calculation"""
        config = BackoffConfig(
            policy=RetryPolicy.FIXED,
            base_delay=120,
            max_delay=3600,
            max_retries=3
        )
        
        assert BackoffStrategy.fixed(0, config) == 120
        assert BackoffStrategy.fixed(1, config) == 120
        assert BackoffStrategy.fixed(2, config) == 120


class TestDeadLetterQueueHandler:
    """Test dead letter queue handling"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_app = MagicMock()
        self.mock_redis = MagicMock()
        self.dlq_handler = DeadLetterQueueHandler(self.mock_app, self.mock_redis)
    
    def test_non_retryable_error_detection(self):
        """Test detection of non-retryable errors"""
        # Non-retryable errors
        assert self.dlq_handler._is_non_retryable_error(ValueError()) is True
        assert self.dlq_handler._is_non_retryable_error(TypeError()) is True
        assert self.dlq_handler._is_non_retryable_error(KeyError()) is True
        
        # Retryable errors
        assert self.dlq_handler._is_non_retryable_error(ConnectionError()) is False
        assert self.dlq_handler._is_non_retryable_error(TimeoutError()) is False
    
    def test_retry_policy_selection(self):
        """Test retry policy selection based on queue and task"""
        # Queue-specific policy
        config = self.dlq_handler._get_retry_policy('gpu.generation', 'any_task')
        assert config.policy == RetryPolicy.EXPONENTIAL
        assert config.base_delay == 120
        
        # Task name pattern matching
        config = self.dlq_handler._get_retry_policy(None, 'generate_image')
        assert config.policy == RetryPolicy.EXPONENTIAL
        
        config = self.dlq_handler._get_retry_policy(None, 'thumbnail_task')
        assert config.policy == RetryPolicy.FIXED
        
        # Default policy
        config = self.dlq_handler._get_retry_policy(None, 'unknown_task')
        assert config.policy == RetryPolicy.EXPONENTIAL
        assert config.base_delay == 60
    
    @patch('app.worker.dead_letter_queue.datetime')
    def test_task_failure_handling(self, mock_datetime):
        """Test task failure handling and retry scheduling"""
        # Setup mock datetime
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        # Test retryable error
        exception = ConnectionError("Network error")
        
        with patch.object(self.dlq_handler, '_schedule_retry', return_value=True) as mock_schedule:
            result = self.dlq_handler.handle_task_failure(
                task_id='test_task_id',
                task_name='test_task',
                args=['arg1', 'arg2'],
                kwargs={'param': 'value'},
                exception=exception,
                traceback='traceback here',
                queue='cpu.analysis'
            )
            
            assert result is True
            mock_schedule.assert_called_once()
    
    def test_dlq_stats_retrieval(self):
        """Test DLQ statistics retrieval"""
        # Mock Redis responses
        self.mock_redis.hgetall.side_effect = [
            {b'cpu.analysis': b'5', b'gpu.generation': b'2'},  # queue stats
            {b'ConnectionError': b'3', b'TimeoutError': b'4'}   # error stats
        ]
        self.mock_redis.get.side_effect = [b'7', b'3']  # total counts
        
        stats = self.dlq_handler.get_dlq_stats('2024-01-01')
        
        assert stats['dlq_by_queue'] == {'cpu.analysis': 5, 'gpu.generation': 2}
        assert stats['dlq_by_error'] == {'ConnectionError': 3, 'TimeoutError': 4}
        assert stats['total_dlq_entries'] == 7
        assert stats['total_permanent_failures'] == 3


class TestQueueMonitor:
    """Test queue monitoring system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_app = MagicMock()
        self.mock_redis = MagicMock()
        self.monitor = QueueMonitor(self.mock_app, self.mock_redis)
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self):
        """Test monitoring start/stop lifecycle"""
        assert self.monitor.monitoring_active is False
        
        # Start monitoring
        await self.monitor.start_monitoring(interval=0.1)
        assert self.monitor.monitoring_active is True
        
        # Let it run briefly
        await asyncio.sleep(0.2)
        
        # Stop monitoring
        await self.monitor.stop_monitoring()
        assert self.monitor.monitoring_active is False
    
    def test_processing_rate_calculation(self):
        """Test processing rate calculation"""
        # Mock Redis sorted set operations
        self.mock_redis.zremrangebyscore.return_value = 5
        self.mock_redis.zcard.return_value = 100
        
        with patch('app.worker.queue_monitor.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            rate = asyncio.run(self.monitor._calculate_processing_rate('test_queue', '1m'))
            assert rate == 100 / 60  # 100 tasks in 60 seconds
    
    def test_alert_threshold_checking(self):
        """Test alert threshold checking"""
        # Create test metrics that exceed thresholds
        metrics = QueueMetrics(
            queue_name='gpu.generation',
            depth=100,  # Exceeds threshold of 50
            processing_rate=0.5,
            completion_rate=0.4,
            error_rate=15.0,  # Exceeds threshold of 5%
            avg_processing_time=45.0,
            oldest_task_age=600,  # Exceeds threshold of 300s
            active_consumers=2,
            timestamp=datetime.now()
        )
        
        self.monitor.current_metrics['gpu.generation'] = metrics
        
        with patch.object(self.monitor, '_send_alert') as mock_alert:
            asyncio.run(self.monitor._check_alerts())
            
            # Should send 3 alerts (depth, error rate, task age)
            assert mock_alert.call_count == 3
    
    def test_queue_summary_generation(self):
        """Test queue summary generation"""
        # Setup mock metrics
        self.monitor.current_metrics = {
            'gpu.generation': QueueMetrics(
                queue_name='gpu.generation',
                depth=10,
                processing_rate=2.0,
                completion_rate=1.8,
                error_rate=2.0,
                avg_processing_time=30.0,
                oldest_task_age=120,
                active_consumers=1,
                timestamp=datetime.now()
            ),
            'cpu.analysis': QueueMetrics(
                queue_name='cpu.analysis',
                depth=25,
                processing_rate=5.0,
                completion_rate=4.5,
                error_rate=1.0,
                avg_processing_time=15.0,
                oldest_task_age=60,
                active_consumers=2,
                timestamp=datetime.now()
            )
        }
        
        summary = self.monitor.get_queue_summary()
        
        assert summary['total_queues'] == 2
        assert summary['total_depth'] == 35
        assert summary['average_error_rate'] == 1.5
        assert summary['queues_with_alerts'] == 0  # No alerts with these metrics


class TestQueueHealthChecker:
    """Test queue health checking"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_redis = MagicMock()
        self.health_checker = QueueHealthChecker(self.mock_redis)
    
    def test_queue_health_check_healthy(self):
        """Test health check for healthy queue"""
        # Mock Redis responses for healthy queue
        self.mock_redis.llen.return_value = 5  # Low depth
        
        with patch.object(self.health_checker, '_get_oldest_task_age', return_value=30):
            health = self.health_checker.check_queue_health('cpu.analysis')
            
            assert health['healthy'] is True
            assert health['depth'] == 5
            assert health['oldest_task_age'] == 30
            assert len(health['issues']) == 0
    
    def test_queue_health_check_unhealthy(self):
        """Test health check for unhealthy queue"""
        # Mock Redis responses for unhealthy queue
        self.mock_redis.llen.return_value = 300  # High depth
        
        with patch.object(self.health_checker, '_get_oldest_task_age', return_value=2000):
            health = self.health_checker.check_queue_health('cpu.analysis')
            
            assert health['healthy'] is False
            assert health['depth'] == 300
            assert health['oldest_task_age'] == 2000
            assert len(health['issues']) == 2  # Depth and age issues


class TestQueueAPI:
    """Test queue management API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    @patch('app.api.endpoints.queues.task_router')
    @patch('app.api.endpoints.queues.queue_monitor')
    def test_list_queues(self, mock_monitor, mock_router):
        """Test listing all queues"""
        # Mock responses
        mock_router.get_all_queues_info.return_value = {
            'gpu.generation': {
                'name': 'gpu.generation',
                'description': 'GPU generation tasks',
                'resource_type': 'gpu',
                'priority': 10
            }
        }
        mock_monitor.get_current_metrics.return_value = {}
        
        response = self.client.get("/api/v1/queues/")
        assert response.status_code == 200
        
        data = response.json()
        assert 'queues' in data
        assert 'total_queues' in data
    
    @patch('app.api.endpoints.queues.task_router')
    def test_get_queue_info(self, mock_router):
        """Test getting specific queue information"""
        mock_router.get_queue_info.return_value = {
            'name': 'gpu.generation',
            'description': 'GPU generation tasks',
            'resource_type': 'gpu'
        }
        
        # Queue exists
        response = self.client.get("/api/v1/queues/gpu.generation")
        assert response.status_code == 200
        
        # Queue doesn't exist
        response = self.client.get("/api/v1/queues/nonexistent")
        assert response.status_code == 404
    
    @patch('app.api.endpoints.queues.task_router')
    @patch('app.api.endpoints.queues.celery_app')
    def test_submit_task(self, mock_celery, mock_router):
        """Test task submission"""
        # Mock routing and celery
        mock_router.route_task.return_value = {
            'queue': 'gpu.generation',
            'routing_key': 'gpu.generation',
            'priority': 8
        }
        mock_result = MagicMock()
        mock_result.id = 'test_task_id_123'
        mock_celery.send_task.return_value = mock_result
        
        payload = {
            'task_name': 'generate_image',
            'args': ['arg1', 'arg2'],
            'kwargs': {'param': 'value'},
            'priority': 8
        }
        
        response = self.client.post("/api/v1/queues/submit", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data['task_id'] == 'test_task_id_123'
        assert data['queue'] == 'gpu.generation'
        assert data['status'] == 'submitted'
    
    @patch('app.api.endpoints.queues.task_router')
    def test_preview_task_routing(self, mock_router):
        """Test task routing preview"""
        mock_router.route_task.return_value = {
            'queue': 'gpu.generation',
            'routing_key': 'gpu.generation',
            'priority': 8
        }
        mock_router.get_queue_info.return_value = {
            'name': 'gpu.generation',
            'description': 'GPU generation tasks'
        }
        
        response = self.client.get(
            "/api/v1/queues/routing/preview?task_name=generate_image&priority=8"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['task_name'] == 'generate_image'
        assert 'routing_info' in data
        assert 'target_queue' in data


if __name__ == "__main__":
    pytest.main([__file__])