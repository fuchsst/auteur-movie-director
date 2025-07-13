"""
Git Performance Manager for optimizing repository operations.

Provides caching, background processing, and performance monitoring
for Git operations on large media projects.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path

from git import Repo, GitCommandError
import redis
from celery import Celery

from app.config import settings
from app.services.git import GitService
from app.schemas.git import GitStatus, GitCommit

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_KEYS = {
    "status": "git:status:{project_id}",
    "history": "git:history:{project_id}:{page}:{limit}",
    "stats": "git:stats:{project_id}",
    "diff": "git:diff:{project_id}:{commit_hash}",
    "file_status": "git:file_status:{project_id}:{file_path}"
}

CACHE_TTL = {
    "status": 30,       # 30 seconds
    "history": 300,     # 5 minutes
    "stats": 3600,      # 1 hour
    "diff": 3600,       # 1 hour
    "file_status": 60   # 1 minute
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "status_check_ms": 500,
    "commit_operation_ms": 2000,
    "history_fetch_ms": 1000,
    "max_memory_mb": 500,
    "cache_hit_rate": 0.8
}


class GitPerformanceManager:
    """Manages Git performance optimizations including caching and monitoring."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the performance manager.
        
        Args:
            redis_client: Redis client for caching (optional)
        """
        self.redis_client = redis_client
        self.git_service = GitService()
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "operation_times": {}
        }
        self._init_cache()
    
    def _init_cache(self):
        """Initialize cache connection if Redis is available."""
        if not self.redis_client:
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis not available, caching disabled: {e}")
                self.redis_client = None
    
    async def get_status_cached(self, project_id: str) -> GitStatus:
        """
        Get Git status with caching.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Git status information
        """
        start_time = time.time()
        cache_key = CACHE_KEYS["status"].format(project_id=project_id)
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            self._record_metric("cache_hit", "status")
            return GitStatus(**cached_data)
        
        # Fetch fresh data
        self._record_metric("cache_miss", "status")
        status = await self._fetch_status_async(project_id)
        
        # Cache the result
        self._set_cache(cache_key, status.dict(), CACHE_TTL["status"])
        
        # Record performance
        elapsed_ms = (time.time() - start_time) * 1000
        self._record_operation_time("status_check", elapsed_ms)
        
        return status
    
    async def get_history_paginated(
        self,
        project_id: str,
        page: int = 1,
        limit: int = 50,
        branch: Optional[str] = None
    ) -> Tuple[List[GitCommit], int]:
        """
        Get commit history with pagination and caching.
        
        Args:
            project_id: Project identifier
            page: Page number (1-based)
            limit: Items per page
            branch: Git branch name
            
        Returns:
            Tuple of (commits, total_count)
        """
        start_time = time.time()
        cache_key = CACHE_KEYS["history"].format(
            project_id=project_id,
            page=page,
            limit=limit
        )
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            self._record_metric("cache_hit", "history")
            commits = [GitCommit(**c) for c in cached_data["commits"]]
            return commits, cached_data["total"]
        
        # Fetch fresh data
        self._record_metric("cache_miss", "history")
        commits, total = await self._fetch_history_async(
            project_id, page, limit, branch
        )
        
        # Cache the result
        cache_data = {
            "commits": [c.dict() for c in commits],
            "total": total
        }
        self._set_cache(cache_key, cache_data, CACHE_TTL["history"])
        
        # Record performance
        elapsed_ms = (time.time() - start_time) * 1000
        self._record_operation_time("history_fetch", elapsed_ms)
        
        return commits, total
    
    async def optimize_repository(self, project_id: str) -> Dict[str, Any]:
        """
        Run Git optimization operations.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Optimization results
        """
        project_path = self.git_service._get_project_path(project_id)
        repo = Repo(project_path)
        
        results = {
            "gc_run": False,
            "pack_optimized": False,
            "reflog_cleaned": False,
            "size_before": self._get_repo_size(project_path),
            "size_after": 0,
            "duration_ms": 0
        }
        
        start_time = time.time()
        
        try:
            # Run garbage collection
            logger.info(f"Running git gc for {project_id}")
            repo.git.gc("--aggressive", "--prune=now")
            results["gc_run"] = True
            
            # Optimize pack files
            logger.info(f"Optimizing pack files for {project_id}")
            repo.git.repack("-a", "-d", "-f", "--depth=250", "--window=250")
            results["pack_optimized"] = True
            
            # Clean reflog
            logger.info(f"Cleaning reflog for {project_id}")
            repo.git.reflog("expire", "--expire=now", "--all")
            results["reflog_cleaned"] = True
            
            # Get size after optimization
            results["size_after"] = self._get_repo_size(project_path)
            
            # Clear all caches for this project
            self._clear_project_cache(project_id)
            
        except GitCommandError as e:
            logger.error(f"Git optimization failed: {e}")
            raise
        
        results["duration_ms"] = (time.time() - start_time) * 1000
        results["size_reduction_mb"] = (
            results["size_before"] - results["size_after"]
        ) / (1024 * 1024)
        
        return results
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        total_requests = self.metrics["total_requests"]
        cache_hits = self.metrics["cache_hits"]
        
        cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0
        
        avg_times = {}
        for operation, times in self.metrics["operation_times"].items():
            if times:
                avg_times[operation] = sum(times) / len(times)
        
        return {
            "cache_hit_rate": cache_hit_rate,
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "cache_misses": self.metrics["cache_misses"],
            "average_operation_times_ms": avg_times,
            "thresholds": PERFORMANCE_THRESHOLDS,
            "cache_enabled": self.redis_client is not None
        }
    
    def invalidate_cache(self, project_id: str, operation: Optional[str] = None):
        """
        Invalidate cache entries for a project.
        
        Args:
            project_id: Project identifier
            operation: Specific operation to invalidate (optional)
        """
        if not self.redis_client:
            return
        
        if operation:
            # Invalidate specific operation
            pattern = f"git:{operation}:{project_id}*"
        else:
            # Invalidate all project caches
            pattern = f"git:*:{project_id}*"
        
        try:
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
            logger.info(f"Cache invalidated for {project_id}, pattern: {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
    
    # Private helper methods
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get data from cache."""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
        
        return None
    
    def _set_cache(self, key: str, data: Dict, ttl: int):
        """Set data in cache."""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
    
    def _clear_project_cache(self, project_id: str):
        """Clear all cache entries for a project."""
        self.invalidate_cache(project_id)
    
    async def _fetch_status_async(self, project_id: str) -> GitStatus:
        """Fetch Git status asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.git_service.get_status,
            project_id
        )
    
    async def _fetch_history_async(
        self,
        project_id: str,
        page: int,
        limit: int,
        branch: Optional[str]
    ) -> Tuple[List[GitCommit], int]:
        """Fetch Git history asynchronously."""
        loop = asyncio.get_event_loop()
        
        # Get total count
        project_path = self.git_service._get_project_path(project_id)
        repo = Repo(project_path)
        total = len(list(repo.iter_commits(branch or 'HEAD')))
        
        # Get paginated commits
        skip = (page - 1) * limit
        commits = await loop.run_in_executor(
            None,
            self._get_commits_sync,
            project_id,
            branch,
            skip,
            limit
        )
        
        return commits, total
    
    def _get_commits_sync(
        self,
        project_id: str,
        branch: Optional[str],
        skip: int,
        limit: int
    ) -> List[GitCommit]:
        """Get commits synchronously for executor."""
        project_path = self.git_service._get_project_path(project_id)
        repo = Repo(project_path)
        
        commits = []
        for commit in repo.iter_commits(
            branch or 'HEAD',
            skip=skip,
            max_count=limit
        ):
            commits.append(self.git_service._commit_to_schema(commit))
        
        return commits
    
    def _get_repo_size(self, repo_path: Path) -> int:
        """Get repository size in bytes."""
        total_size = 0
        for path in repo_path.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        return total_size
    
    def _record_metric(self, metric_type: str, operation: str):
        """Record a metric event."""
        self.metrics["total_requests"] += 1
        
        if metric_type == "cache_hit":
            self.metrics["cache_hits"] += 1
        elif metric_type == "cache_miss":
            self.metrics["cache_misses"] += 1
    
    def _record_operation_time(self, operation: str, time_ms: float):
        """Record operation execution time."""
        if operation not in self.metrics["operation_times"]:
            self.metrics["operation_times"][operation] = []
        
        # Keep last 100 measurements
        times = self.metrics["operation_times"][operation]
        times.append(time_ms)
        if len(times) > 100:
            times.pop(0)
        
        # Check threshold
        threshold_key = f"{operation}_ms"
        if threshold_key in PERFORMANCE_THRESHOLDS:
            threshold = PERFORMANCE_THRESHOLDS[threshold_key]
            if time_ms > threshold:
                logger.warning(
                    f"Performance threshold exceeded for {operation}: "
                    f"{time_ms:.1f}ms > {threshold}ms"
                )


# Celery task definitions (if Celery is configured)
try:
    from app.core.celery_app import celery_app
    
    @celery_app.task
    def background_commit(project_id: str, file_paths: List[str], message: str):
        """
        Perform Git commit in background.
        
        Args:
            project_id: Project identifier
            file_paths: Files to commit
            message: Commit message
        """
        from app.services.git import GitService
        from app.core.websocket import manager
        
        git_service = GitService()
        
        try:
            # Perform commit
            commit_hash = git_service.commit_files(
                project_id,
                file_paths,
                message
            )
            
            # Invalidate cache
            perf_manager = GitPerformanceManager()
            perf_manager.invalidate_cache(project_id, "status")
            perf_manager.invalidate_cache(project_id, "history")
            
            # Send success notification
            asyncio.run(manager.send_message(
                f"project:{project_id}",
                {
                    "type": "git_commit_complete",
                    "commit_hash": commit_hash,
                    "message": message
                }
            ))
            
        except Exception as e:
            # Send error notification
            asyncio.run(manager.send_message(
                f"project:{project_id}",
                {
                    "type": "git_commit_failed",
                    "error": str(e)
                }
            ))
    
    @celery_app.task
    def optimize_repository_task(project_id: str):
        """
        Run repository optimization in background.
        
        Args:
            project_id: Project identifier
        """
        perf_manager = GitPerformanceManager()
        
        try:
            results = asyncio.run(
                perf_manager.optimize_repository(project_id)
            )
            
            logger.info(
                f"Repository optimization complete for {project_id}: "
                f"Size reduced by {results['size_reduction_mb']:.1f} MB"
            )
            
        except Exception as e:
            logger.error(f"Repository optimization failed: {e}")
            
except ImportError:
    logger.info("Celery not configured, background tasks disabled")