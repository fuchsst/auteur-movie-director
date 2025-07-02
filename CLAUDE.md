Above all: YOU ARE A PROFESSIONAL SENIOR SOFTWARE DEVELOPER!!! this means you do not just duplicate code or just generate the first code that comes to your mind. You think, you leverage exisitng strucutres, you consult the documentation, you reflect if this is the best solution before writing any code. Be the best in your class! You are pragmatic, do not overengineer (e.g. too many perfomance optimisations). Choose one appraoch, avoid too many fallbacks (fail early!)

## CRITICAL: Code Quality Workflow

**ALWAYS** follow this workflow when writing code:
1. After creating/modifying files: `make format` or `npm run format`
2. Before considering task complete: `make lint` or `npm run lint`
3. Before any git operation: `make test` or `npm run test`
4. If hooks block you: Read the error and run the suggested command

use `npm run` commands as the primary way to run project tasks

Follow the BMAD method as defined in `.bmad-core/tasks/`

# Generative Media Studio - Project Guide

## Project Overview

A web-based platform that transforms narrative concepts into cinematic sequences using AI agents and distributed generative engines. Built on the BMAD (Breakthrough Method of Agile AI-Driven Development) framework for modern web development.

### Core Architecture

**Three-tier system:**
1. **Frontend Layer**: SvelteKit web application with node-based canvas
2. **Backend Layer**: FastAPI service with WebSocket support
3. **Processing Layer**: Containerized AI models via Function Runner pattern

**AI Agent Crew:**
- **Producer**: Master orchestrator, resource manager (VRAM budgeting)
- **Screenwriter**: Script development via LLM
- **Casting Director**: Character asset management (LoRAs, voice models)
- **Art Director**: Visual style consistency
- **Cinematographer**: Video generation and camera control
- **Sound Designer**: Audio generation (dialogue, effects)
- **Editor**: Final assembly with EDL export

### Key Technical Features

**Regenerative Content Model:**
- Creative definitions stored in project.json
- Generated content as recreatable file references
- Version control friendly with Git integration

**Asset Management:**
- File-based project structure
- Takes system for non-destructive versioning
- Relational data model for Characters, Styles, Locations, Scenes, Shots

**VRAM Budgeting System:**
- Dynamic memory profiling
- Sequential execution for limited hardware
- Model swapping to prevent OOM errors

## Development Setup

### Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/generative-media-studio.git
cd generative-media-studio

# Install npm dependencies (includes concurrently)
npm install

# Run automated setup (checks prerequisites, installs all dependencies)
npm run setup

# Start development servers (frontend + backend)
npm run dev

# Alternative: Use traditional Makefile
make help  # View all available commands
make dev   # Start development servers
```

### About Dependencies

This project uses modern dependency management:
- **npm/pnpm** for JavaScript dependencies (frontend)
- **pip/poetry** for Python dependencies (backend)
- **Docker** for containerized AI models
- Lock files ensure reproducible builds

### Project Structure

```
generative-media-studio/
├── backend/                 # FastAPI application
│   ├── app/                # Application code
│   ├── services/           # Business logic
│   └── requirements.txt    # Python dependencies
├── frontend/               # SvelteKit application
│   ├── src/               # Source code
│   └── package.json       # Node dependencies
├── tests/                  # Test suite
├── scripts/                # Dev automation
├── package.json           # Root npm scripts
└── docker-compose.yml     # Service orchestration
```

### Development Commands

The project uses npm scripts as the primary task runner, with Makefile as an alternative:

#### NPM Scripts (Recommended)

```bash
# Setup & Installation
npm run setup              # Complete setup with prerequisite checks
npm run setup:check        # Check prerequisites only
npm run setup:env          # Create environment files

# Development
npm run dev                # Start frontend + backend concurrently
npm run dev:backend        # Backend server only
npm run dev:frontend       # Frontend server only

# Testing
npm run test               # Run all tests
npm run test:backend       # Python tests
npm run test:frontend      # JavaScript tests
npm run test:integration   # Integration tests only

# Code Quality
npm run lint               # Lint all code
npm run format             # Auto-format code

# Utilities
npm run clean              # Clean build artifacts
npm run workspace:init     # Initialize workspace
npm run project:create     # Create new project
```

#### Makefile (Alternative)

```bash
# Quick access to npm scripts
make dev            # Same as npm run dev
make test           # Same as npm run test
make lint           # Same as npm run lint

# Docker commands
make docker-up      # Start with docker-compose
make docker-down    # Stop containers
make docker-logs    # View container logs
```

All commands handle dependency management automatically - no manual virtual environment activation needed!

### Testing Workflow

```bash
# Run all tests
npm run test

# Run backend tests only
npm run test:backend

# Run frontend tests only
npm run test:frontend

# Run integration tests
npm run test:integration

# Generate coverage report
npm run test:backend -- --cov
```

## Implementation Roadmap

**Current Sprint Focus:**
1. Web platform foundation (SvelteKit + FastAPI)
2. File-based project management system
3. WebSocket real-time communication

**Next Steps:**
- Implement Production Canvas with Svelte Flow
- Create Function Runner architecture
- Build quality management system

## Critical Constraints

**Hardware Requirements:**
- Minimum: RTX 4080 (16GB VRAM)
- Recommended: RTX 4090 (24GB VRAM)
- LLM serving requires additional VRAM

**Backend Services Required:**
- ComfyUI (port 8188)
- Wan2GP (port 7860)
- RVC (port 7865)
- AudioLDM (port 7863)
- LiteLLM (local inference)

## Development Guidelines

1. **Code Organization:**
   - Follow web development best practices
   - Use TypeScript for frontend type safety
   - Implement proper error handling

2. **Testing:**
   - Unit tests for all services
   - Integration tests for API endpoints
   - E2E tests for critical user flows

3. **Performance:**
   - Optimize WebSocket message handling
   - Implement proper caching strategies
   - Monitor API response times

4. **UI Design:**
   - Use responsive design principles
   - Keep the node canvas performant
   - Provide clear feedback for async operations

## Environment Variables

Key settings in `.env`:
```
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000
WORKSPACE_ROOT=./workspace
DEFAULT_QUALITY=standard
DEBUG=true
LOG_LEVEL=INFO
```

## Common Issues

**CORS errors:** Check that frontend and backend URLs are correctly configured
**WebSocket disconnects:** Ensure stable network connection and check heartbeat settings
**File permission errors:** Verify workspace directory has proper write permissions

---

For detailed implementation specifics, refer to PRDs in `.bmad-core/prds/` directory.

## Development Workflow - Code Quality Commands

### IMPORTANT: When to Run Quality Checks

When developing features, ALWAYS run these commands at the appropriate times:

#### Before Writing Code
```bash
# Ensure clean working directory
make clean
npm run setup:env
```

#### While Writing Code
```bash
# Format code after making changes
make format
# Or
npm run format

# Check linting frequently
make lint
# Or  
npm run lint
```

#### After Writing Code (Before Committing)
```bash
# ALWAYS run this sequence:
make format    # Auto-format code
make lint      # Check code quality
make test      # Run all tests

# Or using npm:
npm run format
npm run lint  
npm run test
```

#### When Tests Fail
```bash
# Run specific test suites
npm run test:backend    # Backend only
npm run test:frontend   # Frontend only
npm run test:quick      # Fast tests only

# Debug specific test
cd backend && pytest tests/test_api.py -v -s
```

### Hook Integration

If hooks are configured (see https://docs.anthropic.com/en/docs/claude-code/hooks), these commands may trigger automatically. If a hook blocks an action:

1. Check the hook output for specific issues
2. Run `make format` to fix formatting issues
3. Run `make lint` to identify code quality issues
4. Run `make test` to ensure tests pass
5. If still blocked, ask the user to check their hooks configuration

### Command Reference by Task

#### When creating new files:
1. Create the file
2. Run `make format` immediately
3. Run `make lint` to check for issues

#### When modifying existing files:
1. Make changes
2. Run `make format` on the file
3. Run `make lint` on the file
4. Run relevant tests

#### Before any git operation:
1. `make format` - Format all code
2. `make lint` - Check all code quality
3. `make test` - Run full test suite

#### When blocked by hooks:
1. Read the hook error message
2. Run the suggested make command
3. Fix any remaining issues manually
4. Try the action again

### Important Notes

- **ALWAYS** run `make lint` after writing code to ensure it meets quality standards
- **ALWAYS** run `make test` before considering a task complete
- If the user asks you to commit, run the full quality check sequence first
- If hooks are blocking, determine which check failed and run the appropriate command