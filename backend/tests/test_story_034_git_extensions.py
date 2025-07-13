"""
Tests for STORY-034: Git Service Extensions
Validates auto-commit, enhanced history, rollback, and tag functionality.
"""

import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import git
import pytest

from app.services.git import GitService, AutoCommitManager
from app.services.workspace import WorkspaceService
from app.schemas.project import ProjectCreate, QualityLevel


class TestStory034GitExtensions:
    """Test STORY-034 Git Service Extensions requirements"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def git_service(self):
        """Create git service instance"""
        return GitService()

    @pytest.fixture
    def workspace_service(self, temp_workspace):
        """Create workspace service instance"""
        return WorkspaceService(temp_workspace)

    @pytest.fixture
    def sample_project(self, workspace_service):
        """Create a sample project with Git initialized"""
        with patch.object(workspace_service, "_initialize_git_with_lfs"):
            with patch.object(workspace_service, "_create_initial_commit"):
                mock_validation = MagicMock()
                mock_validation.valid = True
                mock_validation.git_initialized = True
                
                with patch.object(
                    workspace_service, "validate_project_structure", return_value=mock_validation
                ):
                    project_data = ProjectCreate(
                        name="Test Git Project", quality=QualityLevel.STANDARD
                    )
                    project_path, manifest = workspace_service.create_project(project_data)
                    
                    # Actually initialize Git for testing
                    repo = git.Repo.init(project_path)
                    repo.config_writer().set_value("user", "name", "Test User").release()
                    repo.config_writer().set_value("user", "email", "test@example.com").release()
                    
                    # Create initial commit
                    (project_path / "README.md").write_text("# Test Project")
                    repo.index.add(["README.md"])
                    repo.index.commit("Initial commit")
                    
                    return {"id": manifest.id, "path": Path(project_path), "repo": repo}

    def test_generate_commit_message(self, git_service):
        """Test AC: Smart commit message generation"""
        # Test single category
        changes = ["01_Assets/character1.png", "01_Assets/character2.jpg"]
        message = git_service.generate_commit_message(changes)
        assert message == "feat: Add 2 new assets"

        # Test renders
        changes = ["03_Renders/scene1/shot1/take_001/output.mp4"]
        message = git_service.generate_commit_message(changes)
        assert message == "feat: Generate 1 new render"

        # Test multiple categories
        changes = [
            "01_Assets/char.png",
            "03_Renders/output.mp4",
            "02_Story/script.md",
        ]
        message = git_service.generate_commit_message(changes)
        assert message == "feat: Update 3 files across 3 categories"

        # Test empty changes
        message = git_service.generate_commit_message([])
        assert message == "chore: Update files"

    async def test_enhanced_history_with_stats(self, git_service, sample_project):
        """Test AC: Enhanced history with diff statistics"""
        repo = sample_project["repo"]
        project_path = sample_project["path"]

        # Create some commits with changes
        (project_path / "file1.txt").write_text("Line 1\nLine 2\nLine 3")
        repo.index.add(["file1.txt"])
        repo.index.commit("Add file1")

        (project_path / "file1.txt").write_text("Line 1 modified\nLine 2\nLine 3\nLine 4")
        repo.index.add(["file1.txt"])
        repo.index.commit("Modify file1")

        # Get enhanced history
        history = await git_service.get_enhanced_history(project_path, limit=10)

        # Verify structure
        assert len(history) >= 2
        latest = history[0]

        assert "hash" in latest
        assert "short_hash" in latest
        assert "message" in latest
        assert "stats" in latest
        assert "files" in latest
        assert "parent_hashes" in latest

        # Verify stats
        assert "additions" in latest["stats"]
        assert "deletions" in latest["stats"]
        assert "files" in latest["stats"]

        # Verify file changes
        if latest["files"]:
            file_change = latest["files"][0]
            assert "path" in file_change
            assert "change_type" in file_change

    async def test_rollback_soft_mode(self, git_service, sample_project):
        """Test AC: Rollback with soft mode (keeps changes)"""
        repo = sample_project["repo"]
        project_path = sample_project["path"]

        # Create commits
        initial_commit = repo.head.commit.hexsha

        (project_path / "file1.txt").write_text("Content 1")
        repo.index.add(["file1.txt"])
        repo.index.commit("Add file1")

        (project_path / "file2.txt").write_text("Content 2")
        repo.index.add(["file2.txt"])
        second_commit = repo.index.commit("Add file2")

        # Rollback to initial commit (soft)
        success = await git_service.rollback(project_path, initial_commit, mode="soft")
        assert success is True

        # Verify HEAD moved but changes are staged
        assert repo.head.commit.hexsha == initial_commit
        assert len(repo.index.diff("HEAD")) > 0  # Changes are staged

    async def test_rollback_hard_mode_with_dirty_check(self, git_service, sample_project):
        """Test AC: Rollback hard mode fails with uncommitted changes"""
        repo = sample_project["repo"]
        project_path = sample_project["path"]

        initial_commit = repo.head.commit.hexsha

        # Create a commit
        (project_path / "file1.txt").write_text("Content")
        repo.index.add(["file1.txt"])
        repo.index.commit("Add file1")

        # Make uncommitted changes
        (project_path / "file2.txt").write_text("Uncommitted")

        # Try hard rollback - should fail
        success = await git_service.rollback(project_path, initial_commit, mode="hard")
        assert success is False  # Should fail due to uncommitted changes

    async def test_create_lightweight_tag(self, git_service, sample_project):
        """Test AC: Create lightweight tag"""
        project_path = sample_project["path"]

        # Create tag
        success = await git_service.create_tag(project_path, "v1.0.0")
        assert success is True

        # Verify tag exists
        repo = git.Repo(project_path)
        assert "v1.0.0" in [tag.name for tag in repo.tags]

    async def test_create_annotated_tag(self, git_service, sample_project):
        """Test AC: Create annotated tag with message"""
        project_path = sample_project["path"]

        # Create annotated tag
        success = await git_service.create_tag(
            project_path, "release-1.0", message="First release"
        )
        assert success is True

        # Verify tag exists and has message
        repo = git.Repo(project_path)
        tag = repo.tags["release-1.0"]
        assert tag.tag is not None  # Annotated tags have a tag object

    async def test_tag_already_exists(self, git_service, sample_project):
        """Test AC: Cannot create duplicate tags"""
        project_path = sample_project["path"]

        # Create tag
        await git_service.create_tag(project_path, "v1.0.0")

        # Try to create same tag again
        success = await git_service.create_tag(project_path, "v1.0.0")
        assert success is False

    def test_auto_commit_manager_initialization(self, git_service):
        """Test AC: AutoCommitManager initialization"""
        manager = AutoCommitManager(git_service)
        
        assert manager.batch_window == 300  # 5 minutes
        assert manager.max_batch_size == 50
        assert manager.pending_changes == {}
        assert manager.last_batch_time == {}

    async def test_auto_commit_tracking(self, git_service):
        """Test AC: Track changes for auto-commit"""
        manager = AutoCommitManager(git_service)
        
        project_id = "test-project"
        project_path = Path("/tmp/test-project")
        
        # Track a change
        await manager.track_change(project_id, project_path, "file1.txt")
        
        # Verify tracking
        assert project_id in manager.pending_changes
        assert "file1.txt" in manager.pending_changes[project_id]["files"]
        assert manager.pending_changes[project_id]["path"] == project_path

    async def test_auto_commit_batching(self, git_service, sample_project):
        """Test AC: Auto-commit batches changes within window"""
        manager = AutoCommitManager(git_service)
        
        project_id = sample_project["id"]
        project_path = sample_project["path"]
        
        # Track multiple changes
        await manager.track_change(project_id, project_path, "01_Assets/asset1.png")
        await manager.track_change(project_id, project_path, "01_Assets/asset2.png")
        await manager.track_change(project_id, project_path, "01_Assets/asset3.png")
        
        # Should still be pending (within batch window)
        assert len(manager.pending_changes[project_id]["files"]) == 3

    async def test_auto_commit_max_batch_size(self, git_service):
        """Test AC: Auto-commit triggers at max batch size"""
        manager = AutoCommitManager(git_service)
        
        # Mock the commit method
        with patch.object(git_service, "commit_changes", new=AsyncMock(return_value=True)):
            project_id = "test-project"
            project_path = Path("/tmp/test-project")
            
            # Track files up to max batch size
            for i in range(manager.max_batch_size):
                await manager.track_change(project_id, project_path, f"file{i}.txt")
            
            # Verify commit was called
            git_service.commit_changes.assert_called()

    async def test_auto_commit_time_window(self, git_service):
        """Test AC: Auto-commit triggers after time window"""
        manager = AutoCommitManager(git_service)
        manager.batch_window = 0.1  # Set very short for testing
        
        # Mock the commit method
        with patch.object(git_service, "commit_changes", new=AsyncMock(return_value=True)):
            project_id = "test-project"
            project_path = Path("/tmp/test-project")
            
            # Track initial change
            await manager.track_change(project_id, project_path, "file1.txt")
            
            # Wait for batch window
            await asyncio.sleep(0.2)
            
            # Track another change - should trigger commit
            await manager.track_change(project_id, project_path, "file2.txt")
            
            # Verify commit was called
            git_service.commit_changes.assert_called()

    async def test_force_commit_all(self, git_service):
        """Test AC: Force commit all pending changes"""
        manager = AutoCommitManager(git_service)
        
        # Mock the commit method
        with patch.object(git_service, "commit_changes", new=AsyncMock(return_value=True)):
            # Track changes for multiple projects
            for i in range(3):
                project_id = f"project-{i}"
                project_path = Path(f"/tmp/project-{i}")
                await manager.track_change(project_id, project_path, "file.txt")
            
            # Force commit all
            await manager.force_commit_all()
            
            # Verify all projects were committed
            assert len(manager.pending_changes) == 0
            assert git_service.commit_changes.call_count == 3

    async def test_rollback_invalid_commit(self, git_service, sample_project):
        """Test AC: Rollback fails with invalid commit hash"""
        project_path = sample_project["path"]
        
        # Try to rollback to non-existent commit
        success = await git_service.rollback(project_path, "invalid-hash")
        assert success is False

    async def test_enhanced_history_file_specific(self, git_service, sample_project):
        """Test AC: Get history for specific file"""
        repo = sample_project["repo"]
        project_path = sample_project["path"]
        
        # Create commits affecting different files
        (project_path / "file1.txt").write_text("Content 1")
        repo.index.add(["file1.txt"])
        repo.index.commit("Add file1")
        
        (project_path / "file2.txt").write_text("Content 2")
        repo.index.add(["file2.txt"])
        repo.index.commit("Add file2")
        
        (project_path / "file1.txt").write_text("Modified content 1")
        repo.index.add(["file1.txt"])
        repo.index.commit("Modify file1")
        
        # Get history for file1 only
        history = await git_service.get_enhanced_history(
            project_path, limit=10, file_path="file1.txt"
        )
        
        # Should only include commits affecting file1
        assert len(history) == 2
        assert all("file1" in commit["message"] for commit in history)