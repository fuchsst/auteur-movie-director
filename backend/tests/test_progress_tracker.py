"""Tests for progress tracking system"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from redis import asyncio as aioredis

from app.progress import (
    ProgressTracker, StageManager, ETAPredictor,
    TaskProgress, StageStatus, TaskStatus
)
from app.services.websocket import WebSocketManager


@pytest.fixture
async def redis_mock():
    """Mock Redis client"""
    redis = AsyncMock(spec=aioredis.Redis)
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def ws_manager_mock():
    """Mock WebSocket manager"""
    ws_manager = Mock(spec=WebSocketManager)
    ws_manager.broadcast = AsyncMock()
    return ws_manager


@pytest.fixture
async def progress_tracker(redis_mock, ws_manager_mock):
    """Create progress tracker instance"""
    return ProgressTracker(redis_mock, ws_manager_mock)


class TestProgressTracker:
    """Test ProgressTracker functionality"""
    
    async def test_create_task_progress(self, progress_tracker):
        """Test creating new task progress"""
        task_id = "test-task-123"
        template_id = "image-gen-v1"
        
        progress = await progress_tracker.create_task_progress(
            task_id=task_id,
            template_id=template_id,
            template_category='image_generation'
        )
        
        assert progress.task_id == task_id
        assert progress.template_id == template_id
        assert progress.status == TaskStatus.QUEUED
        assert progress.current_stage == 0
        assert progress.total_stages == 4  # Image generation has 4 stages
        assert len(progress.stages) == 4
        assert progress.overall_progress == 0.0
    
    async def test_update_stage_progress(self, progress_tracker):
        """Test updating stage progress"""
        # Create task
        task_id = "test-task-456"
        progress = await progress_tracker.create_task_progress(
            task_id=task_id,
            template_id="test-template",
            template_category='default'
        )
        
        # Update first stage to in progress
        await progress_tracker.update_stage(
            task_id=task_id,
            stage=0,
            status=StageStatus.IN_PROGRESS,
            progress=0.5,
            message="Processing queue"
        )
        
        # Verify update
        updated = await progress_tracker.get_progress(task_id)
        assert updated.stages[0].status == StageStatus.IN_PROGRESS
        assert updated.stages[0].progress == 0.5
        assert updated.stages[0].message == "Processing queue"
        assert updated.status == TaskStatus.QUEUED
        assert updated.started_at is not None
    
    async def test_stage_completion(self, progress_tracker):
        """Test completing stages"""
        task_id = "test-task-789"
        await progress_tracker.create_task_progress(
            task_id=task_id,
            template_id="test-template",
            template_category='default'
        )
        
        # Complete all stages
        for stage in range(4):
            await progress_tracker.update_stage(
                task_id=task_id,
                stage=stage,
                status=StageStatus.IN_PROGRESS,
                progress=1.0
            )
            await progress_tracker.update_stage(
                task_id=task_id,
                stage=stage,
                status=StageStatus.COMPLETED
            )
        
        # Verify completion
        progress = await progress_tracker.get_progress(task_id)
        assert progress.status == TaskStatus.COMPLETED
        assert progress.overall_progress == pytest.approx(100.0)
        assert progress.completed_at is not None
    
    async def test_stage_failure(self, progress_tracker):
        """Test handling stage failures"""
        task_id = "test-task-fail"
        await progress_tracker.create_task_progress(
            task_id=task_id,
            template_id="test-template"
        )
        
        # Fail second stage
        await progress_tracker.update_stage(
            task_id=task_id,
            stage=1,
            status=StageStatus.FAILED,
            message="Model loading failed"
        )
        
        progress = await progress_tracker.get_progress(task_id)
        assert progress.status == TaskStatus.FAILED
        assert progress.error == "Model loading failed"
    
    async def test_resource_usage_update(self, progress_tracker):
        """Test updating resource usage"""
        task_id = "test-task-resources"
        await progress_tracker.create_task_progress(
            task_id=task_id,
            template_id="test-template"
        )
        
        resources = {
            'cpu_percent': 75.5,
            'memory_mb': 2048,
            'gpu_percent': 90.0,
            'gpu_memory_mb': 4096
        }
        
        await progress_tracker.update_resource_usage(task_id, resources)
        
        progress = await progress_tracker.get_progress(task_id)
        assert progress.resource_usage == resources
    
    async def test_batch_progress_aggregation(self, progress_tracker):
        """Test batch progress calculation"""
        batch_id = "batch-123"
        task_ids = []
        
        # Create multiple tasks
        for i in range(3):
            task_id = f"batch-task-{i}"
            task_ids.append(task_id)
            await progress_tracker.create_task_progress(
                task_id=task_id,
                template_id="test-template"
            )
        
        # Update tasks to different states
        await progress_tracker.update_stage(task_ids[0], 0, StageStatus.COMPLETED)
        await progress_tracker.update_stage(task_ids[0], 1, StageStatus.COMPLETED)
        
        await progress_tracker.update_stage(task_ids[1], 0, StageStatus.COMPLETED)
        await progress_tracker.update_stage(task_ids[1], 1, StageStatus.IN_PROGRESS, progress=0.5)
        
        # Get batch progress
        batch_progress = await progress_tracker.get_batch_progress(batch_id, task_ids)
        
        assert batch_progress.total_tasks == 3
        assert batch_progress.completed_tasks == 0
        assert batch_progress.failed_tasks == 0
        assert 0 < batch_progress.overall_progress < 100


class TestStageManager:
    """Test StageManager functionality"""
    
    def test_get_stages_for_template(self):
        """Test getting stages for different template types"""
        # Test default stages
        stages = StageManager.get_stages_for_template("test", "default")
        assert len(stages) == 4
        assert stages[0].name == "queue"
        
        # Test image generation stages
        stages = StageManager.get_stages_for_template("img-gen", "image_generation")
        assert len(stages) == 4
        assert stages[2].name == "generation"
        assert stages[2].weight == 0.70
        
        # Test video generation stages
        stages = StageManager.get_stages_for_template("vid-gen", "video_generation")
        assert stages[2].name == "frame_generation"
        assert stages[2].weight == 0.80
    
    def test_calculate_stage_weights(self):
        """Test stage weight calculation"""
        stages = [
            Stage("stage1", "Stage 1", weight=0.1),
            Stage("stage2", "Stage 2", weight=0.6),
            Stage("stage3", "Stage 3", weight=0.3)
        ]
        
        weights = StageManager.calculate_stage_weights(stages)
        
        assert weights[0] == 0.1
        assert weights[1] == 0.6
        assert weights[2] == 0.3
        assert sum(weights.values()) == pytest.approx(1.0)
    
    def test_custom_template_stages(self):
        """Test registering custom stages for a template"""
        custom_stages = [
            Stage("custom1", "Custom Stage 1", weight=0.5),
            Stage("custom2", "Custom Stage 2", weight=0.5)
        ]
        
        StageManager.register_template_stages("custom-template", custom_stages)
        
        stages = StageManager.get_stages_for_template("custom-template")
        assert len(stages) == 2
        assert stages[0].name == "custom1"


class TestETAPredictor:
    """Test ETA prediction functionality"""
    
    async def test_simple_estimate(self):
        """Test ETA calculation without historical data"""
        predictor = ETAPredictor()
        
        eta = await predictor.predict(
            template_id="test-template",
            current_stage=1,
            stage_progress=0.5,
            total_stages=4,
            quality='standard',
            historical_data=[]
        )
        
        assert eta is not None
        assert eta > datetime.now()
        assert eta < datetime.now() + timedelta(minutes=10)
    
    async def test_historical_prediction(self):
        """Test ETA with historical data"""
        predictor = ETAPredictor()
        
        # Create historical data
        from app.progress.models import TaskHistory
        historical_data = [
            TaskHistory(
                task_id=f"hist-{i}",
                template_id="test-template",
                quality='standard',
                stage_durations={0: 5, 1: 30, 2: 120, 3: 20},
                total_duration=175,
                resource_config={},
                completed_at=datetime.now() - timedelta(minutes=i),
                success=True
            )
            for i in range(10)
        ]
        
        eta = await predictor.predict(
            template_id="test-template",
            current_stage=1,
            stage_progress=0.5,
            total_stages=4,
            quality='standard',
            historical_data=historical_data
        )
        
        assert eta is not None
        # Should predict approximately 15 + 120 + 20 = 155 seconds remaining
        expected_eta = datetime.now() + timedelta(seconds=155)
        assert abs((eta - expected_eta).total_seconds()) < 60  # Within 1 minute
    
    def test_percentile_calculation(self):
        """Test percentile calculation"""
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        
        assert ETAPredictor._percentile(data, 50) == 55  # Median
        assert ETAPredictor._percentile(data, 75) == 77.5  # 75th percentile
        assert ETAPredictor._percentile(data, 25) == 32.5  # 25th percentile


@pytest.mark.asyncio
async def test_progress_websocket_integration(progress_tracker, ws_manager_mock):
    """Test WebSocket progress broadcasting"""
    task_id = "ws-test-task"
    
    # Create task
    await progress_tracker.create_task_progress(
        task_id=task_id,
        template_id="test-template"
    )
    
    # Update progress
    await progress_tracker.update_stage(
        task_id=task_id,
        stage=0,
        status=StageStatus.IN_PROGRESS,
        progress=0.75
    )
    
    # Verify broadcast was called
    assert ws_manager_mock.broadcast.call_count >= 2  # Initial + update
    
    # Check broadcast message
    last_call = ws_manager_mock.broadcast.call_args[0][0]
    assert last_call['type'] == 'progress.update'
    assert last_call['task_id'] == task_id
    assert last_call['data']['overall_progress'] >= 0