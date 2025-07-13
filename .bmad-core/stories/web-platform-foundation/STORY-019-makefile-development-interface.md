# STORY-019: Makefile Development Interface

## Story
As a developer, I need a comprehensive Makefile that provides easy-to-use commands for all common development tasks, including Docker compose orchestration and model-specific operations.

## Acceptance Criteria
- [x] Makefile exists with all common development targets
- [x] Docker compose commands are integrated (up, down, logs, etc.)
- [x] Model-specific compose targets work (up-with-comfyui, up-with-litellm)
- [x] Help target displays all available commands with descriptions
- [x] Commands handle dependencies automatically (e.g., installing deps before running)
- [x] Cross-platform compatibility (works on Mac, Linux, Windows with WSL)

## Technical Details

### Required Make Targets

#### Development Commands
- `make dev` - Start both frontend and backend in development mode
- `make dev-backend` - Start only backend server
- `make dev-frontend` - Start only frontend server
- `make install` - Install all dependencies (backend + frontend)
- `make clean` - Clean all build artifacts and caches

#### Docker Commands
- `make docker-up` - Start all services with docker-compose
- `make docker-down` - Stop all services
- `make docker-logs` - Show logs from all containers
- `make docker-build` - Build all Docker images
- `make docker-clean` - Remove containers, volumes, and images

#### Model-Specific Commands
- `make up-with-comfyui` - Start platform with ComfyUI
- `make up-with-litellm` - Start platform with LiteLLM
- `make up-with-audio` - Start platform with audio services
- `make up-all` - Start platform with all AI services

#### Testing & Quality
- `make test` - Run all tests
- `make test-backend` - Run backend tests only
- `make test-frontend` - Run frontend tests only
- `make lint` - Run linters on all code
- `make format` - Auto-format all code

#### Utility Commands
- `make help` - Display all available commands
- `make setup-env` - Create .env files from templates
- `make check-deps` - Verify all dependencies are installed

### Implementation Requirements

```makefile
# Header with description
.PHONY: help
help: ## Display this help message
	@echo "Auteur Movie Director - Development Commands"
	@echo "==========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Dependency management
.PHONY: check-deps
check-deps: ## Check if all dependencies are installed
	@which python3 >/dev/null || (echo "Python 3 not found" && exit 1)
	@which node >/dev/null || (echo "Node.js not found" && exit 1)
	@which docker >/dev/null || (echo "Docker not found" && exit 1)
	@which docker-compose >/dev/null || (echo "Docker Compose not found" && exit 1)

# Environment setup
.PHONY: setup-env
setup-env: ## Create .env files from templates
	@test -f .env || cp .env.example .env
	@test -f backend/.env || cp backend/.env.template backend/.env
	@test -f frontend/.env || cp frontend/.env.template frontend/.env
```

### Docker Compose Integration

The Makefile should wrap docker-compose commands with useful defaults:
- Set project name: `-p auteur-movie-director`
- Use correct compose file: `-f docker-compose.yml`
- Handle additional compose files for different model configurations

### Error Handling

- Check for required dependencies before running commands
- Provide helpful error messages when things fail
- Suggest fixes for common issues
- Exit with proper status codes

## Dependencies
- Make utility installed on system
- Docker and Docker Compose
- Python 3.12+ and Node.js 20+
- All setup scripts from STORY-001

## Story Points: 3

## Priority: High

## Implementation Status

**Completed: February 3, 2025**

All acceptance criteria have been met:

✅ **Development Commands**
- Added `dev-backend` and `dev-frontend` targets
- All development targets functional

✅ **Docker Commands**
- Added `docker-clean` target for cleaning Docker resources
- Added profile-based targets for AI services:
  - `docker-up-ai` - All AI services
  - `docker-up-comfyui` - ComfyUI only
  - `docker-up-audio` - Audio services
  - `docker-up-video` - Video services
  - `docker-up-full` - All services

✅ **Docker Compose Profiles**
- Added profiles to docker-compose.yml:
  - `ai` - All AI services
  - `comfyui` - ComfyUI service
  - `audio` - RVC and AudioLDM
  - `video` - Wan2GP
  - `full` - Everything

✅ **Help Documentation**
- Updated help target with new commands
- Clear descriptions for all targets

The Makefile now provides a comprehensive interface for all development tasks with proper Docker integration and profile support.

## Status: ✅ Completed

## Related Stories
- STORY-001: Development Environment Setup
- STORY-020: Docker Compose Orchestration