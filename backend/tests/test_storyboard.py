"""
Tests for Storyboard/Pre-vis Integration
STORY-087 Implementation
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.models.storyboard_models import (
    StoryboardSequence, StoryboardShot, StoryboardFrame,
    PrevisGenerationRequest, StoryboardFrameStatus, CameraMovement
)
from app.services.storyboard_service import StoryboardService
from app.services.breakdown_service import BreakdownService
from app.models.breakdown_models import SceneBreakdown, ElementCategory, BreakdownElement


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace for testing."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_asset_registry():
    """Mock asset registry."""
    from app.services.asset_registry import AssetRegistry
    mock_registry = AsyncMock(spec=AssetRegistry)
    return mock_registry


@pytest.fixture
def breakdown_service(temp_workspace, mock_asset_registry):
    """Create breakdown service for testing."""
    return BreakdownService(
        project_root=str(temp_workspace),
        asset_registry=mock_asset_registry
    )


@pytest.fixture
def storyboard_service(temp_workspace, breakdown_service):
    """Create storyboard service for testing."""
    return StoryboardService(
        project_root=str(temp_workspace),
        breakdown_service=breakdown_service
    )


@pytest.fixture
def sample_scene_breakdown():
    """Create sample scene breakdown."""
    return SceneBreakdown(
        scene_id="scene_001",
        scene_number="1",
        scene_heading="INT. COFFEE SHOP - DAY",
        synopsis="Character enters coffee shop and orders drink",
        location="Coffee Shop",
        time_of_day="DAY",
        interior_exterior="INT",
        characters=["ALEX", "BARISTA"],
        elements={
            ElementCategory.CAST: [
                BreakdownElement(
                    element_id="char_alex",
                    element_type=ElementCategory.CAST,
                    name="Alex",
                    description="Main character",
                    scene_id="scene_001"
                ),
                BreakdownElement(
                    element_id="char_barista",
                    element_type=ElementCategory.CAST,
                    name="Barista",
                    description="Coffee shop employee",
                    scene_id="scene_001"
                )
            ],
            ElementCategory.PROPS: [
                BreakdownElement(
                    element_id="prop_coffee",
                    element_type=ElementCategory.PROPS,
                    name="Coffee Cup",
                    description="Hot coffee in ceramic cup",
                    scene_id="scene_001"
                )
            ]
        }
    )


class TestStoryboardModels:
    """Test storyboard model functionality."""
    
    def test_storyboard_sequence_creation(self):
        """Test storyboard sequence creation."""
        sequence = StoryboardSequence(
            sequence_id="test_sequence",
            scene_id="scene_001",
            sequence_name="Test Sequence"
        )
        
        assert sequence.sequence_id == "test_sequence"
        assert sequence.scene_id == "scene_001"
        assert sequence.get_shot_count() == 0
        assert sequence.get_frame_count() == 0
    
    def test_storyboard_shot_creation(self):
        """Test storyboard shot creation."""
        shot = StoryboardShot(
            shot_id="test_shot_1",
            scene_id="scene_001",
            shot_number=1,
            shot_type="establishing"
        )
        
        assert shot.shot_id == "test_shot_1"
        assert shot.shot_number == 1
        assert shot.shot_type == "establishing"
        assert shot.get_frame_count() == 0
    
    def test_storyboard_frame_creation(self):
        """Test storyboard frame creation."""
        frame = StoryboardFrame(
            frame_id="test_frame_1",
            scene_id="scene_001",
            shot_number=1,
            frame_number=1,
            description="Test frame"
        )
        
        assert frame.frame_id == "test_frame_1"
        assert frame.frame_number == 1
        assert frame.description == "Test frame"
        assert frame.status == StoryboardFrameStatus.CONCEPT
    
    def test_sequence_duration_calculation(self):
        """Test sequence duration calculation."""
        sequence = StoryboardSequence(
            sequence_id="test_sequence",
            scene_id="scene_001"
        )
        
        # Add shots with different durations
        shot1 = StoryboardShot(
            shot_id="shot_1", 
            scene_id="scene_001", 
            shot_number=1, 
            duration=3.0
        )
        shot2 = StoryboardShot(
            shot_id="shot_2", 
            scene_id="scene_001", 
            shot_number=2, 
            duration=2.5
        )
        
        sequence.add_shot(shot1)
        sequence.add_shot(shot2)
        
        assert sequence.total_duration == 5.5


class TestStoryboardService:
    """Test storyboard service functionality."""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, storyboard_service):
        """Test service initialization."""
        assert storyboard_service is not None
        assert len(storyboard_service.templates) > 0
        assert "standard" in storyboard_service.templates
        assert "cinematic" in storyboard_service.templates
    
    @pytest.mark.asyncio
    async def test_create_sequence_from_breakdown(
        self, 
        storyboard_service, 
        sample_scene_breakdown
    ):
        """Test creating sequence from scene breakdown."""
        # Mock the breakdown service
        storyboard_service.breakdown_service.get_breakdown = AsyncMock()
        storyboard_service.breakdown_service.get_breakdown.return_value = AsyncMock()
        storyboard_service.breakdown_service.get_breakdown.return_value.scenes = {
            "scene_001": sample_scene_breakdown
        }
        
        sequence = await storyboard_service.create_sequence_from_breakdown(
            project_id="test_project",
            scene_id="scene_001",
            template_id="standard"
        )
        
        assert sequence is not None
        assert sequence.sequence_id == "sequence_scene_001"
        assert sequence.scene_id == "scene_001"
        assert sequence.get_shot_count() > 0
    
    @pytest.mark.asyncio
    async def test_add_frame_to_shot(self, storyboard_service):
        """Test adding frame to shot."""
        # Create a sequence first
        sequence = StoryboardSequence(
            sequence_id="test_sequence",
            scene_id="scene_001"
        )
        
        shot = StoryboardShot(
            shot_id="test_shot_1",
            scene_id="scene_001",
            shot_number=1
        )
        sequence.add_shot(shot)
        
        storyboard_service.sequences["test_sequence"] = sequence
        
        frame_data = {
            "description": "New test frame",
            "camera_angle": "high_angle",
            "composition": "wide"
        }
        
        frame = await storyboard_service.add_frame(
            sequence_id="test_sequence",
            shot_id="test_shot_1",
            frame_data=frame_data
        )
        
        assert frame is not None
        assert frame.description == "New test frame"
        assert frame.camera_angle == "high_angle"
    
    @pytest.mark.asyncio
    async def test_update_frame(self, storyboard_service):
        """Test updating storyboard frame."""
        # Create test data
        sequence = StoryboardSequence(
            sequence_id="test_sequence",
            scene_id="scene_001"
        )
        
        shot = StoryboardShot(
            shot_id="test_shot_1",
            scene_id="scene_001",
            shot_number=1
        )
        
        frame = StoryboardFrame(
            frame_id="test_frame_1",
            scene_id="scene_001",
            shot_number=1,
            frame_number=1,
            description="Original description"
        )
        
        shot.add_frame(frame)
        sequence.add_shot(shot)
        storyboard_service.sequences["test_sequence"] = sequence
        
        updates = {"description": "Updated description", "camera_angle": "low_angle"}
        
        success = await storyboard_service.update_frame(
            sequence_id="test_sequence",
            shot_id="test_shot_1",
            frame_id="test_frame_1",
            updates=updates
        )
        
        assert success is True
        updated_frame = shot.frames[0]
        assert updated_frame.description == "Updated description"
        assert updated_frame.camera_angle == "low_angle"
    
    @pytest.mark.asyncio
    async def test_generate_previs(self, storyboard_service):
        """Test pre-visualization generation."""
        # Create test sequence
        sequence = StoryboardSequence(
            sequence_id="test_sequence",
            scene_id="scene_001"
        )
        
        shot = StoryboardShot(
            shot_id="test_shot_1",
            scene_id="scene_001",
            shot_number=1
        )
        
        frame = StoryboardFrame(
            frame_id="test_frame_1",
            scene_id="scene_001",
            shot_number=1,
            frame_number=1,
            description="Test frame description"
        )
        
        shot.add_frame(frame)
        sequence.add_shot(shot)
        storyboard_service.sequences["test_sequence"] = sequence
        
        request = PrevisGenerationRequest(
            sequence_id="test_sequence",
            scene_id="scene_001"
        )
        
        result = await storyboard_service.generate_previs(request)
        
        assert result is not None
        assert result.sequence_id == "test_sequence"
        assert result.status == "processing"
    
    @pytest.mark.asyncio
    async def test_export_sequence(self, storyboard_service):
        """Test sequence export functionality."""
        # Create test sequence
        sequence = StoryboardSequence(
            sequence_id="test_sequence",
            scene_id="scene_001"
        )
        
        shot = StoryboardShot(
            shot_id="test_shot_1",
            scene_id="scene_001",
            shot_number=1
        )
        
        frame = StoryboardFrame(
            frame_id="test_frame_1",
            scene_id="scene_001",
            shot_number=1,
            frame_number=1,
            description="Test frame description"
        )
        
        shot.add_frame(frame)
        sequence.add_shot(shot)
        storyboard_service.sequences["test_sequence"] = sequence
        
        export_data = await storyboard_service.export_sequence(
            sequence_id="test_sequence",
            format="json"
        )
        
        assert export_data is not None
        assert export_data["export_metadata"]["format"] == "json"
        assert "sequence" in export_data
        assert export_data["export_metadata"]["total_shots"] == 1
        assert export_data["export_metadata"]["total_frames"] == 1


class TestAPIEndpoints:
    """Test API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_sequence_endpoint(self, client, storyboard_service):
        """Test create sequence endpoint."""
        # Mock the service
        with patch('app.api.v1.storyboard.get_storyboard_service', return_value=storyboard_service):
            storyboard_service.create_sequence_from_breakdown = AsyncMock()
            
            mock_sequence = StoryboardSequence(
                sequence_id="test_sequence",
                scene_id="scene_001"
            )
            storyboard_service.create_sequence_from_breakdown.return_value = mock_sequence
            
            response = client.post(
                "/api/v1/storyboard/sequences",
                json={
                    "project_id": "test_project",
                    "scene_id": "scene_001",
                    "template_id": "standard"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "sequence_id" in data
    
    @pytest.mark.asyncio
    async def test_get_sequence_endpoint(self, client, storyboard_service):
        """Test get sequence endpoint."""
        with patch('app.api.v1.storyboard.get_storyboard_service', return_value=storyboard_service):
            storyboard_service.get_sequence = AsyncMock()
            
            mock_sequence = StoryboardSequence(
                sequence_id="test_sequence",
                scene_id="scene_001"
            )
            storyboard_service.get_sequence.return_value = mock_sequence
            
            response = client.get("/api/v1/storyboard/sequences/test_sequence")
            
            assert response.status_code == 200
            data = response.json()
            assert "sequence" in data
    
    @pytest.mark.asyncio
    async def test_template_endpoints(self, client, storyboard_service):
        """Test template endpoints."""
        with patch('app.api.v1.storyboard.get_storyboard_service', return_value=storyboard_service):
            response = client.get("/api/v1/storyboard/templates")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            
            # Test specific template
            response = client.get("/api/v1/storyboard/templates/standard")
            assert response.status_code == 200
            template = response.json()
            assert template["template_id"] == "standard"


class TestIntegration:
    """Integration tests for storyboard functionality."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, storyboard_service, sample_scene_breakdown):
        """Test complete storyboard workflow."""
        # Setup
        storyboard_service.breakdown_service.get_breakdown = AsyncMock()
        storyboard_service.breakdown_service.get_breakdown.return_value = AsyncMock()
        storyboard_service.breakdown_service.get_breakdown.return_value.scenes = {
            "scene_001": sample_scene_breakdown
        }
        
        # Create sequence
        sequence = await storyboard_service.create_sequence_from_breakdown(
            project_id="test_project",
            scene_id="scene_001"
        )
        
        assert sequence is not None
        assert len(sequence.shots) > 0
        
        # Add custom frame
        first_shot = sequence.shots[0]
        frame_data = {
            "description": "Custom frame description",
            "camera_angle": "dutch_angle",
            "composition": "closeup"
        }
        
        new_frame = await storyboard_service.add_frame(
            sequence_id=sequence.sequence_id,
            shot_id=first_shot.shot_id,
            frame_data=frame_data
        )
        
        assert new_frame.description == "Custom frame description"
        assert new_frame.camera_angle == "dutch_angle"
        
        # Export sequence
        export_data = await storyboard_service.export_sequence(
            sequence.sequence_id, "json"
        )
        
        assert export_data["export_metadata"]["total_shots"] == len(sequence.shots)
        assert export_data["export_metadata"]["total_frames"] > 0
    
    @pytest.mark.asyncio
    async def test_template_application(self, storyboard_service):
        """Test template application."""
        sequence = StoryboardSequence(
            sequence_id="test_sequence",
            scene_id="scene_001"
        )
        
        template = storyboard_service.templates["cinematic"]
        template.apply_template(sequence)
        
        assert sequence.aspect_ratio == "16:9"
        assert sequence.resolution == "1920x1080"
        assert sequence.frame_rate == 24.0


if __name__ == "__main__":
    pytest.main([__file__])