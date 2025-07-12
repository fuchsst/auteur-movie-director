"""Pytest configuration for integration tests"""

import asyncio
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.config import settings
from app.main import app
from app.redis_client import redis_client


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def tmp_workspace(monkeypatch) -> Path:
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = Path(tmpdir) / "test_workspace"
        workspace_path.mkdir(exist_ok=True)

        # Patch the workspace root setting
        monkeypatch.setattr(settings, "workspace_root", str(workspace_path))

        yield workspace_path


@pytest.fixture(autouse=True)
async def clear_redis():
    """Clear Redis before each test."""
    await redis_client.flushdb()
    yield
    await redis_client.flushdb()


@pytest.fixture
def mock_git_lfs(monkeypatch):
    """Mock Git LFS commands for testing."""

    def mock_run(*args, **kwargs):
        # Mock successful Git LFS operations
        class MockResult:
            returncode = 0
            stdout = "Git LFS initialized"
            stderr = ""

        return MockResult()

    import subprocess

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
async def create_test_project(async_client, tmp_workspace):
    """Factory fixture to create test projects."""
    created_projects = []

    async def _create_project(name: str = "test-project", quality: str = "standard"):
        response = await async_client.post(
            "/api/v1/projects", json={"name": name, "quality": quality}
        )
        assert response.status_code == 201
        project = response.json()
        created_projects.append(project["id"])
        return project

    yield _create_project

    # Cleanup
    for project_id in created_projects:
        await async_client.delete(f"/api/v1/projects/{project_id}")


# pytest_plugins is now defined in root conftest.py
