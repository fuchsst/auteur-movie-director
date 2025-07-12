Use `make` to run project commands!
Avoid fallbacks! Fail early instead! Use one clear consistent approach! Assume prerequisits, and fail if they are not met!

# Blender Movie Director - Workspace Instructions

## Project Overview
AI-powered Blender addon that transforms narrative concepts into cinematic sequences using CrewAI agents and local generative engines (ComfyUI, Wan2GP, LiteLLM).

**Architecture**: UI Layer → AI Orchestration (CrewAI) → Backend Services

## Development Standards
- **Professional approach**: Think before coding, leverage existing structures, consult documentation
- Use `make` for all project commands
- Follow BMAD method from `.bmad-core/tasks/`
- Target: Blender 4.4+, RTX 4090+ (24GB VRAM minimum)

## Key Workflows

### Addon Development Lifecycle
1. **Foundation**: Addon structure, UI panels, custom properties
2. **AI Integration**: CrewAI agents, backend connections
3. **Production Pipeline**: Script-to-video workflow, character/audio systems
4. **Integration & Polish**: VSE assembly, Asset Browser, UX optimization
5. **Quality Assurance**: E2E testing, Blender Integration testing using Blender MCP

### Film Production Pipeline
**Concept** → **Script** → **Pre-Production** → **Production** → **Post-Production**

## Agent Roles
- **Producer**: Master orchestrator, resource management
- **Screenwriter**: Script development via LLM
- **Cinematographer**: Video generation (ComfyUI/Wan2GP)
- **Sound Designer**: Audio generation and voice cloning
- **Editor**: VSE assembly and final output

## Core Tasks (`.bmad-core/tasks/`)
- `create-addon-structure`: Foundation with bl_info, registration, Blender 4.0+ compatibility
- `design-ui-panels`: Calm, consistent UI following Blender guidelines
- `implement-crewai-agents`: Film crew agents with CrewAI framework
- `setup-backend-integration`: Robust backend connections with error handling
- `create-addon-feature`: Feature specification based on project roadmap

## Essential Commands
```bash
make setup          # Dev environment setup
make run            # Launch Blender with addon
make test           # Run all tests
make services       # Start backend services
make package        # Create addon .zip
```

## Critical Requirements
- **Backend Services**: ComfyUI (8188), Wan2GP (7860), LiteLLM (4000)
- **VRAM Management**: Sequential loading, resource budgeting, OOM prevention
- **UI Standards**: Progressive disclosure, Blender-native components, responsive design
- **Error Handling**: Graceful degradation, clear user feedback, offline-first operation

## Current Sprint Focus
1. Service discovery and backend connectivity
2. Basic UI structure with preferences
3. Producer agent as master orchestrator
4. Core workflow templates for ComfyUI

**Success Criteria**: Addon loads cleanly, backends connect, basic film production workflow functional.
