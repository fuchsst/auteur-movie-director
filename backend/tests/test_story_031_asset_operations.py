"""
Tests for STORY-031: Asset Operations
Verifies all acceptance criteria for copying assets from library to projects.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile
from PIL import Image

from app.schemas.project import AssetReference, AssetType, ProjectCreate, QualityLevel
from app.services.asset_operations import AssetOperationsService
from app.services.assets import AssetService
from app.services.workspace import WorkspaceService


class TestStory031AssetOperations:
    """Test STORY-031 acceptance criteria"""

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
    def operations_service(self, temp_workspace, workspace_service, asset_service):
        """Create asset operations service instance"""
        return AssetOperationsService(temp_workspace, asset_service, workspace_service)

    @pytest.fixture
    def sample_project(self, workspace_service):
        """Create a sample project for testing"""
        # Mock Git operations to avoid event loop issues
        with patch.object(workspace_service, "_initialize_git_with_lfs"):
            with patch.object(workspace_service, "_create_initial_commit"):
                # Mock validation
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
                    project_data = ProjectCreate(name="Test Project", quality=QualityLevel.STANDARD)
                    project_path, manifest = workspace_service.create_project(project_data)
                    return {"id": manifest.id, "path": str(project_path), "manifest": manifest}

    @pytest.fixture
    def sample_library_asset(self, asset_service):
        """Create a sample asset in the workspace library"""

        async def _create_asset():
            # Create test image
            img = Image.new("RGB", (100, 100), color="blue")
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(temp_file.name, "PNG")

            # Create UploadFile mock
            with open(temp_file.name, "rb") as f:
                content = f.read()

            upload_file = MagicMock(spec=UploadFile)
            upload_file.filename = "test_character.png"
            upload_file.read = AsyncMock(return_value=content)

            # Import to library
            files = {"image": upload_file}
            asset = await asset_service.import_asset(
                category=AssetType.CHARACTERS,
                name="Library Character",
                files=files,
                metadata={"description": "Test character from library"},
                tags=["test", "character"],
            )

            # Cleanup temp file
            Path(temp_file.name).unlink(missing_ok=True)
            return asset

        return _create_asset

    async def test_ac_031_01_copy_single_asset_to_project(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test copying a single asset from library to project"""
        # Create library asset
        library_asset = await sample_library_asset()

        # Copy to project
        copied_asset = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
            target_name="Project Character",
            replace_existing=False,
        )

        # Verify copied asset
        assert isinstance(copied_asset, AssetReference)
        assert copied_asset.name == "Project Character"
        assert copied_asset.type == AssetType.CHARACTERS.value
        assert copied_asset.id != library_asset.id  # Should have new ID

        # Verify asset exists in project
        project_path = Path(sample_project["path"])
        asset_path = project_path / copied_asset.path
        assert asset_path.exists()
        assert (asset_path / "test_character.png").exists()
        assert (asset_path / "asset.json").exists()

        # Verify metadata contains source tracking
        with open(asset_path / "asset.json") as f:
            metadata = json.load(f)

        assert "source" in metadata
        assert metadata["source"]["library_asset_id"] == library_asset.id
        assert metadata["source"]["library_asset_name"] == library_asset.name
        assert metadata["source"]["copied_from"] == "workspace_library"

    async def test_ac_031_02_handle_name_conflicts(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test handling asset name conflicts with auto-renaming"""
        library_asset = await sample_library_asset()

        # Copy first asset
        copied_asset_1 = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
            target_name="Character",
        )

        # Copy second asset with same name
        copied_asset_2 = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
            target_name="Character",
        )

        # Verify naming
        assert copied_asset_1.name == "Character"
        assert copied_asset_2.name == "Character_2"

        # Both assets should exist
        project_path = Path(sample_project["path"])
        assert (project_path / copied_asset_1.path).exists()
        assert (project_path / copied_asset_2.path).exists()

    async def test_ac_031_03_replace_existing_asset(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test replacing existing asset when replace_existing=True"""
        library_asset = await sample_library_asset()

        # Copy first asset
        copied_asset_1 = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
            target_name="Character",
        )

        original_id = copied_asset_1.id

        # Replace with new copy
        copied_asset_2 = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
            target_name="Character",
            replace_existing=True,
        )

        # Should have same name but different ID
        assert copied_asset_2.name == "Character"
        assert copied_asset_2.id != original_id

        # Only one asset should exist in project
        project_assets = await operations_service.get_project_assets(
            sample_project["id"], AssetType.CHARACTERS
        )
        character_assets = [asset for asset in project_assets if asset.name == "Character"]
        assert len(character_assets) == 1

    async def test_ac_031_04_batch_copy_assets(
        self, operations_service, asset_service, sample_project
    ):
        """Test copying multiple assets in a batch operation"""
        # Create multiple library assets
        library_assets = []
        for i in range(3):
            # Create test assets
            img = Image.new("RGB", (100, 100), color="red")
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(temp_file.name, "PNG")

            with open(temp_file.name, "rb") as f:
                content = f.read()

            upload_file = MagicMock(spec=UploadFile)
            upload_file.filename = f"asset_{i}.png"
            upload_file.read = AsyncMock(return_value=content)

            files = {"image": upload_file}
            asset = await asset_service.import_asset(
                category=AssetType.STYLES,
                name=f"Style Asset {i}",
                files=files,
                tags=[f"batch{i}"],
            )
            library_assets.append(asset)
            Path(temp_file.name).unlink(missing_ok=True)

        # Batch copy to project
        asset_requests = [
            {
                "category": AssetType.STYLES.value,
                "asset_id": asset.id,
                "target_name": f"Project Style {i}",
            }
            for i, asset in enumerate(library_assets)
        ]

        copied_assets = await operations_service.copy_multiple_assets_to_project(
            project_id=sample_project["id"], asset_requests=asset_requests
        )

        # Verify all assets copied
        assert len(copied_assets) == 3
        for i, copied_asset in enumerate(copied_assets):
            assert copied_asset.name == f"Project Style {i}"
            assert copied_asset.type == AssetType.STYLES.value

        # Verify assets exist in project
        project_assets = await operations_service.get_project_assets(
            sample_project["id"], AssetType.STYLES
        )
        assert len(project_assets) == 3

    async def test_ac_031_05_atomic_operations_rollback(
        self, operations_service, asset_service, sample_project
    ):
        """Test atomic batch operations with rollback on failure"""
        # Create one valid asset
        img = Image.new("RGB", (100, 100), color="green")
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(temp_file.name, "PNG")

        with open(temp_file.name, "rb") as f:
            content = f.read()

        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "valid_asset.png"
        upload_file.read = AsyncMock(return_value=content)

        valid_asset = await asset_service.import_asset(
            category=AssetType.LOCATIONS, name="Valid Asset", files={"image": upload_file}
        )
        Path(temp_file.name).unlink(missing_ok=True)

        # Create batch with valid and invalid asset IDs
        asset_requests = [
            {"category": AssetType.LOCATIONS.value, "asset_id": valid_asset.id},
            {"category": AssetType.LOCATIONS.value, "asset_id": "invalid-id"},
        ]

        # Batch operation should fail and rollback
        with pytest.raises(Exception):
            await operations_service.copy_multiple_assets_to_project(
                project_id=sample_project["id"], asset_requests=asset_requests
            )

        # Verify no assets were copied (rollback successful)
        project_assets = await operations_service.get_project_assets(
            sample_project["id"], AssetType.LOCATIONS
        )
        assert len(project_assets) == 0

    async def test_ac_031_06_list_project_assets(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test listing assets copied to a project"""
        library_asset = await sample_library_asset()

        # Copy asset to project
        await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
        )

        # List all project assets
        all_project_assets = await operations_service.get_project_assets(sample_project["id"])
        assert len(all_project_assets) == 1
        assert all_project_assets[0].type == AssetType.CHARACTERS.value

        # List by category
        character_assets = await operations_service.get_project_assets(
            sample_project["id"], AssetType.CHARACTERS
        )
        assert len(character_assets) == 1

        style_assets = await operations_service.get_project_assets(
            sample_project["id"], AssetType.STYLES
        )
        assert len(style_assets) == 0

    async def test_ac_031_07_remove_project_asset(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test removing assets from projects"""
        library_asset = await sample_library_asset()

        # Copy asset to project
        copied_asset = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
        )

        # Verify asset exists
        project_assets = await operations_service.get_project_assets(sample_project["id"])
        assert len(project_assets) == 1

        # Remove asset
        success = await operations_service.remove_project_asset(
            project_id=sample_project["id"],
            category=AssetType.CHARACTERS,
            asset_id=copied_asset.id,
        )
        assert success is True

        # Verify asset removed
        project_assets = await operations_service.get_project_assets(sample_project["id"])
        assert len(project_assets) == 0

        # Library asset should still exist
        library_assets = await operations_service.asset_service.list_assets(
            category=AssetType.CHARACTERS
        )
        assert len(library_assets) == 1

    async def test_ac_031_08_preserve_metadata_during_copy(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test that asset metadata is preserved during copy operations"""
        library_asset = await sample_library_asset()

        # Copy asset
        copied_asset = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
        )

        # Verify metadata preservation
        assert copied_asset.metadata["tags"] == ["test", "character"]
        assert copied_asset.metadata["metadata"]["description"] == "Test character from library"

        # Verify source tracking
        assert "source" in copied_asset.metadata
        assert copied_asset.metadata["source"]["library_asset_id"] == library_asset.id

    async def test_ac_031_09_project_manifest_updates(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test that project manifest is updated with asset references"""
        library_asset = await sample_library_asset()

        # Copy asset
        copied_asset = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
        )

        # Verify manifest is updated
        project_path = Path(sample_project["path"])
        manifest_file = project_path / "project.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        # Check asset reference in manifest
        assert "assets" in manifest
        assert AssetType.CHARACTERS.value in manifest["assets"]

        character_refs = manifest["assets"][AssetType.CHARACTERS.value]
        assert len(character_refs) == 1

        asset_ref = character_refs[0]
        assert asset_ref["id"] == copied_asset.id
        assert asset_ref["source_id"] == library_asset.id

    async def test_ac_031_10_error_handling(self, operations_service, sample_project):
        """Test error handling for various failure scenarios"""
        # Test copy with invalid source asset
        with pytest.raises(Exception, match="Source asset .* not found"):
            await operations_service.copy_asset_to_project(
                project_id=sample_project["id"],
                source_category=AssetType.CHARACTERS,
                source_asset_id="invalid-id",
            )

        # Test copy to invalid project
        with pytest.raises(Exception, match="Project .* not found"):
            await operations_service.copy_asset_to_project(
                project_id="invalid-project",
                source_category=AssetType.CHARACTERS,
                source_asset_id="any-id",
            )

    async def test_ac_031_11_file_integrity_verification(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test file integrity during copy operations"""
        library_asset = await sample_library_asset()

        # Copy asset
        copied_asset = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
        )

        # Verify files copied correctly
        project_path = Path(sample_project["path"])
        copied_asset_path = project_path / copied_asset.path
        library_asset_path = operations_service.asset_service.library_path / library_asset.path

        # Check file exists and has same size
        copied_file = copied_asset_path / "test_character.png"
        original_file = library_asset_path / "test_character.png"

        assert copied_file.exists()
        assert original_file.exists()
        assert copied_file.stat().st_size == original_file.stat().st_size

    async def test_ac_031_12_concurrent_operations_handling(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test handling of concurrent copy operations"""
        library_asset = await sample_library_asset()

        # Simulate concurrent copy operations
        import asyncio

        tasks = []
        for i in range(3):
            task = operations_service.copy_asset_to_project(
                project_id=sample_project["id"],
                source_category=AssetType.CHARACTERS,
                source_asset_id=library_asset.id,
                target_name=f"Concurrent Asset {i}",
            )
            tasks.append(task)

        # All operations should complete successfully
        copied_assets = await asyncio.gather(*tasks)
        assert len(copied_assets) == 3

        # Verify all assets exist
        project_assets = await operations_service.get_project_assets(
            sample_project["id"], AssetType.CHARACTERS
        )
        assert len(project_assets) == 3

    async def test_ac_031_13_directory_structure_compliance(
        self, operations_service, sample_project, sample_library_asset
    ):
        """Test that copied assets follow project directory structure"""
        library_asset = await sample_library_asset()

        # Copy asset
        copied_asset = await operations_service.copy_asset_to_project(
            project_id=sample_project["id"],
            source_category=AssetType.CHARACTERS,
            source_asset_id=library_asset.id,
        )

        # Verify asset is in correct directory structure
        project_path = Path(sample_project["path"])
        expected_base_path = project_path / "01_Assets" / "Characters"

        asset_path = project_path / copied_asset.path
        assert asset_path.parent.parent == expected_base_path.parent
        assert asset_path.parent.name == "Characters"

    def test_ac_031_14_sanitize_asset_names(self, operations_service):
        """Test asset name sanitization for filesystem safety"""
        test_cases = [
            ("Normal Name", "Normal_Name"),
            ("Name with/slashes", "Name_with_slashes"),
            ("Name with spaces", "Name_with_spaces"),
            ("Name@#$%^&*()", "Name__________"),
            ("", "asset"),  # Empty name fallback
        ]

        for input_name, expected_output in test_cases:
            result = operations_service._sanitize_name(input_name)
            assert result == expected_output
