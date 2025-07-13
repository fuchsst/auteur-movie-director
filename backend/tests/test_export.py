"""
Tests for project export functionality.
"""

import json
import os
import tarfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.project import ExportOptions
from app.services.export import ProjectExportService


@pytest.fixture
def export_service():
    """Create export service instance."""
    return ProjectExportService()


@pytest.fixture
def mock_project_dir(tmp_path):
    """Create a mock project directory structure."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create project structure
    (project_dir / "project.json").write_text(
        json.dumps(
            {"id": "test-project", "name": "Test Project", "created": datetime.now().isoformat()}
        )
    )

    # Create some content
    (project_dir / "01_Assets").mkdir()
    (project_dir / "01_Assets" / "test_asset.txt").write_text("Asset content")

    (project_dir / "03_Renders").mkdir()
    (project_dir / "03_Renders" / "test_render.mp4").write_bytes(b"Video content")

    # Create Git directory
    git_dir = project_dir / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main")

    # Create LFS objects
    lfs_dir = git_dir / "lfs" / "objects"
    lfs_dir.mkdir(parents=True)
    (lfs_dir / "test_lfs_object").write_bytes(b"LFS content")

    return project_dir


class TestProjectExportService:
    """Test project export service."""

    @pytest.mark.asyncio
    async def test_init(self, export_service):
        """Test service initialization."""
        assert export_service.workspace_root.exists()
        assert export_service.temp_dir.exists()

    @pytest.mark.asyncio
    async def test_export_project_zip(self, export_service, mock_project_dir):
        """Test exporting project as ZIP."""
        # Mock workspace root
        with patch.object(export_service, "workspace_root", mock_project_dir.parent):
            options = ExportOptions(format="zip", include_history=True, include_cache=False)

            # Export project
            archive_path = await export_service.export_project("test-project", options)

            # Verify archive exists
            assert Path(archive_path).exists()
            assert archive_path.endswith(".zip")

            # Verify contents
            with zipfile.ZipFile(archive_path, "r") as zf:
                namelist = zf.namelist()
                assert "test-project/project.json" in namelist
                assert "test-project/01_Assets/test_asset.txt" in namelist
                assert "test-project/export_manifest.json" in namelist

                # Check manifest
                manifest_data = zf.read("test-project/export_manifest.json")
                manifest = json.loads(manifest_data)
                assert manifest["project_id"] == "test-project"
                assert manifest["export_version"] == "1.0"

    @pytest.mark.asyncio
    async def test_export_project_tar_gz(self, export_service, mock_project_dir):
        """Test exporting project as TAR.GZ."""
        with patch.object(export_service, "workspace_root", mock_project_dir.parent):
            options = ExportOptions(format="tar.gz", include_history=False, include_cache=False)

            archive_path = await export_service.export_project("test-project", options)

            assert Path(archive_path).exists()
            assert archive_path.endswith(".tar.gz")

            # Verify contents
            with tarfile.open(archive_path, "r:gz") as tf:
                names = tf.getnames()
                assert "test-project/project.json" in names
                assert "test-project/01_Assets/test_asset.txt" in names

    @pytest.mark.asyncio
    async def test_export_with_progress(self, export_service, mock_project_dir):
        """Test export with progress callback."""
        progress_updates = []

        async def progress_callback(progress: float, message: str):
            progress_updates.append((progress, message))

        with patch.object(export_service, "workspace_root", mock_project_dir.parent):
            options = ExportOptions()

            await export_service.export_project("test-project", options, progress_callback)

            # Verify progress updates
            assert len(progress_updates) > 0
            assert progress_updates[0][0] == 0  # First update at 0%
            assert progress_updates[-1][0] == 1.0  # Last update at 100%
            assert "completed" in progress_updates[-1][1].lower()

    @pytest.mark.asyncio
    async def test_export_exclude_cache(self, export_service, mock_project_dir):
        """Test excluding cache files."""
        # Add cache files
        cache_dir = mock_project_dir / "04_Cache"
        cache_dir.mkdir()
        (cache_dir / "temp.cache").write_text("Cache content")

        with patch.object(export_service, "workspace_root", mock_project_dir.parent):
            options = ExportOptions(include_cache=False)

            archive_path = await export_service.export_project("test-project", options)

            # Verify cache excluded
            with zipfile.ZipFile(archive_path, "r") as zf:
                namelist = zf.namelist()
                assert not any("04_Cache" in name for name in namelist)
                assert not any(".cache" in name for name in namelist)

    @pytest.mark.asyncio
    async def test_bundle_git_history(self, export_service, mock_project_dir):
        """Test Git history bundling."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Mock git bundle command
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            await export_service._bundle_git_repo(mock_project_dir, mock_project_dir / "staging")

            # Verify git bundle was called
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0]
            assert call_args[0] == "git"
            assert "bundle" in call_args
            assert "create" in call_args

    @pytest.mark.asyncio
    async def test_bundle_lfs_objects(self, export_service, mock_project_dir):
        """Test LFS object bundling."""
        staging_dir = mock_project_dir / "staging"
        staging_dir.mkdir()

        await export_service._bundle_lfs_objects(mock_project_dir, staging_dir)

        # Verify LFS objects copied
        lfs_dest = staging_dir / ".git-lfs-objects"
        assert lfs_dest.exists()
        assert (lfs_dest / "test_lfs_object").exists()

    @pytest.mark.asyncio
    async def test_create_manifest(self, export_service, mock_project_dir):
        """Test manifest creation."""
        options = ExportOptions()

        manifest = await export_service._create_manifest("test-project", mock_project_dir, options)

        assert manifest.export_version == "1.0"
        assert manifest.project_id == "test-project"
        assert manifest.statistics.total_files > 0
        assert manifest.statistics.total_size_bytes > 0

    @pytest.mark.asyncio
    async def test_export_nonexistent_project(self, export_service):
        """Test exporting non-existent project."""
        options = ExportOptions()

        with pytest.raises(ValueError, match="Project nonexistent not found"):
            await export_service.export_project("nonexistent", options)

    @pytest.mark.asyncio
    async def test_split_archive(self, export_service, tmp_path):
        """Test archive splitting."""
        # Create a dummy archive
        archive_path = tmp_path / "test.zip"
        archive_path.write_bytes(b"x" * 1024 * 1024)  # 1MB

        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            result = await export_service._split_archive(archive_path, 1)

            # Should return first part
            assert str(result).endswith(".partaa")

    def test_list_exports(self, export_service):
        """Test listing exports."""
        # Create some dummy export files
        export_file = export_service.temp_dir / "project_export_20250113_120000.zip"
        export_file.write_bytes(b"test")

        exports = export_service.list_exports()

        assert len(exports) > 0
        assert exports[0]["filename"] == export_file.name
        assert exports[0]["size"] == 4

    def test_cleanup_old_exports(self, export_service):
        """Test cleaning up old exports."""
        # Create old export file
        old_file = export_service.temp_dir / "project_export_old.zip"
        old_file.write_bytes(b"old")

        # Make it old

        old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
        os.utime(old_file, (old_time, old_time))

        # Create recent file
        new_file = export_service.temp_dir / "project_export_new.zip"
        new_file.write_bytes(b"new")

        # Clean up files older than 7 days
        export_service.cleanup_old_exports(days=7)

        assert not old_file.exists()
        assert new_file.exists()


class TestExportAPI:
    """Test export API endpoints."""

    @pytest.mark.asyncio
    async def test_export_endpoint(self, client):
        """Test export API endpoint."""
        with patch("app.api.v1.export.export_service.export_project") as mock_export:
            mock_export.return_value = "/tmp/export.zip"

            response = client.post(
                "/api/v1/export/test-project",
                json={"format": "zip", "include_history": True, "include_cache": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["project_id"] == "test-project"
            assert data["status"] == "started"

    @pytest.mark.asyncio
    async def test_download_endpoint(self, client):
        """Test download endpoint."""
        # Mock file existence
        with patch("app.api.v1.export.export_service.temp_dir") as mock_temp_dir:
            mock_temp_dir.return_value = Path("/tmp")

            with patch("pathlib.Path.exists", return_value=True):
                response = client.get(
                    "/api/v1/export/test-project/download/test-project_export_20250113.zip"
                )

                # Should return FileResponse
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_exports_endpoint(self, client):
        """Test list exports endpoint."""
        with patch("app.api.v1.export.export_service.list_exports") as mock_list:
            mock_list.return_value = [
                {"filename": "test_export.zip", "size": 1024, "created": datetime.now().isoformat()}
            ]

            response = client.get("/api/v1/export/list")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert data["exports"][0]["filename"] == "test_export.zip"
