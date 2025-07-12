"""
Git LFS (Large File Storage) service for managing large media files.
Provides comprehensive LFS operations and validation.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GitLFSService:
    """Service for managing Git LFS operations"""

    # File patterns for LFS tracking
    LFS_PATTERNS = [
        # Images
        "*.png",
        "*.jpg",
        "*.jpeg",
        "*.gif",
        "*.bmp",
        "*.tiff",
        "*.tif",
        "*.webp",
        "*.ico",
        "*.svg",
        "*.psd",
        "*.ai",
        "*.eps",
        # Videos
        "*.mp4",
        "*.avi",
        "*.mov",
        "*.wmv",
        "*.flv",
        "*.webm",
        "*.mkv",
        "*.m4v",
        "*.mpg",
        "*.mpeg",
        "*.3gp",
        "*.3g2",
        # Audio
        "*.mp3",
        "*.wav",
        "*.flac",
        "*.aac",
        "*.ogg",
        "*.wma",
        "*.m4a",
        "*.opus",
        "*.aiff",
        "*.alac",
        # 3D Models
        "*.obj",
        "*.fbx",
        "*.dae",
        "*.3ds",
        "*.blend",
        "*.stl",
        "*.ply",
        # AI Models
        "*.ckpt",
        "*.safetensors",
        "*.pt",
        "*.pth",
        "*.pkl",
        "*.h5",
        "*.onnx",
        "*.pb",
        "*.tflite",
        "*.bin",
        "*.model",
        # Archives
        "*.zip",
        "*.rar",
        "*.7z",
        "*.tar",
        "*.gz",
        "*.bz2",
        "*.xz",
        # Other large files
        "*.pdf",
        "*.exe",
        "*.dmg",
        "*.iso",
        "*.deb",
        "*.rpm",
    ]

    # Size threshold for automatic LFS tracking (50MB)
    SIZE_THRESHOLD = 50 * 1024 * 1024

    def __init__(self):
        self.lfs_available = self.check_lfs_installed()

    def check_lfs_installed(self) -> bool:
        """Check if Git LFS is installed and available"""
        try:
            result = subprocess.run(
                ["git", "lfs", "version"], capture_output=True, text=True, check=True
            )
            logger.info(f"Git LFS version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Git LFS is not installed or not in PATH")
            return False

    def initialize_lfs(self, project_path: Path) -> bool:
        """Initialize Git LFS in a project"""
        if not self.lfs_available:
            raise RuntimeError("Git LFS is not installed")

        try:
            # Initialize LFS
            subprocess.run(
                ["git", "lfs", "install"], cwd=project_path, check=True, capture_output=True
            )

            # Create .gitattributes
            self.create_gitattributes(project_path)

            logger.info(f"Git LFS initialized for project: {project_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize Git LFS: {e.stderr}")
            raise

    def create_gitattributes(self, project_path: Path) -> None:
        """Create .gitattributes file with LFS patterns"""
        gitattributes_path = project_path / ".gitattributes"

        content = ["# Git LFS patterns for Auteur Movie Director\n"]
        content.append("# Auto-generated - do not edit manually\n\n")

        # Group patterns by category
        categories = {
            "Images": [
                "*.png",
                "*.jpg",
                "*.jpeg",
                "*.gif",
                "*.bmp",
                "*.tiff",
                "*.tif",
                "*.webp",
                "*.psd",
                "*.ai",
                "*.eps",
            ],
            "Videos": [
                "*.mp4",
                "*.avi",
                "*.mov",
                "*.wmv",
                "*.flv",
                "*.webm",
                "*.mkv",
                "*.m4v",
                "*.mpg",
                "*.mpeg",
            ],
            "Audio": ["*.mp3", "*.wav", "*.flac", "*.aac", "*.ogg", "*.wma", "*.m4a", "*.opus"],
            "3D Models": ["*.obj", "*.fbx", "*.dae", "*.3ds", "*.blend", "*.stl"],
            "AI Models": [
                "*.ckpt",
                "*.safetensors",
                "*.pt",
                "*.pth",
                "*.pkl",
                "*.h5",
                "*.onnx",
                "*.pb",
                "*.tflite",
                "*.bin",
            ],
            "Archives": ["*.zip", "*.rar", "*.7z", "*.tar", "*.gz", "*.bz2"],
            "Large Files": ["*.pdf", "*.exe", "*.dmg", "*.iso"],
        }

        for category, patterns in categories.items():
            content.append(f"# {category}\n")
            for pattern in patterns:
                content.append(f"{pattern} filter=lfs diff=lfs merge=lfs -text\n")
            content.append("\n")

        # Write file
        with open(gitattributes_path, "w") as f:
            f.writelines(content)

        # Stage the .gitattributes file
        subprocess.run(["git", "add", ".gitattributes"], cwd=project_path, check=True)

    def track_file(self, project_path: Path, file_path: str) -> bool:
        """Track a specific file with Git LFS"""
        if not self.lfs_available:
            raise RuntimeError("Git LFS is not installed")

        try:
            subprocess.run(
                ["git", "lfs", "track", file_path],
                cwd=project_path,
                check=True,
                capture_output=True,
            )

            # Stage the updated .gitattributes
            subprocess.run(["git", "add", ".gitattributes"], cwd=project_path, check=True)

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to track file with LFS: {e.stderr}")
            return False

    def untrack_file(self, project_path: Path, pattern: str) -> bool:
        """Untrack a pattern from Git LFS"""
        if not self.lfs_available:
            raise RuntimeError("Git LFS is not installed")

        try:
            subprocess.run(
                ["git", "lfs", "untrack", pattern],
                cwd=project_path,
                check=True,
                capture_output=True,
            )

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to untrack pattern from LFS: {e.stderr}")
            return False

    def get_lfs_files(self, project_path: Path) -> list[dict[str, Any]]:
        """Get list of files tracked by Git LFS"""
        if not self.lfs_available:
            return []

        try:
            result = subprocess.run(
                ["git", "lfs", "ls-files"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True,
            )

            files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    # Parse: oid size path
                    parts = line.split(None, 2)
                    if len(parts) >= 3:
                        files.append({"oid": parts[0], "size": int(parts[1]), "path": parts[2]})

            return files

        except subprocess.CalledProcessError:
            return []

    def check_file_size(self, file_path: Path) -> bool:
        """Check if file should be tracked by LFS based on size"""
        try:
            size = file_path.stat().st_size
            return size > self.SIZE_THRESHOLD
        except OSError:
            return False

    def get_lfs_status(self, project_path: Path) -> dict[str, Any]:
        """Get comprehensive LFS status for a project"""
        if not self.lfs_available:
            return {"enabled": False, "installed": False, "error": "Git LFS is not installed"}

        try:
            # Check if LFS is initialized
            result = subprocess.run(
                ["git", "config", "--get", "filter.lfs.clean"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )

            lfs_initialized = result.returncode == 0

            # Get tracked patterns
            patterns = []
            gitattributes = project_path / ".gitattributes"
            if gitattributes.exists():
                with open(gitattributes) as f:
                    for line in f:
                        if "filter=lfs" in line:
                            pattern = line.split()[0]
                            patterns.append(pattern)

            # Get LFS files
            lfs_files = self.get_lfs_files(project_path)

            return {
                "enabled": True,
                "installed": True,
                "initialized": lfs_initialized,
                "tracked_patterns": patterns,
                "tracked_files": lfs_files,
                "file_count": len(lfs_files),
                "total_size": sum(f["size"] for f in lfs_files),
            }

        except Exception as e:
            logger.error(f"Failed to get LFS status: {e}")
            return {"enabled": True, "installed": True, "initialized": False, "error": str(e)}

    def validate_lfs_setup(self) -> dict[str, Any]:
        """Validate system-wide LFS setup"""
        validation = {
            "git_installed": False,
            "lfs_installed": False,
            "lfs_version": None,
            "git_version": None,
            "issues": [],
        }

        # Check Git
        try:
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True, check=True
            )
            validation["git_installed"] = True
            validation["git_version"] = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            validation["issues"].append("Git is not installed")

        # Check Git LFS
        if validation["git_installed"]:
            try:
                result = subprocess.run(
                    ["git", "lfs", "version"], capture_output=True, text=True, check=True
                )
                validation["lfs_installed"] = True
                validation["lfs_version"] = result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                validation["issues"].append("Git LFS is not installed")

        return validation


# Global instance
git_lfs_service = GitLFSService()
