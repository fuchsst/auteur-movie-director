# Story: WebSocket Service

**Story ID**: STORY-005  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 5 (Medium)  
**Priority**: High  

## Story Description
As a frontend developer, I need a WebSocket connection to receive real-time updates about file changes, processing status, and system events so that the UI can reflect the current state without polling.

## Acceptance Criteria

### Functional Requirements
- [ ] WebSocket endpoint accepts connections at `/ws`
- [ ] Clients can subscribe to specific project updates
- [ ] File change events are broadcast to connected clients
- [ ] Connection heartbeat prevents timeouts
- [ ] Graceful reconnection after disconnects
- [ ] Multiple clients can connect simultaneously

### Technical Requirements
- [ ] Implement WebSocket manager for connection tracking
- [ ] Use JSON for all message payloads
- [ ] Include message type and timestamp in all events
- [ ] Implement subscription-based filtering
- [ ] Add connection authentication (session-based)
- [ ] Handle backpressure for slow clients

### Message Types
- `connection.established` - Initial handshake
- `project.created` - New project created
- `project.updated` - Project metadata changed
- `project.deleted` - Project removed
- `file.uploaded` - New file added
- `file.deleted` - File removed
- `process.started` - Long operation began
- `process.progress` - Progress update
- `process.completed` - Operation finished
- `system.heartbeat` - Keep-alive ping

## Implementation Notes

### WebSocket Manager
```python
# app/services/websocket.py
from typing import Dict, List, Set
from fastapi import WebSocket
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        await self.send_personal_message(
            {"type": "connection.established", "client_id": client_id},
            client_id
        )
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.subscriptions.pop(client_id, None)
    
    async def send_personal_message(self, message: dict, client_id: str):
        if websocket := self.active_connections.get(client_id):
            await websocket.send_json(message)
    
    async def broadcast(self, message: dict, project_id: str = None):
        if project_id:
            # Send only to subscribers of this project
            clients = [cid for cid, subs in self.subscriptions.items() 
                      if project_id in subs]
        else:
            clients = list(self.active_connections.keys())
        
        # Send to all relevant clients
        tasks = [self.send_personal_message(message, cid) 
                for cid in clients]
        await asyncio.gather(*tasks, return_exceptions=True)
```

### WebSocket Endpoint
```python
# app/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect, Depends
from app.services.websocket import ConnectionManager
import uuid

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            # Handle different message types
            if data["type"] == "subscribe":
                project_id = data["project_id"]
                manager.subscribe(client_id, project_id)
                
            elif data["type"] == "unsubscribe":
                project_id = data["project_id"]
                manager.unsubscribe(client_id, project_id)
                
            elif data["type"] == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow()},
                    client_id
                )
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

### Event Broadcasting
```python
# app/services/events.py
from app.services.websocket import manager
import asyncio

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
    asyncio.create_task(heartbeat_task())
```

### Message Schema
```typescript
// Common message structure
interface WSMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

// Client to server
interface SubscribeMessage {
  type: 'subscribe' | 'unsubscribe';
  project_id: string;
}

// Server to client
interface FileEvent {
  type: 'file.uploaded' | 'file.deleted';
  project_id: string;
  file: {
    name: string;
    path: string;
    size: number;
    asset_type: string;
  };
  timestamp: string;
}
```

## Dependencies
- FastAPI WebSocket support
- Connection manager implementation
- Event system for triggering broadcasts
- JSON message serialization

## Testing Criteria
- [ ] WebSocket connects successfully
- [ ] Messages are received by subscribed clients only
- [ ] Disconnections are handled gracefully
- [ ] Heartbeat keeps connections alive
- [ ] Multiple simultaneous connections work
- [ ] Large messages don't block other clients

## Definition of Done
- [ ] WebSocket endpoint implemented and tested
- [ ] Connection manager handles multiple clients
- [ ] All event types implemented
- [ ] Subscription filtering works correctly
- [ ] Heartbeat prevents connection timeouts
- [ ] Integration with file operations complete

## Story Links
- **Depends On**: STORY-003-fastapi-application-bootstrap
- **Blocks**: STORY-009-websocket-client
- **Related PRD**: PRD-001-web-platform-foundation