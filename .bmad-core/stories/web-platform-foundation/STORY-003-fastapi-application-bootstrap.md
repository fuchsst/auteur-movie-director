# Story: FastAPI Application Bootstrap

**Story ID**: STORY-003  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 3 (Small)  
**Priority**: High  

## Story Description
As a backend developer, I need to set up the foundational FastAPI application structure with Docker-first approach, Celery integration, and proper configuration so that we have a containerized backend service ready for orchestration with other platform components.

## Acceptance Criteria

### Functional Requirements
- [ ] FastAPI application starts successfully in Docker container
- [ ] CORS is configured for local development (localhost:3000)
- [ ] Health check endpoint returns 200 OK for container orchestration
- [ ] Global error handling returns consistent JSON responses
- [ ] Application configuration loads from environment variables
- [ ] Celery worker starts alongside FastAPI in same container
- [ ] Redis connection is established for message broker

### Technical Requirements
- [ ] Create modular FastAPI app structure
- [ ] Implement middleware for CORS, logging, and error handling
- [ ] Use Pydantic for configuration management
- [ ] Set up proper logging with structured output
- [ ] Include request ID tracking for debugging
- [ ] Create Dockerfile for unified FastAPI + Celery image
- [ ] Configure volume mounts for workspace directory
- [ ] Implement graceful shutdown for container stops

### Container Requirements
- [ ] Dockerfile builds successfully with all dependencies
- [ ] Container exposes port 8000 for FastAPI
- [ ] Health check configured for Docker orchestration
- [ ] Environment variables properly passed to container
- [ ] Workspace volume mounted at /workspace
- [ ] Container runs both FastAPI and Celery processes

### API Requirements
- [ ] `GET /health` - Returns application and Celery worker status
- [ ] `GET /api/v1/info` - Returns API version and metadata
- [ ] All errors return consistent JSON structure
- [ ] 404 errors have helpful messages
- [ ] 500 errors don't leak sensitive information

## Implementation Notes

### Application Structure
```python
backend/
├── Dockerfile               # Unified container for FastAPI + Celery
├── docker-entrypoint.sh     # Manages multiple processes
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app creation
│   ├── config.py            # Settings management
│   ├── celery_app.py        # Celery application setup
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── cors.py          # CORS configuration
│   │   ├── logging.py       # Request logging
│   │   └── errors.py        # Error handling
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py        # Main API router
│   │   └── health.py        # Health endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   └── exceptions.py    # Custom exceptions
│   └── workers/
│       ├── __init__.py
│       └── tasks.py         # Celery task definitions
```

### Dockerfile Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create workspace directory
RUN mkdir -p /workspace

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose FastAPI port
EXPOSE 8000

# Run both FastAPI and Celery
ENTRYPOINT ["./docker-entrypoint.sh"]
```

### Docker Entrypoint Script
```bash
#!/bin/bash
# docker-entrypoint.sh

# Start Celery worker in background
celery -A app.celery_app worker --loglevel=info &

# Start FastAPI with uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Configuration Schema
```python
# app/config.py
from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Application
    app_name: str = "Auteur Movie Director API"
    version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Workspace (mounted volume in container)
    workspace_root: Path = Path("/workspace")
    
    # Celery & Redis
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Container environment
    is_docker: bool = False
    container_name: str = "auteur-backend"
    
    class Config:
        env_file = ".env"
        env_prefix = "BACKEND_"
```

### Celery Configuration
```python
# app/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "auteur_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)
```

### Error Response Format
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Project not found",
    "details": {
      "project_id": "abc123"
    }
  },
  "request_id": "req_xyz789",
  "timestamp": "2025-01-02T10:00:00Z"
}
```

### Main Application Setup
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware import setup_middleware
from app.api import router
from app.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Include routers
    app.include_router(router.api_router, prefix="/api/v1")
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.app_name} in {'Docker' if settings.is_docker else 'local'} mode")
        logger.info(f"Workspace mounted at: {settings.workspace_root}")
        logger.info(f"Celery broker: {settings.celery_broker_url}")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application gracefully")
    
    return app

app = create_app()
```

### Health Check Implementation
```python
# app/api/health.py
from fastapi import APIRouter
from app.celery_app import celery_app
from app.config import settings
import redis
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check for container orchestration"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "version": settings.version,
        "checks": {
            "api": "ok",
            "celery": "unknown",
            "redis": "unknown",
            "workspace": "unknown"
        }
    }
    
    # Check Celery worker status
    try:
        stats = celery_app.control.inspect().stats()
        if stats:
            health_status["checks"]["celery"] = "ok"
        else:
            health_status["checks"]["celery"] = "no_workers"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["celery"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis connection
    try:
        r = redis.from_url(settings.celery_broker_url)
        r.ping()
        health_status["checks"]["redis"] = "ok"
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
```

## Dependencies
- FastAPI framework
- Pydantic for data validation
- Python-multipart for file uploads
- Uvicorn for ASGI server
- Celery for task queue
- Redis for message broker
- Docker for containerization

## Docker Compose Integration
```yaml
# docker-compose.yml snippet
services:
  backend:
    build: ./backend
    container_name: auteur-backend
    ports:
      - "8000:8000"
    environment:
      - BACKEND_IS_DOCKER=true
      - BACKEND_WORKSPACE_ROOT=/workspace
      - BACKEND_CELERY_BROKER_URL=redis://redis:6379/0
      - BACKEND_FRONTEND_URL=http://localhost:3000
    volumes:
      - ./workspace:/workspace
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: auteur-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## Testing Criteria
- [ ] Container builds and starts successfully
- [ ] Health endpoint responds with all checks passing
- [ ] CORS allows frontend requests from container
- [ ] Error responses match expected format
- [ ] Environment variables properly loaded in container
- [ ] Celery worker connects to Redis
- [ ] Workspace volume is accessible
- [ ] Graceful shutdown works properly

## Definition of Done
- [ ] Dockerfile created with FastAPI + Celery setup
- [ ] Docker entrypoint script manages both processes
- [ ] Health check endpoint monitors all services
- [ ] Container properly configured in docker-compose
- [ ] All middleware properly configured
- [ ] Error handling tested with various scenarios
- [ ] Logging outputs structured JSON
- [ ] Documentation available at /api/docs
- [ ] Container passes health checks in orchestration

## Story Links
- **Depends On**: STORY-001-development-environment-setup
- **Blocks**: STORY-004-file-management-api, STORY-005-websocket-service
- **Related PRD**: PRD-001-web-platform-foundation