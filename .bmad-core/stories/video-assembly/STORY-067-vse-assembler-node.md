# User Story: STORY-067 - VSEAssemblerNode Terminal Node Implementation

## Story Description
**As a** filmmaker using the production canvas
**I want** a terminal node that accepts shot sequences and triggers video assembly
**So that** I can complete my film production workflow without leaving the platform

## Acceptance Criteria

### Functional Requirements
- [ ] VSEAssemblerNode appears in node palette as terminal node type
- [ ] Node accepts shot sequence inputs via visual connections
- [ ] Node has single "Render Final Video" button on UI
- [ ] Node prevents outgoing connections (terminal-only validation)
- [ ] Properties panel displays format, resolution, bitrate controls
- [ ] Node integrates with existing canvas zoom and pan functionality

### Technical Requirements
- [ ] Node extends base CanvasNode with terminal node restrictions
- [ ] Input validation ensures only shot sequences can connect
- [ ] Node serialization includes all configuration parameters
- [ ] TypeScript interfaces define node properties and methods
- [ ] Integration with Svelte Flow node system
- [ ] WebSocket integration for progress updates

### Quality Requirements
- [ ] Unit tests cover node creation and configuration
- [ ] Integration tests validate canvas integration
- [ ] UI tests verify button functionality and validation
- [ ] Performance tests ensure 60 FPS with 500+ nodes
- [ ] Accessibility tests for keyboard navigation

## Implementation Notes

### Technical Approach
- **Frontend**: Extend CanvasNode class in Svelte Flow
- **Backend**: Create FastAPI endpoint for node configuration
- **Canvas Integration**: Register node type in node registry
- **Validation**: Implement input type checking and connection restrictions

### Component Structure
```
VSEAssemblerNode/
├── VSEAssemblerNode.svelte
├── VSEAssemblerNode.types.ts
├── VSEAssemblerNode.utils.ts
└── VSEAssemblerNode.stories.ts
```

### Key Dependencies
- **EPIC-004**: Production Canvas infrastructure
- **STORY-068**: MoviePy assembly pipeline
- **STORY-071**: EDL generation system
- **WebSocket Service**: For real-time updates

### API Endpoints Required
- `POST /api/v1/assembly/nodes` - Create assembler node
- `GET /api/v1/assembly/nodes/{id}` - Get node configuration
- `PUT /api/v1/assembly/nodes/{id}` - Update node settings
- `POST /api/v1/assembly/nodes/{id}/render` - Trigger assembly

### Testing Strategy
- **Unit Tests**: Node creation, validation, serialization
- **Integration Tests**: Canvas workflow, WebSocket updates
- **E2E Tests**: Complete assembly trigger flow
- **Performance Tests**: 500+ node canvas performance

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 1-2 (Phase 1)**

## Risk Factors
- **Canvas Performance**: May impact with large shot sequences
- **Type Safety**: Complex node interfaces require careful TypeScript
- **Terminal Node Logic**: Unique restrictions need validation

## Success Criteria
- User can drag VSEAssemblerNode onto canvas
- Node accepts connections from shot sequences only
- "Render Final Video" button triggers backend assembly
- All configuration persists across sessions