"""
Git integration service with LFS support.
Manages version control for project repositories.
"""

import asyncio
import logging
import subprocess
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

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
        "*.png",
        "*.jpg",
        "*.jpeg",
        "*.gif",
        "*.webp",
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
        "*.bin",
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

            # Create initial commit
            try:
                # Stage all files in the project
                repo.git.add(A=True)

                # Create initial commit
                repo.index.commit("Initial project setup")
                logger.info("Created initial commit")
            except Exception as e:
                logger.warning(f"Failed to create initial commit: {e}")
                # Don't fail initialization if commit fails

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

    async def get_config(self, project_path: Path) -> dict[str, any]:
        """
        Get Git configuration for a repository.

        Returns:
            Dictionary with configuration details
        """
        try:
            config = {
                "user_name": None,
                "user_email": None,
                "lfs_enabled": False,
                "lfs_version": None,
                "git_version": None,
                "tracked_patterns": [],
            }

            # Check if repository exists
            if not (project_path / ".git").exists():
                return config

            repo = git.Repo(project_path)

            # Get user config
            with repo.config_reader() as git_config:
                if git_config.has_option("user", "name"):
                    config["user_name"] = git_config.get_value("user", "name")
                if git_config.has_option("user", "email"):
                    config["user_email"] = git_config.get_value("user", "email")

            # Get Git version
            try:
                result = subprocess.run(
                    ["git", "--version"], capture_output=True, text=True, check=True
                )
                config["git_version"] = result.stdout.strip()
            except Exception:
                pass

            # Get LFS status
            from app.services.git_lfs import git_lfs_service

            if git_lfs_service.lfs_available:
                config["lfs_enabled"] = True
                try:
                    result = subprocess.run(
                        ["git", "lfs", "version"], capture_output=True, text=True, check=True
                    )
                    config["lfs_version"] = result.stdout.strip()
                except Exception:
                    pass

                # Get tracked patterns from .gitattributes
                gitattributes = project_path / ".gitattributes"
                if gitattributes.exists():
                    patterns = []
                    with open(gitattributes) as f:
                        for line in f:
                            if "filter=lfs" in line and not line.strip().startswith("#"):
                                pattern = line.split()[0]
                                patterns.append(pattern)
                    config["tracked_patterns"] = patterns

            return config

        except Exception as e:
            logger.error(f"Failed to get repository config: {e}")
            return {
                "user_name": None,
                "user_email": None,
                "lfs_enabled": False,
                "lfs_version": None,
                "git_version": None,
                "tracked_patterns": [],
                "error": str(e),
            }

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

    async def get_enhanced_history(
        self, project_path: Path, limit: int = 50, file_path: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Get enhanced commit history with diff statistics.

        Args:
            project_path: Path to project directory
            limit: Maximum number of commits to return
            file_path: Optional path to get history for specific file

        Returns:
            List of enhanced commit information with diffs
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
                # Get diff statistics
                stats = commit.stats.total

                # Get list of changed files
                changed_files = []
                if commit.parents:
                    diffs = commit.diff(commit.parents[0])
                    for diff in diffs:
                        changed_files.append(
                            {
                                "path": diff.a_path or diff.b_path,
                                "change_type": diff.change_type,
                                "additions": diff.diff.count(b"\n+"),
                                "deletions": diff.diff.count(b"\n-"),
                            }
                        )

                history.append(
                    {
                        "hash": commit.hexsha,
                        "short_hash": commit.hexsha[:8],
                        "message": commit.message.strip(),
                        "author": commit.author.name,
                        "email": commit.author.email,
                        "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                        "stats": {
                            "additions": stats.get("insertions", 0),
                            "deletions": stats.get("deletions", 0),
                            "files": stats.get("files", 0),
                        },
                        "files": changed_files[:10],  # Limit to 10 files for performance
                        "parent_hashes": [p.hexsha for p in commit.parents],
                    }
                )

            return history

        except Exception as e:
            logger.error(f"Failed to get enhanced history: {e}")
            return []

    async def rollback(self, project_path: Path, commit_hash: str, mode: str = "soft") -> bool:
        """
        Rollback to a specific commit.

        Args:
            project_path: Path to project directory
            commit_hash: Hash of commit to rollback to
            mode: Rollback mode - "soft" (keep changes), "mixed" (unstage), "hard" (discard)

        Returns:
            True if successful
        """
        try:
            repo = git.Repo(project_path)

            # Validate commit exists
            try:
                commit = repo.commit(commit_hash)
            except Exception:
                logger.error(f"Invalid commit hash: {commit_hash}")
                return False

            # Check for uncommitted changes if hard reset
            if mode == "hard" and repo.is_dirty():
                logger.warning("Repository has uncommitted changes, cannot hard reset")
                return False

            # Perform rollback
            if mode == "soft":
                repo.head.reset(commit, index=False, working_tree=False)
            elif mode == "mixed":
                repo.head.reset(commit, index=True, working_tree=False)
            elif mode == "hard":
                repo.head.reset(commit, index=True, working_tree=True)
            else:
                logger.error(f"Invalid rollback mode: {mode}")
                return False

            logger.info(f"Rolled back to commit {commit_hash} ({mode} mode)")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback: {e}")
            return False

    async def create_tag(
        self, project_path: Path, tag_name: str, message: str | None = None
    ) -> bool:
        """
        Create a tag at the current HEAD.

        Args:
            project_path: Path to project directory
            tag_name: Name for the tag
            message: Optional tag message (creates annotated tag)

        Returns:
            True if successful
        """
        try:
            repo = git.Repo(project_path)

            # Check if tag already exists
            if tag_name in [tag.name for tag in repo.tags]:
                logger.error(f"Tag '{tag_name}' already exists")
                return False

            # Create tag
            if message:
                # Annotated tag
                repo.create_tag(tag_name, message=message)
            else:
                # Lightweight tag
                repo.create_tag(tag_name)

            logger.info(f"Created tag: {tag_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create tag: {e}")
            return False

    def generate_commit_message(self, changes: list[str]) -> str:
        """
        Generate descriptive commit message based on changed files.

        Args:
            changes: List of changed file paths

        Returns:
            Generated commit message
        """
        if not changes:
            return "chore: Update files"

        # Analyze changes
        categories = defaultdict(list)
        for file_path in changes:
            path = Path(file_path)

            # Categorize by directory
            if path.parts:
                if "01_Assets" in path.parts:
                    categories["assets"].append(path.name)
                elif "03_Renders" in path.parts:
                    categories["renders"].append(path.name)
                elif "02_Story" in path.parts:
                    categories["story"].append(path.name)
                elif "04_Compositions" in path.parts:
                    categories["compositions"].append(path.name)
                elif "05_Audio" in path.parts:
                    categories["audio"].append(path.name)
                elif "06_Exports" in path.parts:
                    categories["exports"].append(path.name)
                else:
                    categories["other"].append(path.name)

        # Generate message based on categories
        if len(categories) == 1:
            category = list(categories.keys())[0]
            count = len(list(categories.values())[0])

            messages = {
                "assets": f"feat: Add {count} new asset{'s' if count > 1 else ''}",
                "renders": f"feat: Generate {count} new render{'s' if count > 1 else ''}",
                "story": f"docs: Update story content ({count} file{'s' if count > 1 else ''})",
                "compositions": f"feat: Update {count} composition{'s' if count > 1 else ''}",
                "audio": f"feat: Add {count} audio file{'s' if count > 1 else ''}",
                "exports": f"feat: Export {count} file{'s' if count > 1 else ''}",
                "other": f"chore: Update {count} file{'s' if count > 1 else ''}",
            }
            return messages.get(category, "chore: Update files")
        else:
            # Multiple categories
            total_files = sum(len(files) for files in categories.values())
            return f"feat: Update {total_files} files across {len(categories)} categories"


class AutoCommitManager:
    """
    Manages automatic commits with batching and smart message generation.
    """

    def __init__(self, git_service: GitService):
        self.git_service = git_service
        self.pending_changes: dict[str, dict[str, Any]] = {}  # project_id -> changes
        self.last_batch_time: dict[str, float] = {}  # project_id -> timestamp
        self.batch_window = 300  # 5 minutes
        self.max_batch_size = 50
        self._lock = asyncio.Lock()

    async def track_change(self, project_id: str, project_path: Path, file_path: str):
        """
        Track a file change for potential auto-commit.

        Args:
            project_id: Project identifier
            project_path: Path to project directory
            file_path: Changed file path relative to project
        """
        async with self._lock:
            current_time = time.time()

            # Initialize project tracking if needed
            if project_id not in self.pending_changes:
                self.pending_changes[project_id] = {
                    "path": project_path,
                    "files": set(),
                    "start_time": current_time,
                }
                self.last_batch_time[project_id] = current_time

            # Add file to pending changes
            self.pending_changes[project_id]["files"].add(file_path)

            # Check if we should commit
            time_elapsed = current_time - self.last_batch_time[project_id]
            file_count = len(self.pending_changes[project_id]["files"])

            # Commit if batch window expired or max size reached
            if time_elapsed >= self.batch_window or file_count >= self.max_batch_size:
                await self._commit_batch(project_id)

    async def _commit_batch(self, project_id: str):
        """Commit pending changes for a project."""
        if project_id not in self.pending_changes:
            return

        changes = self.pending_changes[project_id]
        if not changes["files"]:
            return

        try:
            # Generate commit message
            file_list = list(changes["files"])
            message = self.git_service.generate_commit_message(file_list)

            # Perform commit
            success = await self.git_service.commit_changes(
                project_path=changes["path"],
                message=f"[auto] {message}",
                files=file_list,
            )

            if success:
                logger.info(f"Auto-committed {len(file_list)} files for project {project_id}")
                # Clear pending changes
                del self.pending_changes[project_id]
                del self.last_batch_time[project_id]
            else:
                logger.error(f"Auto-commit failed for project {project_id}")

        except Exception as e:
            logger.error(f"Error during auto-commit: {e}")

    async def force_commit_all(self):
        """Force commit all pending changes across all projects."""
        async with self._lock:
            project_ids = list(self.pending_changes.keys())
            for project_id in project_ids:
                await self._commit_batch(project_id)


# Global service instance
git_service = GitService()
auto_commit_manager = AutoCommitManager(git_service)
