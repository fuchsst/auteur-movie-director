# Story: FastAPI Application Bootstrap

**Story ID**: STORY-003  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 3 (Small)  
**Priority**: High  

## Story Description
As a backend developer, I need to set up the foundational FastAPI application structure with Docker-first approach, WebSocket support, task dispatcher pattern, and proper configuration so that we have a containerized backend service ready for orchestration with AI processing components and real-time communication.

## Acceptance Criteria

### Functional Requirements
- [ ] FastAPI application starts successfully in Docker container
- [ ] CORS is configured for local development (localhost:3000)
- [ ] Health check endpoint returns 200 OK for container orchestration
- [ ] Global error handling returns consistent JSON responses
- [ ] Application configuration loads from environment variables
- [ ] Redis connection is established for pub/sub and caching
- [ ] WebSocket endpoint structure supports project-specific connections
- [ ] Task dispatcher foundation ready for Function Runner integration

### Technical Requirements
- [ ] Create modular FastAPI app structure with dispatcher pattern
- [ ] Implement middleware for CORS, logging, and error handling
- [ ] Use Pydantic for configuration management and message validation
- [ ] Set up proper logging with structured output
- [ ] Include request ID tracking for debugging
- [ ] Create Dockerfile for unified FastAPI service
- [ ] Configure volume mounts for workspace directory
- [ ] Implement graceful shutdown for container stops
- [ ] Set up Redis pub/sub for progress events
- [ ] Implement project state management in Redis
- [ ] Create WebSocket message handler foundation
- [ ] Prepare quality mapping logic for task routing

### Container Requirements
- [ ] Dockerfile builds successfully with all dependencies
- [ ] Container exposes port 8000 for FastAPI
- [ ] Health check configured for Docker orchestration
- [ ] Environment variables properly passed to container
- [ ] Workspace volume mounted at /workspace
- [ ] Redis connection available for pub/sub

### API Requirements
- [ ] `GET /health` - Returns application and Redis status
- [ ] `GET /api/v1/info` - Returns API version and metadata
- [ ] `WS /ws/{project_id}` - WebSocket endpoint for project connections
- [ ] All errors return consistent JSON structure
- [ ] 404 errors have helpful messages
- [ ] 500 errors don't leak sensitive information

### WebSocket Message Requirements
- [ ] Support `start_generation` message type
- [ ] Support `progress` message type for updates
- [ ] Support `complete` message type for results
- [ ] Support `error` message type for failures
- [ ] Messages include project_id and task_id

## Implementation Notes

### Application Structure
```python
backend/
├── Dockerfile               # FastAPI container
├── docker-entrypoint.sh     # Container startup
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app creation
│   ├── config.py            # Settings management
│   ├── redis_client.py      # Redis pub/sub setup
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── cors.py          # CORS configuration
│   │   ├── logging.py       # Request logging
│   │   └── errors.py        # Error handling
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py        # Main API router
│   │   ├── health.py        # Health endpoints
│   │   └── websocket.py     # WebSocket handlers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── dispatcher.py    # Task dispatcher
│   │   ├── quality.py       # Quality mapping logic
│   │   └── messages.py      # WebSocket message types
│   ├── services/
│   │   ├── __init__.py
│   │   ├── project_state.py # Project state in Redis
│   │   └── task_queue.py    # Task queue abstraction
│   └── models/
│       ├── __init__.py
│       ├── websocket.py     # WebSocket message models
│       └── tasks.py         # Task models
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

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis is ready!"

# Start FastAPI with uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Configuration Schema
```python
# app/config.py
from pydantic import BaseSettings
from pathlib import Path
from typing import Dict

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
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    redis_progress_channel: str = "auteur:progress"
    redis_state_prefix: str = "auteur:project:"
    
    # WebSocket
    ws_heartbeat_interval: int = 30  # seconds
    ws_message_queue_size: int = 100
    
    # Quality Settings
    quality_presets: Dict[str, Dict] = {
        "draft": {"steps": 10, "resolution": "512x512"},
        "standard": {"steps": 20, "resolution": "1024x1024"},
        "high": {"steps": 30, "resolution": "1536x1536"},
        "ultra": {"steps": 50, "resolution": "2048x2048"}
    }
    default_quality: str = "standard"
    
    # Task Dispatcher
    task_timeout: int = 300  # 5 minutes
    max_concurrent_tasks: int = 3
    
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

### Redis Client Setup
```python
# app/redis_client.py
import redis.asyncio as redis
from app.config import settings
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
    async def connect(self):
        """Initialize Redis connection"""
        self.redis = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self.pubsub = self.redis.pubsub()
        logger.info("Redis client connected")
        
    async def disconnect(self):
        """Close Redis connections"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        logger.info("Redis client disconnected")
        
    async def publish_progress(self, project_id: str, task_id: str, progress: Dict[str, Any]):
        """Publish progress update to Redis channel"""
        message = {
            "project_id": project_id,
            "task_id": task_id,
            "type": "progress",
            **progress
        }
        await self.redis.publish(
            settings.redis_progress_channel,
            json.dumps(message)
        )
        
    async def get_project_state(self, project_id: str) -> Optional[Dict]:
        """Get project state from Redis"""
        key = f"{settings.redis_state_prefix}{project_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
        
    async def set_project_state(self, project_id: str, state: Dict):
        """Store project state in Redis"""
        key = f"{settings.redis_state_prefix}{project_id}"
        await self.redis.set(
            key,
            json.dumps(state),
            ex=3600  # 1 hour expiry
        )

# Global instance
redis_client = RedisClient()
```

### WebSocket Message Models
```python
# app/models/websocket.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal
from datetime import datetime
import uuid

class WebSocketMessage(BaseModel):
    """Base WebSocket message"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Literal["start_generation", "progress", "complete", "error", "ping", "pong"]
    project_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StartGenerationMessage(WebSocketMessage):
    """Request to start generation"""
    type: Literal["start_generation"] = "start_generation"
    task_type: str  # e.g., "text_to_image", "image_to_video"
    params: Dict[str, Any]
    quality: str = "standard"
    
class ProgressMessage(WebSocketMessage):
    """Progress update from backend"""
    type: Literal["progress"] = "progress"
    task_id: str
    progress: float  # 0.0 to 1.0
    message: Optional[str] = None
    preview_url: Optional[str] = None
    
class CompleteMessage(WebSocketMessage):
    """Task completion notification"""
    type: Literal["complete"] = "complete"
    task_id: str
    result: Dict[str, Any]
    duration: float  # seconds
    
class ErrorMessage(WebSocketMessage):
    """Error notification"""
    type: Literal["error"] = "error"
    task_id: Optional[str] = None
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
```

### Task Dispatcher Foundation
```python
# app/core/dispatcher.py
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import asyncio
import logging
from app.config import settings
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

class TaskHandler(ABC):
    """Abstract base for task handlers"""
    
    @abstractmethod
    async def can_handle(self, task_type: str) -> bool:
        """Check if this handler can process the task type"""
        pass
        
    @abstractmethod
    async def process(self, task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process the task and return result"""
        pass

class TaskDispatcher:
    """Routes tasks to appropriate handlers"""
    
    def __init__(self):
        self.handlers: Dict[str, TaskHandler] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
    def register_handler(self, name: str, handler: TaskHandler):
        """Register a task handler"""
        self.handlers[name] = handler
        logger.info(f"Registered handler: {name}")
        
    async def dispatch(
        self,
        project_id: str,
        task_type: str,
        params: Dict[str, Any],
        quality: str = "standard"
    ) -> str:
        """Dispatch task to appropriate handler"""
        task_id = f"{project_id}:{task_type}:{asyncio.get_event_loop().time()}"
        
        # Apply quality settings
        quality_params = settings.quality_presets.get(quality, {})
        params = {**quality_params, **params}
        
        # Find handler
        handler = None
        for name, h in self.handlers.items():
            if await h.can_handle(task_type):
                handler = h
                break
                
        if not handler:
            raise ValueError(f"No handler found for task type: {task_type}")
            
        # Create async task
        task = asyncio.create_task(
            self._run_task(task_id, project_id, handler, params)
        )
        self.active_tasks[task_id] = task
        
        return task_id
        
    async def _run_task(
        self,
        task_id: str,
        project_id: str,
        handler: TaskHandler,
        params: Dict[str, Any]
    ):
        """Run task with progress tracking"""
        try:
            # Notify start
            await redis_client.publish_progress(
                project_id, task_id,
                {"progress": 0.0, "message": "Task started"}
            )
            
            # Process task
            result = await handler.process(task_id, params)
            
            # Notify completion
            await redis_client.publish_progress(
                project_id, task_id,
                {"progress": 1.0, "message": "Task completed", "result": result}
            )
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await redis_client.publish_progress(
                project_id, task_id,
                {"error": str(e), "message": "Task failed"}
            )
        finally:
            self.active_tasks.pop(task_id, None)

# Global dispatcher instance
task_dispatcher = TaskDispatcher()
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
from app.api.websocket import websocket_router
from app.redis_client import redis_client
from app.core.dispatcher import task_dispatcher
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
    app.include_router(websocket_router, prefix="/ws")
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting {settings.app_name} in {'Docker' if settings.is_docker else 'local'} mode")
        logger.info(f"Workspace mounted at: {settings.workspace_root}")
        
        # Connect to Redis
        await redis_client.connect()
        logger.info(f"Redis connected: {settings.redis_url}")
        
        # Initialize task handlers (placeholder for future)
        # task_dispatcher.register_handler("text_to_image", TextToImageHandler())
        logger.info("Task dispatcher initialized")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application gracefully")
        await redis_client.disconnect()
    
    return app

app = create_app()
```

### Health Check Implementation
```python
# app/api/health.py
from fastapi import APIRouter
from app.redis_client import redis_client
from app.config import settings
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
            "redis": "unknown",
            "workspace": "unknown"
        }
    }
    
    # Check Redis connection
    try:
        if redis_client.redis:
            await redis_client.redis.ping()
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
```

### WebSocket Handler Implementation
```python
# app/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.models.websocket import (
    StartGenerationMessage, ProgressMessage, 
    CompleteMessage, ErrorMessage
)
from app.core.dispatcher import task_dispatcher
from app.redis_client import redis_client
from app.config import settings
import asyncio
import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)

websocket_router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections per project"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[project_id] = websocket
        logger.info(f"WebSocket connected: {project_id}")
        
    def disconnect(self, project_id: str):
        self.active_connections.pop(project_id, None)
        logger.info(f"WebSocket disconnected: {project_id}")
        
    async def send_message(self, project_id: str, message: dict):
        if project_id in self.active_connections:
            await self.active_connections[project_id].send_json(message)

manager = ConnectionManager()

@websocket_router.websocket("/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for project-specific connections"""
    await manager.connect(project_id, websocket)
    
    # Subscribe to Redis progress channel
    progress_task = asyncio.create_task(
        subscribe_to_progress(project_id)
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle different message types
            if data["type"] == "start_generation":
                msg = StartGenerationMessage(**data, project_id=project_id)
                
                # Dispatch task
                task_id = await task_dispatcher.dispatch(
                    project_id=msg.project_id,
                    task_type=msg.task_type,
                    params=msg.params,
                    quality=msg.quality
                )
                
                # Send acknowledgment
                await manager.send_message(project_id, {
                    "type": "task_started",
                    "task_id": task_id,
                    "project_id": project_id
                })
                
            elif data["type"] == "ping":
                await manager.send_message(project_id, {"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(project_id)
        progress_task.cancel()
    except Exception as e:
        logger.error(f"WebSocket error for {project_id}: {e}")
        error_msg = ErrorMessage(
            project_id=project_id,
            error_code="WEBSOCKET_ERROR",
            message=str(e)
        )
        await manager.send_message(project_id, error_msg.dict())
        manager.disconnect(project_id)
        progress_task.cancel()

async def subscribe_to_progress(project_id: str):
    """Subscribe to Redis progress updates for a project"""
    await redis_client.pubsub.subscribe(settings.redis_progress_channel)
    
    try:
        async for message in redis_client.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                
                # Filter messages for this project
                if data.get("project_id") == project_id:
                    await manager.send_message(project_id, data)
    except asyncio.CancelledError:
        await redis_client.pubsub.unsubscribe(settings.redis_progress_channel)
```

## Dependencies
- FastAPI framework with WebSocket support
- Pydantic for data validation and models
- Python-multipart for file uploads
- Uvicorn for ASGI server
- Redis for pub/sub and caching
- aioredis for async Redis operations
- Docker for containerization
- websockets for real-time communication

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
      - BACKEND_REDIS_URL=redis://redis:6379/0
      - BACKEND_FRONTEND_URL=http://localhost:3000
      - BACKEND_DEFAULT_QUALITY=standard
      - BACKEND_LOG_LEVEL=INFO
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
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

## Testing Criteria
- [ ] Container builds and starts successfully
- [ ] Health endpoint responds with all checks passing
- [ ] CORS allows frontend requests from container
- [ ] Error responses match expected format
- [ ] Environment variables properly loaded in container
- [ ] Redis connection established on startup
- [ ] WebSocket connections work at /ws/{project_id}
- [ ] Task dispatcher accepts and routes tasks
- [ ] Progress updates published to Redis
- [ ] Workspace volume is accessible
- [ ] Graceful shutdown works properly

## Definition of Done
- [ ] Dockerfile created with FastAPI setup
- [ ] Docker entrypoint script waits for Redis
- [ ] Health check endpoint monitors Redis and workspace
- [ ] Container properly configured in docker-compose
- [ ] All middleware properly configured
- [ ] WebSocket endpoint accepts project connections
- [ ] Task dispatcher foundation implemented
- [ ] Redis pub/sub integrated for progress updates
- [ ] Quality mapping logic prepared for tasks
- [ ] Error handling tested with various scenarios
- [ ] Logging outputs structured JSON
- [ ] Documentation available at /api/docs
- [ ] Container passes health checks in orchestration

## Future Integration Notes

### Function Runner Preparation
This story lays the foundation for Function Runner integration by:
- **Task Dispatcher Pattern**: Abstract base class allows registering different handlers
- **Quality Mapping**: Configuration supports quality presets for different processing levels
- **Redis Pub/Sub**: Progress tracking ready for long-running AI tasks
- **WebSocket Infrastructure**: Real-time updates for generation progress
- **Project State Management**: Redis-based state for fast access during processing

### Example Future Handler
```python
# Future implementation example (not part of this story)
class TextToImageHandler(TaskHandler):
    async def can_handle(self, task_type: str) -> bool:
        return task_type == "text_to_image"
        
    async def process(self, task_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Will integrate with Function Runner API
        # Quality settings already applied by dispatcher
        pass
```

## Story Links
- **Depends On**: STORY-001-development-environment-setup
- **Blocks**: STORY-004-file-management-api, STORY-005-websocket-service
- **Related PRD**: PRD-001-web-platform-foundation, PRD-003-function-runner-architecture