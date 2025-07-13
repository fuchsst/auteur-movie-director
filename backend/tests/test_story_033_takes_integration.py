"""
Tests for STORY-033: Takes Integration
Validates thumbnail generation, Git LFS tracking, and storage metrics.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from PIL import Image

from app.services.takes import TakesService
from app.services.thumbnails import ThumbnailService
from app.services.workspace import WorkspaceService
from app.schemas.project import ProjectCreate, QualityLevel


class TestStory033TakesIntegration:
    """Test STORY-033 Takes Integration requirements"""

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
    def thumbnail_service(self):
        """Create thumbnail service instance"""
        return ThumbnailService()

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
                        name="Test Integration Project", quality=QualityLevel.STANDARD
                    )
                    project_path, manifest = workspace_service.create_project(project_data)
                    return {"id": manifest.id, "path": Path(project_path), "manifest": manifest}

    def create_test_image(self, path: Path, size=(640, 480), color=(255, 0, 0)):
        """Create a test image file"""
        img = Image.new("RGB", size, color)
        img.save(path, "PNG")
        return path

    def create_test_video_file(self, path: Path):
        """Create a fake video file for testing"""
        # Just create a file with video extension for testing
        path.write_bytes(b"fake video content")
        return path

    async def test_thumbnail_generation_for_images(self, thumbnail_service, temp_workspace):
        """Test AC: Automatic thumbnail generation for image takes"""
        # Create test image
        source_image = Path(temp_workspace) / "test_image.png"
        self.create_test_image(source_image)

        # Generate thumbnail
        output_path = Path(temp_workspace) / "thumbnail.png"
        success = await thumbnail_service.generate_thumbnail(
            source_image, output_path, size=(320, 180)
        )

        assert success is True
        assert output_path.exists()

        # Verify thumbnail dimensions
        with Image.open(output_path) as thumb:
            assert thumb.size == (320, 180)

    async def test_multiple_thumbnail_sizes(self, thumbnail_service, temp_workspace):
        """Test AC: Generate thumbnails in multiple sizes"""
        # Create test image
        source_image = Path(temp_workspace) / "test_image.png"
        self.create_test_image(source_image, size=(1920, 1080))

        # Generate multiple sizes
        output_dir = Path(temp_workspace)
        thumbnails = await thumbnail_service.generate_multiple_sizes(
            source_image, output_dir, "test"
        )

        # Verify all sizes were generated
        assert "large" in thumbnails
        assert "medium" in thumbnails
        assert "small" in thumbnails

        # Verify each thumbnail exists and has correct size
        for size_name, path in thumbnails.items():
            assert path.exists()
            with Image.open(path) as thumb:
                expected_size = thumbnail_service.SIZES[size_name]
                # Allow for aspect ratio preservation
                assert thumb.size[0] <= expected_size[0]
                assert thumb.size[1] <= expected_size[1]

    async def test_video_thumbnail_generation(self, thumbnail_service, temp_workspace):
        """Test AC: Video thumbnail extraction"""
        # Skip if ffmpeg not available
        if not thumbnail_service.ffmpeg_available:
            pytest.skip("ffmpeg not available")

        # This test would require actual video file and ffmpeg
        # For unit test, we just verify the method exists
        source_video = Path(temp_workspace) / "test_video.mp4"
        self.create_test_video_file(source_video)

        output_path = Path(temp_workspace) / "video_thumb.png"
        
        # Mock the subprocess call since we can't actually run ffmpeg
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            success = await thumbnail_service.generate_thumbnail(
                source_video, output_path, timestamp=2.5
            )

            # Verify ffmpeg was called with correct parameters
            mock_subprocess.assert_called_once()
            args = mock_subprocess.call_args[0]
            assert args[0] == "ffmpeg"
            assert "-ss" in args
            assert "2.5" in args

    async def test_take_creation_with_thumbnails(self, takes_service, sample_project):
        """Test AC: Automatic thumbnail generation on take creation"""
        shot_id = "01_Chapter/01_Scene/001_Shot"
        
        # Create test image content
        img = Image.new("RGB", (640, 480), (0, 255, 0))
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        file_content = buffer.getvalue()

        # Create take with automatic thumbnail generation
        take_data = await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=file_content,
            file_extension="png",
        )

        # Verify take was created
        assert take_data["id"] == "take_001"
        assert take_data["status"] == "complete"

        # Verify thumbnails were generated
        take_dir = (
            sample_project["path"] / "03_Renders" / "01_Chapter" / "01_Scene" / 
            "001_Shot" / "takes" / "take_001"
        )
        
        # Check for thumbnail files
        thumb_files = list(take_dir.glob("*_thumb_*.png"))
        assert len(thumb_files) > 0  # At least one thumbnail should exist

    async def test_git_lfs_tracking(self, takes_service, sample_project):
        """Test AC: Automatic Git LFS tracking for video takes"""
        shot_id = "01_Chapter/01_Scene/002_Video_Shot"
        
        # Mock git LFS service
        with patch("app.services.takes.git_lfs_service") as mock_lfs:
            mock_lfs.track_file = AsyncMock()
            
            # Create video take
            take_data = await takes_service.create_and_save_take(
                project_path=sample_project["path"],
                shot_id=shot_id,
                file_content=b"fake video content",
                file_extension="mp4",
            )

            # Verify LFS tracking was called for video file
            mock_lfs.track_file.assert_called_once()
            call_args = mock_lfs.track_file.call_args[0]
            assert str(call_args[0]) == str(sample_project["path"])
            assert ".mp4" in call_args[1]

    async def test_storage_metrics_calculation(self, takes_service, sample_project):
        """Test AC: Storage metrics calculation"""
        # Create multiple takes with different qualities
        for i in range(3):
            shot_id = f"01_Chapter/01_Scene/{i:03d}_Shot"
            quality = ["draft", "standard", "high"][i]
            
            await takes_service.create_and_save_take(
                project_path=sample_project["path"],
                shot_id=shot_id,
                file_content=b"x" * (1024 * (i + 1)),  # Different sizes
                file_extension="mp4",
                quality=quality,
            )

        # Get storage metrics
        metrics = await takes_service.get_storage_metrics(sample_project["path"])

        # Verify metrics structure
        assert metrics["total_takes"] == 3
        assert metrics["total_size"] > 0
        assert metrics["media_size"] > 0
        assert "by_quality" in metrics
        assert "by_status" in metrics
        assert "largest_takes" in metrics

        # Verify quality breakdown
        assert "draft" in metrics["by_quality"]
        assert "standard" in metrics["by_quality"]
        assert "high" in metrics["by_quality"]

        # Verify largest takes list
        assert len(metrics["largest_takes"]) <= 10
        if metrics["largest_takes"]:
            # Should be sorted by size descending
            sizes = [t["size"] for t in metrics["largest_takes"]]
            assert sizes == sorted(sizes, reverse=True)

    async def test_cleanup_orphaned_files(self, takes_service, sample_project):
        """Test AC: Cleanup of orphaned take files"""
        shot_id = "01_Chapter/01_Scene/001_Shot"
        
        # Create a legitimate take
        await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"legitimate content",
            file_extension="mp4",
        )

        # Create an orphaned directory
        orphan_dir = (
            sample_project["path"] / "03_Renders" / "01_Chapter" / "01_Scene" / 
            "001_Shot" / "takes" / "take_999"
        )
        orphan_dir.mkdir(parents=True)
        orphan_file = orphan_dir / "orphan.mp4"
        orphan_file.write_bytes(b"orphaned content")

        # Run cleanup
        stats = await takes_service.cleanup_orphaned_files(sample_project["path"])

        # Verify cleanup stats
        assert stats["orphaned_directories"] == 1
        assert stats["bytes_freed"] > 0

        # Verify orphaned directory was removed
        assert not orphan_dir.exists()

        # Verify legitimate take still exists
        legit_dir = (
            sample_project["path"] / "03_Renders" / "01_Chapter" / "01_Scene" / 
            "001_Shot" / "takes" / "take_001"
        )
        assert legit_dir.exists()

    async def test_cleanup_old_deleted_takes(self, takes_service, sample_project):
        """Test AC: Cleanup of old soft-deleted takes"""
        import time
        
        shot_id = "01_Chapter/01_Scene/001_Shot"
        
        # Create and delete a take
        await takes_service.create_and_save_take(
            project_path=sample_project["path"],
            shot_id=shot_id,
            file_content=b"to be deleted",
            file_extension="mp4",
        )
        
        # Delete the take
        await takes_service.delete_take(sample_project["path"], shot_id, "take_001")

        # Create an old deleted directory (>7 days)
        old_timestamp = int(time.time()) - (8 * 24 * 60 * 60)
        old_deleted = (
            sample_project["path"] / "03_Renders" / "01_Chapter" / "01_Scene" / 
            "001_Shot" / "takes" / f".deleted_take_002_{old_timestamp}"
        )
        old_deleted.mkdir(parents=True)
        old_file = old_deleted / "old.mp4"
        old_file.write_bytes(b"old content")

        # Run cleanup
        stats = await takes_service.cleanup_orphaned_files(sample_project["path"])

        # Verify old deleted directory was removed
        assert not old_deleted.exists()
        assert stats["orphaned_directories"] >= 1

    async def test_project_metadata_updates(self, takes_service, sample_project):
        """Test AC: Project metadata includes take information"""
        shot_id = "01_Chapter/01_Scene/001_Shot"
        
        # Create multiple takes
        for i in range(3):
            await takes_service.create_and_save_take(
                project_path=sample_project["path"],
                shot_id=shot_id,
                file_content=b"content" * (i + 1),
                file_extension="mp4",
            )

        # Read project metadata
        project_file = sample_project["path"] / "project.json"
        with open(project_file) as f:
            project_data = json.load(f)

        # Verify takes information in metadata
        assert "takes" in project_data
        assert shot_id in project_data["takes"]
        
        shot_takes = project_data["takes"][shot_id]
        assert shot_takes["total_takes"] == 3
        assert shot_takes["active_take"] == "take_001"  # First take is active by default
        assert "last_generated" in shot_takes

    async def test_performance_large_take_list(self, takes_service, sample_project):
        """Test AC: Performance with many takes"""
        shot_id = "01_Chapter/01_Scene/001_Shot"
        
        # Create 50 takes (not 100 to keep test fast)
        tasks = []
        for i in range(50):
            task = takes_service.create_and_save_take(
                project_path=sample_project["path"],
                shot_id=shot_id,
                file_content=f"content_{i}".encode(),
                file_extension="txt",
                generation_params={"index": i},
            )
            tasks.append(task)
        
        # Create takes concurrently
        await asyncio.gather(*tasks)

        # Measure list performance
        import time
        start = time.time()
        takes = await takes_service.list_takes(sample_project["path"], shot_id)
        duration = time.time() - start

        # Verify performance
        assert len(takes) == 50
        assert duration < 1.0  # Should list 50 takes in under 1 second

    async def test_concurrent_thumbnail_generation(self, thumbnail_service, temp_workspace):
        """Test AC: Concurrent thumbnail generation for performance"""
        # Create multiple test images
        source_images = []
        for i in range(5):
            img_path = Path(temp_workspace) / f"test_{i}.png"
            self.create_test_image(img_path, color=(i * 50, 0, 0))
            source_images.append(img_path)

        # Generate thumbnails concurrently
        tasks = []
        for i, source in enumerate(source_images):
            output_dir = Path(temp_workspace) / f"thumbs_{i}"
            output_dir.mkdir()
            task = thumbnail_service.generate_multiple_sizes(
                source, output_dir, f"test_{i}"
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Verify all thumbnails were generated
        assert len(results) == 5
        for result in results:
            assert len(result) == 3  # Three sizes per image