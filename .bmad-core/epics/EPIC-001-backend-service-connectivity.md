# Epic: Backend Service Connectivity

**Epic ID:** EPIC-001  
**Based on PRD:** PRD-001 (Backend Integration Service Layer)  
**Target Milestone:** v0.1.0 - Foundation Release  
**Priority:** Critical (P0)  
**Owner:** Backend Integration Team  
**Status:** Ready for Development  

---

## Epic Description

The Backend Service Connectivity epic establishes the foundational communication layer between the Blender Movie Director addon and all AI generation backends (ComfyUI, Wan2GP, LiteLLM, RVC, AudioLDM). This epic transforms the addon from a static UI prototype into a live system capable of discovering, connecting to, and maintaining stable connections with local AI services.

This is the most critical epic as it enables all other functionality - without reliable backend connections, no AI generation is possible. The system must be resilient, self-healing, and provide clear feedback to users about service availability.

## Business Value

- **Immediate Functionality**: Transforms non-functional UI into working generative film studio
- **User Experience**: Zero-configuration service discovery reduces technical barriers
- **Reliability**: Automatic recovery ensures uninterrupted creative workflow
- **Foundation**: Enables all downstream AI generation capabilities
- **Market Differentiation**: Seamless backend integration sets product apart from competitors

## Scope & Boundaries

### In Scope
- Automatic service discovery for ComfyUI, Wan2GP, LiteLLM, RVC, AudioLDM
- Connection establishment and WebSocket/HTTP client initialization
- Health monitoring with configurable intervals
- Automatic reconnection with exponential backoff
- Service status visualization in Blender UI
- Connection configuration persistence in .blend file
- Multi-backend coordination and status aggregation
- Error handling and user notification system

### Out of Scope
- Backend installation or configuration (assumed pre-installed)
- Complex workflow execution (covered in separate epic)
- Resource management beyond connection status
- Authentication or security features (local-only in v1)
- Network proxy or remote backend support

## Acceptance Criteria

### Functional Criteria
- [ ] Addon automatically discovers all running backend services on startup
- [ ] Each backend connection status clearly displayed in main panel
- [ ] Services can be manually refreshed without addon reload
- [ ] Disconnected services attempt reconnection every 30 seconds
- [ ] Connection failures show user-friendly error messages
- [ ] Service URLs and ports configurable via addon preferences
- [ ] Connection state persists across Blender sessions
- [ ] Multi-backend status aggregated into single health indicator

### Technical Criteria
- [ ] WebSocket client successfully connects to ComfyUI
- [ ] Gradio client successfully connects to Wan2GP
- [ ] HTTP client successfully connects to LiteLLM API
- [ ] All connections use thread-safe async patterns
- [ ] Connection pooling implemented for HTTP clients
- [ ] Exponential backoff prevents connection flooding
- [ ] Service discovery completes within 5 seconds
- [ ] Memory usage remains stable during reconnection cycles

### Quality Criteria
- [ ] 99.9% connection uptime during normal operation
- [ ] Reconnection succeeds within 3 attempts (90 seconds)
- [ ] Clear error messages for all failure scenarios
- [ ] No UI freezing during connection operations
- [ ] Unit tests cover all connection scenarios
- [ ] Integration tests validate multi-backend coordination
- [ ] Documentation includes troubleshooting guide
- [ ] Performance profiling shows <100ms UI impact

## User Stories

### Story 1: Automatic Service Discovery
**As a** filmmaker using Blender Movie Director  
**I want** the addon to automatically find my AI services  
**So that** I don't need technical knowledge to get started  

**Given** I have ComfyUI, Wan2GP, and LiteLLM running locally  
**When** I enable the Movie Director addon  
**Then** all services are discovered and connected within 5 seconds  
**And** I see green status indicators for each service  
**And** I can immediately start generating content  

**Story Points:** 8  
**Dependencies:** None  

### Story 2: Connection Status Visualization
**As a** content creator  
**I want** to see the status of all backend services  
**So that** I know what generation capabilities are available  

**Given** the addon is loaded with multiple backends  
**When** I open the main Movie Director panel  
**Then** I see a status section showing all backend services  
**And** each service shows connection state (Connected/Disconnected/Connecting)  
**And** failed services show the reason for failure  
**And** I can click for more detailed connection information  

**Story Points:** 5  
**Dependencies:** Story 1  

### Story 3: Automatic Reconnection
**As a** user working on a long project  
**I want** disconnected services to automatically reconnect  
**So that** temporary issues don't interrupt my workflow  

**Given** I'm actively using the addon  
**When** a backend service becomes unavailable  
**Then** the addon detects disconnection within 30 seconds  
**And** automatically attempts reconnection with exponential backoff  
**And** notifies me when service is restored  
**And** queued tasks resume when connection returns  

**Story Points:** 8  
**Dependencies:** Story 1, Story 2  

### Story 4: Manual Service Configuration
**As a** technical user  
**I want** to configure custom service endpoints  
**So that** I can use non-standard backend configurations  

**Given** I have backends on non-default ports  
**When** I open addon preferences  
**Then** I can set custom URLs for each backend service  
**And** test each connection individually  
**And** save configuration for future sessions  
**And** use environment variables for configuration  

**Story Points:** 5  
**Dependencies:** Story 1  

### Story 5: Connection Error Handling
**As a** user  
**I want** clear error messages when connections fail  
**So that** I can troubleshoot issues myself  

**Given** a backend service is not accessible  
**When** the addon tries to connect  
**Then** I see a specific error message (not generic)  
**And** the message suggests potential solutions  
**And** I can copy error details for support  
**And** the addon remains functional for other services  

**Story Points:** 3  
**Dependencies:** Story 1, Story 2  

### Story 6: Health Monitoring Dashboard
**As a** power user  
**I want** detailed health metrics for all services  
**So that** I can optimize my generation pipeline  

**Given** multiple backends are connected  
**When** I open the health monitoring panel  
**Then** I see response times for each service  
**And** connection uptime percentages  
**And** recent error history  
**And** current queue depths  

**Story Points:** 5  
**Dependencies:** Story 1, Story 2, Story 3  

## Technical Requirements

### Architecture Components
1. **Service Discovery Manager**
   - Port scanning for known backend services
   - mDNS/Zeroconf support for automatic discovery
   - Fallback to manual configuration

2. **Connection Pool Manager**
   - WebSocket client for ComfyUI
   - Gradio client for Wan2GP
   - HTTP client pool for LiteLLM
   - Thread-safe connection management

3. **Health Monitor Service**
   - Periodic health checks (configurable interval)
   - Connection state machine implementation
   - Event-based status notifications

4. **UI Integration Layer**
   - Real-time status updates via bpy.app.timers
   - Non-blocking UI updates
   - Status icon rendering system

### Integration Points
- **PRD-002**: Script analysis requires LiteLLM connection
- **PRD-003**: Character generation requires ComfyUI connection
- **PRD-004**: Style workflows require ComfyUI connection
- **PRD-005**: Environment generation requires ComfyUI/Wan2GP
- **PRD-006**: Node execution triggers via connection layer
- **PRD-007**: Regeneration queue uses connection pool

## Risk Assessment

### Technical Risks
1. **WebSocket Compatibility** (Medium)
   - Risk: Blender's Python may have WebSocket limitations
   - Mitigation: Fallback to HTTP polling if needed

2. **Thread Safety** (High)
   - Risk: Concurrent connections may cause race conditions
   - Mitigation: Implement proper locking and queue mechanisms

### Business Risks
1. **Backend Diversity** (Medium)
   - Risk: Supporting many backends increases complexity
   - Mitigation: Modular architecture with backend plugins

## Success Metrics
- Connection success rate >99%
- Average discovery time <3 seconds
- Reconnection success within 90 seconds
- Zero UI freezes during connection operations
- User satisfaction with connection reliability >4.5/5

## Dependencies
- Blender 3.6+ Python environment
- Network libraries (requests, websocket-client, gradio_client)
- Backend services running and accessible

## Timeline Estimate
- Development: 3 weeks
- Testing: 1 week
- Documentation: 3 days
- Total: ~4.5 weeks

---

**Sign-off Required:**
- [ ] Technical Lead
- [ ] Product Owner
- [ ] QA Lead
- [ ] UX Designer