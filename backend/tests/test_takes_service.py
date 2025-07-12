"""
Tests for takes management service.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.takes import TakesService


@pytest.fixture
def takes_service():
    """Create takes service instance"""
    return TakesService()


@pytest.fixture
def mock_project_path(tmp_path):
    """Create mock project directory structure"""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create renders directory
    renders_dir = project_path / "03_Renders"
    renders_dir.mkdir()

    return project_path


class TestTakesService:
    """Test takes service functionality"""

    async def test_create_take_directory(self, takes_service, mock_project_path):
        """Test creating take directory structure"""
        shot_id = "01_Chapter/01_Scene/001_Shot"
        take_number = 1

        take_dir = await takes_service.create_take_directory(
            mock_project_path, shot_id, take_number
        )

        assert take_dir.exists()
        assert take_dir.name == "take_001"
        assert "03_Renders/01_Chapter/01_Scene/001_Shot/takes/take_001" in str(take_dir)

    async def test_create_take_directory_simple_shot_id(self, takes_service, mock_project_path):
        """Test creating take directory with simple shot ID"""
        shot_id = "shot_001"
        take_number = 1

        take_dir = await takes_service.create_take_directory(
            mock_project_path, shot_id, take_number
        )

        assert take_dir.exists()
        assert "03_Renders/01_Default_Chapter/01_Default_Scene/shot_001/takes/take_001" in str(
            take_dir
        )

    def test_generate_take_name(self, takes_service):
        """Test take name generation"""
        shot_id = "01_Chapter/01_Scene/001_Shot"
        take_number = 5

        name = takes_service.generate_take_name(shot_id, take_number)
        assert name == "001_Shot_take_005.mp4"

        # Test with different extension
        name = takes_service.generate_take_name(shot_id, take_number, "png")
        assert name == "001_Shot_take_005.png"

    async def test_get_next_take_number_empty(self, takes_service, mock_project_path):
        """Test getting next take number when no takes exist"""
        shot_id = "01_Chapter/01_Scene/001_Shot"

        next_num = await takes_service.get_next_take_number(mock_project_path, shot_id)
        assert next_num == 1

    async def test_get_next_take_number_with_existing(self, takes_service, mock_project_path):
        """Test getting next take number with existing takes"""
        shot_id = "01_Chapter/01_Scene/001_Shot"

        # Create some existing takes
        for i in range(1, 4):
            take_dir = await takes_service.create_take_directory(mock_project_path, shot_id, i)
            await takes_service.save_take_metadata(
                take_dir, f"take_{i:03d}", shot_id, {}, "standard"
            )

        next_num = await takes_service.get_next_take_number(mock_project_path, shot_id)
        assert next_num == 4

    async def test_save_take_metadata(self, takes_service, mock_project_path):
        """Test saving take metadata"""
        shot_id = "01_Chapter/01_Scene/001_Shot"
        take_dir = await takes_service.create_take_directory(mock_project_path, shot_id, 1)

        generation_params = {
            "model": "test-model",
            "seed": 12345,
            "prompt": "test prompt",
            "steps": 20,
            "cfg": 7.5,
        }

        metadata_path = await takes_service.save_take_metadata(
            take_dir, "take_001", shot_id, generation_params, "standard"
        )

        assert metadata_path.exists()

        # Read and verify metadata
        with open(metadata_path) as f:
            metadata = json.load(f)

        assert metadata["id"] == "take_001"
        assert metadata["shotId"] == shot_id
        assert metadata["generationParams"] == generation_params
        assert metadata["resources"]["quality"] == "standard"
        assert metadata["status"] == "generating"

    async def test_update_take_metadata(self, takes_service, mock_project_path):
        """Test updating take metadata"""
        shot_id = "01_Chapter/01_Scene/001_Shot"
        take_dir = await takes_service.create_take_directory(mock_project_path, shot_id, 1)

        # Save initial metadata
        metadata_path = await takes_service.save_take_metadata(
            take_dir, "take_001", shot_id, {}, "standard"
        )

        # Update metadata
        updates = {
            "status": "complete",
            "duration": 5.0,
            "resources": {"vramUsed": 8192, "generationTime": 30.5},
        }

        updated = await takes_service.update_take_metadata(metadata_path, updates)

        assert updated["status"] == "complete"
        assert updated["duration"] == 5.0
        assert updated["resources"]["vramUsed"] == 8192
        assert updated["resources"]["generationTime"] == 30.5
        assert updated["resources"]["quality"] == "standard"  # Original value preserved

    async def test_list_takes(self, takes_service, mock_project_path):
        """Test listing takes"""
        shot_id = "01_Chapter/01_Scene/001_Shot"

        # Create multiple takes
        for i in range(1, 4):
            take_dir = await takes_service.create_take_directory(mock_project_path, shot_id, i)
            await takes_service.save_take_metadata(
                take_dir, f"take_{i:03d}", shot_id, {"seed": i}, "standard"
            )

            # Create dummy media file
            media_file = take_dir / f"001_Shot_take_{i:03d}.mp4"
            media_file.write_text("dummy")

            # Create thumbnail
            thumbnail = take_dir / f"001_Shot_take_{i:03d}_thumbnail.png"
            thumbnail.write_text("dummy")

        takes = await takes_service.list_takes(mock_project_path, shot_id)

        assert len(takes) == 3
        assert all(t["id"] in ["take_001", "take_002", "take_003"] for t in takes)
        assert all("filePath" in t for t in takes)
        assert all("thumbnailPath" in t for t in takes)

    async def test_get_set_active_take(self, takes_service, mock_project_path):
        """Test getting and setting active take"""
        shot_id = "01_Chapter/01_Scene/001_Shot"

        # Initially no active take
        active = await takes_service.get_active_take(mock_project_path, shot_id)
        assert active is None

        # Create a take
        take_dir = await takes_service.create_take_directory(mock_project_path, shot_id, 1)
        await takes_service.save_take_metadata(take_dir, "take_001", shot_id, {}, "standard")

        # Set active take
        success = await takes_service.set_active_take(mock_project_path, shot_id, "take_001")
        assert success

        # Get active take
        active = await takes_service.get_active_take(mock_project_path, shot_id)
        assert active == "take_001"

    async def test_delete_take(self, takes_service, mock_project_path):
        """Test deleting a take (soft delete)"""
        shot_id = "01_Chapter/01_Scene/001_Shot"

        # Create a take
        take_dir = await takes_service.create_take_directory(mock_project_path, shot_id, 1)
        await takes_service.save_take_metadata(take_dir, "take_001", shot_id, {}, "standard")

        # Delete take
        success = await takes_service.delete_take(mock_project_path, shot_id, "take_001")
        assert success

        # Verify directory was renamed
        assert not take_dir.exists()
        deleted_dirs = list(take_dir.parent.glob(".deleted_take_001_*"))
        assert len(deleted_dirs) == 1

    async def test_delete_active_take_switches_active(self, takes_service, mock_project_path):
        """Test deleting active take switches to another take"""
        shot_id = "01_Chapter/01_Scene/001_Shot"

        # Create two takes
        for i in range(1, 3):
            take_dir = await takes_service.create_take_directory(mock_project_path, shot_id, i)
            await takes_service.save_take_metadata(
                take_dir, f"take_{i:03d}", shot_id, {}, "standard"
            )

        # Set first take as active
        await takes_service.set_active_take(mock_project_path, shot_id, "take_001")

        # Delete active take
        await takes_service.delete_take(mock_project_path, shot_id, "take_001")

        # Check new active take
        active = await takes_service.get_active_take(mock_project_path, shot_id)
        assert active == "take_002"

    @patch("shutil.which")
    @patch("asyncio.create_subprocess_exec")
    async def test_generate_thumbnail(self, mock_subprocess, mock_which, takes_service, tmp_path):
        """Test thumbnail generation"""
        mock_which.return_value = "/usr/bin/ffmpeg"

        # Mock subprocess
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        mock_subprocess.return_value = mock_process

        media_path = tmp_path / "video.mp4"
        media_path.write_text("dummy")
        output_path = tmp_path / "thumbnail.png"

        success = await takes_service.generate_thumbnail(media_path, output_path)
        assert success

        # Verify ffmpeg was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0]
        assert call_args[0] == "/usr/bin/ffmpeg"
        assert "-ss" in call_args
        assert "scale=320:180" in call_args

    async def test_cleanup_old_takes(self, takes_service, mock_project_path):
        """Test cleaning up old takes"""
        shot_id = "01_Chapter/01_Scene/001_Shot"

        # Create many takes
        for i in range(1, 16):
            take_dir = await takes_service.create_take_directory(mock_project_path, shot_id, i)
            metadata = await takes_service.save_take_metadata(
                take_dir, f"take_{i:03d}", shot_id, {}, "standard"
            )
            # Simulate different creation times
            await takes_service.update_take_metadata(
                metadata, {"created": f"2024-01-{i:02d}T00:00:00Z"}
            )

        # Set take_005 as active
        await takes_service.set_active_take(mock_project_path, shot_id, "take_005")

        # Cleanup keeping only 10
        deleted = await takes_service.cleanup_old_takes(mock_project_path, shot_id, 10)

        # Should delete 5 takes (15 total - 10 to keep)
        assert deleted == 5

        # Verify active take was not deleted
        active = await takes_service.get_active_take(mock_project_path, shot_id)
        assert active == "take_005"

    async def test_export_take(self, takes_service, mock_project_path):
        """Test exporting a take"""
        shot_id = "01_Chapter/01_Scene/001_Shot"

        # Create a take with media file
        take_dir = await takes_service.create_take_directory(mock_project_path, shot_id, 1)
        await takes_service.save_take_metadata(take_dir, "take_001", shot_id, {}, "standard")

        media_file = take_dir / "001_Shot_take_001.mp4"
        media_file.write_text("video content")

        # Export
        export_dir = mock_project_path / "06_Exports"
        export_path = await takes_service.export_take(
            mock_project_path, shot_id, "take_001", export_dir
        )

        assert export_path is not None
        assert export_path.exists()
        assert export_path.read_text() == "video content"
        assert "06_Exports/01_Chapter/01_Scene/001_Shot/001_Shot_take_001.mp4" in str(export_path)
