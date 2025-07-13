"""
Asset operations service for copying workspace library assets to projects.
Implements STORY-031 requirements for advanced asset management.
"""

import json
import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.schemas.project import AssetReference, AssetType
from app.services.assets import get_asset_service
from app.services.workspace import get_workspace_service

logger = logging.getLogger(__name__)


class AssetOperationError(Exception):
    """Exception raised when asset operations fail"""

    pass


class AssetOperationsService:
    """
    Service for advanced asset operations including copying from library to projects.
    Provides atomic operations with rollback, progress tracking, and reference management.
    """

    def __init__(self, workspace_root: str, asset_service=None, workspace_service=None):
        self.workspace_root = Path(workspace_root)
        self.asset_service = asset_service or get_asset_service()
        self.workspace_service = workspace_service or get_workspace_service()

    async def copy_asset_to_project(
        self,
        project_id: str,
        source_category: AssetType,
        source_asset_id: str,
        target_name: str | None = None,
        replace_existing: bool = False,
    ) -> AssetReference:
        """
        Copy an asset from workspace library to a specific project.

        Args:
            project_id: Target project ID
            source_category: Asset category in library
            source_asset_id: Source asset ID to copy
            target_name: Optional new name for the copied asset
            replace_existing: Whether to replace existing assets with same name

        Returns:
            AssetReference for the copied asset

        Raises:
            AssetOperationError: If copy operation fails
        """
        try:
            # Get source asset from library
            source_asset = await self.asset_service.get_asset(source_category, source_asset_id)
            if not source_asset:
                raise AssetOperationError(
                    f"Source asset {source_asset_id} not found in category {source_category.value}"
                )

            # Get project info
            project_path = self.workspace_service.get_project_path(project_id)
            if not project_path or not project_path.exists():
                raise AssetOperationError(f"Project {project_id} not found")

            # Determine target name
            if target_name is None:
                target_name = source_asset.name

            # Check for name conflicts
            final_name = await self._resolve_asset_name_conflict(
                project_id, source_category, target_name, replace_existing
            )

            # Create target directory structure
            category_mapping = {
                AssetType.CHARACTERS: "Characters",
                AssetType.STYLES: "Styles",
                AssetType.LOCATIONS: "Locations",
                AssetType.MUSIC: "Music",
            }
            category_name = category_mapping.get(source_category, source_category.value.title())
            project_assets_dir = project_path / "01_Assets" / category_name
            project_assets_dir.mkdir(parents=True, exist_ok=True)

            # Generate new asset ID for project copy
            target_asset_id = str(uuid4())
            target_dir_name = f"{self._sanitize_name(final_name)}_{target_asset_id[:8]}"
            target_asset_path = project_assets_dir / target_dir_name

            # Perform atomic copy operation
            source_asset_path = self.asset_service.library_path / source_asset.path
            copied_files = await self._atomic_copy_asset(source_asset_path, target_asset_path)

            # Create project asset metadata
            project_asset_metadata = self._create_project_asset_metadata(
                source_asset,
                source_category,
                target_asset_id,
                final_name,
                copied_files,
                target_asset_path,
            )

            # Save project asset metadata
            metadata_file = target_asset_path / "asset.json"
            with open(metadata_file, "w") as f:
                json.dump(project_asset_metadata, f, indent=2, default=str)

            # Update project manifest
            await self._update_project_asset_references(project_id, project_asset_metadata)

            logger.info(
                f"Copied asset {source_asset.name} from library to project {project_id} as {final_name}"
            )

            # Create AssetReference for the copied asset
            project_asset_ref = AssetReference(
                id=target_asset_id,
                name=final_name,
                type=source_category.value,
                path=str(target_asset_path.relative_to(project_path)),
                metadata=project_asset_metadata,
            )

            return project_asset_ref

        except Exception as e:
            logger.error(f"Failed to copy asset {source_asset_id} to project {project_id}: {e}")
            # Cleanup on failure
            if "target_asset_path" in locals() and target_asset_path.exists():
                shutil.rmtree(target_asset_path, ignore_errors=True)
            raise AssetOperationError(f"Asset copy failed: {str(e)}")

    async def copy_multiple_assets_to_project(
        self,
        project_id: str,
        asset_requests: list[dict[str, Any]],
        replace_existing: bool = False,
    ) -> list[AssetReference]:
        """
        Copy multiple assets from library to project in a batch operation.

        Args:
            project_id: Target project ID
            asset_requests: List of asset copy requests with category, id, and optional name
            replace_existing: Whether to replace existing assets

        Returns:
            List of AssetReference objects for copied assets

        Raises:
            AssetOperationError: If batch operation fails
        """
        copied_assets = []
        failed_assets = []

        for request in asset_requests:
            try:
                asset_ref = await self.copy_asset_to_project(
                    project_id=project_id,
                    source_category=AssetType(request["category"]),
                    source_asset_id=request["asset_id"],
                    target_name=request.get("target_name"),
                    replace_existing=replace_existing,
                )
                copied_assets.append(asset_ref)
                logger.info(f"Successfully copied asset {request['asset_id']}")

            except Exception as e:
                failed_assets.append({"request": request, "error": str(e)})
                logger.error(f"Failed to copy asset {request['asset_id']}: {e}")

        if failed_assets:
            # Rollback successful copies on partial failure
            await self._rollback_copied_assets(project_id, copied_assets)
            raise AssetOperationError(
                f"Batch copy failed. {len(failed_assets)} assets failed: {failed_assets}"
            )

        return copied_assets

    async def get_project_assets(
        self, project_id: str, category: AssetType | None = None
    ) -> list[AssetReference]:
        """
        Get assets that have been copied to a specific project.

        Args:
            project_id: Project ID
            category: Optional category filter

        Returns:
            List of project assets
        """
        try:
            project_path = self.workspace_service.get_project_path(project_id)
            if not project_path or not project_path.exists():
                raise AssetOperationError(f"Project {project_id} not found")

            assets_dir = project_path / "01_Assets"
            if not assets_dir.exists():
                return []

            project_assets = []
            categories_to_search = [category] if category else list(AssetType)

            category_mapping = {
                AssetType.CHARACTERS: "Characters",
                AssetType.STYLES: "Styles",
                AssetType.LOCATIONS: "Locations",
                AssetType.MUSIC: "Music",
            }

            for cat in categories_to_search:
                category_name = category_mapping.get(cat, cat.value.title())
                category_dir = assets_dir / category_name
                if not category_dir.exists():
                    continue

                for asset_dir in category_dir.iterdir():
                    if not asset_dir.is_dir():
                        continue

                    metadata_file = asset_dir / "asset.json"
                    if not metadata_file.exists():
                        continue

                    try:
                        with open(metadata_file) as f:
                            asset_data = json.load(f)

                        asset_ref = AssetReference(
                            id=asset_data["id"],
                            name=asset_data["name"],
                            type=asset_data["type"],
                            path=str(asset_dir.relative_to(project_path)),
                            metadata=asset_data,
                        )
                        project_assets.append(asset_ref)

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(
                            f"Failed to load project asset metadata from {metadata_file}: {e}"
                        )
                        continue

            # Sort by creation date
            project_assets.sort(key=lambda a: a.metadata.get("created_at", ""), reverse=True)
            return project_assets

        except Exception as e:
            logger.error(f"Failed to get project assets for {project_id}: {e}")
            raise AssetOperationError(f"Failed to retrieve project assets: {str(e)}")

    async def remove_project_asset(
        self, project_id: str, category: AssetType, asset_id: str
    ) -> bool:
        """
        Remove an asset from a project (does not affect library original).

        Args:
            project_id: Project ID
            category: Asset category
            asset_id: Asset ID to remove

        Returns:
            True if successfully removed, False if not found
        """
        try:
            project_assets = await self.get_project_assets(project_id, category)
            asset_to_remove = None

            for asset in project_assets:
                if asset.id == asset_id:
                    asset_to_remove = asset
                    break

            if not asset_to_remove:
                return False

            # Remove asset directory
            project_path = self.workspace_service.get_project_path(project_id)
            asset_path = project_path / asset_to_remove.path

            if asset_path.exists():
                shutil.rmtree(asset_path)
                logger.info(f"Removed project asset {asset_id} from {project_id}")

                # Update project manifest
                await self._remove_project_asset_reference(project_id, asset_id)
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to remove project asset {asset_id}: {e}")
            return False

    async def _resolve_asset_name_conflict(
        self,
        project_id: str,
        category: AssetType,
        target_name: str,
        replace_existing: bool,
    ) -> str:
        """Resolve naming conflicts when copying assets to projects"""
        if replace_existing:
            return target_name

        project_assets = await self.get_project_assets(project_id, category)
        existing_names = {asset.name for asset in project_assets}

        if target_name not in existing_names:
            return target_name

        # Generate unique name with suffix
        counter = 2
        while f"{target_name}_{counter}" in existing_names:
            counter += 1

        return f"{target_name}_{counter}"

    async def _atomic_copy_asset(self, source_path: Path, target_path: Path) -> dict[str, str]:
        """Perform atomic file copy operation with rollback on failure"""
        target_path.mkdir(parents=True, exist_ok=True)
        copied_files = {}

        try:
            for source_file in source_path.iterdir():
                if source_file.is_file() and source_file.name != ".gitkeep":
                    target_file = target_path / source_file.name
                    shutil.copy2(source_file, target_file)
                    copied_files[source_file.name] = source_file.name

            return copied_files

        except Exception as e:
            # Rollback on failure
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)
            raise AssetOperationError(f"Atomic copy failed: {str(e)}")

    def _create_project_asset_metadata(
        self,
        source_asset: AssetReference,
        source_category: AssetType,
        target_asset_id: str,
        final_name: str,
        copied_files: dict[str, str],
        target_path: Path,
    ) -> dict[str, Any]:
        """Create metadata for project asset copy"""
        now = datetime.now(UTC).isoformat()

        return {
            "id": target_asset_id,
            "name": final_name,
            "category": source_category.value,  # Use the enum value for consistency
            "type": source_category.value,  # Use the enum value for consistency
            "version": "1.0",
            "created_at": now,
            "updated_at": now,
            "copied_at": now,
            "source": {
                "library_asset_id": source_asset.id,
                "library_asset_name": source_asset.name,
                "library_path": source_asset.path,
                "copied_from": "workspace_library",
            },
            "tags": source_asset.metadata.get("tags", []),
            "metadata": source_asset.metadata.get("metadata", {}),
            "files": copied_files,
            "path": str(target_path.name),  # Just the directory name
        }

    async def _update_project_asset_references(
        self, project_id: str, asset_metadata: dict[str, Any]
    ) -> None:
        """Update project manifest with new asset reference"""
        try:
            project_path = self.workspace_service.get_project_path(project_id)
            manifest_file = project_path / "project.json"

            if manifest_file.exists():
                with open(manifest_file) as f:
                    manifest = json.load(f)

                # Add asset reference to manifest
                if "assets" not in manifest:
                    manifest["assets"] = {}

                category = asset_metadata["category"]
                if category not in manifest["assets"]:
                    manifest["assets"][category] = []

                # Add reference
                asset_ref = {
                    "id": asset_metadata["id"],
                    "name": asset_metadata["name"],
                    "path": asset_metadata["path"],
                    "source_id": asset_metadata["source"]["library_asset_id"],
                    "copied_at": asset_metadata["copied_at"],
                }

                manifest["assets"][category].append(asset_ref)
                manifest["updated_at"] = datetime.now(UTC).isoformat()

                # Save updated manifest
                with open(manifest_file, "w") as f:
                    json.dump(manifest, f, indent=2, default=str)

        except Exception as e:
            logger.warning(f"Failed to update project manifest: {e}")

    async def _remove_project_asset_reference(self, project_id: str, asset_id: str) -> None:
        """Remove asset reference from project manifest"""
        try:
            project_path = self.workspace_service.get_project_path(project_id)
            manifest_file = project_path / "project.json"

            if manifest_file.exists():
                with open(manifest_file) as f:
                    manifest = json.load(f)

                # Remove asset reference
                if "assets" in manifest:
                    for category_assets in manifest["assets"].values():
                        manifest["assets"][category] = [
                            asset for asset in category_assets if asset["id"] != asset_id
                        ]

                    manifest["updated_at"] = datetime.now(UTC).isoformat()

                    # Save updated manifest
                    with open(manifest_file, "w") as f:
                        json.dump(manifest, f, indent=2, default=str)

        except Exception as e:
            logger.warning(f"Failed to remove project asset reference: {e}")

    async def _rollback_copied_assets(
        self, project_id: str, copied_assets: list[AssetReference]
    ) -> None:
        """Rollback copied assets on batch operation failure"""
        for asset in copied_assets:
            try:
                await self.remove_project_asset(project_id, AssetType(asset.type), asset.id)
            except Exception as e:
                logger.error(f"Failed to rollback asset {asset.id}: {e}")

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use as directory name"""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return safe_name.strip("_") or "asset"


# Global service instance
_asset_operations_service = None


def get_asset_operations_service() -> AssetOperationsService:
    """Get or create asset operations service instance"""
    global _asset_operations_service
    if _asset_operations_service is None:
        from app.config import settings

        _asset_operations_service = AssetOperationsService(str(settings.workspace_root))
    return _asset_operations_service
