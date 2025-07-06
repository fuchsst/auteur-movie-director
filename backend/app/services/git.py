"""
Git integration service with LFS support.
Manages version control for project repositories.
"""

import asyncio
import logging
import subprocess
from datetime import datetime
from pathlib import Path

import git
from git.exc import GitCommandError, InvalidGitRepositoryError

from app.config import settings

logger = logging.getLogger(__name__)


class GitService:
    """
    Service for managing Git repositories with LFS support.
    Handles automatic version control for creative assets.
    """

    # Media file extensions that should use Git LFS
    LFS_EXTENSIONS = {
        # Video formats
        "*.mp4",
        "*.mov",
        "*.avi",
        "*.mkv",
        "*.webm",
        "*.flv",
        "*.wmv",
        "*.m4v",
        "*.mpg",
        "*.mpeg",
        "*.ogv",
        "*.prores",
        "*.dnxhd",
        "*.dnxhr",
        # Audio formats
        "*.wav",
        "*.mp3",
        "*.aiff",
        "*.flac",
        "*.ogg",
        "*.m4a",
        "*.wma",
        "*.aac",
        "*.opus",
        "*.ac3",
        "*.dts",
        # Image formats
        "*.psd",
        "*.psb",
        "*.ai",
        "*.indd",
        "*.raw",
        "*.arw",
        "*.cr2",
        "*.nef",
        "*.dng",
        "*.orf",
        "*.rw2",
        "*.tiff",
        "*.tif",
        "*.exr",
        "*.hdr",
        "*.dpx",
        "*.bmp",
        "*.jp2",
        "*.j2k",
        # 3D formats
        "*.blend",
        "*.fbx",
        "*.obj",
        "*.dae",
        "*.3ds",
        "*.ply",
        "*.stl",
        "*.gltf",
        "*.glb",
        "*.usd",
        "*.usda",
        "*.usdc",
        "*.usdz",
        "*.abc",
        "*.max",
        "*.c4d",
        "*.ma",
        "*.mb",
        "*.ztl",
        "*.zpr",
        # AI/ML model formats
        "*.ckpt",
        "*.safetensors",
        "*.pt",
        "*.pth",
        "*.onnx",
        "*.pb",
        "*.h5",
        "*.keras",
        "*.tflite",
        "*.mlmodel",
        "*.caffemodel",
        # Archive formats
        "*.zip",
        "*.rar",
        "*.7z",
        "*.tar",
        "*.gz",
        "*.bz2",
        "*.xz",
        # Other large binary formats
        "*.pdf",
        "*.sketch",
        "*.fig",
        "*.xd",
    }

    # Semantic commit prefixes
    COMMIT_PREFIXES = {
        "feat": "New feature or capability",
        "asset": "New asset added",
        "fix": "Bug fix or correction",
        "refactor": "Code restructuring",
        "style": "Visual or formatting changes",
        "test": "Test additions or changes",
        "docs": "Documentation updates",
        "chore": "Maintenance tasks",
        "wip": "Work in progress",
    }

    def __init__(self):
        self.author_name = settings.git_author_name or "Auteur Movie Director"
        self.author_email = settings.git_author_email or "auteur@localhost"

    async def check_lfs_installed(self) -> bool:
        """Check if Git LFS is installed and available."""
        from app.services.git_lfs import git_lfs_service

        return git_lfs_service.check_lfs_installed()

    async def initialize_repository(self, project_path: Path) -> bool:
        """
        Initialize a new Git repository with LFS support.

        Args:
            project_path: Path to project directory

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create repository
            repo = git.Repo.init(project_path)

            # Configure author
            with repo.config_writer() as config:
                config.set_value("user", "name", self.author_name)
                config.set_value("user", "email", self.author_email)

            # Initialize LFS
            from app.services.git_lfs import git_lfs_service

            if git_lfs_service.lfs_available:
                try:
                    git_lfs_service.initialize_lfs(project_path)
                    logger.info(f"Initialized Git repository with LFS at {project_path}")
                except Exception as e:
                    logger.warning(f"Git LFS initialization failed: {e}")
            else:
                logger.warning("Git LFS not available, initialized without LFS support")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            return False

    def _generate_gitattributes(self) -> str:
        """Generate .gitattributes content with LFS tracking rules."""
        lines = ["# Git LFS tracking for media and large files", ""]

        # Group extensions by category
        categories = {
            "Video files": ["*.mp4", "*.mov", "*.avi", "*.mkv", "*.webm"],
            "Audio files": ["*.wav", "*.mp3", "*.aiff", "*.flac", "*.ogg"],
            "Large images": ["*.psd", "*.psb", "*.exr", "*.tiff", "*.dpx"],
            "3D files": ["*.blend", "*.fbx", "*.obj", "*.usd*", "*.abc"],
            "AI models": ["*.ckpt", "*.safetensors", "*.pt", "*.pth"],
            "Archives": ["*.zip", "*.rar", "*.7z", "*.tar", "*.gz"],
        }

        for category, extensions in categories.items():
            lines.append(f"# {category}")
            for ext in extensions:
                if ext in self.LFS_EXTENSIONS:
                    lines.append(f"{ext} filter=lfs diff=lfs merge=lfs -text")
            lines.append("")

        # Add remaining extensions
        lines.append("# Other large binary files")
        for ext in sorted(self.LFS_EXTENSIONS):
            if not any(ext in exts for exts in categories.values()):
                lines.append(f"{ext} filter=lfs diff=lfs merge=lfs -text")

        return "\n".join(lines)

    async def _run_git_command(self, cwd: Path, args: list[str]) -> tuple[str, str]:
        """Run a git command asynchronously."""
        cmd = ["git"] + args
        process = await asyncio.create_subprocess_exec(
            *cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise GitCommandError(cmd, process.returncode, stderr.decode())

        return stdout.decode(), stderr.decode()

    async def get_status(self, project_path: Path) -> dict[str, any]:
        """
        Get Git repository status including LFS tracking.

        Returns:
            Dictionary with status information
        """
        try:
            repo = git.Repo(project_path)

            # Get basic status
            status = {
                "initialized": True,
                "branch": repo.active_branch.name,
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files,
                "modified_files": [item.a_path for item in repo.index.diff(None)],
                "staged_files": [item.a_path for item in repo.index.diff("HEAD")],
            }

            # Check LFS status
            if await self.check_lfs_installed():
                stdout, _ = await self._run_git_command(project_path, ["lfs", "ls-files"])
                lfs_files = [line.split()[-1] for line in stdout.strip().split("\n") if line]
                status["lfs_files"] = lfs_files

                # Get LFS tracking info
                stdout, _ = await self._run_git_command(project_path, ["lfs", "track"])
                status["lfs_patterns"] = [
                    line.strip()
                    for line in stdout.split("\n")
                    if line.strip() and not line.startswith("Listing")
                ]

            return status

        except InvalidGitRepositoryError:
            return {"initialized": False}
        except Exception as e:
            logger.error(f"Error getting repository status: {e}")
            return {"initialized": False, "error": str(e)}

    async def commit_changes(
        self,
        project_path: Path,
        message: str,
        prefix: str | None = None,
        files: list[str] | None = None,
    ) -> bool:
        """
        Commit changes to the repository.

        Args:
            project_path: Path to project directory
            message: Commit message
            prefix: Semantic prefix (feat, fix, etc.)
            files: Specific files to commit, or None for all

        Returns:
            True if successful
        """
        try:
            repo = git.Repo(project_path)

            # Format message with prefix
            if prefix and prefix in self.COMMIT_PREFIXES:
                full_message = f"{prefix}: {message}"
            else:
                full_message = message

            # Stage files
            if files:
                repo.index.add(files)
            else:
                # Stage all modified and new files
                repo.git.add(A=True)

            # Check if there are changes to commit
            if len(repo.index.diff("HEAD")) == 0 and len(repo.untracked_files) == 0:
                logger.info("No changes to commit")
                return True

            # Commit
            repo.index.commit(full_message)
            logger.info(f"Committed changes: {full_message}")

            return True

        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return False

    async def get_history(
        self, project_path: Path, limit: int = 20, file_path: str | None = None
    ) -> list[dict[str, any]]:
        """
        Get commit history for the repository or a specific file.

        Args:
            project_path: Path to project directory
            limit: Maximum number of commits to return
            file_path: Optional path to get history for specific file

        Returns:
            List of commit information
        """
        try:
            repo = git.Repo(project_path)

            # Get commits
            if file_path:
                commits = list(repo.iter_commits(paths=file_path, max_count=limit))
            else:
                commits = list(repo.iter_commits(max_count=limit))

            history = []
            for commit in commits:
                history.append(
                    {
                        "hash": commit.hexsha[:8],
                        "message": commit.message.strip(),
                        "author": commit.author.name,
                        "email": commit.author.email,
                        "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                        "files_changed": len(commit.stats.files),
                    }
                )

            return history

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    async def track_large_file(self, project_path: Path, file_path: str) -> bool:
        """
        Ensure a large file is tracked by Git LFS.

        Args:
            project_path: Path to project directory
            file_path: Path to file relative to project root

        Returns:
            True if successful
        """
        try:
            if not await self.check_lfs_installed():
                logger.warning("Git LFS not available")
                return False

            # Check file size
            full_path = project_path / file_path
            if full_path.exists():
                size_mb = full_path.stat().st_size / (1024 * 1024)

                if size_mb > 50:  # Files larger than 50MB
                    # Track with LFS
                    await self._run_git_command(project_path, ["lfs", "track", file_path])

                    # Update .gitattributes
                    repo = git.Repo(project_path)
                    repo.index.add([".gitattributes"])

                    logger.info(f"Added {file_path} to Git LFS tracking")
                    return True

            return True

        except Exception as e:
            logger.error(f"Failed to track file with LFS: {e}")
            return False

    async def validate_repository(self, project_path: Path) -> dict[str, any]:
        """
        Validate repository health and configuration.

        Returns:
            Validation results with any issues found
        """
        results = {
            "valid": True,
            "issues": [],
            "warnings": [],
        }

        try:
            # Check if repository exists
            if not (project_path / ".git").exists():
                results["valid"] = False
                results["issues"].append("Not a Git repository")
                return results

            repo = git.Repo(project_path)

            # Check for uncommitted changes
            if repo.is_dirty():
                results["warnings"].append("Repository has uncommitted changes")

            # Check LFS
            if await self.check_lfs_installed():
                # Verify LFS is initialized
                stdout, _ = await self._run_git_command(project_path, ["lfs", "env"])
                if "git config filter.lfs.required = true" not in stdout:
                    results["warnings"].append("Git LFS not properly initialized")
            else:
                results["warnings"].append("Git LFS not installed")

            # Check .gitattributes
            gitattributes_path = project_path / ".gitattributes"
            if not gitattributes_path.exists():
                results["warnings"].append("Missing .gitattributes file")

            return results

        except Exception as e:
            results["valid"] = False
            results["issues"].append(f"Repository validation error: {str(e)}")
            return results


# Global service instance
git_service = GitService()
