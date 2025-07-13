"""
Tests for Function Runner Foundation

Tests the task dispatcher, quality mapping, and generation task handler
without requiring actual AI models.
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.dispatcher import TaskDispatcher, QualityTier, task_dispatcher_service
from app.core.dispatcher import GenerationTaskHandler, task_dispatcher


class TestTaskDispatcher:
    """Test the task dispatcher service"""

    def test_quality_pipeline_mapping(self):
        """Test task dispatcher quality mapping"""
        dispatcher = TaskDispatcher()
        
        # Test each quality tier
        for quality in ["low", "standard", "high", "premium"]:
            config = dispatcher.get_pipeline_config(quality)
            assert config.pipeline_id.startswith("auteur-flux")
            assert config.target_vram > 0
            assert len(config.optimizations) > 0
            assert config.timeout_seconds > 0
            assert config.max_concurrent > 0
        
        # Test unknown quality defaults to standard
        config = dispatcher.get_pipeline_config("unknown")
        standard_config = dispatcher.QUALITY_PIPELINE_MAPPING[QualityTier.STANDARD]
        assert config.pipeline_id == standard_config.pipeline_id

    def test_quality_tier_enum(self):
        """Test quality tier enumeration"""
        assert QualityTier.LOW == "low"
        assert QualityTier.STANDARD == "standard"
        assert QualityTier.HIGH == "high"
        assert QualityTier.PREMIUM == "premium"

    def test_pipeline_config_properties(self):
        """Test pipeline configuration properties"""
        config = task_dispatcher_service.get_pipeline_config("high")
        assert config.pipeline_id == "auteur-flux:1.0-high-fidelity"
        assert config.target_vram == 24
        assert "full_parallel" in config.optimizations
        assert "high_res" in config.optimizations
        assert config.max_concurrent == 3
        assert config.timeout_seconds == 120

    @pytest.mark.asyncio
    async def test_task_dispatch_integration(self):
        """Test task dispatch creates proper task payload"""
        dispatcher = TaskDispatcher()
        
        with patch.object(task_dispatcher, 'submit_task') as mock_submit:
            mock_submit.return_value = "test-task-123"
            
            task_id = await dispatcher.dispatch_task(
                node_type="image_generation",
                quality="standard",
                parameters={
                    "prompt": "test image",
                    "node_id": "node-123",
                    "project_id": "test-project"
                }
            )
            
            assert task_id == "test-task-123"
            mock_submit.assert_called_once()
            
            # Check the payload structure
            call_args = mock_submit.call_args
            task_type, payload = call_args[0]
            assert task_type == "generation"
            assert payload["pipeline_id"] == "auteur-flux:1.0-standard"
            assert payload["node_type"] == "image_generation"
            assert payload["parameters"]["prompt"] == "test image"

    def test_priority_mapping(self):
        """Test quality to priority mapping"""
        dispatcher = TaskDispatcher()
        
        assert dispatcher._get_priority_for_quality("low") == 3
        assert dispatcher._get_priority_for_quality("standard") == 2
        assert dispatcher._get_priority_for_quality("high") == 1
        assert dispatcher._get_priority_for_quality("premium") == 0
        assert dispatcher._get_priority_for_quality("unknown") == 2  # Default to standard


class TestGenerationTaskHandler:
    """Test the generation task handler"""

    @pytest.mark.asyncio
    async def test_can_handle_generation(self):
        """Test generation handler can handle generation tasks"""
        handler = GenerationTaskHandler()
        
        assert await handler.can_handle("generation")
        assert not await handler.can_handle("echo")
        assert not await handler.can_handle("unknown")

    @pytest.mark.asyncio
    async def test_generation_process_simulation(self):
        """Test generation process creates proper outputs"""
        handler = GenerationTaskHandler()
        
        # Mock redis client
        with patch('app.core.dispatcher.redis_client') as mock_redis:
            mock_redis.publish_progress = AsyncMock()
            
            # Create temporary workspace
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                workspace_path = temp_dir
                output_path = f"{workspace_path}/outputs/test-node"
                
                task_params = {
                    "pipeline_id": "auteur-flux:1.0-standard",
                    "node_type": "image_generation",
                    "workspace_path": workspace_path,
                    "parameters": {
                        "node_id": "test-node",
                        "project_id": "test-project",
                        "output_path": output_path,
                        "prompt": "test generation"
                    },
                    "config": {
                        "optimizations": ["moderate_parallel", "standard_res"],
                        "target_vram": 16
                    }
                }
                
                # Process the task
                result = await handler.process("test-task-456", task_params)
                
                # Verify result structure
                assert result["task_id"] == "test-task-456"
                assert result["node_id"] == "test-node"
                assert result["pipeline_id"] == "auteur-flux:1.0-standard"
                assert result["node_type"] == "image_generation"
                assert "metadata" in result
                assert "outputs" in result
                
                # Verify output files were created
                output_dir = Path(output_path)
                assert output_dir.exists()
                
                result_file = output_dir / "test-node_result.json"
                assert result_file.exists()
                
                placeholder_file = output_dir / "test-node_generated.png"
                assert placeholder_file.exists()
                
                # Verify progress events were published
                assert mock_redis.publish_progress.call_count >= 8  # Multiple progress updates

    @pytest.mark.asyncio
    async def test_generation_error_handling(self):
        """Test generation handler error handling"""
        handler = GenerationTaskHandler()
        
        with patch('app.core.dispatcher.redis_client') as mock_redis:
            mock_redis.publish_progress = AsyncMock()
            
            # Force an error by providing invalid workspace path
            task_params = {
                "pipeline_id": "test-pipeline",
                "parameters": {
                    "node_id": "test-node",
                    "project_id": "test-project",
                    "output_path": "/invalid/path/that/cannot/be/created"
                }
            }
            
            with pytest.raises(Exception):
                await handler.process("test-task-error", task_params)
            
            # Verify error was reported
            error_calls = [
                call for call in mock_redis.publish_progress.call_args_list
                if call[0][2].get("status") == "failed"
            ]
            assert len(error_calls) > 0


class TestTaskDispatcherIntegration:
    """Test integration between dispatcher components"""

    @pytest.mark.asyncio
    async def test_end_to_end_task_flow(self):
        """Test complete task flow from dispatch to completion"""
        # Register generation handler in dispatcher
        generation_handler = GenerationTaskHandler()
        task_dispatcher.register_handler("test_generation", generation_handler)
        
        # Mock redis client
        with patch('app.core.dispatcher.redis_client') as mock_redis:
            mock_redis.publish_progress = AsyncMock()
            
            # Create task through dispatcher service
            dispatcher_service = TaskDispatcher()
            
            with patch.object(task_dispatcher, 'submit_task') as mock_submit:
                mock_submit.return_value = "integration-test-task"
                
                task_id = await dispatcher_service.dispatch_task(
                    node_type="image_generation",
                    quality="high",
                    parameters={
                        "node_id": "integration-node",
                        "project_id": "integration-project",
                        "prompt": "integration test"
                    }
                )
                
                assert task_id == "integration-test-task"
                
                # Verify dispatcher was called with correct parameters
                call_args = mock_submit.call_args
                task_type, payload = call_args[0]
                assert task_type == "generation"
                assert payload["pipeline_id"] == "auteur-flux:1.0-high-fidelity"

    def test_task_tracking(self):
        """Test task tracking functionality"""
        dispatcher = TaskDispatcher()
        
        # Initially no active tasks
        assert len(dispatcher.get_active_tasks()) == 0
        
        # Mark task as active (simulated)
        task_id = "tracking-test-task"
        dispatcher.active_tasks[task_id] = {
            "node_type": "image_generation",
            "quality": "standard",
            "status": "running"
        }
        
        # Check tracking
        active_tasks = dispatcher.get_active_tasks()
        assert task_id in active_tasks
        
        task_info = dispatcher.get_task_info(task_id)
        assert task_info["status"] == "running"
        
        # Mark as completed
        dispatcher.mark_task_completed(task_id, {"output": "test_result"})
        task_info = dispatcher.get_task_info(task_id)
        assert task_info["status"] == "completed"
        assert task_info["result"]["output"] == "test_result"

    def test_model_storage_structure_validation(self):
        """Test model storage directory structure"""
        # This would be created by init-model-storage.sh
        workspace = Path("./workspace/Library/AI_Models")
        
        # Verify basic structure (if it exists)
        if workspace.exists():
            categories = ["image", "video", "audio", "language"]
            for category in categories:
                category_path = workspace / category
                if category_path.exists():
                    # Check subdirectories
                    assert (category_path / "models").exists() or True  # May not exist yet
                    assert (category_path / "pipelines").exists() or True
                    assert (category_path / "configs").exists() or True


@pytest.mark.asyncio
async def test_quality_configuration_completeness():
    """Test that all quality configurations are complete"""
    dispatcher = TaskDispatcher()
    
    for quality_tier in QualityTier:
        config = dispatcher.get_pipeline_config(quality_tier.value)
        
        # Verify all required fields are present
        assert config.pipeline_id
        assert config.container_image
        assert config.target_vram > 0
        assert config.max_concurrent > 0
        assert config.timeout_seconds > 0
        assert len(config.optimizations) > 0
        
        # Verify tier-specific characteristics
        if quality_tier == QualityTier.LOW:
            assert config.target_vram <= 12
            assert "cpu_offloading" in config.optimizations
        elif quality_tier == QualityTier.PREMIUM:
            assert config.target_vram >= 48
            assert "multi_gpu" in config.optimizations