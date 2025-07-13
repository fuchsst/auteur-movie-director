"""
Git Performance API endpoints.

Provides endpoints for performance monitoring, caching control,
and optimization operations.
"""


from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.schemas.git import GitStatus
from app.services.git_performance import GitPerformanceManager
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/git/performance", tags=["git-performance"])

# Initialize services
git_perf = GitPerformanceManager()
workspace_service = WorkspaceService()


@router.get("/metrics")
async def get_performance_metrics() -> dict:
    """
    Get current Git performance metrics.

    Returns:
        Performance metrics including cache hit rate, operation times
    """
    metrics = git_perf.get_performance_metrics()
    return metrics


@router.get("/{project_id}/status")
async def get_cached_status(project_id: str) -> GitStatus:
    """
    Get Git status with caching.

    Args:
        project_id: Project identifier

    Returns:
        Git status (cached if available)
    """
    # Verify project exists
    if not workspace_service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        status = await git_perf.get_status_cached(project_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/history")
async def get_cached_history(
    project_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    branch: str | None = None,
) -> dict:
    """
    Get commit history with pagination and caching.

    Args:
        project_id: Project identifier
        page: Page number (1-based)
        limit: Items per page
        branch: Git branch name

    Returns:
        Paginated commit history
    """
    # Verify project exists
    if not workspace_service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        commits, total = await git_perf.get_history_paginated(project_id, page, limit, branch)

        return {
            "commits": commits,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/optimize")
async def optimize_repository(project_id: str, background_tasks: BackgroundTasks) -> dict:
    """
    Trigger repository optimization.

    Runs git gc, repacks objects, and cleans reflog to improve performance.
    This is a potentially long operation and runs in background.

    Args:
        project_id: Project identifier

    Returns:
        Task information
    """
    # Verify project exists
    if not workspace_service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if Celery is available
    try:
        from app.core.celery_app import celery_app
        from app.services.git_performance import optimize_repository_task

        # Queue background task
        task = optimize_repository_task.delay(project_id)

        return {"task_id": task.id, "status": "queued", "message": "Repository optimization queued"}
    except ImportError:
        # Fallback to FastAPI background tasks
        background_tasks.add_task(git_perf.optimize_repository, project_id)

        return {"status": "started", "message": "Repository optimization started in background"}


@router.delete("/{project_id}/cache")
async def invalidate_cache(
    project_id: str, operation: str | None = Query(None, regex="^(status|history|stats|diff)$")
) -> dict:
    """
    Invalidate cache entries for a project.

    Args:
        project_id: Project identifier
        operation: Specific operation to invalidate (optional)

    Returns:
        Cache invalidation status
    """
    # Verify project exists
    if not workspace_service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    git_perf.invalidate_cache(project_id, operation)

    return {"status": "success", "message": f"Cache invalidated for project {project_id}"}


@router.post("/{project_id}/commit/background")
async def background_commit(
    project_id: str, file_paths: list[str], message: str, background_tasks: BackgroundTasks
) -> dict:
    """
    Perform Git commit in background.

    Useful for large commits that might take time.

    Args:
        project_id: Project identifier
        file_paths: Files to commit
        message: Commit message

    Returns:
        Task information
    """
    # Verify project exists
    if not workspace_service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if Celery is available
    try:
        from app.core.celery_app import celery_app
        from app.services.git_performance import background_commit

        # Queue background task
        task = background_commit.delay(project_id, file_paths, message)

        return {"task_id": task.id, "status": "queued", "message": "Commit operation queued"}
    except ImportError:
        # Fallback to FastAPI background tasks
        from app.services.git import GitService

        git_service = GitService()

        background_tasks.add_task(git_service.commit_files, project_id, file_paths, message)

        return {"status": "started", "message": "Commit operation started in background"}


@router.get("/health")
async def check_performance_health() -> dict:
    """
    Check Git performance subsystem health.

    Returns:
        Health status of performance features
    """
    health = {
        "status": "healthy",
        "cache_available": git_perf.redis_client is not None,
        "metrics": git_perf.get_performance_metrics(),
    }

    # Check if cache is working
    if git_perf.redis_client:
        try:
            git_perf.redis_client.ping()
            health["cache_status"] = "connected"
        except Exception as e:
            health["cache_status"] = f"error: {str(e)}"
            health["status"] = "degraded"
    else:
        health["cache_status"] = "disabled"

    # Check performance thresholds
    metrics = health["metrics"]
    if metrics["cache_hit_rate"] < 0.5 and metrics["total_requests"] > 100:
        health["status"] = "degraded"
        health["warnings"] = ["Low cache hit rate"]

    return health
