# Product Requirements Document: Backend Integration Service Layer

**Version:** 2.1  
**Date:** 2025-01-29  
**Owner:** BMAD Business Analyst  
**Status:** Web Architecture Pivot  
**PRD ID:** PRD-001  
**Dependencies:** PRD-008 (File-Based Project Structure)  

---

## Executive Summary

### Business Justification
The Backend Integration Service Layer transforms the Movie Director from a conceptual framework into a fully functional web-based generative film studio. This layer serves as the critical bridge between the browser-based user interface and powerful AI generation backends (ComfyUI, Wan2GP, heterogeneous model repositories), enabling users to create professional-quality video content through any modern web browser without installation barriers.

This foundation layer directly enables the regenerative content model that defines the entire platform: users define project parameters once in the database, while the backend service layer orchestrates unlimited content generation and regeneration from those stored definitions. This architectural approach ensures project portability, collaborative workflows, and eliminates the traditional file management burden of generative workflows.

### Target User Personas
- **Independent Filmmakers** - Creating short films and concept videos collaboratively from anywhere
- **Content Creation Teams** - Distributed teams producing high-quality video content together
- **Concept Artists** - Visualizing ideas for pre-production with real-time client feedback
- **Advertising Agencies** - Rapid prototyping with multiple stakeholders reviewing simultaneously
- **Educational Institutions** - Teaching film production with cloud-based collaborative tools
- **Enterprise Studios** - Scaling production capacity with distributed compute resources

### Expected Impact on Film Production Workflow
- **Accessibility Revolution**: Enable creation from any device with a web browser
- **Collaborative Transformation**: Real-time multi-user editing and review capabilities
- **Scalability Breakthrough**: Dynamically scale compute resources based on demand
- **Cost Optimization**: Pay-per-use model eliminates need for expensive local hardware
- **Market Expansion**: Reach users who cannot invest in high-end local GPU setups

---

## Problem Statement

### Current Limitations in Desktop-Based Production
1. **Hardware Barriers**: Requires expensive local GPU hardware (RTX 4080+ minimum)
2. **Installation Complexity**: Complex setup of multiple backend services and dependencies
3. **Single-User Limitation**: No real-time collaboration or remote review capabilities
4. **Platform Lock-In**: Limited to specific operating systems and hardware configurations
5. **Maintenance Burden**: Users must manage updates and compatibility across services

### Pain Points in Existing Web Workflows
- **Fragmented Services**: Current web tools are disconnected point solutions
- **No Unified Interface**: Artists juggle multiple browser tabs and services
- **Limited Asset Management**: No integrated system for managing generative assets
- **Poor Collaboration**: File-based sharing instead of real-time cooperation
- **No Version Control**: Difficult to track iterations and revert changes

### Gaps in Current Generative Pipeline
- **No Distributed Processing**: Cannot leverage cloud compute for resource-intensive tasks
- **Limited Scalability**: Single-machine bottleneck for complex productions
- **No Real-Time Updates**: Collaborators cannot see work in progress
- **Poor Resource Utilization**: Idle local GPUs while waiting for other tasks

---

## Solution Overview

### Feature Description within Web Architecture
The Backend Integration Service Layer implements a modern, distributed architecture using FastAPI for the API gateway, Celery for task orchestration, and WebSockets for real-time communication. This service layer acts as the intelligent orchestrator of the generative film studio, coordinating between the web UI, specialized processing workers, and external AI services.

**Core Components:**
1. **FastAPI Gateway** - RESTful API and WebSocket server for client communication
2. **Celery Task Orchestration** - Distributed task queue with Redis message broker
3. **Function Runner System** - Heterogeneous model execution for standalone repositories
4. **Worker Pool Management** - GPU/CPU worker allocation and load balancing
5. **Real-Time Event System** - WebSocket protocol for live updates and collaboration
6. **File Storage Service** - S3-compatible object storage for generated assets
7. **Metadata Database** - PostgreSQL for project state and regenerative parameters
8. **Project Structure Service** - Automated project scaffolding and file management
9. **Path Resolution Service** - Centralized file path handling for all operations
10. **Git Integration Service** - Version control operations and history tracking
11. **Quality-Based Pipeline Architecture** - Three-tier model selection system
12. **VRAM Budget Management** - Intelligent memory allocation and model swapping

### Distributed Processing Architecture
- **GPU Worker Pools**: Specialized Celery workers for ComfyUI, Wan2GP, and custom models
- **CPU Worker Pools**: Dedicated workers for video assembly, audio processing, and file operations
- **Function Runner Workers**: Isolated Docker containers for arbitrary Python model execution
- **Auto-Scaling**: Dynamic worker scaling based on queue depth and resource availability
- **Load Balancing**: Intelligent task routing based on worker capabilities and current load

### Real-Time Collaboration Features
- **Live Canvas Updates**: WebSocket events for node graph modifications
- **Progress Broadcasting**: Real-time generation progress to all connected clients
- **Collaborative Editing**: Multiple users can work on same project simultaneously
- **Change Notifications**: Instant updates when team members modify assets or settings
- **Presence Awareness**: See which team members are active and what they're working on

---

## User Stories & Acceptance Criteria

### Epic 1: Web-Based Access and Authentication
**As a filmmaker, I want to access the movie director from any web browser so that I can work from anywhere without installation.**

#### User Story 1.1: Browser-Based Access
- **Given** I have a modern web browser (Chrome, Firefox, Safari, Edge)
- **When** I navigate to the Movie Director URL
- **Then** the application loads without plugins or downloads
- **And** I see the login/registration screen
- **And** the UI is responsive to my screen size

#### User Story 1.2: User Authentication and Projects
- **Given** I have registered an account
- **When** I log in with my credentials
- **Then** I see my project dashboard
- **And** can create new projects or open existing ones
- **And** my projects are securely isolated from other users

### Epic 2: Distributed Task Execution
**As a content creator, I want my generation tasks to run on powerful cloud servers so that I don't need expensive local hardware.**

#### User Story 2.1: Cloud-Based Generation
- **Given** I have created a shot node with generation parameters
- **When** I click "Generate"
- **Then** the task is queued to available GPU workers
- **And** I see real-time progress updates via WebSocket
- **And** the generated content appears in my canvas when complete
- **And** other team members see the same updates in real-time

#### User Story 2.2: Function Runner Integration
- **Given** I want to use a cutting-edge model like FlexiAct or LoRAEdit
- **When** I connect it to my shot node
- **Then** the Function Runner creates an isolated environment
- **And** executes the model's multi-step Python workflow
- **And** handles all dependencies and file paths automatically
- **And** returns results seamlessly to the main workflow

### Epic 3: Real-Time Collaboration
**As a creative team, we want to work together on the same project simultaneously so that we can iterate faster.**

#### User Story 3.1: Collaborative Canvas Editing
- **Given** multiple team members have the project open
- **When** one member adds or modifies a node
- **Then** all other members see the change within 500ms
- **And** the change is properly synchronized without conflicts
- **And** each user's cursor/selection is visible to others

#### User Story 3.2: Shared Asset Management
- **Given** team members are working with character and style assets
- **When** one member creates or updates an asset
- **Then** it immediately appears in all users' asset libraries
- **And** usage tracking shows who created/modified each asset
- **And** version history is maintained for rollback

### Epic 4: Scalable Resource Management
**As a production studio, I want to scale processing power based on demand so that we can handle variable workloads efficiently.**

#### User Story 4.1: Auto-Scaling Workers
- **Given** multiple users are generating content simultaneously
- **When** the task queue exceeds threshold depth
- **Then** the system automatically provisions additional workers
- **And** new tasks are distributed across available workers
- **And** workers are decommissioned when queue empties

#### User Story 4.2: Heterogeneous Model Support
- **Given** I want to use models from different repositories and frameworks
- **When** I add a new model via Function Runner configuration
- **Then** the system creates appropriate Docker container
- **And** manages all dependencies and environment setup
- **And** integrates seamlessly with existing workflow nodes

---

## Technical Requirements

### Node Type Specifications

#### Input/Output Socket Types
**Core Socket Types:**
- **Image**: Single image data (PNG, JPEG, WebP)
- **Video**: Video clip data (MP4, MOV, WebM)
- **Audio**: Audio track data (WAV, MP3, AAC)
- **Text**: String data for prompts and descriptions
- **Number**: Numeric values for parameters
- **Boolean**: True/false flags
- **Asset Reference**: ID-based reference to project assets
- **Style Parameters**: Complex style configuration object
- **Camera Data**: Camera position and movement information

**Node Categories:**
1. **Generation Nodes**
   - Shot Generation (Text → Video)
   - Image Generation (Text → Image)
   - Audio Generation (Text → Audio)
   - Voice Synthesis (Text + Character → Audio)

2. **Processing Nodes**
   - Style Transfer (Video + Style → Video)
   - Upscale (Video → Video)
   - Transition (Video + Video → Video)
   - Composite (Video + Video + Mask → Video)

3. **Asset Nodes**
   - Character Reference (Character ID → Image Set)
   - Style Reference (Style ID → Parameters)
   - Environment Reference (Location ID → Background)

4. **Control Nodes**
   - Pipeline Node (Configuration → Workflow)
   - Conditional (Boolean → Route Selection)
   - Loop Controller (Number → Iteration Count)

### Web Application Architecture

#### 1. Frontend Integration (SvelteKit)
- **Framework**: SvelteKit with server-side rendering for performance
- **State Management**: Svelte stores for reactive UI updates
- **Real-Time**: Native WebSocket integration for live updates
- **Node Editor**: Svelte Flow for visual workflow editing
- **Asset Management**: Drag-and-drop asset library with preview

#### 2. API Gateway (FastAPI)
```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Movie Director API")

# REST endpoints for CRUD operations
@app.post("/api/projects/{project_id}/generate")
async def generate_content(project_id: str, node_id: str, params: GenerationParams):
    """Queue generation task to Celery workers"""
    task = celery_app.send_task(
        'generate.video',
        args=[project_id, node_id, params.dict()],
        queue='gpu_heavy'
    )
    return {"task_id": task.id, "status": "queued"}

# WebSocket for real-time updates
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """Handle real-time collaboration and progress updates"""
    await connection_manager.connect(websocket, project_id)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_client_event(project_id, data)
    finally:
        connection_manager.disconnect(websocket, project_id)
```

#### 3. Task Orchestration (Celery)

**Quality-Based Queue Configuration:**
- **Low Quality Queue**: Fast processing with smaller models (SD 1.5, etc.)
- **Standard Queue**: Balanced processing (Flux Schnell, etc.)
- **High Quality Queue**: Premium processing (Flux Dev FP16, etc.)

**VRAM Budget Management:**
- Dynamic profiling of model memory requirements
- Sequential execution for memory-constrained environments
- Model unloading/swapping to prevent OOM errors
- Priority-based resource allocation

```python
from celery import Celery
from celery.signals import task_prerun, task_postrun

celery_app = Celery('movie_director', broker='redis://localhost:6379')

@celery_app.task(bind=True, name='generate.video')
def generate_video_task(self, project_id, node_id, params):
    """Execute video generation with progress updates"""
    # Get project paths
    paths = ProjectPaths(WORKSPACE_ROOT)
    project = get_project_sync(project_id)
    project_root = paths.get_project_root(project.name)
    
    # Resolve asset paths for generation
    path_service = PathResolutionService(WORKSPACE_ROOT)
    if params.get('character_id'):
        char_path = path_service.resolve_asset_path_sync(
            project_id, 'character', params['character_id']
        )
        params['character_files'] = list(char_path.glob('reference_images/*'))
    
    # Select optimal backend
    backend = select_backend(params['complexity'], params['requirements'])
    
    # Send progress via WebSocket
    def progress_callback(percent, message):
        send_websocket_event(project_id, {
            'type': 'progress',
            'node_id': node_id,
            'percent': percent,
            'message': message
        })
    
    # Execute generation
    result = backend.generate(params, progress_callback)
    
    # Store output in project structure
    scene = params.get('scene', 'SCENE_01')
    shot = params.get('shot', 'SHOT_001')
    version = params.get('version', 1)
    take = get_next_take_number(project_root, scene, shot, version)
    
    output_path = paths.get_shot_render_path(
        project_root, scene, shot, version, take
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Move generated file to correct location
    shutil.move(result['temp_path'], output_path)
    
    # Update result with proper path
    result['output_path'] = str(output_path)
    result['take_number'] = take
    
    # Store result and notify
    store_generated_asset(project_id, node_id, result)
    send_websocket_event(project_id, {
        'type': 'generation_complete',
        'node_id': node_id,
        'output_path': str(output_path.relative_to(project_root)),
        'take_number': take
    })
    
    # Auto-commit if enabled
    if params.get('auto_commit', True):
        git_service = GitIntegrationService()
        git_service.commit_changes_sync(
            project_id, 
            f"Generated {scene}/{shot} take {take}",
            params['user_id']
        )
    
    return result
```

#### 4. Function Runner System
```python
class FunctionRunner:
    """Execute arbitrary model repositories in isolated environments"""
    
    def __init__(self, docker_client):
        self.docker = docker_client
        self.containers = {}
        self.supported_node_types = {
            'shot_generation': self.run_shot_model,
            'transition': self.run_transition_model,
            'combine_overlay': self.run_composite_model,
            'style_transfer': self.run_style_model,
            'upscale': self.run_upscale_model
        }
    
    async def run_model(self, model_config, inputs, node_type='shot_generation'):
        """Run a model based on node type with appropriate input/output handling"""
        
        # Validate inputs based on node type
        self.validate_inputs(inputs, node_type)
        
        # Execute appropriate handler
        handler = self.supported_node_types.get(node_type)
        if not handler:
            raise ValueError(f"Unsupported node type: {node_type}")
        
        return await handler(model_config, inputs)
    
    def validate_inputs(self, inputs, node_type):
        """Validate input types for specific node"""
        required_inputs = {
            'shot_generation': {
                'image_paths': list,      # Reference images
                'prompt': str,            # Text prompt
                'parameters': dict,       # Model parameters
                'quality': str           # Quality tier (low/standard/high)
            },
            'transition': {
                'video_a': str,           # Path to first video
                'video_b': str,           # Path to second video
                'duration': float,        # Transition duration
                'type': str,             # Transition type (fade, wipe, etc.)
                'quality': str           # Quality tier for transition
            },
            'combine_overlay': {
                'base_media': str,        # Base image/video path
                'overlay_media': str,     # Overlay image/video path
                'mask': str,             # Optional mask path
                'blend_mode': str,       # Blend mode (multiply, screen, etc.)
                'opacity': float,        # Overlay opacity
                'quality': str           # Quality tier for compositing
            },
            'style_transfer': {
                'content_media': str,     # Content image/video path
                'style_reference': str,   # Style reference path
                'strength': float,        # Style strength (0-1)
                'quality': str           # Quality tier
            },
            'upscale': {
                'input_media': str,       # Input image/video path
                'scale_factor': int,      # Upscale factor (2, 4, etc.)
                'model': str,            # Upscale model selection
                'quality': str           # Quality tier
            }
        }
        
        # Check required inputs exist
        for key, expected_type in required_inputs.get(node_type, {}).items():
            if key not in inputs:
                raise ValueError(f"Missing required input: {key}")
            if not isinstance(inputs[key], expected_type):
                raise TypeError(f"Input {key} must be {expected_type}")
    
    async def run_shot_model(self, model_config, inputs):
        """Generate shot from prompts and references"""
        container = await self.get_or_create_container(model_config)
        
        # Standard shot generation with Docker image
        volumes = {
            inputs['image_paths'][0].parent: {'bind': '/inputs', 'mode': 'ro'},
            '/tmp/outputs': {'bind': '/outputs', 'mode': 'rw'}
        }
        
        # For development: run locally, for production: deploy to cloud
        if model_config.get('local_dev', True):
            result = container.exec_run(
                f"python inference.py --prompt '{inputs['prompt']}' --output /outputs",
                volumes=volumes
            )
        else:
            # Cloud deployment would use K8s Job or similar
            result = await self.submit_cloud_job(model_config, inputs)
        
        return {
            'output_path': '/tmp/outputs/generated.mp4',
            'metadata': self.extract_metadata(result)
        }
    
    async def run_transition_model(self, model_config, inputs):
        """Create transition between two video clips"""
        container = await self.get_or_create_container(model_config)
        
        # Transition-specific processing
        cmd = f"""python transition.py \
            --video_a /inputs/video_a.mp4 \
            --video_b /inputs/video_b.mp4 \
            --type {inputs['type']} \
            --duration {inputs['duration']} \
            --output /outputs/transition.mp4"""
        
        result = container.exec_run(cmd, volumes=self.get_volumes(inputs))
        
        return {
            'output_path': '/tmp/outputs/transition.mp4',
            'duration': inputs['duration'],
            'type': inputs['type']
        }
    
    async def run_composite_model(self, model_config, inputs):
        """Combine/overlay multiple media elements"""
        container = await self.get_or_create_container(model_config)
        
        # Compositing with optional mask
        cmd_parts = [
            "python composite.py",
            f"--base /inputs/base.{inputs['base_media'].split('.')[-1]}",
            f"--overlay /inputs/overlay.{inputs['overlay_media'].split('.')[-1]}",
            f"--blend_mode {inputs['blend_mode']}",
            f"--opacity {inputs['opacity']}"
        ]
        
        if inputs.get('mask'):
            cmd_parts.append(f"--mask /inputs/mask.png")
        
        cmd_parts.append("--output /outputs/composite.mp4")
        
        result = container.exec_run(" ".join(cmd_parts), volumes=self.get_volumes(inputs))
        
        return {
            'output_path': '/tmp/outputs/composite.mp4',
            'blend_mode': inputs['blend_mode'],
            'has_mask': bool(inputs.get('mask'))
        }
```

### Backend Service Integration

#### 1. ComfyUI WebSocket Adapter
- **Protocol**: WebSocket communication with ComfyUI server
- **Workflow Management**: JSON template system with parameter injection
- **Progress Tracking**: Real-time progress events forwarded to clients
- **Error Handling**: Graceful fallback and error propagation
- **Quality-Based Workflows**: Different workflow templates per quality tier

#### 2. Wan2GP HTTP Adapter  
- **Integration**: Gradio client for HTTP-based communication
- **Batch Processing**: Queue multiple requests for efficiency
- **Format Conversion**: Automatic video format handling
- **Quality Presets**: Dynamic quality selection based on requirements
- **Model Selection**: Different models based on quality tier

#### 3. Heterogeneous Model Integration
- **Docker Containers**: Isolated environments for each model type
- **Dependency Management**: Automatic pip/conda environment setup
- **GPU Allocation**: Dynamic GPU assignment to containers
- **File System Bridge**: Shared volumes for input/output data
- **Quality-Specific Containers**: Separate containers per quality tier

#### 4. Function Runner System (from Canvas Architecture)
- **Heterogeneous Model Integration**: Support for models with different dependencies
- **Docker Containerization**: Each model in isolated Docker container
- **Command-Line Interface**: Execute models via subprocess calls
- **Volume Mounting**: Share data between host and containers
- **Dependency Isolation**: Prevent conflicts between model requirements

**Advanced Model Support:**
- **InfiniteYou**: Zero-shot character consistency on FLUX
- **DreamO**: Unified identity, try-on, and style transfer
- **OmniGen2**: Multi-modal generation from complex prompts
- **FlexiAct**: Human action and motion control
- **LoRAEdit**: Fine-grained style control

#### 5. VRAM Budget System
- **Worker Concurrency Control**: `--concurrency=1` for GPU workers
- **Exclusive GPU Access**: One task per GPU worker at a time
- **Queue Intelligence**: Check queue depth before dispatching
- **Application-Level Queueing**: Secondary queue in database for burst handling
- **Resource Monitoring**: Real-time VRAM usage tracking

### Database Schema Requirements

#### 1. PostgreSQL Core Tables
**Projects Table:**
- UUID primary key for project identification
- Project metadata (name, title, description, settings)
- JSONB field for complete node graph storage
- User ownership and creation tracking
- Version field for conflict resolution

**Assets Table:**
- UUID identification for all generative assets
- Asset type classification (character, style, environment)
- JSONB storage for complete regeneration parameters
- File references to S3/storage locations
- User attribution and timestamp tracking

**Collaboration Tables:**
- Real-time session tracking per project
- User presence and cursor position data
- WebSocket connection management
- Activity logging for audit trails

#### 2. Storage Architecture Requirements
**S3-Compatible Object Storage:**
- Project-based organization: `/projects/{project_id}/`
- Asset-specific paths following PRD-008 structure
- Version control with immutable file naming
- CDN integration for global asset delivery
- Lifecycle policies for temporary file cleanup

#### 1. Project Structure Service
**Automated Project Scaffolding:**
- **Template-Based Creation**: Use PRD-008 directory structure template
- **Git Repository Initialization**: Automatic Git setup with proper .gitignore/.gitattributes
- **Database Record Creation**: Link file system structure to database metadata
- **Atomic Operations**: Ensure complete project creation or rollback on failure

**API Requirements:**
- `POST /api/projects/create` - Create project with full directory structure
- `GET /api/projects/{id}/structure` - Return file tree for project browser
- **Error Handling**: Comprehensive validation and rollback on creation failure
- **User Authorization**: Verify user permissions for project operations

#### 2. Path Resolution Service
**Core Functionality:**
- **Asset ID Resolution**: Convert frontend asset IDs to file system paths
- **Project Structure Adherence**: Enforce PRD-008 directory conventions
- **Cross-Platform Compatibility**: Abstract path handling for Windows/Linux
- **Git LFS Integration**: Automatic LFS handling for large files

**Required Methods:**
- `resolve_asset_path(project_id, asset_type, asset_id)` → Path
- `resolve_shot_render_path(project_id, scene, shot, version, take)` → Path
- `resolve_character_reference_path(project_id, character_id)` → Path
- `get_project_workspace_root(project_id)` → Path
- `list_asset_files(project_id, asset_type, asset_id)` → FileList

#### 3. Git Integration Service
**Version Control Operations:**
- **Auto-commit**: Optional commit after successful generation
- **Git LFS Management**: Automatic tracking of large binary files
- **Atomic Versioning**: Immutable file naming with version/take numbers
- **Branch Management**: Support for feature branches and merging
- **User Attribution**: Proper Git commit attribution for collaborative work

**Git LFS Configuration (from draft4_filestructure.md):**
- Track `*.safetensors`, `*.ckpt`, `*.mp4`, `*.mov`, `*.wav` files
- Exclude cache directories and temporary files
- Implement `*.gitattributes` templates for new projects

**API Requirements:**
- `POST /api/projects/{id}/commit` - Manual commit with message
- `GET /api/projects/{id}/history` - Commit history with pagination
- **Automatic Operations**: Background commits for generation results
- **Conflict Resolution**: Handle concurrent modifications

### Performance Requirements

#### 1. Scalability Architecture
**Horizontal Scaling Requirements:**
- **API Gateway**: Load-balanced FastAPI instances with auto-scaling
- **Worker Pools**: Quality-specific Celery workers with VRAM-aware distribution
- **Database**: Read replicas for query distribution and caching
- **Message Broker**: Redis cluster for high-throughput task queuing
- **Storage**: S3-compatible object storage with CDN integration

#### 2. Quality-Based Resource Allocation
**VRAM Tier Specifications (from draft4_filestructure.md):**
- **12GB Workers**: SD 1.5, SDXL optimized, Flux Schnell
- **16GB Workers**: SDXL + ControlNets, Flux.Dev FP8 quantized
- **24GB Workers**: Full Flux.Dev FP16, multiple LoRAs, 2K resolution

**Scaling Strategy:**
- **Dynamic Provisioning**: Auto-scale workers based on queue depth per tier
- **Intelligent Routing**: Producer agent selects appropriate VRAM tier
- **Fallback Logic**: Automatic quality downgrade when resources unavailable
- **Load Balancing**: Distribute tasks across available workers in tier

#### 3. Performance Benchmarks
**Response Time Requirements:**
- **API Endpoints**: <200ms for 95th percentile
- **WebSocket Events**: <100ms for collaborative updates  
- **File Operations**: <500ms for asset resolution
- **Database Queries**: <50ms for metadata operations

**Throughput Requirements:**
- **Concurrent Users**: Support 1,000+ simultaneous users
- **Generation Tasks**: Process 10,000+ tasks per day
- **WebSocket Connections**: Handle 5,000+ real-time connections
- **Worker Efficiency**: Maintain >80% GPU utilization during peak

---

## Success Metrics

### Technical Performance Metrics
**Core System Performance:**
- **API Response Time**: <200ms for 95th percentile REST endpoints
- **WebSocket Latency**: <100ms for real-time collaborative updates
- **Task Completion Rate**: >98% successful generation completion
- **System Uptime**: 99.9% availability SLA
- **Worker Efficiency**: >80% GPU utilization during peak hours

**Scalability Benchmarks:**
- **Concurrent Users**: Support 1,000+ simultaneous active users
- **Generation Throughput**: Process 10,000+ tasks per day
- **WebSocket Connections**: Handle 5,000+ real-time connections
- **Auto-scaling Response**: <2 minutes to provision new workers
- **Database Performance**: <50ms for metadata queries

### Architectural Compliance
**Integration Requirements:**
- **WebSocket Protocol**: 100% compliance with draft4_canvas.md event schema
- **File Structure**: Complete adherence to PRD-008 directory conventions
- **Path Resolution**: Zero file path exposure to frontend clients
- **Git LFS Integration**: Automatic handling per draft4_filestructure.md specs
- **Quality Tier Routing**: Proper VRAM-based task distribution

**Collaboration Features:**
- **Real-time Synchronization**: Changes propagate within 500ms
- **Conflict Resolution**: Automatic handling of concurrent edits
- **State Consistency**: Database remains authoritative source of truth
- **Connection Resilience**: Automatic reconnection with state sync

---

## Implementation Dependencies

### Core Technology Stack
**Backend Requirements:**
- **FastAPI**: ASGI-based web framework with WebSocket support
- **Celery**: Distributed task queue with Redis broker
- **PostgreSQL**: Primary database with JSONB support
- **Redis**: Message broker and session cache
- **Docker**: Containerized model execution environment

**Integration Requirements:**
- **ComfyUI Adapter**: WebSocket client for ComfyUI integration
- **Wan2GP Client**: HTTP client for Gradio-based services
- **Git LFS**: Large file storage for binary assets
- **S3 SDK**: Object storage client for file management
- **MoviePy**: Python video editing for final assembly

### External Service Dependencies
**Required Services:**
- **ComfyUI Server**: Running on port 8188 for image/video generation
- **Wan2GP Server**: Running on port 7860 for video-to-prompt services
- **Model Storage**: Accessible model repository for Function Runner
- **Authentication Provider**: JWT-based user authentication
- **Monitoring Stack**: Logging, metrics, and alerting infrastructure

### Development Prerequisites
**Environment Setup:**
- **Python 3.11+**: Backend development environment
- **Node.js 18+**: Frontend build tools and development
- **Docker Compose**: Local development orchestration
- **Git LFS**: Large file handling in repositories
- **UV**: Fast Python package management

---

## Implementation Validation

### Core Architecture Validation
**WebSocket Protocol Compliance:**
- Implement exact event schema from draft4_canvas.md Table 4
- Validate ConnectionManager handles per-project client lifecycle
- Ensure optimistic updates with server-side conflict resolution
- Test automatic reconnection with full state synchronization

**File Structure Compliance:**
- Enforce PRD-008 directory structure for all projects
- Implement Path Resolution Service for ID-to-path conversion
- Validate Git LFS integration per draft4_filestructure.md specifications
- Test atomic file naming convention (SHOT-010_v01_take01.mp4)

**Quality Tier Implementation:**
- Implement three-tier VRAM management (12GB/16GB/24GB)
- Validate quality-based queue routing in Celery
- Test automatic fallback and user notification
- Ensure Producer agent intelligence for hardware-aware routing

### Integration Testing Requirements
**Real-time Collaboration:**
- Multi-user canvas editing with conflict resolution
- WebSocket event propagation within 500ms
- State versioning and optimistic update handling
- Connection resilience with automatic recovery

**Backend Service Integration:**
- ComfyUI WebSocket adapter with progress forwarding
- Wan2GP HTTP client integration
- Function Runner Docker container management
- Git operations with user attribution

**End-to-End Workflows:**
- Complete shot generation from node graph to rendered output
- Asset management from creation to usage in generation
- EDL compilation and MoviePy video assembly
- Project collaboration with real-time synchronization

---

## Compliance Checklist

### Draft4_Canvas.md Alignment
- [ ] **WebSocket Event Schema**: Implement Table 4 events exactly as specified
- [ ] **Connection Management**: ConnectionManager class per project ID
- [ ] **State Synchronization**: Database as authoritative source with client caching
- [ ] **Conflict Resolution**: Version-based conflict detection and resolution
- [ ] **Real-time Updates**: Optimistic updates with server confirmation

### Draft4_Svelte.md Integration
- [ ] **SvelteKit Routing**: File-based routing structure as specified
- [ ] **Svelte Flow Nodes**: Custom node components for production canvas
- [ ] **State Management**: Svelte stores for reactive UI updates
- [ ] **API Integration**: RESTful endpoints and WebSocket communication
- [ ] **Assembly Pipeline**: Graph-to-EDL compilation with MoviePy rendering

### Draft4_Filestructure.md Compliance
- [ ] **Project Structure**: Complete PRD-008 directory hierarchy
- [ ] **Git LFS Configuration**: Automatic tracking per .gitattributes template
- [ ] **Path Resolution**: Abstract file paths from frontend completely
- [ ] **VRAM Management**: Three-tier system with intelligent routing
- [ ] **Atomic Versioning**: Immutable file naming with version/take numbers

### Quality Integration Requirements
- [ ] **Three-Tier System**: Low/Standard/High quality pipelines
- [ ] **Container Architecture**: Isolated Docker environments per tier
- [ ] **Resource Management**: VRAM-aware task routing and fallback
- [ ] **Producer Intelligence**: Hardware-aware task orchestration
- [ ] **User Experience**: Transparent quality selection and feedback

---

**Architecture Validation:**
This PRD successfully integrates all architectural specifications from the three concept files, ensuring the Backend Integration Service Layer provides the foundational infrastructure for a modern, web-based generative film studio with real-time collaboration, distributed processing, and intelligent resource management.

---

*Implementation must follow all specifications exactly as defined in the concept files to ensure architectural consistency across the entire platform.*