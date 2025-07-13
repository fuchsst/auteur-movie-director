"""
Performance load tests for Git operations.

Tests performance with large repositories and high concurrency.
"""

import pytest
import asyncio
import time
from pathlib import Path
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from git import Repo

from app.services.git_performance import GitPerformanceManager, PERFORMANCE_THRESHOLDS
from app.services.git import GitService


@pytest.mark.performance
class TestGitPerformanceLoad:
    """Load tests for Git performance optimization."""
    
    @pytest.fixture
    def large_repo(self):
        """Create a large test repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "large-repo"
            repo = Repo.init(repo_path)
            
            # Configure Git
            repo.config_writer().set_value("user", "name", "Test User").release()
            repo.config_writer().set_value("user", "email", "test@example.com").release()
            
            # Create many commits
            for i in range(100):
                # Create multiple files per commit
                for j in range(5):
                    file_path = repo_path / f"file_{i}_{j}.txt"
                    file_path.write_text(f"Content for file {i}-{j}\n" * 100)
                    repo.index.add([str(file_path)])
                
                repo.index.commit(f"Commit {i}: Added batch of files")
            
            yield repo_path
    
    @pytest.mark.asyncio
    async def test_status_check_performance(self, large_repo):
        """Test status check performance meets threshold."""
        perf_manager = GitPerformanceManager()
        project_id = "test-project"
        
        # Mock the project path
        with patch.object(perf_manager.git_service, '_get_project_path', return_value=large_repo):
            # Warm up cache
            await perf_manager.get_status_cached(project_id)
            
            # Test cached performance
            start = time.time()
            status = await perf_manager.get_status_cached(project_id)
            elapsed_ms = (time.time() - start) * 1000
            
            assert elapsed_ms < PERFORMANCE_THRESHOLDS["status_check_ms"]
            assert status.initialized is True
    
    @pytest.mark.asyncio
    async def test_history_fetch_performance(self, large_repo):
        """Test history fetch performance with pagination."""
        perf_manager = GitPerformanceManager()
        project_id = "test-project"
        
        with patch.object(perf_manager.git_service, '_get_project_path', return_value=large_repo):
            # Test first page fetch
            start = time.time()
            commits, total = await perf_manager.get_history_paginated(
                project_id, page=1, limit=50
            )
            elapsed_ms = (time.time() - start) * 1000
            
            assert elapsed_ms < PERFORMANCE_THRESHOLDS["history_fetch_ms"]
            assert len(commits) == 50
            assert total == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, large_repo):
        """Test performance under concurrent load."""
        perf_manager = GitPerformanceManager()
        project_id = "test-project"
        
        with patch.object(perf_manager.git_service, '_get_project_path', return_value=large_repo):
            # Simulate concurrent requests
            async def concurrent_request(request_id):
                start = time.time()
                
                if request_id % 2 == 0:
                    await perf_manager.get_status_cached(project_id)
                else:
                    await perf_manager.get_history_paginated(project_id, page=1)
                
                return time.time() - start
            
            # Run 20 concurrent requests
            tasks = [concurrent_request(i) for i in range(20)]
            times = await asyncio.gather(*tasks)
            
            # Check average response time
            avg_time_ms = (sum(times) / len(times)) * 1000
            assert avg_time_ms < 1000  # Average should be under 1 second
            
            # Check cache effectiveness
            metrics = perf_manager.get_performance_metrics()
            assert metrics["cache_hit_rate"] > 0.7  # Should have good cache hits
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, large_repo):
        """Test memory usage stays within limits."""
        import psutil
        import os
        
        perf_manager = GitPerformanceManager()
        project_id = "test-project"
        process = psutil.Process(os.getpid())
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch.object(perf_manager.git_service, '_get_project_path', return_value=large_repo):
            # Load large history
            for page in range(1, 5):
                await perf_manager.get_history_paginated(
                    project_id, page=page, limit=50
                )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < PERFORMANCE_THRESHOLDS["max_memory_mb"]
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate(self, large_repo):
        """Test cache hit rate meets threshold."""
        perf_manager = GitPerformanceManager()
        project_id = "test-project"
        
        with patch.object(perf_manager.git_service, '_get_project_path', return_value=large_repo):
            # Perform many operations
            for _ in range(10):
                await perf_manager.get_status_cached(project_id)
            
            for page in range(1, 6):
                # Fetch each page twice
                await perf_manager.get_history_paginated(project_id, page=page)
                await perf_manager.get_history_paginated(project_id, page=page)
            
            metrics = perf_manager.get_performance_metrics()
            assert metrics["cache_hit_rate"] >= PERFORMANCE_THRESHOLDS["cache_hit_rate"]
    
    @pytest.mark.asyncio
    async def test_optimization_performance(self, large_repo):
        """Test repository optimization performance."""
        perf_manager = GitPerformanceManager()
        project_id = "test-project"
        
        with patch.object(perf_manager.git_service, '_get_project_path', return_value=large_repo):
            start = time.time()
            results = await perf_manager.optimize_repository(project_id)
            elapsed = time.time() - start
            
            # Optimization should complete in reasonable time
            assert elapsed < 30  # 30 seconds max
            assert results["gc_run"] is True
            assert results["size_reduction_mb"] >= 0