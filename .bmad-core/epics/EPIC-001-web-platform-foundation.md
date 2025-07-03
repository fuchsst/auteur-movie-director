# Epic: Web Platform Foundation

## Epic Description
Establish the foundational web-based platform architecture for the Generative Media Studio, transforming AI-powered film production into a browser-accessible creative tool. This epic focuses on building a simple, working local development system with SvelteKit frontend and FastAPI backend, implementing file-based project management and preparing the infrastructure for the Function Runner pattern.

## Business Value
- **Immediate Accessibility**: Browser-based interface removes installation barriers
- **Professional Workflow**: Git-based project management enables version control
- **Extensible Foundation**: Function Runner pattern allows easy AI model integration
- **Developer Velocity**: Simple architecture enables rapid feature development
- **Future-Ready**: Clean separation prepares for cloud deployment when needed

## Scope & Boundaries

### In Scope
- SvelteKit frontend application with TypeScript
- Three-panel UI layout architecture:
  - Left Panel: Project Browser (hierarchical tree) + Asset Browser (categorized)
  - Center Panel: Main View with Scene/Asset view tabs
  - Right Panel: Properties Inspector + Progress/Notification Area
- FastAPI backend service (single Python app)
- File-based project storage with Git integration
- Git LFS (Large File Storage) configuration and validation
- Local workspace/project directory structure with numbered folders:
  - 01_Assets (raw source materials)
  - 02_Source_Creative (canvas saves, scripts)
  - 03_Renders (generated media/takes)
  - 04_Project_Files (external app files)
  - 05_Cache (temporary data, git-ignored)
  - 06_Exports (final deliverables, git-ignored)
- Hierarchical project structure (Project → Chapter → Scene → Shot → Take)
- Basic project CRUD operations (create, read, update, delete)
- Asset management system with categories (Locations, Characters, Music, Styles)
- WebSocket connection for real-time updates with typed events
- Simple user session management (local development)
- Project manifest (project.json) handling
- Basic file upload/download for assets
- Full Docker Compose orchestration for all services:
  - Frontend (SvelteKit)
  - Backend (FastAPI)
  - Worker (Celery)
  - Redis (Message Broker)
- Celery worker service for asynchronous task processing
- Redis message broker for task queue management
- Makefile as primary developer interface
- Development environment configuration with multi-stage Dockerfiles
- Project scaffolding automation
- .gitignore and .gitattributes configuration

### Out of Scope
- Production Canvas node editor (PRD-002)
- Function Runner containers (PRD-003)
- Advanced authentication (JWT, OAuth)
- Multi-user collaboration features
- Cloud deployment configuration
- Database systems (using file-based)
- nginx or reverse proxy (direct access)
- Production security hardening
- Performance optimization

## Acceptance Criteria

### Functional Criteria
- [ ] Three-panel layout displays correctly with resizable boundaries
- [ ] User can create a new project with name and quality tier
- [ ] Projects are created in correct workspace directory structure
- [ ] Project directories follow numbered folder structure (01_Assets through 06_Exports)
- [ ] Project Browser shows hierarchical tree (Project/Chapter/Scene/Shot/Take)
- [ ] Asset Browser displays categorized assets (Locations, Characters, Music, Styles)
- [ ] Project manifest (project.json) saves/loads correctly
- [ ] Files can be uploaded to project assets folder
- [ ] Asset abstraction hides file complexity from users
- [ ] WebSocket connects and maintains connection
- [ ] File changes trigger real-time UI updates in all panels
- [ ] Projects initialize as Git repositories with proper .gitignore and .gitattributes
- [ ] Git LFS properly configured for all media file types
- [ ] Properties Inspector updates based on selection
- [ ] Progress Area shows task status and notifications
- [ ] Celery workers process async generation tasks
- [ ] Redis maintains task queue persistence

### Technical Criteria
- [ ] All services start with single `make up` command
- [ ] Docker Compose orchestrates all services (frontend, backend, worker, redis)
- [ ] Makefile provides all common development commands
- [ ] Frontend runs with `npm run dev` (SvelteKit)
- [ ] Backend runs with `uvicorn` (FastAPI)
- [ ] Celery worker processes background tasks
- [ ] Redis persists message queue data
- [ ] WebSocket connection established on page load
- [ ] File operations use async I/O
- [ ] Project directories follow specified structure
- [ ] API endpoints return proper status codes
- [ ] Frontend handles API errors gracefully
- [ ] Git operations work for project versioning
- [ ] Git LFS validation on application startup
- [ ] Multi-stage Dockerfiles optimize image sizes

### Function Runner Foundation Criteria
- [ ] Task dispatcher maps quality settings to pipeline configurations
- [ ] WebSocket supports task execution protocol (start_generation, progress, success/failed)
- [ ] Celery tasks can publish progress to Redis pub/sub
- [ ] Worker volume mounts allow access to workspace for future containers
- [ ] Project.json quality field integrated with backend dispatcher
- [ ] Task submission via WebSocket with node_id payload
- [ ] Redis pub/sub channel established for progress events
- [ ] WebSocket manager subscribes to task progress channels

### Quality Criteria
- [ ] Setup documented in README
- [ ] Code follows project conventions
- [ ] Basic error handling implemented
- [ ] File paths work cross-platform
- [ ] No hardcoded configuration values
- [ ] API endpoints have basic validation
- [ ] UI provides operation feedback
- [ ] Development workflow is smooth

## Dependencies
- **Development Environment**: 
  - Node.js 20+ (for IDE support and local tooling)
  - Python 3.12+ (for local development tools)
  - Docker Engine 20.10+ and Docker Compose
  - Git and Git LFS (mandatory prerequisite)
  - Make utility (for developer interface)
- **Workspace Structure**: Decision on default workspace location (/Generative_Studio_Workspace/)
- **Project Structure**: Finalized numbered directory layout from PRD-004
- **API Design**: Basic REST endpoints defined
- **Container Architecture**: Docker images for all services

## Risk Factors
- **Cross-Platform Paths**: File path handling between Windows/Mac/Linux
- **Git Integration**: Handling Git operations from web context
- **Git LFS**: Ensuring all developers have LFS installed and configured
- **WebSocket Stability**: Connection drops and reconnection logic
- **File Permissions**: Web app accessing local filesystem
- **Container Resources**: Local machine VRAM/RAM constraints
- **Repository Size**: Media files bloating without proper LFS configuration

## Story Breakdown

### Infrastructure Stories
1. **Development Environment Setup** (2 points)
   - Create setup scripts for frontend and backend
   - Configure environment variables
   - Document development workflow

2. **Project Structure Definition** (3 points)
   - Implement workspace/project directory creation
   - Define project.json schema
   - Create Git initialization for projects

### Backend Stories
3. **FastAPI Application Bootstrap** (3 points)
   - Set up basic FastAPI app structure
   - Configure CORS for local development
   - Implement error handling middleware
   - Create health check endpoint

4. **File Management API** (5 points)
   - Create workspace configuration endpoint
   - Implement project CRUD operations
   - Add file upload/download endpoints
   - Handle cross-platform path operations

5. **WebSocket Service** (5 points)
   - Set up WebSocket endpoint
   - Implement connection management
   - Create file change notifications
   - Add heartbeat/reconnection logic

6. **Git Integration Service** (3 points)
   - Implement Git init for new projects
   - Add basic commit functionality
   - Create status checking endpoint

### Frontend Stories
7. **SvelteKit Application Setup** (2 points)
   - Initialize SvelteKit with TypeScript
   - Configure development environment
   - Set up basic routing structure

8. **Three-Panel Layout Implementation** (5 points)
   - Create resizable three-panel container
   - Implement panel collapse/expand functionality
   - Add panel persistence to local storage
   - Configure responsive behavior

9. **Project Browser Component** (5 points)
   - Create hierarchical tree view component
   - Implement expand/collapse for tree nodes
   - Add project/chapter/scene/shot/take structure
   - Enable selection and navigation

10. **Asset Browser Component** (5 points)
    - Create categorized asset listing
    - Implement asset preview thumbnails
    - Add drag-drop placeholder for future canvas
    - Support folder organization within categories

11. **Properties Inspector Panel** (3 points)
    - Create context-sensitive property display
    - Implement dynamic form generation
    - Add update handlers for property changes

12. **Progress & Notification Area** (3 points)
    - Create collapsible notification panel
    - Implement progress bar components
    - Add notification queue management
    - Display task status updates

13. **Main View Container** (3 points)
    - Create tabbed interface for Scene/Asset views
    - Implement view switching logic
    - Add placeholder for future canvas

14. **WebSocket Client** (3 points)
    - Implement connection management
    - Handle reconnection logic
    - Create typed event dispatcher
    - Add event handlers for UI updates

15. **File Upload Component** (3 points)
    - Create drag-and-drop upload area
    - Show upload progress in Progress Area
    - Handle multiple file uploads
    - Integrate with asset categories

### Integration Stories
16. **API Client Setup** (2 points)
    - Create TypeScript API client
    - Define interfaces for all endpoints
    - Implement error handling

17. **End-to-End Project Flow** (3 points)
    - Test complete project creation
    - Verify file structure creation
    - Validate Git initialization
    - Ensure all panels update correctly

18. **Makefile Development Interface** (3 points)
    - Create comprehensive Makefile with all targets
    - Include docker-compose orchestration commands
    - Add model-specific compose targets (up-with-comfyui)
    - Document available commands with help target

19. **Docker Compose Orchestration** (5 points)
    - Create docker-compose.yml with all services
    - Configure service dependencies and networks
    - Set up named volumes for data persistence
    - Configure workspace volume mounting

20. **Git LFS Integration** (3 points)
    - Create .gitattributes template for media files
    - Implement LFS validation on startup
    - Add LFS setup to project scaffolding
    - Create helper scripts for LFS configuration

21. **Function Runner Foundation** (5 points)
    - Implement task dispatcher service with quality mapping
    - Create WebSocket task execution protocol
    - Set up Redis pub/sub for progress events
    - Configure worker for container orchestration readiness
    - Add model storage directory structure

## Estimated Effort
**Total Story Points**: 73 points (updated with Function Runner foundation)
**Estimated Duration**: 3-4 sprints (6-8 weeks)
**Team Size**: 2 developers (1 frontend, 1 backend)

## Success Metrics
- Projects created successfully with correct structure
- WebSocket maintains stable connection
- File uploads complete without errors
- Git repositories initialize properly
- API responds quickly (< 200ms local)
- UI updates reflect file changes

## Technical Architecture Notes

### Frontend Architecture
```
frontend/
├── src/
│   ├── routes/          # SvelteKit pages
│   │   ├── +page.svelte # Main application page
│   │   └── project/
│   │       └── [id]/    # Project workspace
│   ├── lib/
│   │   ├── components/  # UI components
│   │   │   ├── layout/
│   │   │   │   ├── ThreePanelLayout.svelte
│   │   │   │   ├── LeftPanel.svelte
│   │   │   │   ├── CenterPanel.svelte
│   │   │   │   └── RightPanel.svelte
│   │   │   ├── project/
│   │   │   │   └── ProjectBrowser.svelte
│   │   │   ├── asset/
│   │   │   │   └── AssetBrowser.svelte
│   │   │   ├── properties/
│   │   │   │   └── PropertiesInspector.svelte
│   │   │   └── progress/
│   │   │       └── ProgressArea.svelte
│   │   ├── stores/      # Svelte stores
│   │   ├── api/         # API client
│   │   └── ws/          # WebSocket client
│   └── app.html         # App template
├── static/              # Static assets
└── package.json         # Dependencies
```

### Backend Architecture
```
backend/
├── app/
│   ├── main.py          # FastAPI app entry
│   ├── api/
│   │   ├── projects.py  # Project endpoints
│   │   ├── files.py     # File operations
│   │   ├── tasks.py     # Task submission endpoints
│   │   └── ws.py        # WebSocket handler
│   ├── services/
│   │   ├── workspace.py # Workspace management
│   │   ├── git.py       # Git operations
│   │   ├── files.py     # File utilities
│   │   └── dispatcher.py # Task dispatcher (quality mapping)
│   ├── worker/
│   │   ├── celery_app.py # Celery configuration
│   │   └── tasks.py      # Task definitions
│   └── config.py        # Configuration
├── requirements.txt     # Python dependencies
└── Dockerfile          # Container setup
```

### API Design Principles
- Simple REST endpoints for CRUD operations
- File operations use multipart/form-data
- WebSocket for real-time notifications
- Consistent JSON error responses
- Clear HTTP status codes

### Key API Endpoints
```
GET    /api/workspace/config     # Get workspace settings
GET    /api/projects            # List all projects
POST   /api/projects            # Create new project
GET    /api/projects/{id}       # Get project details
DELETE /api/projects/{id}       # Delete project
POST   /api/projects/{id}/files # Upload files
GET    /api/projects/{id}/files # List project files
WS     /ws/{project_id}        # Project-specific WebSocket connection

# Function Runner Foundation Endpoints
POST   /api/tasks/submit       # Submit generation task
GET    /api/tasks/{id}/status  # Get task status
GET    /api/quality/mappings   # Get quality to pipeline mappings
```

### WebSocket Event Types
```typescript
// UI State Events
interface PanelResizeEvent {
  type: 'panel_resize';
  panel: 'left' | 'right';
  width: number;
}

interface SelectionChangeEvent {
  type: 'selection_change';
  targetType: 'project' | 'asset' | 'node';
  targetId: string;
}

// Node State Events (Function Runner Foundation)
interface NodeStateUpdatedEvent {
  type: 'node_state_updated';
  nodeId: string;
  state: 'idle' | 'generating' | 'completed' | 'error';
}

// Task Execution Events (Aligned with Function Runner)
interface StartGenerationEvent {
  type: 'start_generation';
  nodeId: string;
  nodeType: string;
  parameters: Record<string, any>;
}

interface TaskProgressEvent {
  type: 'task_progress';
  taskId: string;
  nodeId: string;
  progress: number;
  step: string;  // Granular step description
  status: 'pending' | 'running' | 'completed' | 'error';
}

interface TaskSuccessEvent {
  type: 'task_success';
  taskId: string;
  nodeId: string;
  result: {
    outputPath: string;
    metadata?: Record<string, any>;
  };
}

interface TaskFailedEvent {
  type: 'task_failed';
  taskId: string;
  nodeId: string;
  error: string;
}

// Project Events
interface ProjectUpdateEvent {
  type: 'project_update';
  projectId: string;
  changes: Partial<Project>;
}

// Asset Events
interface AssetAddedEvent {
  type: 'asset_added';
  category: 'locations' | 'characters' | 'music' | 'styles';
  asset: AssetData;
}
```

### Project.json Schema
```json
{
  "id": "unique-project-id",
  "name": "My Film Project",
  "created": "2025-01-02T10:00:00Z",
  "quality": "standard",
  "canvas": {
    "nodes": [],
    "edges": [],
    "viewport": {}
  },
  "settings": {
    "fps": 24,
    "resolution": [1920, 1080]
  }
}
```

### Docker Compose Configuration
```yaml
version: '3.8'

services:
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
      - /app/node_modules
    environment:
      - VITE_BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - gms_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: gms_backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - generative_studio_workspace:/Generative_Studio_Workspace
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - WORKSPACE_ROOT=/Generative_Studio_Workspace
    depends_on:
      - redis
    networks:
      - gms_network

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: gms_worker
    command: celery -A app.worker.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
      - generative_studio_workspace:/Generative_Studio_Workspace
      - /var/run/docker.sock:/var/run/docker.sock  # For Function Runner container orchestration
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - WORKSPACE_ROOT=/Generative_Studio_Workspace
      - DOCKER_HOST=unix:///var/run/docker.sock
    depends_on:
      - backend
      - redis
    networks:
      - gms_network

  redis:
    image: redis:7-alpine
    container_name: gms_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - gms_network

networks:
  gms_network:
    driver: bridge

volumes:
  redis_data:
  generative_studio_workspace:
    driver: local
    driver_opts:
      type: 'none'
      o: 'bind'
      device: './Generative_Studio_Workspace'
```

### Makefile Targets
```makefile
# Key developer commands
make help           # Show all available commands
make build          # Build all Docker images
make up             # Start all services
make down           # Stop and clean up
make logs           # Follow service logs
make test           # Run test suite
make new-project    # Create new project structure
make shell-backend  # Access backend container
make shell-frontend # Access frontend container

# Model-specific targets
make up-with-comfyui    # Start with ComfyUI model
```

### Project Directory Structure
```
/Generative_Studio_Workspace/
├── Projects/
│   └── MyFilm/
│       ├── project.json         # Project manifest
│       ├── .git/                # Version control
│       ├── .gitignore           # Ignore patterns
│       ├── .gitattributes       # LFS configuration
│       ├── 01_Assets/           # Source materials
│       ├── 02_Source_Creative/  # Canvas saves & scripts
│       ├── 03_Renders/          # Generated content
│       ├── 04_Project_Files/    # External app files
│       ├── 05_Cache/            # Temporary (ignored)
│       └── 06_Exports/          # Final deliverables
└── Library/                     # Workspace-level assets
    ├── Pipeline_Templates/
    ├── Stock_Media/
    ├── Characters/
    ├── Styles/
    ├── Locations/
    └── AI_Models/              # Model storage (Function Runner prep)
```

### Function Runner Foundation
The platform architecture is designed to support the Function Runner pattern for AI model execution:

#### Task Dispatcher Architecture
```python
# Dispatcher service maps quality settings to pipeline configurations
QUALITY_PIPELINE_MAPPING = {
    "low": {
        "pipeline_id": "gms-flux:1.0-low-vram",
        "target_vram": 12,
        "optimizations": ["cpu_offloading", "sequential"]
    },
    "standard": {
        "pipeline_id": "gms-flux:1.0-standard",
        "target_vram": 16,
        "optimizations": ["moderate_parallel"]
    },
    "high": {
        "pipeline_id": "gms-flux:1.0-high-fidelity",
        "target_vram": 24,
        "optimizations": ["full_parallel"]
    }
}
```

#### Celery Task Structure
```python
# Foundation for Function Runner tasks
@celery_app.task
def execute_generation(node_id: str, project_id: str, parameters: dict):
    # 1. Retrieve node data and project quality setting
    # 2. Map quality to pipeline configuration
    # 3. Prepare task payload with output paths
    # 4. Publish progress updates via Redis pub/sub
    # 5. Return success/failure with output path
    pass
```

#### WebSocket Progress Relay
- Worker publishes events to Redis pub/sub channel
- FastAPI WebSocket manager subscribes to channels
- Events forwarded to appropriate client connections
- Enables real-time progress tracking for long-running tasks

---

**Epic Version**: 1.3  
**Created**: 2025-01-02  
**Updated**: 2025-01-03  
**Owner**: Auteur Movie Director Development Team  
**Status**: Ready for Development