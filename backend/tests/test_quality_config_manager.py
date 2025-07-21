"""
Unit tests for Quality Configuration Manager

Tests the fixed quality-to-workflow mapping system without resource analysis.
"""

import pytest
import os
import tempfile
from pathlib import Path
from app.services.quality_config_manager import QualityConfigManager, QualityTierMapper


class TestQualityConfigManager:
    
    @pytest.fixture(autouse=True)
    def cleanup_temp_files(self):
        """Cleanup temporary files after tests."""
        temp_files = []
        yield temp_files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except FileNotFoundError:
                pass
    
    @pytest.fixture
    def temp_config(self, cleanup_temp_files):
        """Create temporary configuration file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = """
version: "1.0"
metadata:
  test: true

mappings:
  character_portrait:
    low:
      workflow_path: "library/character/character_portrait/low_v1"
      description: "Fast character portrait"
      parameters:
        steps: 20
        cfg_scale: 7.0
    
    standard:
      workflow_path: "library/character/character_portrait/standard_v1"
      description: "Balanced character portrait"
      parameters:
        steps: 35
        cfg_scale: 7.5
    
    high:
      workflow_path: "library/character/character_portrait/high_v1"
      description: "High quality character portrait"
      parameters:
        steps: 60
        cfg_scale: 8.0

  scene_generation:
    low:
      workflow_path: "library/scene/scene_generation/low_v1"
      description: "Fast scene generation"
      parameters:
        steps: 25
        cfg_scale: 7.0
    
    standard:
      workflow_path: "library/scene/scene_generation/standard_v1"
      description: "Balanced scene generation"
      parameters:
        steps: 40
        cfg_scale: 7.5
"""
            f.write(config_content)
            f.flush()
            cleanup_temp_files.append(f.name)
            yield f.name
    
    @pytest.fixture
    def config_manager(self, temp_config):
        """Create QualityConfigManager instance."""
        return QualityConfigManager(temp_config)
    
    def test_load_configuration_success(self, temp_config):
        """Test successful configuration loading."""
        manager = QualityConfigManager(temp_config)
        assert manager.config_data['version'] == "1.0"
        assert 'character_portrait' in manager.config_data['mappings']
    
    def test_load_configuration_missing_file(self):
        """Test handling of missing configuration file."""
        manager = QualityConfigManager("/nonexistent/path.yaml")
        assert manager.config_data == {"version": "1.0", "mappings": {}}
    
    def test_get_workflow_path_success(self, config_manager):
        """Test successful workflow path retrieval."""
        path = config_manager.get_workflow_path("character_portrait", "standard")
        assert path == "library/character/character_portrait/standard_v1"
    
    def test_get_workflow_path_invalid_task(self, config_manager):
        """Test handling of invalid task type."""
        path = config_manager.get_workflow_path("invalid_task", "standard")
        assert path is None
    
    def test_get_workflow_path_invalid_tier(self, config_manager):
        """Test handling of invalid quality tier."""
        path = config_manager.get_workflow_path("character_portrait", "ultra")
        assert path is None
    
    def test_get_quality_config_complete(self, config_manager):
        """Test complete quality configuration retrieval."""
        config = config_manager.get_quality_config("character_portrait", "low")
        assert config is not None
        assert config['workflow_path'] == "library/character/character_portrait/low_v1"
        assert config['description'] == "Fast character portrait"
        assert config['parameters']['steps'] == 20
    
    def test_get_available_tiers(self, config_manager):
        """Test retrieval of available tiers for task type."""
        tiers = config_manager.get_available_tiers("character_portrait")
        assert set(tiers) == {'low', 'standard', 'high'}
    
    def test_get_available_tiers_invalid_task(self, config_manager):
        """Test handling of invalid task type for tier retrieval."""
        tiers = config_manager.get_available_tiers("invalid_task")
        assert tiers == []
    
    def test_validate_configuration_success(self, config_manager):
        """Test successful configuration validation."""
        report = config_manager.validate_configuration()
        assert report['valid'] is True
        assert report['valid_mappings'] == 5  # 2 task types: character_portrait (3) + scene_generation (2)
        assert report['total_mappings'] == 5
    
    def test_validate_configuration_missing_fields(self):
        """Test validation with missing required fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = """
mappings:
  character_portrait:
    low:
      workflow_path: "test/path"
      # Missing description and parameters
"""
            f.write(config_content)
            f.flush()
            
            try:
                manager = QualityConfigManager(f.name)
                report = manager.validate_configuration()
                assert report['valid'] is False
                assert len(report['issues']) > 0
            finally:
                os.unlink(f.name)
    
    def test_get_all_configurations(self, config_manager):
        """Test retrieval of all configurations."""
        all_config = config_manager.get_all_configurations()
        assert 'mappings' in all_config
        assert 'character_portrait' in all_config['mappings']
        assert 'scene_generation' in all_config['mappings']
    
    def test_reload_configuration(self, temp_config):
        """Test configuration reload functionality."""
        manager = QualityConfigManager(temp_config)
        
        # Modify file
        with open(temp_config, 'a') as f:
            f.write("\n  test_task:\n    low:\n      workflow_path: \"test/path\"")
        
        manager.reload_configuration()
        assert 'test_task' in manager.config_data['mappings']


class TestQualityTierMapper:
    
    @pytest.fixture(autouse=True)
    def cleanup_temp_files(self):
        """Cleanup temporary files after tests."""
        temp_files = []
        yield temp_files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except FileNotFoundError:
                pass
    
    @pytest.fixture
    def temp_config(self, cleanup_temp_files):
        """Create temporary configuration file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = """
version: "1.0"
mappings:
  character_portrait:
    low:
      workflow_path: "library/character/character_portrait/low_v1"
      description: "Fast character portrait"
      parameters:
        steps: 20
        cfg_scale: 7.0
    standard:
      workflow_path: "library/character/character_portrait/standard_v1"
      description: "Balanced character portrait"
      parameters:
        steps: 35
        cfg_scale: 7.5
"""
            f.write(config_content)
            f.flush()
            cleanup_temp_files.append(f.name)
            yield f.name
    
    @pytest.fixture
    def tier_mapper(self, temp_config):
        """Create QualityTierMapper instance."""
        config_manager = QualityConfigManager(temp_config)
        return QualityTierMapper(config_manager)
    
    def test_map_to_workflow_success(self, tier_mapper):
        """Test successful workflow mapping."""
        result = tier_mapper.map_to_workflow("character_portrait", "low")
        
        assert result['workflow_path'] == "library/character/character_portrait/low_v1"
        assert result['description'] == "Fast character portrait"
        assert result['parameters']['steps'] == 20
        assert result['quality_tier'] == "low"
        assert result['task_type'] == "character_portrait"
    
    def test_map_to_workflow_invalid_task(self, tier_mapper):
        """Test handling of invalid task type."""
        with pytest.raises(ValueError, match="No configuration found"):
            tier_mapper.map_to_workflow("invalid_task", "low")
    
    def test_map_to_workflow_invalid_tier(self, tier_mapper):
        """Test handling of invalid quality tier."""
        with pytest.raises(ValueError, match="No configuration found"):
            tier_mapper.map_to_workflow("character_portrait", "invalid_tier")
    
    def test_get_available_mappings(self, tier_mapper):
        """Test retrieval of all available mappings."""
        mappings = tier_mapper.get_available_mappings()
        
        assert 'character_portrait' in mappings
        assert set(mappings['character_portrait']) == {'low', 'standard'}
    
    def test_get_available_mappings_empty(self):
        """Test available mappings with empty configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("mappings: {}")
            f.flush()
            
            try:
                config_manager = QualityConfigManager(f.name)
                tier_mapper = QualityTierMapper(config_manager)
                
                mappings = tier_mapper.get_available_mappings()
                assert mappings == {}
            finally:
                os.unlink(f.name)
    
    def test_consistent_mapping_across_calls(self, tier_mapper):
        """Test that mappings are consistent across multiple calls."""
        result1 = tier_mapper.map_to_workflow("character_portrait", "low")
        result2 = tier_mapper.map_to_workflow("character_portrait", "low")
        
        assert result1 == result2


class TestQualityIntegration:
    
    def test_complete_quality_flow(self):
        """Test complete quality configuration and mapping flow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = """
version: "1.0"
mappings:
  test_task:
    low:
      workflow_path: "library/test_task/low_v1"
      description: "Test low quality"
      parameters:
        steps: 10
        cfg_scale: 7.0
    standard:
      workflow_path: "library/test_task/standard_v1"
      description: "Test standard quality"
      parameters:
        steps: 20
        cfg_scale: 7.5
    high:
      workflow_path: "library/test_task/high_v1"
      description: "Test high quality"
      parameters:
        steps: 30
        cfg_scale: 8.0
"""
            f.write(config_content)
            f.flush()
            
            try:
                # Test configuration loading
                config_manager = QualityConfigManager(f.name)
                assert config_manager.validate_configuration()['valid']
                
                # Test tier mapping
                tier_mapper = QualityTierMapper(config_manager)
                
                # Test all tiers
                for tier in ['low', 'standard', 'high']:
                    result = tier_mapper.map_to_workflow("test_task", tier)
                    assert result['quality_tier'] == tier
                    assert result['task_type'] == "test_task"
                    assert f"{tier}_v1" in result['workflow_path']
                    assert result['parameters']['steps'] == [10, 20, 30][['low', 'standard', 'high'].index(tier)]
            
            finally:
                os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])