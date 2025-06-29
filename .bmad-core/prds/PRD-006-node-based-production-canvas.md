# Product Requirements Document: Node-Based Production Canvas

**Version:** 2.1  
**Date:** 2025-01-29  
**Owner:** BMAD Business Analyst  
**Status:** Web Architecture Pivot  
**PRD ID:** PRD-006  
**Dependencies:** Backend Integration Service Layer (PRD-001), Intelligent Script-to-Shot Breakdown System (PRD-002), Character Consistency Engine (PRD-003), Style Consistency Framework (PRD-004), Environment Management System (PRD-005), File-Based Project Structure (PRD-008)

---

## Executive Summary

### Business Justification
The Node-Based Production Canvas transforms Movie Director from a traditional interface into a visual, intuitive production environment accessible through any web browser. This feature addresses the fundamental challenge of managing complex film production hierarchies by providing a visual graph representation of the entire filmmaking process, from high-level story structure down to individual shot generation, all with real-time collaboration capabilities.

By leveraging Svelte Flow's proven node-based interface paradigm, this system makes the complex relationships between story elements, assets, scenes, and shots immediately visible and manipulable to distributed teams. The visual nature of the canvas dramatically reduces the cognitive load of managing multi-layered film production workflows while enabling seamless collaboration between team members working from different locations.

The web-based node canvas serves as the central nervous system of the regenerative content model, where all project definitions are visualized as nodes with connections stored in PostgreSQL, while generated content remains as S3 file references that can be regenerated based on the node parameters at any time. Real-time synchronization ensures all team members see the same production state.

### Target User Personas
- **Distributed Creative Teams** - Artists collaborating on productions from different locations
- **Visual Production Managers** - Filmmakers who prefer visual organization over lists
- **Technical Directors** - Building custom workflows accessible to entire teams
- **Film Schools** - Teaching production pipeline concepts through collaborative tools
- **Creative Agencies** - Managing client projects with real-time visibility
- **Remote Production Companies** - Coordinating global teams on complex projects

### Expected Impact on Film Production Workflow
- **Visual Collaboration**: Transform production planning into shared visual experience
- **Workflow Transparency**: Make pipeline configurations visible and editable by all
- **Real-Time Coordination**: Enable instant updates across distributed teams
- **Production Scalability**: Manage complex multi-scene films through cloud infrastructure
- **Pipeline Democratization**: Allow non-technical users to understand and modify workflows

---

## Problem Statement

### Current Limitations in Desktop Production Tools
1. **Single-User Workflows**: Node-based tools locked to individual workstations
2. **No Real-Time Sharing**: Team members work in isolation with manual syncing
3. **Hidden Pipelines**: Generation workflows invisible and unmodifiable
4. **Platform Limitations**: Desktop-only access restricts collaboration
5. **Version Conflicts**: Node graph changes create merge conflicts

### Pain Points in Web-Based Creative Tools
- **Limited Visual Tools**: Most web tools use simple forms, not visual graphs
- **No Pipeline Control**: Users can't see or modify generation workflows
- **Poor Scalability**: Interfaces become unwieldy with complex projects
- **Fragmented Tools**: Visual planning separate from execution
- **No Custom Workflows**: Stuck with predefined, inflexible pipelines

### Gaps in Current Web Pipeline
- **Missing Visual Orchestration**: No way to visualize entire production flow
- **No Collaborative Graphs**: Node editors typically single-user only
- **Limited Pipeline Access**: Can't customize generation pipelines
- **Poor Dependency Tracking**: Asset relationships hidden from view
- **No Hierarchical Organization**: Flat structures for complex productions

---

## Solution Overview

### Feature Description within Web Architecture
The Node-Based Production Canvas introduces a web-based visual editor using Svelte Flow that visualizes and controls the entire generative film production pipeline. This system represents each production element—from story concepts to individual shots—as nodes that can be connected, configured, and executed within a hierarchical graph structure, all synchronized in real-time across team members.

**Core Components:**
1. **Hierarchical Node System** - Multi-level graphs with subflows for project → scene → shot navigation
2. **Production Node Types** - Specialized nodes for each element (Character, Style, Environment, Shot, etc.)
3. **Pipeline Configuration Nodes** - Visual pipeline builders pointing to backend workflows
4. **Asset Integration** - Drag-and-drop from shared asset library with live previews
5. **Execution Control** - Generate buttons with real-time progress for all users
6. **Dependency Visualization** - Live highlighting of asset usage across production
7. **Collaborative Features** - Multi-cursor support, user presence, real-time updates
8. **Version Control** - Complete history with visual diff and rollback
9. **Template System** - Shareable workflow templates for common patterns
10. **API Integration** - External tool connectivity through visual nodes

### Integration with Advanced Features
**Real-Time Collaboration:**
- WebSocket-based synchronization of all node changes
- Conflict-free collaborative editing with operational transformation
- User presence indicators showing who's working where
- Shared execution state visible to all team members

**Cloud Processing Integration:**
- Visual representation of distributed task execution
- Real-time progress updates on node interfaces
- Queue visualization for pending operations
- Resource usage indicators per node

**Pipeline Flexibility:**
- Function Runner nodes for arbitrary model execution
- ComfyUI workflow nodes with parameter exposure
- Wan2GP integration nodes with quality presets
- Custom pipeline creation through visual interface

### Backend Service Architecture
**FastAPI Endpoints:**
- Node graph CRUD operations
- Graph validation and analysis
- Execution orchestration
- Template management

**Celery Task Integration:**
- Node execution mapped to distributed tasks
- Progress streaming to WebSocket
- Dependency resolution for parallel execution
- Resource-aware scheduling

**WebSocket Events:**
- Node position/connection updates
- Execution progress streaming
- User cursor synchronization
- Real-time error propagation

---

## User Stories & Acceptance Criteria

### Epic 1: Collaborative Visual Production
**As a distributed team, we want to see and edit our production structure together so we can coordinate effectively across locations.**

#### User Story 1.1: Real-Time Graph Editing
- **Given** multiple team members have the project open
- **When** one member adds or modifies nodes
- **Then** all members see changes within 300ms
- **And** smooth animations show what changed
- **And** user avatars indicate who made changes
- **And** conflicts are resolved automatically

**Acceptance Criteria:**
- Sub-300ms synchronization latency
- Smooth node position interpolation
- Clear user attribution
- Operational transformation for conflicts

#### User Story 1.2: Hierarchical Navigation
- **Given** a complex multi-scene production
- **When** users navigate the graph
- **Then** they can enter scene subflows seamlessly
- **And** breadcrumbs show current context
- **And** all users can be in different subflows
- **And** navigation state is preserved

**Acceptance Criteria:**
- Instant subflow navigation
- Context-aware breadcrumbs
- Independent user navigation
- State persistence across sessions

### Epic 2: Visual Pipeline Configuration
**As a technical director, I want to configure pipelines visually so my entire team can understand and modify workflows.**

#### User Story 2.1: Pipeline Node System
- **Given** various backend workflows available
- **When** I add pipeline nodes to the canvas
- **Then** I can visually configure data flow
- **And** parameters are exposed as node controls
- **And** team members see my configurations
- **And** changes are validated in real-time

**Acceptance Criteria:**
- Dynamic pipeline node creation
- Visual parameter controls
- Real-time validation feedback
- Instant team synchronization

#### User Story 2.2: Custom Workflow Builder
- **Given** I need a specialized workflow
- **When** I create it using visual nodes
- **Then** it's saved as a reusable template
- **And** other team members can use it
- **And** it integrates with existing nodes
- **And** becomes part of our library

**Acceptance Criteria:**
- Visual workflow creation
- Template export/import
- Team template sharing
- Seamless integration

### Epic 3: Asset Integration and Visualization
**As a creative director, I want to see how assets are used across the production so I can maintain consistency and efficiency.**

#### User Story 3.1: Visual Asset Management
- **Given** characters, styles, and environments in our library
- **When** I drag them onto the canvas
- **Then** asset nodes are created with previews
- **And** connections show usage relationships
- **And** changes propagate to all uses
- **And** team sees the same relationships

**Acceptance Criteria:**
- Drag-and-drop asset creation
- Live preview thumbnails
- Automatic relationship tracking
- Real-time propagation

#### User Story 3.2: Dependency Highlighting
- **Given** complex asset relationships
- **When** I select an asset node
- **Then** all dependent nodes highlight
- **And** usage statistics display
- **And** I can filter to show only dependencies
- **And** team members see my selection

**Acceptance Criteria:**
- Interactive highlighting system
- Real-time statistics
- Advanced filtering options
- Shared selection state

### Epic 4: Distributed Execution Control
**As a producer, I want to manage generation tasks visually so I can optimize resource usage and track progress across the team.**

#### User Story 4.1: Visual Task Execution
- **Given** configured production nodes
- **When** team members initiate generation
- **Then** progress displays on the nodes
- **And** all users see the same progress
- **And** queue position is visible
- **And** results update automatically

**Acceptance Criteria:**
- On-node progress indicators
- Real-time progress sync
- Queue visualization
- Automatic result integration

#### User Story 4.2: Resource Management
- **Given** limited GPU resources
- **When** multiple generations are requested
- **Then** resource usage displays per node
- **And** intelligent scheduling occurs
- **And** team sees resource allocation
- **And** priorities can be adjusted

**Acceptance Criteria:**
- Resource usage visualization
- Smart scheduling algorithms
- Team-wide resource visibility
- Priority adjustment interface

### Epic 5: Template and Knowledge Sharing
**As a studio, we want to build a library of production templates so teams can leverage proven workflows.**

#### User Story 5.1: Workflow Templates
- **Given** successful production patterns
- **When** we save them as templates
- **Then** they're available to all projects
- **And** include documentation
- **And** can be customized per project
- **And** usage is tracked

**Acceptance Criteria:**
- Template creation system
- Cross-project availability
- Embedded documentation
- Usage analytics

#### User Story 5.2: Community Sharing
- **Given** valuable workflow patterns
- **When** we share with community
- **Then** others can import them
- **And** attribution is maintained
- **And** improvements can be shared back
- **And** quality is rated

**Acceptance Criteria:**
- Public template repository
- Attribution system
- Version management
- Quality ratings

---

## Technical Requirements

### Web Application Architecture

#### 1. Svelte Flow Integration Requirements
**Component Architecture:**
- Main Production Canvas component using Svelte Flow library
- Reactive state management with Svelte stores for nodes and edges
- WebSocket integration for real-time synchronization
- Custom node and edge type registration system

**Core Functionality Requirements:**
- Initialize canvas with project-specific node types
- Handle node position changes with optimistic updates
- Broadcast changes to connected team members
- Maintain local state synchronized with server
- Support undo/redo operations
- Auto-save functionality with debouncing

**Event Handling:**
- Node selection and multi-selection
- Connection validation between compatible node types
- Drag-and-drop from asset library
- Keyboard shortcuts for common operations
- Context menus for node-specific actions

#### 2. Custom Node Component Requirements

**Character Node Requirements:**
- Display character thumbnail/avatar prominently
- Show character name in header with appropriate icon
- Display key character traits (age, role, personality)
- Provide "Edit Character" action button
- Output handle to connect to Shot nodes
- Visual indication when character is in use
- Support drag-and-drop from asset library
- Reference character by ID, not file paths

**Style Node Requirements:**
- Display grid of 4 style example images
- Show style name with palette icon
- Display top 3 style keywords as tags
- Hoverable preview for larger image view
- Output handle for style connections
- Visual feedback when connected to shots
- Load style data from asset ID reference

**Shot Node Requirements:**
- Multiple input handles for character, style, environment
- Editable prompt text area with placeholder
- Quality selector dropdown (Low/Standard/High)
- Generate button with loading states
- Progress indicator during generation
- Takes gallery showing all generated versions
- Active take selection mechanism
- Display of connected assets as tags
- User avatar showing who's working on it
- Scene/shot identifier in header
- Output handle for sequence connections

**Quality Tier Display Requirements:**
- Dropdown selector with three options:
  - Low: "Draft - Fast Generation"
  - Standard: "Production - Balanced Quality"
  - High: "Premium - Maximum Quality"
- Visual indicator (icon/color) for selected tier
- Estimated generation time display
- Resource usage indicator

**Environment Node Requirements:**
- Display environment thumbnail image
- Show location name and type
- Display mood/atmosphere metadata
- Output handle for connections
- Support for both 2D and 3D environments
- Integration with location asset library

**Script Node Requirements:**
- Display script title prominently
- Show scene and page count metrics
- "Break Down to Shots" action button
- Generate scene/shot hierarchy when activated
- Reference script from project file structure
- Visual indication of breakdown status

#### 3. Real-Time Synchronization Requirements

**Synchronization Manager Requirements:**
- Handle all graph state changes from multiple clients
- Validate incoming changes before processing
- Apply operational transformation for concurrent edits
- Maintain consistency across all connected clients
- Broadcast updates with sub-300ms latency

**Change Processing Requirements:**
- Support node position updates
- Handle edge creation/deletion
- Process node property changes
- Manage subflow navigation state
- Track user cursor positions

**Conflict Resolution Requirements:**
- Detect simultaneous edits to same elements
- Apply last-write-wins for properties
- Merge non-conflicting position changes
- Notify users of conflicts when needed
- Maintain edit history for rollback

**Performance Requirements:**
- Debounce rapid position updates
- Batch multiple changes when possible
- Use differential updates, not full state
- Compress large payloads
- Handle reconnection gracefully

#### 4. Execution Orchestration Requirements

**Task Routing Requirements:**
- Route different node types to appropriate handlers
- Support extensible node type registration
- Handle unknown node types gracefully
- Maintain execution context throughout

**Shot Generation Orchestration:**
- Gather all connected asset references
- Build generation context from high-level assets
- Select pipeline based on quality tier:
  - Low: Route to fast generation pipeline
  - Standard: Use balanced quality pipeline
  - High: Employ premium generation pipeline
- Track progress with granular updates
- Store results in project file structure
- Update node state upon completion

**Quality-Based Pipeline Selection:**
- Map quality tiers to specific model pipelines
- Consider available resources when routing
- Queue management per quality tier
- Different timeout values per tier
- Cost tracking per quality level

**Asset Context Building:**
- Extract character IDs from connected nodes
- Retrieve style parameters from style nodes
- Gather environment settings
- Combine into unified generation context
- Never expose file paths to frontend
- Use asset service for file resolution

### Database Schema Extensions

#### PostgreSQL Tables for Graph Management
```sql
-- Graph state and versioning
CREATE TABLE graph_states (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    nodes JSONB,
    edges JSONB,
    viewport JSONB,
    version INTEGER,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP
);

-- Node execution history
CREATE TABLE node_executions (
    id UUID PRIMARY KEY,
    node_id VARCHAR(255),
    project_id UUID REFERENCES projects(id),
    status VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    initiated_by UUID REFERENCES users(id),
    parameters JSONB,
    result JSONB
);

-- Graph templates
CREATE TABLE graph_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    category VARCHAR(100),
    graph_data JSONB,
    created_by UUID REFERENCES users(id),
    is_public BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0
);

-- User graph sessions
CREATE TABLE graph_sessions (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    user_id UUID REFERENCES users(id),
    viewport JSONB,
    selected_nodes JSONB,
    active_subflow VARCHAR(255),
    last_activity TIMESTAMP
);
```

### Performance Optimizations

#### 1. Graph Rendering
- Virtual rendering for large graphs
- Level-of-detail node rendering
- Progressive loading of subflows
- Cached node previews

#### 2. Synchronization
- Debounced position updates
- Differential sync for changes
- Conflict-free replicated data types
- Optimistic UI updates

#### 3. Execution Management
- Dependency analysis for parallelization
- Resource-aware task scheduling
- Progress streaming via WebSocket
- Result caching and reuse

---

## Success Metrics

### Collaboration Effectiveness
**Primary KPIs:**
- **Concurrent Users**: Average 5+ per active project
- **Edit Conflicts**: <0.1% requiring manual resolution
- **Sync Latency**: <300ms for 95th percentile
- **Team Satisfaction**: >4.5/5.0 collaboration rating

**Measurement Methods:**
- Real-time collaboration analytics
- Conflict resolution tracking
- Latency monitoring
- Team satisfaction surveys

### Visual Workflow Adoption
**Adoption Metrics:**
- **Canvas Usage**: >80% prefer visual interface
- **Efficiency Gain**: 50% faster project setup
- **Error Reduction**: 60% fewer config errors
- **Learning Time**: <2 hours to proficiency

**Measurement Methods:**
- Interface preference tracking
- Time-to-completion analysis
- Error rate monitoring
- Training completion metrics

### Technical Performance
**System Metrics:**
- **Graph Load Time**: <2s for 1000 nodes
- **Sync Reliability**: >99.9% consistency
- **Execution Success**: >95% first attempt
- **Template Usage**: 100+ shared templates

**Scalability Metrics:**
- **Concurrent Graphs**: 1000+ active
- **Node Capacity**: 10,000+ per graph
- **User Capacity**: 50+ per graph
- **Template Library**: 500+ templates

---

## Risk Assessment & Mitigation

### Technical Risks

#### High Risk: Graph Synchronization Complexity
- **Risk**: Concurrent edits causing inconsistencies
- **Impact**: Data loss or corruption
- **Mitigation**: 
  - Operational transformation algorithms
  - Comprehensive conflict resolution
  - Automatic backups
  - Rollback capabilities

#### Medium Risk: Performance at Scale
- **Risk**: Large graphs becoming unwieldy
- **Impact**: Poor user experience
- **Mitigation**:
  - Virtual rendering techniques
  - Progressive loading
  - Graph optimization
  - Performance monitoring

### Business Risks

#### High Risk: Learning Curve
- **Risk**: Users struggle with node concepts
- **Impact**: Low adoption rate
- **Mitigation**:
  - Comprehensive tutorials
  - Template library
  - Progressive disclosure
  - Community support

---

## Implementation Roadmap

### Phase 1: Core Canvas Infrastructure (Weeks 1-4)
**Deliverables:**
- Basic Svelte Flow integration
- Core node types
- Simple synchronization
- Database schema

**Success Criteria:**
- Canvas loads and renders
- Basic nodes functional
- Simple sync working

### Phase 2: Collaborative Features (Weeks 5-8)
**Deliverables:**
- Real-time synchronization
- User presence
- Conflict resolution
- Version history

**Success Criteria:**
- Multi-user editing stable
- <500ms sync latency
- Conflicts resolved gracefully

### Phase 3: Advanced Nodes (Weeks 9-12)
**Deliverables:**
- All production node types
- Pipeline configuration
- Asset integration
- Execution system

**Success Criteria:**
- Complete node library
- Pipeline config working
- Assets drag-and-drop
- Execution reliable

### Phase 4: Templates and Polish (Weeks 13-16)
**Deliverables:**
- Template system
- Performance optimization
- Advanced features
- Documentation

**Success Criteria:**
- Templates shareable
- Performance targets met
- Features complete
- Docs comprehensive

---

## Stakeholder Sign-Off

### Development Team Approval
- [ ] **Frontend Lead** - Svelte Flow architecture approved
- [ ] **Backend Lead** - Synchronization approach validated
- [ ] **UI/UX Designer** - Node designs finalized
- [ ] **DevOps Lead** - Scalability plan confirmed

### Business Stakeholder Approval
- [ ] **Product Owner** - Features meet vision
- [ ] **Customer Success** - User workflow validated
- [ ] **Marketing** - Differentiation clear
- [ ] **Finance** - Development costs approved

---

**Next Steps:**
1. Create Svelte Flow proof of concept
2. Design custom node components
3. Implement WebSocket synchronization
4. Plan user testing sessions
5. Develop template library

---

*This PRD represents the transformation of the production canvas from a desktop-only tool to a collaborative web-based visual interface, enabling global teams to work together in real-time on complex film productions through the power of modern web technologies.*