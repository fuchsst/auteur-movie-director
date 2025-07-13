"""
Asset service implementing workspace-level asset management.
Handles characters, styles, locations, and music assets with versioning.
"""

import json
import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image
from pydantic import ValidationError

from app.schemas.project import AssetReference, AssetType

logger = logging.getLogger(__name__)


class AssetService:
    """
    Service for managing workspace-level assets.
    Provides CRUD operations for characters, styles, locations, and music.
    """

    # Asset categories mapping to directory names
    ASSET_CATEGORIES = {
        AssetType.CHARACTERS: "Characters",
        AssetType.STYLES: "Styles",
        AssetType.LOCATIONS: "Locations",
        AssetType.MUSIC: "Music",
    }

    # Supported file types by category
    SUPPORTED_FILE_TYPES = {
        AssetType.CHARACTERS: {
            "model": [".safetensors", ".ckpt", ".pt"],
            "image": [".png", ".jpg", ".jpeg", ".webp"],
            "config": [".json", ".yaml", ".yml"],
        },
        AssetType.STYLES: {
            "image": [".png", ".jpg", ".jpeg", ".webp"],
            "reference": [".pdf", ".txt", ".md"],
        },
        AssetType.LOCATIONS: {
            "image": [".png", ".jpg", ".jpeg", ".webp", ".hdr", ".exr"],
            "model": [".obj", ".fbx", ".glb", ".gltf"],
        },
        AssetType.MUSIC: {
            "audio": [".wav", ".mp3", ".ogg", ".flac", ".aac"],
            "midi": [".mid", ".midi"],
        },
    }

    # Preview image settings
    PREVIEW_SIZE = (512, 512)
    PREVIEW_QUALITY = 85

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.library_path = self.workspace_root / "Library"
        self._ensure_library_structure()

    def _ensure_library_structure(self) -> None:
        """Ensure library directory structure exists"""
        self.library_path.mkdir(exist_ok=True)

        for category_dir in self.ASSET_CATEGORIES.values():
            (self.library_path / category_dir).mkdir(exist_ok=True)
            # Add .gitkeep to prevent empty directory removal
            (self.library_path / category_dir / ".gitkeep").touch()

    def _get_category_path(self, category: AssetType) -> Path:
        """Get the path for an asset category"""
        category_name = self.ASSET_CATEGORIES.get(category)
        if not category_name:
            raise ValueError(f"Unsupported asset category: {category}")
        return self.library_path / category_name

    def _get_asset_path(self, category: AssetType, asset_id: str) -> Path:
        """Get the path for a specific asset"""
        return self._get_category_path(category) / asset_id

    def _sanitize_asset_name(self, name: str) -> str:
        """Sanitize asset name for use as directory name"""
        # Replace spaces and special characters with underscores
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        # Remove leading/trailing underscores
        safe_name = safe_name.strip("_")
        # Ensure not empty
        if not safe_name:
            safe_name = "untitled_asset"
        return safe_name

    def _validate_file_type(self, category: AssetType, file_type: str, filename: str) -> bool:
        """Validate if file type is supported for the category"""
        if category not in self.SUPPORTED_FILE_TYPES:
            return False

        supported_types = self.SUPPORTED_FILE_TYPES[category]
        if file_type not in supported_types:
            return False

        file_ext = Path(filename).suffix.lower()
        return file_ext in supported_types[file_type]

    async def _generate_preview(self, asset_path: Path, source_file: Path) -> Path | None:
        """Generate preview image for an asset"""
        try:
            preview_path = asset_path / "preview.png"

            # Check if source is an image
            if source_file.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                with Image.open(source_file) as img:
                    # Convert to RGB if necessary
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Resize to preview size maintaining aspect ratio
                    img.thumbnail(self.PREVIEW_SIZE, Image.Resampling.LANCZOS)

                    # Create centered preview with padding
                    preview = Image.new("RGB", self.PREVIEW_SIZE, (255, 255, 255))
                    offset = (
                        (self.PREVIEW_SIZE[0] - img.size[0]) // 2,
                        (self.PREVIEW_SIZE[1] - img.size[1]) // 2,
                    )
                    preview.paste(img, offset)

                    preview.save(preview_path, "PNG", quality=self.PREVIEW_QUALITY)
                    return preview_path

            # For non-image files, create a placeholder
            preview = Image.new("RGB", self.PREVIEW_SIZE, (240, 240, 240))
            preview.save(preview_path, "PNG")
            return preview_path

        except Exception as e:
            logger.warning(f"Failed to generate preview for {source_file}: {e}")
            return None

    async def import_asset(
        self,
        category: AssetType,
        name: str,
        files: dict[str, UploadFile],
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> AssetReference:
        """
        Import a new asset into the workspace library.

        Args:
            category: Asset category (character, style, location, music)
            name: Human-readable asset name
            files: Dictionary of file type to UploadFile
            metadata: Optional metadata dictionary
            tags: Optional list of tags

        Returns:
            AssetReference for the imported asset

        Raises:
            ValueError: For invalid category or file types
            RuntimeError: For import failures
        """
        if not files:
            raise ValueError("At least one file must be provided")

        # Validate category
        if category not in self.ASSET_CATEGORIES:
            raise ValueError(f"Unsupported category: {category}")

        # Generate unique asset ID
        asset_id = str(uuid4())
        safe_name = self._sanitize_asset_name(name)
        asset_dir_name = f"{safe_name}_{asset_id[:8]}"

        asset_path = self._get_category_path(category) / asset_dir_name

        try:
            # Create asset directory
            asset_path.mkdir(parents=True)

            # Validate and save files
            saved_files = {}
            primary_file = None

            for file_type, upload_file in files.items():
                if not self._validate_file_type(category, file_type, upload_file.filename):
                    raise ValueError(f"Unsupported file type '{file_type}' for {category}")

                # Save file
                file_path = asset_path / upload_file.filename
                with open(file_path, "wb") as f:
                    content = await upload_file.read()
                    f.write(content)

                saved_files[file_type] = upload_file.filename

                # Track primary file for preview generation
                if file_type in ["image", "model"] and primary_file is None:
                    primary_file = file_path

            # Generate preview if possible
            preview_path = None
            if primary_file:
                preview_path = await self._generate_preview(asset_path, primary_file)

            # Create asset metadata
            asset_metadata = {
                "id": asset_id,
                "name": name,
                "category": category.value,
                "type": category.value.lower(),
                "version": "1.0",
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
                "tags": tags or [],
                "metadata": metadata or {},
                "files": saved_files,
                "preview": "preview.png" if preview_path else None,
                "path": str(asset_path.relative_to(self.library_path)),
            }

            # Save metadata file
            metadata_path = asset_path / "asset.json"
            with open(metadata_path, "w") as f:
                json.dump(asset_metadata, f, indent=2, default=str)

            logger.info(f"Imported {category.value} asset: {name} ({asset_id})")

            # Return AssetReference
            return AssetReference(
                id=asset_id,
                name=name,
                type=category.value,
                path=str(asset_path.relative_to(self.workspace_root)),
                metadata=asset_metadata,
            )

        except Exception as e:
            # Clean up on failure
            if asset_path.exists():
                shutil.rmtree(asset_path)
            logger.error(f"Failed to import asset: {e}")
            raise RuntimeError(f"Asset import failed: {str(e)}")

    async def list_assets(
        self,
        category: AssetType | None = None,
        tags: list[str] | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[AssetReference]:
        """
        List assets with optional filtering.

        Args:
            category: Optional category filter
            tags: Optional tag filter (OR logic)
            limit: Maximum number of assets to return
            offset: Number of assets to skip

        Returns:
            List of AssetReference objects
        """
        assets = []

        categories_to_search = [category] if category else list(self.ASSET_CATEGORIES.keys())

        for cat in categories_to_search:
            category_path = self._get_category_path(cat)

            if not category_path.exists():
                continue

            for asset_dir in category_path.iterdir():
                if not asset_dir.is_dir() or asset_dir.name == ".gitkeep":
                    continue

                metadata_file = asset_dir / "asset.json"
                if not metadata_file.exists():
                    continue

                try:
                    with open(metadata_file) as f:
                        asset_data = json.load(f)

                    # Apply tag filter if specified
                    if tags:
                        asset_tags = asset_data.get("tags", [])
                        if not any(tag in asset_tags for tag in tags):
                            continue

                    asset_ref = AssetReference(
                        id=asset_data["id"],
                        name=asset_data["name"],
                        type=asset_data["type"],
                        path=asset_data["path"],
                        metadata=asset_data,
                    )

                    assets.append(asset_ref)

                except (json.JSONDecodeError, KeyError, ValidationError) as e:
                    logger.warning(f"Failed to load asset metadata from {metadata_file}: {e}")
                    continue

        # Sort by creation date (newest first)
        assets.sort(key=lambda a: a.metadata.get("created_at", ""), reverse=True)

        # Apply pagination
        return assets[offset : offset + limit]

    async def get_asset(self, category: AssetType, asset_id: str) -> AssetReference | None:
        """
        Get a specific asset by ID and category.

        Args:
            category: Asset category
            asset_id: Asset UUID

        Returns:
            AssetReference if found, None otherwise
        """
        category_path = self._get_category_path(category)

        # Search for asset directory containing the ID
        for asset_dir in category_path.iterdir():
            if not asset_dir.is_dir():
                continue

            metadata_file = asset_dir / "asset.json"
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file) as f:
                    asset_data = json.load(f)

                if asset_data.get("id") == asset_id:
                    return AssetReference(
                        id=asset_data["id"],
                        name=asset_data["name"],
                        type=asset_data["type"],
                        path=asset_data["path"],
                        metadata=asset_data,
                    )

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load asset metadata from {metadata_file}: {e}")
                continue

        return None

    async def delete_asset(self, category: AssetType, asset_id: str) -> bool:
        """
        Delete an asset from the workspace library.

        Args:
            category: Asset category
            asset_id: Asset UUID

        Returns:
            True if deleted successfully, False if not found
        """
        asset = await self.get_asset(category, asset_id)
        if not asset:
            return False

        try:
            asset_path = self.library_path / asset.path
            if asset_path.exists():
                shutil.rmtree(asset_path)
                logger.info(f"Deleted {category.value} asset: {asset.name} ({asset_id})")
                return True
        except Exception as e:
            logger.error(f"Failed to delete asset {asset_id}: {e}")

        return False

    async def search_assets(
        self,
        query: str,
        category: AssetType | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
    ) -> list[AssetReference]:
        """
        Search assets by name and description.

        Args:
            query: Search query string
            category: Optional category filter
            tags: Optional tag filter
            limit: Maximum results to return

        Returns:
            List of matching AssetReference objects
        """
        all_assets = await self.list_assets(category=category, tags=tags, limit=1000)

        if not query.strip():
            return all_assets[:limit]

        query_lower = query.lower()
        matching_assets = []

        for asset in all_assets:
            # Search in name
            if query_lower in asset.name.lower():
                matching_assets.append(asset)
                continue

            # Search in description
            description = asset.metadata.get("metadata", {}).get("description", "")
            if query_lower in description.lower():
                matching_assets.append(asset)
                continue

            # Search in tags
            asset_tags = asset.metadata.get("tags", [])
            if any(query_lower in tag.lower() for tag in asset_tags):
                matching_assets.append(asset)
                continue

        return matching_assets[:limit]

    async def update_asset_metadata(
        self,
        category: AssetType,
        asset_id: str,
        name: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AssetReference | None:
        """
        Update asset metadata.

        Args:
            category: Asset category
            asset_id: Asset UUID
            name: Optional new name
            tags: Optional new tags
            metadata: Optional new metadata

        Returns:
            Updated AssetReference if successful, None if not found
        """
        asset = await self.get_asset(category, asset_id)
        if not asset:
            return None

        try:
            asset_path = self.library_path / asset.path
            metadata_file = asset_path / "asset.json"

            # Load current metadata
            with open(metadata_file) as f:
                asset_data = json.load(f)

            # Update fields
            if name is not None:
                asset_data["name"] = name
            if tags is not None:
                asset_data["tags"] = tags
            if metadata is not None:
                asset_data["metadata"].update(metadata)

            asset_data["updated_at"] = datetime.now(UTC).isoformat()

            # Save updated metadata
            with open(metadata_file, "w") as f:
                json.dump(asset_data, f, indent=2, default=str)

            logger.info(
                f"Updated {category.value} asset metadata: {asset_data['name']} ({asset_id})"
            )

            # Return updated reference
            return AssetReference(
                id=asset_data["id"],
                name=asset_data["name"],
                type=asset_data["type"],
                path=asset_data["path"],
                metadata=asset_data,
            )

        except Exception as e:
            logger.error(f"Failed to update asset metadata {asset_id}: {e}")
            return None

    def get_asset_statistics(self) -> dict[str, Any]:
        """
        Get statistics about workspace assets.

        Returns:
            Dictionary with asset counts and storage information
        """
        stats = {
            "total_assets": 0,
            "by_category": {},
            "total_size_bytes": 0,
            "library_path": str(self.library_path),
        }

        for category in self.ASSET_CATEGORIES:
            category_path = self._get_category_path(category)
            category_name = category.value

            count = 0
            size = 0

            if category_path.exists():
                for asset_dir in category_path.iterdir():
                    if asset_dir.is_dir() and asset_dir.name != ".gitkeep":
                        count += 1
                        # Calculate directory size
                        for file_path in asset_dir.rglob("*"):
                            if file_path.is_file():
                                size += file_path.stat().st_size

            stats["by_category"][category_name] = {"count": count, "size_bytes": size}
            stats["total_assets"] += count
            stats["total_size_bytes"] += size

        return stats


# Global asset service instance
asset_service = None


def get_asset_service() -> AssetService:
    """Get or create asset service instance"""
    global asset_service
    if asset_service is None:
        from app.config import settings

        asset_service = AssetService(str(settings.workspace_root))
    return asset_service
