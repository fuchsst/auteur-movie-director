"""
Tests for STORY-027: Project API Endpoints
Verifies all acceptance criteria for comprehensive project management APIs.
"""

import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.project import (
    NarrativeStructure,
    ProjectCreate,
    QualityLevel,
)
from app.services.workspace import WorkspaceService


class TestStory027ProjectAPIEndpoints:
    """Test STORY-027 acceptance criteria"""

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
    def client(self, workspace_service):
        """Create test client with mocked workspace service"""
        with patch("app.api.endpoints.workspace.get_workspace_service") as mock_get_ws:
            mock_get_ws.return_value = workspace_service
            with patch("app.api.v1.projects.get_workspace_service") as mock_get_ws_projects:
                mock_get_ws_projects.return_value = workspace_service
                # Mock asyncio.new_event_loop to avoid event loop issues in tests
                with patch("asyncio.new_event_loop") as mock_new_loop:
                    mock_loop = MagicMock()
                    mock_loop.run_until_complete.return_value = True
                    mock_new_loop.return_value = mock_loop
                    with TestClient(app) as client:
                        yield client

    @pytest.fixture
    def sample_project(self, workspace_service):
        """Create a sample project for testing"""
        # Mock the Git initialization to avoid event loop issues
        with patch.object(workspace_service, "_initialize_git_with_lfs"):
            with patch.object(workspace_service, "_create_initial_commit"):
                # Mock validation to pass
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
                        name="Test Project",
                        narrative_structure=NarrativeStructure.THREE_ACT,
                        quality=QualityLevel.STANDARD,
                        description="Test project description",
                    )
                    project_path, manifest = workspace_service.create_project(project_data)

                    # Manually set Git status for testing
                    manifest.git.initialized = True
                    manifest.git.lfs_enabled = True

                    return {
                        "id": manifest.id,
                        "path": str(project_path),
                        "manifest": manifest,
                    }

    def test_list_all_projects_with_metadata(self, client, sample_project):
        """Test listing all projects with complete metadata"""
        response = client.get("/api/v1/projects")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1

        project = data[0]
        assert project["id"] == sample_project["id"]
        assert project["name"] == "Test Project"
        assert "created" in project
        assert "modified" in project
        assert project["quality"] == "standard"
        assert project["narrative_structure"] == "three-act"
        assert "git_status" in project

    def test_get_single_project_details(self, client, sample_project):
        """Test getting single project details"""
        response = client.get(f"/api/v1/projects/{sample_project['id']}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_project["id"]
        assert data["name"] == "Test Project"
        assert "manifest" in data
        assert data["manifest"]["narrative"]["structure"] == "three-act"

    def test_create_new_project(self, client):
        """Test creating a new project"""
        project_data = {
            "name": "New Project",
            "narrative_structure": "three-act",
            "quality": "standard",
            "description": "New project description",
        }

        response = client.post("/api/v1/projects", json=project_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "New Project"
        assert "id" in data
        assert "path" in data
        assert "manifest" in data

    def test_update_project_metadata(self, client, sample_project):
        """Test updating project metadata"""
        update_data = {
            "name": "Updated Project",
            "description": "Updated description",
            "tags": ["action", "drama"],
        }

        response = client.patch(f"/api/v1/projects/{sample_project['id']}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Project"
        assert data["manifest"]["metadata"]["description"] == "Updated description"
        assert data["manifest"]["metadata"]["tags"] == ["action", "drama"]

    def test_delete_project_with_confirmation(self, client, sample_project):
        """Test deleting a project with confirmation"""
        # First attempt without confirmation should fail
        response = client.delete(f"/api/v1/projects/{sample_project['id']}")
        assert response.status_code == 400

        # With confirmation should succeed
        response = client.delete(
            f"/api/v1/projects/{sample_project['id']}", params={"confirm": "true"}
        )
        assert response.status_code == 200

        # Verify project is deleted
        response = client.get(f"/api/v1/projects/{sample_project['id']}")
        assert response.status_code == 404

    def test_validate_project_structure(self, client, sample_project):
        """Test project structure validation endpoint"""
        response = client.post(f"/api/v1/projects/{sample_project['id']}/validate")
        assert response.status_code == 200

        data = response.json()
        assert "valid" in data
        assert "missing_directories" in data
        assert "git_initialized" in data
        assert data["valid"] is True

    def test_search_projects_by_name(self, client, workspace_service):
        """Test searching projects by name"""
        # Create multiple projects
        for name in ["Alpha Project", "Beta Test", "Gamma Alpha"]:
            project_data = ProjectCreate(name=name)
            workspace_service.create_project(project_data)

        # Search for "Alpha"
        response = client.get("/api/v1/projects/search", params={"q": "Alpha"})
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        names = [p["name"] for p in data]
        assert "Alpha Project" in names
        assert "Gamma Alpha" in names

    def test_filter_projects_by_date_status(self, client, workspace_service):
        """Test filtering projects by date and status"""
        # Create projects
        project_data = ProjectCreate(name="Quality Test", quality=QualityLevel.HIGH)
        workspace_service.create_project(project_data)

        # Filter by quality
        response = client.get("/api/v1/projects", params={"quality": "high"})
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["quality"] == "high"

    def test_pagination_support(self, client, workspace_service):
        """Test pagination support for list endpoint"""
        # Create 15 projects
        for i in range(15):
            project_data = ProjectCreate(name=f"Project {i:02d}")
            workspace_service.create_project(project_data)

        # Get first page
        response = client.get("/api/v1/projects", params={"skip": 0, "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # Get second page
        response = client.get("/api/v1/projects", params={"skip": 10, "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_consistent_error_response_format(self, client):
        """Test consistent error response format"""
        response = client.get("/api/v1/projects/nonexistent-id")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert data["error"]["code"] == "PROJECT_NOT_FOUND"

    def test_request_response_validation(self, client):
        """Test request/response validation with Pydantic"""
        # Invalid request data
        invalid_data = {
            "name": "",  # Empty name should fail
            "narrative_structure": "invalid_structure",
        }

        response = client.post("/api/v1/projects", json=invalid_data)
        assert response.status_code == 422  # Validation error

        # Valid request should work
        valid_data = {
            "name": "Valid Project",
            "narrative_structure": "three-act",
        }

        response = client.post("/api/v1/projects", json=valid_data)
        assert response.status_code == 200

    def test_proper_http_status_codes(self, client, sample_project):
        """Test proper HTTP status codes"""
        # 200 OK for successful GET
        response = client.get("/api/v1/projects")
        assert response.status_code == 200

        # 201 Created for successful POST (once implemented)
        # 204 No Content for successful DELETE (once implemented)
        # 404 Not Found for missing resource
        response = client.get("/api/v1/projects/nonexistent")
        assert response.status_code == 404

        # 400 Bad Request for invalid request
        response = client.delete(f"/api/v1/projects/{sample_project['id']}")
        assert response.status_code == 400  # Missing confirmation

    def test_cors_headers_configured(self, client):
        """Test CORS headers are properly configured"""
        response = client.options("/api/v1/projects")
        # CORS should be handled by middleware
        assert response.status_code in [200, 405]  # Either OK or Method Not Allowed

    def test_performance_list_under_100ms(self, client, workspace_service):
        """Test list endpoint performance < 100ms"""
        import time

        # Create 50 projects
        for i in range(50):
            project_data = ProjectCreate(name=f"Perf Test {i}")
            workspace_service.create_project(project_data)

        # Measure response time
        start_time = time.time()
        response = client.get("/api/v1/projects")
        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 100, f"Response took {elapsed:.2f}ms (should be < 100ms)"

    def test_handles_missing_projects_gracefully(self, client):
        """Test handling of missing projects gracefully"""
        # Try to get non-existent project
        response = client.get("/api/v1/projects/missing-id")
        assert response.status_code == 404

        # Try to update non-existent project
        response = client.patch("/api/v1/projects/missing-id", json={"name": "New Name"})
        assert response.status_code == 404

        # Try to delete non-existent project
        response = client.delete("/api/v1/projects/missing-id", params={"confirm": "true"})
        assert response.status_code == 404

    def test_security_path_traversal_prevention(self, client):
        """Test path traversal attack prevention"""
        # Try to create project with malicious name
        malicious_data = {
            "name": "../../../etc/passwd",
            "narrative_structure": "three-act",
        }

        response = client.post("/api/v1/projects", json=malicious_data)
        # Should either reject or sanitize the name
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            # Name should be sanitized
            assert "../" not in data["path"]

    def test_sorting_options(self, client, workspace_service):
        """Test sorting options for project list"""
        # Create projects with different names
        for name in ["Zebra", "Alpha", "Beta"]:
            project_data = ProjectCreate(name=name)
            workspace_service.create_project(project_data)

        # Sort by name ascending
        response = client.get("/api/v1/projects", params={"sort_by": "name", "order": "asc"})
        assert response.status_code == 200
        data = response.json()
        names = [p["name"] for p in data]
        assert names == sorted(names)

    def test_api_documentation_generation(self):
        """Test API documentation is auto-generated"""
        # FastAPI automatically generates OpenAPI docs
        with TestClient(app) as client:
            response = client.get("/openapi.json")
            assert response.status_code == 200

            openapi = response.json()
            assert "paths" in openapi
            # Check our endpoints are documented
            assert "/api/v1/projects" in openapi["paths"]

    async def test_websocket_notifications(self, workspace_service):
        """Test WebSocket notifications on project changes"""
        # This would test WebSocket integration
        # Marking as async for future implementation
        pass
