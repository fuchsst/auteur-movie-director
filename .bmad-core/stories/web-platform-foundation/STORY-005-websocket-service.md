# Story: WebSocket Service

**Story ID**: STORY-005  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 5 (Medium)  
**Priority**: High  

## Story Description
As a frontend developer, I need a WebSocket connection to receive real-time updates about file changes, processing status, Celery task progress, and system events so that the UI can reflect the current state without polling. The service must support container orchestration environments and handle connection management across container restarts.

## Acceptance Criteria

### Functional Requirements
- [ ] WebSocket endpoint accepts connections at `/ws`
- [ ] Clients can subscribe to specific project updates
- [ ] File change events are broadcast to connected clients
- [ ] Celery task progress updates are streamed in real-time
- [ ] Connection heartbeat prevents timeouts
- [ ] Graceful reconnection after disconnects
- [ ] Multiple clients can connect simultaneously
- [ ] Support for Redis pub/sub event distribution
- [ ] Container-aware connection management

### Technical Requirements
- [ ] Implement WebSocket manager for connection tracking
- [ ] Use JSON for all message payloads
- [ ] Include message type and timestamp in all events
- [ ] Implement subscription-based filtering
- [ ] Add connection authentication (session-based)
- [ ] Handle backpressure for slow clients
- [ ] Redis integration for scalable event distribution
- [ ] Environment-aware WebSocket URL configuration
- [ ] Typed event schemas for all message types
- [ ] Connection state persistence across container restarts

### Message Types
- `connection.established` - Initial handshake
- `project.created` - New project created
- `project.updated` - Project metadata changed
- `project.deleted` - Project removed
- `file.uploaded` - New file added
- `file.deleted` - File removed
- `file.changed` - File content modified
- `workspace.changed` - Workspace directory updated
- `task.started` - Celery task initiated
- `task.progress` - Celery task progress update
- `task.completed` - Celery task finished
- `task.failed` - Celery task error
- `process.started` - Long operation began
- `process.progress` - Progress update
- `process.completed` - Operation finished
- `system.heartbeat` - Keep-alive ping
- `container.reconnect` - Container restart notification

## Implementation Notes

### WebSocket Manager with Redis Integration
```python
# app/services/websocket.py
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
import json
import asyncio
import redis.asyncio as redis
from datetime import datetime
import os

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.PubSub] = None
        self._redis_task = None
    
    async def initialize(self):
        """Initialize Redis connection for distributed events"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = await redis.from_url(redis_url)
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe("websocket:broadcast")
        
        # Start listening for Redis events
        self._redis_task = asyncio.create_task(self._redis_listener())
    
    async def shutdown(self):
        """Clean shutdown of Redis connections"""
        if self._redis_task:
            self._redis_task.cancel()
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def _redis_listener(self):
        """Listen for Redis pub/sub events"""
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await self._handle_redis_event(data)
    
    async def _handle_redis_event(self, event: dict):
        """Handle events from Redis (from other containers)"""
        project_id = event.get("project_id")
        await self.broadcast(event, project_id, from_redis=True)
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Store connection state in Redis for reconnection
        if self.redis_client:
            await self.redis_client.setex(
                f"ws:connection:{client_id}", 
                3600,  # 1 hour TTL
                json.dumps({"connected_at": datetime.utcnow().isoformat()})
            )
        
        await self.send_personal_message(
            {"type": "connection.established", "client_id": client_id},
            client_id
        )
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.subscriptions.pop(client_id, None)
            
            # Remove connection state from Redis
            if self.redis_client:
                asyncio.create_task(
                    self.redis_client.delete(f"ws:connection:{client_id}")
                )
    
    async def send_personal_message(self, message: dict, client_id: str):
        if websocket := self.active_connections.get(client_id):
            try:
                await websocket.send_json(message)
            except Exception as e:
                # Handle disconnected clients
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict, project_id: str = None, 
                       from_redis: bool = False):
        """Broadcast message to connected clients"""
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        # Publish to Redis for other containers (unless it came from Redis)
        if self.redis_client and not from_redis:
            await self.redis_client.publish(
                "websocket:broadcast",
                json.dumps({**message, "project_id": project_id})
            )
        
        # Send to local connections
        if project_id:
            clients = [cid for cid, subs in self.subscriptions.items() 
                      if project_id in subs]
        else:
            clients = list(self.active_connections.keys())
        
        tasks = [self.send_personal_message(message, cid) 
                for cid in clients]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, client_id: str, project_id: str):
        """Subscribe client to project updates"""
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()
        self.subscriptions[client_id].add(project_id)
    
    def unsubscribe(self, client_id: str, project_id: str):
        """Unsubscribe client from project updates"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(project_id)
```

### WebSocket Endpoint with Environment Configuration
```python
# app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect, Depends, Request
from app.services.websocket import ConnectionManager
from app.core.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    request: Request
):
    client_id = str(uuid.uuid4())
    
    # Log connection info for debugging in container environment
    logger.info(f"WebSocket connection attempt from {request.client.host}")
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            # Handle different message types
            if data["type"] == "subscribe":
                project_id = data["project_id"]
                manager.subscribe(client_id, project_id)
                await manager.send_personal_message({
                    "type": "subscription.confirmed",
                    "project_id": project_id
                }, client_id)
                
            elif data["type"] == "unsubscribe":
                project_id = data["project_id"]
                manager.unsubscribe(client_id, project_id)
                
            elif data["type"] == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    client_id
                )
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)

# Environment-aware configuration helper
def get_websocket_url():
    """Get WebSocket URL based on environment"""
    if settings.environment == "production":
        return f"wss://{settings.domain}/ws"
    elif settings.environment == "docker":
        return f"ws://{settings.backend_host}:{settings.backend_port}/ws"
    else:
        return f"ws://localhost:{settings.backend_port}/ws"
```

### Event Broadcasting with Celery Integration
```python
# app/services/events.py
from app.services.websocket import manager
from datetime import datetime
import asyncio
from typing import Optional, Dict, Any

class EventBroadcaster:
    @staticmethod
    async def project_created(project_id: str, project_data: dict):
        await manager.broadcast({
            "type": "project.created",
            "project_id": project_id,
            "data": project_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def file_uploaded(project_id: str, file_info: dict):
        await manager.broadcast({
            "type": "file.uploaded",
            "project_id": project_id,
            "file": file_info,
            "timestamp": datetime.utcnow().isoformat()
        }, project_id=project_id)
    
    @staticmethod
    async def file_changed(project_id: str, file_path: str, change_type: str):
        await manager.broadcast({
            "type": "file.changed",
            "project_id": project_id,
            "file_path": file_path,
            "change_type": change_type,  # 'modified', 'created', 'deleted'
            "timestamp": datetime.utcnow().isoformat()
        }, project_id=project_id)
    
    @staticmethod
    async def workspace_changed(workspace_id: str, change_summary: Dict[str, Any]):
        await manager.broadcast({
            "type": "workspace.changed",
            "workspace_id": workspace_id,
            "changes": change_summary,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Celery task events
    @staticmethod
    async def task_started(task_id: str, task_name: str, project_id: str, 
                          metadata: Optional[Dict] = None):
        await manager.broadcast({
            "type": "task.started",
            "task_id": task_id,
            "task_name": task_name,
            "project_id": project_id,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }, project_id=project_id)
    
    @staticmethod
    async def task_progress(task_id: str, project_id: str, 
                           current: int, total: int, 
                           message: Optional[str] = None,
                           metadata: Optional[Dict] = None):
        await manager.broadcast({
            "type": "task.progress",
            "task_id": task_id,
            "project_id": project_id,
            "progress": {
                "current": current,
                "total": total,
                "percentage": (current / total * 100) if total > 0 else 0
            },
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }, project_id=project_id)
    
    @staticmethod
    async def task_completed(task_id: str, project_id: str, 
                            result: Optional[Dict] = None):
        await manager.broadcast({
            "type": "task.completed",
            "task_id": task_id,
            "project_id": project_id,
            "result": result or {},
            "timestamp": datetime.utcnow().isoformat()
        }, project_id=project_id)
    
    @staticmethod
    async def task_failed(task_id: str, project_id: str, 
                         error: str, traceback: Optional[str] = None):
        await manager.broadcast({
            "type": "task.failed",
            "task_id": task_id,
            "project_id": project_id,
            "error": error,
            "traceback": traceback,
            "timestamp": datetime.utcnow().isoformat()
        }, project_id=project_id)
    
    @staticmethod
    async def process_progress(project_id: str, process_id: str, 
                              progress: float, message: str = None):
        await manager.broadcast({
            "type": "process.progress",
            "project_id": project_id,
            "process_id": process_id,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }, project_id=project_id)
```

### Heartbeat Implementation
```python
# app/services/heartbeat.py
async def heartbeat_task():
    """Send heartbeat to all connected clients every 30 seconds"""
    while True:
        await asyncio.sleep(30)
        await manager.broadcast({
            "type": "system.heartbeat",
            "timestamp": datetime.utcnow().isoformat()
        })

# Start heartbeat on app startup
@app.on_event("startup")
async def startup_event():
    await manager.initialize()  # Initialize Redis connections
    asyncio.create_task(heartbeat_task())

@app.on_event("shutdown")
async def shutdown_event():
    await manager.shutdown()  # Clean shutdown of Redis
```

### Celery Task Progress Integration
```python
# app/tasks/base.py
from celery import Task
from app.services.events import EventBroadcaster
import asyncio

class ProgressTask(Task):
    """Base task class with WebSocket progress updates"""
    
    def __init__(self):
        self.project_id = None
        self.task_id = None
    
    def update_progress(self, current: int, total: int, message: str = None):
        """Send progress update via WebSocket"""
        if self.project_id and self.task_id:
            # Run async broadcast in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                EventBroadcaster.task_progress(
                    self.task_id, self.project_id, 
                    current, total, message
                )
            )
            loop.close()
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        project_id = kwargs.get('project_id')
        if project_id:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                EventBroadcaster.task_failed(
                    task_id, project_id, str(exc), str(einfo)
                )
            )
            loop.close()
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        project_id = kwargs.get('project_id')
        if project_id:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                EventBroadcaster.task_completed(
                    task_id, project_id, retval
                )
            )
            loop.close()

# Example usage in a Celery task
@celery_app.task(base=ProgressTask, bind=True)
def process_video(self, project_id: str, video_path: str):
    self.project_id = project_id
    self.task_id = self.request.id
    
    # Send task started event
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        EventBroadcaster.task_started(
            self.task_id, "process_video", project_id,
            {"video_path": video_path}
        )
    )
    loop.close()
    
    # Process with progress updates
    total_frames = 100
    for i in range(total_frames):
        # Do processing...
        self.update_progress(i + 1, total_frames, f"Processing frame {i + 1}")
    
    return {"status": "completed", "frames": total_frames}
```

### Message Schema
```typescript
// Common message structure
interface WSMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

// Client to server messages
interface SubscribeMessage {
  type: 'subscribe' | 'unsubscribe';
  project_id: string;
}

interface PingMessage {
  type: 'ping';
}

// Server to client events
interface ConnectionEvent {
  type: 'connection.established' | 'subscription.confirmed';
  client_id?: string;
  project_id?: string;
  timestamp: string;
}

interface FileEvent {
  type: 'file.uploaded' | 'file.deleted' | 'file.changed';
  project_id: string;
  file?: {
    name: string;
    path: string;
    size: number;
    asset_type: string;
  };
  file_path?: string;
  change_type?: 'modified' | 'created' | 'deleted';
  timestamp: string;
}

interface WorkspaceEvent {
  type: 'workspace.changed';
  workspace_id: string;
  changes: {
    added?: string[];
    modified?: string[];
    deleted?: string[];
  };
  timestamp: string;
}

interface TaskEvent {
  type: 'task.started' | 'task.progress' | 'task.completed' | 'task.failed';
  task_id: string;
  project_id: string;
  task_name?: string;
  progress?: {
    current: number;
    total: number;
    percentage: number;
  };
  message?: string;
  metadata?: Record<string, any>;
  result?: any;
  error?: string;
  traceback?: string;
  timestamp: string;
}

interface ProcessEvent {
  type: 'process.started' | 'process.progress' | 'process.completed';
  project_id: string;
  process_id: string;
  progress?: number;
  message?: string;
  timestamp: string;
}

interface SystemEvent {
  type: 'system.heartbeat' | 'container.reconnect';
  timestamp: string;
}
```

## Dependencies
- FastAPI WebSocket support
- Redis for pub/sub event distribution
- redis.asyncio for async Redis operations
- Connection manager implementation
- Event system for triggering broadcasts
- JSON message serialization
- Celery for task management
- Docker environment configuration

## Testing Criteria
- [ ] WebSocket connects successfully
- [ ] Messages are received by subscribed clients only
- [ ] Disconnections are handled gracefully
- [ ] Heartbeat keeps connections alive
- [ ] Multiple simultaneous connections work
- [ ] Large messages don't block other clients
- [ ] Redis pub/sub distributes events across containers
- [ ] Celery task progress updates stream correctly
- [ ] Connection state persists across container restarts
- [ ] Environment-aware URL configuration works
- [ ] File change events are properly typed
- [ ] Workspace change events aggregate correctly

## Definition of Done
- [ ] WebSocket endpoint implemented and tested
- [ ] Connection manager handles multiple clients
- [ ] All event types implemented (including Celery tasks)
- [ ] Subscription filtering works correctly
- [ ] Heartbeat prevents connection timeouts
- [ ] Integration with file operations complete
- [ ] Redis pub/sub integration tested
- [ ] Container orchestration support verified
- [ ] Typed event schemas documented
- [ ] Environment configuration tested

### Container Reconnection Handling
```python
# app/services/reconnect.py
import os
from app.services.websocket import manager
from app.services.events import EventBroadcaster

async def handle_container_restart():
    """Handle WebSocket reconnections after container restart"""
    # Check if this is a container restart
    if os.getenv("CONTAINER_RESTART", "false") == "true":
        # Notify all clients to reconnect
        await manager.broadcast({
            "type": "container.reconnect",
            "message": "Server restarted, please reconnect",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Clear the restart flag
        os.environ["CONTAINER_RESTART"] = "false"

# Docker health check endpoint
@router.get("/health/websocket")
async def websocket_health():
    """Health check for WebSocket service"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "redis_connected": manager.redis_client is not None,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Environment Configuration
```python
# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # WebSocket settings
    ws_heartbeat_interval: int = 30
    ws_connection_timeout: int = 3600
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    redis_channel: str = "websocket:broadcast"
    
    # Environment detection
    environment: str = "development"
    backend_host: str = "localhost"
    backend_port: int = 8000
    domain: str = "localhost"
    
    # Container settings
    container_id: str = None
    container_restart: bool = False
    
    class Config:
        env_file = ".env"
```

## Story Links
- **Depends On**: STORY-003-fastapi-application-bootstrap
- **Blocks**: STORY-009-websocket-client
- **Related PRD**: PRD-001-web-platform-foundation