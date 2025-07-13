"""
Simple tests for STORY-027: Project API Endpoints
Tests core functionality without complex mocking.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.project import ProjectStructureValidation


class TestStory027Simple:
    """Test STORY-027 API endpoints functionality"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        with TestClient(app) as client:
            yield client

    def test_api_documentation_exists(self, client):
        """Test that API documentation is generated"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi = response.json()
        assert "paths" in openapi
        # Check our endpoints are documented
        assert "/api/v1/projects" in openapi["paths"]
        assert "/api/v1/projects/{project_id}" in openapi["paths"]
        assert "/api/v1/projects/search" in openapi["paths"]

    def test_list_projects_endpoint_structure(self, client):
        """Test list projects endpoint returns correct structure"""
        # Mock workspace service
        mock_workspace = MagicMock()
        mock_workspace.list_projects.return_value = []

        with patch("app.api.v1.projects.get_workspace_service", return_value=mock_workspace):
            response = client.get("/api/v1/projects")
            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_get_project_not_found(self, client):
        """Test get project returns 404 for missing project"""
        mock_workspace = MagicMock()
        mock_workspace.get_project_path.return_value = None

        with patch("app.api.v1.projects.get_workspace_service", return_value=mock_workspace):
            response = client.get("/api/v1/projects/nonexistent-id")
            assert response.status_code == 404

            data = response.json()
            assert "error" in data
            # The error middleware wraps it as HTTP_404
            assert data["error"]["code"] == "HTTP_404"

    def test_delete_project_requires_confirmation(self, client):
        """Test delete project requires confirmation parameter"""
        mock_workspace = MagicMock()
        mock_workspace.get_project_path.return_value = Path("/test/project")

        with patch("app.api.v1.projects.get_workspace_service", return_value=mock_workspace):
            # Without confirmation should fail
            response = client.delete("/api/v1/projects/test-id")
            assert response.status_code == 400

            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "HTTP_400"

    def test_validate_project_endpoint(self, client):
        """Test project validation endpoint"""
        mock_workspace = MagicMock()
        mock_workspace.get_project_path.return_value = Path("/test/project")

        # Create mock validation result
        mock_validation = ProjectStructureValidation(
            valid=True,
            missing_directories=[],
            unexpected_directories=[],
            git_initialized=True,
            git_lfs_enabled=True,
            project_json_valid=True,
            errors=[],
        )
        mock_workspace.validate_project_structure.return_value = mock_validation

        with patch("app.api.v1.projects.get_workspace_service", return_value=mock_workspace):
            response = client.post("/api/v1/projects/test-id/validate")
            assert response.status_code == 200

            data = response.json()
            assert data["valid"] is True
            assert data["git_initialized"] is True

    def test_search_projects_requires_query(self, client):
        """Test search endpoint requires query parameter"""
        response = client.get("/api/v1/projects/search")
        assert response.status_code == 422  # Validation error

    def test_list_projects_pagination_params(self, client):
        """Test list projects accepts pagination parameters"""
        mock_workspace = MagicMock()
        mock_workspace.list_projects.return_value = []

        with patch("app.api.v1.projects.get_workspace_service", return_value=mock_workspace):
            response = client.get("/api/v1/projects?skip=10&limit=20")
            assert response.status_code == 200

    def test_list_projects_sorting_params(self, client):
        """Test list projects accepts sorting parameters"""
        mock_workspace = MagicMock()
        mock_workspace.list_projects.return_value = []

        with patch("app.api.v1.projects.get_workspace_service", return_value=mock_workspace):
            response = client.get("/api/v1/projects?sort_by=name&order=asc")
            assert response.status_code == 200

    def test_create_project_validation(self, client):
        """Test create project validates input"""
        # Invalid data - empty name
        invalid_data = {"name": "", "narrative_structure": "three-act"}

        response = client.post("/api/v1/projects", json=invalid_data)
        assert response.status_code == 422

    def test_update_project_endpoint_exists(self, client):
        """Test update project endpoint exists"""
        mock_workspace = MagicMock()
        mock_workspace.get_project_path.return_value = None

        with patch("app.api.v1.projects.get_workspace_service", return_value=mock_workspace):
            response = client.patch("/api/v1/projects/test-id", json={"name": "Updated"})
            assert response.status_code == 404  # Project not found, but endpoint exists
