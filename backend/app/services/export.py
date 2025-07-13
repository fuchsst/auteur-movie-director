"""
Project export service for creating portable project archives.

Handles exporting projects with all assets, Git history, and LFS objects
into distributable archive formats.
"""

import asyncio
import json
import logging
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
from app.schemas.project import ExportManifest, ExportOptions, ExportStatistics

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export archive formats."""

    ZIP = "zip"
    TAR_GZ = "tar.gz"


class ProjectExportService:
    """Service for exporting projects as portable archives."""

    def __init__(self):
        self.workspace_root = Path(settings.workspace_root)
        self.temp_dir = Path(tempfile.gettempdir()) / "auteur-exports"
        self.temp_dir.mkdir(exist_ok=True)

    async def export_project(
        self,
        project_id: str,
        options: ExportOptions,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> str:
        """
        Export a project as an archive.

        Args:
            project_id: Project identifier
            options: Export configuration options
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the created archive file
        """
        project_path = self.workspace_root / project_id
        if not project_path.exists():
            raise ValueError(f"Project {project_id} not found")

        # Create temporary staging directory
        export_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        staging_dir = self.temp_dir / f"{project_id}_{export_id}"
        staging_dir.mkdir(exist_ok=True)

        try:
            # Calculate total steps for progress
            total_steps = 5
            current_step = 0

            # Step 1: Copy project files
            await self._update_progress(
                progress_callback, current_step / total_steps, "Copying project files..."
            )
            await self._copy_project_files(project_path, staging_dir / project_id, options)
            current_step += 1

            # Step 2: Bundle Git repository
            if options.include_history:
                await self._update_progress(
                    progress_callback, current_step / total_steps, "Bundling Git history..."
                )
                await self._bundle_git_repo(project_path, staging_dir / project_id)
            current_step += 1

            # Step 3: Resolve LFS objects
            await self._update_progress(
                progress_callback, current_step / total_steps, "Resolving LFS objects..."
            )
            await self._bundle_lfs_objects(project_path, staging_dir / project_id)
            current_step += 1

            # Step 4: Create manifest
            await self._update_progress(
                progress_callback, current_step / total_steps, "Creating export manifest..."
            )
            manifest = await self._create_manifest(project_id, staging_dir / project_id, options)
            manifest_path = staging_dir / project_id / "export_manifest.json"
            with open(manifest_path, "w") as f:
                f.write(json.dumps(manifest.dict(), indent=2))
            current_step += 1

            # Step 5: Create archive
            await self._update_progress(
                progress_callback, current_step / total_steps, "Creating archive..."
            )
            archive_path = await self._create_archive(
                staging_dir, project_id, options.format, options.split_size_mb
            )

            await self._update_progress(progress_callback, 1.0, "Export completed successfully")

            return str(archive_path)

        finally:
            # Cleanup staging directory
            if staging_dir.exists():
                shutil.rmtree(staging_dir)

    async def _copy_project_files(self, source: Path, destination: Path, options: ExportOptions):
        """Copy project files with filtering."""
        destination.mkdir(parents=True, exist_ok=True)

        # Define patterns to exclude
        exclude_patterns = [
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            "node_modules",
            ".env",
            ".env.local",
        ]

        if not options.include_cache:
            exclude_patterns.extend(["04_Cache", "*.cache", "thumbs.db", ".DS_Store"])

        def should_exclude(path: Path) -> bool:
            """Check if path should be excluded."""
            path_str = str(path)
            for pattern in exclude_patterns:
                if pattern in path_str:
                    return True
            return False

        # Copy files
        for item in source.rglob("*"):
            if item.is_file() and not should_exclude(item):
                relative_path = item.relative_to(source)
                dest_path = destination / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)

    async def _bundle_git_repo(self, repo_path: Path, staging_path: Path):
        """Bundle Git repository with history."""
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            logger.warning(f"No Git repository found at {repo_path}")
            return

        # Create bundle
        bundle_path = staging_path / "git-bundle.bundle"
        cmd = ["git", "-C", str(repo_path), "bundle", "create", str(bundle_path), "--all"]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Git bundle failed: {stderr.decode()}")
            raise RuntimeError("Failed to create Git bundle")

    async def _bundle_lfs_objects(self, repo_path: Path, staging_path: Path):
        """Bundle Git LFS objects."""
        lfs_dir = repo_path / ".git" / "lfs" / "objects"
        if not lfs_dir.exists():
            logger.info("No LFS objects found")
            return

        # Create LFS objects directory in staging
        dest_lfs_dir = staging_path / ".git-lfs-objects"
        dest_lfs_dir.mkdir(parents=True, exist_ok=True)

        # Copy LFS objects maintaining structure
        for obj_file in lfs_dir.rglob("*"):
            if obj_file.is_file():
                relative_path = obj_file.relative_to(lfs_dir)
                dest_path = dest_lfs_dir / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(obj_file, dest_path)

    async def _create_manifest(
        self, project_id: str, staging_path: Path, options: ExportOptions
    ) -> ExportManifest:
        """Create export manifest with metadata."""
        # Calculate statistics
        total_files = 0
        total_size = 0

        for item in staging_path.rglob("*"):
            if item.is_file():
                total_files += 1
                total_size += item.stat().st_size

        # Count Git commits if repository exists
        git_commits = 0
        if (staging_path / "git-bundle.bundle").exists():
            try:
                cmd = [
                    "git",
                    "-C",
                    str(staging_path.parent.parent / project_id),
                    "rev-list",
                    "--count",
                    "HEAD",
                ]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                if process.returncode == 0:
                    git_commits = int(stdout.decode().strip())
            except Exception as e:
                logger.warning(f"Failed to count commits: {e}")

        statistics = ExportStatistics(
            total_files=total_files, total_size_bytes=total_size, git_commits=git_commits
        )

        return ExportManifest(
            export_version="1.0",
            project_id=project_id,
            exported_at=datetime.utcnow().isoformat() + "Z",
            export_options=options.dict(),
            statistics=statistics,
        )

    async def _create_archive(
        self,
        staging_dir: Path,
        project_id: str,
        format: ExportFormat,
        split_size_mb: int | None = None,
    ) -> Path:
        """Create archive from staging directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{project_id}_export_{timestamp}"

        if format == ExportFormat.ZIP:
            archive_path = self.temp_dir / f"{archive_name}.zip"
            await self._create_zip_archive(staging_dir, archive_path)
        else:  # TAR_GZ
            archive_path = self.temp_dir / f"{archive_name}.tar.gz"
            await self._create_tar_archive(staging_dir, archive_path)

        # Handle splitting if requested
        if split_size_mb and archive_path.stat().st_size > split_size_mb * 1024 * 1024:
            return await self._split_archive(archive_path, split_size_mb)

        return archive_path

    async def _create_zip_archive(self, source_dir: Path, output_path: Path):
        """Create ZIP archive."""

        def _write_zip():
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for item in source_dir.rglob("*"):
                    if item.is_file():
                        arcname = item.relative_to(source_dir)
                        zf.write(item, arcname)

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _write_zip)

    async def _create_tar_archive(self, source_dir: Path, output_path: Path):
        """Create TAR.GZ archive."""

        def _write_tar():
            with tarfile.open(output_path, "w:gz") as tf:
                for item in source_dir.iterdir():
                    tf.add(item, arcname=item.name)

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _write_tar)

    async def _split_archive(self, archive_path: Path, split_size_mb: int) -> Path:
        """Split large archive into multiple parts."""
        # Use split command on Unix-like systems
        cmd = ["split", "-b", f"{split_size_mb}M", str(archive_path), str(archive_path) + ".part"]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Split failed: {stderr.decode()}")
            # Return original file if split fails
            return archive_path

        # Remove original and return first part
        archive_path.unlink()
        return Path(str(archive_path) + ".partaa")

    async def _update_progress(self, callback: Callable | None, progress: float, message: str):
        """Update progress if callback provided."""
        if callback:
            await callback(progress, message)

    def get_export_status(self, export_id: str) -> dict[str, Any] | None:
        """Get status of an export operation."""
        # This would be implemented with a proper job tracking system
        # For now, return None
        return None

    def list_exports(self) -> list[dict[str, Any]]:
        """List available exports."""
        exports = []
        for file in self.temp_dir.glob("*_export_*.{zip,tar.gz}"):
            exports.append(
                {
                    "filename": file.name,
                    "size": file.stat().st_size,
                    "created": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                }
            )
        return exports

    def cleanup_old_exports(self, days: int = 7):
        """Clean up exports older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        for file in self.temp_dir.glob("*_export_*"):
            if file.stat().st_mtime < cutoff:
                file.unlink()
                logger.info(f"Cleaned up old export: {file.name}")


# Service singleton
export_service = ProjectExportService()
