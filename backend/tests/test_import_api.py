"""
Tests for project import API endpoints.
"""

import json
import zipfile
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from httpx import AsyncClient

from app.schemas.project import ImportResult, ValidationResult


@pytest.fixture
def sample_archive_file(tmp_path):
    """Create a sample archive file for upload testing."""
    # Create minimal project structure
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Add project.json
    project_json = {
        "id": "test_project",
        "name": "Test Project",
        "created": datetime.utcnow().isoformat(),
    }
    (project_dir / "project.json").write_text(json.dumps(project_json))

    # Create ZIP archive
    archive_path = tmp_path / "test_project.zip"
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.write(project_dir / "project.json", "test_project/project.json")

    return archive_path


class TestImportAPI:
    """Test import API endpoints."""

    @pytest.mark.asyncio
    async def test_upload_archive_success(self, async_client: AsyncClient, sample_archive_file):
        """Test successful archive upload."""
        with open(sample_archive_file, "rb") as f:
            files = {"file": ("test_project.zip", f, "application/zip")}

            with patch("app.services.import_.import_service.validate_archive") as mock_validate:
                mock_validate.return_value = ValidationResult(
                    valid=True, version="2.0", project_id="test_project", errors=[], warnings=[]
                )

                response = await async_client.post("/api/v1/import/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test_project.zip"
        assert data["size"] > 0
        assert "temp_path" in data
        assert data["validation"]["valid"] is True

    @pytest.mark.asyncio
    async def test_upload_invalid_format(self, async_client: AsyncClient, tmp_path):
        """Test upload with invalid file format."""
        # Create a non-archive file
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not an archive")

        with open(invalid_file, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = await async_client.post("/api/v1/import/upload", files=files)

        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_import_project_success(self, async_client: AsyncClient):
        """Test successful project import."""
        with patch("app.services.import_.import_service.import_archive") as mock_import:
            mock_import.return_value = ImportResult(
                success=True,
                project_id="imported_project",
                project_name="Imported Project",
                import_duration=5.2,
                statistics={"total_files": 100},
                errors=[],
                warnings=[],
            )

            # Mock temp file existence
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True

                response = await async_client.post(
                    "/api/v1/import/",
                    data={
                        "temp_path": "/tmp/test_archive.zip",
                        "target_name": "imported_project",
                        "options": json.dumps({"overwrite": False, "rename_on_conflict": True}),
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "import_id" in data

    @pytest.mark.asyncio
    async def test_import_with_client_id(self, async_client: AsyncClient):
        """Test import with WebSocket client ID."""
        with patch("app.services.import_.import_service.import_archive") as mock_import:
            mock_import.return_value = ImportResult(
                success=True,
                project_id="ws_project",
                project_name="WS Project",
                import_duration=3.0,
                statistics={},
                errors=[],
                warnings=[],
            )

            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True

                with patch("app.services.websocket.manager.send_personal_message") as mock_ws:
                    response = await async_client.post(
                        "/api/v1/import/?client_id=test-client",
                        data={
                            "temp_path": "/tmp/ws_archive.zip",
                            "target_name": "ws_project",
                            "options": "{}",
                        },
                    )

                    # WebSocket notifications should not be sent synchronously
                    # They'll be sent in the background task

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_import_missing_temp_file(self, async_client: AsyncClient):
        """Test import with missing temp file."""
        response = await async_client.post(
            "/api/v1/import/",
            data={
                "temp_path": "/tmp/nonexistent.zip",
                "target_name": "test_project",
                "options": "{}",
            },
        )

        assert response.status_code == 404
        assert "Upload file not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_validate_archive(self, async_client: AsyncClient, sample_archive_file):
        """Test archive validation endpoint."""
        with open(sample_archive_file, "rb") as f:
            files = {"file": ("test_project.zip", f, "application/zip")}

            with patch("app.services.import_.import_service.validate_archive") as mock_validate:
                mock_validate.return_value = ValidationResult(
                    valid=True,
                    version="2.0",
                    project_id="test_project",
                    errors=[],
                    warnings=["Missing some optional directories"],
                )

                response = await async_client.post("/api/v1/import/validate", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["version"] == "2.0"
        assert len(data["warnings"]) == 1

    @pytest.mark.asyncio
    async def test_cleanup_temp_files(self, async_client: AsyncClient):
        """Test cleanup endpoint."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            with patch("pathlib.Path.iterdir") as mock_iterdir:
                # Mock old files
                old_file = Mock()
                old_file.is_file.return_value = True
                old_file.stat.return_value.st_mtime = 0  # Very old
                old_file.unlink = Mock()

                new_file = Mock()
                new_file.is_file.return_value = True
                new_file.stat.return_value.st_mtime = datetime.now().timestamp()  # Recent
                new_file.unlink = Mock()

                mock_iterdir.return_value = [old_file, new_file]

                response = await async_client.delete("/api/v1/import/cleanup?days=1")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "deleted_files" in data

                # Only old file should be deleted
                old_file.unlink.assert_called_once()
                new_file.unlink.assert_not_called()

    @pytest.mark.asyncio
    async def test_import_invalid_options(self, async_client: AsyncClient):
        """Test import with invalid options JSON."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            response = await async_client.post(
                "/api/v1/import/",
                data={
                    "temp_path": "/tmp/test.zip",
                    "target_name": "test",
                    "options": "invalid json",
                },
            )

        assert response.status_code == 400
        assert "Invalid options format" in response.json()["detail"]
