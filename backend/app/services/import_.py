"""
Project import service for restoring project archives.

Handles importing project archives with validation, migration, and Git/LFS restoration.
"""

import asyncio
import json
import logging
import os
import shutil
import tarfile
import tempfile
import zipfile
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas.project import ImportOptions, ImportResult, ValidationResult
from app.services.git import git_service

logger = logging.getLogger(__name__)


class ImportFormat(str, Enum):
    """Supported import archive formats."""

    ZIP = "zip"
    TAR_GZ = "tar.gz"


class ProjectImportService:
    """Service for importing project archives."""

    def __init__(self):
        self.workspace_root = Path(settings.workspace_root)
        self.temp_dir = Path(tempfile.gettempdir()) / "auteur-imports"
        self.temp_dir.mkdir(exist_ok=True)

        # Version migration registry
        self.migrations = {"1.0": self._migrate_v1_to_v2, "1.1": self._migrate_v1_1_to_v2}

        # Current structure version
        self.current_version = "2.0"

    async def import_archive(
        self,
        archive_path: str,
        target_name: str,
        options: ImportOptions = ImportOptions(),
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> ImportResult:
        """
        Import a project from an archive.

        Args:
            archive_path: Path to the archive file
            target_name: Target project name
            options: Import configuration
            progress_callback: Progress update callback

        Returns:
            Import result with statistics
        """
        start_time = datetime.now()
        archive_path = Path(archive_path)

        if not archive_path.exists():
            raise ValueError(f"Archive file not found: {archive_path}")

        # Create temporary extraction directory
        extract_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        extract_dir = self.temp_dir / f"import_{extract_id}"
        extract_dir.mkdir(exist_ok=True)

        try:
            # Step 1: Extract archive
            await self._update_progress(progress_callback, 0.1, "Extracting archive...")
            await self._extract_archive(archive_path, extract_dir)

            # Find project root (might be nested)
            project_root = await self._find_project_root(extract_dir)
            if not project_root:
                raise ValueError("No valid project found in archive")

            # Step 2: Validate structure
            await self._update_progress(progress_callback, 0.2, "Validating project structure...")
            validation = await self._validate_project_structure(project_root)
            if not validation.valid:
                raise ValueError(f"Invalid project structure: {', '.join(validation.errors)}")

            # Step 3: Check version and migrate if needed
            await self._update_progress(progress_callback, 0.3, "Checking project version...")
            if validation.version != self.current_version:
                await self._migrate_project(project_root, validation.version, self.current_version)

            # Step 4: Resolve naming conflicts
            await self._update_progress(progress_callback, 0.4, "Resolving naming conflicts...")
            final_name = await self._resolve_project_name(target_name, options.rename_on_conflict)

            # Step 5: Copy to workspace
            await self._update_progress(progress_callback, 0.5, "Copying project files...")
            target_path = self.workspace_root / final_name
            await self._copy_project_files(project_root, target_path)

            # Step 6: Restore Git repository
            if options.restore_git_history and (project_root / "git-bundle.bundle").exists():
                await self._update_progress(progress_callback, 0.7, "Restoring Git history...")
                await self._restore_git_repository(project_root / "git-bundle.bundle", target_path)
            else:
                # Initialize new Git repository
                await git_service.init_repository(str(target_path))

            # Step 7: Restore LFS objects
            if (project_root / ".git-lfs-objects").exists():
                await self._update_progress(progress_callback, 0.8, "Restoring LFS objects...")
                await self._restore_lfs_objects(project_root / ".git-lfs-objects", target_path)

            # Step 8: Update project metadata
            await self._update_progress(progress_callback, 0.9, "Updating project metadata...")
            await self._update_project_metadata(target_path, final_name)

            # Calculate import statistics
            statistics = await self._calculate_import_statistics(target_path)

            await self._update_progress(progress_callback, 1.0, "Import completed successfully")

            duration = (datetime.now() - start_time).total_seconds()

            return ImportResult(
                success=True,
                project_id=final_name,
                project_name=final_name,
                import_duration=duration,
                statistics=statistics,
                warnings=validation.warnings,
            )

        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            duration = (datetime.now() - start_time).total_seconds()
            return ImportResult(
                success=False,
                project_id="",
                project_name=target_name,
                import_duration=duration,
                statistics={},
                errors=[str(e)],
            )
        finally:
            # Cleanup temporary directory
            if extract_dir.exists():
                shutil.rmtree(extract_dir)

    async def _extract_archive(self, archive_path: Path, extract_dir: Path):
        """Extract archive to temporary directory."""
        file_extension = archive_path.suffix.lower()

        def _extract():
            if file_extension == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(extract_dir)
            elif archive_path.name.endswith(".tar.gz"):
                with tarfile.open(archive_path, "r:gz") as tf:
                    tf.extractall(extract_dir)
            else:
                raise ValueError(f"Unsupported archive format: {file_extension}")

        # Run extraction in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _extract)

    async def _find_project_root(self, extract_dir: Path) -> Path | None:
        """Find the project root directory in extracted files."""
        # Look for project.json or export_manifest.json
        for root, _, files in os.walk(extract_dir):
            root_path = Path(root)
            if "project.json" in files or "export_manifest.json" in files:
                return root_path
        return None

    async def _validate_project_structure(self, project_path: Path) -> ValidationResult:
        """Validate project structure and return validation result."""
        errors = []
        warnings = []
        version = None
        project_id = None

        # Check for manifest
        manifest_path = project_path / "export_manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
                version = manifest.get("export_version", "1.0")
                project_id = manifest.get("project_id")
            except Exception as e:
                errors.append(f"Invalid manifest: {str(e)}")
        else:
            # Try to detect version from structure
            if (project_path / "project.json").exists():
                version = "1.0"
            else:
                errors.append("No project manifest found")

        # Check required directories based on version
        if version:
            required_dirs = self._get_required_directories(version)
            for dir_name in required_dirs:
                if not (project_path / dir_name).exists():
                    warnings.append(f"Missing directory: {dir_name}")

        # Check for Git repository if bundle exists
        if (project_path / "git-bundle.bundle").exists():
            if not (project_path / ".git").exists() and version != "1.0":
                warnings.append("Git bundle found but no .git directory")

        return ValidationResult(
            valid=len(errors) == 0,
            version=version,
            project_id=project_id,
            errors=errors,
            warnings=warnings,
        )

    def _get_required_directories(self, version: str) -> list[str]:
        """Get required directories for a specific version."""
        if version == "1.0":
            return ["Assets", "Story", "Renders"]
        else:  # 2.0 and later
            return ["01_Assets", "02_Story", "03_Renders"]

    async def _migrate_project(self, project_path: Path, from_version: str, to_version: str):
        """Migrate project structure to current version."""
        logger.info(f"Migrating project from {from_version} to {to_version}")

        # Apply migrations sequentially
        current = from_version
        while current != to_version:
            if current in self.migrations:
                await self.migrations[current](project_path)
                # Update version (simplified, assumes linear progression)
                if current == "1.0":
                    current = "1.1"
                elif current == "1.1":
                    current = "2.0"
            else:
                logger.warning(f"No migration path from {current}")
                break

    async def _migrate_v1_to_v2(self, project_path: Path):
        """Migrate from v1.0 to v2.0 structure."""
        # Rename directories
        mappings = {
            "Assets": "01_Assets",
            "Story": "02_Story",
            "Renders": "03_Renders",
            "Compositions": "04_Compositions",
            "Audio": "05_Audio",
            "Exports": "06_Exports",
        }

        for old_name, new_name in mappings.items():
            old_path = project_path / old_name
            new_path = project_path / new_name
            if old_path.exists() and not new_path.exists():
                old_path.rename(new_path)

    async def _migrate_v1_1_to_v2(self, project_path: Path):
        """Migrate from v1.1 to v2.0 structure."""
        # Similar to v1 to v2 but might have different requirements
        await self._migrate_v1_to_v2(project_path)

    async def _resolve_project_name(self, target_name: str, rename_on_conflict: bool) -> str:
        """Resolve project naming conflicts."""
        target_path = self.workspace_root / target_name

        if not target_path.exists():
            return target_name

        if not rename_on_conflict:
            raise ValueError(f"Project '{target_name}' already exists")

        # Find unique name
        counter = 1
        while True:
            new_name = f"{target_name}_{counter}"
            if not (self.workspace_root / new_name).exists():
                return new_name
            counter += 1

    async def _copy_project_files(self, source: Path, destination: Path):
        """Copy project files to workspace."""
        destination.mkdir(parents=True, exist_ok=True)

        # Copy all files except temporary/system files
        exclude_patterns = [
            "export_manifest.json",
            "git-bundle.bundle",
            ".git-lfs-objects",
            "__pycache__",
            "*.pyc",
            ".DS_Store",
            "Thumbs.db",
        ]

        def should_exclude(path: Path) -> bool:
            name = path.name
            return any(
                name == pattern or name.endswith(pattern.replace("*", ""))
                for pattern in exclude_patterns
            )

        for item in source.rglob("*"):
            if item.is_file() and not should_exclude(item):
                relative_path = item.relative_to(source)
                dest_path = destination / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)

    async def _restore_git_repository(self, bundle_path: Path, project_path: Path):
        """Restore Git repository from bundle."""
        git_dir = project_path / ".git"

        # Initialize repository
        await git_service.init_repository(str(project_path))

        # Fetch from bundle
        cmd = ["git", "-C", str(project_path), "fetch", str(bundle_path), "+refs/*:refs/*"]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Git restore failed: {stderr.decode()}")
            raise RuntimeError("Failed to restore Git repository")

        # Checkout default branch
        cmd = ["git", "-C", str(project_path), "checkout", "-f", "main"]
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

    async def _restore_lfs_objects(self, lfs_source: Path, project_path: Path):
        """Restore Git LFS objects."""
        lfs_dest = project_path / ".git" / "lfs" / "objects"

        if lfs_source.exists():
            # Copy LFS objects
            shutil.copytree(lfs_source, lfs_dest, dirs_exist_ok=True)

            # Run LFS checkout to restore files
            cmd = ["git", "-C", str(project_path), "lfs", "checkout"]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.warning(f"LFS checkout had issues: {stderr.decode()}")

    async def _update_project_metadata(self, project_path: Path, project_name: str):
        """Update project metadata after import."""
        metadata_path = project_path / "project.json"

        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
        else:
            metadata = {}

        # Update metadata
        metadata.update(
            {
                "name": project_name,
                "imported_at": datetime.utcnow().isoformat() + "Z",
                "import_version": self.current_version,
            }
        )

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    async def _calculate_import_statistics(self, project_path: Path) -> dict[str, Any]:
        """Calculate statistics for imported project."""
        total_files = 0
        total_size = 0
        file_types = {}

        for item in project_path.rglob("*"):
            if item.is_file():
                total_files += 1
                size = item.stat().st_size
                total_size += size

                # Track file types
                ext = item.suffix.lower()
                if ext:
                    file_types[ext] = file_types.get(ext, 0) + 1

        # Count Git commits if repository exists
        git_commits = 0
        if (project_path / ".git").exists():
            try:
                cmd = ["git", "-C", str(project_path), "rev-list", "--count", "HEAD"]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                if process.returncode == 0:
                    git_commits = int(stdout.decode().strip())
            except Exception as e:
                logger.warning(f"Failed to count commits: {e}")

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types,
            "git_commits": git_commits,
        }

    async def _update_progress(self, callback: Callable | None, progress: float, message: str):
        """Update progress if callback provided."""
        if callback:
            await callback(progress, message)

    async def validate_archive(self, archive_path: str) -> ValidationResult:
        """
        Validate an archive without importing.

        Args:
            archive_path: Path to archive file

        Returns:
            Validation result
        """
        archive_path = Path(archive_path)
        if not archive_path.exists():
            return ValidationResult(valid=False, errors=["Archive file not found"])

        # Extract to temp for validation
        extract_dir = self.temp_dir / f"validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        extract_dir.mkdir(exist_ok=True)

        try:
            await self._extract_archive(archive_path, extract_dir)
            project_root = await self._find_project_root(extract_dir)

            if not project_root:
                return ValidationResult(valid=False, errors=["No valid project found in archive"])

            return await self._validate_project_structure(project_root)

        finally:
            if extract_dir.exists():
                shutil.rmtree(extract_dir)


# Service singleton
import_service = ProjectImportService()
