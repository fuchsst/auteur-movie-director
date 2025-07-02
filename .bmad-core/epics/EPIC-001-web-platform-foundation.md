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
- FastAPI backend service (single Python app)
- File-based project storage with Git integration
- Local workspace/project directory structure
- Basic project CRUD operations (create, read, update, delete)
- WebSocket connection for real-time updates
- Simple user session management (local development)
- Project manifest (project.json) handling
- Basic file upload/download for assets
- Docker setup for backend service only
- Development environment configuration

### Out of Scope
- Production Canvas node editor (PRD-002)
- Function Runner containers (PRD-003)
- Advanced authentication (JWT, OAuth)
- Redis/Celery task queue (start simple)
- Multi-user collaboration features
- Cloud deployment configuration
- Database systems (using file-based)
- nginx or reverse proxy (direct access)
- Production security hardening
- Performance optimization

## Acceptance Criteria

### Functional Criteria
- [ ] User can create a new project with name and quality tier
- [ ] Projects are created in correct workspace directory structure
- [ ] Project list shows all projects in workspace
- [ ] Project manifest (project.json) saves/loads correctly
- [ ] Files can be uploaded to project assets folder
- [ ] WebSocket connects and maintains connection
- [ ] File changes trigger real-time UI updates
- [ ] Projects initialize as Git repositories

### Technical Criteria
- [ ] Frontend runs with `npm run dev` (SvelteKit)
- [ ] Backend runs with `uvicorn` (FastAPI)
- [ ] WebSocket connection established on page load
- [ ] File operations use async I/O
- [ ] Project directories follow specified structure
- [ ] API endpoints return proper status codes
- [ ] Frontend handles API errors gracefully
- [ ] Git operations work for project versioning

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
- **Development Environment**: Node.js 18+ and Python 3.11+ installed
- **Workspace Structure**: Decision on default workspace location
- **Project Structure**: Finalized directory layout from PRD-004
- **API Design**: Basic REST endpoints defined

## Risk Factors
- **Cross-Platform Paths**: File path handling between Windows/Mac/Linux
- **Git Integration**: Handling Git operations from web context
- **WebSocket Stability**: Connection drops and reconnection logic
- **File Permissions**: Web app accessing local filesystem

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

8. **Project Gallery View** (5 points)
   - Create project listing component
   - Implement grid/list view toggle
   - Add project creation dialog
   - Show project metadata

9. **WebSocket Client** (3 points)
   - Implement connection management
   - Handle reconnection logic
   - Create event dispatcher for updates

10. **File Upload Component** (3 points)
    - Create drag-and-drop upload area
    - Show upload progress
    - Handle multiple file uploads

### Integration Stories
11. **API Client Setup** (2 points)
    - Create TypeScript API client
    - Define interfaces for all endpoints
    - Implement error handling

12. **End-to-End Project Flow** (3 points)
    - Test complete project creation
    - Verify file structure creation
    - Validate Git initialization

## Estimated Effort
**Total Story Points**: 40 points
**Estimated Duration**: 2 sprints (4 weeks)
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
│   │   ├── +page.svelte # Project gallery
│   │   └── project/
│   │       └── [id]/    # Project workspace
│   ├── lib/
│   │   ├── components/  # UI components
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
│   │   └── ws.py        # WebSocket handler
│   ├── services/
│   │   ├── workspace.py # Workspace management
│   │   ├── git.py       # Git operations
│   │   └── files.py     # File utilities
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
WS     /ws                      # WebSocket connection
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

---

**Epic Version**: 1.1  
**Created**: 2025-01-02  
**Updated**: 2025-01-02  
**Owner**: Generative Media Studio Development Team  
**Status**: Ready for Development