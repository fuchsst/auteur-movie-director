# User Story: WebSocket Client for ComfyUI

**Story ID:** STORY-002  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Backend Client  
**Story Points:** 5  
**Priority:** Critical (P0)  

---

## Story Description

**As a** filmmaker using ComfyUI for image/video generation  
**I want** a reliable WebSocket connection to ComfyUI  
**So that** I can execute workflows and receive real-time updates  

## Acceptance Criteria

### Functional Requirements
- [ ] Establishes WebSocket connection to ComfyUI server
- [ ] Maintains persistent connection during addon lifetime
- [ ] Sends workflow execution requests via WebSocket
- [ ] Receives real-time progress updates from ComfyUI
- [ ] Handles connection drops and automatic reconnection
- [ ] Queues messages during disconnection
- [ ] Supports multiple concurrent workflow executions
- [ ] Provides connection status to UI layer

### Technical Requirements
- [ ] Implements WebSocket client using `websockets` library
- [ ] Thread-safe message queue for outgoing messages
- [ ] Event-based architecture for incoming messages
- [ ] Connection state machine (disconnected/connecting/connected)
- [ ] Exponential backoff for reconnection attempts
- [ ] Message serialization/deserialization for ComfyUI protocol
- [ ] Heartbeat/ping mechanism to detect stale connections
- [ ] Proper cleanup on addon disable

### Quality Requirements
- [ ] WebSocket connection stable for >1 hour continuous use
- [ ] Reconnection succeeds within 3 attempts
- [ ] Message delivery reliability >99.9%
- [ ] No memory leaks during long sessions
- [ ] Unit tests cover all connection states
- [ ] Clear error messages for connection failures
- [ ] Performance: <50ms message round-trip
- [ ] Thread-safe operations verified

## Implementation Notes

### Technical Approach

**ComfyUI WebSocket Client:**
```python
class ComfyUIWebSocketClient:
    def __init__(self, url="ws://localhost:8188/ws"):
        self.url = url
        self.websocket = None
        self.state = ConnectionState.DISCONNECTED
        self.message_queue = asyncio.Queue()
        self.handlers = {}
        self.reconnect_delay = 1.0
        self.max_reconnect_delay = 60.0
        
    async def connect(self):
        """Establish WebSocket connection with retry logic"""
        while self.state != ConnectionState.CONNECTED:
            try:
                self.websocket = await websockets.connect(self.url)
                self.state = ConnectionState.CONNECTED
                self.reconnect_delay = 1.0
                await self._start_message_handlers()
            except Exception as e:
                await self._handle_connection_error(e)
                
    async def send_workflow(self, workflow_json):
        """Send workflow execution request"""
        message = {
            "type": "execute",
            "data": workflow_json,
            "client_id": self.client_id
        }
        await self.send_message(message)
```

**Message Protocol:**
```python
# Outgoing message types
EXECUTE_WORKFLOW = "execute"
GET_STATUS = "status"
CANCEL_JOB = "cancel"

# Incoming message types  
EXECUTION_START = "execution_start"
EXECUTION_PROGRESS = "progress"
EXECUTION_COMPLETE = "executed"
EXECUTION_ERROR = "error"
```

**Connection State Management:**
```python
class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
```

### Blender Integration
- WebSocket client runs in background thread
- Status updates via `bpy.app.timers`
- Connection status shown in UI panel
- Error notifications via `bpy.ops.wm.report`

### ComfyUI Protocol Specifics
- Client ID required for session tracking
- Binary data for image preview updates
- JSON messages for workflow control
- Progress updates include preview images

### Error Handling
- Network errors: Automatic reconnection
- Protocol errors: Log and notify user
- Server errors: Parse and display ComfyUI error messages
- Timeout errors: Configurable timeout with retry

## Testing Strategy

### Unit Tests
```python
class TestComfyUIWebSocket(unittest.TestCase):
    async def test_connection_establishment(self):
        # Mock WebSocket server
        # Verify successful connection
        
    async def test_reconnection_logic(self):
        # Simulate connection drop
        # Verify exponential backoff
        
    async def test_message_queuing(self):
        # Queue messages while disconnected
        # Verify delivery on reconnection
```

### Integration Tests
- Test with real ComfyUI instance
- Simulate network interruptions
- Test high-load scenarios
- Verify long-running stability

## Dependencies
- STORY-001: Service Discovery (to find ComfyUI endpoint)
- Python `websockets` library
- Python `asyncio` for async operations

## Related Stories
- Used by STORY-009 (Connection Pool Manager)
- Monitored by STORY-010 (Health Check Service)
- Status shown in STORY-005 (Connection Status Panel)

## Definition of Done
- [ ] WebSocket connection established successfully
- [ ] Messages sent and received correctly
- [ ] Reconnection logic works reliably
- [ ] All ComfyUI message types handled
- [ ] Unit test coverage >90%
- [ ] Integration tests with real ComfyUI
- [ ] No memory leaks verified
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] Backend Engineer
- [ ] QA Engineer