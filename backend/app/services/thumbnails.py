"""
Thumbnail generation service for media files.
"""

import asyncio
import logging
import shutil
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


class ThumbnailService:
    """Service for generating thumbnails from media files"""

    # Standard thumbnail sizes
    SIZES = {
        "large": (512, 512),
        "medium": (320, 180),  # 16:9 aspect for videos
        "small": (128, 128),
    }

    def __init__(self):
        self.ffmpeg_available = shutil.which("ffmpeg") is not None
        if not self.ffmpeg_available:
            logger.warning("ffmpeg not found - video thumbnail generation will be disabled")

    async def generate_thumbnail(
        self,
        source_path: Path,
        output_path: Path,
        size: tuple[int, int] = (320, 180),
        timestamp: float = 1.0,
    ) -> bool:
        """
        Generate a thumbnail from an image or video file.

        Args:
            source_path: Path to source media file
            output_path: Path for output thumbnail
            size: Tuple of (width, height) for thumbnail
            timestamp: For videos, the timestamp to capture (in seconds)

        Returns:
            True if successful, False otherwise
        """
        if not source_path.exists():
            logger.error(f"Source file not found: {source_path}")
            return False

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine file type
        suffix = source_path.suffix.lower()

        if suffix in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
            return await self._generate_image_thumbnail(source_path, output_path, size)
        elif suffix in [".mp4", ".mov", ".avi", ".mkv", ".webm"] and self.ffmpeg_available:
            return await self._generate_video_thumbnail(source_path, output_path, size, timestamp)
        else:
            logger.warning(f"Unsupported file type for thumbnail: {suffix}")
            return False

    async def _generate_image_thumbnail(
        self, source_path: Path, output_path: Path, size: tuple[int, int]
    ) -> bool:
        """Generate thumbnail from an image file using Pillow"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._create_image_thumbnail_sync, source_path, output_path, size
            )
            return True
        except Exception as e:
            logger.error(f"Error generating image thumbnail: {e}")
            return False

    def _create_image_thumbnail_sync(
        self, source_path: Path, output_path: Path, size: tuple[int, int]
    ):
        """Synchronous image thumbnail creation"""
        with Image.open(source_path) as img:
            # Convert to RGB if necessary
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            # Calculate aspect-preserving size
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Create background if aspect doesn't match
            if img.size != size:
                # Create new image with exact size
                new_img = Image.new("RGB", size, (0, 0, 0))
                # Paste resized image centered
                x = (size[0] - img.size[0]) // 2
                y = (size[1] - img.size[1]) // 2
                new_img.paste(img, (x, y))
                img = new_img

            # Save as JPEG for smaller size
            img.save(output_path, "PNG", optimize=True, quality=85)

    async def _generate_video_thumbnail(
        self, source_path: Path, output_path: Path, size: tuple[int, int], timestamp: float
    ) -> bool:
        """Generate thumbnail from a video file using ffmpeg"""
        try:
            cmd = [
                "ffmpeg",
                "-ss",
                str(timestamp),  # Seek to timestamp
                "-i",
                str(source_path),  # Input file
                "-vframes",
                "1",  # Extract 1 frame
                "-vf",
                f"scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease,pad={size[0]}:{size[1]}:(ow-iw)/2:(oh-ih)/2",
                "-y",  # Overwrite output
                str(output_path),  # Output file
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"ffmpeg failed: {stderr.decode()}")
                return False

            logger.debug(f"Generated video thumbnail: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating video thumbnail: {e}")
            return False

    async def generate_multiple_sizes(
        self,
        source_path: Path,
        output_dir: Path,
        base_name: str,
        timestamp: float = 1.0,
    ) -> dict[str, Path]:
        """
        Generate thumbnails in multiple standard sizes.

        Args:
            source_path: Path to source media file
            output_dir: Directory for output thumbnails
            base_name: Base name for thumbnail files
            timestamp: For videos, the timestamp to capture

        Returns:
            Dictionary mapping size name to output path
        """
        results = {}

        # Generate thumbnails concurrently
        tasks = []
        for size_name, dimensions in self.SIZES.items():
            output_path = output_dir / f"{base_name}_thumb_{size_name}.png"
            task = self.generate_thumbnail(source_path, output_path, dimensions, timestamp)
            tasks.append((size_name, output_path, task))

        # Wait for all thumbnails to complete
        for size_name, output_path, task in tasks:
            success = await task
            if success:
                results[size_name] = output_path
            else:
                logger.warning(f"Failed to generate {size_name} thumbnail")

        return results

    async def clean_thumbnails(self, base_path: Path, base_name: str) -> int:
        """
        Clean up all thumbnails for a given base name.

        Args:
            base_path: Directory containing thumbnails
            base_name: Base name of thumbnails to remove

        Returns:
            Number of files removed
        """
        removed = 0
        pattern = f"{base_name}_thumb_*.png"

        for thumb_file in base_path.glob(pattern):
            try:
                thumb_file.unlink()
                removed += 1
                logger.debug(f"Removed thumbnail: {thumb_file}")
            except Exception as e:
                logger.error(f"Failed to remove thumbnail {thumb_file}: {e}")

        return removed


# Global instance
thumbnail_service = ThumbnailService()
