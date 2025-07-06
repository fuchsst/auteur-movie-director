"""
Tests for system information API endpoints.
"""

import platform
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_system_info():
    """Test system info endpoint returns expected data"""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200

    data = response.json()

    # Check required fields
    assert "version" in data
    assert "pythonVersion" in data
    assert "platform" in data
    assert "workspacePath" in data
    assert "apiEndpoint" in data

    # Check Python version matches
    assert data["pythonVersion"] == platform.python_version()

    # Check platform contains system info
    assert platform.system() in data["platform"]

    # Check optional fields exist (may be None)
    assert "nodeVersion" in data
    assert "gitVersion" in data
    assert "gitLFSInstalled" in data
    assert "dockerVersion" in data
    assert "gpuSupport" in data


@patch("subprocess.run")
def test_get_system_info_with_git(mock_run):
    """Test system info with Git installed"""
    # Mock git version command
    git_result = MagicMock()
    git_result.returncode = 0
    git_result.stdout = "git version 2.34.0"

    # Mock git lfs version command
    lfs_result = MagicMock()
    lfs_result.returncode = 0
    lfs_result.stdout = "git-lfs/3.0.0"

    # Configure mock to return different results based on command
    def run_side_effect(cmd, **kwargs):
        if cmd == ["git", "--version"]:
            return git_result
        elif cmd == ["git", "lfs", "version"]:
            return lfs_result
        else:
            result = MagicMock()
            result.returncode = 1
            return result

    mock_run.side_effect = run_side_effect

    response = client.get("/api/v1/system/info")
    assert response.status_code == 200

    data = response.json()
    assert data["gitVersion"] == "2.34.0"
    assert data["gitLFSInstalled"] is True


@patch("subprocess.run")
def test_get_system_info_without_git(mock_run):
    """Test system info when Git is not installed"""
    # Mock subprocess to simulate command not found
    mock_run.side_effect = FileNotFoundError()

    response = client.get("/api/v1/system/info")
    assert response.status_code == 200

    data = response.json()
    assert data["gitVersion"] is None
    assert data["gitLFSInstalled"] is False


@patch("subprocess.run")
def test_get_system_info_with_node(mock_run):
    """Test system info with Node.js installed"""
    node_result = MagicMock()
    node_result.returncode = 0
    node_result.stdout = "v20.0.0"

    def run_side_effect(cmd, **kwargs):
        if cmd == ["node", "--version"]:
            return node_result
        else:
            result = MagicMock()
            result.returncode = 1
            return result

    mock_run.side_effect = run_side_effect

    response = client.get("/api/v1/system/info")
    assert response.status_code == 200

    data = response.json()
    assert data["nodeVersion"] == "20.0.0"  # 'v' prefix should be stripped


@patch("subprocess.run")
def test_get_system_info_with_docker(mock_run):
    """Test system info with Docker installed"""
    docker_result = MagicMock()
    docker_result.returncode = 0
    docker_result.stdout = "Docker version 20.10.21, build baeda1f"

    def run_side_effect(cmd, **kwargs):
        if cmd == ["docker", "--version"]:
            return docker_result
        else:
            result = MagicMock()
            result.returncode = 1
            return result

    mock_run.side_effect = run_side_effect

    response = client.get("/api/v1/system/info")
    assert response.status_code == 200

    data = response.json()
    assert data["dockerVersion"] == "20.10.21"  # Should parse version number


@patch("subprocess.run")
def test_get_system_info_timeout_handling(mock_run):
    """Test system info handles command timeouts gracefully"""
    import subprocess

    # Mock subprocess to simulate timeout
    mock_run.side_effect = subprocess.TimeoutExpired(cmd=["git", "--version"], timeout=5)

    response = client.get("/api/v1/system/info")
    assert response.status_code == 200

    # Should still return valid response with None values
    data = response.json()
    assert data["gitVersion"] is None
