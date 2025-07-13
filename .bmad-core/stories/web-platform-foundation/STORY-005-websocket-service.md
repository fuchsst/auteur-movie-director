# Story: WebSocket Service

**Story ID**: STORY-005  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: ⚠️ Partially Completed (January 2025)  

## Story Description
As a frontend developer, I need a WebSocket connection to receive real-time updates about file changes, processing status, node state changes, task execution progress, and system events so that the UI can reflect the current state without polling. The service acts as the nervous system of the application, relaying events from the Function Runner architecture through Redis pub/sub for decoupled event publishing. The service must support container orchestration environments and handle connection management across container restarts.

## Acceptance Criteria

### Functional Requirements
- [ ] WebSocket endpoint accepts connections at `/ws/{project_id}`
- [ ] Clients automatically subscribe to project-specific events on connection
- [ ] Node state change events are broadcast to connected clients
- [ ] Task execution events with granular progress updates
- [ ] File change events are broadcast to connected clients
- [ ] Connection heartbeat prevents timeouts
- [ ] Graceful reconnection after disconnects
- [ ] Multiple clients can connect simultaneously per project
- [ ] Redis pub/sub for decoupled event publishing from Function Runners
- [ ] WebSocket manager subscribes to Redis channels for event relay
- [ ] Container-aware connection management

### Technical Requirements
- [ ] Implement WebSocket manager with project-based connection tracking
- [ ] Use JSON for all message payloads
- [ ] Include message type, timestamp, and project_id in all events
- [ ] Automatic project-based subscription on connection
- [ ] Add connection authentication (session-based)
- [ ] Handle backpressure for slow clients
- [ ] Redis pub/sub integration for event relay pattern
- [ ] Subscribe to project-specific Redis channels
- [ ] Environment-aware WebSocket URL configuration
- [ ] Typed event schemas for all message types
- [ ] Connection state persistence across container restarts
- [ ] Support for step-by-step progress with descriptions

### Message Types

#### Connection Events
- `connection.established` - Initial handshake with project context
- `connection.closed` - Clean disconnection
- `system.heartbeat` - Keep-alive ping
- `container.reconnect` - Container restart notification

#### Project Events
- `project.created` - New project created
- `project.updated` - Project metadata changed
- `project.deleted` - Project removed

#### Node State Events
- `node.state.updated` - Node state changed (idle, queued, processing, completed, failed)
- `node.progress.updated` - Node execution progress with step details
- `node.output.ready` - Node output is available
- `node.error.occurred` - Node encountered an error

#### Task Execution Events
- `task.queued` - Task added to execution queue
- `task.started` - Task execution began
- `task.progress` - Granular progress update with current step
- `task.success` - Task completed successfully
- `task.failed` - Task execution failed
- `task.cancelled` - Task was cancelled

#### Creative Workflow Events
- `agent.task.assigned` - Creative agent assigned task (e.g., Screenwriter)
- `agent.task.progress` - Agent task progress update
- `agent.task.completed` - Agent finished task
- `take.created` - New Take generated
- `take.selected` - Take marked as active

#### File Events
- `file.uploaded` - New file added
- `file.deleted` - File removed
- `file.changed` - File content modified
- `workspace.changed` - Workspace directory updated

#### Function Runner Events
- `runner.assigned` - Function runner picked up task
- `runner.heartbeat` - Function runner health check
- `runner.completed` - Function runner finished execution

#### Character Events
- `character.created` - New character asset created
- `character.updated` - Character metadata updated
- `character.baseFace.uploaded` - Base face image uploaded
- `character.variation.generated` - Character variation generated
- `character.lora.status` - LoRA training status update
- `character.usage.updated` - Character usage in shots updated

## Implementation Notes

### WebSocket Manager with Event Relay Pattern
```python
# app/services/websocket.py
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
import json
import asyncio
import redis.asyncio as redis
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}  # {project_id: {client_id: websocket}}
        self.client_projects: Dict[str, str] = {}  # {client_id: project_id}
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.PubSub] = None
        self._redis_tasks: Dict[str, asyncio.Task] = {}
        self._subscribed_channels: Set[str] = set()
    
    async def initialize(self):
        """Initialize Redis connection for event relay"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = await redis.from_url(redis_url)
        self.pubsub = self.redis_client.pubsub()
        
        # Subscribe to global broadcast channel
        await self.pubsub.subscribe("websocket:broadcast")
        self._subscribed_channels.add("websocket:broadcast")
        
        # Start global listener
        self._redis_tasks["global"] = asyncio.create_task(
            self._redis_listener("websocket:broadcast")
        )
    
    async def subscribe_to_project(self, project_id: str):
        """Subscribe to project-specific Redis channel"""
        channel = f"project:{project_id}:events"
        if channel not in self._subscribed_channels:
            await self.pubsub.subscribe(channel)
            self._subscribed_channels.add(channel)
            self._redis_tasks[project_id] = asyncio.create_task(
                self._redis_listener(channel, project_id)
            )
            logger.info(f"Subscribed to Redis channel: {channel}")
    
    async def unsubscribe_from_project(self, project_id: str):
        """Unsubscribe from project-specific Redis channel if no clients"""
        if project_id not in self.active_connections or not self.active_connections[project_id]:
            channel = f"project:{project_id}:events"
            if channel in self._subscribed_channels:
                await self.pubsub.unsubscribe(channel)
                self._subscribed_channels.remove(channel)
                if project_id in self._redis_tasks:
                    self._redis_tasks[project_id].cancel()
                    del self._redis_tasks[project_id]
                logger.info(f"Unsubscribed from Redis channel: {channel}")
    
    async def shutdown(self):
        """Clean shutdown of Redis connections"""
        for task in self._redis_tasks.values():
            task.cancel()
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def _redis_listener(self, channel: str, project_id: str = None):
        """Listen for Redis pub/sub events on specific channel"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message" and message["channel"].decode() == channel:
                    try:
                        data = json.loads(message["data"])
                        await self._handle_redis_event(data, project_id)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error handling Redis event: {e}")
        except asyncio.CancelledError:
            logger.info(f"Redis listener for {channel} cancelled")
            raise
        except Exception as e:
            logger.error(f"Redis listener error for {channel}: {e}")
    
    async def _handle_redis_event(self, event: dict, project_id: str = None):
        """Handle events from Redis (from Function Runners or other services)"""
        # Extract project_id from event if not provided
        if not project_id:
            project_id = event.get("project_id")
        
        if project_id:
            await self.broadcast_to_project(project_id, event, from_redis=True)
        else:
            # Global broadcast
            await self.broadcast_all(event, from_redis=True)
    
    async def connect(self, websocket: WebSocket, client_id: str, project_id: str):
        """Connect client to project-specific WebSocket"""
        await websocket.accept()
        
        # Initialize project connection dict if needed
        if project_id not in self.active_connections:
            self.active_connections[project_id] = {}
            await self.subscribe_to_project(project_id)
        
        # Store connection
        self.active_connections[project_id][client_id] = websocket
        self.client_projects[client_id] = project_id
        
        # Store connection state in Redis
        if self.redis_client:
            await self.redis_client.setex(
                f"ws:connection:{client_id}", 
                3600,  # 1 hour TTL
                json.dumps({
                    "connected_at": datetime.utcnow().isoformat(),
                    "project_id": project_id
                })
            )
        
        # Send connection established event
        await self.send_to_client(
            {
                "type": "connection.established",
                "client_id": client_id,
                "project_id": project_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            client_id,
            project_id
        )
    
    async def disconnect(self, client_id: str):
        """Disconnect client and clean up"""
        project_id = self.client_projects.get(client_id)
        
        if project_id and project_id in self.active_connections:
            self.active_connections[project_id].pop(client_id, None)
            
            # Clean up empty project connections
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
                await self.unsubscribe_from_project(project_id)
        
        # Remove client tracking
        self.client_projects.pop(client_id, None)
        
        # Remove connection state from Redis
        if self.redis_client:
            await self.redis_client.delete(f"ws:connection:{client_id}")
    
    async def send_to_client(self, message: dict, client_id: str, project_id: str):
        """Send message to specific client"""
        if project_id in self.active_connections:
            if websocket := self.active_connections[project_id].get(client_id):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    await self.disconnect(client_id)
    
    async def broadcast_to_project(self, project_id: str, message: dict, 
                                  from_redis: bool = False):
        """Broadcast message to all clients in a project"""
        # Add metadata if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        if "project_id" not in message:
            message["project_id"] = project_id
        
        # Publish to Redis for other services (unless it came from Redis)
        if self.redis_client and not from_redis:
            channel = f"project:{project_id}:events"
            await self.redis_client.publish(channel, json.dumps(message))
        
        # Send to local connections
        if project_id in self.active_connections:
            tasks = [
                self.send_to_client(message, client_id, project_id)
                for client_id in self.active_connections[project_id]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_all(self, message: dict, from_redis: bool = False):
        """Broadcast message to all connected clients"""
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        # Publish to Redis for other services
        if self.redis_client and not from_redis:
            await self.redis_client.publish("websocket:broadcast", json.dumps(message))
        
        # Send to all local connections
        tasks = []
        for project_id, connections in self.active_connections.items():
            for client_id in connections:
                tasks.append(self.send_to_client(message, client_id, project_id))
        
        await asyncio.gather(*tasks, return_exceptions=True)
```

### WebSocket Endpoint with Project-Specific Connections
```python
# app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect, Depends, Request, Path
from app.services.websocket import ConnectionManager
from app.core.config import settings
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
manager = ConnectionManager()

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str = Path(..., description="Project ID to connect to"),
    request: Request = None
):
    client_id = str(uuid.uuid4())
    
    # Log connection info for debugging
    client_host = request.client.host if request else "unknown"
    logger.info(f"WebSocket connection from {client_host} for project {project_id}")
    
    # Connect with automatic project subscription
    await manager.connect(websocket, client_id, project_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            # Handle different message types
            if message_type == "ping":
                await manager.send_to_client(
                    {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                        "project_id": project_id
                    },
                    client_id,
                    project_id
                )
            
            elif message_type == "node.execute":
                # Relay node execution request to Function Runner via Redis
                await manager.redis_client.publish(
                    f"project:{project_id}:commands",
                    json.dumps({
                        "type": "execute_node",
                        "node_id": data.get("node_id"),
                        "parameters": data.get("parameters", {}),
                        "client_id": client_id,
                        "project_id": project_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
            
            elif message_type == "task.cancel":
                # Relay task cancellation to Function Runner
                await manager.redis_client.publish(
                    f"project:{project_id}:commands",
                    json.dumps({
                        "type": "cancel_task",
                        "task_id": data.get("task_id"),
                        "client_id": client_id,
                        "project_id": project_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {client_id} disconnected from project {project_id}")
        await manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await manager.disconnect(client_id)

# Environment-aware configuration helper
def get_websocket_url(project_id: str) -> str:
    """Get WebSocket URL for specific project based on environment"""
    if settings.environment == "production":
        return f"wss://{settings.domain}/ws/{project_id}"
    elif settings.environment == "docker":
        return f"ws://{settings.backend_host}:{settings.backend_port}/ws/{project_id}"
    else:
        return f"ws://localhost:{settings.backend_port}/ws/{project_id}"
```

### Event Broadcasting Service
```python
# app/services/events.py
from app.services.websocket import manager
from datetime import datetime
import asyncio
from typing import Optional, Dict, Any, List
from enum import Enum

class NodeState(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class EventBroadcaster:
    """Event broadcasting service for real-time updates"""
    
    # Node State Events
    @staticmethod
    async def node_state_updated(project_id: str, node_id: str, 
                                state: NodeState, metadata: Optional[Dict] = None):
        """Broadcast node state change"""
        await manager.broadcast_to_project(project_id, {
            "type": "node.state.updated",
            "node_id": node_id,
            "state": state.value,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def node_progress_updated(project_id: str, node_id: str,
                                   progress: float, step: str,
                                   current_step: int, total_steps: int,
                                   metadata: Optional[Dict] = None):
        """Broadcast node execution progress with step details"""
        await manager.broadcast_to_project(project_id, {
            "type": "node.progress.updated",
            "node_id": node_id,
            "progress": progress,
            "step": step,
            "step_info": {
                "current": current_step,
                "total": total_steps,
                "description": step
            },
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def node_output_ready(project_id: str, node_id: str,
                               outputs: Dict[str, Any], 
                               execution_time: float):
        """Broadcast that node output is ready"""
        await manager.broadcast_to_project(project_id, {
            "type": "node.output.ready",
            "node_id": node_id,
            "outputs": outputs,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def node_error_occurred(project_id: str, node_id: str,
                                 error: str, traceback: Optional[str] = None):
        """Broadcast node error"""
        await manager.broadcast_to_project(project_id, {
            "type": "node.error.occurred",
            "node_id": node_id,
            "error": error,
            "traceback": traceback,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Task Execution Events
    @staticmethod
    async def task_queued(project_id: str, task_id: str, 
                         node_id: str, priority: int = 0):
        """Broadcast task queued event"""
        await manager.broadcast_to_project(project_id, {
            "type": "task.queued",
            "task_id": task_id,
            "node_id": node_id,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def task_started(project_id: str, task_id: str, 
                          node_id: str, runner_id: str):
        """Broadcast task started by Function Runner"""
        await manager.broadcast_to_project(project_id, {
            "type": "task.started",
            "task_id": task_id,
            "node_id": node_id,
            "runner_id": runner_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def task_progress(project_id: str, task_id: str, node_id: str,
                           progress: float, step_description: str,
                           current_step: int, total_steps: int,
                           metadata: Optional[Dict] = None):
        """Broadcast granular task progress with step information"""
        await manager.broadcast_to_project(project_id, {
            "type": "task.progress",
            "task_id": task_id,
            "node_id": node_id,
            "progress": {
                "percentage": progress,
                "current_step": current_step,
                "total_steps": total_steps,
                "step_description": step_description
            },
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def task_success(project_id: str, task_id: str, node_id: str,
                          result: Dict[str, Any], execution_time: float):
        """Broadcast task success"""
        await manager.broadcast_to_project(project_id, {
            "type": "task.success",
            "task_id": task_id,
            "node_id": node_id,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def task_failed(project_id: str, task_id: str, node_id: str,
                         error: str, traceback: Optional[str] = None):
        """Broadcast task failure"""
        await manager.broadcast_to_project(project_id, {
            "type": "task.failed",
            "task_id": task_id,
            "node_id": node_id,
            "error": error,
            "traceback": traceback,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def task_cancelled(project_id: str, task_id: str, node_id: str):
        """Broadcast task cancellation"""
        await manager.broadcast_to_project(project_id, {
            "type": "task.cancelled",
            "task_id": task_id,
            "node_id": node_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Function Runner Events
    @staticmethod
    async def runner_assigned(project_id: str, task_id: str, 
                            runner_id: str, runner_info: Dict[str, Any]):
        """Broadcast Function Runner assignment"""
        await manager.broadcast_to_project(project_id, {
            "type": "runner.assigned",
            "task_id": task_id,
            "runner_id": runner_id,
            "runner_info": runner_info,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def runner_heartbeat(runner_id: str, status: Dict[str, Any]):
        """Broadcast Function Runner heartbeat (global)"""
        await manager.broadcast_all({
            "type": "runner.heartbeat",
            "runner_id": runner_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def runner_completed(project_id: str, task_id: str, 
                             runner_id: str, metrics: Dict[str, Any]):
        """Broadcast Function Runner completion"""
        await manager.broadcast_to_project(project_id, {
            "type": "runner.completed",
            "task_id": task_id,
            "runner_id": runner_id,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # File Events (existing)
    @staticmethod
    async def file_uploaded(project_id: str, file_info: dict):
        await manager.broadcast_to_project(project_id, {
            "type": "file.uploaded",
            "file": file_info,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def file_changed(project_id: str, file_path: str, change_type: str):
        await manager.broadcast_to_project(project_id, {
            "type": "file.changed",
            "file_path": file_path,
            "change_type": change_type,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Project Events
    @staticmethod
    async def project_created(project_id: str, project_data: dict):
        await manager.broadcast_all({
            "type": "project.created",
            "project_id": project_id,
            "data": project_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def workspace_changed(workspace_id: str, changes: Dict[str, List[str]]):
        await manager.broadcast_all({
            "type": "workspace.changed",
            "workspace_id": workspace_id,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Creative Workflow Events
    @staticmethod
    async def agent_task_assigned(project_id: str, agent_type: str, 
                                 task_id: str, task_description: str):
        """Broadcast creative agent task assignment"""
        await manager.broadcast_to_project(project_id, {
            "type": "agent.task.assigned",
            "agent_type": agent_type,  # Producer, Screenwriter, Art Director, etc.
            "task_id": task_id,
            "task_description": task_description,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def agent_task_progress(project_id: str, agent_type: str,
                                 task_id: str, progress: float, message: str):
        """Broadcast creative agent progress"""
        await manager.broadcast_to_project(project_id, {
            "type": "agent.task.progress",
            "agent_type": agent_type,
            "task_id": task_id,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def agent_task_completed(project_id: str, agent_type: str,
                                  task_id: str, output: Dict[str, Any]):
        """Broadcast creative agent task completion"""
        await manager.broadcast_to_project(project_id, {
            "type": "agent.task.completed",
            "agent_type": agent_type,
            "task_id": task_id,
            "output": output,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Takes System Events
    @staticmethod
    async def take_created(project_id: str, node_id: str, take_info: Dict[str, Any]):
        """Broadcast new Take creation"""
        await manager.broadcast_to_project(project_id, {
            "type": "take.created",
            "node_id": node_id,
            "take_info": take_info,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def take_selected(project_id: str, node_id: str, take_id: str):
        """Broadcast Take selection as active"""
        await manager.broadcast_to_project(project_id, {
            "type": "take.selected",
            "node_id": node_id,
            "take_id": take_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Character Events
    @staticmethod
    async def character_created(project_id: str, character_data: Dict[str, Any]):
        """Broadcast character creation"""
        await manager.broadcast_to_project(project_id, {
            "type": "character.created",
            "character": character_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def character_updated(project_id: str, char_id: str, updates: Dict[str, Any]):
        """Broadcast character updates"""
        await manager.broadcast_to_project(project_id, {
            "type": "character.updated",
            "char_id": char_id,
            "updates": updates,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def character_base_face_uploaded(project_id: str, char_id: str, 
                                         image_path: str):
        """Broadcast base face upload"""
        await manager.broadcast_to_project(project_id, {
            "type": "character.baseFace.uploaded",
            "char_id": char_id,
            "image_path": image_path,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def character_variation_generated(project_id: str, char_id: str,
                                          variation_type: str, image_path: str):
        """Broadcast character variation generation"""
        await manager.broadcast_to_project(project_id, {
            "type": "character.variation.generated",
            "char_id": char_id,
            "variation_type": variation_type,
            "image_path": image_path,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def character_lora_status(project_id: str, char_id: str,
                                   status: str, progress: Optional[float] = None):
        """Broadcast LoRA training status"""
        await manager.broadcast_to_project(project_id, {
            "type": "character.lora.status",
            "char_id": char_id,
            "status": status,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @staticmethod
    async def character_usage_updated(project_id: str, char_id: str,
                                    usage: List[str]):
        """Broadcast character usage update"""
        await manager.broadcast_to_project(project_id, {
            "type": "character.usage.updated",
            "char_id": char_id,
            "usage": usage,
            "timestamp": datetime.utcnow().isoformat()
        })
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

### Function Runner Event Publishing
```python
# Example: Function Runner publishing events via Redis
import redis
import json
from datetime import datetime
import asyncio

class FunctionRunnerEventPublisher:
    """Event publisher for Function Runners to send updates via Redis"""
    
    def __init__(self, runner_id: str):
        self.runner_id = runner_id
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def publish_event(self, project_id: str, event: dict):
        """Publish event to project-specific Redis channel"""
        channel = f"project:{project_id}:events"
        event["timestamp"] = datetime.utcnow().isoformat()
        event["runner_id"] = self.runner_id
        self.redis_client.publish(channel, json.dumps(event))
    
    def node_state_update(self, project_id: str, node_id: str, state: str):
        """Publish node state update"""
        self.publish_event(project_id, {
            "type": "node.state.updated",
            "node_id": node_id,
            "state": state
        })
    
    def task_progress(self, project_id: str, task_id: str, node_id: str,
                     progress: float, step: str, current_step: int, total_steps: int):
        """Publish granular task progress"""
        self.publish_event(project_id, {
            "type": "task.progress",
            "task_id": task_id,
            "node_id": node_id,
            "progress": {
                "percentage": progress,
                "current_step": current_step,
                "total_steps": total_steps,
                "step_description": step
            }
        })
    
    def task_success(self, project_id: str, task_id: str, node_id: str,
                    result: dict, execution_time: float):
        """Publish task success"""
        self.publish_event(project_id, {
            "type": "task.success",
            "task_id": task_id,
            "node_id": node_id,
            "result": result,
            "execution_time": execution_time
        })
    
    def task_failed(self, project_id: str, task_id: str, node_id: str,
                   error: str, traceback: str = None):
        """Publish task failure"""
        self.publish_event(project_id, {
            "type": "task.failed",
            "task_id": task_id,
            "node_id": node_id,
            "error": error,
            "traceback": traceback
        })

# Example usage in a Function Runner
def execute_text_to_image(project_id: str, task_id: str, node_id: str, params: dict):
    """Example function runner task execution with event publishing"""
    publisher = FunctionRunnerEventPublisher("runner-001")
    
    try:
        # Update node state to processing
        publisher.node_state_update(project_id, node_id, "processing")
        
        # Task execution with granular progress
        steps = [
            ("Loading model", 0.2),
            ("Processing prompt", 0.4),
            ("Generating image", 0.8),
            ("Saving output", 1.0)
        ]
        
        for i, (step_desc, progress) in enumerate(steps):
            # Simulate work
            time.sleep(1)
            
            # Publish progress
            publisher.task_progress(
                project_id, task_id, node_id,
                progress * 100, step_desc, i + 1, len(steps)
            )
        
        # Task completed
        result = {"image_path": "/outputs/image.png", "seed": 12345}
        publisher.task_success(project_id, task_id, node_id, result, 4.5)
        
        # Update node state to completed
        publisher.node_state_update(project_id, node_id, "completed")
        
    except Exception as e:
        # Handle failure
        publisher.task_failed(project_id, task_id, node_id, str(e))
        publisher.node_state_update(project_id, node_id, "failed")
```

### Message Schema
```typescript
// Common message structure
interface WSMessage {
  type: string;
  timestamp: string;
  project_id?: string;
  [key: string]: any;
}

// Client to server messages
interface PingMessage {
  type: 'ping';
}

interface NodeExecuteMessage {
  type: 'node.execute';
  node_id: string;
  parameters: Record<string, any>;
}

interface TaskCancelMessage {
  type: 'task.cancel';
  task_id: string;
}

// Connection events
interface ConnectionEvent {
  type: 'connection.established' | 'connection.closed';
  client_id: string;
  project_id: string;
  timestamp: string;
}

// Node state events
interface NodeStateEvent {
  type: 'node.state.updated';
  node_id: string;
  state: 'idle' | 'queued' | 'processing' | 'completed' | 'failed';
  metadata?: Record<string, any>;
  timestamp: string;
}

interface NodeProgressEvent {
  type: 'node.progress.updated';
  node_id: string;
  progress: number;
  step: string;
  step_info: {
    current: number;
    total: number;
    description: string;
  };
  metadata?: Record<string, any>;
  timestamp: string;
}

interface NodeOutputEvent {
  type: 'node.output.ready';
  node_id: string;
  outputs: Record<string, any>;
  execution_time: number;
  timestamp: string;
}

interface NodeErrorEvent {
  type: 'node.error.occurred';
  node_id: string;
  error: string;
  traceback?: string;
  timestamp: string;
}

// Task execution events
interface TaskQueuedEvent {
  type: 'task.queued';
  task_id: string;
  node_id: string;
  priority: number;
  timestamp: string;
}

interface TaskStartedEvent {
  type: 'task.started';
  task_id: string;
  node_id: string;
  runner_id: string;
  timestamp: string;
}

interface TaskProgressEvent {
  type: 'task.progress';
  task_id: string;
  node_id: string;
  progress: {
    percentage: number;
    current_step: number;
    total_steps: number;
    step_description: string;
  };
  metadata?: Record<string, any>;
  timestamp: string;
}

interface TaskSuccessEvent {
  type: 'task.success';
  task_id: string;
  node_id: string;
  result: Record<string, any>;
  execution_time: number;
  timestamp: string;
}

interface TaskFailedEvent {
  type: 'task.failed';
  task_id: string;
  node_id: string;
  error: string;
  traceback?: string;
  timestamp: string;
}

interface TaskCancelledEvent {
  type: 'task.cancelled';
  task_id: string;
  node_id: string;
  timestamp: string;
}

// Function Runner events
interface RunnerAssignedEvent {
  type: 'runner.assigned';
  task_id: string;
  runner_id: string;
  runner_info: {
    capabilities: string[];
    resources: Record<string, any>;
  };
  timestamp: string;
}

interface RunnerHeartbeatEvent {
  type: 'runner.heartbeat';
  runner_id: string;
  status: {
    active_tasks: number;
    available_memory: number;
    cpu_usage: number;
  };
  timestamp: string;
}

interface RunnerCompletedEvent {
  type: 'runner.completed';
  task_id: string;
  runner_id: string;
  metrics: {
    execution_time: number;
    memory_used: number;
    [key: string]: any;
  };
  timestamp: string;
}

// File events
interface FileEvent {
  type: 'file.uploaded' | 'file.deleted' | 'file.changed';
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

// System events
interface SystemEvent {
  type: 'system.heartbeat' | 'container.reconnect';
  timestamp: string;
}

// Creative workflow events
interface AgentTaskAssignedEvent {
  type: 'agent.task.assigned';
  agent_type: 'Producer' | 'Screenwriter' | 'Art Director' | 'Casting Director' | 'Location Scout' | 'First AD';
  task_id: string;
  task_description: string;
  timestamp: string;
}

interface AgentTaskProgressEvent {
  type: 'agent.task.progress';
  agent_type: string;
  task_id: string;
  progress: number;
  message: string;
  timestamp: string;
}

interface AgentTaskCompletedEvent {
  type: 'agent.task.completed';
  agent_type: string;
  task_id: string;
  output: {
    asset_type?: string;
    asset_ids?: string[];
    document_path?: string;
    [key: string]: any;
  };
  timestamp: string;
}

// Takes system events
interface TakeCreatedEvent {
  type: 'take.created';
  node_id: string;
  take_info: {
    take_id: string;
    take_number: number;
    path: string;
    chapter: string;
    scene: string;
    shot: string;
    metadata: Record<string, any>;
  };
  timestamp: string;
}

interface TakeSelectedEvent {
  type: 'take.selected';
  node_id: string;
  take_id: string;
  timestamp: string;
}

// Character events
interface CharacterCreatedEvent {
  type: 'character.created';
  character: {
    assetId: string;
    name: string;
    description: string;
    triggerWord: string;
  };
  timestamp: string;
}

interface CharacterUpdatedEvent {
  type: 'character.updated';
  char_id: string;
  updates: Record<string, any>;
  timestamp: string;
}

interface CharacterBaseFaceUploadedEvent {
  type: 'character.baseFace.uploaded';
  char_id: string;
  image_path: string;
  timestamp: string;
}

interface CharacterVariationGeneratedEvent {
  type: 'character.variation.generated';
  char_id: string;
  variation_type: string;
  image_path: string;
  timestamp: string;
}

interface CharacterLoraStatusEvent {
  type: 'character.lora.status';
  char_id: string;
  status: 'untrained' | 'training' | 'completed' | 'failed';
  progress?: number;
  timestamp: string;
}

interface CharacterUsageUpdatedEvent {
  type: 'character.usage.updated';
  char_id: string;
  usage: string[];
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
- [ ] WebSocket connects successfully to project-specific endpoints
- [ ] Project-based event filtering works correctly
- [ ] Node state updates are received in real-time
- [ ] Task progress events include step descriptions
- [ ] Disconnections are handled gracefully
- [ ] Heartbeat keeps connections alive
- [ ] Multiple clients can connect to same project
- [ ] Redis pub/sub relays events from Function Runners
- [ ] Event relay pattern works across services
- [ ] Connection state persists across container restarts
- [ ] Environment-aware URL configuration works
- [ ] Granular progress updates display correctly
- [ ] Task cancellation propagates properly
- [ ] Function Runner events are received
- [ ] Project-specific Redis channels are managed efficiently
- [ ] Character creation events broadcast correctly
- [ ] Character update events include all metadata
- [ ] LoRA training status updates with progress
- [ ] Character usage tracking updates in real-time

## Definition of Done
- [ ] Project-specific WebSocket endpoints implemented
- [ ] Connection manager handles project-based connections
- [ ] All event types implemented (node state, task execution, runner status)
- [ ] Redis event relay pattern fully functional
- [ ] Automatic project subscription on connection
- [ ] Heartbeat prevents connection timeouts
- [ ] Function Runner event publishing integrated
- [ ] Granular progress reporting with steps
- [ ] Container orchestration support verified
- [ ] Typed event schemas documented
- [ ] Environment configuration tested
- [ ] Redis channel lifecycle management working
- [ ] Event broadcasting service complete
- [ ] Character event broadcasting methods implemented
- [ ] TypeScript interfaces for character events defined

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
- **Related PRD**: PRD-001-web-platform-foundation, PRD-003-function-runner-architecture

## Key Enhancements from Node Specification

This story has been enhanced to support the Function Runner architecture with:

1. **Project-Specific WebSocket Endpoints**: Connections are now established per project at `/ws/{project_id}`
2. **Comprehensive Event Protocol**: Added node state management and task execution events
3. **Redis Event Relay Pattern**: WebSocket manager subscribes to Redis channels for decoupled event publishing
4. **Granular Progress Updates**: Support for step-by-step progress with descriptions
5. **Function Runner Integration**: Events from distributed Function Runners are relayed through Redis
6. **Automatic Project Subscription**: Clients are automatically subscribed to their project's events on connection

The WebSocket service now acts as the nervous system of the application, providing real-time communication between the web platform and the Function Runner architecture.

## Implementation Summary (January 2025)

### ✅ Implemented:
- WebSocket endpoint at `/ws/{project_id}` 
- Basic connection management per project
- Redis pub/sub for progress updates
- Core message types (ping/pong, start_generation, progress, complete, error)
- JSON message format
- Project-based organization

### ❌ Missing:
- Full event broadcasting service (EventBroadcaster class)
- Heartbeat task implementation
- Multiple clients per project support (currently single client only)
- Comprehensive message types (only ~10% implemented)
- Project-specific Redis channels
- Reconnection handling
- Container-aware connection management
- Connection state persistence
- Full Function Runner event relay
- Character, takes, and creative workflow events

The basic WebSocket infrastructure is in place but needs significant expansion to support all specified event types and features. Approximately 25-30% complete.