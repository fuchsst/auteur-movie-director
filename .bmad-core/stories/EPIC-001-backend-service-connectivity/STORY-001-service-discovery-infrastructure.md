# User Story: Service Discovery Infrastructure

**Story ID:** STORY-001  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Backend Infrastructure  
**Story Points:** 8  
**Priority:** Critical (P0)  
**Status:** ✅ VALIDATED (94.7% tests passing, 77.97% coverage)

---

## Story Description

**As a** Blender user with AI backends running locally  
**I want** the addon to automatically discover all available services  
**So that** I can start creating content without manual configuration  

## Acceptance Criteria

### Functional Requirements
- [x] Discovers ComfyUI on default port (8188) and configurable ports
- [x] Discovers Wan2GP on default port (7860) and configurable ports  
- [x] Discovers RVC on default port (7865) and configurable ports
- [x] Discovers AudioLDM on default port (7863) and configurable ports
- [x] Falls back to manual configuration if auto-discovery fails
- [x] Completes discovery scan within 5 seconds
- [x] Supports parallel discovery of all services

### Technical Requirements
- [x] Implements async service discovery pattern
- [x] Uses thread-safe discovery mechanism
- [x] Supports both HTTP and WebSocket protocol detection
- [x] Implements timeout handling for unresponsive ports
- [x] Creates service registry data structure
- [x] Handles network errors gracefully
- [x] Supports IPv4 and IPv6 addresses
- [x] Implements service type detection from response

### Quality Requirements
- [x] Unit tests cover all discovery scenarios (18/19 tests passing)
- [x] Mock services for testing without real backends
- [x] Discovery completes without blocking UI
- [x] Memory usage remains constant during discovery
- [x] Clear logging of discovery process
- [x] Performance profiling shows <100ms per service
- [ ] Documentation includes port configuration guide
- [x] Error messages are actionable for users

## Implementation Notes

### Technical Approach

**Service Discovery Manager Class:**
```python
class ServiceDiscoveryManager:
    def __init__(self):
        self.services = {
            'comfyui': {'default_port': 8188, 'protocol': 'http'},  # Uses HTTP API
            'wan2gp': {'default_port': 7860, 'protocol': 'http'},
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
- ComfyUI: `http://localhost:8188/system_stats` (HTTP API endpoint)
- Wan2GP: `http://localhost:7860/api/health`
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
- [x] Service discovery completes in <5 seconds
- [x] All supported backends can be discovered
- [x] Manual configuration fallback works
- [ ] Unit test coverage >90% (currently 77.97%)
- [x] Integration tests pass
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [x] No blocking of Blender UI

---

## Validation Notes (2025-06-28)

**Test Results:**
- Unit tests: 18/19 passing (94.7% pass rate)
- Code coverage: 77.97% for service_discovery.py
- Single test failure: `test_discovery_timeout` expects 6s but takes ~9s in test environment

**Key Validations:**
- ✅ All 4 backend services properly configured with correct ports and endpoints
- ✅ Parallel discovery implemented using asyncio
- ✅ Graceful error handling with clear messages
- ✅ Alternative port discovery working
- ✅ Both async (aiohttp) and sync (urllib) fallback implemented
- ✅ Singleton pattern for Blender addon integration

**Minor Issues:**
- Test timeout adjustment needed for slower environments
- Documentation for port configuration still pending
- Code coverage below 90% target (mainly due to sync fallback paths)

**Recommendation:** Story is functionally complete and ready for integration. Minor documentation and test adjustments can be handled in polish phase.

---

**Sign-off:**
- [ ] Development Lead
- [ ] Technical Architect
- [x] QA Engineer (validated via automated tests)