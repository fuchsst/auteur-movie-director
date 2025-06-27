# Epic: API Client Infrastructure

**Epic ID:** EPIC-002  
**Based on PRD:** PRD-001 (Backend Integration Service Layer)  
**Target Milestone:** v0.1.0 - Foundation Release  
**Priority:** Critical (P0)  
**Owner:** Backend Integration Team  
**Status:** Ready for Development  

---

## Epic Description

The API Client Infrastructure epic implements the core communication protocols and client libraries that enable the Blender Movie Director addon to interact with each AI backend service. This epic creates unified, abstracted interfaces for ComfyUI (WebSocket), Wan2GP (Gradio), LiteLLM (OpenAI-compatible), RVC (HTTP), and AudioLDM (HTTP) that hide backend-specific complexity from the rest of the system.

This infrastructure layer is critical for maintaining clean architecture and enabling future backend additions without disrupting existing functionality. It provides the foundation for all AI generation capabilities through well-defined, testable interfaces.

## Business Value

- **Architectural Foundation**: Clean API abstraction enables maintainable codebase
- **Backend Flexibility**: Easy addition of new AI backends as they emerge
- **Developer Productivity**: Unified interfaces reduce integration complexity
- **Reliability**: Robust error handling and retry logic at API level
- **Performance**: Optimized client implementations for each backend type

## Scope & Boundaries

### In Scope
- ComfyUI WebSocket client with real-time progress tracking
- Wan2GP Gradio client for video generation
- LiteLLM OpenAI-compatible client for text generation
- RVC HTTP client for voice synthesis
- AudioLDM client for sound effect generation
- Unified API interface abstraction layer
- Request/response serialization and validation
- Client-specific error handling and retry logic
- Connection pooling and resource management
- Mock implementations for testing

### Out of Scope
- Backend server implementation or modification
- Authentication beyond basic API keys
- Network proxy or VPN handling
- Remote backend support (local-only for v1)
- Client UI components (separate epic)

## Acceptance Criteria

### Functional Criteria
- [ ] ComfyUI client can submit workflows and receive progress updates
- [ ] Wan2GP client can generate videos with all parameter options
- [ ] LiteLLM client supports streaming and non-streaming completions
- [ ] RVC client can train voices and generate speech
- [ ] AudioLDM client generates sound effects from text
- [ ] All clients implement common error interface
- [ ] Clients support cancellation of in-progress operations
- [ ] Response data correctly parsed and validated

### Technical Criteria
- [ ] WebSocket client maintains persistent connections
- [ ] HTTP clients use connection pooling
- [ ] All API calls are async and non-blocking
- [ ] Timeout handling for all network operations
- [ ] Proper cleanup of resources on failure
- [ ] Type hints for all public interfaces
- [ ] 100% unit test coverage for client methods
- [ ] Integration tests with mock backends

### Quality Criteria
- [ ] API response time <100ms overhead per call
- [ ] Memory usage stable under high request volume
- [ ] No resource leaks during extended operation
- [ ] Clear error messages with actionable information
- [ ] API documentation with usage examples
- [ ] Thread-safe operation for concurrent requests
- [ ] Graceful degradation on partial failures
- [ ] Performance benchmarks documented

## User Stories

### Story 1: ComfyUI WebSocket Client
**As a** developer integrating ComfyUI workflows  
**I want** a reliable WebSocket client  
**So that** I can execute workflows and track progress in real-time  

**Given** a ComfyUI server is running  
**When** I submit a workflow via the client  
**Then** I receive a prompt ID immediately  
**And** progress updates stream via WebSocket  
**And** the final result includes output paths  
**And** errors are clearly communicated  

**Story Points:** 13  
**Dependencies:** EPIC-001 (Backend Service Connectivity)  

### Story 2: Wan2GP Gradio Client
**As a** developer generating videos  
**I want** a Gradio client for Wan2GP  
**So that** I can generate videos with various models and parameters  

**Given** Wan2GP server is accessible  
**When** I submit a video generation request  
**Then** the client handles Gradio protocol correctly  
**And** supports all Wan2GP parameter options  
**And** returns video file paths on completion  
**And** provides progress callbacks during generation  

**Story Points:** 8  
**Dependencies:** EPIC-001  

### Story 3: LiteLLM Text Generation Client
**As a** developer implementing script analysis  
**I want** an OpenAI-compatible client for LiteLLM  
**So that** I can generate and analyze text with local models  

**Given** LiteLLM server is running  
**When** I request a completion  
**Then** the client supports both streaming and blocking modes  
**And** handles model selection transparently  
**And** manages conversation context  
**And** returns structured JSON when requested  

**Story Points:** 8  
**Dependencies:** EPIC-001  

### Story 4: Unified Error Handling
**As a** developer using multiple backends  
**I want** consistent error handling across all clients  
**So that** I can handle failures uniformly  

**Given** any API client operation  
**When** an error occurs  
**Then** a typed exception is raised  
**And** the exception includes error code, message, and context  
**And** network errors are distinguished from API errors  
**And** retry logic is applied where appropriate  

**Story Points:** 5  
**Dependencies:** Stories 1-3  

### Story 5: Request Cancellation
**As a** developer managing long-running operations  
**I want** to cancel in-progress requests  
**So that** users can abort operations cleanly  

**Given** an active API request  
**When** cancellation is requested  
**Then** the client immediately stops waiting  
**And** sends cancellation to backend if supported  
**And** cleans up any resources  
**And** returns a cancelled status  

**Story Points:** 5  
**Dependencies:** Stories 1-3  

### Story 6: Mock Client Implementation
**As a** developer writing tests  
**I want** mock implementations of all clients  
**So that** I can test without running backends  

**Given** the mock client mode is enabled  
**When** I make any API call  
**Then** realistic mock responses are returned  
**And** progress callbacks fire on schedule  
**And** errors can be simulated  
**And** responses match real backend formats  

**Story Points:** 8  
**Dependencies:** Stories 1-3  

## Technical Requirements

### Architecture Components

1. **Abstract Base Client**
   ```python
   class BaseAPIClient(ABC):
       @abstractmethod
       async def submit(self, request: Dict) -> str
       @abstractmethod
       async def get_status(self, job_id: str) -> JobStatus
       @abstractmethod
       async def cancel(self, job_id: str) -> bool
       @abstractmethod
       async def get_result(self, job_id: str) -> Dict
   ```

2. **ComfyUI WebSocket Client**
   - WebSocket connection management
   - Binary message handling for images
   - Queue position tracking
   - Progress percentage calculation

3. **Wan2GP Gradio Client**
   - Gradio protocol implementation
   - File upload/download handling
   - Session management
   - Parameter validation

4. **LiteLLM HTTP Client**
   - OpenAI API compatibility
   - Streaming response handler
   - Token counting
   - Context window management

5. **Audio Service Clients**
   - RVC model training endpoints
   - Voice synthesis API
   - AudioLDM text-to-sound
   - File format conversion

### Integration Points
- **EPIC-001**: Uses connection pool from connectivity layer
- **EPIC-003**: Task queue submits via these clients
- **EPIC-004**: Workflow execution uses client interfaces
- **EPIC-008**: Audio services integrated here
- **PRD-006**: Node system calls clients for execution
- **PRD-007**: Regeneration uses same client interfaces

## Risk Assessment

### Technical Risks
1. **Protocol Changes** (Medium)
   - Risk: Backend APIs may change without notice
   - Mitigation: Version detection and compatibility layer

2. **WebSocket Stability** (High)
   - Risk: WebSocket connections may drop frequently
   - Mitigation: Automatic reconnection with state recovery

3. **Response Size** (Medium)
   - Risk: Large responses may overwhelm memory
   - Mitigation: Streaming response handlers

### Business Risks
1. **Backend Diversity** (Medium)
   - Risk: Each backend has unique quirks
   - Mitigation: Comprehensive integration testing

## Success Metrics
- All API calls complete within timeout (99%)
- Zero memory leaks over 24-hour operation
- Mock tests cover 100% of real scenarios
- API overhead <100ms per request
- Developer integration time <1 day per backend

## Dependencies
- EPIC-001 must be complete for connection management
- Python packages: websocket-client, gradio_client, httpx, aiohttp
- Backend API documentation

## Timeline Estimate
- Development: 4 weeks
- Testing: 1 week  
- Documentation: 3 days
- Total: ~5.5 weeks

---

**Sign-off Required:**
- [ ] Technical Lead
- [ ] Backend Architect
- [ ] QA Lead
- [ ] API Designer