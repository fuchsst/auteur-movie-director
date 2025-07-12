"""
Tests for Git integration service.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.git import GitService


@pytest.fixture
def git_service():
    """Create Git service instance"""
    return GitService()


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Clean up
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_check_lfs_installed(git_service):
    """Test Git LFS detection"""
    # Mock git_lfs_service at import location
    with patch("app.services.git_lfs.git_lfs_service") as mock_lfs_service:
        # Simulate successful Git LFS check
        mock_lfs_service.check_lfs_installed.return_value = True
        result = await git_service.check_lfs_installed()
        assert result is True

        # Simulate missing Git LFS
        mock_lfs_service.check_lfs_installed.return_value = False
        result = await git_service.check_lfs_installed()
        assert result is False


@pytest.mark.asyncio
async def test_initialize_repository(git_service, temp_project_dir):
    """Test repository initialization"""
    with patch("git.Repo.init") as mock_init:
        mock_repo = MagicMock()
        mock_config_writer = MagicMock()
        mock_repo.config_writer.return_value.__enter__.return_value = mock_config_writer
        mock_repo.index = MagicMock()
        mock_init.return_value = mock_repo

        # Mock git_lfs_service
        with patch("app.services.git_lfs.git_lfs_service") as mock_lfs_service:
            mock_lfs_service.lfs_available = True
            mock_lfs_service.initialize_lfs.return_value = True

            result = await git_service.initialize_repository(temp_project_dir)
            assert result is True

            # Verify Git was initialized
            mock_init.assert_called_once_with(temp_project_dir)

            # Verify author configuration
            mock_config_writer.set_value.assert_any_call("user", "name", "Auteur Movie Director")
            mock_config_writer.set_value.assert_any_call("user", "email", "auteur@localhost")

            # Verify LFS was initialized
            mock_lfs_service.initialize_lfs.assert_called_once_with(temp_project_dir)


@pytest.mark.asyncio
async def test_get_status(git_service, temp_project_dir):
    """Test repository status retrieval"""
    with patch("git.Repo") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.is_dirty.return_value = True
        mock_repo.untracked_files = ["new_file.txt"]
        mock_repo.active_branch.name = "main"
        mock_repo.index.diff.return_value = []
        mock_repo_class.return_value = mock_repo

        with patch.object(git_service, "check_lfs_installed", return_value=True):
            with patch.object(git_service, "_run_git_command") as mock_run:
                mock_run.side_effect = [
                    ("12345 file1.mp4\n67890 file2.blend", ""),  # lfs ls-files
                    ("Listing tracked patterns\n    *.mp4\n    *.blend", ""),  # lfs track
                ]

                status = await git_service.get_status(temp_project_dir)

                assert status["initialized"] is True
                assert status["branch"] == "main"
                assert status["is_dirty"] is True
                assert status["untracked_files"] == ["new_file.txt"]
                assert status["lfs_files"] == ["file1.mp4", "file2.blend"]
                assert "*.mp4" in status["lfs_patterns"]


@pytest.mark.asyncio
async def test_commit_changes(git_service, temp_project_dir):
    """Test committing changes"""
    with patch("git.Repo") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.index.diff.return_value = [MagicMock()]  # Has changes
        mock_repo.untracked_files = []
        mock_repo_class.return_value = mock_repo

        result = await git_service.commit_changes(
            temp_project_dir, "Add new feature", prefix="feat"
        )

        assert result is True
        mock_repo.git.add.assert_called_once_with(A=True)
        mock_repo.index.commit.assert_called_once_with("feat: Add new feature")


@pytest.mark.asyncio
async def test_get_history(git_service, temp_project_dir):
    """Test retrieving commit history"""
    with patch("git.Repo") as mock_repo_class:
        mock_repo = MagicMock()

        # Mock commit
        mock_commit = MagicMock()
        mock_commit.hexsha = "abcdef1234567890"
        mock_commit.message = "Initial commit"
        mock_commit.author.name = "Test Author"
        mock_commit.author.email = "test@example.com"
        mock_commit.committed_date = 1609459200  # 2021-01-01
        mock_commit.stats.files = {"file1.txt": {}, "file2.txt": {}}

        mock_repo.iter_commits.return_value = [mock_commit]
        mock_repo_class.return_value = mock_repo

        history = await git_service.get_history(temp_project_dir, limit=10)

        assert len(history) == 1
        assert history[0]["hash"] == "abcdef12"
        assert history[0]["message"] == "Initial commit"
        assert history[0]["author"] == "Test Author"
        assert history[0]["files_changed"] == 2


@pytest.mark.asyncio
async def test_track_large_file(git_service, temp_project_dir):
    """Test tracking large files with LFS"""
    # Create a mock large file
    large_file = temp_project_dir / "large_video.mp4"
    large_file.write_text("x" * 100)  # Small for testing

    with patch.object(git_service, "check_lfs_installed", return_value=True):
        with patch.object(git_service, "_run_git_command", return_value=("", "")):
            with patch("git.Repo") as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo_class.return_value = mock_repo

                # Mock file size to be over 50MB
                with patch.object(Path, "stat") as mock_stat:
                    mock_stat.return_value = MagicMock(st_size=60 * 1024 * 1024)

                    result = await git_service.track_large_file(temp_project_dir, "large_video.mp4")

                    assert result is True


@pytest.mark.asyncio
async def test_validate_repository(git_service, temp_project_dir):
    """Test repository validation"""
    # Create .git directory
    (temp_project_dir / ".git").mkdir()

    with patch("git.Repo") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.is_dirty.return_value = False
        mock_repo_class.return_value = mock_repo

        with patch.object(git_service, "check_lfs_installed", return_value=True):
            with patch.object(git_service, "_run_git_command") as mock_run:
                mock_run.return_value = ("git config filter.lfs.required = true", "")

                # Create .gitattributes
                (temp_project_dir / ".gitattributes").write_text("*.mp4 filter=lfs")

                results = await git_service.validate_repository(temp_project_dir)

                assert results["valid"] is True
                assert len(results["issues"]) == 0
                assert len(results["warnings"]) == 0
