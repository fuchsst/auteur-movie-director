# Story: Development Environment Setup

**Story ID**: STORY-001  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Infrastructure  
**Points**: 3 (Medium)  
**Priority**: High  
**Status**: ✅ Completed (January 2025)  

## Story Description
As a developer, I need a containerized development environment with streamlined setup process so that I can quickly start contributing to the Auteur Movie Director project with all necessary dependencies, services, and configurations in place, ensuring consistency across all development machines.

## Acceptance Criteria

### Functional Requirements
- [x] Running `make setup` or `npm run setup` completes successfully on Windows, Mac, and Linux
- [x] Setup script checks for all required prerequisites including Docker and Git LFS
- [x] Docker Compose orchestrates all core services with a single command
- [x] Makefile provides primary developer interface for common tasks
- [x] Development servers can be started with `make up` or `npm run dev`
- [x] Git LFS is properly configured for all new projects (via GitService)

### Technical Requirements
- [x] Implement prerequisite checking for: Git, Git LFS, Docker Engine, Docker Compose, Node.js 20+, Python 3.11+
- [x] Create multi-stage Dockerfiles for optimized frontend and backend images
- [x] Configure docker-compose.yml with all core services (frontend, backend, worker, redis)
- [x] Implement Makefile as primary developer interface with intuitive targets
- [x] Create `.env.template` files for all configurable settings
- [x] Setup scripts handle both npm and Docker dependency installation
- [x] Implement workspace directory structure with proper volume mounts
- [x] Configure hot-reloading for both frontend (Vite HMR) and backend (Uvicorn)

### Documentation Requirements
- [x] Update README.md with containerized quick start instructions
- [x] Document all Makefile targets with clear descriptions
- [x] Document all npm scripts as alternative interface
- [x] Include Docker troubleshooting section
- [x] Add Git LFS setup and verification instructions
- [x] Document workspace and project structure requirements

## Implementation Notes

### Core Tooling Stack
```
Host Machine Requirements:
├── Git (with Git LFS extension) - MANDATORY
├── Docker Engine & Docker Compose
├── Node.js 20+ (for IDE support)
├── Python 3.11+ (for local tooling)
└── Make (for developer interface)

Future Requirements (for generative pipeline):
├── NVIDIA Docker Runtime (for GPU support)
├── CUDA 11.8+ (for AI model execution)
└── 16GB+ VRAM (recommended for quality generation)
```

### Docker Service Architecture
```yaml
services:
  frontend:   # SvelteKit on port 5173
  backend:    # FastAPI on port 8000
  worker:     # Celery background tasks
  redis:      # Message broker on port 6379
  # Future: crew-orchestrator for multi-agent workflows
```

### Makefile Primary Targets
```makefile
# Core workflow commands
make help          # Show all available commands
make setup         # Complete initial setup
make build         # Build all Docker images
make up            # Start all services
make down          # Stop and clean up
make logs          # Follow service logs
make test          # Run test suite

# Development helpers
make shell-backend  # Interactive backend shell
make shell-frontend # Interactive frontend shell
make new-project    # Scaffold new project

# Optional model integration
make up-with-comfyui # Start with AI model
```

### Setup Script Structure
```bash
scripts/
├── setup.js           # Main orchestrator
├── check-prereqs.js   # Verify ALL requirements
├── setup-env.js       # Create .env files
├── setup-deps.js      # Install dependencies
├── validate-env.js    # Verify configuration
└── create-project.sh  # Project scaffolding
```

### Environment Configuration
```env
# .env.template
# Core settings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=5173
WORKSPACE_ROOT=./workspace

# Service URLs
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
VITE_BACKEND_URL=http://backend:8000

# Development settings
NODE_ENV=development
LOG_LEVEL=INFO
DEBUG=true

# Creative Pipeline settings
DEFAULT_QUALITY=standard
ENABLE_TAKES_SYSTEM=true
ASSET_LIBRARY_PATH=./workspace/Library
```

### Multi-Stage Frontend Dockerfile Pattern
```dockerfile
# Builder stage with all dependencies
FROM node:20-alpine AS builder
# ... build process ...

# Final stage with only runtime needs
FROM node:20-alpine
# ... minimal runtime image ...
```

## Dependencies
- Docker and Docker Compose for containerization
- Git LFS for large file handling (MANDATORY)
- Make for developer workflow interface
- Node.js for frontend tooling
- Python for backend development
- Redis for message brokering

## Testing Criteria
- [ ] Clean install works on fresh system with only prerequisites
- [ ] All services start and communicate correctly
- [ ] Hot-reloading works for both frontend and backend changes
- [ ] Git LFS properly handles large files in test project
- [ ] Makefile targets execute without errors
- [ ] Volume mounts provide proper file access
- [ ] Re-running setup is idempotent
- [ ] Missing prerequisites show actionable error messages

## Definition of Done
- [ ] All Dockerfiles created with multi-stage optimization
- [ ] docker-compose.yml orchestrates all services
- [ ] Makefile provides complete developer interface
- [ ] Setup scripts check all prerequisites including Git LFS
- [ ] Environment templates include all required variables
- [ ] README updated with Docker-first instructions
- [ ] All services tested on Windows, Mac, and Linux
- [ ] PR approved with successful CI/CD run
- [ ] No hardcoded values or platform-specific issues

## Story Links
- **Blocks**: All other development stories
- **Related PRD**: PRD-001-web-platform-foundation
- **Architecture Ref**: /concept/breakdown/project_setup.md