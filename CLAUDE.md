Above all: YOU ARE A PROFESSIONAL SENIOR SOFTWARE DEVELOPER!!! this means you do not just duplicate code or just generate the first code that comes to your mind. You think, you leverage exisitng strucutres, you consult the documentation, you reflect if this is the best solution before writing any code. Be the best in your class!

# Blender Movie Director (BMAD) - Project Guide

## Project Overview

A Blender addon that transforms narrative concepts into cinematic sequences using AI agents and local generative engines (ComfyUI, Wan2GP). Built on the BMAD (Breakthrough Method of Agile AI-Driven Development) framework.

### Core Architecture

**Three-tier system:**
1. **UI Layer**: Blender-native panels and operators
2. **Orchestration Layer**: Producer agent managing AI crew via CrewAI
3. **Backend Layer**: Local services (ComfyUI, Wan2GP, RVC, AudioLDM, LiteLLM)

**AI Agent Crew:**
- **Producer**: Master orchestrator, resource manager (VRAM budgeting)
- **Screenwriter**: Script development via LLM
- **Casting Director**: Character asset management (LoRAs, voice models)
- **Art Director**: Visual style consistency
- **Cinematographer**: Video generation and camera control
- **Sound Designer**: Audio generation (dialogue, effects)
- **Editor**: Final assembly in VSE

### Key Technical Features

**Regenerative Content Model:**
- Creative definitions stored in .blend file
- Generated content as recreatable file references
- Version control friendly (small .blend files)

**Asset Management:**
- Custom properties on Blender objects
- Integration with Asset Browser
- Relational data model for Characters, Styles, Locations, Scenes, Shots

**VRAM Budgeting System:**
- Dynamic memory profiling
- Sequential execution for limited hardware
- Model swapping to prevent OOM errors

## Development Setup

### Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/blender-movie-director.git
cd blender-movie-director

# View all available commands
make help

# Set up development environment (installs UV if needed)
make setup

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run Blender with addon
make run
```

### About UV

This project uses [UV](https://docs.astral.sh/uv/) by Astral for ultra-fast Python dependency management. UV is automatically installed by the setup script if not present. Benefits include:
- 10-100x faster than pip
- Built-in virtual environment management
- Lock file support for reproducible builds
- No manual venv activation needed

### Project Structure

```
blender-movie-director/
├── blender_movie_director/    # Addon code
│   ├── agents/               # AI agents (CrewAI)
│   ├── backend/             # Service integrations
│   ├── ui/                  # Blender UI
│   └── workflows/           # ComfyUI templates
├── tests/                   # Test suite
├── scripts/                 # Dev automation
├── pyproject.toml          # Project config & dependencies
└── uv.lock                 # Lock file (auto-generated)
```

### Development Commands (via Makefile)

All project commands should be run through the Makefile for consistency:

```bash
# Setup & Installation (UV installed automatically)
make setup          # Full dev environment setup
make setup-test     # Test environment only
make setup-clean    # Clean setup (removes existing)
make setup-prod     # Production environment

# Development
make run            # Launch Blender with addon
make test           # Run all tests
make test-quick     # Fast tests (no integration)
make test-coverage  # Generate coverage report
make lint           # Code quality checks
make format         # Auto-format code

# Backend Services
make services       # Start all services
make services-stop  # Stop all services
make services-status # Check service status

# Distribution & Blender
make package        # Create addon .zip
make clean          # Remove build artifacts
make blender-deps   # Install deps in Blender's Python

# UV Management
make uv-update      # Update UV to latest version
make uv-lock        # Regenerate lock file
```

The Makefile wraps the scripts in `scripts/` directory. All commands use UV for dependency management - no manual virtual environment activation needed!

### Testing Workflow

```bash
# Start backend services
make services

# Run all tests
make test

# Run quick tests (no integration)
make test-quick

# Generate coverage report
make test-coverage

# Manual testing (when services are running)
./scripts/run-script.sh tests/manual_test_discovery.py
```

## Implementation Roadmap

**Current Sprint Focus:**
1. Service discovery and backend connectivity
2. Basic UI structure and preferences
3. Agent framework setup with CrewAI

**Next Steps:**
- Implement Producer agent orchestration
- Create workflow templates for ComfyUI
- Build asset management system

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
   - Follow Blender addon conventions
   - Use type hints and docstrings
   - Implement proper error handling

2. **Testing:**
   - Unit tests for all agents
   - Integration tests for backend services
   - Manual test scripts for UI components

3. **VRAM Management:**
   - Profile all model usage
   - Implement sequential loading
   - Test on minimum hardware

4. **UI Design:**
   - Use Blender's native components
   - Keep panels organized by agent role
   - Provide clear feedback for long operations

## Environment Variables

Key settings in `.env`:
```
BLENDER_PATH=/path/to/blender
COMFYUI_PORT=8188
WAN2GP_PORT=7860
DEBUG=true
LOG_LEVEL=INFO
```

## Common Issues

**Import errors:** Ensure virtual environment is activated
**Service discovery fails:** Check backend services are running
**VRAM errors:** Enable sequential execution in preferences

---

For detailed implementation specifics, refer to agent-specific CLAUDE.md files in subdirectories.