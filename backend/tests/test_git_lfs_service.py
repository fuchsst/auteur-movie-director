"""
Tests for Git LFS service
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.services.git_lfs import GitLFSService


@pytest.fixture
def git_lfs_service():
    """Create a Git LFS service instance"""
    return GitLFSService()


@pytest.fixture
def temp_project_path(tmp_path):
    """Create a temporary project directory"""
    project_path = tmp_path / "test_project"
    project_path.mkdir()
    return project_path


class TestGitLFSService:
    """Test Git LFS service functionality"""

    def test_lfs_patterns_comprehensive(self, git_lfs_service):
        """Test that LFS patterns cover all expected file types"""
        patterns = git_lfs_service.LFS_PATTERNS

        # Check key patterns are included
        assert "*.mp4" in patterns  # Video
        assert "*.png" in patterns  # Images
        assert "*.wav" in patterns  # Audio
        assert "*.blend" in patterns  # 3D
        assert "*.ckpt" in patterns  # AI models
        assert "*.zip" in patterns  # Archives

    def test_size_threshold(self, git_lfs_service):
        """Test size threshold is set correctly"""
        assert git_lfs_service.SIZE_THRESHOLD == 50 * 1024 * 1024  # 50MB

    @patch("subprocess.run")
    def test_check_lfs_installed_success(self, mock_run, git_lfs_service):
        """Test successful LFS installation check"""
        mock_run.return_value = MagicMock(stdout="git-lfs/3.2.0", returncode=0)

        result = git_lfs_service.check_lfs_installed()

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "lfs", "version"], capture_output=True, text=True, check=True
        )

    @patch("subprocess.run")
    def test_check_lfs_installed_failure(self, mock_run, git_lfs_service):
        """Test failed LFS installation check"""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "lfs", "version"])

        result = git_lfs_service.check_lfs_installed()

        assert result is False

    @patch("subprocess.run")
    def test_initialize_lfs(self, mock_run, git_lfs_service, temp_project_path):
        """Test LFS initialization in project"""
        git_lfs_service.lfs_available = True
        mock_run.return_value = MagicMock(returncode=0)

        result = git_lfs_service.initialize_lfs(temp_project_path)

        assert result is True
        assert (temp_project_path / ".gitattributes").exists()

        # Check git commands were called
        calls = mock_run.call_args_list
        assert any(
            "git" in str(call) and "lfs" in str(call) and "install" in str(call) for call in calls
        )

    def test_initialize_lfs_not_available(self, git_lfs_service, temp_project_path):
        """Test LFS initialization when LFS not available"""
        git_lfs_service.lfs_available = False

        with pytest.raises(RuntimeError, match="Git LFS is not installed"):
            git_lfs_service.initialize_lfs(temp_project_path)

    def test_create_gitattributes(self, git_lfs_service, temp_project_path):
        """Test .gitattributes file creation"""
        with patch("subprocess.run"):
            git_lfs_service.create_gitattributes(temp_project_path)

        gitattributes_path = temp_project_path / ".gitattributes"
        assert gitattributes_path.exists()

        content = gitattributes_path.read_text()
        assert "# Git LFS patterns for Auteur Movie Director" in content
        assert "*.mp4 filter=lfs diff=lfs merge=lfs -text" in content
        assert "*.png filter=lfs diff=lfs merge=lfs -text" in content
        assert "*.ckpt filter=lfs diff=lfs merge=lfs -text" in content

    def test_check_file_size(self, git_lfs_service, temp_project_path):
        """Test file size checking"""
        # Create small file
        small_file = temp_project_path / "small.txt"
        small_file.write_text("small content")
        assert git_lfs_service.check_file_size(small_file) is False

        # Create large file (mock)
        large_file = temp_project_path / "large.mp4"
        large_file.write_text("x" * (51 * 1024 * 1024))  # 51MB
        assert git_lfs_service.check_file_size(large_file) is True

    @patch("subprocess.run")
    def test_get_lfs_files(self, mock_run, git_lfs_service, temp_project_path):
        """Test getting list of LFS tracked files"""
        git_lfs_service.lfs_available = True
        mock_run.return_value = MagicMock(
            stdout="oid1234 1048576 video.mp4\noid5678 2097152 model.ckpt", returncode=0
        )

        files = git_lfs_service.get_lfs_files(temp_project_path)

        assert len(files) == 2
        assert files[0]["path"] == "video.mp4"
        assert files[0]["size"] == 1048576
        assert files[1]["path"] == "model.ckpt"
        assert files[1]["size"] == 2097152

    def test_validate_lfs_setup(self, git_lfs_service):
        """Test LFS setup validation"""
        with patch("subprocess.run") as mock_run:
            # Mock git version check
            mock_run.side_effect = [
                MagicMock(stdout="git version 2.38.0", returncode=0),
                MagicMock(stdout="git-lfs/3.2.0", returncode=0),
            ]

            validation = git_lfs_service.validate_lfs_setup()

            assert validation["git_installed"] is True
            assert validation["lfs_installed"] is True
            assert "git version" in validation["git_version"]
            assert "git-lfs" in validation["lfs_version"]
            assert len(validation["issues"]) == 0

    @patch("subprocess.run")
    def test_get_lfs_status(self, mock_run, git_lfs_service, temp_project_path):
        """Test getting comprehensive LFS status"""
        git_lfs_service.lfs_available = True

        # Create .gitattributes
        gitattributes = temp_project_path / ".gitattributes"
        gitattributes.write_text("*.mp4 filter=lfs diff=lfs merge=lfs -text\n")

        # Mock git config check
        mock_run.return_value = MagicMock(returncode=0)

        with patch.object(git_lfs_service, "get_lfs_files") as mock_get_files:
            mock_get_files.return_value = [{"oid": "abc", "size": 1000000, "path": "video.mp4"}]

            status = git_lfs_service.get_lfs_status(temp_project_path)

            assert status["enabled"] is True
            assert status["installed"] is True
            assert status["initialized"] is True
            assert "*.mp4" in status["tracked_patterns"]
            assert status["file_count"] == 1
            assert status["total_size"] == 1000000
