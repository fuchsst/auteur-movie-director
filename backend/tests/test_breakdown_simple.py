"""
Simple tests for STORY-086: Breakdown View Interface
"""

import pytest
import tempfile
from pathlib import Path
import asyncio

from app.services.breakdown_service import BreakdownService
from app.models.breakdown_models import ElementCategory, BreakdownElementStatus
from app.services.asset_registry import AssetRegistry


@pytest.mark.asyncio
async def test_breakdown_creation():
    """Test basic breakdown creation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        asset_registry = AssetRegistry(Path(tmp_dir))
        service = BreakdownService(tmp_dir, asset_registry)
        
        sample_script = """
INT. WAREHOUSE - NIGHT

JOHN, wearing a tattered trench coat, examines an ancient bronze sword.
The flickering light reveals his weathered face.

EXT. CITY STREET - DAY

MARY drives a red sports car through the busy street.
"""
        
        breakdown = await service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        assert breakdown.project_id == "test-project"
        assert breakdown.total_scenes == 2
        assert breakdown.total_elements > 0
        assert len(breakdown.scenes) == 2


@pytest.mark.asyncio
async def test_element_mapping():
    """Test element category mapping."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        asset_registry = AssetRegistry(Path(tmp_dir))
        service = BreakdownService(tmp_dir, asset_registry)
        
        from app.models.asset_types import AssetType
        
        mappings = {
            ElementCategory.CAST: AssetType.CHARACTER,
            ElementCategory.PROPS: AssetType.PROP,
            ElementCategory.WARDROBE: AssetType.WARDROBE,
            ElementCategory.VEHICLES: AssetType.VEHICLE,
            ElementCategory.LOCATIONS: AssetType.LOCATION,
        }
        
        for category, expected_type in mappings.items():
            result = service._map_element_to_asset_type(category)
            assert result == expected_type


@pytest.mark.asyncio
async def test_scene_details_parsing():
    """Test scene details parsing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        asset_registry = AssetRegistry(Path(tmp_dir))
        service = BreakdownService(tmp_dir, asset_registry)
        
        location, time, int_ext = service._parse_scene_details("INT. WAREHOUSE - NIGHT")
        assert location == "WAREHOUSE"
        assert time == "NIGHT"
        assert int_ext == "INT"
        
        location, time, int_ext = service._parse_scene_details("EXT. CITY STREET - DAY")
        assert location == "CITY STREET"
        assert time == "DAY"
        assert int_ext == "EXT"


@pytest.mark.asyncio
async def test_custom_element_addition():
    """Test adding custom elements."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        asset_registry = AssetRegistry(Path(tmp_dir))
        service = BreakdownService(tmp_dir, asset_registry)
        
        # Create minimal breakdown
        from app.models.breakdown_models import ScriptBreakdown
        breakdown = ScriptBreakdown(
            project_id="test-project",
            project_name="Test Project",
            script_title="Test Script",
            script_author="Test Author",
            total_scenes=1,
            total_pages=1.0
        )
        
        # Add a scene
        from app.models.breakdown_models import SceneBreakdown
        scene = SceneBreakdown(
            scene_id="scene-1",
            scene_number="1",
            scene_heading="INT. TEST - DAY",
            synopsis="Test scene",
            location="TEST",
            time_of_day="DAY",
            interior_exterior="INT"
        )
        
        breakdown.scenes["scene-1"] = scene
        service.breakdowns["test-project"] = breakdown
        
        # Add custom element
        element = await service.add_custom_element(
            project_id="test-project",
            scene_id="scene-1",
            element_data={
                "element_type": "props",
                "name": "Magic Wand",
                "description": "Magical artifact",
                "quantity": 1,
                "estimated_cost": 100.0
            }
        )
        
        assert element.name == "Magic Wand"
        assert element.element_type == ElementCategory.PROPS
        assert element.estimated_cost == 100.0


@pytest.mark.asyncio
async def test_breakdown_validation():
    """Test breakdown validation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        asset_registry = AssetRegistry(Path(tmp_dir))
        service = BreakdownService(tmp_dir, asset_registry)
        
        from app.models.breakdown_models import ScriptBreakdown
        breakdown = ScriptBreakdown(
            project_id="test-project",
            project_name="Test Project",
            script_title="Test Script",
            script_author="Test Author",
            total_scenes=1,
            total_pages=1.0
        )
        
        # Add valid scene
        from app.models.breakdown_models import SceneBreakdown
        scene = SceneBreakdown(
            scene_id="scene-1",
            scene_number="1",
            scene_heading="INT. TEST - DAY",
            synopsis="Test scene",
            location="TEST",
            time_of_day="DAY",
            interior_exterior="INT"
        )
        breakdown.scenes["scene-1"] = scene
        
        is_valid = breakdown.validate_breakdown()
        assert is_valid is True
        assert len(breakdown.validation_errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])