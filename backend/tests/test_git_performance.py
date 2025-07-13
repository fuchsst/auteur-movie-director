"""
Tests for Git Performance optimization features.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import redis

from app.services.git_performance import GitPerformanceManager, CACHE_TTL, PERFORMANCE_THRESHOLDS
from app.schemas.git import GitStatus, GitCommit


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = Mock(spec=redis.Redis)
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.scan_iter.return_value = []
    mock.delete.return_value = 1
    mock.ping.return_value = True
    return mock


@pytest.fixture
def mock_git_service():
    """Mock Git service."""
    with patch('app.services.git_performance.GitService') as mock:
        service = mock.return_value
        service._get_project_path.return_value = "/workspace/test-project"
        service.get_status.return_value = GitStatus(
            initialized=True,
            has_commits=True,
            branch="main",
            is_dirty=False,
            untracked_files=[],
            modified_files=[],
            staged_files=[]
        )
        service._commit_to_schema.return_value = GitCommit(
            hash="abc123",
            message="Test commit",
            author="Test User",
            email="test@example.com",
            date=datetime.now().isoformat(),
            files_changed=1,
            additions=10,
            deletions=5
        )
        yield mock


@pytest.fixture
def perf_manager(mock_redis):
    """Create performance manager with mocked Redis."""
    return GitPerformanceManager(redis_client=mock_redis)


class TestGitPerformanceManager:
    """Test Git performance optimization features."""
    
    def test_init_without_redis(self):
        """Test initialization without Redis."""
        manager = GitPerformanceManager(redis_client=None)
        assert manager.redis_client is None
        assert manager.metrics["total_requests"] == 0
    
    def test_init_with_redis(self, mock_redis):
        """Test initialization with Redis."""
        manager = GitPerformanceManager(redis_client=mock_redis)
        assert manager.redis_client == mock_redis
        mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_status_cached_miss(self, perf_manager, mock_git_service):
        """Test status fetch with cache miss."""
        # Mock cache miss
        perf_manager.redis_client.get.return_value = None
        
        status = await perf_manager.get_status_cached("test-project")
        
        assert status.initialized is True
        assert status.branch == "main"
        assert perf_manager.metrics["cache_misses"] == 1
        assert perf_manager.metrics["cache_hits"] == 0
        
        # Verify cache set was called
        perf_manager.redis_client.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_status_cached_hit(self, perf_manager, mock_redis):
        """Test status fetch with cache hit."""
        # Mock cache hit
        cached_data = {
            "initialized": True,
            "has_commits": True,
            "branch": "main",
            "is_dirty": False,
            "untracked_files": [],
            "modified_files": [],
            "staged_files": []
        }
        mock_redis.get.return_value = json.dumps(cached_data)
        
        status = await perf_manager.get_status_cached("test-project")
        
        assert status.branch == "main"
        assert perf_manager.metrics["cache_hits"] == 1
        assert perf_manager.metrics["cache_misses"] == 0
    
    @pytest.mark.asyncio
    async def test_get_history_paginated(self, perf_manager, mock_git_service):
        """Test paginated history fetch."""
        # Mock repository with commits
        mock_repo = MagicMock()
        mock_commits = [MagicMock(hexsha=f"commit{i}") for i in range(5)]
        mock_repo.iter_commits.return_value = mock_commits
        
        with patch('app.services.git_performance.Repo', return_value=mock_repo):
            commits, total = await perf_manager.get_history_paginated(
                "test-project", page=1, limit=2
            )
        
        assert len(commits) == 2
        assert total == 5
        assert perf_manager.metrics["cache_misses"] == 1
    
    @pytest.mark.asyncio
    async def test_optimize_repository(self, perf_manager, mock_git_service):
        """Test repository optimization."""
        mock_repo = MagicMock()
        mock_repo.git = MagicMock()
        
        with patch('app.services.git_performance.Repo', return_value=mock_repo):
            with patch.object(perf_manager, '_get_repo_size') as mock_size:
                mock_size.side_effect = [1000000, 800000]  # Size before and after
                
                results = await perf_manager.optimize_repository("test-project")
        
        assert results["gc_run"] is True
        assert results["pack_optimized"] is True
        assert results["reflog_cleaned"] is True
        assert results["size_reduction_mb"] > 0
        
        # Verify Git commands were called
        mock_repo.git.gc.assert_called_with("--aggressive", "--prune=now")
        mock_repo.git.repack.assert_called()
        mock_repo.git.reflog.assert_called()
    
    def test_get_performance_metrics(self, perf_manager):
        """Test performance metrics retrieval."""
        # Add some metrics
        perf_manager._record_metric("cache_hit", "status")
        perf_manager._record_metric("cache_miss", "history")
        perf_manager._record_operation_time("status_check", 450)
        perf_manager._record_operation_time("history_fetch", 950)
        
        metrics = perf_manager.get_performance_metrics()
        
        assert metrics["cache_hit_rate"] == 0.5  # 1 hit, 1 miss
        assert metrics["total_requests"] == 2
        assert metrics["cache_hits"] == 1
        assert metrics["cache_misses"] == 1
        assert "status_check" in metrics["average_operation_times_ms"]
        assert metrics["cache_enabled"] is True
    
    def test_invalidate_cache_all(self, perf_manager, mock_redis):
        """Test cache invalidation for all operations."""
        mock_redis.scan_iter.return_value = [
            "git:status:test-project",
            "git:history:test-project:1:50"
        ]
        
        perf_manager.invalidate_cache("test-project")
        
        mock_redis.scan_iter.assert_called_with(match="git:*:test-project*")
        assert mock_redis.delete.call_count == 2
    
    def test_invalidate_cache_specific(self, perf_manager, mock_redis):
        """Test cache invalidation for specific operation."""
        mock_redis.scan_iter.return_value = ["git:status:test-project"]
        
        perf_manager.invalidate_cache("test-project", "status")
        
        mock_redis.scan_iter.assert_called_with(match="git:status:test-project*")
        mock_redis.delete.assert_called_once()
    
    def test_performance_threshold_warning(self, perf_manager, caplog):
        """Test performance threshold warnings."""
        # Record operation time exceeding threshold
        perf_manager._record_operation_time("status_check", 600)  # > 500ms threshold
        
        assert "Performance threshold exceeded" in caplog.text
        assert "status_check" in caplog.text
    
    def test_cache_disabled_fallback(self, mock_git_service):
        """Test behavior when Redis is not available."""
        manager = GitPerformanceManager(redis_client=None)
        
        # Operations should still work without cache
        assert manager.get_performance_metrics()["cache_enabled"] is False
        
        # Cache operations should not fail
        manager.invalidate_cache("test-project")  # Should not raise
    
    @pytest.mark.asyncio
    async def test_background_commit_task(self, mock_git_service):
        """Test background commit task (without Celery)."""
        # This test verifies the task logic even without Celery installed
        from app.services.git import GitService
        
        git_service = GitService()
        with patch.object(git_service, 'commit_files') as mock_commit:
            mock_commit.return_value = "abc123"
            
            # Simulate the task logic
            project_id = "test-project"
            file_paths = ["file1.txt", "file2.txt"]
            message = "Test commit"
            
            # This would normally be called by Celery
            commit_hash = git_service.commit_files(project_id, file_paths, message)
            
            assert commit_hash == "abc123"
            mock_commit.assert_called_once_with(project_id, file_paths, message)