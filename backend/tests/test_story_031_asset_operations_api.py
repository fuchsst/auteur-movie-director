"""
Tests for STORY-031: Asset Operations API
Verifies all API acceptance criteria for asset operations endpoints.
"""

import tempfile
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.schemas.project import AssetType, ProjectCreate, QualityLevel
from app.services.asset_operations import AssetOperationsService
from app.services.assets import AssetService
from app.services.workspace import WorkspaceService


class TestStory031AssetOperationsAPI:
    """Test STORY-031 API acceptance criteria"""

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
    def asset_service(self, temp_workspace):
        """Create asset service instance"""
        return AssetService(temp_workspace)

    @pytest.fixture
    def operations_service(self, temp_workspace):
        """Create asset operations service instance"""
        return AssetOperationsService(temp_workspace)

    @pytest.fixture
    def client(self, workspace_service, asset_service, operations_service):
        """Create test client with mocked services"""
        with patch("app.api.endpoints.workspace.get_workspace_service") as mock_ws:
            mock_ws.return_value = workspace_service
            with patch("app.api.v1.projects.get_workspace_service") as mock_proj_ws:
                mock_proj_ws.return_value = workspace_service
                with patch("app.api.v1.assets.get_asset_service") as mock_assets:
                    mock_assets.return_value = asset_service
                    with patch(
                        "app.api.v1.asset_operations.get_asset_operations_service"
                    ) as mock_ops:
                        mock_ops.return_value = operations_service
                        with TestClient(app) as client:
                            yield client

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
                        name="API Test Project", quality=QualityLevel.STANDARD
                    )
                    project_path, manifest = workspace_service.create_project(project_data)
                    return {"id": manifest.id, "path": str(project_path), "manifest": manifest}

    @pytest.fixture
    def sample_library_asset(self, asset_service):
        """Create a sample asset in the workspace library"""

        async def _create_asset():
            img = Image.new("RGB", (100, 100), color="purple")
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(temp_file.name, "PNG")

            with open(temp_file.name, "rb") as f:
                content = f.read()

            upload_file = MagicMock()
            upload_file.filename = "api_test_character.png"
            upload_file.read = AsyncMock(return_value=content)

            files = {"image": upload_file}
            asset = await asset_service.import_asset(
                category=AssetType.CHARACTERS,
                name="API Test Character",
                files=files,
                metadata={"description": "Character for API testing"},
                tags=["api", "test"],
            )

            import os

            os.unlink(temp_file.name)
            return asset

        return _create_asset

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes for API testing"""
        img = Image.new("RGB", (50, 50), color="orange")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return img_bytes.getvalue()

    def test_api_031_01_copy_single_asset_endpoint(
        self, client, sample_project, operations_service, sample_library_asset
    ):
        """Test POST /api/v1/projects/{id}/assets/copy endpoint"""
        # Create library asset
        import asyncio

        library_asset = asyncio.run(sample_library_asset())

        # API request to copy asset
        copy_request = {
            "source_category": AssetType.CHARACTERS.value,
            "source_asset_id": library_asset.id,
            "target_name": "API Copied Character",
            "replace_existing": False,
        }

        response = client.post(
            f"/api/v1/projects/{sample_project['id']}/assets/copy", json=copy_request
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "asset" in data
        assert data["asset"]["name"] == "API Copied Character"
        assert data["asset"]["type"] == AssetType.CHARACTERS.value
        assert data["asset"]["id"] != library_asset.id

    def test_api_031_02_batch_copy_assets_endpoint(
        self, client, sample_project, asset_service, sample_image_bytes
    ):
        """Test POST /api/v1/projects/{id}/assets/copy-batch endpoint"""
        # Create multiple library assets
        import asyncio

        async def create_assets():
            library_assets = []
            for i in range(2):
                upload_file = MagicMock()
                upload_file.filename = f"batch_asset_{i}.png"
                upload_file.read = AsyncMock(return_value=sample_image_bytes)

                asset = await asset_service.import_asset(
                    category=AssetType.STYLES,
                    name=f"Batch Asset {i}",
                    files={"image": upload_file},
                    tags=[f"batch{i}"],
                )
                library_assets.append(asset)
            return library_assets

        library_assets = asyncio.run(create_assets())

        # API request for batch copy
        batch_request = {
            "assets": [
                {
                    "source_category": AssetType.STYLES.value,
                    "source_asset_id": asset.id,
                    "target_name": f"Project Asset {i}",
                }
                for i, asset in enumerate(library_assets)
            ],
            "replace_existing": False,
        }

        response = client.post(
            f"/api/v1/projects/{sample_project['id']}/assets/copy-batch", json=batch_request
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["total_requested"] == 2
        assert data["total_copied"] == 2
        assert len(data["copied_assets"]) == 2

    def test_api_031_03_list_project_assets_endpoint(
        self, client, sample_project, operations_service, sample_library_asset
    ):
        """Test GET /api/v1/projects/{id}/assets endpoint"""
        # First copy an asset to the project
        import asyncio

        library_asset = asyncio.run(sample_library_asset())
        asyncio.run(
            operations_service.copy_asset_to_project(
                project_id=sample_project["id"],
                source_category=AssetType.CHARACTERS,
                source_asset_id=library_asset.id,
            )
        )

        # API request to list project assets
        response = client.get(f"/api/v1/projects/{sample_project['id']}/assets")

        assert response.status_code == 200

        data = response.json()
        assert "assets" in data
        assert data["project_id"] == sample_project["id"]
        assert data["total"] == 1
        assert len(data["assets"]) == 1
        assert data["assets"][0]["type"] == AssetType.CHARACTERS.value

    def test_api_031_04_list_project_assets_by_category_endpoint(
        self, client, sample_project, operations_service, sample_library_asset
    ):
        """Test GET /api/v1/projects/{id}/assets/{category} endpoint"""
        # Copy asset to project
        import asyncio

        library_asset = asyncio.run(sample_library_asset())
        asyncio.run(
            operations_service.copy_asset_to_project(
                project_id=sample_project["id"],
                source_category=AssetType.CHARACTERS,
                source_asset_id=library_asset.id,
            )
        )

        # API request to list characters
        response = client.get(
            f"/api/v1/projects/{sample_project['id']}/assets/{AssetType.CHARACTERS.value}"
        )

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["type"] == AssetType.CHARACTERS.value

        # Test empty category
        response = client.get(
            f"/api/v1/projects/{sample_project['id']}/assets/{AssetType.STYLES.value}"
        )

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_api_031_05_get_specific_project_asset_endpoint(
        self, client, sample_project, operations_service, sample_library_asset
    ):
        """Test GET /api/v1/projects/{id}/assets/{category}/{asset_id} endpoint"""
        # Copy asset to project
        import asyncio

        library_asset = asyncio.run(sample_library_asset())
        copied_asset = asyncio.run(
            operations_service.copy_asset_to_project(
                project_id=sample_project["id"],
                source_category=AssetType.CHARACTERS,
                source_asset_id=library_asset.id,
            )
        )

        # API request to get specific asset
        response = client.get(
            f"/api/v1/projects/{sample_project['id']}/assets/{AssetType.CHARACTERS.value}/{copied_asset.id}"
        )

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == copied_asset.id
        assert data["name"] == copied_asset.name
        assert data["type"] == AssetType.CHARACTERS.value

    def test_api_031_06_get_nonexistent_project_asset(self, client, sample_project):
        """Test getting non-existent project asset returns 404"""
        response = client.get(
            f"/api/v1/projects/{sample_project['id']}/assets/{AssetType.CHARACTERS.value}/fake-id"
        )

        assert response.status_code == 404

        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "PROJECT_ASSET_NOT_FOUND"

    def test_api_031_07_remove_project_asset_endpoint(
        self, client, sample_project, operations_service, sample_library_asset
    ):
        """Test DELETE /api/v1/projects/{id}/assets/{category}/{asset_id} endpoint"""
        # Copy asset to project
        import asyncio

        library_asset = asyncio.run(sample_library_asset())
        copied_asset = asyncio.run(
            operations_service.copy_asset_to_project(
                project_id=sample_project["id"],
                source_category=AssetType.CHARACTERS,
                source_asset_id=library_asset.id,
            )
        )

        # API request to remove asset
        response = client.delete(
            f"/api/v1/projects/{sample_project['id']}/assets/{AssetType.CHARACTERS.value}/{copied_asset.id}"
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify asset is removed
        response = client.get(
            f"/api/v1/projects/{sample_project['id']}/assets/{AssetType.CHARACTERS.value}/{copied_asset.id}"
        )
        assert response.status_code == 404

    def test_api_031_08_remove_nonexistent_project_asset(self, client, sample_project):
        """Test removing non-existent project asset returns 404"""
        response = client.delete(
            f"/api/v1/projects/{sample_project['id']}/assets/{AssetType.CHARACTERS.value}/fake-id"
        )

        assert response.status_code == 404

    def test_api_031_09_copy_with_invalid_source_asset(self, client, sample_project):
        """Test copying with invalid source asset ID"""
        copy_request = {
            "source_category": AssetType.CHARACTERS.value,
            "source_asset_id": "invalid-id",
            "target_name": "Should Fail",
        }

        response = client.post(
            f"/api/v1/projects/{sample_project['id']}/assets/copy", json=copy_request
        )

        assert response.status_code == 500  # Should return error

    def test_api_031_10_copy_to_invalid_project(self, client, sample_library_asset):
        """Test copying to non-existent project"""
        import asyncio

        library_asset = asyncio.run(sample_library_asset())

        copy_request = {
            "source_category": AssetType.CHARACTERS.value,
            "source_asset_id": library_asset.id,
        }

        response = client.post("/api/v1/projects/invalid-project/assets/copy", json=copy_request)

        assert response.status_code == 500

    def test_api_031_11_filter_project_assets_by_category(
        self, client, sample_project, operations_service, asset_service, sample_image_bytes
    ):
        """Test filtering project assets by category parameter"""
        import asyncio

        async def setup_mixed_assets():
            # Create and copy character asset
            char_upload = MagicMock()
            char_upload.filename = "character.png"
            char_upload.read = AsyncMock(return_value=sample_image_bytes)

            char_asset = await asset_service.import_asset(
                category=AssetType.CHARACTERS,
                name="Character Asset",
                files={"image": char_upload},
            )

            await operations_service.copy_asset_to_project(
                project_id=sample_project["id"],
                source_category=AssetType.CHARACTERS,
                source_asset_id=char_asset.id,
            )

            # Create and copy style asset
            style_upload = MagicMock()
            style_upload.filename = "style.png"
            style_upload.read = AsyncMock(return_value=sample_image_bytes)

            style_asset = await asset_service.import_asset(
                category=AssetType.STYLES, name="Style Asset", files={"image": style_upload}
            )

            await operations_service.copy_asset_to_project(
                project_id=sample_project["id"],
                source_category=AssetType.STYLES,
                source_asset_id=style_asset.id,
            )

        asyncio.run(setup_mixed_assets())

        # Test filtering by characters
        response = client.get(
            f"/api/v1/projects/{sample_project['id']}/assets",
            params={"category": AssetType.CHARACTERS.value},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["assets"][0]["type"] == AssetType.CHARACTERS.value

        # Test filtering by styles
        response = client.get(
            f"/api/v1/projects/{sample_project['id']}/assets",
            params={"category": AssetType.STYLES.value},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["assets"][0]["type"] == AssetType.STYLES.value

    def test_api_031_12_request_validation(self, client, sample_project):
        """Test request validation for asset operations endpoints"""
        # Test invalid category in copy request
        invalid_request = {
            "source_category": "invalid_category",
            "source_asset_id": "some-id",
        }

        response = client.post(
            f"/api/v1/projects/{sample_project['id']}/assets/copy", json=invalid_request
        )

        assert response.status_code == 422  # Validation error

        # Test empty batch request
        empty_batch = {"assets": []}

        response = client.post(
            f"/api/v1/projects/{sample_project['id']}/assets/copy-batch", json=empty_batch
        )

        assert response.status_code == 200  # Should succeed but copy nothing

    def test_api_031_13_response_format_consistency(
        self, client, sample_project, operations_service, sample_library_asset
    ):
        """Test consistent response formats across endpoints"""
        import asyncio

        library_asset = asyncio.run(sample_library_asset())

        # Test copy response format
        copy_request = {
            "source_category": AssetType.CHARACTERS.value,
            "source_asset_id": library_asset.id,
        }

        copy_response = client.post(
            f"/api/v1/projects/{sample_project['id']}/assets/copy", json=copy_request
        )

        assert copy_response.status_code == 200
        copy_data = copy_response.json()

        # Verify copy response structure
        assert "success" in copy_data
        assert "asset" in copy_data
        assert "message" in copy_data

        asset_id = copy_data["asset"]["id"]

        # Test get response format
        get_response = client.get(
            f"/api/v1/projects/{sample_project['id']}/assets/{AssetType.CHARACTERS.value}/{asset_id}"
        )

        assert get_response.status_code == 200
        get_data = get_response.json()

        # Both should have same asset structure
        required_fields = ["id", "name", "type", "path", "metadata"]
        for field in required_fields:
            assert field in copy_data["asset"]
            assert field in get_data

    def test_api_031_14_openapi_documentation(self, client):
        """Test that asset operations endpoints are documented in OpenAPI spec"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()
        paths = openapi_spec["paths"]

        # Verify asset operations endpoints are documented
        expected_paths = [
            "/api/v1/projects/{project_id}/assets/copy",
            "/api/v1/projects/{project_id}/assets/copy-batch",
            "/api/v1/projects/{project_id}/assets",
            "/api/v1/projects/{project_id}/assets/{category}",
            "/api/v1/projects/{project_id}/assets/{category}/{asset_id}",
        ]

        for path in expected_paths:
            assert path in paths

    def test_api_031_15_error_response_format(self, client, sample_project):
        """Test consistent error response format"""
        # Try to get non-existent asset
        response = client.get(
            f"/api/v1/projects/{sample_project['id']}/assets/{AssetType.CHARACTERS.value}/fake-id"
        )

        assert response.status_code == 404
        error_data = response.json()

        # Verify error structure
        assert "detail" in error_data
        error_detail = error_data["detail"]
        assert "error" in error_detail
        assert "message" in error_detail
        assert "details" in error_detail

        # Verify error content
        assert error_detail["error"] == "PROJECT_ASSET_NOT_FOUND"
        assert "fake-id" in error_detail["message"]
