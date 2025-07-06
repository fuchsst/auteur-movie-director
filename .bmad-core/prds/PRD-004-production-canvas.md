# Product Requirements Document: Production Canvas

## Executive Summary

### Business Justification
The Production Canvas serves as the creative command center of the Generative Media Studio, implementing a visual programming paradigm that transforms AI-powered content creation from a technical exercise into an intuitive creative process. This interface directly enables:
- **90% Reduction in Technical Barriers**: Visual nodes replace command lines
- **10x Creative Iteration Speed**: Real-time feedback and instant variations
- **Unlimited Workflow Complexity**: Hierarchical organization via subflows
- **Professional Standards Compliance**: Node-based editing familiar to industry

### Target User Personas
- **Visual Effects Artists**: Experienced with node-based tools (Nuke, Houdini)
- **Film Directors**: Need narrative control without technical complexity
- **Content Creators**: Require rapid iteration for social media
- **Creative Agencies**: Building custom branded workflows
- **Media Students**: Learning AI-powered production techniques

### Expected Impact
- Transform AI generation from technical task to creative flow
- Enable complex multi-stage productions in single interface
- Establish visual programming standard for generative media
- Support real-time collaborative creative sessions
- Reduce production time from days to hours

## Problem Statement

### Current Limitations
1. **Technical Abstraction Gap**: AI models require deep technical knowledge
2. **Workflow Invisibility**: No visual representation of creative pipeline
3. **Parameter Opacity**: Critical settings hidden in configurations
4. **Delayed Feedback**: Results only visible after full completion
5. **Iteration Friction**: Each variation requires manual reconfiguration

### Pain Points
- Creative vision lost in technical implementation
- No way to visualize complex production pipelines
- Impossible to reuse successful creative patterns
- Collaborative creation blocked by single-user tools
- Learning curve prevents adoption by non-technical users

### Industry Gaps
- Missing visual standard for AI-powered creation
- No real-time collaborative node editing
- Lack of hierarchical workflow organization
- Absent integration between generation and assembly
- No unified interface for all media types

## Solution Overview

### Visual Programming Environment
Implement Svelte Flow-based node editor with custom nodes designed specifically for generative media production:

**Core Design Principles**
1. **Functional Abstraction**: Nodes represent creative tasks, not technical models
2. **Visual Data Flow**: Clear connections show creative pipeline
3. **Real-Time Feedback**: Live progress and previews on canvas
4. **Hierarchical Organization**: Scenes contain shots, shots contain elements
5. **Non-Destructive Workflow**: Takes system preserves all variations

### Custom Node Architecture

**Primary Node Types**
- **ShotNode**: Central execution unit with prompt, generate button, progress, takes gallery
- **AssetNode**: Reusable elements (Characters, Styles, Locations) with previews
- **SceneGroupNode**: Hierarchical container for organizing narrative structure
- **PipelineNode**: Abstracted AI capabilities with quality selection

**Functional Categories**
- **Generation**: Create new content from text/image inputs
- **Transformation**: Modify existing content (style, motion, effects)
- **Assembly**: Combine elements into sequences
- **Export**: Format for final delivery

## User Stories & Acceptance Criteria

### Epic 1: Intuitive Visual Creation
**As a** creative professional  
**I want to** build complex workflows visually  
**So that** I can focus on creativity, not technology

**Acceptance Criteria:**
- [ ] Drag nodes from categorized library
- [ ] Connect with visual compatibility feedback
- [ ] Preview connections before confirming
- [ ] Auto-arrange for clarity
- [ ] Tooltips explain functionality

### Epic 2: Real-Time Collaborative Editing
**As a** creative team  
**I want to** work together on the same canvas  
**So that** we can iterate faster

**Acceptance Criteria:**
- [ ] Multiple cursors visible on canvas
- [ ] Name labels for each user
- [ ] Changes sync within 500ms
- [ ] Conflict resolution for simultaneous edits
- [ ] Activity log shows who did what

### Epic 3: Hierarchical Production Organization
**As a** filmmaker  
**I want to** organize shots into scenes  
**So that** I can manage complex narratives

**Acceptance Criteria:**
- [ ] Double-click to enter SceneGroupNode
- [ ] Breadcrumb navigation shows context
- [ ] Nested subflows up to 5 levels deep
- [ ] Collapse/expand scene contents
- [ ] Overview minimap for navigation

### Epic 4: Non-Destructive Takes System
**As an** artist  
**I want to** generate multiple variations  
**So that** I can choose the best result

**Acceptance Criteria:**
- [ ] Each generation creates new take
- [ ] Gallery view shows all takes
- [ ] Side-by-side comparison mode
- [ ] One-click active take selection
- [ ] Preserve all generation parameters

### Epic 5: Progressive Complexity
**As a** user of any skill level  
**I want to** start simple and grow  
**So that** I'm not overwhelmed

**Acceptance Criteria:**
- [ ] Starter template library
- [ ] Progressive node disclosure
- [ ] Complexity indicators on nodes
- [ ] Guided workflow suggestions
- [ ] Save/share custom templates

## Technical Requirements

### Development Container Setup
#### Frontend Dockerfile (Multi-Stage Build)
```dockerfile
# Builder Stage - Development dependencies
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
RUN npm prune --production

# Final Stage - Production runtime
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/build ./build
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
EXPOSE 4173
ENV NODE_ENV=production
CMD ["node", "build"]
```

#### Development Environment Configuration
```yaml
# docker-compose.yml frontend service
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  container_name: gms_frontend
  ports:
    - "5173:5173"  # Vite HMR port
    - "4173:4173"  # Preview port
  volumes:
    - ./frontend:/app
    - /app/node_modules  # Prevent host override
  environment:
    - VITE_BACKEND_URL=http://backend:8000
    - VITE_WS_URL=ws://backend:8000/ws
```

#### Performance Optimization
- **Hot Module Replacement**: Vite configuration for instant updates
- **Volume Mounts**: Source code changes reflect immediately
- **Node Modules Isolation**: Container-specific dependencies
- **Build Caching**: Layer optimization for faster rebuilds

### Canvas Implementation
- **Framework**: SvelteKit with @xyflow/svelte
- **State Management**: 
  ```javascript
  // projectStore.js structure
  {
    nodes: Map<id, NodeData>,
    edges: Map<id, EdgeData>,
    viewport: { x, y, zoom },
    selectedNodes: Set<id>,
    activeTakes: Map<nodeId, takeId>
  }
  ```
- **Persistence**: Auto-save to project.json every 5 seconds
- **Synchronization**: WebSocket events for real-time updates

### Node System Architecture
```javascript
// Base node class
class GenerativeNode {
  constructor(type, position) {
    this.id = generateUUID();
    this.type = type;
    this.position = position;
    this.data = {
      label: this.getLabel(),
      status: 'idle',
      progress: 0,
      takes: [],
      activeTake: null
    };
  }
  
  async generate() {
    // Implemented by subclasses
  }
}
```

### Real-Time Communication
- **WebSocket Protocol**: 
  - Connect: `ws://backend/canvas/{projectId}`
  - Events: `nodeUpdate`, `edgeUpdate`, `cursorMove`, `generateProgress`
- **Optimistic Updates**: Apply changes locally, reconcile with server
- **Conflict Resolution**: Last-write-wins with visual indicators

### Performance Specifications
- **Rendering**: 60 FPS with 1000+ nodes
- **Interaction Latency**: < 16ms for direct manipulation
- **State Sync**: < 200ms for remote updates
- **Memory Usage**: < 1GB for large projects
- **Load Time**: < 2s for 500-node graph

### Testing Infrastructure
#### Unit Testing Setup
```javascript
// Canvas component testing with Vitest
import { render, fireEvent } from '@testing-library/svelte';
import { vi } from 'vitest';
import ProductionCanvas from '$lib/components/ProductionCanvas.svelte';

test('node creation', async () => {
  const { container } = render(ProductionCanvas);
  const canvas = container.querySelector('.svelte-flow');
  
  // Simulate drag from library
  await fireEvent.drop(canvas, {
    dataTransfer: { getData: () => 'shotNode' }
  });
  
  expect(container.querySelectorAll('.node')).toHaveLength(1);
});
```

#### Integration Testing
- **WebSocket Mock Server**: Test real-time synchronization
- **State Management Tests**: Verify store updates and persistence
- **Collision Detection**: Test simultaneous edit resolution
- **Performance Benchmarks**: Canvas rendering with large graphs

#### End-to-End Testing
```javascript
// Playwright test for complete workflow
test('create shot workflow', async ({ page }) => {
  await page.goto('/project/123/canvas');
  
  // Drag Shot node
  await page.dragAndDrop('.node-library .shot-node', '.canvas');
  
  // Connect nodes
  await page.dragAndDrop('.output-socket', '.input-socket');
  
  // Generate content
  await page.click('.generate-button');
  await page.waitForSelector('.progress-complete');
  
  // Verify take created
  await expect(page.locator('.takes-gallery .take')).toHaveCount(1);
});
```

#### Development Testing Commands
```makefile
# Makefile additions for canvas testing
test-canvas:        # Run canvas-specific tests
	docker compose exec frontend npm run test:canvas

test-canvas-e2e:    # Run E2E canvas tests
	docker compose exec frontend npx playwright test canvas/

test-performance:   # Run performance benchmarks
	docker compose exec frontend npm run test:perf
```

## User Interface Design

### Canvas Layout Structure
```
┌─────────────────────────────────────────────────────┐
│ Header Toolbar                                      │
│ [New] [Save] [Undo] [Redo] [├─┤] [Zoom] [Share]   │
├──────────┬────────────────────────────┬────────────┤
│          │                            │            │
│  Node    │     Production Canvas      │ Inspector  │
│ Library  │                            │   Panel    │
│          │  ┌─────┐    ┌─────┐       │            │
│ ▼ Create │  │Shot │───▶│Shot │       │ Node Props │
│   Image  │  └─────┘    └─────┘       │            │
│   Video  │      │                     │ Takes      │
│   Audio  │      ▼                     │ Gallery    │
│          │  ┌─────┐                   │            │
│ ▼ Assets │  │ VSE │                   │ [===] 60%  │
│          │  └─────┘                   │            │
└──────────┴────────────────────────────┴────────────┘
```

### Node Visual Language
- **Status Indicators**: 
  - Idle: Gray border
  - Processing: Animated blue border
  - Complete: Green border
  - Error: Red border with icon
- **Progress Display**: Circular progress on node
- **Take Indicator**: Badge showing take count
- **Connection Points**: Color-coded by data type

### Node Anatomy
Each node is a self-contained component with standardized UI elements:
- **Header**: Node title and type identification
- **Connection Ports (Sockets)**: Circular points on left (inputs) and right (outputs)
- **Preview Area**: Thumbnail display showing node output
- **Input Fields**: Direct parameter editing on the node
- **Toggles and Buttons**: Interactive elements (e.g., "Generate" button, feature toggles)

### Typed Socket System
Connections enforce type safety at the UI level:

| Socket Data Type | Description | Underlying Data | Example Use Case |
|-----------------|-------------|-----------------|------------------|
| **String** | Standard text string | string | Text prompts, labels, parameters |
| **Integer** | Whole number | number | Seed values, step counts, frame numbers |
| **Float** | Floating-point number | number | Weights, scale factors |
| **Boolean** | True/false value | boolean | Feature toggles, flags |
| **Image** | Raster image reference | string (file path) | Image processing pipelines |
| **Video** | Video file reference | string (file path) | Video editing workflows |
| **Audio** | Audio file reference | string (file path) | Dialogue, music, sound effects |
| **AssetReference** | Unique asset identifier | string (UUID) | Character, Style connections |
| **ControlMap** | Conditioning image | string (file path) | Depth maps, edge detection |
| **Mask** | Grayscale mask image | string (file path) | Inpainting, selective edits |
| **EDL** | Edit Decision List | string (CMX3600) | Final assembly data |

### Core Node Interfaces

#### Fixed Canvas Nodes
- **Input Node**
  - **Description**: Non-deletable entry point providing context from parent/previous element
  - **Input Ports**: None
  - **Parameters**: Toggle for last frame (Image) vs full video (Video) from previous shot
  - **Output Ports**: Previous Output (Image/Video), Scene Context (Data), Project Context (Data)
  - **Properties Panel**: Shows source information (previous shot/scene name)

- **Output Node**
  - **Description**: Non-deletable exit point collecting final workflow result
  - **Input Ports**: Final Result (Video/Image/Audio)
  - **Parameters**: None
  - **Output Ports**: None
  - **Properties Panel**: Displays output destination in project hierarchy

#### Content Generation Nodes
- **Shot Node**
  - **Description**: Container representing single shot within scene
  - **Input Ports**: Sequence In
  - **Parameters**: Thumbnail of final output
  - **Output Ports**: Sequence Out
  - **Properties Panel**: Shot info, description, Takes gallery with active take selection

- **Generate Video from Image Node**
  - **Description**: Animates source image based on text prompt
  - **Input Ports**: Source Image (Image), Prompt (String), Style (AssetReference)
  - **Parameters**: Generate button, progress indicator, thumbnail
  - **Output Ports**: Output (Video)
  - **Properties Panel**: Expanded prompt, generation settings (motion strength, seed), Takes gallery

#### Asset Management Nodes
- **Asset Node**
  - **Description**: Reusable creative entity (Character, Style, Location)
  - **Input Ports**: None
  - **Parameters**: Preview image, name label
  - **Output Ports**: Asset (AssetReference)
  - **Properties Panel**: Large preview, metadata, link to Asset Browser source

#### Processing Nodes
- **Bokeh Node**
  - **Description**: Applies depth-of-field effect
  - **Input Ports**: Source (Image/Video)
  - **Parameters**: None on-node
  - **Output Ports**: Output (Image/Video)
  - **Properties Panel**: Focal Point, Blur Amount, Aperture Shape sliders, Takes gallery

- **Layer Node**
  - **Description**: Composites multiple layers
  - **Input Ports**: Background (Image/Video), Foreground 1-N (dynamic)
  - **Parameters**: None on-node
  - **Output Ports**: Output (Image/Video)
  - **Properties Panel**: Layer list with Blend Mode, Opacity, Position, Scale per layer

- **Upscale Node**
  - **Description**: AI-powered resolution increase
  - **Input Ports**: Source (Image/Video)
  - **Parameters**: Upscale button
  - **Output Ports**: Output (Image/Video)
  - **Properties Panel**: Scale Factor (2x, 4x), Model Selection, Takes gallery

- **Improve Quality Node**
  - **Description**: AI enhancement (denoise, artifacts, color)
  - **Input Ports**: Source (Image/Video)
  - **Parameters**: Enhance button
  - **Output Ports**: Output (Image/Video)
  - **Properties Panel**: Denoise Strength, Sharpness, Color Model selection

#### Assembly Nodes
- **Transition Node**
  - **Description**: Creates transitions between clips
  - **Input Ports**: Clip A (Video), Clip B (Video)
  - **Parameters**: Transition type icon
  - **Output Ports**: Output (Video)
  - **Properties Panel**: Transition Type dropdown, Duration field

- **Combine Audio Node**
  - **Description**: Mixes video with audio tracks
  - **Input Ports**: Video In (Video), Audio 1-N (Audio)
  - **Parameters**: None on-node
  - **Output Ports**: Video Out (Video)
  - **Properties Panel**: Volume sliders, mute toggles, pan controls per track

- **VSE Assembler Node**
  - **Description**: Terminal node for sequence compilation
  - **Input Ports**: Sequence In (EDL)
  - **Parameters**: Render Final Video button, status display
  - **Output Ports**: Final Video (Video)
  - **Properties Panel**: Output format, resolution, bitrate, render progress

### Chatbar Interface
Located at bottom of Scene View, provides CLI for power users:
- Text-based node graph editing
- Batch operations (create multiple nodes, bulk parameter changes)
- Rapid workflow construction via commands
- Combines visual intuitiveness with text-based speed

## Success Metrics

### Adoption Metrics
- **Learning Curve**: 80% proficient within 2 hours
- **Template Usage**: 70% start with templates
- **Feature Discovery**: 90% use 5+ node types in first week
- **Workflow Sharing**: 40% save custom templates
- **Collaboration Rate**: 50% of projects have 2+ users

### Performance Metrics
- **Canvas FPS**: Consistent 60 FPS with 500 nodes
- **Sync Latency**: P95 < 200ms
- **Generation Start**: < 1s from click to processing
- **Memory Efficiency**: < 100KB per node
- **Crash Rate**: < 0.1% of sessions

### Quality Metrics
- **Task Success**: 95% complete intended workflow
- **Error Recovery**: 90% self-resolve issues
- **Satisfaction Score**: 4.5+ stars
- **Recommendation Rate**: 70% would recommend
- **Support Tickets**: < 5% need help

## Risk Assessment

### Technical Risks
1. **Canvas Performance**: Large graphs may impact browser
   - *Mitigation*: Virtual viewport, node culling, WebGL rendering
2. **Sync Conflicts**: Collaborative editing race conditions
   - *Mitigation*: Operational transformation, conflict UI
3. **Browser Limits**: Memory constraints on complex projects
   - *Mitigation*: Pagination, lazy loading, cloud processing

### Usability Risks
1. **Complexity Overwhelm**: Too many options paralyze users
   - *Mitigation*: Progressive disclosure, smart defaults
2. **Mobile Experience**: Touch interaction limitations
   - *Mitigation*: Responsive design, gesture support
3. **Learning Curve**: Visual programming unfamiliar
   - *Mitigation*: Interactive tutorials, template library

## Development Phases

### Phase 1: Core Canvas (Week 1-2)
- Svelte Flow integration
- Basic node types (Shot, Asset)
- Connection system
- Canvas persistence

### Phase 2: Real-Time Features (Week 3-4)
- WebSocket infrastructure
- Collaborative cursors
- Progress tracking
- State synchronization

### Phase 3: Advanced Nodes (Week 5-6)
- SceneGroupNode with subflows
- PipelineNode variants
- Takes gallery system
- VSEAssemblerNode

### Phase 4: Polish & Performance (Week 7-8)
- Template system
- Performance optimization
- Mobile support
- User onboarding

## Integration Requirements

### Backend Services
- **Generation API**: Submit jobs, track progress
- **Asset Management**: Reference project files
- **WebSocket Gateway**: Real-time communication
- **Storage System**: Save/load canvas state

### Project System
- **project.json Integration**: Canvas state persistence
- **Git Compatibility**: Diff-friendly serialization
- **Asset References**: Relative path resolution
- **Takes Management**: Link to file system

## Future Enhancements
- AI-powered node suggestions based on context
- Voice-controlled node creation
- AR/VR canvas manipulation
- Automated workflow optimization
- Community node marketplace

---

**Document Version**: 2.0  
**Created**: 2025-01-02  
**Last Updated**: 2025-01-02  
**Status**: Final Draft  
**Owner**: Generative Media Studio Product Team