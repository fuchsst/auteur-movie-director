"""
Takes management service for non-destructive versioning of generated content.
"""

import asyncio
import json
import logging
import platform
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)


class TakesService:
    """Manages takes (versioned outputs) for shots"""

    def __init__(self):
        self.active_takes_file = "active_take.json"
        self.metadata_suffix = "_metadata.json"
        self.thumbnail_suffix = "_thumbnail.png"

    async def create_take_directory(
        self, project_path: Path, shot_id: str, take_number: int
    ) -> Path:
        """Create directory structure for a new take"""
        # Parse shot structure (e.g., "001_Shot_Description")
        parts = shot_id.split("/")
        if len(parts) >= 3:
            chapter = parts[0]
            scene = parts[1]
            shot = parts[2]
        else:
            # Fallback for simple shot_id
            chapter = "01_Default_Chapter"
            scene = "01_Default_Scene"
            shot = shot_id

        # Build path: 03_Renders/Chapter/Scene/Shot/takes/take_XXX
        renders_dir = project_path / "03_Renders" / chapter / scene / shot / "takes"
        take_id = f"take_{str(take_number).zfill(3)}"
        take_dir = renders_dir / take_id

        # Create directory
        take_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created take directory: {take_dir}")

        return take_dir

    def generate_take_name(self, shot_id: str, take_number: int, extension: str = "mp4") -> str:
        """Generate standardized take filename"""
        # Extract shot name from ID
        shot_name = shot_id.split("/")[-1] if "/" in shot_id else shot_id
        take_id = f"take_{str(take_number).zfill(3)}"
        return f"{shot_name}_{take_id}.{extension}"

    async def get_next_take_number(self, project_path: Path, shot_id: str) -> int:
        """Get the next available take number for a shot"""
        takes = await self.list_takes(project_path, shot_id)
        if not takes:
            return 1

        # Extract take numbers
        numbers = []
        for take in takes:
            if "id" in take and take["id"].startswith("take_"):
                try:
                    num = int(take["id"].split("_")[1])
                    numbers.append(num)
                except (IndexError, ValueError):
                    continue

        return max(numbers) + 1 if numbers else 1

    async def save_take_metadata(
        self,
        take_dir: Path,
        take_id: str,
        shot_id: str,
        generation_params: dict[str, Any],
        quality: str = "standard",
    ) -> Path:
        """Save metadata for a take"""
        metadata = {
            "id": take_id,
            "shotId": shot_id,
            "created": datetime.now(UTC).isoformat(),
            "generationParams": generation_params,
            "resources": {
                "quality": quality,
                "vramUsed": 0,  # To be updated by generation
                "generationTime": 0,  # To be updated by generation
            },
            "status": "generating",
        }

        # Generate filename from take_id
        base_name = take_id.replace("take_", f"{shot_id.split('/')[-1]}_take_")
        metadata_path = take_dir / f"{base_name}{self.metadata_suffix}"

        async with aiofiles.open(metadata_path, "w") as f:
            await f.write(json.dumps(metadata, indent=2))

        logger.debug(f"Saved take metadata: {metadata_path}")
        return metadata_path

    async def update_take_metadata(
        self, metadata_path: Path, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Update existing take metadata"""
        # Read existing metadata
        async with aiofiles.open(metadata_path) as f:
            content = await f.read()
            metadata = json.loads(content)

        # Deep merge updates
        for key, value in updates.items():
            if isinstance(value, dict) and key in metadata and isinstance(metadata[key], dict):
                metadata[key].update(value)
            else:
                metadata[key] = value

        # Write back
        async with aiofiles.open(metadata_path, "w") as f:
            await f.write(json.dumps(metadata, indent=2))

        return metadata

    async def list_takes(self, project_path: Path, shot_id: str) -> list[dict[str, Any]]:
        """List all takes for a shot"""
        # Parse shot structure
        parts = shot_id.split("/")
        if len(parts) >= 3:
            chapter = parts[0]
            scene = parts[1]
            shot = parts[2]
        else:
            chapter = "01_Default_Chapter"
            scene = "01_Default_Scene"
            shot = shot_id

        takes_dir = project_path / "03_Renders" / chapter / scene / shot / "takes"
        if not takes_dir.exists():
            return []

        takes = []
        for take_dir in sorted(takes_dir.iterdir()):
            if not take_dir.is_dir() or not take_dir.name.startswith("take_"):
                continue

            # Find metadata file
            metadata_files = list(take_dir.glob(f"*{self.metadata_suffix}"))
            if not metadata_files:
                continue

            try:
                async with aiofiles.open(metadata_files[0]) as f:
                    content = await f.read()
                    metadata = json.loads(content)

                # Find thumbnail
                thumbnail_files = list(take_dir.glob(f"*{self.thumbnail_suffix}"))
                if thumbnail_files:
                    metadata["thumbnailPath"] = str(thumbnail_files[0].relative_to(project_path))

                # Find main file
                for ext in [".mp4", ".mov", ".avi", ".png", ".jpg"]:
                    main_files = list(take_dir.glob(f"*{ext}"))
                    if main_files and not main_files[0].name.endswith(self.thumbnail_suffix):
                        metadata["filePath"] = str(main_files[0].relative_to(project_path))
                        metadata["fileSize"] = main_files[0].stat().st_size
                        break

                takes.append(metadata)

            except Exception as e:
                logger.error(f"Error reading take metadata from {metadata_files[0]}: {e}")
                continue

        return takes

    async def get_active_take(self, project_path: Path, shot_id: str) -> str | None:
        """Get the currently active take for a shot"""
        # Parse shot structure
        parts = shot_id.split("/")
        if len(parts) >= 3:
            chapter = parts[0]
            scene = parts[1]
            shot = parts[2]
        else:
            chapter = "01_Default_Chapter"
            scene = "01_Default_Scene"
            shot = shot_id

        shot_dir = project_path / "03_Renders" / chapter / scene / shot
        active_file = shot_dir / self.active_takes_file

        if active_file.exists():
            try:
                async with aiofiles.open(active_file) as f:
                    content = await f.read()
                    data = json.loads(content)
                    return data.get("activeTakeId")
            except Exception as e:
                logger.error(f"Error reading active take file: {e}")

        return None

    async def set_active_take(self, project_path: Path, shot_id: str, take_id: str) -> bool:
        """Set the active take for a shot"""
        # Verify take exists
        takes = await self.list_takes(project_path, shot_id)
        if not any(t.get("id") == take_id for t in takes):
            logger.error(f"Take {take_id} not found for shot {shot_id}")
            return False

        # Parse shot structure
        parts = shot_id.split("/")
        if len(parts) >= 3:
            chapter = parts[0]
            scene = parts[1]
            shot = parts[2]
        else:
            chapter = "01_Default_Chapter"
            scene = "01_Default_Scene"
            shot = shot_id

        shot_dir = project_path / "03_Renders" / chapter / scene / shot
        active_file = shot_dir / self.active_takes_file

        # Write active take pointer
        data = {
            "shotId": shot_id,
            "activeTakeId": take_id,
            "updated": datetime.now(UTC).isoformat(),
        }

        async with aiofiles.open(active_file, "w") as f:
            await f.write(json.dumps(data, indent=2))

        # Try to create symlink (optional)
        await self._update_active_symlink(project_path, shot_id, take_id)

        logger.info(f"Set active take for {shot_id} to {take_id}")
        return True

    async def _update_active_symlink(self, project_path: Path, shot_id: str, take_id: str) -> None:
        """Update active take symlink (platform-dependent)"""
        try:
            # Parse shot structure
            parts = shot_id.split("/")
            if len(parts) >= 3:
                chapter = parts[0]
                scene = parts[1]
                shot = parts[2]
            else:
                chapter = "01_Default_Chapter"
                scene = "01_Default_Scene"
                shot = shot_id

            shot_dir = project_path / "03_Renders" / chapter / scene / shot
            symlink_path = shot_dir / "active_take"
            target_path = shot_dir / "takes" / take_id

            # Remove existing symlink/junction
            if symlink_path.exists() or symlink_path.is_symlink():
                if platform.system() == "Windows":
                    # Windows junction
                    import subprocess

                    subprocess.run(["cmd", "/c", "rmdir", str(symlink_path)], capture_output=True)
                else:
                    symlink_path.unlink()

            # Create new symlink/junction
            if platform.system() == "Windows":
                # Use junction on Windows
                import subprocess

                subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(symlink_path), str(target_path)],
                    capture_output=True,
                    check=True,
                )
            else:
                # Use symlink on Unix
                symlink_path.symlink_to(target_path)

            logger.debug(f"Updated active take symlink: {symlink_path} -> {target_path}")

        except Exception as e:
            # Symlinks are optional enhancement, don't fail
            logger.debug(f"Could not create active take symlink: {e}")

    async def delete_take(self, project_path: Path, shot_id: str, take_id: str) -> bool:
        """Mark a take as deleted (soft delete)"""
        # Parse shot structure
        parts = shot_id.split("/")
        if len(parts) >= 3:
            chapter = parts[0]
            scene = parts[1]
            shot = parts[2]
        else:
            chapter = "01_Default_Chapter"
            scene = "01_Default_Scene"
            shot = shot_id

        takes_dir = project_path / "03_Renders" / chapter / scene / shot / "takes"
        take_dir = takes_dir / take_id

        if not take_dir.exists():
            logger.error(f"Take directory not found: {take_dir}")
            return False

        # Check if this is the active take
        active_take = await self.get_active_take(project_path, shot_id)
        if active_take == take_id:
            # Find another take to make active
            takes = await self.list_takes(project_path, shot_id)
            other_takes = [t for t in takes if t.get("id") != take_id]
            if other_takes:
                await self.set_active_take(project_path, shot_id, other_takes[0]["id"])
            else:
                # Remove active take file if no other takes
                active_file = (
                    project_path / "03_Renders" / chapter / scene / shot / self.active_takes_file
                )
                if active_file.exists():
                    active_file.unlink()

        # Rename directory to mark as deleted
        deleted_dir = takes_dir / f".deleted_{take_id}_{int(datetime.now(UTC).timestamp())}"
        take_dir.rename(deleted_dir)

        logger.info(f"Soft deleted take: {take_id}")
        return True

    async def generate_thumbnail(
        self, media_path: Path, output_path: Path, timestamp: float = 1.0
    ) -> bool:
        """Generate thumbnail from media file"""
        try:
            # Check if ffmpeg is available
            ffmpeg_cmd = shutil.which("ffmpeg")
            if not ffmpeg_cmd:
                logger.warning("ffmpeg not found, skipping thumbnail generation")
                return False

            # Build ffmpeg command
            cmd = [
                ffmpeg_cmd,
                "-ss",
                str(timestamp),  # Seek to timestamp
                "-i",
                str(media_path),  # Input file
                "-vframes",
                "1",  # Extract 1 frame
                "-vf",
                "scale=320:180",  # Scale to 320x180
                "-y",  # Overwrite output
                str(output_path),  # Output file
            ]

            # Run ffmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"ffmpeg failed: {stderr.decode()}")
                return False

            logger.debug(f"Generated thumbnail: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return False

    async def cleanup_old_takes(
        self, project_path: Path, shot_id: str, keep_count: int = 10
    ) -> int:
        """Clean up old takes, keeping the most recent ones and the active take"""
        takes = await self.list_takes(project_path, shot_id)
        if len(takes) <= keep_count:
            return 0

        # Sort by creation date
        takes.sort(key=lambda t: t.get("created", ""), reverse=True)

        # Get active take
        active_take = await self.get_active_take(project_path, shot_id)

        # Separate active take from others
        active_take_data = None
        other_takes = []
        for take in takes:
            if take.get("id") == active_take:
                active_take_data = take
            else:
                other_takes.append(take)

        # Build list of takes to keep
        takes_to_keep = []
        if active_take_data:
            takes_to_keep.append(active_take_data)
            # Keep the most recent (keep_count - 1) other takes
            takes_to_keep.extend(other_takes[: keep_count - 1])
        else:
            # No active take, just keep the most recent keep_count
            takes_to_keep = takes[:keep_count]

        # Get IDs of takes to keep
        keep_ids = {take.get("id") for take in takes_to_keep if take.get("id")}

        # Delete takes not in keep list
        deleted_count = 0
        for take in takes:
            take_id = take.get("id")
            if take_id and take_id not in keep_ids:
                if await self.delete_take(project_path, shot_id, take_id):
                    deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old takes for {shot_id}")
        return deleted_count

    async def export_take(
        self, project_path: Path, shot_id: str, take_id: str, export_dir: Path
    ) -> Path | None:
        """Export a take to the exports directory"""
        # Parse shot structure
        parts = shot_id.split("/")
        if len(parts) >= 3:
            chapter = parts[0]
            scene = parts[1]
            shot = parts[2]
        else:
            chapter = "01_Default_Chapter"
            scene = "01_Default_Scene"
            shot = shot_id

        takes_dir = project_path / "03_Renders" / chapter / scene / shot / "takes"
        take_dir = takes_dir / take_id

        if not take_dir.exists():
            logger.error(f"Take directory not found: {take_dir}")
            return None

        # Find main file
        main_file = None
        for ext in [".mp4", ".mov", ".avi", ".png", ".jpg"]:
            files = list(take_dir.glob(f"*{ext}"))
            if files and not files[0].name.endswith(self.thumbnail_suffix):
                main_file = files[0]
                break

        if not main_file:
            logger.error(f"No media file found in take: {take_id}")
            return None

        # Create export directory structure
        export_subdir = export_dir / chapter / scene / shot
        export_subdir.mkdir(parents=True, exist_ok=True)

        # Copy file to export directory
        export_path = export_subdir / main_file.name
        shutil.copy2(main_file, export_path)

        # Also copy metadata
        metadata_files = list(take_dir.glob(f"*{self.metadata_suffix}"))
        if metadata_files:
            shutil.copy2(metadata_files[0], export_subdir / metadata_files[0].name)

        logger.info(f"Exported take {take_id} to {export_path}")
        return export_path

    async def create_and_save_take(
        self,
        project_path: Path,
        shot_id: str,
        file_content: bytes,
        file_extension: str = "mp4",
        generation_params: dict[str, Any] = None,
        quality: str = "standard",
    ) -> dict[str, Any]:
        """
        Create and save a complete take with file content.
        This is a simplified interface for creating takes.
        """
        if generation_params is None:
            generation_params = {
                "model": "default",
                "seed": 42,
                "prompt": "Generated content",
                "steps": 20,
                "cfg": 7.5,
            }

        # Get next take number
        take_number = await self.get_next_take_number(project_path, shot_id)
        take_id = f"take_{str(take_number).zfill(3)}"

        # Create take directory
        take_dir = await self.create_take_directory(project_path, shot_id, take_number)

        # Save main file
        filename = self.generate_take_name(shot_id, take_number, file_extension)
        file_path = take_dir / filename

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        # Save metadata
        metadata_path = await self.save_take_metadata(
            take_dir=take_dir,
            take_id=take_id,
            shot_id=shot_id,
            generation_params=generation_params,
            quality=quality,
        )

        # Update metadata with file info
        updates = {
            "status": "complete",
            "filePath": str(file_path.relative_to(project_path)),
            "fileSize": len(file_content),
        }
        await self.update_take_metadata(metadata_path, updates)

        # Generate thumbnail if it's a video/image
        if file_extension.lower() in ["mp4", "mov", "avi"]:
            thumbnail_name = f"{filename.rsplit('.', 1)[0]}{self.thumbnail_suffix}"
            thumbnail_path = take_dir / thumbnail_name
            await self.generate_thumbnail(file_path, thumbnail_path)

        # Check if this should be the active take (if no active take exists)
        active_take = await self.get_active_take(project_path, shot_id)
        if active_take is None:
            await self.set_active_take(project_path, shot_id, take_id)

        # Update project metadata
        await self._update_project_metadata(project_path, shot_id, take_id)

        logger.info(f"Created and saved take {take_id} for shot {shot_id}")

        # Return take metadata
        takes = await self.list_takes(project_path, shot_id)
        return next((t for t in takes if t.get("id") == take_id), {})

    async def _update_project_metadata(self, project_path: Path, shot_id: str, take_id: str):
        """Update project.json with take information"""
        try:
            project_file = project_path / "project.json"
            if not project_file.exists():
                return

            async with aiofiles.open(project_file, "r") as f:
                content = await f.read()
                project_data = json.loads(content)

            # Initialize takes structure if not exists
            if "takes" not in project_data:
                project_data["takes"] = {}

            if shot_id not in project_data["takes"]:
                project_data["takes"][shot_id] = {
                    "total_takes": 0,
                    "active_take": None,
                    "last_generated": None,
                }

            # Update take info
            project_data["takes"][shot_id]["total_takes"] += 1
            project_data["takes"][shot_id]["last_generated"] = datetime.now(UTC).isoformat()

            # Update active take if this is the first one
            if project_data["takes"][shot_id]["active_take"] is None:
                project_data["takes"][shot_id]["active_take"] = take_id

            # Update project modified time
            project_data["updated_at"] = datetime.now(UTC).isoformat()

            # Save updated project data
            async with aiofiles.open(project_file, "w") as f:
                await f.write(json.dumps(project_data, indent=2))

            logger.debug(f"Updated project metadata for take {take_id}")

        except Exception as e:
            logger.warning(f"Failed to update project metadata: {e}")


# Global instance
takes_service = TakesService()
