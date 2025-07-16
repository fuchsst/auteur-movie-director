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

# Testing commands:
make test             # Run all tests
make test-coverage    # Run with coverage report
make test-quick       # Fast unit tests only
make test-e2e         # Full test suite in Docker (CI-like)

# Test specific areas:
cd backend && pytest -xvs tests/test_file.py    # Debug specific backend test
cd frontend && npm test ComponentName            # Test specific frontend component

# Docker testing (recommended for consistency):
docker-compose -f docker-compose.test.yml up     # Run complete test suite
docker-compose -f docker-compose.test.yml down -v # Clean up after tests
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
| `POST /api/v1/export/{project}` | Export project as archive |
| `GET /api/v1/export/{project}/download/{file}` | Download exported archive |
| `WS /api/ws/{client_id}` | WebSocket connection |

### Docker Services:
- **backend**: FastAPI on port 8000
- **frontend**: SvelteKit on port 3000  
- **redis**: Cache and pubsub (optional)

## 🧪 Testing

### Running Tests
- **All Tests**: `make test`
- **With Coverage**: `make test-coverage` (target: 80% minimum)
- **In Docker**: `make test-e2e` (recommended - same as CI)
- **Quick Tests**: `make test-quick` (skip integration tests)

### Test Structure
- **Backend**: `backend/tests/` - pytest with async support
- **Frontend**: `frontend/src/lib/**/*.test.ts` - vitest with Svelte support
- **E2E**: `tests/integration/` - Playwright tests

### Before Committing
```bash
make format && make test  # Format code and run tests
```

See `.bmad-core/methods/TESTING-GUIDE.md` for detailed testing documentation.

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (interactive)
- **PRDs**: `.bmad-core/prds/` - Product requirements
- **Stories**: `.bmad-core/stories/` - Implementation stories
- **Validation**: `.bmad-core/validation/` - Test reports
- **Testing Guide**: `.bmad-core/methods/TESTING-GUIDE.md`

---

**Remember**: Think before coding. Use existing structures. Run quality checks.

## 🚧 Development Progress

### EPIC-003: Function Runner Architecture (86/90 points - 96% complete)

**Completed Stories:**
- ✅ STORY-041: Worker Pool Management (8 points)
- ✅ STORY-042: Task Queue Configuration (7 points)
- ✅ STORY-043: Worker Health Monitoring (5 points)
- ✅ STORY-044: Function Template Registry (8 points)
- ✅ STORY-045: Template Validation System (5 points)
- ✅ STORY-046: Resource Requirement Mapping (5 points)
- ✅ STORY-047: Function Runner API Client (10 points)
- ✅ STORY-048: Progress Tracking System (7 points)
- ✅ STORY-049: Error Handling & Recovery (5 points)
- ✅ STORY-050: Quality Preset System (6 points)
- ✅ STORY-051: End-to-End Integration (8 points)
- ⚠️ STORY-013: Function Runner Foundation (12 points - 60% complete)

**Remaining Stories:**
- 🔲 STORY-052: Performance Testing Suite (4 points)