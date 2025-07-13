"""
Tests for project import service.
"""

import json
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.project import ImportOptions
from app.services.import_ import ProjectImportService


@pytest.fixture
def import_service():
    """Create import service instance."""
    return ProjectImportService()


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def sample_project_archive(tmp_path):
    """Create a sample project archive for testing."""
    # Create project structure
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()

    # Create project.json
    project_json = {
        "id": "sample_project",
        "name": "Sample Project",
        "created": datetime.utcnow().isoformat(),
        "narrative_structure": "three_act",
        "quality": "standard",
    }
    (project_dir / "project.json").write_text(json.dumps(project_json))

    # Create directory structure
    (project_dir / "01_Assets").mkdir()
    (project_dir / "02_Story").mkdir()
    (project_dir / "03_Renders").mkdir()

    # Create export manifest
    manifest = {
        "export_version": "2.0",
        "project_id": "sample_project",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "export_options": {"format": "zip", "include_history": True},
        "statistics": {"total_files": 10, "total_size_bytes": 1000000, "git_commits": 5},
    }
    (project_dir / "export_manifest.json").write_text(json.dumps(manifest))

    # Create archive
    archive_path = tmp_path / "sample_project.zip"
    with zipfile.ZipFile(archive_path, "w") as zf:
        for file in project_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(tmp_path))

    return archive_path


@pytest.fixture
def legacy_project_archive(tmp_path):
    """Create a legacy v1.0 project archive."""
    project_dir = tmp_path / "legacy_project"
    project_dir.mkdir()

    # Old structure
    (project_dir / "Assets").mkdir()
    (project_dir / "Story").mkdir()
    (project_dir / "Renders").mkdir()

    # Old project.json
    project_json = {"name": "Legacy Project", "created": "2024-01-01T00:00:00"}
    (project_dir / "project.json").write_text(json.dumps(project_json))

    # Create archive
    archive_path = tmp_path / "legacy_project.zip"
    with zipfile.ZipFile(archive_path, "w") as zf:
        for file in project_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(tmp_path))

    return archive_path


class TestProjectImportService:
    """Test project import service."""

    @pytest.mark.asyncio
    async def test_validate_valid_archive(self, import_service, sample_project_archive):
        """Test validating a valid archive."""
        result = await import_service.validate_archive(str(sample_project_archive))

        assert result.valid is True
        assert result.version == "2.0"
        assert result.project_id == "sample_project"
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_invalid_archive(self, import_service, tmp_path):
        """Test validating an invalid archive."""
        # Create empty zip
        invalid_archive = tmp_path / "invalid.zip"
        with zipfile.ZipFile(invalid_archive, "w") as zf:
            zf.writestr("dummy.txt", "dummy content")

        result = await import_service.validate_archive(str(invalid_archive))

        assert result.valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_legacy_archive(self, import_service, legacy_project_archive):
        """Test validating a legacy v1.0 archive."""
        result = await import_service.validate_archive(str(legacy_project_archive))

        assert result.valid is True
        assert result.version == "1.0"
        assert len(result.warnings) > 0  # Should have warnings about missing v2 directories

    @pytest.mark.asyncio
    async def test_import_simple_project(
        self, import_service, sample_project_archive, temp_workspace, monkeypatch
    ):
        """Test importing a simple project."""
        monkeypatch.setattr(import_service, "workspace_root", temp_workspace)

        options = ImportOptions()
        result = await import_service.import_archive(
            str(sample_project_archive), "imported_project", options
        )

        assert result.success is True
        assert result.project_id == "imported_project"
        assert result.project_name == "imported_project"
        assert result.import_duration > 0

        # Check project was created
        imported_path = temp_workspace / "imported_project"
        assert imported_path.exists()
        assert (imported_path / "project.json").exists()
        assert (imported_path / "01_Assets").exists()

    @pytest.mark.asyncio
    async def test_import_with_name_conflict(
        self, import_service, sample_project_archive, temp_workspace, monkeypatch
    ):
        """Test importing with name conflict resolution."""
        monkeypatch.setattr(import_service, "workspace_root", temp_workspace)

        # Create existing project
        existing = temp_workspace / "test_project"
        existing.mkdir()

        options = ImportOptions(rename_on_conflict=True)
        result = await import_service.import_archive(
            str(sample_project_archive), "test_project", options
        )

        assert result.success is True
        assert result.project_id == "test_project_1"
        assert (temp_workspace / "test_project_1").exists()

    @pytest.mark.asyncio
    async def test_import_legacy_with_migration(
        self, import_service, legacy_project_archive, temp_workspace, monkeypatch
    ):
        """Test importing legacy project with migration."""
        monkeypatch.setattr(import_service, "workspace_root", temp_workspace)

        options = ImportOptions()
        result = await import_service.import_archive(
            str(legacy_project_archive), "migrated_project", options
        )

        assert result.success is True

        # Check migration happened
        migrated_path = temp_workspace / "migrated_project"
        assert (migrated_path / "01_Assets").exists()
        assert (migrated_path / "02_Story").exists()
        assert (migrated_path / "03_Renders").exists()
        assert not (migrated_path / "Assets").exists()  # Old directory should be gone

    @pytest.mark.asyncio
    async def test_import_with_git_bundle(
        self, import_service, sample_project_archive, temp_workspace, monkeypatch
    ):
        """Test importing with Git bundle restoration."""
        monkeypatch.setattr(import_service, "workspace_root", temp_workspace)

        # Mock Git operations
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"", b"")
            mock_subprocess.return_value = mock_process

            # Add fake Git bundle to archive
            with tempfile.TemporaryDirectory() as tmpdir:
                # Extract archive
                with zipfile.ZipFile(sample_project_archive, "r") as zf:
                    zf.extractall(tmpdir)

                # Add Git bundle
                bundle_path = Path(tmpdir) / "sample_project" / "git-bundle.bundle"
                bundle_path.write_text("fake bundle")

                # Repack archive
                new_archive = temp_workspace / "with_git.zip"
                with zipfile.ZipFile(new_archive, "w") as zf:
                    for file in Path(tmpdir).rglob("*"):
                        if file.is_file():
                            zf.write(file, file.relative_to(tmpdir))

                options = ImportOptions(restore_git_history=True)
                result = await import_service.import_archive(
                    str(new_archive), "git_project", options
                )

                assert result.success is True
                assert mock_subprocess.called

    @pytest.mark.asyncio
    async def test_import_with_progress_callback(
        self, import_service, sample_project_archive, temp_workspace, monkeypatch
    ):
        """Test import with progress callback."""
        monkeypatch.setattr(import_service, "workspace_root", temp_workspace)

        progress_updates = []

        async def progress_callback(progress: float, message: str):
            progress_updates.append((progress, message))

        options = ImportOptions()
        result = await import_service.import_archive(
            str(sample_project_archive), "progress_test", options, progress_callback
        )

        assert result.success is True
        assert len(progress_updates) > 0
        assert progress_updates[0][0] == 0.1  # First progress
        assert progress_updates[-1][0] == 1.0  # Last progress
        assert "completed" in progress_updates[-1][1].lower()

    @pytest.mark.asyncio
    async def test_import_statistics(
        self, import_service, sample_project_archive, temp_workspace, monkeypatch
    ):
        """Test import statistics calculation."""
        monkeypatch.setattr(import_service, "workspace_root", temp_workspace)

        options = ImportOptions()
        result = await import_service.import_archive(
            str(sample_project_archive), "stats_test", options
        )

        assert result.success is True
        assert "total_files" in result.statistics
        assert "total_size_bytes" in result.statistics
        assert "total_size_mb" in result.statistics
        assert "file_types" in result.statistics
        assert result.statistics["total_files"] > 0

    @pytest.mark.asyncio
    async def test_import_rollback_on_failure(
        self, import_service, sample_project_archive, temp_workspace, monkeypatch
    ):
        """Test rollback on import failure."""
        monkeypatch.setattr(import_service, "workspace_root", temp_workspace)

        # Make workspace read-only to force failure
        temp_workspace.chmod(0o444)

        try:
            options = ImportOptions()
            result = await import_service.import_archive(
                str(sample_project_archive), "fail_test", options
            )

            assert result.success is False
            assert len(result.errors) > 0
            # Project directory should not exist
            assert not (temp_workspace / "fail_test").exists()
        finally:
            # Restore permissions
            temp_workspace.chmod(0o755)

    def test_get_required_directories(self, import_service):
        """Test getting required directories for different versions."""
        v1_dirs = import_service._get_required_directories("1.0")
        assert "Assets" in v1_dirs
        assert "Story" in v1_dirs

        v2_dirs = import_service._get_required_directories("2.0")
        assert "01_Assets" in v2_dirs
        assert "02_Story" in v2_dirs
