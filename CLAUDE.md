# Auteur Movie Director - Development Guide

## 🚀 Quick Start

```bash
# First time setup
make setup             # Full dev setup (installs UV if needed)

# Start with Docker (recommended)
make up                # Frontend: http://localhost:3000
                       # Backend: http://localhost:8000/api/docs

# Or start manually
make dev               # Start development servers
```

### Essential Make Commands
- `make help` - Show all available commands
- `make dev` - Start development servers
- `make test` - Run all tests  
- `make format` - Auto-format code
- `make lint` - Check code quality

## 📋 Critical Commands (Run These Often!)

```bash
# BEFORE committing or when code is complete:
make format            # Auto-format code
make lint             # Check code quality  
make test             # Run all tests

# During development:
make test-backend      # Test Python code
make test-frontend     # Test JavaScript code
```

## 🏗️ Architecture Overview

**Auteur Movie Director** - AI-powered filmmaking platform for directors to create cinematic sequences.

### Three-Layer Architecture:
- **Frontend**: SvelteKit app with node-based Production Canvas
- **Backend**: FastAPI with WebSocket support, Takes system, Git LFS
- **AI Layer**: Function Runner pattern for ComfyUI, LLMs, audio models

### Core Concepts:
- **Projects**: File-based structure with Git version control
- **Takes System**: Non-destructive versioning (like film production)
- **Story Integration**: Three-Act, Seven-Point, Blake Snyder structures
- **Characters**: Asset management with LoRAs and voice models

## 📁 Project Structure

```
auteur-movie-director/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   │   ├── endpoints/    # REST endpoints (health, system, upload, workspace)
│   │   │   ├── v1/          # Versioned APIs (git, git_lfs, takes)
│   │   │   └── websocket.py # WebSocket endpoint
│   │   ├── core/        # Core functionality (dispatcher, exceptions)
│   │   ├── middleware/  # CORS, error handling, logging
│   │   ├── schemas/     # Pydantic models (project, takes, git)
│   │   └── services/    # Business logic
│   │       ├── workspace.py  # Project management
│   │       ├── takes.py      # Version management
│   │       ├── git.py        # Repository operations
│   │       └── git_lfs.py    # Large file storage
│   └── tests/           # Test suite
├── frontend/            # SvelteKit application  
│   └── src/
│       ├── lib/
│       │   ├── api/     # API clients (workspace, takes, git)
│       │   ├── components/   # UI components
│       │   │   ├── asset/    # Asset browser, filters
│       │   │   ├── project/  # Project browser, tree
│       │   │   ├── takes/    # Takes gallery, dialogs
│       │   │   └── views/    # Main view components
│       │   ├── stores/  # State management (app, assets, websocket)
│       │   └── services/# WebSocket client
│       └── routes/      # App pages
├── .bmad-core/          # BMAD framework
│   ├── prds/           # Product requirements
│   ├── stories/        # User stories
│   └── validation/     # Test reports
├── scripts/            # Automation scripts
├── tests/              # E2E tests
└── workspace/          # File storage (gitignored)

```

## 🔧 Key Services

### Backend Services:
- **WorkspaceService**: Project creation, structure validation, character management
- **TakesService**: Version management for shots, thumbnail generation
- **GitService**: Repository init, commits, status tracking
- **GitLFSService**: Large file tracking (.mp4, .png, renders)
- **WebSocketManager**: Real-time communication, task updates

### Frontend Components:
- **ProjectBrowser**: Project selection and creation
- **TakesGallery**: Visual take browser with thumbnails
- **CharacterUploadDialog**: LoRA and asset upload
- **PropertiesInspector**: Context-aware property editing
- **ProgressArea**: Real-time task monitoring

### Core Stores:
- **websocket**: Server connection, message handling
- **assets**: Character/style/location management
- **notifications**: Task progress, errors, updates
- **selection**: Active project/shot/take tracking

## 📝 Project File Structure

### Workspace Organization:
```
workspace/
├── My_Project/
│   ├── .git/            # Git repository with LFS
│   ├── project.json     # Project manifest & metadata
│   ├── 01_Assets/       # Project assets
│   │   ├── Characters/  # Character LoRAs
│   │   ├── Styles/      # Visual styles
│   │   └── Locations/   # Environment assets
│   ├── 02_Story/        # Narrative structure
│   │   └── {act}/{chapter}/{scene}/
│   ├── 03_Renders/      # Generated content
│   │   └── {chapter}/{scene}/{shot}/
│   │       └── {take_id}/
│   │           ├── metadata.json
│   │           ├── thumbnail.png
│   │           └── output.mp4
│   ├── 04_Compositions/ # Canvas saves
│   ├── 05_Audio/        # Generated audio
│   └── 06_Exports/      # Final exports
└── Library/             # Shared assets
    ├── Characters/
    ├── Styles/
    └── Templates/
```

### Story Hierarchy:
```
Project → Act → Chapter → Scene → Shot → Take
         (3-Act)  (Narrative)  (Location)  (Camera)  (Version)
```

## 🛠️ Common Tasks

```bash
# Project Management
make new-project NAME="My Project"        # Create new project
make setup                               # Initialize development environment

# Development
make dev                                 # Start both servers
make dev-backend                         # Backend only
make dev-frontend                        # Frontend only

# Testing
make test                                # Run all tests
make test-quick                          # Quick tests (no integration)
make test-coverage                       # Generate coverage report
make test-integration                    # Integration tests
make test-e2e                           # End-to-end tests with Docker

# Docker Operations
make up                                  # Start core services
make down                               # Stop services
make logs                               # View service logs
make build                              # Build Docker images
make docker-clean                       # Clean Docker resources

# AI Services (Docker)
make docker-up-ai                        # Start all AI services
make docker-up-comfyui                   # ComfyUI only
make docker-up-audio                     # Audio services (RVC, AudioLDM)
make docker-up-video                     # Video services (Wan2GP)
make docker-up-full                      # All services combined
make up-with-comfyui                     # Core + AI services together
```

## ⚙️ Configuration

### Environment Variables (.env):
```
# Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Workspace & Storage
WORKSPACE_ROOT=./workspace
UPLOAD_MAX_SIZE=104857600  # 100MB
DEFAULT_QUALITY=standard

# Development
DEBUG=true
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379
```

### Key APIs:
| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/workspace/projects` | List all projects |
| `POST /api/v1/workspace/projects` | Create new project |
| `GET /api/v1/takes/{project}/{shot}` | List takes for shot |
| `POST /api/v1/takes/{project}/{shot}` | Create new take |
| `GET /api/v1/git/{project}/status` | Git repository status |
| `WS /api/ws/{client_id}` | WebSocket connection |

### Docker Services:
- **backend**: FastAPI on port 8000
- **frontend**: SvelteKit on port 3000  
- **redis**: Cache and pubsub (optional)

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (interactive)
- **PRDs**: `.bmad-core/prds/` - Product requirements
- **Stories**: `.bmad-core/stories/` - Implementation stories
- **Validation**: `.bmad-core/validation/` - Test reports

---

**Remember**: Think before coding. Use existing structures. Run quality checks.