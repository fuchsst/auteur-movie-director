"""Main FastAPI application entry point"""

import logging
import os

from fastapi import FastAPI

from app.api import router
from app.api.websocket import websocket_router
from app.config import settings
from app.core.dispatcher import EchoTaskHandler, task_dispatcher
from app.middleware import setup_middleware
from app.redis_client import redis_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if settings.log_format != "json"
    else None,
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title=settings.app_name,
        description="Backend API for director-centric AI-powered film production",
        version=settings.version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Setup middleware
    setup_middleware(app)

    # Include routers
    app.include_router(router.api_router, prefix="/api/v1")
    app.include_router(websocket_router, prefix="/ws")

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {"message": settings.app_name, "version": settings.version, "docs": "/api/docs"}

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.app_name} v{settings.version}")
        logger.info(f"Environment: {'Docker' if settings.is_docker else 'Local'}")
        logger.info(f"Workspace: {settings.workspace_root}")

        # Ensure workspace exists
        settings.workspace_root.mkdir(parents=True, exist_ok=True)

        # Connect to Redis
        try:
            await redis_client.connect()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Continue without Redis for development

        # Register task handlers
        from app.core.dispatcher import EchoTaskHandler, GenerationTaskHandler

        task_dispatcher.register_handler("echo", EchoTaskHandler())
        task_dispatcher.register_handler("generation", GenerationTaskHandler())
        logger.info("Task dispatcher initialized with echo and generation handlers")

        # Check Git LFS installation
        from app.services.git_lfs import git_lfs_service

        lfs_validation = git_lfs_service.validate_lfs_setup()
        if lfs_validation["lfs_installed"]:
            logger.info(f"Git LFS is installed: {lfs_validation['lfs_version']}")
        else:
            logger.warning(
                "Git LFS not found - large file tracking will be disabled. "
                "Install Git LFS for optimal media file handling."
            )
            for issue in lfs_validation["issues"]:
                logger.warning(f"  - {issue}")

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application...")

        # Cancel active tasks
        await task_dispatcher.shutdown()

        # Disconnect from Redis
        await redis_client.disconnect()

        logger.info("Shutdown complete")

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_config=None,  # Use our logging config
    )
