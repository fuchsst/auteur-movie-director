import pytest
import asyncio
from pathlib import Path
from app.services.breakdown_service import BreakdownService
from app.services.script_parser import ScriptParserService
from app.models.breakdown_models import (
    ScriptBreakdown, SceneBreakdown, BreakdownElement, ElementCategory,
    BreakdownElementStatus, BreakdownExportRequest, BreakdownExportFormat
)


class TestBreakdownService:
    """Comprehensive tests for STORY-086: Breakdown View Interface."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def asset_registry(self, temp_dir):
        """Create test asset registry."""
        from app.services.asset_registry import AssetRegistry
        return AssetRegistry(temp_dir)
    
    @pytest.fixture
    def breakdown_service(self, temp_dir, asset_registry):
        """Create test breakdown service."""
        return BreakdownService(str(temp_dir), asset_registry)
    
    @pytest.fixture
    def sample_script(self):
        """Create sample script content."""
        return """
        INT. WAREHOUSE - NIGHT
        
        JOHN, wearing a tattered trench coat, examines an ancient bronze sword.
        The flickering light reveals his weathered face. A police car's siren
        wails in the distance. He carefully places the sword in a leather bag.
        
        EXT. CITY STREET - DAY
        
        MARY drives a red sports car through the busy street. She's wearing
        a designer dress and expensive sunglasses. The car screeches to a halt
        as she spots something in the rearview mirror.
        
        INT. OFFICE BUILDING - DAY
        
        DETECTIVE SMITH, dressed in a sharp suit, reviews case files at his desk.
        A vintage desk lamp provides warm light. Stacks of evidence boxes
        surround him. The sound of typing echoes through the office.
        """
    
    @pytest.mark.asyncio
    async def test_create_breakdown_from_script(self, breakdown_service, sample_script):
        """Test creating breakdown from script."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        assert breakdown.project_id == "test-project"
        assert breakdown.project_name == "Test Project"
        assert breakdown.total_scenes == 3
        assert breakdown.total_elements > 0
        assert "test-project" in breakdown_service.breakdowns
    
    @pytest.mark.asyncio
    async def test_scene_breakdown_creation(self, breakdown_service, sample_script):
        """Test scene breakdown creation."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        scenes = list(breakdown.scenes.values())
        assert len(scenes) == 3
        
        # Check first scene
        scene1 = scenes[0]
        assert scene1.scene_heading == "INT. WAREHOUSE - NIGHT"
        assert scene1.location == "WAREHOUSE"
        assert scene1.time_of_day == "NIGHT"
        assert scene1.interior_exterior == "INT"
        assert "JOHN" in scene1.characters
        assert scene1.get_total_elements() > 0
    
    @pytest.mark.asyncio
    async def test_element_detection(self, breakdown_service, sample_script):
        """Test production element detection."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        scene1 = breakdown.scenes["scene-1"]
        
        # Check detected elements
        props = scene1.elements[ElementCategory.PROPS]
        wardrobe = scene1.elements[ElementCategory.WARDROBE]
        
        # Should detect sword, bag, trench coat
        prop_names = [p.name.lower() for p in props]
        wardrobe_names = [w.name.lower() for w in wardrobe]
        
        assert any("sword" in name for name in prop_names)
        assert any("bag" in name for name in prop_names)
        assert any("trench coat" in name for name in wardrobe_names)
    
    @pytest.mark.asyncio
    async def test_update_element_status(self, breakdown_service, sample_script):
        """Test updating element status."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        scene1 = breakdown.scenes["scene-1"]
        elements = scene1.elements[ElementCategory.PROPS]
        
        if elements:
            element = elements[0]
            original_status = element.status
            
            success = await breakdown_service.update_element_status(
                project_id="test-project",
                scene_id="scene-1",
                element_id=element.element_id,
                new_status=BreakdownElementStatus.CONFIRMED
            )
            
            assert success is True
            assert element.status == BreakdownElementStatus.CONFIRMED
    
    @pytest.mark.asyncio
    async def test_add_custom_element(self, breakdown_service, sample_script):
        """Test adding custom elements."""
        await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        element = await breakdown_service.add_custom_element(
            project_id="test-project",
            scene_id="scene-1",
            element_data={
                "element_type": "props",
                "name": "Magic Crystal",
                "description": "Ancient magical artifact",
                "quantity": 1,
                "estimated_cost": 500.0
            }
        )
        
        assert element.name == "Magic Crystal"
        assert element.element_type == ElementCategory.PROPS
        assert element.quantity == 1
        assert element.estimated_cost == 500.0
    
    @pytest.mark.asyncio
    async def test_breakdown_calculations(self, breakdown_service, sample_script):
        """Test breakdown calculations."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        # Check totals are calculated
        assert breakdown.total_elements > 0
        assert breakdown.total_estimated_cost >= 0
        assert breakdown.total_estimated_duration > 0
        
        # Check element counts by category
        for category in ElementCategory:
            assert category.value in breakdown.element_counts
    
    @pytest.mark.asyncio
    async def test_export_breakdown_json(self, breakdown_service, sample_script):
        """Test JSON export functionality."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        export_request = BreakdownExportRequest(
            project_id="test-project",
            export_format=BreakdownExportFormat.JSON,
            include_costs=True,
            include_notes=True
        )
        
        export_data = await breakdown_service.export_breakdown(
            project_id="test-project",
            export_request=export_request
        )
        
        assert "breakdown" in export_data
        assert "export_metadata" in export_data
        assert export_data["export_metadata"]["format"] == "json"
    
    @pytest.mark.asyncio
    async def test_export_breakdown_csv(self, breakdown_service, sample_script):
        """Test CSV export functionality."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        export_request = BreakdownExportRequest(
            project_id="test-project",
            export_format=BreakdownExportFormat.CSV,
            include_costs=True,
            include_notes=True
        )
        
        csv_data = await breakdown_service.export_breakdown(
            project_id="test-project",
            export_request=export_request
        )
        
        assert isinstance(csv_data, str)
        assert "Scene" in csv_data
        assert "Element Type" in csv_data
    
    @pytest.mark.asyncio
    async def test_breakdown_validation(self, breakdown_service, sample_script):
        """Test breakdown validation."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        is_valid = breakdown.validate_breakdown()
        
        # Should be valid initially
        assert is_valid is True
        assert len(breakdown.validation_errors) == 0
    
    @pytest.mark.asyncio
    async def test_asset_creation_from_element(self, breakdown_service, sample_script):
        """Test automatic asset creation from confirmed elements."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        scene1 = breakdown.scenes["scene-1"]
        
        if scene1.elements[ElementCategory.PROPS]:
            element = scene1.elements[ElementCategory.PROPS][0]
            
            # Update to created status (should trigger asset creation)
            success = await breakdown_service.update_element_status(
                project_id="test-project",
                scene_id="scene-1",
                element_id=element.element_id,
                new_status=BreakdownElementStatus.CREATED
            )
            
            assert success is True
            assert element.asset_id is not None
    
    @pytest.mark.asyncio
    async def test_get_elements_by_category(self, breakdown_service, sample_script):
        """Test retrieving elements by category."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        elements = []
        for scene in breakdown.scenes.values():
            elements.extend(scene.elements[ElementCategory.PROPS])
        
        assert len(elements) > 0
        assert all(e.element_type == ElementCategory.PROPS for e in elements)
    
    @pytest.mark.asyncio
    async def test_breakdown_persistence(self, breakdown_service, sample_script):
        """Test saving and loading breakdown from file."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        # Save breakdown
        await breakdown_service._save_breakdown(breakdown)
        
        # Load breakdown
        loaded_breakdown = await breakdown_service._load_breakdown_from_file(
            breakdown_service.breakdown_dir / "test-project_breakdown.json"
        )
        
        assert loaded_breakdown.project_id == "test-project"
        assert loaded_breakdown.total_scenes == breakdown.total_scenes
    
    def test_element_category_mapping(self):
        """Test element category to asset type mapping."""
        from app.services.breakdown_service import BreakdownService
        from app.models.asset_types import AssetType
        
        service = BreakdownService("/tmp/test", None)
        
        mappings = {
            ElementCategory.CAST: AssetType.CHARACTER,
            ElementCategory.PROPS: AssetType.PROP,
            ElementCategory.WARDROBE: AssetType.WARDROBE,
            ElementCategory.VEHICLES: AssetType.VEHICLE,
            ElementCategory.LOCATIONS: AssetType.LOCATION,
            ElementCategory.SOUNDS: AssetType.SOUND,
            ElementCategory.SFX: AssetType.SFX,
            ElementCategory.SET_DRESSING: AssetType.SET_DRESSING,
            ElementCategory.MUSIC: AssetType.MUSIC,
        }
        
        for category, expected_type in mappings.items():
            result = service._map_element_to_asset_type(category)
            assert result == expected_type
    
    @pytest.mark.asyncio
    async def test_scene_by_number_lookup(self, breakdown_service, sample_script):
        """Test finding scene by scene number."""
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="test-project",
            project_name="Test Project",
            script_path="test_script.txt",
            script_content=sample_script.encode('utf-8')
        )
        
        # Find scene by iterating since get_scene_by_number might not exist
        scene = None
        for s in breakdown.scenes.values():
            if s.scene_number == "1":
                scene = s
                break
        assert scene is not None
        assert scene.scene_number == "1"
    
    @pytest.mark.asyncio
    async def test_breakdown_with_empty_script(self, breakdown_service):
        """Test handling empty script."""
        empty_script = ""
        
        breakdown = await breakdown_service.create_breakdown_from_script(
            project_id="empty-project",
            project_name="Empty Project",
            script_path="empty.txt",
            script_content=empty_script.encode('utf-8')
        )
        
        assert breakdown.total_scenes == 0
        assert breakdown.total_elements == 0
        assert len(breakdown.scenes) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])