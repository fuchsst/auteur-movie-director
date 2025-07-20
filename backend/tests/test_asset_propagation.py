"""
Tests for Asset Propagation System
STORY-089 Implementation
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List

from app.services.asset_propagation import AssetPropagationService, AssetPropagationRule
from app.models.asset_types import AssetType


class TestAssetPropagation:
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_workspace):
        """Create a propagation service instance."""
        return AssetPropagationService(temp_workspace)
    
    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert len(service.rules) > 0  # Should have default rules
        assert service.propagation_dir.exists()
    
    def test_create_context(self, service):
        """Test creating asset propagation contexts."""
        context = service.create_context("test_project", "project", "main")
        
        assert context.project_id == "test_project"
        assert context.level == "project"
        assert context.level_id == "main"
        assert len(context.local_assets) == 0
    
    def test_add_asset_to_context(self, service):
        """Test adding assets to contexts."""
        service.add_asset_to_context(
            "test_project", "project", "main", 
            "char_001", AssetType.CHARACTER
        )
        
        resolved = service.resolve_assets("test_project", "project", "main")
        assert len(resolved) == 1
        assert "character:char_001" in resolved
    
    def test_asset_inheritance(self, service):
        """Test asset inheritance across hierarchy levels."""
        # Add asset at project level
        service.add_asset_to_context(
            "test_project", "project", "main", 
            "style_001", AssetType.STYLE
        )
        
        # Should inherit at scene level
        resolved = service.resolve_assets("test_project", "scene", "scene_1")
        assert "style:style_001" in resolved
        assert resolved["style:style_001"].source_level == "project"
    
    def test_asset_override(self, service):
        """Test asset override functionality."""
        # Add asset at project level
        service.add_asset_to_context(
            "test_project", "project", "main", 
            "location_001", AssetType.LOCATION
        )
        
        # Override at scene level
        service.add_asset_to_context(
            "test_project", "scene", "scene_1", 
            "location_002", AssetType.LOCATION,
            override_data={"description": "Scene-specific location"}
        )
        
        # Check scene has override
        scene_assets = service.resolve_assets("test_project", "scene", "scene_1")
        assert "location:location_002" in scene_assets
        assert scene_assets["location:location_002"].is_overridden
    
    def test_custom_propagation_rule(self, service):
        """Test adding custom propagation rules."""
        rule = AssetPropagationRule(
            asset_type=AssetType.PROP,
            source_level="scene",
            target_level="shot",
            propagation_mode="merge",
            priority=10
        )
        
        service.add_propagation_rule(rule)
        assert len(service.rules) > 1
        assert any(r.propagation_mode == "merge" for r in service.rules)
    
    def test_asset_tracking(self, service):
        """Test asset usage tracking."""
        # Add and track asset
        service.add_asset_to_context(
            "test_project", "scene", "scene_1", 
            "prop_001", AssetType.PROP
        )
        
        service.track_asset_usage(
            "test_project", "prop_001", "scene", "scene_1",
            {"usage": "character_holds"}
        )
        
        usage = service.get_asset_usage("test_project", "prop_001")
        assert len(usage) == 1
        assert usage[0]["level"] == "scene"
        assert usage[0]["level_id"] == "scene_1"
    
    def test_validation(self, service):
        """Test asset consistency validation."""
        # Add some test assets
        service.add_asset_to_context("test_project", "project", "main", "char_001", AssetType.CHARACTER)
        service.add_asset_to_context("test_project", "scene", "scene_1", "prop_001", AssetType.PROP)
        
        validation = service.validate_asset_consistency("test_project")
        assert "project_id" in validation
        assert "consistent" in validation
        assert "statistics" in validation
        assert validation["statistics"]["character"] == 1
        assert validation["statistics"]["prop"] == 1
    
    def test_state_save_load(self, service, temp_workspace):
        """Test saving and loading propagation state."""
        # Add some test data
        service.add_asset_to_context("test_project", "project", "main", "char_001", AssetType.CHARACTER)
        service.add_asset_to_context("test_project", "scene", "scene_1", "prop_001", AssetType.PROP)
        
        # Save state
        service.save_state("test_project")
        
        # Create new service instance
        new_service = AssetPropagationService(temp_workspace)
        new_service.load_state("test_project")
        
        # Verify state was loaded
        resolved = new_service.resolve_assets("test_project", "project", "main")
        assert "character:char_001" in resolved
    
    def test_complex_hierarchy(self, service):
        """Test complex hierarchy with multiple levels."""
        # Setup hierarchy: project -> act -> scene -> shot -> take
        
        # Add assets at different levels
        service.add_asset_to_context("test_project", "project", "main", "style_global", AssetType.STYLE)
        service.add_asset_to_context("test_project", "act", "act_1", "char_main", AssetType.CHARACTER)
        service.add_asset_to_context("test_project", "scene", "scene_1", "location_set", AssetType.LOCATION)
        service.add_asset_to_context("test_project", "shot", "shot_1", "prop_detail", AssetType.PROP)
        service.add_asset_to_context("test_project", "take", "take_1", "wardrobe_alt", AssetType.WARDROBE)
        
        # Test take level (should have all inherited assets)
        take_assets = service.resolve_assets("test_project", "take", "take_1")
        
        expected_assets = [
            "style:style_global",
            "character:char_main", 
            "location:location_set",
            "prop:prop_detail",
            "wardrobe:wardrobe_alt"
        ]
        
        for asset_key in expected_assets:
            assert asset_key in take_assets
    
    def test_asset_resolver(self, service):
        """Test the asset resolver functionality."""
        service.add_asset_to_context("test_project", "project", "main", "char_hero", AssetType.CHARACTER)
        service.add_asset_to_context("test_project", "scene", "scene_1", "location_city", AssetType.LOCATION)
        
        resolver = service.propagation_resolver
        generation_context = resolver.resolve_for_generation("test_project", "scene", "scene_1")
        
        assert "characters" in generation_context
        assert "locations" in generation_context
        assert len(generation_context["characters"]) == 1
        assert len(generation_context["locations"]) == 1
        assert generation_context["characters"][0]["id"] == "char_hero"
        assert generation_context["locations"][0]["id"] == "location_city"
    
    def test_export_state(self, service):
        """Test exporting propagation state."""
        service.add_asset_to_context("test_project", "project", "main", "test_asset", AssetType.CHARACTER)
        
        export_data = service.export_propagation_state("test_project")
        
        assert export_data["project_id"] == "test_project"
        assert "contexts" in export_data
        assert "rules" in export_data
        assert "validation" in export_data
    
    def test_error_handling(self, service):
        """Test error handling for invalid inputs."""
        
        # Test invalid level
        with pytest.raises(ValueError):
            service.resolve_assets("test_project", "invalid_level", "test")
        
        # Test invalid asset type
        with pytest.raises(ValueError):
            service.add_asset_to_context("test_project", "project", "main", "test", "invalid_type")
    
    def test_propagation_rules_priority(self, service):
        """Test that higher priority rules override lower priority ones."""
        
        # Add low priority rule
        low_priority_rule = AssetPropagationRule(
            asset_type=AssetType.PROP,
            source_level="project",
            target_level="scene",
            propagation_mode="inherit",
            priority=1
        )
        
        # Add high priority rule
        high_priority_rule = AssetPropagationRule(
            asset_type=AssetType.PROP,
            source_level="project", 
            target_level="scene",
            propagation_mode="block",
            priority=10
        )
        
        service.add_propagation_rule(low_priority_rule)
        service.add_propagation_rule(high_priority_rule)
        
        service.add_asset_to_context("test_project", "project", "main", "prop_test", AssetType.PROP)
        
        # High priority rule should block propagation
        scene_assets = service.resolve_assets("test_project", "scene", "scene_1")
        assert "prop:prop_test" not in scene_assets


class TestAssetPropagationIntegration:
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for integration testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_workspace):
        """Create a propagation service instance."""
        return AssetPropagationService(temp_workspace)
    
    def test_full_workflow(self, service):
        """Test complete asset propagation workflow."""
        
        # 1. Create project-level assets
        service.add_asset_to_context("film_project", "project", "main", 
                                   "hero_style", AssetType.STYLE)
        service.add_asset_to_context("film_project", "project", "main", 
                                   "main_character", AssetType.CHARACTER)
        
        # 2. Create act-level assets
        service.add_asset_to_context("film_project", "act", "act_1", 
                                   "act1_location", AssetType.LOCATION)
        
        # 3. Create scene-level assets
        service.add_asset_to_context("film_project", "scene", "scene_1", 
                                   "scene_prop", AssetType.PROP,
                                   {"description": "Hero's sword"})
        
        # 4. Create shot-level assets
        service.add_asset_to_context("film_project", "shot", "shot_1", 
                                   "shot_wardrobe", AssetType.WARDROBE)
        
        # 5. Track usage
        service.track_asset_usage("film_project", "main_character", "scene", "scene_1")
        service.track_asset_usage("film_project", "main_character", "shot", "shot_1")
        
        # 6. Validate consistency
        validation = service.validate_asset_consistency("film_project")
        assert validation["consistent"] is True
        
        # 7. Export state
        export_data = service.export_propagation_state("film_project")
        assert export_data["project_id"] == "film_project"
        assert len(export_data["contexts"]) > 0
        
        # 8. Test generation context
        resolver = service.propagation_resolver
        gen_context = resolver.resolve_for_generation("film_project", "shot", "shot_1")
        
        assert len(gen_context["characters"]) == 1
        assert len(gen_context["styles"]) == 1
        assert len(gen_context["locations"]) == 1
        assert len(gen_context["props"]) == 1
        assert len(gen_context["wardrobe"]) == 1