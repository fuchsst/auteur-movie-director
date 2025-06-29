# Product Requirements Document: Character Consistency Engine

**Version:** 2.0  
**Date:** 2025-01-29  
**Owner:** BMAD Business Analyst  
**Status:** Web Architecture Pivot  
**PRD ID:** PRD-003  
**Dependencies:** Backend Integration Service Layer (PRD-001), Intelligent Script-to-Shot Breakdown System (PRD-002), Style Consistency Framework (PRD-004), Environment Management System (PRD-005), Node-Based Production Canvas (PRD-006), Regenerative Content Model (PRD-007), File-Based Project Structure (PRD-008)

---

## Executive Summary

### Business Justification
The Character Consistency Engine addresses the fundamental barrier in generative filmmaking: maintaining character identity across multiple shots and scenes in a collaborative web environment. This feature transforms the Movie Director from a script processing tool into a genuine character-driven storytelling platform capable of producing professional-quality narrative content through distributed team collaboration.

Character consistency represents the most technically complex and creatively critical challenge in generative film production. Without reliable character identity maintenance, filmmakers cannot create coherent narratives. This engine implements a sophisticated multi-tier approach combining cutting-edge AI models (InfiniteYou, DreamO, OmniGen2) with practical production workflows, all accessible through a web browser with real-time team collaboration.

The system operates on the regenerative content model: users define character parameters once in the PostgreSQL database, and the system maintains that identity across unlimited generations. Character assets exist as parametric definitions with S3 file references to generated content, enabling complete character regeneration at any time while supporting real-time collaborative workflows.

### Target User Personas
- **Distributed Film Teams** - Creating character-driven stories with remote team members
- **Animation Studios** - Developing series with consistent characters across episodes
- **Global Creative Agencies** - Building brand characters with international teams
- **Educational Institutions** - Teaching character development through cloud collaboration
- **Freelance Character Artists** - Creating consistent characters for multiple clients
- **Virtual Production Teams** - Managing digital actors across distributed workflows

### Expected Impact on Film Production Workflow
- **Collaborative Character Development**: Multiple artists refine characters simultaneously
- **Cloud-Based Consistency**: Leverage powerful servers for advanced character models
- **Real-Time Updates**: Character changes instantly visible to all team members
- **Scalable Processing**: Handle multiple character training jobs in parallel
- **Global Asset Library**: Share character assets across projects and teams

---

## Problem Statement

### Current Limitations in Desktop Character Tools
1. **Single-User Character Development**: Character creation locked to individual workstations
2. **No Real-Time Sharing**: Team members work on characters in isolation
3. **Hardware Limitations**: LoRA training requires expensive local GPUs
4. **File Synchronization Issues**: Character asset versions conflict across team
5. **Limited Model Access**: Can't leverage cutting-edge models without local setup

### Pain Points in Web-Based Creative Tools
- **No Advanced Consistency**: Web tools lack sophisticated character consistency
- **Fragmented Asset Management**: Character references scattered across services
- **Poor Team Coordination**: No unified character development workflow
- **Limited Processing Power**: Browser-based tools can't handle complex models
- **No Version Control**: Character iterations lost without proper tracking

### Gaps in Current Web Pipeline
- **Missing Advanced Models**: No access to InfiniteYou, DreamO, OmniGen2
- **No Distributed Training**: Can't leverage cloud GPUs for LoRA training
- **Limited Real-Time Preview**: Character updates not instantly visible
- **Poor Cross-Project Sharing**: Characters locked to single projects

---

## Solution Overview

### Feature Description within Web Architecture
The Character Consistency Engine leverages the distributed web architecture to provide collaborative character development with advanced AI models. Using Function Runner for heterogeneous model execution and Celery for distributed processing, teams can develop, train, and maintain consistent characters across entire productions with real-time synchronization.

**Core Capabilities:**
1. **Collaborative Character Gallery** - Real-time shared character asset library
2. **Cloud-Based Model Training** - Distributed LoRA training on GPU workers
3. **Advanced Model Integration** - InfiniteYou, DreamO, OmniGen2 via Function Runner
4. **Live Character Preview** - Instant visual updates across all clients
5. **Quality-Tiered Consistency** - Three levels of character quality
6. **Version History** - Complete character evolution tracking
7. **Cross-Project Templates** - Share characters across productions
8. **Team Annotations** - Collaborative notes and feedback on characters
9. **Batch Variation Generation** - Create multiple poses/expressions in parallel
10. **API Access** - Integrate character assets with external tools
11. **Git LFS Integration** - Version control for character assets
12. **File Structure Compliance** - Organized in project hierarchy

**Quality Tier Specifications:**
- **Low Quality**: Basic character consistency with IPAdapter, fast generation
- **Standard Quality**: Enhanced consistency with LoRA or InstantID, balanced
- **High Quality**: Maximum consistency with InfiniteYou/DreamO, best results

### Integration with Advanced Models
**Function Runner Model Support:**
- **InfiniteYou**: Zero-shot identity preservation on FLUX
- **DreamO**: Unified identity, try-on, and style transfer
- **OmniGen2**: Multi-modal character generation from complex prompts
- **Traditional Models**: LoRA training, IPAdapter, InstantID as fallbacks

**Distributed Processing Benefits:**
- Parallel character training across multiple GPU workers
- Real-time progress updates to all team members
- Automatic model selection based on hardware availability
- Seamless fallback to simpler models when needed

### Backend Service Architecture
**FastAPI Endpoints:**
- Character CRUD operations with team permissions
- Training job submission and monitoring
- Character validation and consistency scoring
- Gallery management and sharing

**Celery Task Processing:**
- Distributed LoRA training on GPU clusters
- Quality-based queue routing for character tasks
- Parallel processing for batch variations
- Progress streaming to all connected clients

**File Storage Integration:**
- Characters stored in `01_Assets/Generative_Assets/Characters/`
- Reference images in standardized subdirectories
- Model files tracked with Git LFS
- Metadata in version-controlled JSON files
- Parallel character variation generation
- Batch consistency validation
- Model optimization and compression

**WebSocket Events:**
- Real-time character preview updates
- Training progress streaming
- Gallery synchronization
- Team collaboration events

---

## User Stories & Acceptance Criteria

### Epic 1: Collaborative Character Development
**As a character design team, we want to develop characters together in real-time so that we maintain consistent vision across our production.**

#### User Story 1.1: Shared Character Gallery
- **Given** multiple team members working on a project
- **When** one member creates or updates a character
- **Then** all team members see the change immediately
- **And** can access the same character reference images
- **And** see who made what changes and when
- **And** can revert to previous versions if needed

**Acceptance Criteria:**
- Real-time gallery synchronization <500ms
- Version history with visual diff
- User attribution for all changes
- Rollback capability with team notification

#### User Story 1.2: Collaborative Character Refinement
- **Given** a team has created initial character concepts
- **When** they want to refine character details together
- **Then** multiple users can annotate character images
- **And** suggest variations and improvements
- **And** vote on preferred character versions
- **And** see consensus emerging in real-time

**Acceptance Criteria:**
- Multi-user annotation system
- Variation suggestion workflow
- Voting/approval mechanism
- Real-time consensus visualization

### Epic 2: Cloud-Based Advanced Model Integration
**As a filmmaker, I want to use cutting-edge character consistency models without local setup so that I can achieve the best possible results.**

#### User Story 2.1: InfiniteYou Integration
- **Given** I have character reference images
- **When** I select InfiniteYou for character generation
- **Then** the system uses Function Runner to execute the model
- **And** maintains character identity with zero-shot learning
- **And** streams results back to all team members
- **And** handles the complex model dependencies automatically

**Acceptance Criteria:**
- Successful InfiniteYou model execution via Function Runner
- >90% identity preservation accuracy
- Results streaming to all connected clients
- Automatic dependency management

#### User Story 2.2: Intelligent Model Selection
- **Given** different characters with varying importance levels
- **When** I generate character content
- **Then** the system automatically selects the best model
- **And** considers available resources and queue depth
- **And** falls back gracefully if advanced models are busy
- **And** notifies me of the model being used

**Acceptance Criteria:**
- Automatic model selection based on character importance
- Resource-aware scheduling
- Graceful fallback mechanism
- Clear model selection feedback

### Epic 3: Distributed Character Training
**As a production team, we want to train custom character models in the cloud so that we don't need expensive local hardware.**

#### User Story 3.1: Cloud LoRA Training
- **Given** I have collected character reference images
- **When** I initiate LoRA training
- **Then** the job is distributed to available GPU workers
- **And** progress updates stream to all team members
- **And** the trained model is automatically available upon completion
- **And** training can be monitored from any device

**Acceptance Criteria:**
- Distributed training across GPU workers
- Real-time progress updates via WebSocket
- Automatic model deployment on completion
- Cross-device monitoring capability

#### User Story 3.2: Training Queue Management
- **Given** multiple team members submitting training jobs
- **When** resources are limited
- **Then** jobs are intelligently prioritized
- **And** users see their position in queue
- **And** can adjust priority based on urgency
- **And** receive notifications when training starts/completes

**Acceptance Criteria:**
- Fair queue management algorithm
- Queue position visibility
- Priority adjustment system
- Multi-channel notifications

### Epic 4: Character Variation Generation
**As a creative team, we want to generate multiple character variations efficiently so that we can explore different options quickly.**

#### User Story 4.1: Batch Variation Generation
- **Given** I have a base character defined
- **When** I request variations (poses, expressions, outfits)
- **Then** the system generates multiple options in parallel
- **And** displays them in a comparison grid
- **And** allows team voting on preferred variations
- **And** integrates selected variations into the character asset

**Acceptance Criteria:**
- Parallel generation of 10+ variations
- Grid-based comparison interface
- Team voting mechanism
- Seamless integration of selections

#### User Story 4.2: Context-Aware Variations
- **Given** characters assigned to specific scenes
- **When** generating variations
- **Then** the system considers scene context
- **And** generates appropriate expressions/poses
- **And** maintains consistency with scene mood
- **And** suggests variations based on script analysis

**Acceptance Criteria:**
- Scene context integration
- Mood-appropriate generation
- Script-based suggestions
- Consistency validation

### Epic 5: Cross-Project Character Sharing
**As a studio, we want to reuse characters across projects so that we can build a library of consistent digital actors.**

#### User Story 5.1: Character Templates
- **Given** I have developed characters in one project
- **When** I want to use them in another project
- **Then** I can export characters as templates
- **And** import them into new projects
- **And** maintain all consistency parameters
- **And** track character usage across projects

**Acceptance Criteria:**
- Character export/import functionality
- Parameter preservation
- Cross-project usage tracking
- Template versioning

#### User Story 5.2: Studio Character Library
- **Given** our studio has created many characters
- **When** starting new projects
- **Then** we can browse our character library
- **And** filter by attributes and tags
- **And** see usage statistics
- **And** maintain character licensing info

**Acceptance Criteria:**
- Centralized character library
- Advanced filtering and search
- Usage analytics
- Licensing management

---

## Technical Requirements

### Web Application Architecture

#### 1. Frontend Component Requirements

**Character Gallery Component Requirements:**
- Real-time synchronization of character assets
- WebSocket connection for live updates
- Display character thumbnails with metadata
- Quality tier indicators (Low/Standard/High)
- Training status visualization
- Batch selection for operations
- Drag-and-drop to Production Canvas
- Reference characters by ID only

**Character Creation Interface Requirements:**
- Multiple reference image upload
- Automatic image validation
- Quality tier selection:
  - Low: Basic consistency, 5+ images
  - Standard: Enhanced consistency, 10+ images
  - High: Maximum consistency, 20+ images
- Metadata input (name, age, traits)
- Real-time preview generation
- Team collaboration features

**Training Monitor Requirements:**
- Live progress tracking for all training jobs
- Queue position display
- Resource usage visualization
- Time estimation based on quality tier
- Cancel/pause functionality
- Multi-character batch training
- Success/failure notifications

#### 2. API Endpoint Requirements

**Character Training Endpoint Requirements:**
- Accept character ID and quality tier parameter
- Validate reference image count based on tier:
  - Low: Minimum 5 images
  - Standard: Minimum 10 images
  - High: Minimum 20 images
- Queue to appropriate worker pool:
  - Low: Fast training with basic model
  - Standard: Balanced training with LoRA
  - High: Premium training with advanced techniques
- Calculate priority based on user tier and urgency
- Store training job metadata
- Broadcast start notification to team
- Return job ID and estimated time

**Advanced Model Generation Endpoints:**
- Support multiple model backends:
  - InfiniteYou for zero-shot consistency
  - DreamO for unified identity operations
  - OmniGen2 for multi-modal generation
- Quality-based model selection:
  - Low: IPAdapter or basic LoRA
  - Standard: Fine-tuned LoRA or InstantID
  - High: InfiniteYou or DreamO
- Handle fallback when models unavailable
- Stream progress updates via WebSocket following draft4_canvas.md protocol
- Route tasks to appropriate quality-based worker pools
- Handle model fallback automatically
- Support batch character generation

#### 3. Function Runner Integration Requirements

**Advanced Model Execution:**
- Execute models in isolated Docker containers
- Support for multiple model repositories:
  - InfiniteYou for zero-shot consistency
  - DreamO for unified identity operations
  - OmniGen2 for multi-modal generation
- Quality-based container selection
- Workflow orchestration for multi-step processes

**Container Configuration per Quality:**
- **Low Quality**:
  - Basic models container
  - Minimal resource allocation
  - Fast execution priority
  
- **Standard Quality**:
  - Balanced models container
  - Standard resource allocation
  - Normal execution priority
  
- **High Quality**:
  - Premium models container
  - Maximum resource allocation
  - Extended execution timeouts

**Distributed Training Architecture:**
- Multi-GPU support for large models
- Automatic data distribution
- Training strategy based on resources:
  - Single GPU for low quality
  - Multi-GPU for standard/high
- Progress tracking across workers
- Model optimization per quality tier
- Automatic deployment to storage

#### 4. WebSocket Protocol for Character Collaboration

**Character-Specific Events (extending draft4_canvas.md):**

| Event Name | Direction | Payload Schema | Description |
|------------|-----------|----------------|-------------|
| `client:character.update` | C → S | `{"character_id": "...", "data": {...}}` | Character property updates |
| `client:character.train` | C → S | `{"character_id": "...", "quality": "standard"}` | Initiate training job |
| `client:character.generate` | C → S | `{"character_id": "...", "params": {...}}` | Generate character variation |
| `server:character.updated` | S → C | `{"character_id": "...", "data": {...}}` | Character state changes |
| `server:training.progress` | S → C | `{"job_id": "...", "progress": 45, "step": "..."}` | Training progress updates |
| `server:training.complete` | S → C | `{"job_id": "...", "character_id": "...", "model_url": "..."}` | Training completion |
| `server:generation.result` | S → C | `{"character_id": "...", "variation_id": "...", "image_url": "..."}` | Generation results |

**Real-time Collaboration Requirements:**
- Database as authoritative source following draft4_canvas.md
- Optimistic updates with server confirmation
- Conflict resolution for simultaneous character edits
- Automatic preview generation on character updates
- Team notification for training job status changes

### Database Schema Requirements

#### PostgreSQL Tables for Character Management

**Characters Table (extending PRD-001 assets table):**
- UUID primary key for character identification
- Project ID foreign key following PRD-008 structure
- Character metadata (name, description, importance score)
- Consistency tier (low/standard/high)
- Script character linkage for PRD-002 integration
- Quality tier parameters for regeneration
- User attribution and collaboration tracking
- File path references (no direct paths exposed)

**Character Training Jobs Table:**
- Training job lifecycle management
- Queue priority and status tracking
- Quality tier and resource requirements
- Progress tracking for WebSocket updates
- User attribution and team notifications
- Parameters storage for regeneration capability
- Results and model artifact references

**Character Variations Table:**
- Generated character variations and expressions
- Quality tier used for generation
- Model and parameters for regeneration
- Team voting and approval tracking
- File references via S3/storage service
- Integration with node graph system

**Character Collaboration Table:**
- Team annotations and feedback
- Real-time cursor and selection tracking
- Change attribution and version history
- Conflict resolution state management
- Activity timestamps for presence

**Character Templates Table:**
- Cross-project character sharing
- Complete regeneration parameters
- Usage tracking and analytics
- Public/private sharing permissions
- Version control for template evolution

### Celery Task System Integration

#### 1. Quality-Tiered Task Processing
**Task Queue Configuration (following draft4_filestructure.md VRAM tiers):**
- **Low Quality Queue** (`character_low`): Basic consistency models
- **Standard Quality Queue** (`character_standard`): LoRA training and InstantID
- **High Quality Queue** (`character_high`): InfiniteYou, DreamO, OmniGen2

**Character-Specific Celery Tasks:**
- `character.train_lora` - Distributed LoRA training on GPU workers
- `character.generate_variation` - Create character variations with consistency
- `character.validate_consistency` - Quality validation across shots
- `character.optimize_model` - Post-training optimization and compression
- `character.deploy_model` - Deploy trained models to storage

#### 2. Function Runner Integration
**Advanced Model Execution:**
- InfiniteYou for zero-shot character consistency
- DreamO for unified identity and style transfer
- OmniGen2 for multi-modal character generation
- Automatic model selection based on quality tier
- Graceful fallback to traditional models

**Container Architecture per Quality Tier:**
- Isolated Docker environments for each model
- Quality-specific resource allocation
- Automatic dependency management
- Progress streaming via WebSocket events

#### 3. Performance and Scalability
**Training Optimization:**
- Multi-GPU distributed training for high quality
- Checkpoint-based resumption for reliability
- Priority queue management for team coordination
- Automatic scaling based on demand

**Real-time Synchronization:**
- WebSocket connection pooling and load balancing
- Differential updates for character changes
- Optimistic UI updates with server confirmation
- Conflict resolution for simultaneous edits

**Caching Strategy:**
- Character preview caching with CDN delivery
- Model artifact caching for faster deployment
- Reference image optimization and compression
- Lazy loading for large character galleries

---

## Success Metrics

### Celery Task System Performance
**Task Processing Metrics:**
- **Training Queue Throughput**: 100+ concurrent LoRA training jobs
- **Generation Speed**: <3 minutes per character variation
- **Queue Latency**: <30 seconds from submission to start
- **Success Rate**: >98% successful task completion
- **Resource Utilization**: >80% GPU efficiency across quality tiers

**Quality Tier Performance:**
- **Low Quality**: <15 minutes LoRA training, 95% success rate
- **Standard Quality**: <60 minutes LoRA training, 92% success rate
- **High Quality**: <120 minutes advanced model training, 88% success rate
- **Fallback Rate**: <15% quality degradation when resources constrained

### Real-time Collaboration Metrics
**WebSocket Protocol Compliance:**
- **Event Latency**: <200ms for character updates (draft4_canvas.md requirement)
- **Synchronization Success**: >99.5% successful character state sync
- **Connection Resilience**: <5 second recovery from disconnections
- **Concurrent Users**: Support 100+ users per character gallery

**Character Consistency Quality:**
- **Visual Similarity**: >90% consistency score across shots
- **Identity Preservation**: >85% with InfiniteYou integration
- **Cross-Shot Coherence**: >92% character recognition accuracy
- **Professional Standards**: Meet broadcast quality requirements

### Integration Architecture Performance
**Cross-System Integration:**
- **Script Integration** (PRD-002): Automatic character creation from analysis
- **Canvas Integration** (PRD-006): Character nodes appear within 2 seconds
- **Style Integration** (PRD-004): Consistent style application across characters
- **Storage Integration** (PRD-008): 100% path resolution compliance

**Advanced Model Integration:**
- **Function Runner Success**: >90% successful advanced model execution
- **Model Selection Accuracy**: >95% optimal model choice for quality tier
- **Container Performance**: <30 second startup for advanced models
- **Resource Management**: Proper VRAM allocation per draft4_filestructure.md

---

## Architectural Compliance Requirements

### Draft4_Canvas.md Integration
**WebSocket Protocol Implementation:**
- Extend core event schema with character-specific events
- Implement ConnectionManager for character gallery sessions
- Support real-time character updates with optimistic UI
- Handle training progress streaming to all connected clients
- Maintain database as authoritative source of truth

### Draft4_Filestructure.md Compliance
**File Storage Integration:**
- Store characters in `01_Assets/Generative_Assets/Characters/` directory
- Follow atomic versioning for character model files
- Never expose file paths to frontend - use character IDs only
- Integrate with Git LFS for large model files
- Support VRAM-tier routing for training tasks

### Celery Task System Architecture
**Quality-Based Queue Management:**
- Route training tasks to appropriate VRAM-tier workers
- Implement Producer agent intelligence for resource allocation
- Support automatic fallback when premium workers unavailable
- Provide transparent quality adjustment notifications
- Handle distributed training across multiple GPU workers

### Cross-PRD Dependencies
**Integration Requirements:**
- **PRD-001**: Backend service layer and WebSocket protocol
- **PRD-002**: Character creation from script analysis
- **PRD-004**: Style consistency application to characters
- **PRD-005**: Environment integration for character contexts
- **PRD-006**: Character node representation in production canvas
- **PRD-007**: Regenerative parameters for character recreation
- **PRD-008**: File structure and path management compliance

---

## Implementation Validation

### Core Architecture Validation
**Celery Task Integration:**
- Validate quality-tier queue routing works correctly
- Test distributed LoRA training across multiple GPU workers
- Ensure training progress streams properly via WebSocket
- Verify automatic model deployment to storage service
- Test graceful fallback when advanced models unavailable

**WebSocket Protocol Compliance:**
- Implement character-specific events extending draft4_canvas.md Table 4
- Test real-time character gallery synchronization
- Validate training progress streaming to all connected clients
- Ensure conflict resolution for simultaneous character edits
- Test automatic reconnection with state synchronization

**Function Runner Integration:**
- Validate InfiniteYou, DreamO, OmniGen2 execution via containers
- Test automatic model selection based on quality tier
- Ensure proper resource allocation per VRAM requirements
- Validate progress tracking across heterogeneous models
- Test error handling and fallback mechanisms

### Cross-System Integration Testing
**Character Creation Pipeline:**
- Script analysis triggers character asset creation (PRD-002)
- Characters appear correctly in production canvas (PRD-006)
- Style frameworks apply consistently to characters (PRD-004)
- Environment contexts integrate properly (PRD-005)
- All data follows regenerative content model (PRD-007)
- File operations respect project structure (PRD-008)

**Real-time Collaboration:**
- Multi-user character editing without conflicts
- Training job coordination across team members
- Character variations shared instantly
- Team annotations and feedback systems
- Cross-project character template sharing

### Performance Validation
**Training Performance:**
- Load testing with 100+ concurrent training jobs
- VRAM allocation efficiency across quality tiers
- Training time benchmarks per quality level
- Resource utilization monitoring
- Queue management under high load

**Character Generation:**
- Batch variation generation performance
- Real-time preview updates across clients
- Character consistency validation
- Model selection accuracy testing
- Storage and CDN performance optimization

---

## Architecture Alignment Summary

### Draft4_Canvas.md Compliance
✅ **WebSocket Protocol**: Extended event schema with character-specific events  
✅ **State Management**: Database authoritative with optimistic character updates  
✅ **Connection Management**: Per-project character gallery sessions  
✅ **Real-time Sync**: Training progress and character updates <200ms  
✅ **Conflict Resolution**: Simultaneous character editing with operational transformation  

### Draft4_Filestructure.md Integration
✅ **VRAM Management**: Quality-tier routing for training tasks  
✅ **File Storage**: Characters in `01_Assets/Generative_Assets/Characters/`  
✅ **Path Resolution**: ID-based references with no exposed file paths  
✅ **Git LFS**: Large model files tracked automatically  
✅ **Atomic Versioning**: Character model files with proper naming  

### Celery Task System Architecture
✅ **Quality-Based Queues**: character_low, character_standard, character_high  
✅ **Distributed Training**: Multi-GPU LoRA training with progress streaming  
✅ **Function Runner**: Advanced models (InfiniteYou, DreamO, OmniGen2)  
✅ **Producer Intelligence**: Automatic resource allocation and fallback  
✅ **Progress Tracking**: Real-time updates via WebSocket events  

### Cross-PRD Integration Points
✅ **Script Analysis** (PRD-002): Automatic character creation from analysis  
✅ **Style Framework** (PRD-004): Consistent style application to characters  
✅ **Environment Integration** (PRD-005): Character-environment context handling  
✅ **Production Canvas** (PRD-006): Character nodes in visual workflow  
✅ **Regenerative Model** (PRD-007): Character parameters for recreation  
✅ **File Structure** (PRD-008): Complete project organization compliance  

---

**Character Engine Foundation:**
This PRD successfully establishes the Character Consistency Engine as a distributed, collaborative system that integrates seamlessly with the Movie Director platform architecture while providing professional-grade character development capabilities through advanced AI models and real-time team coordination.

---

*Character consistency evolves from desktop limitation to cloud-powered collaboration, enabling global teams to create and maintain professional digital actors through distributed AI processing and real-time synchronization.*