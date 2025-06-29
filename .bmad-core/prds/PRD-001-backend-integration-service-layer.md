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
                'parameters': dict        # Model parameters
            },
            'transition': {
                'video_a': str,           # Path to first video
                'video_b': str,           # Path to second video
                'duration': float,        # Transition duration
                'type': str              # Transition type (fade, wipe, etc.)
            },
            'combine_overlay': {
                'base_media': str,        # Base image/video path
                'overlay_media': str,     # Overlay image/video path
                'mask': str,             # Optional mask path
                'blend_mode': str,       # Blend mode (multiply, screen, etc.)
                'opacity': float         # Overlay opacity
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

#### 2. Wan2GP HTTP Adapter  
- **Integration**: Gradio client for HTTP-based communication
- **Batch Processing**: Queue multiple requests for efficiency
- **Format Conversion**: Automatic video format handling
- **Quality Presets**: Dynamic quality selection based on requirements

#### 3. Heterogeneous Model Integration
- **Docker Containers**: Isolated environments for each model type
- **Dependency Management**: Automatic pip/conda environment setup
- **GPU Allocation**: Dynamic GPU assignment to containers
- **File System Bridge**: Shared volumes for input/output data

### Data Storage Architecture

#### 1. PostgreSQL Database Schema
```sql
-- Projects and collaboration
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP,
    node_graph JSONB,
    settings JSONB
);

-- Generative assets with regeneration parameters
CREATE TABLE assets (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    type VARCHAR(50), -- character, style, environment
    name VARCHAR(255),
    parameters JSONB, -- Full regeneration parameters
    file_references JSONB, -- S3 URLs for generated content
    created_at TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Real-time collaboration tracking
CREATE TABLE project_sessions (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    user_id UUID REFERENCES users(id),
    connected_at TIMESTAMP,
    last_activity TIMESTAMP,
    cursor_position JSONB
);
```

#### 2. S3-Compatible Object Storage
- **Asset Organization**: `/projects/{project_id}/assets/{asset_id}/`
- **Version Control**: Automatic versioning for iterative generations
- **CDN Integration**: Optional CDN for global asset delivery
- **Lifecycle Policies**: Automatic cleanup of temporary files

### WebSocket Event Protocol

#### Event Types and Payloads
```typescript
// Client to Server Events
interface ClientEvent {
    type: 'node.create' | 'node.update' | 'node.delete' | 
          'edge.create' | 'edge.delete' | 'generate.start' |
          'cursor.move' | 'selection.change';
    payload: any;
    timestamp: number;
}

// Server to Client Events  
interface ServerEvent {
    type: 'state.update' | 'progress.update' | 'generation.complete' |
          'error.occurred' | 'user.joined' | 'user.left' |
          'cursor.update' | 'selection.update';
    payload: any;
    userId?: string;
    timestamp: number;
}

// Progress Update Payload
interface ProgressUpdate {
    nodeId: string;
    taskId: string;
    percent: number;
    message: string;
    eta?: number;
}
```

### File Storage Architecture

#### 1. Project Structure Service
```python
from pathlib import Path
from project_paths import ProjectPaths
import subprocess

@app.post("/api/projects/create")
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user)
):
    """Scaffold complete project structure with Git initialization"""
    paths = ProjectPaths(WORKSPACE_ROOT)
    scaffolder = ProjectScaffolder(WORKSPACE_ROOT, TEMPLATE_DIR)
    
    try:
        # Create project structure
        project_root = scaffolder.create_project(
            request.project_name,
            request.title,
            request.description
        )
        
        # Create database record
        project = await create_project_record(
            name=request.project_name,
            title=request.title,
            owner_id=current_user.id,
            root_path=str(project_root)
        )
        
        return {
            "project_id": project.id,
            "name": project.name,
            "structure_created": True,
            "git_initialized": True
        }
    except Exception as e:
        logger.error(f"Project creation failed: {e}")
        raise HTTPException(400, str(e))

@app.get("/api/projects/{project_id}/structure")
async def get_project_structure(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Return project file tree structure"""
    project = await get_user_project(project_id, current_user.id)
    paths = ProjectPaths(WORKSPACE_ROOT)
    project_root = paths.get_project_root(project.name)
    
    def build_tree(path: Path):
        tree = {"name": path.name, "type": "directory", "children": []}
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.git'):
                    continue
                if item.is_dir():
                    tree["children"].append(build_tree(item))
                else:
                    tree["children"].append({
                        "name": item.name,
                        "type": "file",
                        "size": item.stat().st_size
                    })
        except PermissionError:
            pass
        return tree
    
    return build_tree(project_root)
```

#### 2. Path Resolution Service
```python
class PathResolutionService:
    """Centralized service for resolving asset references to file paths"""
    
    def __init__(self, workspace_root: Path):
        self.paths = ProjectPaths(workspace_root)
    
    async def resolve_asset_path(
        self, 
        project_id: str, 
        asset_type: str, 
        asset_name: str
    ) -> Path:
        """Resolve high-level asset reference to file path"""
        project = await get_project(project_id)
        project_root = self.paths.get_project_root(project.name)
        
        if asset_type == "character":
            return self.paths.get_character_asset_path(project_root, asset_name)
        elif asset_type == "style":
            return self.paths.get_style_asset_path(project_root, asset_name)
        elif asset_type == "location":
            return project_root / "01_Assets" / "Generative_Assets" / "Locations" / asset_name
        else:
            raise ValueError(f"Unknown asset type: {asset_type}")
    
    async def get_asset_files(
        self, 
        project_id: str, 
        asset_type: str, 
        asset_name: str
    ) -> Dict[str, List[str]]:
        """List all files for a given asset"""
        asset_path = await self.resolve_asset_path(project_id, asset_type, asset_name)
        
        files = {
            "reference_images": [],
            "models": [],
            "metadata": []
        }
        
        if not asset_path.exists():
            return files
        
        for file in asset_path.rglob("*"):
            if file.is_file():
                if file.suffix in [".png", ".jpg", ".jpeg"]:
                    files["reference_images"].append(str(file.relative_to(asset_path)))
                elif file.suffix in [".safetensors", ".ckpt", ".pth"]:
                    files["models"].append(str(file.relative_to(asset_path)))
                elif file.suffix in [".txt", ".json"]:
                    files["metadata"].append(str(file.relative_to(asset_path)))
        
        return files

# API endpoints using path resolution
@app.post("/api/assets/{asset_type}/create")
async def create_asset(
    asset_type: str,
    request: CreateAssetRequest,
    current_user: User = Depends(get_current_user)
):
    """Create asset folder structure"""
    path_service = PathResolutionService(WORKSPACE_ROOT)
    
    # Create asset directory
    asset_path = await path_service.resolve_asset_path(
        request.project_id,
        asset_type,
        request.name
    )
    
    asset_path.mkdir(parents=True, exist_ok=True)
    
    # Create standard subdirectories
    if asset_type in ["character", "style", "location"]:
        (asset_path / "reference_images").mkdir(exist_ok=True)
    
    # Create metadata files
    with open(asset_path / "description.txt", "w") as f:
        f.write(request.description or "")
    
    return {"asset_path": str(asset_path), "created": True}
```

#### 3. Git Integration Service
```python
class GitIntegrationService:
    """Handles Git operations for project version control"""
    
    async def commit_project_changes(
        self, 
        project_id: str, 
        message: str, 
        user_id: str
    ):
        """Create Git commit for project changes"""
        project = await get_project(project_id)
        project_root = Path(project.root_path)
        
        # Stage all changes
        subprocess.run(["git", "add", "-A"], cwd=project_root, check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            return {"status": "no_changes"}
        
        # Commit with user attribution
        user = await get_user(user_id)
        subprocess.run([
            "git", "-c", f"user.name={user.name}",
            "-c", f"user.email={user.email}",
            "commit", "-m", message
        ], cwd=project_root, check=True)
        
        return {"status": "committed", "message": message}
    
    async def get_project_history(
        self, 
        project_id: str, 
        limit: int = 20
    ):
        """Get Git commit history for project"""
        project = await get_project(project_id)
        project_root = Path(project.root_path)
        
        result = subprocess.run([
            "git", "log", 
            f"--max-count={limit}",
            "--pretty=format:%H|%an|%ae|%at|%s"
        ], cwd=project_root, capture_output=True, text=True, check=True)
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                hash, author, email, timestamp, subject = line.split("|", 4)
                commits.append({
                    "hash": hash,
                    "author": author,
                    "email": email,
                    "timestamp": int(timestamp),
                    "message": subject
                })
        
        return commits

# API endpoints for Git operations
@app.post("/api/projects/{project_id}/commit")
async def commit_project(
    project_id: str,
    request: CommitRequest,
    current_user: User = Depends(get_current_user)
):
    """Commit project changes"""
    git_service = GitIntegrationService()
    result = await git_service.commit_project_changes(
        project_id,
        request.message,
        current_user.id
    )
    return result

@app.get("/api/projects/{project_id}/history")
async def get_history(
    project_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get project commit history"""
    await verify_project_access(project_id, current_user.id)
    git_service = GitIntegrationService()
    return await git_service.get_project_history(project_id, limit)
```

### Performance and Scalability

#### 1. Horizontal Scaling Strategy
- **API Gateway**: Multiple FastAPI instances behind load balancer
- **Worker Pools**: Separate queues for GPU-heavy and CPU-only tasks
- **Database**: Read replicas for query distribution
- **Redis Cluster**: Sharded Redis for message broker scaling
- **Quality-Based Scaling**: Different worker pools per quality tier

#### 2. Quality-Optimized Resource Allocation
- **Low Quality Workers**: More workers with smaller GPUs (8GB VRAM)
- **Standard Workers**: Balanced count with mid-range GPUs (16GB VRAM)
- **High Quality Workers**: Fewer workers with premium GPUs (24GB+ VRAM)
- **Dynamic Scaling**: Scale worker pools based on queue depth per quality tier

#### 3. Caching Architecture
- **Result Caching**: Cache generated content with same parameters
- **Asset CDN**: CloudFront or similar for global asset delivery
- **Database Caching**: Redis cache for frequently accessed metadata
- **Workflow Templates**: Pre-parsed template cache
- **Quality-Aware Caching**: Different cache TTL per quality tier

#### 4. Resource Optimization
- **Worker Recycling**: Periodic worker restart to prevent memory leaks
- **Connection Pooling**: Reuse database and Redis connections
- **Batch Processing**: Group similar tasks for GPU efficiency
- **Progressive Loading**: Stream large assets instead of bulk transfer
- **Quality-Based Timeouts**: Shorter timeouts for low quality, longer for high

---

## Success Metrics

### User Adoption and Engagement
**Primary KPIs:**
- **Monthly Active Users**: Target 5,000+ MAU within 6 months
- **Collaborative Projects**: >40% of projects have multiple active users
- **Session Duration**: Average session >45 minutes indicating engagement
- **Geographic Distribution**: Users from 50+ countries demonstrating global reach

**Measurement Methods:**
- Analytics integration (Plausible, PostHog)
- WebSocket connection metrics
- Project collaboration statistics
- User survey feedback

### Performance and Reliability
**Technical Metrics:**
- **API Response Time**: <200ms for 95th percentile
- **WebSocket Latency**: <100ms for collaborative updates
- **Task Completion Rate**: >98% successful generation completion
- **Uptime**: 99.9% availability SLA

**Scalability Metrics:**
- **Concurrent Users**: Support 1,000+ simultaneous users
- **Task Throughput**: Process 10,000+ generation tasks/day
- **Worker Efficiency**: >80% GPU utilization during peak
- **Auto-scaling Response**: <2 minutes to provision new workers

### Business Impact
**Revenue Metrics:**
- **Conversion Rate**: 10% free to paid conversion
- **Resource Usage**: Optimize compute costs to <$0.50 per generation
- **Customer Acquisition Cost**: <$50 per paying user
- **Lifetime Value**: >$500 per paying customer

---

## Risk Assessment & Mitigation

### Technical Risks

#### High Risk: Distributed System Complexity
- **Risk**: Complex coordination between multiple services
- **Impact**: System instability and difficult debugging
- **Mitigation**: 
  - Comprehensive logging and tracing (OpenTelemetry)
  - Circuit breakers for service failures
  - Gradual rollout with feature flags
  - Extensive integration testing

#### Medium Risk: Real-Time Synchronization Conflicts
- **Risk**: Concurrent edits causing data conflicts
- **Impact**: Lost work or corrupted projects
- **Mitigation**:
  - Operational transformation for conflict resolution
  - Automatic save and version history
  - Conflict detection and user notification
  - Manual merge tools for complex conflicts

### Business Risks

#### High Risk: Infrastructure Costs
- **Risk**: GPU compute costs exceeding revenue
- **Impact**: Unsustainable business model
- **Mitigation**:
  - Efficient task scheduling and batching
  - Spot instance usage for non-urgent tasks
  - Tiered pricing with resource limits
  - Aggressive caching of common operations

#### Medium Risk: Network Latency
- **Risk**: Poor experience for global users
- **Impact**: Limited international adoption
- **Mitigation**:
  - Multi-region deployment strategy
  - Edge caching for static assets
  - Regional worker pools
  - Progressive enhancement for slow connections

---

## Implementation Roadmap

### Phase 1: Core Web Infrastructure (Weeks 1-4)
**Deliverables:**
- FastAPI application with basic CRUD operations
- PostgreSQL database schema and migrations
- S3 storage integration for file management
- Basic SvelteKit frontend with authentication
- Docker development environment

**Success Criteria:**
- Users can create accounts and projects
- Basic REST API functional
- File upload/download working
- Development environment reproducible

### Phase 2: Real-Time Collaboration (Weeks 5-8)
**Deliverables:**
- WebSocket server implementation
- Real-time event synchronization
- Collaborative editing for node canvas
- User presence indicators
- Conflict resolution system

**Success Criteria:**
- Multiple users can edit same project
- Changes propagate in <500ms
- No data loss during concurrent edits
- Smooth user experience

### Phase 3: Distributed Processing (Weeks 9-12)
**Deliverables:**
- Celery worker infrastructure
- GPU worker pool management
- ComfyUI and Wan2GP adapters
- Function Runner for arbitrary models
- Progress tracking system

**Success Criteria:**
- Generation tasks execute on remote workers
- Real-time progress updates to UI
- Support for multiple model types
- Automatic scaling under load

### Phase 4: Production Features (Weeks 13-16)
**Deliverables:**
- Advanced caching system
- Performance optimization
- Monitoring and alerting
- User documentation
- Public beta launch preparation

**Success Criteria:**
- Meet all performance benchmarks
- 99.9% uptime in testing
- Complete user documentation
- Successful load testing at 1000+ users

---

## Stakeholder Sign-Off

### Development Team Approval
- [ ] **Frontend Lead** - SvelteKit architecture approved
- [ ] **Backend Lead** - FastAPI/Celery design validated
- [ ] **DevOps Lead** - Infrastructure approach confirmed
- [ ] **QA Lead** - Testing strategy comprehensive

### Business Stakeholder Approval  
- [ ] **Product Owner** - Requirements meet business goals
- [ ] **Finance** - Infrastructure costs acceptable
- [ ] **Marketing** - Go-to-market strategy aligned
- [ ] **Legal** - Data privacy compliance confirmed

---

**Next Steps:**
1. Infrastructure setup and cost modeling
2. Development environment creation
3. API specification documentation
4. Frontend mockup creation
5. Database schema implementation

---

*This PRD represents the foundational shift from desktop-based to web-based architecture, enabling global access, real-time collaboration, and scalable processing for the next generation of AI-assisted filmmaking.*