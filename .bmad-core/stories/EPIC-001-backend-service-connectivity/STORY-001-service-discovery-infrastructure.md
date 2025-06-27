# User Story: Service Discovery Infrastructure

**Story ID:** STORY-001  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Backend Infrastructure  
**Story Points:** 8  
**Priority:** Critical (P0)  

---

## Story Description

**As a** Blender user with AI backends running locally  
**I want** the addon to automatically discover all available services  
**So that** I can start creating content without manual configuration  

## Acceptance Criteria

### Functional Requirements
- [ ] Discovers ComfyUI on default port (8188) and configurable ports
- [ ] Discovers Wan2GP on default port (7860) and configurable ports  
- [ ] Discovers LiteLLM on default port (8000) and configurable ports
- [ ] Discovers RVC on default port (7865) and configurable ports
- [ ] Discovers AudioLDM on default port (7863) and configurable ports
- [ ] Falls back to manual configuration if auto-discovery fails
- [ ] Completes discovery scan within 5 seconds
- [ ] Supports parallel discovery of all services

### Technical Requirements
- [ ] Implements async service discovery pattern
- [ ] Uses thread-safe discovery mechanism
- [ ] Supports both HTTP and WebSocket protocol detection
- [ ] Implements timeout handling for unresponsive ports
- [ ] Creates service registry data structure
- [ ] Handles network errors gracefully
- [ ] Supports IPv4 and IPv6 addresses
- [ ] Implements service type detection from response

### Quality Requirements
- [ ] Unit tests cover all discovery scenarios
- [ ] Mock services for testing without real backends
- [ ] Discovery completes without blocking UI
- [ ] Memory usage remains constant during discovery
- [ ] Clear logging of discovery process
- [ ] Performance profiling shows <100ms per service
- [ ] Documentation includes port configuration guide
- [ ] Error messages are actionable for users

## Implementation Notes

### Technical Approach

**Service Discovery Manager Class:**
```python
class ServiceDiscoveryManager:
    def __init__(self):
        self.services = {
            'comfyui': {'default_port': 8188, 'protocol': 'websocket'},
            'wan2gp': {'default_port': 7860, 'protocol': 'http'},
            'litellm': {'default_port': 8000, 'protocol': 'http'},
            'rvc': {'default_port': 7865, 'protocol': 'http'},
            'audioldm': {'default_port': 7863, 'protocol': 'http'}
        }
        self.discovered_services = {}
        
    async def discover_all_services(self):
        """Discover all backend services in parallel"""
        tasks = []
        for service_name, config in self.services.items():
            task = self.discover_service(service_name, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self.process_discovery_results(results)
```

**Port Scanning Strategy:**
1. Check default ports first
2. Check common alternative ports (8000-8200 range)
3. Use service-specific health endpoints for validation
4. Implement exponential backoff for retries

**Service Detection Endpoints:**
- ComfyUI: `ws://localhost:8188/ws` (WebSocket test)
- Wan2GP: `http://localhost:7860/api/health`
- LiteLLM: `http://localhost:8000/health`
- RVC: `http://localhost:7865/api/status`
- AudioLDM: `http://localhost:7863/api/ready`

### Blender Integration
- Store discovered services in addon preferences
- Use `bpy.props.CollectionProperty` for service list
- Implement `bpy.app.timers` for non-blocking discovery
- Create operator `MOVIE_DIRECTOR_OT_discover_services`

### Dependencies
- Python `asyncio` for async operations
- `aiohttp` for HTTP service detection
- `websockets` for WebSocket detection
- Thread pool executor for parallel scanning
- No external Blender addon dependencies

### Agent System Integration
- Producer agent will use discovery results for routing
- Service registry feeds into backend capability catalog
- Discovery status reported to health monitoring system

### Backend Service Requirements
- Services must respond to health check endpoints
- Services should provide capability information
- Standard timeout of 5 seconds per service

## Testing Strategy

### Unit Tests
```python
class TestServiceDiscovery(unittest.TestCase):
    def test_discovery_with_all_services_available(self):
        # Mock all services responding
        # Verify all discovered correctly
        
    def test_discovery_with_partial_services(self):
        # Mock only some services available
        # Verify partial discovery works
        
    def test_discovery_timeout_handling(self):
        # Mock slow/hanging service
        # Verify timeout works correctly
```

### Integration Tests
- Test with real backend services
- Test with various network configurations
- Test discovery recovery after network issues

## Dependencies
- None (this is the foundation story)

## Related Stories
- Provides service registry for STORY-002, STORY-003, STORY-004
- Feeds into STORY-010 (Health Check Service)
- Required by STORY-012 (Service Registry)

## Definition of Done
- [ ] Service discovery completes in <5 seconds
- [ ] All supported backends can be discovered
- [ ] Manual configuration fallback works
- [ ] Unit test coverage >90%
- [ ] Integration tests pass
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] No blocking of Blender UI

---

**Sign-off:**
- [ ] Development Lead
- [ ] Technical Architect
- [ ] QA Engineer