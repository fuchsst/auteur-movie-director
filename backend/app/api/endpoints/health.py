"""
Health check endpoints for container orchestration.
"""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.config import settings
from app.redis_client import redis_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check for container orchestration"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": settings.app_name,
        "version": settings.version,
        "checks": {"api": "ok", "redis": "unknown", "workspace": "unknown"},
    }

    # Check Redis connection
    try:
        if await redis_client.health_check():
            health_status["checks"]["redis"] = "ok"
        else:
            health_status["checks"]["redis"] = "not_connected"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check workspace volume
    try:
        if settings.workspace_root.exists() and settings.workspace_root.is_dir():
            health_status["checks"]["workspace"] = "ok"
        else:
            health_status["checks"]["workspace"] = "not_mounted"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["workspace"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status


@router.get("/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": "docker" if settings.is_docker else "local",
        "quality_presets": list(settings.quality_presets.keys()),
        "default_quality": settings.default_quality,
        "features": {
            "websocket": True,
            "task_dispatcher": True,
            "redis_pubsub": True,
            "crew_ai": settings.enable_crew_ai,
        },
    }
