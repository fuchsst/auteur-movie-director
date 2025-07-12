"""
Tests for file upload functionality.
"""

import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_workspace_service():
    """Mock workspace service"""
    with patch("app.api.endpoints.upload.get_workspace_service") as mock_factory:
        mock_service = MagicMock()
        mock_service.get_project_path.return_value = Path("/workspace/test-project")
        mock_service.create_character_structure.return_value = Path(
            "/workspace/test-project/01_Assets/Characters/TestChar"
        )
        mock_factory.return_value = mock_service
        yield mock_service


@pytest.fixture
def mock_git_service():
    """Mock git service"""
    with patch("app.api.endpoints.upload.git_service") as mock:
        mock.track_large_file = AsyncMock(return_value=True)
        mock.commit_changes = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    with patch("app.api.endpoints.upload.redis_client") as mock:
        mock.publish_progress = AsyncMock()
        yield mock


def test_get_upload_categories():
    """Test getting upload categories"""
    response = client.get("/api/v1/upload/categories")
    assert response.status_code == 200

    data = response.json()
    assert "character" in data
    assert "style" in data
    assert "location" in data

    # Check character category details
    char_category = data["character"]
    assert ".png" in char_category["extensions"]
    assert ".safetensors" in char_category["extensions"]
    assert "01_Assets/Characters" in char_category["directory"]
    assert "character_name" in char_category["required_metadata"]


def test_upload_file_invalid_category(mock_workspace_service, mock_redis_client):
    """Test uploading file with invalid category"""
    # Create test file
    file_content = b"test content"
    files = {"file": ("test.png", io.BytesIO(file_content), "image/png")}

    response = client.post(
        "/api/v1/upload/test-project/invalid_category", files=files, data={"metadata": "{}"}
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Invalid category" in data["error"]["message"]


def test_upload_file_invalid_extension(mock_workspace_service, mock_redis_client):
    """Test uploading file with invalid extension"""
    # Create test file with invalid extension
    file_content = b"test content"
    files = {"file": ("test.exe", io.BytesIO(file_content), "application/x-executable")}

    response = client.post(
        "/api/v1/upload/test-project/character", files=files, data={"metadata": "{}"}
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "not allowed for category" in data["error"]["message"]


def test_upload_file_missing_metadata(mock_workspace_service, mock_redis_client):
    """Test uploading file with missing required metadata"""
    file_content = b"test content"
    files = {"file": ("character.png", io.BytesIO(file_content), "image/png")}

    # Character category requires character_name metadata
    response = client.post(
        "/api/v1/upload/test-project/character",
        files=files,
        data={"metadata": "{}"},  # Missing character_name
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Missing required metadata" in data["error"]["message"]


@patch("builtins.open", new_callable=MagicMock)
@patch("pathlib.Path.stat")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.mkdir")
def test_upload_file_success(
    mock_mkdir,
    mock_exists,
    mock_stat,
    mock_open,
    mock_workspace_service,
    mock_git_service,
    mock_redis_client,
):
    """Test successful file upload"""
    # Setup mocks
    mock_exists.return_value = False  # File doesn't exist
    mock_stat.return_value = MagicMock(st_size=1024)  # 1KB file

    # Mock file writing
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    # Create test file
    file_content = b"test content"
    files = {"file": ("character.png", io.BytesIO(file_content), "image/png")}

    response = client.post(
        "/api/v1/upload/test-project/character",
        files=files,
        data={"metadata": json.dumps({"character_name": "TestCharacter"}), "auto_commit": "true"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "character.png"
    assert "task_id" in data

    # Verify progress was published
    assert mock_redis_client.publish_progress.called

    # Verify file was written
    mock_file.write.assert_called_with(file_content)

    # Verify Git commit was called
    mock_git_service.commit_changes.assert_called_once()


@patch("pathlib.Path.exists")
def test_upload_file_with_duplicate_name(mock_exists, mock_workspace_service, mock_redis_client):
    """Test uploading file when filename already exists"""
    # First call returns True (file exists), subsequent calls return False
    mock_exists.side_effect = [True, False]

    with patch("builtins.open", new_callable=MagicMock):
        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value = MagicMock(st_size=1024)

            file_content = b"test content"
            files = {"file": ("character.png", io.BytesIO(file_content), "image/png")}

            response = client.post(
                "/api/v1/upload/test-project/character",
                files=files,
                data={
                    "metadata": json.dumps({"character_name": "TestCharacter"}),
                    "auto_commit": "false",
                },
            )

            assert response.status_code == 201
            data = response.json()
            # Should have renamed file
            assert data["filename"] == "character_1.png"


@patch("builtins.open", new_callable=MagicMock)
@patch("pathlib.Path.stat")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.mkdir")
def test_upload_large_file_triggers_lfs(
    mock_mkdir,
    mock_exists,
    mock_stat,
    mock_open,
    mock_workspace_service,
    mock_git_service,
    mock_redis_client,
):
    """Test that large files trigger Git LFS tracking"""
    # Setup mocks
    mock_exists.return_value = False
    # Large file (60MB)
    mock_stat.return_value = MagicMock(st_size=60 * 1024 * 1024)

    file_content = b"large file content"
    files = {
        "file": ("large_model.safetensors", io.BytesIO(file_content), "application/octet-stream")
    }

    response = client.post(
        "/api/v1/upload/test-project/character",
        files=files,
        data={"metadata": json.dumps({"character_name": "TestCharacter"}), "auto_commit": "true"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["git_lfs"] is True

    # Verify Git LFS tracking was called
    mock_git_service.track_large_file.assert_called_once()


def test_batch_upload(mock_workspace_service, mock_git_service, mock_redis_client):
    """Test batch file upload"""
    with patch("app.api.endpoints.upload.upload_file") as mock_upload:
        # Mock individual upload responses
        mock_upload.return_value = MagicMock(body={"success": True, "path": "test/path"})

        # Create multiple test files
        files = [
            ("file1", ("char1.png", io.BytesIO(b"content1"), "image/png")),
            ("file2", ("char2.png", io.BytesIO(b"content2"), "image/png")),
        ]

        response = client.post(
            "/api/v1/upload/test-project/batch/character",
            files=files,
            data={
                "metadata": json.dumps({"character_name": "TestCharacter"}),
                "auto_commit": "true",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["uploaded"] == 2

        # Verify batch commit
        mock_git_service.commit_changes.assert_called_once()
