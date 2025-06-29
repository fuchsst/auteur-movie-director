# Product Requirements Document: Intelligent Script-to-Shot Breakdown System

**Version:** 2.0  
**Date:** 2025-01-29  
**Owner:** BMAD Business Analyst  
**Status:** Web Architecture Pivot  
**PRD ID:** PRD-002  
**Dependencies:** Backend Integration Service Layer (PRD-001), Character Consistency Engine (PRD-003), Style Consistency Framework (PRD-004), Environment Management System (PRD-005), Node-Based Production Canvas (PRD-006), Regenerative Content Model (PRD-007), File-Based Project Structure (PRD-008)

---

## Executive Summary

### Business Justification
The Intelligent Script-to-Shot Breakdown System represents the critical entry point into the Movie Director web-based generative film studio. This feature transforms the fundamental bottleneck of film pre-production—manually breaking down scripts into actionable scenes and shots—into an automated, AI-driven process accessible from any web browser. By enabling filmmakers to begin with raw screenplay text and automatically generate the complete narrative structure as an interactive node graph, this system eliminates the most time-consuming and error-prone aspect of pre-production planning.

This feature directly addresses the primary user journey barrier: the complexity gap between creative intent (a script idea) and technical execution (structured generative workflows). It democratizes film pre-production by making professional-grade script analysis and shot planning accessible to creators without extensive film school training or industry experience, all through an intuitive web interface.

The system operates on the regenerative content model foundation: script analysis parameters and breakdown structures are stored as project definitions in the PostgreSQL database, while the actual content generation (character assets, environment references, shot videos) exists as S3 file references that can be regenerated at any time. This approach ensures project portability and enables unlimited iteration without file management complexity.

### Target User Personas
- **Independent Screenwriters** - Converting scripts into visual proof-of-concepts collaboratively
- **Film Production Teams** - Distributed teams breaking down scripts together in real-time
- **Content Creator Collectives** - Multiple creators working on shared story projects
- **Film Schools** - Teaching collaborative pre-production workflows online
- **Creative Agencies** - Client-involved concept visualization and iteration
- **Remote Production Companies** - Global teams planning projects asynchronously

### Expected Impact on Film Production Workflow
- **Collaborative Transformation**: Multiple users can work on script breakdown simultaneously
- **Global Accessibility**: Access from any device with internet connection
- **Real-Time Iteration**: Instant updates across all team members during revisions
- **Cloud Processing**: Leverage powerful servers for complex script analysis
- **Version Control**: Complete history of script iterations and breakdowns

---

## Problem Statement

### Current Limitations in Desktop-Based Script Tools
1. **Single-User Workflow**: Traditional tools lock scripts to individual workstations
2. **No Real-Time Collaboration**: Team members work in isolation and merge later
3. **Installation Barriers**: Complex software setup on each user's machine
4. **Limited Processing Power**: Script analysis limited by local hardware
5. **File Synchronization Issues**: Manual sharing leads to version conflicts

### Pain Points in Web-Based Creative Tools
- **Fragmented Workflow**: Script writing separate from production planning
- **No Visual Representation**: Text-based tools lack visual workflow capabilities
- **Limited Intelligence**: Basic formatting without cinematographic understanding
- **Poor Integration**: Scripts don't connect to production pipeline
- **Manual Data Entry**: Re-entering script data into production tools

### Gaps in Current Web Pipeline
- **Missing Visual Interface**: No node-based representation of script structure
- **No Collaborative Analysis**: AI insights not shared in real-time
- **Limited Asset Linking**: Scripts disconnected from character/environment assets
- **No Progressive Enhancement**: Can't leverage cloud compute for better analysis

---

## Solution Overview

### Feature Description within Web Architecture
The Intelligent Script-to-Shot Breakdown System leverages the web platform to provide real-time collaborative script analysis and visual production planning. Using the FastAPI backend for processing and WebSockets for live collaboration, multiple users can work together to transform scripts into production-ready node graphs visible to all team members instantly.

**Core Capabilities:**
1. **Collaborative Script Editor** - Real-time multi-user script editing with presence indicators
2. **Cloud-Based Analysis** - Powerful LLMs analyze scripts on backend servers
3. **Live Node Graph Generation** - Automatic visual representation updated for all users
4. **Shared Asset Creation** - Characters and environments created collaboratively
5. **Version History** - Complete tracking of all changes with rollback capability
6. **Progressive Processing** - Stream results as analysis completes
7. **Cross-Device Sync** - Seamless experience across desktop, tablet, and mobile
8. **Real-Time Notifications** - Team alerts for important changes and completions
9. **Export/Import Flexibility** - Support for all major screenplay formats
10. **API Integration** - Connect with external screenwriting tools

### Integration with Film Crew Agents
**Web-Enhanced Screenwriter Agent:**
- Runs on backend servers with access to powerful LLMs
- Streams analysis results to all connected clients via WebSocket
- Maintains conversation context in database for team continuity
- Provides real-time suggestions visible to all collaborators

**Distributed Processing Benefits:**
- **Casting Director**: Character assets immediately available to all team members
- **Art Director**: Style suggestions propagate instantly across sessions
- **Environment Director**: Location assets shared in real-time
- **Cinematographer**: Shot specifications synchronized across team
- **Sound Designer**: Audio requirements visible during initial planning
- **Editor**: Scene structure updates reflected immediately

### Backend Service Architecture
**FastAPI Endpoints:**
- Script upload and format detection
- Incremental script analysis with progress streaming
- Asset creation triggers for downstream systems
- Version control and change tracking

**Celery Task Processing:**
- Long-running script analysis on GPU workers
- Parallel processing of scenes for faster results
- Background asset generation from script data
- Batch export of production documents

**WebSocket Events:**
- Real-time script editor synchronization
- Live node graph updates as analysis progresses
- Collaborative cursor and selection sharing
- Team presence and activity indicators

---

## User Stories & Acceptance Criteria

### Epic 1: Collaborative Script Management
**As a film production team, we want to collaboratively work on script breakdowns so that all team members stay synchronized throughout pre-production.**

#### User Story 1.1: Multi-User Script Editing
- **Given** multiple team members have access to a project
- **When** they open the script editor simultaneously
- **Then** all users see real-time updates as others type
- **And** each user's cursor and selection is visible to others
- **And** changes are synchronized within 200ms
- **And** conflict resolution handles simultaneous edits gracefully

**Acceptance Criteria:**
- Operational transformation for conflict-free editing
- Color-coded user cursors and selections
- Presence indicators showing active users
- Change attribution in version history

#### User Story 1.2: Cloud-Based Script Analysis
- **Given** a team has uploaded or created a screenplay
- **When** they trigger AI analysis
- **Then** the script is processed on backend servers
- **And** progress updates stream to all connected users
- **And** results appear progressively as scenes are analyzed
- **And** all team members see the same analysis results

**Acceptance Criteria:**
- Server-side processing with no local compute required
- WebSocket streaming of analysis progress
- Incremental result display as available
- Consistent results across all clients

### Epic 2: Visual Node Graph Collaboration
**As a visual production planner, I want to see and manipulate the script structure as a node graph that updates for all team members in real-time.**

#### User Story 2.1: Automatic Node Graph Generation
- **Given** a script has been analyzed by the AI
- **When** users open the Production Canvas
- **Then** they see a complete node graph of the film structure
- **And** the graph is synchronized across all users
- **And** layout is optimized for readability
- **And** assets are automatically linked to appropriate nodes

**Acceptance Criteria:**
- Svelte Flow integration with real-time sync
- Hierarchical scene/shot organization
- Automatic asset node creation and linking
- Smooth animations for graph updates

#### User Story 2.2: Collaborative Node Editing
- **Given** multiple users are viewing the node canvas
- **When** one user modifies the graph (add/move/delete nodes)
- **Then** all users see the changes immediately
- **And** modifications are animated smoothly
- **And** the database is updated to persist changes
- **And** undo/redo is available for all users

**Acceptance Criteria:**
- <500ms synchronization latency
- Smooth graph animations
- Multi-level undo/redo system
- Conflict resolution for simultaneous edits

### Epic 3: Progressive Analysis and Streaming
**As a production team working with long scripts, we want to see analysis results as they're generated rather than waiting for complete processing.**

#### User Story 3.1: Streaming Script Analysis
- **Given** a team uploads a feature-length screenplay
- **When** analysis begins on backend servers
- **Then** results stream to the UI as each scene is processed
- **And** users can start working with completed sections
- **And** the UI remains responsive during analysis
- **And** estimated completion time is displayed

**Acceptance Criteria:**
- Scene-by-scene result streaming
- Progressive UI updates without blocking
- Accurate time estimates based on script length
- Ability to work with partial results

#### User Story 3.2: Distributed Processing
- **Given** a complex script requiring extensive analysis
- **When** the system processes it
- **Then** the work is distributed across multiple backend workers
- **And** different scenes are analyzed in parallel
- **And** results are assembled in correct order
- **And** total processing time is minimized

**Acceptance Criteria:**
- Parallel scene processing on Celery workers
- Intelligent work distribution
- Result ordering and assembly
- Linear performance scaling with workers

### Epic 4: Asset Creation and Linking
**As a production designer, I want character and environment assets to be automatically created and linked based on script analysis, visible to all team members.**

#### User Story 4.1: Collaborative Asset Generation
- **Given** the script analysis identifies characters and locations
- **When** asset generation is triggered
- **Then** placeholder assets are created in the shared library
- **And** all team members see new assets immediately
- **And** assets are linked to relevant scenes/shots
- **And** team members can collaborate on asset refinement

**Acceptance Criteria:**
- Automatic asset creation from script data
- Real-time asset library updates
- Bidirectional scene-asset linking
- Collaborative asset property editing

#### User Story 4.2: Cross-System Asset Coordination
- **Given** assets are created from script analysis
- **When** team members refine them
- **Then** updates propagate to all linked systems
- **And** character consistency parameters are shared
- **And** environment variations are generated
- **And** style frameworks are applied consistently

**Acceptance Criteria:**
- Asset updates trigger system-wide propagation
- Consistency parameters shared across workers
- Version control for asset iterations
- Real-time preview generation

### Epic 5: Version Control and History
**As a production coordinator, I want complete version history of our script breakdown so we can track changes and revert if needed.**

#### User Story 5.1: Change Tracking
- **Given** team members are making changes to the script/breakdown
- **When** changes are saved
- **Then** they are recorded with attribution and timestamp
- **And** a visual diff shows what changed
- **And** change history is searchable
- **And** any team member can review history

**Acceptance Criteria:**
- Git-like change tracking in PostgreSQL
- Visual diff viewer for script changes
- Change attribution with user avatars
- Searchable change history

#### User Story 5.2: Version Rollback
- **Given** a team needs to revert changes
- **When** they select a previous version
- **Then** they can preview the differences
- **And** choose to restore that version
- **And** all team members are notified
- **And** the action is recorded in history

**Acceptance Criteria:**
- Non-destructive rollback (preserves history)
- Preview before rollback
- Team notifications for major changes
- Rollback attribution and reasoning

---

## Technical Requirements

### Web Application Architecture

#### 1. Frontend Component Requirements

**Collaborative Script Editor Requirements:**
- Real-time collaborative text editing with WebSocket
- Operational transformation for conflict resolution
- User cursor and selection visualization
- Syntax highlighting for screenplay format
- Auto-save with debouncing
- Version history sidebar

**Script Analysis Interface Requirements:**
- Analysis trigger button with quality selector
- Progress visualization during processing
- Streaming results display
- Scene/shot preview generation
- Character extraction display
- Location identification interface

**Quality Tier Selection for Analysis:**
- **Low**: Fast analysis, basic scene detection
- **Standard**: Balanced analysis with character/location extraction
- **High**: Deep analysis with cinematography suggestions

**Node Graph Generation Requirements:**
- Automatic layout from script structure
- Hierarchical scene/shot organization
- Character nodes linked to appearances
- Style suggestions based on genre
- Environment nodes from location descriptions

#### 2. API Endpoint Requirements

**Script Analysis Endpoint Requirements:**
- Accept script content and quality tier parameter
- Queue analysis task to appropriate worker pool:
  - Low: Fast LLM queue with smaller models
  - Standard: Balanced LLM queue
  - High: Premium LLM queue with larger models
- Store task ID for progress tracking
- Return estimated completion time based on quality
- Support partial script analysis

**WebSocket Endpoint Requirements:**
- Handle real-time script editing events
- Stream analysis progress updates
- Broadcast node graph changes
- Manage user presence and cursors
- Support reconnection with state sync

**Script Storage Requirements:**
- Store scripts in project file structure
- Path: `02_Source_Creative/Scripts/`
- Version tracking with Git
- Never expose file paths to frontend
- Use script ID references
    """Handle real-time script collaboration"""
    user = await verify_ws_token(token)
    await script_manager.connect(websocket, project_id, user.id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data['type'] == 'script.edit':
                # Apply operational transformation
                transformed = await apply_ot(project_id, data['payload'])
                
                # Broadcast to other users
                await script_manager.broadcast(
                    project_id,
                    {
                        'type': 'script.change',
                        'payload': transformed,
                        'userId': user.id,
                        'timestamp': datetime.utcnow()
                    },
                    exclude_user=user.id
                )
                
                # Persist change
                await save_script_change(project_id, transformed)
                
    finally:
        script_manager.disconnect(websocket, project_id, user.id)
```

#### 3. Celery Task Processing
```python
@celery_app.task(bind=True, name='script.analyze')
def analyze_script_task(self, project_id: str, script_content: str):
    """Analyze script with progressive result streaming"""
    
    # Parse script into scenes
    scenes = script_parser.extract_scenes(script_content)
    
    # Initialize WebSocket notifications
    ws_notify = WebSocketNotifier(project_id)
    
    # Process scenes in parallel batches
    for i, scene_batch in enumerate(batch(scenes, size=5)):
        # Update progress
        progress = (i * 5) / len(scenes) * 100
        self.update_state(
            state='PROGRESS',
            meta={'current': i * 5, 'total': len(scenes), 'percent': progress}
        )
        
        # Analyze scenes in parallel
        scene_results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for scene in scene_batch:
                future = executor.submit(analyze_single_scene, scene)
                futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                scene_results.append(result)
                
                # Stream result immediately
                ws_notify.send({
                    'type': 'analysis.scene_complete',
                    'scene_id': result['scene_id'],
                    'data': result
                })
        
        # Create assets for completed scenes
        create_scene_assets.delay(project_id, scene_results)
    
    # Generate node graph structure
    graph_data = generate_node_graph(project_id)
    ws_notify.send({
        'type': 'analysis.complete',
        'graph': graph_data
    })
    
    return {'status': 'complete', 'scenes': len(scenes)}

def analyze_single_scene(scene: Dict) -> Dict:
    """Analyze individual scene with LLM"""
    
    # Extract scene metadata
    metadata = {
        'location': scene['header']['location'],
        'time': scene['header']['time'],
        'characters': extract_characters(scene['content'])
    }
    
    # Generate shots using LLM
    shot_prompt = create_shot_generation_prompt(scene)
    shots = llm_client.generate(shot_prompt, model='gpt-4')
    
    # Extract audio requirements
    audio_reqs = analyze_audio_requirements(scene)
    
    return {
        'scene_id': scene['id'],
        'metadata': metadata,
        'shots': shots,
        'audio_requirements': audio_reqs,
        'assets_needed': {
            'characters': metadata['characters'],
            'environment': metadata['location']
        }
    }
```

#### 4. Node Graph Synchronization
**Node Graph Synchronizer Requirements:**
- Handle all node graph changes from analysis
- Validate changes before applying
- Persist to database atomically
- Broadcast updates to all connected clients
- Support node creation from script elements
- Automatic asset node creation
- Link assets by ID references only

**Change Types Supported:**
- Node creation (scenes, shots, assets)
- Node updates (prompts, parameters)
- Node deletion with cascade handling
- Edge creation for asset connections
- Subflow organization for scenes
- Batch operations for efficiency

**Asset Node Generation:**
- Create character nodes from script analysis
- Generate environment nodes for locations
- Suggest style nodes based on genre
- All nodes reference assets by ID
- No file paths exposed to frontend
- Automatic thumbnail generation

### Database Schema Extensions

#### PostgreSQL Schema Requirements for Script Management

**Script Versions Table Requirements:**
- Store complete script content with version history
- Track version numbers sequentially
- Support multiple script formats (Fountain, FDX, PDF)
- User attribution for each version
- Change summaries for version comparison
- File path reference to project structure
- Quality tier used for analysis

**Script Analysis Results Table:**
- Link to specific script version
- Store complete analysis data as JSONB
- Scene breakdown array with metadata
- Quality tier of analysis performed
- Processing time for performance tracking
- Model versions used
- Confidence scores for suggestions

**Collaborative Editing Sessions:**
- Track active users per script
- Store cursor positions for visualization
- Selection ranges for conflict detection
- Activity timestamps for presence
- Session state management
- Connection quality indicators

**Script Assets Tracking:**
- Assets generated from script analysis
- Asset type categorization
- Source scene linkage
- Generation parameters
- Quality tier for asset generation
- References to asset IDs only
- No direct file paths

### Performance Optimizations

#### 1. Progressive Loading
- Stream script analysis results as available
- Lazy load node graph sections for large projects
- Virtualized script editor for long documents
- Incremental asset generation
- Quality-based loading priorities

#### 2. Quality-Tiered Processing
- **Low Quality**: Fast workers with smaller models
- **Standard Quality**: Balanced workers with mid-tier models
- **High Quality**: Premium workers with large models
- Different timeout values per quality tier
- Resource allocation based on quality selection

#### 3. Caching Strategy
- Cache parsed script structures in Redis
- Store frequently accessed analysis results
- CDN delivery for generated assets
- Browser caching for static resources
- Quality-aware cache policies

#### 4. Scalability Measures
- Horizontal scaling of analysis workers per quality tier
- Sharded WebSocket connections
- Database read replicas for queries
- Queue prioritization for active users
- Separate worker pools for each quality level

---

## Success Metrics

### Collaboration Effectiveness
**Primary KPIs:**
- **Concurrent Users**: Average 3+ users per active project
- **Collaboration Time**: 50% reduction in pre-production planning time
- **Revision Cycles**: 40% fewer revision cycles due to real-time collaboration
- **Global Usage**: Users from 25+ countries collaborating on projects

**Measurement Methods:**
- WebSocket connection analytics
- Session overlap tracking
- Time-to-completion metrics
- Geographic distribution analysis

### Analysis Quality and Speed
**Performance Metrics:**
- **Analysis Speed**: <30 seconds for 90-page screenplay
- **Streaming Latency**: First results within 5 seconds
- **Accuracy**: >95% scene detection accuracy
- **Scalability**: Linear performance with added workers

**Quality Metrics:**
- **Shot Appropriateness**: >85% professional approval rating
- **Character Detection**: >92% accurate identification
- **Asset Linking**: >90% correct automatic associations
- **User Satisfaction**: >4.3/5.0 rating

### Technical Performance
**System Metrics:**
- **WebSocket Latency**: <200ms for 95th percentile
- **Sync Reliability**: >99.5% successful synchronization
- **Uptime**: 99.9% availability during business hours
- **Data Integrity**: Zero data loss incidents

**Scalability Metrics:**
- **Concurrent Projects**: Support 1,000+ active projects
- **User Capacity**: 10,000+ concurrent users
- **Analysis Throughput**: 500+ scripts/hour
- **Storage Efficiency**: <10MB per project average

---

## Risk Assessment & Mitigation

### Technical Risks

#### High Risk: Real-Time Sync Complexity
- **Risk**: Synchronization conflicts causing data inconsistency
- **Impact**: Lost work, frustrated users
- **Mitigation**: 
  - Operational transformation algorithms
  - Comprehensive conflict resolution
  - Automatic backup every 60 seconds
  - Client-side recovery mechanisms

#### Medium Risk: LLM Processing Costs
- **Risk**: High computational costs for script analysis
- **Impact**: Unsustainable unit economics
- **Mitigation**:
  - Efficient prompt engineering
  - Result caching for common patterns
  - Tiered service levels
  - Batch processing optimizations

### Business Risks

#### High Risk: Network Dependency
- **Risk**: Poor experience on slow connections
- **Impact**: Limited adoption in some regions
- **Mitigation**:
  - Progressive enhancement design
  - Offline draft capability
  - Regional server deployment
  - Adaptive quality settings

---

## Implementation Roadmap

### Phase 1: Core Web Infrastructure (Weeks 1-4)
**Deliverables:**
- Basic script upload and viewing
- Initial FastAPI endpoints
- Simple WebSocket connection
- Database schema implementation

**Success Criteria:**
- Users can upload and view scripts
- Basic real-time connection established
- Script data persisted correctly

### Phase 2: Collaborative Editing (Weeks 5-8)
**Deliverables:**
- Operational transformation implementation
- Multi-user script editor
- Presence indicators
- Change history tracking

**Success Criteria:**
- Multiple users can edit simultaneously
- No data loss during concurrent edits
- Change history accurately recorded

### Phase 3: AI Analysis Integration (Weeks 9-12)
**Deliverables:**
- LLM integration for script analysis
- Progressive result streaming
- Automatic asset creation
- Node graph generation

**Success Criteria:**
- Scripts analyzed with >90% accuracy
- Results stream in real-time
- Assets created automatically
- Node graph accurately represents structure

### Phase 4: Advanced Features (Weeks 13-16)
**Deliverables:**
- Advanced collaboration features
- Performance optimizations
- Export/import capabilities
- API for external integrations

**Success Criteria:**
- Meeting all performance benchmarks
- Successful load testing at scale
- Complete feature parity with requirements
- API documentation complete

---

## Stakeholder Sign-Off

### Development Team Approval
- [ ] **Frontend Lead** - Svelte Flow integration approved
- [ ] **Backend Lead** - FastAPI/Celery architecture validated
- [ ] **AI/ML Engineer** - LLM integration approach confirmed
- [ ] **DevOps Lead** - Scalability plan approved

### Business Stakeholder Approval
- [ ] **Product Owner** - Collaboration features meet needs
- [ ] **Customer Success** - User workflow validated
- [ ] **Finance** - Infrastructure costs acceptable
- [ ] **Marketing** - Unique value proposition confirmed

---

**Next Steps:**
1. Set up development environment with Docker
2. Implement basic WebSocket infrastructure
3. Create script editor component prototype
4. Design LLM prompt templates
5. Plan user testing for collaboration features

---

*This PRD represents the transformation of script breakdown from a solitary desktop task to a collaborative web experience, enabling global teams to work together in real-time on the foundation of their film projects.*