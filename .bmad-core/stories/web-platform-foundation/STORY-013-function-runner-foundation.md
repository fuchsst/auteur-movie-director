# Story: Function Runner Foundation

**Story ID**: STORY-013  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Infrastructure  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: ⚠️ Partially Completed (January 2025)  

## Story Description
As a developer, I need to establish the Function Runner foundation that enables the Celery worker to act as an orchestrator for containerized AI model execution, implementing task dispatching with quality-based pipeline routing, WebSocket task execution protocol, and Redis pub/sub for real-time progress events, without implementing actual AI models.

## Acceptance Criteria

### Task Dispatcher Service
- [ ] Task dispatcher maps quality settings to pipeline configurations
- [ ] Quality mappings defined for low/standard/high/premium tiers
- [ ] Pipeline configurations include VRAM targets and optimization flags
- [ ] Dispatcher selects appropriate pipeline based on project quality
- [ ] Pipeline metadata includes container image references (prepared for future)
- [ ] Task routing logic handles unknown quality tiers gracefully
- [ ] Configuration loaded from environment or config file

### WebSocket Task Execution Protocol
- [ ] WebSocket accepts `start_generation` events with node_id and parameters
- [ ] Task submission creates Celery task with unique task_id
- [ ] WebSocket sends immediate acknowledgment with task_id
- [ ] Protocol supports task cancellation requests
- [ ] Error events include descriptive messages and error codes
- [ ] WebSocket maintains task_id to connection mapping
- [ ] Disconnection handling preserves running tasks

### Redis Pub/Sub Integration
- [ ] Celery tasks publish progress to Redis channels
- [ ] Channel naming follows pattern: `task:progress:{task_id}`
- [ ] Progress events include percentage, step description, and timestamp
- [ ] WebSocket manager subscribes to relevant task channels
- [ ] Events forwarded to connected clients in real-time
- [ ] Channel cleanup after task completion
- [ ] Support for batch progress updates

### Worker Configuration
- [ ] Celery worker configured with task routing
- [ ] Worker has access to workspace volume mount
- [ ] Docker SDK integrated for future container orchestration
- [ ] Worker environment includes model storage paths
- [ ] Task concurrency limits configured per queue
- [ ] Worker health checks include Docker daemon connectivity
- [ ] Graceful shutdown preserves task state

### Model Storage Structure
- [ ] Create `/workspace/Library/AI_Models/` directory structure
- [ ] Subdirectories for model categories (image, video, audio, language)
- [ ] Model manifest schema defined (model.json)
- [ ] Version tracking structure for model updates
- [ ] Pipeline definition schema (pipeline.json)
- [ ] Storage paths accessible from worker container
- [ ] Placeholder READMEs explain future model placement

## Implementation Notes

### Task Dispatcher Architecture
```python
# backend/app/services/dispatcher.py
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel

class QualityTier(str, Enum):
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"
    PREMIUM = "premium"

class PipelineConfig(BaseModel):
    pipeline_id: str
    container_image: str  # For future use
    target_vram: int
    optimizations: list[str]
    max_concurrent: int
    timeout_seconds: int

class TaskDispatcher:
    """Routes tasks to appropriate pipelines based on quality settings"""
    
    QUALITY_PIPELINE_MAPPING = {
        QualityTier.LOW: PipelineConfig(
            pipeline_id="auteur-flux:1.0-low-vram",
            container_image="auteur/flux-low:latest",  # Future
            target_vram=12,
            optimizations=["cpu_offloading", "sequential", "low_res"],
            max_concurrent=1,
            timeout_seconds=300
        ),
        QualityTier.STANDARD: PipelineConfig(
            pipeline_id="auteur-flux:1.0-standard",
            container_image="auteur/flux-standard:latest",  # Future
            target_vram=16,
            optimizations=["moderate_parallel", "standard_res"],
            max_concurrent=2,
            timeout_seconds=180
        ),
        QualityTier.HIGH: PipelineConfig(
            pipeline_id="auteur-flux:1.0-high-fidelity",
            container_image="auteur/flux-high:latest",  # Future
            target_vram=24,
            optimizations=["full_parallel", "high_res"],
            max_concurrent=3,
            timeout_seconds=120
        ),
        QualityTier.PREMIUM: PipelineConfig(
            pipeline_id="auteur-flux:1.0-premium",
            container_image="auteur/flux-premium:latest",  # Future
            target_vram=48,
            optimizations=["multi_gpu", "max_quality"],
            max_concurrent=4,
            timeout_seconds=90
        )
    }
    
    async def dispatch_task(
        self, 
        node_type: str,
        quality: str,
        parameters: Dict[str, Any]
    ) -> str:
        """Dispatch task to appropriate pipeline"""
        pipeline_config = self.get_pipeline_config(quality)
        
        # Prepare task payload
        task_payload = {
            "pipeline_id": pipeline_config.pipeline_id,
            "node_type": node_type,
            "parameters": parameters,
            "config": pipeline_config.dict(),
            "workspace_path": "/workspace"
        }
        
        # Submit to Celery
        from app.worker.tasks import execute_generation
        task = execute_generation.apply_async(
            args=[task_payload],
            queue=f"quality_{quality}",
            time_limit=pipeline_config.timeout_seconds
        )
        
        return task.id
    
    def get_pipeline_config(self, quality: str) -> PipelineConfig:
        """Get pipeline configuration for quality tier"""
        try:
            tier = QualityTier(quality.lower())
            return self.QUALITY_PIPELINE_MAPPING[tier]
        except (ValueError, KeyError):
            # Default to standard if unknown quality
            return self.QUALITY_PIPELINE_MAPPING[QualityTier.STANDARD]
```

### WebSocket Task Protocol
```python
# backend/app/api/ws.py
from typing import Dict, Set
import asyncio
import json
from fastapi import WebSocket
from app.services.redis import RedisService
from app.services.dispatcher import TaskDispatcher

class TaskWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.task_to_connection: Dict[str, str] = {}
        self.dispatcher = TaskDispatcher()
        self.redis_subscriptions: Dict[str, asyncio.Task] = {}
    
    async def handle_start_generation(
        self, 
        websocket: WebSocket,
        connection_id: str,
        data: dict
    ):
        """Handle start_generation event"""
        try:
            # Extract parameters
            node_id = data["nodeId"]
            node_type = data["nodeType"]
            parameters = data["parameters"]
            project_id = data["projectId"]
            
            # Get project quality
            project = await get_project(project_id)
            quality = project.quality
            
            # Dispatch task
            task_id = await self.dispatcher.dispatch_task(
                node_type=node_type,
                quality=quality,
                parameters={
                    **parameters,
                    "node_id": node_id,
                    "project_id": project_id,
                    "output_path": f"/workspace/{project.name}/outputs/renders/{node_id}"
                }
            )
            
            # Map task to connection
            self.task_to_connection[task_id] = connection_id
            
            # Subscribe to task progress
            await self.subscribe_to_task_progress(task_id, connection_id)
            
            # Send acknowledgment
            await websocket.send_json({
                "type": "task_acknowledged",
                "taskId": task_id,
                "nodeId": node_id,
                "status": "queued"
            })
            
        except Exception as e:
            await websocket.send_json({
                "type": "task_error",
                "nodeId": data.get("nodeId"),
                "error": str(e),
                "code": "DISPATCH_FAILED"
            })
    
    async def subscribe_to_task_progress(self, task_id: str, connection_id: str):
        """Subscribe to Redis channel for task progress"""
        channel = f"task:progress:{task_id}"
        
        async def progress_listener():
            redis = await RedisService.get_pubsub()
            await redis.subscribe(channel)
            
            try:
                while True:
                    message = await redis.get_message(ignore_subscribe_messages=True)
                    if message and message["type"] == "message":
                        progress_data = json.loads(message["data"])
                        await self.forward_progress_event(
                            connection_id, 
                            task_id, 
                            progress_data
                        )
                        
                        # Check if task completed
                        if progress_data.get("status") in ["completed", "failed"]:
                            break
                            
            finally:
                await redis.unsubscribe(channel)
                del self.redis_subscriptions[task_id]
        
        # Start listener task
        self.redis_subscriptions[task_id] = asyncio.create_task(progress_listener())
    
    async def forward_progress_event(
        self, 
        connection_id: str, 
        task_id: str,
        progress_data: dict
    ):
        """Forward progress event to WebSocket client"""
        websocket = self.active_connections.get(connection_id)
        if not websocket:
            return
        
        event_type = "task_progress"
        if progress_data["status"] == "completed":
            event_type = "task_success"
        elif progress_data["status"] == "failed":
            event_type = "task_failed"
        
        await websocket.send_json({
            "type": event_type,
            "taskId": task_id,
            "nodeId": progress_data.get("node_id"),
            "progress": progress_data.get("progress", 0),
            "step": progress_data.get("step", ""),
            "status": progress_data["status"],
            "result": progress_data.get("result"),
            "error": progress_data.get("error")
        })
```

### Celery Worker Tasks
```python
# backend/app/worker/tasks.py
import asyncio
import json
from celery import current_task
from app.worker.celery_app import celery_app
from app.services.redis import RedisService
import docker
from pathlib import Path

@celery_app.task(bind=True, name="execute_generation")
def execute_generation(self, task_payload: dict):
    """Execute generation task with progress reporting"""
    task_id = self.request.id
    node_id = task_payload["parameters"]["node_id"]
    pipeline_id = task_payload["pipeline_id"]
    
    # Progress reporter
    async def report_progress(progress: int, step: str, status: str = "running"):
        redis = await RedisService.get_client()
        channel = f"task:progress:{task_id}"
        
        progress_data = {
            "task_id": task_id,
            "node_id": node_id,
            "progress": progress,
            "step": step,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await redis.publish(channel, json.dumps(progress_data))
    
    try:
        # Report task started
        asyncio.run(report_progress(0, "Initializing pipeline", "running"))
        
        # Simulate pipeline stages (replace with actual container execution)
        stages = [
            (10, "Loading model configuration"),
            (20, "Preparing workspace"),
            (30, "Validating parameters"),
            (40, "Checking resource availability"),
            (50, "Initializing model"),
            (70, "Processing generation"),
            (90, "Saving outputs"),
            (95, "Cleaning up resources")
        ]
        
        for progress, step in stages:
            asyncio.run(report_progress(progress, step))
            time.sleep(0.5)  # Simulate work
        
        # Simulate output creation
        output_path = Path(task_payload["parameters"]["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"Generated content for {node_id}")
        
        # Report success
        asyncio.run(report_progress(100, "Generation complete", "completed"))
        
        # Send final success event with result
        success_data = {
            "task_id": task_id,
            "node_id": node_id,
            "status": "completed",
            "result": {
                "output_path": str(output_path),
                "metadata": {
                    "pipeline_id": pipeline_id,
                    "duration": 10.5,
                    "model_version": "1.0.0"
                }
            }
        }
        
        redis = RedisService.get_sync_client()
        redis.publish(f"task:progress:{task_id}", json.dumps(success_data))
        
        return success_data
        
    except Exception as e:
        # Report failure
        error_data = {
            "task_id": task_id,
            "node_id": node_id,
            "status": "failed",
            "error": str(e)
        }
        
        redis = RedisService.get_sync_client()
        redis.publish(f"task:progress:{task_id}", json.dumps(error_data))
        
        raise

# Docker SDK preparation for future container orchestration
@celery_app.task(name="prepare_container_environment")
def prepare_container_environment():
    """Verify Docker daemon connectivity and prepare for container orchestration"""
    try:
        client = docker.from_env()
        
        # Check Docker daemon
        info = client.info()
        print(f"Docker daemon connected: {info['ServerVersion']}")
        
        # List available images (for future model containers)
        images = client.images.list()
        model_images = [img for img in images if any(tag.startswith("auteur/") for tag in img.tags)]
        
        # Verify volume access
        workspace_path = Path("/workspace")
        if not workspace_path.exists():
            raise Exception("Workspace volume not mounted")
        
        # Check model storage directory
        model_storage = workspace_path / "Library" / "AI_Models"
        if not model_storage.exists():
            model_storage.mkdir(parents=True)
            
        return {
            "docker_version": info['ServerVersion'],
            "model_images": [img.tags[0] for img in model_images if img.tags],
            "workspace_mounted": True,
            "model_storage_ready": True
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "docker_available": False
        }
```

### Model Storage Directory Structure
```bash
#!/bin/bash
# scripts/init-model-storage.sh

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspace}"
MODEL_BASE="$WORKSPACE_ROOT/Library/AI_Models"

# Create model category directories
mkdir -p "$MODEL_BASE"/{image,video,audio,language}/{models,pipelines,configs}

# Create placeholder files
cat > "$MODEL_BASE/README.md" << 'EOF'
# AI Model Storage

This directory contains AI models organized by category. Each model should include:
- model files (weights, configs)
- model.json manifest
- pipeline.json for execution configuration

## Directory Structure
- `image/` - Image generation models (Flux, SDXL, etc.)
- `video/` - Video generation models (WannaGAN, etc.)
- `audio/` - Audio generation models (AudioLDM, RVC, etc.)
- `language/` - Language models (LLMs for script generation)

## Model Manifest Schema
```json
{
  "id": "model-unique-id",
  "name": "Model Display Name",
  "version": "1.0.0",
  "type": "image|video|audio|language",
  "requirements": {
    "vram": 16,
    "disk_space": 5.5
  },
  "files": [
    {
      "name": "model.safetensors",
      "size": 5368709120,
      "hash": "sha256:..."
    }
  ]
}
```
EOF

# Create example pipeline configuration
cat > "$MODEL_BASE/image/pipelines/example-pipeline.json" << 'EOF'
{
  "id": "auteur-flux:1.0-standard",
  "name": "Flux Standard Pipeline",
  "model_id": "flux-1.0",
  "container_image": "auteur/flux-standard:latest",
  "execution": {
    "command": "python generate.py",
    "args": ["--model", "/models/flux", "--config", "/config/standard.json"],
    "environment": {
      "CUDA_VISIBLE_DEVICES": "0",
      "HF_HOME": "/models/cache"
    }
  },
  "resources": {
    "gpu": true,
    "vram": 16,
    "cpu": 4,
    "memory": "16Gi"
  },
  "mounts": [
    {
      "source": "/workspace",
      "target": "/workspace",
      "readonly": false
    },
    {
      "source": "/models",
      "target": "/models",
      "readonly": true
    }
  ]
}
EOF

echo "Model storage structure initialized at $MODEL_BASE"
```

### Worker Health Check
```python
# backend/app/worker/health.py
import docker
from celery import current_app
from app.services.redis import RedisService

async def check_worker_health():
    """Comprehensive worker health check"""
    health_status = {
        "worker": "unknown",
        "redis": "unknown",
        "docker": "unknown",
        "model_storage": "unknown"
    }
    
    try:
        # Check Celery worker
        stats = current_app.control.inspect().stats()
        if stats:
            health_status["worker"] = "healthy"
            
        # Check Redis connectivity
        redis = await RedisService.get_client()
        await redis.ping()
        health_status["redis"] = "connected"
        
        # Check Docker daemon
        docker_client = docker.from_env()
        docker_client.ping()
        health_status["docker"] = "available"
        
        # Check model storage
        model_path = Path("/workspace/Library/AI_Models")
        if model_path.exists():
            health_status["model_storage"] = "mounted"
            
    except Exception as e:
        print(f"Health check error: {e}")
        
    return health_status
```

### Integration Tests
```python
# tests/test_function_runner_foundation.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.services.dispatcher import TaskDispatcher, QualityTier
from app.worker.tasks import execute_generation

@pytest.mark.asyncio
async def test_quality_pipeline_mapping():
    """Test task dispatcher quality mapping"""
    dispatcher = TaskDispatcher()
    
    # Test each quality tier
    for quality in ["low", "standard", "high", "premium"]:
        config = dispatcher.get_pipeline_config(quality)
        assert config.pipeline_id.startswith("auteur-flux")
        assert config.target_vram > 0
        assert len(config.optimizations) > 0
    
    # Test unknown quality defaults to standard
    config = dispatcher.get_pipeline_config("unknown")
    assert config == dispatcher.QUALITY_PIPELINE_MAPPING[QualityTier.STANDARD]

@pytest.mark.asyncio
async def test_task_dispatch_with_celery(celery_app, celery_worker):
    """Test task dispatch creates Celery task"""
    dispatcher = TaskDispatcher()
    
    with patch('app.worker.tasks.execute_generation.apply_async') as mock_task:
        mock_task.return_value.id = "test-task-123"
        
        task_id = await dispatcher.dispatch_task(
            node_type="image_generation",
            quality="standard",
            parameters={"prompt": "test image"}
        )
        
        assert task_id == "test-task-123"
        mock_task.assert_called_once()
        args = mock_task.call_args[1]
        assert args["queue"] == "quality_standard"
        assert args["time_limit"] == 180

@pytest.mark.asyncio
async def test_websocket_task_protocol(websocket_client):
    """Test WebSocket task execution protocol"""
    async with websocket_client("/ws/test-project") as websocket:
        # Send start_generation event
        await websocket.send_json({
            "type": "start_generation",
            "nodeId": "node-123",
            "nodeType": "image_generation",
            "projectId": "test-project",
            "parameters": {
                "prompt": "test generation",
                "width": 1024,
                "height": 1024
            }
        })
        
        # Expect acknowledgment
        response = await websocket.receive_json()
        assert response["type"] == "task_acknowledged"
        assert response["nodeId"] == "node-123"
        assert "taskId" in response

@pytest.mark.asyncio
async def test_redis_progress_publishing():
    """Test progress events published to Redis"""
    from app.services.redis import RedisService
    
    redis = await RedisService.get_client()
    pubsub = redis.pubsub()
    
    # Subscribe to progress channel
    task_id = "test-task-456"
    channel = f"task:progress:{task_id}"
    await pubsub.subscribe(channel)
    
    # Execute task with progress
    with patch('time.sleep'):  # Speed up test
        result = execute_generation.apply(args=[{
            "pipeline_id": "test-pipeline",
            "parameters": {
                "node_id": "node-456",
                "output_path": "/tmp/test-output"
            }
        }])
    
    # Collect progress events
    events = []
    async for message in pubsub.listen():
        if message["type"] == "message":
            events.append(json.loads(message["data"]))
            if len(events) >= 3:  # Collect a few events
                break
    
    # Verify progress events
    assert any(e["step"] == "Initializing pipeline" for e in events)
    assert any(e["progress"] > 0 for e in events)

@pytest.mark.asyncio
async def test_model_storage_structure():
    """Test model storage directory structure"""
    workspace = Path("/workspace/Library/AI_Models")
    
    # Verify structure created
    assert workspace.exists()
    
    categories = ["image", "video", "audio", "language"]
    for category in categories:
        category_path = workspace / category
        assert category_path.exists()
        assert (category_path / "models").exists()
        assert (category_path / "pipelines").exists()
        assert (category_path / "configs").exists()
    
    # Verify README exists
    assert (workspace / "README.md").exists()

@pytest.mark.asyncio
async def test_docker_sdk_integration():
    """Test Docker SDK integration in worker"""
    result = prepare_container_environment.apply()
    
    assert result.successful()
    data = result.get()
    
    assert "docker_version" in data
    assert data["workspace_mounted"] is True
    assert data["model_storage_ready"] is True
```

## Dependencies
- Celery worker service configured (STORY-019)
- Redis service running (STORY-019)
- WebSocket implementation (STORY-005)
- Docker SDK available in worker container
- Workspace volume mounted

## Testing Criteria
- [ ] Task dispatcher routes tasks based on quality
- [ ] WebSocket protocol handles all event types
- [ ] Redis pub/sub delivers progress events
- [ ] Worker can access Docker daemon
- [ ] Model storage structure created correctly
- [ ] Error handling works at each layer
- [ ] Performance acceptable (< 100ms dispatch time)

## Definition of Done
- [ ] Task dispatcher service implemented with quality mapping
- [ ] WebSocket task execution protocol complete
- [ ] Redis pub/sub integration tested
- [ ] Worker configured for container orchestration
- [ ] Model storage directory structure created
- [ ] Integration tests passing
- [ ] Documentation includes architecture diagrams
- [ ] Performance benchmarks established

## Story Links
- **Depends On**: STORY-005 (WebSocket), STORY-019 (Celery/Redis)
- **Blocks**: PRD-003 (Function Runner containers)
- **Related PRD**: PRD-003-function-runner-architecture

## Implementation Status (January 2025)

### ✅ Completed Components (~60% Complete)

1. **Task Dispatcher Service** - Fully implemented in `backend/app/services/dispatcher.py`:
   - Quality tiers (low, standard, high, premium) with pipeline mapping
   - VRAM targets and optimization flags per tier
   - Container image references for future use
   - Pipeline configuration schema

2. **WebSocket Task Protocol** - Implemented in `backend/app/api/websocket.py`:
   - Handles `start_generation` events
   - Task acknowledgment with task IDs
   - Connection management per project
   - Error event handling

3. **Core Dispatcher Architecture** - Implemented in `backend/app/core/dispatcher.py`:
   - Abstract `TaskHandler` base class
   - Task registration and routing
   - `GenerationTaskHandler` for AI tasks (simulation only)
   - Progress tracking infrastructure

4. **Redis Integration** - Fully implemented:
   - Progress event publishing
   - Pub/sub channel management
   - WebSocket subscription to progress updates
   - Project state management

5. **Model Storage Structure** - Created at `/workspace/Library/AI_Models/`:
   - Category directories (image, video, audio, language)
   - Subdirectories for models, pipelines, configs
   - README documentation

6. **Testing** - Comprehensive test suite in `backend/tests/test_function_runner_foundation.py`

### ❌ Missing Components (~40% Incomplete)

1. **Celery Worker Infrastructure**:
   - No Celery worker implementation
   - No `backend/app/worker/` directory
   - No task queue configuration
   - No broker setup (RabbitMQ/Redis)

2. **Docker SDK Integration**:
   - No Docker client usage in worker
   - No container lifecycle management
   - No container orchestration logic
   - No volume mount verification

3. **Actual Task Execution**:
   - Current implementation only simulates execution
   - No real AI service connections
   - No actual pipeline execution
   - No resource monitoring

4. **Worker-Specific Features**:
   - No worker health checks
   - No GPU resource management
   - No concurrency limits per queue
   - No graceful shutdown handling

### Summary
The foundation is well-architected with proper abstractions, quality mapping, and WebSocket/Redis integration. However, the actual execution layer (Celery workers) and container orchestration are not implemented. The current system can route tasks and track progress but cannot execute real AI workloads.