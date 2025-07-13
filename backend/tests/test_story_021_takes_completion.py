"""
Tests for STORY-021: Takes Service Completion
Simple tests to verify the completed takes functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.project import ProjectCreate, QualityLevel
from app.services.takes import TakesService
from app.services.workspace import WorkspaceService


class TestStory021TakesCompletion:
    """Test STORY-021 completion requirements"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def workspace_service(self, temp_workspace):
        """Create workspace service instance"""
        return WorkspaceService(temp_workspace)

    @pytest.fixture
    def takes_service(self):
        """Create takes service instance"""
        return TakesService()

    @pytest.fixture
    def sample_project(self, workspace_service):
        """Create a sample project for testing"""
        with patch.object(workspace_service, "_initialize_git_with_lfs"):
            with patch.object(workspace_service, "_create_initial_commit"):
                mock_validation = MagicMock()
                mock_validation.valid = True
                mock_validation.git_initialized = True
                mock_validation.git_lfs_enabled = True
                mock_validation.project_json_valid = True
                mock_validation.missing_directories = []
                mock_validation.errors = []

                with patch.object(
                    workspace_service, "validate_project_structure", return_value=mock_validation
                ):
                    project_data = ProjectCreate(
                        name="Test Takes Project", quality=QualityLevel.STANDARD
                    )
                    project_path, manifest = workspace_service.create_project(project_data)
                    return {"id": manifest.id, "path": Path(project_path), "manifest": manifest}

    async def test_create_and_save_take_simple(self, takes_service, sample_project):
        """Test creating and saving a simple take"""
        shot_id = "01_Chapter/01_Scene/001_Opening_Shot"
        file_content = b"fake video content for testing"

        # Create take
        take_data = await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=file_content,
            file_extension="mp4",
        )

        # Verify take was created
        assert take_data["id"] == "take_001"
        assert take_data["shotId"] == shot_id
        assert take_data["status"] == "complete"

        # Verify file structure was created
        expected_dir = (
            sample_project["path"]
            / "03_Renders"
            / "01_Chapter"
            / "01_Scene"
            / "001_Opening_Shot"
            / "takes"
            / "take_001"
        )
        assert expected_dir.exists()

        # Verify files exist
        video_file = expected_dir / "001_Opening_Shot_take_001.mp4"
        metadata_file = expected_dir / "001_Opening_Shot_take_001_metadata.json"
        assert video_file.exists()
        assert metadata_file.exists()

        # Verify active take was set
        active_take = await takes_service.get_active_take(sample_project["path"], shot_id)
        assert active_take == "take_001"

    async def test_multiple_takes_active_management(self, takes_service, sample_project):
        """Test creating multiple takes and managing active take"""
        shot_id = "01_Chapter/01_Scene/002_Action_Shot"

        # Create first take
        take1_data = await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"first take content",
        )

        # Create second take
        take2_data = await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"second take content",
        )

        # Verify both takes exist
        takes = await takes_service.list_takes(sample_project["path"], shot_id)
        assert len(takes) == 2

        # First take should still be active (we don't auto-update active)
        active_take = await takes_service.get_active_take(sample_project["path"], shot_id)
        assert active_take == "take_001"

        # Set second take as active
        success = await takes_service.set_active_take(sample_project["path"], shot_id, "take_002")
        assert success is True

        # Verify active take changed
        active_take = await takes_service.get_active_take(sample_project["path"], shot_id)
        assert active_take == "take_002"

    async def test_delete_take_functionality(self, takes_service, sample_project):
        """Test deleting takes"""
        shot_id = "01_Chapter/01_Scene/003_Close_Up"

        # Create two takes
        await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"take 1 content",
        )

        await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"take 2 content",
        )

        # Verify both exist
        takes = await takes_service.list_takes(sample_project["path"], shot_id)
        assert len(takes) == 2

        # Delete the first take
        success = await takes_service.delete_take(sample_project["path"], shot_id, "take_001")
        assert success is True

        # Verify only one take remains
        takes = await takes_service.list_takes(sample_project["path"], shot_id)
        assert len(takes) == 1
        assert takes[0]["id"] == "take_002"

        # Verify take_002 became active (since take_001 was deleted)
        active_take = await takes_service.get_active_take(sample_project["path"], shot_id)
        assert active_take == "take_002"

    async def test_project_metadata_updates(self, takes_service, sample_project):
        """Test that project.json is updated with take information"""
        shot_id = "01_Chapter/01_Scene/004_Final_Shot"

        # Create a take
        await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"final shot content",
        )

        # Check project.json was updated
        project_file = sample_project["path"] / "project.json"
        assert project_file.exists()

        import json

        with open(project_file) as f:
            project_data = json.load(f)

        # Verify takes section exists
        assert "takes" in project_data
        assert shot_id in project_data["takes"]

        # Verify take metadata
        shot_data = project_data["takes"][shot_id]
        assert shot_data["total_takes"] == 1
        assert shot_data["active_take"] == "take_001"
        assert "last_generated" in shot_data

    async def test_take_filename_generation(self, takes_service):
        """Test take filename generation"""
        # Test simple shot ID
        filename = takes_service.generate_take_name("simple_shot", 1, "mp4")
        assert filename == "simple_shot_take_001.mp4"

        # Test hierarchical shot ID
        filename = takes_service.generate_take_name("01_Chapter/01_Scene/001_Shot", 5, "mov")
        assert filename == "001_Shot_take_005.mov"

        # Test different extensions
        filename = takes_service.generate_take_name("test_shot", 10, "png")
        assert filename == "test_shot_take_010.png"

    async def test_next_take_number_calculation(self, takes_service, sample_project):
        """Test next take number calculation"""
        shot_id = "01_Chapter/01_Scene/005_Counting_Shot"

        # Should start with 1
        next_number = await takes_service.get_next_take_number(sample_project["path"], shot_id)
        assert next_number == 1

        # Create a take
        await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"first take",
        )

        # Next should be 2
        next_number = await takes_service.get_next_take_number(sample_project["path"], shot_id)
        assert next_number == 2

        # Create another take
        await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"second take",
        )

        # Next should be 3
        next_number = await takes_service.get_next_take_number(sample_project["path"], shot_id)
        assert next_number == 3

    async def test_take_metadata_structure(self, takes_service, sample_project):
        """Test take metadata structure and content"""
        shot_id = "01_Chapter/01_Scene/006_Metadata_Shot"
        generation_params = {
            "model": "test_model",
            "seed": 12345,
            "prompt": "Test generation prompt",
            "steps": 30,
            "cfg": 8.0,
        }

        # Create take with custom parameters
        take_data = await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"metadata test content",
            file_extension="mp4",
            generation_params=generation_params,
            quality="high",
        )

        # Verify metadata structure
        assert "id" in take_data
        assert "shotId" in take_data
        assert "created" in take_data
        assert "generationParams" in take_data
        assert "status" in take_data
        assert "filePath" in take_data
        assert "fileSize" in take_data

        # Verify generation parameters were saved
        saved_params = take_data["generationParams"]
        assert saved_params["model"] == "test_model"
        assert saved_params["seed"] == 12345
        assert saved_params["prompt"] == "Test generation prompt"

        # Verify quality was saved
        assert take_data["resources"]["quality"] == "high"
