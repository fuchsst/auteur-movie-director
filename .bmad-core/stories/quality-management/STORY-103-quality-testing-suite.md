# Story: STORY-103 - Quality Testing Suite

## Story Description
As a QA engineer, I need comprehensive testing for the quality tier system to ensure that quality selections map correctly to workflows and that all quality tiers produce reliable, consistent results across different task types.

## Acceptance Criteria
- [ ] Unit tests for quality tier mapping accuracy
- [ ] Integration tests for workflow execution with quality tiers
- [ ] Performance tests for different quality tiers
- [ ] Regression tests for quality parameter validation
- [ ] End-to-end tests for complete quality flow
- [ ] Test data generation for quality tiers
- [ ] Quality tier validation testing

## Technical Details

### Unit Tests for Quality Mapping
```python
# backend/tests/test_quality_mapping.py
import pytest
from app.services.quality_config_manager import QualityConfigManager
from app.services.character_quality_service import CharacterQualityService

class TestQualityMapping:
    @pytest.fixture
    def config_manager(self, tmp_path):
        config_path = tmp_path / "quality_mappings.yaml"
        return QualityConfigManager(str(config_path))
    
    def test_quality_tier_mapping_accuracy(self, config_manager):
        """Test that quality tiers map to correct workflows"""
        
        # Test character portrait mappings
        assert config_manager.get_workflow_path(
            "character_portrait", "low"
        ) == "library/image_generation/character_portrait/low_v1"
        
        assert config_manager.get_workflow_path(
            "character_portrait", "standard"
        ) == "library/image_generation/character_portrait/standard_v1"
        
        assert config_manager.get_workflow_path(
            "character_portrait", "high"
        ) == "library/image_generation/character_portrait/high_v1"
    
    def test_invalid_quality_tier_returns_none(self, config_manager):
        """Test invalid quality tier returns None"""
        
        assert config_manager.get_workflow_path(
            "character_portrait", "ultra"
        ) is None
    
    def test_invalid_task_type_returns_none(self, config_manager):
        """Test invalid task type returns None"""
        
        assert config_manager.get_workflow_path(
            "invalid_task", "standard"
        ) is None
    
    def test_available_tiers_for_task_type(self, config_manager):
        """Test getting available tiers for task type"""
        
        tiers = config_manager.get_available_tiers("character_portrait")
        assert "low" in tiers
        assert "standard" in tiers
        assert "high" in tiers
        assert len(tiers) == 3

class TestCharacterQualityService:
    @pytest.fixture
    def service(self, tmp_path):
        config_path = tmp_path / "quality_mappings.yaml"
        return CharacterQualityService(
            workflows_root=str(tmp_path),
            quality_config_manager=QualityConfigManager(str(config_path))
        )
    
    def test_character_specific_parameters(self, service):
        """Test character-specific parameter injection"""
        
        config = service.get_character_quality_config(
            "character_portrait", "standard"
        )
        
        assert config["parameters"]["width"] == 512
        assert config["parameters"]["height"] == 768
        assert "detailed face, portrait" in config["parameters"]["positive_prompt_suffix"]
    
    def test_character_type_mapping(self, service):
        """Test character type to task type mapping"""
        
        # Test that character types map to correct base task types
        with pytest.raises(ValueError):
            service.get_character_quality_config("invalid_type", "standard")
```

### Integration Tests
```python
# backend/tests/test_quality_integration.py
import pytest
import asyncio
from app.services.comfyui_quality_integration import ComfyUIQualityIntegration
from app.services.quality_config_manager import QualityConfigManager
from pathlib import Path

class TestQualityIntegration:
    @pytest.fixture
    def temp_workflows(self, tmp_path):
        """Create temporary workflow structure"""
        workflows_dir = tmp_path / "comfyui_workflows"
        
        # Create character portrait workflows
        for tier in ["low", "standard", "high"]:
            workflow_dir = workflows_dir / "library" / "image_generation" / "character_portrait" / f"{tier}_v1"
            workflow_dir.mkdir(parents=True)
            
            # Create workflow_api.json
            workflow_api = {
                "1": {
                    "class_type": "KSampler",
                    "inputs": {
                        "steps": 20 if tier == "low" else 30 if tier == "standard" else 50,
                        "cfg": 7.0,
                        "seed": 12345
                    }
                }
            }
            
            with open(workflow_dir / "workflow_api.json", "w") as f:
                import json
                json.dump(workflow_api, f)
        
        return workflows_dir
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        config_path = tmp_path / "quality_mappings.yaml"
        
        # Create test configuration
        config_data = {
            "version": "1.0",
            "mappings": {
                "character_portrait": {
                    "low": {
                        "workflow_path": "library/image_generation/character_portrait/low_v1",
                        "description": "Fast generation",
                        "parameters": {"steps": 20, "cfg_scale": 7.0}
                    },
                    "standard": {
                        "workflow_path": "library/image_generation/character_portrait/standard_v1",
                        "description": "Balanced quality",
                        "parameters": {"steps": 30, "cfg_scale": 7.0}
                    },
                    "high": {
                        "workflow_path": "library/image_generation/character_portrait/high_v1",
                        "description": "High quality",
                        "parameters": {"steps": 50, "cfg_scale": 8.0}
                    }
                }
            }
        }
        
        import yaml
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        return QualityConfigManager(str(config_path))
    
    def test_workflow_preparation(self, temp_workflows, config_manager):
        """Test workflow preparation with quality tiers"""
        
        integration = ComfyUIQualityIntegration(
            workflows_root=str(temp_workflows),
            quality_config_manager=config_manager
        )
        
        result = integration.prepare_workflow_execution(
            "character_portrait",
            "standard",
            {"positive_prompt": "test character"}
        )
        
        assert result["quality_tier"] == "standard"
        assert "workflow_api" in result
        assert result["workflow_path"] == "library/image_generation/character_portrait/standard_v1"
    
    def test_parameter_merging(self, temp_workflows, config_manager):
        """Test parameter merging with quality tier defaults"""
        
        integration = ComfyUIQualityIntegration(
            workflows_root=str(temp_workflows),
            quality_config_manager=config_manager
        )
        
        result = integration.prepare_workflow_execution(
            "character_portrait",
            "high",
            {
                "steps": 75,  # Override quality default
                "positive_prompt": "test character"
            }
        )
        
        # Check that parameters are merged correctly
        workflow = result["workflow_api"]
        sampler_node = workflow.get("1", {})
        inputs = sampler_node.get("inputs", {})
        
        assert inputs.get("steps") == 75  # User override
        assert inputs.get("cfg") == 8.0  # Quality default

@pytest.mark.asyncio
async def test_pipeline_execution():
    """Test complete pipeline execution with quality tiers"""
    
    # This would test the full pipeline integration
    # Mock implementation for testing
    pass
```

### Performance Tests
```python
# backend/tests/test_quality_performance.py
import pytest
import time
from app.services.quality_config_manager import QualityConfigManager

class TestQualityPerformance:
    
    def test_quality_tier_performance_estimates(self):
        """Test that quality tier time estimates are reasonable"""
        
        expected_times = {
            "character_portrait": {"low": 30, "standard": 60, "high": 120},
            "scene_generation": {"low": 45, "standard": 90, "high": 180},
            "video_generation": {"low": 120, "standard": 300, "high": 600}
        }
        
        for task_type, tiers in expected_times.items():
            for tier, expected_time in tiers.items():
                # Validate time ranges are realistic
                assert 10 <= expected_time <= 1200  # 10s to 20 minutes
    
    def test_parameter_validation_performance(self):
        """Test parameter validation performance"""
        
        from app.services.parameter_validator import ParameterValidator
        
        validator = ParameterValidator()
        
        start_time = time.time()
        
        # Test multiple parameter validations
        for _ in range(1000):
            test_params = {
                "steps": 30,
                "cfg_scale": 7.5,
                "width": 512,
                "height": 768,
                "positive_prompt": "test character portrait"
            }
            
            validated = validator.validate_parameters(test_params, "standard")
            assert validated["steps"] == 30
        
        elapsed = time.time() - start_time
        assert elapsed < 1.0  # Should be very fast
    
    def test_config_loading_performance(self, tmp_path):
        """Test configuration loading performance"""
        
        config_path = tmp_path / "test_config.yaml"
        
        # Create large test configuration
        import yaml
        large_config = {
            "version": "1.0",
            "mappings": {}
        }
        
        # Add 50 task types with 3 tiers each
        for i in range(50):
            task_type = f"test_task_{i}"
            large_config["mappings"][task_type] = {
                tier: {
                    "workflow_path": f"library/test/{task_type}/{tier}_v1",
                    "description": f"Test {tier} quality",
                    "parameters": {"steps": 20 if tier == "low" else 30 if tier == "standard" else 50}
                }
                for tier in ["low", "standard", "high"]
            }
        
        with open(config_path, "w") as f:
            yaml.dump(large_config, f)
        
        start_time = time.time()
        
        config_manager = QualityConfigManager(str(config_path))
        
        # Test various operations
        for i in range(10):
            task_type = f"test_task_{i}"
            workflow_path = config_manager.get_workflow_path(task_type, "standard")
            assert workflow_path is not None
        
        elapsed = time.time() - start_time
        assert elapsed < 0.1  # Should be very fast
```

### Test Data Generation
```python
# backend/tests/fixtures/quality_test_data.py
import json
import yaml
from pathlib import Path
from typing import Dict, Any

class QualityTestDataGenerator:
    """Generate test data for quality tier testing"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_workflow_structures(self):
        """Generate complete workflow structures for testing"""
        
        workflows = [
            ("character_portrait", "low", 20, 512, 768),
            ("character_portrait", "standard", 30, 512, 768),
            ("character_portrait", "high", 50, 768, 1024),
            ("scene_generation", "low", 25, 768, 512),
            ("scene_generation", "standard", 35, 1024, 576),
            ("scene_generation", "high", 60, 1280, 720),
            ("video_generation", "low", 15, 512, 512),
            ("video_generation", "standard", 25, 768, 768),
            ("video_generation", "high", 40, 1024, 1024)
        ]
        
        for task_type, tier, steps, width, height in workflows:
            workflow_dir = self.output_dir / "library" / task_type / f"{tier}_v1"
            workflow_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate workflow_api.json
            workflow_api = self._generate_workflow_api(steps, width, height)
            
            with open(workflow_dir / "workflow_api.json", "w") as f:
                json.dump(workflow_api, f, indent=2)
            
            # Generate manifest.yaml
            manifest = self._generate_manifest(task_type, tier, steps, width, height)
            
            with open(workflow_dir / "manifest.yaml", "w") as f:
                yaml.dump(manifest, f, default_flow_style=False)
    
    def generate_config_file(self):
        """Generate complete quality mapping configuration"""
        
        config = {
            "version": "1.0",
            "mappings": {}
        }
        
        task_types = [
            "character_portrait",
            "character_fullbody",
            "scene_generation",
            "video_generation",
            "style_generation",
            "lighting_generation"
        ]
        
        for task_type in task_types:
            config["mappings"][task_type] = {
                "low": {
                    "workflow_path": f"library/{task_type}/low_v1",
                    "description": f"Fast {task_type.replace('_', ' ')}",
                    "parameters": self._get_base_parameters(task_type, "low")
                },
                "standard": {
                    "workflow_path": f"library/{task_type}/standard_v1",
                    "description": f"Balanced {task_type.replace('_', ' ')}",
                    "parameters": self._get_base_parameters(task_type, "standard")
                },
                "high": {
                    "workflow_path": f"library/{task_type}/high_v1",
                    "description": f"High quality {task_type.replace('_', ' ')}",
                    "parameters": self._get_base_parameters(task_type, "high")
                }
            }
        
        with open(self.output_dir / "config" / "quality_mappings.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def _generate_workflow_api(self, steps: int, width: int, height: int) -> Dict[str, Any]:
        """Generate basic ComfyUI workflow API"""
        
        return {
            "1": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "positive prompt",
                    "clip": ["4", 1]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "negative prompt",
                    "clip": ["4", 1]
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "v1-5-pruned-emaonly.ckpt"
                }
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "model": ["4", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["1", 0],
                    "steps": steps,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "seed": 12345
                }
            }
        }
    
    def _generate_manifest(self, task_type: str, tier: str, steps: int, width: int, height: int) -> Dict[str, Any]:
        """Generate workflow manifest"""
        
        return {
            "schema_version": "1.0",
            "metadata": {
                "name": f"{task_type.replace('_', ' ').title()} - {tier.title()} Quality",
                "version": "1.0.0",
                "description": f"{tier.title()} quality {task_type.replace('_', ' ')} generation"
            },
            "quality_tier": {
                "tier": tier,
                "task_type": task_type
            },
            "parameters": {
                "steps": {"type": "integer", "default": steps, "min": 10, "max": 100},
                "cfg_scale": {"type": "float", "default": 7.0, "min": 1.0, "max": 20.0},
                "width": {"type": "integer", "default": width, "min": 64, "max": 2048},
                "height": {"type": "integer", "default": height, "min": 64, "max": 2048}
            }
        }
    
    def _get_base_parameters(self, task_type: str, tier: str) -> Dict[str, Any]:
        """Get base parameters for task type and tier"""
        
        tier_multipliers = {"low": 0.6, "standard": 1.0, "high": 1.5}
        
        base_params = {
            "character_portrait": {"steps": 30, "width": 512, "height": 768},
            "character_fullbody": {"steps": 40, "width": 768, "height": 1024},
            "scene_generation": {"steps": 35, "width": 1024, "height": 576},
            "video_generation": {"steps": 25, "width": 768, "height": 768},
            "style_generation": {"steps": 30, "width": 512, "height": 512},
            "lighting_generation": {"steps": 30, "width": 1024, "height": 576}
        }
        
        multiplier = tier_multipliers[tier]
        base = base_params.get(task_type, {"steps": 30, "width": 512, "height": 512})
        
        return {
            "steps": int(base["steps"] * multiplier),
            "cfg_scale": 7.0,
            "width": base["width"],
            "height": base["height"]
        }
```

### End-to-End Tests
```python
# backend/tests/test_quality_e2e.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

class TestQualityEndToEnd:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_quality_flow(self, client):
        """Test complete quality selection and execution flow"""
        
        # 1. Get available quality tiers
        response = client.get("/api/v1/quality/tiers/character_portrait")
        assert response.status_code == 200
        
        data = response.json()
        assert "available_tiers" in data
        assert len(data["available_tiers"]) == 3
        
        # 2. Select quality tier
        select_payload = {
            "task_type": "character_portrait",
            "quality_tier": "standard"
        }
        
        response = client.post("/api/v1/quality/select", json=select_payload)
        assert response.status_code == 200
        
        select_data = response.json()
        assert select_data["quality_tier"] == "standard"
        assert "workflow_path" in select_data
        
        # 3. Prepare workflow execution
        prepare_payload = {
            "task_type": "character_portrait",
            "quality_tier": "standard",
            "user_parameters": {
                "positive_prompt": "A happy character portrait",
                "seed": 12345
            }
        }
        
        response = client.post("/api/v1/quality-execution/prepare", json=prepare_payload)
        assert response.status_code == 200
        
        prepare_data = response.json()
        assert prepare_data["quality_tier"] == "standard"
        assert "workflow_api" in prepare_data
        assert "workflow_path" in prepare_data
    
    def test_quality_tier_validation(self, client):
        """Test quality tier validation"""
        
        # Test invalid quality tier
        response = client.get("/api/v1/quality/tiers/character_portrait")
        assert response.status_code == 200
        
        # Test invalid tier selection
        invalid_payload = {
            "task_type": "character_portrait",
            "quality_tier": "invalid"
        }
        
        response = client.post("/api/v1/quality/select", json=invalid_payload)
        assert response.status_code == 400
    
    def test_user_preference_persistence(self, client):
        """Test user quality preference persistence"""
        
        # Set user preference
        preference_payload = {
            "user_id": "test_user",
            "task_type": "character_portrait",
            "quality_tier": "high"
        }
        
        response = client.post("/api/v1/user-preferences/quality", json=preference_payload)
        assert response.status_code == 200
        
        # Get user preference
        response = client.get("/api/v1/user-preferences/quality/test_user/character_portrait")
        assert response.status_code == 200
        assert response.json()["quality_tier"] == "high"
```

### Test Configuration
```yaml
# backend/tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def test_config():
    """Test configuration for quality tier testing"""
    
    return {
        "workflows_root": "./test_workflows",
        "config_path": "./test_config/quality_mappings.yaml",
        "test_user_id": "test_user_123",
        "quality_tiers": ["low", "standard", "high"],
        "test_task_types": [
            "character_portrait",
            "scene_generation",
            "video_generation"
        ]
    }

@pytest.fixture(scope="session")
def setup_test_environment(tmp_path_factory):
    """Set up complete test environment"""
    
    base_temp = tmp_path_factory.mktemp("quality_tests")
    
    # Generate test data
    from tests.fixtures.quality_test_data import QualityTestDataGenerator
    generator = QualityTestDataGenerator(str(base_temp))
    generator.generate_workflow_structures()
    generator.generate_config_file()
    
    return {
        "temp_dir": base_temp,
        "workflows_root": str(base_temp / "comfyui_workflows"),
        "config_path": str(base_temp / "config" / "quality_mappings.yaml")
    }
```

## Test Requirements
- All quality tier mappings tested
- Workflow execution with quality parameters
- Parameter validation accuracy
- Performance benchmarks established
- Error handling coverage
- End-to-end flow validation

## Definition of Done
- All unit tests pass
- Integration tests cover all quality tiers
- Performance tests establish baselines
- Regression tests prevent quality degradation
- Test data generation scripts available
- End-to-end tests validate complete flow