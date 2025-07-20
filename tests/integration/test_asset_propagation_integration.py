"""
Integration tests for Asset Propagation System
STORY-089 Implementation
"""

import pytest
import requests
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, Any


class TestAssetPropagationIntegration:
    """Integration tests for the asset propagation system."""
    
    @pytest.fixture(scope="class")
    def test_project(self):
        """Create a test project for integration tests."""
        return "test_project_integration"
    
    def test_full_asset_propagation_workflow(self, test_project):
        """Test complete asset propagation workflow via API."""
        
        # 1. Add assets at different hierarchy levels
        base_url = "http://localhost:8000/api/v1/asset-propagation"
        
        # Add project-level assets
        assets_to_add = [
            {
                "project_id": test_project,
                "level": "project",
                "level_id": "main",
                "asset_id": "hero_character",
                "asset_type": "character"
            },
            {
                "project_id": test_project,
                "level": "project",
                "level_id": "main",
                "asset_id": "film_style",
                "asset_type": "style"
            },
            {
                "project_id": test_project,
                "level": "act",
                "level_id": "act_1",
                "asset_id": "act_location",
                "asset_type": "location"
            },
            {
                "project_id": test_project,
                "level": "scene",
                "level_id": "scene_1",
                "asset_id": "scene_prop",
                "asset_type": "prop",
                "override_data": {"description": "Hero's main prop"}
            }
        ]
        
        # Add all assets
        for asset in assets_to_add:
            response = requests.post(f"{base_url}/assets", json=asset)
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
        
        # 2. Test asset resolution at take level
        response = requests.get(f"{base_url}/resolve/{test_project}/take/take_1")
        assert response.status_code == 200
        resolved_assets = response.json()
        
        # Should inherit from all parent levels
        assert "character" in resolved_assets["resolved_assets"]
        assert "style" in resolved_assets["resolved_assets"]
        assert "location" in resolved_assets["resolved_assets"]
        assert "prop" in resolved_assets["resolved_assets"]
        
        # 3. Test generation context
        response = requests.get(f"{base_url}/resolve/generation/{test_project}/take/take_1")
        assert response.status_code == 200
        gen_context = response.json()
        
        # Should have formatted data for generative processes
        assert "characters" in gen_context
        assert "styles" in gen_context
        assert "locations" in gen_context
        assert "props" in gen_context
        
        # 4. Test asset usage tracking
        response = requests.get(f"{base_url}/usage/{test_project}/hero_character")
        assert response.status_code == 200
        usage = response.json()
        assert usage["asset_id"] == "hero_character"
        assert usage["usage_count"] >= 1
        
        # 5. Test validation
        response = requests.get(f"{base_url}/validate/{test_project}")
        assert response.status_code == 200
        validation = response.json()
        assert "consistent" in validation
        assert "statistics" in validation
        
        # 6. Test state export
        response = requests.get(f"{base_url}/export/{test_project}")
        assert response.status_code == 200
        export_data = response.json()
        assert export_data["project_id"] == test_project
        assert "contexts" in export_data
        assert "rules" in export_data
        
    def test_propagation_rules_api(self, test_project):
        """Test propagation rules management via API."""
        base_url = "http://localhost:8000/api/v1/asset-propagation"
        
        # Add custom propagation rule
        rule_data = {
            "asset_type": "prop",
            "source_level": "scene",
            "target_level": "shot",
            "propagation_mode": "override",
            "priority": 10,
            "conditions": {"scene_type": "action"}
        }
        
        response = requests.post(f"{base_url}/rules", json=rule_data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["rule"]["propagation_mode"] == "override"
        
    def test_hierarchy_levels_api(self):
        """Test hierarchy levels endpoint."""
        response = requests.get("http://localhost:8000/api/v1/asset-propagation/hierarchy/levels")
        assert response.status_code == 200
        levels = response.json()
        assert "levels" in levels
        assert "project" in levels["levels"]
        assert "act" in levels["levels"]
        assert "scene" in levels["levels"]
        assert "shot" in levels["levels"]
        assert "take" in levels["levels"]
        
    def test_error_handling(self, test_project):
        """Test error handling for invalid requests."""
        base_url = "http://localhost:8000/api/v1/asset-propagation"
        
        # Test invalid level
        response = requests.get(f"{base_url}/resolve/{test_project}/invalid_level/test")
        assert response.status_code == 400
        
        # Test invalid asset type
        invalid_asset = {
            "project_id": test_project,
            "level": "project",
            "level_id": "main",
            "asset_id": "test_asset",
            "asset_type": "invalid_type"
        }
        response = requests.post(f"{base_url}/assets", json=invalid_asset)
        assert response.status_code == 422  # Pydantic validation error


class TestAssetPropagationUI:
    """UI-focused integration tests."""
    
    def test_asset_propagation_panel_loading(self):
        """Test that the AssetPropagationPanel component can load assets correctly."""
        # This would typically be tested with Playwright or similar
        # For now, we'll verify the component structure
        
        # Check that the panel component exists
        panel_path = Path("frontend/src/lib/components/asset-propagation/AssetPropagationPanel.svelte")
        assert panel_path.exists()
        
        # Check that it has the required exports
        content = panel_path.read_text()
        assert "export let projectId" in content
        assert "export let level" in content
        assert "export let levelId" in content
        
    def test_asset_propagation_store_integration(self):
        """Test store integration with API services."""
        # Check that the store uses the correct API endpoints
        store_path = Path("frontend/src/lib/services/asset-propagation.ts")
        assert store_path.exists()
        
        content = store_path.read_text()
        assert "/api/v1/asset-propagation" in content
        assert "resolveAssets" in content
        assert "resolveForGeneration" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])