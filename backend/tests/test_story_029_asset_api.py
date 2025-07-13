"""
Tests for STORY-029: Asset API Endpoints
Verifies all API acceptance criteria for asset management.
"""

import tempfile
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.schemas.project import AssetType
from app.services.assets import AssetService


class TestStory029AssetAPI:
    """Test STORY-029 API acceptance criteria"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir)

    @pytest.fixture
    def asset_service(self, temp_workspace):
        """Create asset service instance"""
        return AssetService(temp_workspace)

    @pytest.fixture
    def client(self, asset_service):
        """Create test client with mocked asset service"""
        with patch("app.api.v1.assets.get_asset_service") as mock_get_service:
            mock_get_service.return_value = asset_service
            with TestClient(app) as client:
                yield client

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes for file upload testing"""
        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return img_bytes.getvalue()

    def test_api_029_01_list_all_assets(self, client):
        """Test GET /api/v1/assets endpoint"""
        response = client.get("/api/v1/assets")
        assert response.status_code == 200

        data = response.json()
        assert "assets" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert isinstance(data["assets"], list)

    def test_api_029_02_list_assets_by_category(self, client):
        """Test GET /api/v1/assets/{category} endpoint"""
        response = client.get(f"/api/v1/assets/{AssetType.CHARACTERS.value}")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_api_029_03_get_asset_statistics(self, client):
        """Test GET /api/v1/assets/stats endpoint"""
        response = client.get("/api/v1/assets/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_assets" in data
        assert "by_category" in data
        assert "total_size_bytes" in data
        assert "library_path" in data

    def test_api_029_04_search_assets(self, client):
        """Test GET /api/v1/assets/search endpoint"""
        response = client.get("/api/v1/assets/search", params={"q": "test"})
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_api_029_05_import_character_asset(self, client, sample_image_bytes):
        """Test POST /api/v1/assets/{category} endpoint for character import"""
        files = [("files", ("character.png", sample_image_bytes, "image/png"))]

        data = {
            "name": "Test Character",
            "tags": "fantasy,warrior,female",
            "description": "A test character for the story",
        }

        response = client.post(
            f"/api/v1/assets/{AssetType.CHARACTERS.value}", data=data, files=files
        )

        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "asset" in result
        assert result["asset"]["name"] == "Test Character"
        assert result["asset"]["type"] == AssetType.CHARACTERS.value

    def test_api_029_06_import_multiple_file_asset(self, client, sample_image_bytes):
        """Test importing asset with multiple files"""
        # Create mock model file
        model_bytes = b"fake model data for testing"

        files = [
            ("files", ("character.png", sample_image_bytes, "image/png")),
            ("files", ("model.safetensors", model_bytes, "application/octet-stream")),
        ]

        data = {
            "name": "Multi-File Character",
            "tags": "complete,with_model",
            "description": "Character with both image and model",
        }

        response = client.post(
            f"/api/v1/assets/{AssetType.CHARACTERS.value}", data=data, files=files
        )

        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert result["asset"]["name"] == "Multi-File Character"

    def test_api_029_07_get_specific_asset(self, client, asset_service, sample_image_bytes):
        """Test GET /api/v1/assets/{category}/{asset_id} endpoint"""
        # First import an asset
        files = [("files", ("test.png", sample_image_bytes, "image/png"))]
        data = {"name": "Specific Asset Test"}

        import_response = client.post(
            f"/api/v1/assets/{AssetType.STYLES.value}", data=data, files=files
        )

        assert import_response.status_code == 200
        imported_asset = import_response.json()["asset"]
        asset_id = imported_asset["id"]

        # Now get the specific asset
        response = client.get(f"/api/v1/assets/{AssetType.STYLES.value}/{asset_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == asset_id
        assert data["name"] == "Specific Asset Test"
        assert data["type"] == AssetType.STYLES.value

    def test_api_029_08_get_nonexistent_asset(self, client):
        """Test getting a non-existent asset returns 404"""
        response = client.get(f"/api/v1/assets/{AssetType.CHARACTERS.value}/fake-id")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["error"] == "ASSET_NOT_FOUND"

    def test_api_029_09_update_asset_metadata(self, client, sample_image_bytes):
        """Test PATCH /api/v1/assets/{category}/{asset_id} endpoint"""
        # First import an asset
        files = [("files", ("update_test.png", sample_image_bytes, "image/png"))]
        data = {"name": "Original Name", "description": "Original description"}

        import_response = client.post(
            f"/api/v1/assets/{AssetType.LOCATIONS.value}", data=data, files=files
        )

        assert import_response.status_code == 200
        asset_id = import_response.json()["asset"]["id"]

        # Update the asset
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "tags": ["updated", "modified"],
        }

        response = client.patch(
            f"/api/v1/assets/{AssetType.LOCATIONS.value}/{asset_id}", json=update_data
        )

        assert response.status_code == 200

        updated_asset = response.json()
        assert updated_asset["name"] == "Updated Name"
        assert updated_asset["metadata"]["metadata"]["description"] == "Updated description"
        assert updated_asset["metadata"]["tags"] == ["updated", "modified"]

    def test_api_029_10_delete_asset(self, client, sample_image_bytes):
        """Test DELETE /api/v1/assets/{category}/{asset_id} endpoint"""
        # First import an asset
        files = [("files", ("delete_test.png", sample_image_bytes, "image/png"))]
        data = {"name": "To Be Deleted"}

        import_response = client.post(
            f"/api/v1/assets/{AssetType.MUSIC.value}", data=data, files=files
        )

        assert import_response.status_code == 200
        asset_id = import_response.json()["asset"]["id"]

        # Delete the asset
        response = client.delete(f"/api/v1/assets/{AssetType.MUSIC.value}/{asset_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify asset is deleted
        get_response = client.get(f"/api/v1/assets/{AssetType.MUSIC.value}/{asset_id}")
        assert get_response.status_code == 404

    def test_api_029_11_delete_nonexistent_asset(self, client):
        """Test deleting a non-existent asset returns 404"""
        response = client.delete(f"/api/v1/assets/{AssetType.CHARACTERS.value}/fake-id")
        assert response.status_code == 404

    def test_api_029_12_filter_by_tags(self, client, sample_image_bytes):
        """Test filtering assets by tags"""
        # Import assets with different tags
        test_assets = [
            {"name": "Fantasy Hero", "tags": "fantasy,hero,magic"},
            {"name": "Sci-Fi Soldier", "tags": "scifi,soldier,tech"},
            {"name": "Fantasy Villain", "tags": "fantasy,villain,dark"},
        ]

        for asset_data in test_assets:
            files = [("files", (f"{asset_data['name']}.png", sample_image_bytes, "image/png"))]
            client.post(
                f"/api/v1/assets/{AssetType.CHARACTERS.value}", data=asset_data, files=files
            )

        # Filter by fantasy tag
        response = client.get("/api/v1/assets", params={"tags": "fantasy"})
        assert response.status_code == 200

        data = response.json()
        fantasy_assets = data["assets"]
        assert len(fantasy_assets) == 2

        # Verify all returned assets have fantasy tag
        for asset in fantasy_assets:
            assert "fantasy" in asset["metadata"]["tags"]

    def test_api_029_13_pagination_parameters(self, client, sample_image_bytes):
        """Test pagination parameters in list endpoint"""
        # Import multiple assets
        for i in range(15):
            files = [("files", (f"asset_{i}.png", sample_image_bytes, "image/png"))]
            data = {"name": f"Asset {i:02d}"}
            client.post(f"/api/v1/assets/{AssetType.STYLES.value}", data=data, files=files)

        # Test first page
        response = client.get("/api/v1/assets", params={"limit": 10, "offset": 0})
        assert response.status_code == 200

        data = response.json()
        assert len(data["assets"]) == 10
        assert data["offset"] == 0
        assert data["limit"] == 10

        # Test second page
        response = client.get("/api/v1/assets", params={"limit": 10, "offset": 10})
        assert response.status_code == 200

        data = response.json()
        assert len(data["assets"]) == 5  # Remaining assets

    def test_api_029_14_search_with_category_filter(self, client, sample_image_bytes):
        """Test search with category filtering"""
        # Import assets in different categories
        character_files = [("files", ("character.png", sample_image_bytes, "image/png"))]
        style_files = [("files", ("style.png", sample_image_bytes, "image/png"))]

        client.post(
            f"/api/v1/assets/{AssetType.CHARACTERS.value}",
            data={"name": "Warrior Character"},
            files=character_files,
        )

        client.post(
            f"/api/v1/assets/{AssetType.STYLES.value}",
            data={"name": "Warrior Style"},
            files=style_files,
        )

        # Search for "Warrior" in characters only
        response = client.get(
            "/api/v1/assets/search", params={"q": "Warrior", "category": AssetType.CHARACTERS.value}
        )

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["type"] == AssetType.CHARACTERS.value

    def test_api_029_15_invalid_file_upload(self, client):
        """Test validation of file uploads"""
        # Test with no files
        response = client.post(
            f"/api/v1/assets/{AssetType.CHARACTERS.value}", data={"name": "No Files Test"}, files=[]
        )

        assert response.status_code == 400

    def test_api_029_16_request_validation(self, client, sample_image_bytes):
        """Test request validation for various endpoints"""
        files = [("files", ("test.png", sample_image_bytes, "image/png"))]

        # Test with empty name
        response = client.post(
            f"/api/v1/assets/{AssetType.CHARACTERS.value}", data={"name": ""}, files=files
        )

        assert response.status_code == 422  # Validation error

        # Test search with empty query
        response = client.get("/api/v1/assets/search", params={"q": ""})
        assert response.status_code == 422

    def test_api_029_17_response_format_consistency(self, client, sample_image_bytes):
        """Test consistent response formats across endpoints"""
        files = [("files", ("format_test.png", sample_image_bytes, "image/png"))]
        data = {"name": "Format Test Asset"}

        # Import asset
        import_response = client.post(
            f"/api/v1/assets/{AssetType.CHARACTERS.value}", data=data, files=files
        )

        assert import_response.status_code == 200
        import_data = import_response.json()

        # Verify import response format
        assert "success" in import_data
        assert "asset" in import_data
        assert "message" in import_data

        asset_id = import_data["asset"]["id"]

        # Get asset and verify format consistency
        get_response = client.get(f"/api/v1/assets/{AssetType.CHARACTERS.value}/{asset_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()

        # Both should have same asset structure
        required_fields = ["id", "name", "type", "path", "metadata"]
        for field in required_fields:
            assert field in import_data["asset"]
            assert field in get_data

    def test_api_029_18_openapi_documentation(self, client):
        """Test that API endpoints are documented in OpenAPI spec"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()
        paths = openapi_spec["paths"]

        # Verify asset endpoints are documented
        expected_paths = [
            "/api/v1/assets",
            "/api/v1/assets/search",
            "/api/v1/assets/stats",
            "/api/v1/assets/{category}",
            "/api/v1/assets/{category}/{asset_id}",
        ]

        for path in expected_paths:
            assert path in paths

    def test_api_029_19_error_response_format(self, client):
        """Test consistent error response format"""
        # Try to get non-existent asset
        response = client.get(f"/api/v1/assets/{AssetType.CHARACTERS.value}/fake-id")
        assert response.status_code == 404

        error_data = response.json()
        assert "error" in error_data

        # For 404 errors, we expect structured error format
        error_detail = error_data["detail"]
        assert "error" in error_detail
        assert "message" in error_detail
        assert "details" in error_detail

    def test_api_029_20_concurrent_access_handling(self, client, sample_image_bytes):
        """Test concurrent access to asset operations"""
        import threading
        import time

        results = []

        def import_asset(index):
            files = [("files", (f"concurrent_{index}.png", sample_image_bytes, "image/png"))]
            data = {"name": f"Concurrent Asset {index}"}

            response = client.post(
                f"/api/v1/assets/{AssetType.CHARACTERS.value}", data=data, files=files
            )
            results.append(response.status_code)

        # Create multiple threads to import assets simultaneously
        threads = []
        for i in range(5):
            thread = threading.Thread(target=import_asset, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All imports should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5
