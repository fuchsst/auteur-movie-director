# Blender Movie Director - Main Addon Module

## Overview

The main addon module implementing a BMAD-architected generative film studio for Blender, as defined in the [Main Project Plan](/.bmad-core/CLAUDE.md). This module transforms Blender into a local-first, agent-driven production environment capable of creating complete cinematic sequences through specialized AI agents.

## Architecture

Following the three-tier architecture from the project plan:

### 1. UI Layer (The Blender Interface)
- **Location**: `ui/` directory
- **Components**: Panels, operators, properties, asset browser integration
- **Purpose**: Native Blender UI for seamless artist interaction

### 2. Orchestration Layer (The Agent Core)  
- **Location**: `agents/` directory
- **Components**: 7 film crew agents implemented with CrewAI
- **Purpose**: Intelligent workflow orchestration and task routing

### 3. Backend Runners Layer
- **Location**: `backend/` directory
- **Services**: 4 backend services + LLM integration
  - ComfyUI (port 8188)
  - Wan2GP (port 7860)
  - RVC (port 7865)
  - AudioLDM (port 7863)
  - LiteLLM (Python library for LLMs)

## Data Model - Regenerative Content Architecture

Following [PRD-007: Regenerative Content Model](/.bmad-core/prds/PRD-007-regenerative-content-model.md):

### Stored in .blend file (Persistent Project Data):
```python
# Custom properties on Blender objects
- 🎭 Characters: descriptions, reference paths, training parameters
- 🎨 Styles: aesthetic definitions, style references
- 🗺️ Locations: environment descriptions, lighting notes
- 🎬 Scenes: narrative structure, location assignments
- 🎥 Shots: dialogue, camera directions, generation parameters
```

### Generated Content (File References Only):
```python
# Paths to generated files, not embedded
- Character LoRAs (.safetensors)
- Style LoRAs (.safetensors)
- Video clips (.mp4)
- Audio tracks (.wav)
- Preview images (.png)
```

## Key Components

### Agent System (`agents/`)
Implements the 7 BMAD personas:
1. **Producer** - Master orchestrator ([PRD-001](/.bmad-core/prds/PRD-001-backend-integration-service-layer.md))
2. **Screenwriter** - Script development ([PRD-002](/.bmad-core/prds/PRD-002-intelligent-script-to-shot-breakdown.md))
3. **Casting Director** - Character consistency ([PRD-003](/.bmad-core/prds/PRD-003-character-consistency-engine.md))
4. **Art Director** - Style consistency ([PRD-004](/.bmad-core/prds/PRD-004-style-consistency-framework.md))
5. **Cinematographer** - Video generation
6. **Sound Designer** - Audio creation
7. **Editor** - Final assembly

### Backend Integration (`backend/`)
Per [PRD-001](/.bmad-core/prds/PRD-001-backend-integration-service-layer.md):
- Service discovery with 5-second scan
- Connection pooling and health monitoring
- Intelligent task routing based on VRAM
- Python client libraries (comfyui_api_client, gradio_client, litellm)

### UI Components (`ui/`)
- **Panels**: Project overview, agent status, generation controls
- **Operators**: Trigger workflows, manage assets
- **Properties**: Store project data in .blend file
- **Asset Browser**: Visual asset management

### Workflows (`workflows/`)
Pre-configured templates for common tasks:
- Character creation workflows
- Style application pipelines
- Video generation chains
- Audio synthesis flows

## Development Patterns

### Agent Implementation
```python
from crewai import Agent, Tool

class CinematographerAgent(Agent):
    role = "Expert in cinematic visual storytelling"
    goal = "Transform script descriptions into compelling video clips"
    backstory = "Professional cinematographer with expertise..."
    tools = [ComfyUITool(), Wan2GPTool()]
```

### Blender Integration
```python
import bpy
from bpy.types import Panel, Operator, PropertyGroup

class MOVIE_DIRECTOR_PT_main_panel(Panel):
    bl_label = "Movie Director"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Movie Director"
```

### Regenerative Workflow
```python
def regenerate_character_assets(character_obj):
    """Regenerate character content from stored parameters"""
    # Read parameters from .blend file
    description = character_obj.movie_director_character.description
    ref_path = character_obj.movie_director_character.reference_images_path
    
    # Trigger regeneration
    casting_director.regenerate_character_lora(description, ref_path)
    
    # Update file references
    character_obj.movie_director_character.character_lora_path = new_path
```

## Testing

Run tests using helper scripts:
```bash
# Run all tests
./scripts/test.sh all

# Test specific components
pytest tests/test_service_discovery.py -v
pytest tests/test_agents.py -v

# Manual testing
./scripts/run-blender.sh
```

## Configuration

Environment setup in `.env`:
```bash
# Backend service ports
COMFYUI_PORT=8188
WAN2GP_PORT=7860
RVC_PORT=7865
AUDIOLDM_PORT=7863

# LLM API keys
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

## Reference Documentation

### Project Documentation
- [Main Project Plan](/.bmad-core/CLAUDE.md)
- [PRDs](/.bmad-core/prds/) - Product requirement documents
- [User Stories](/.bmad-core/stories/) - Implementation stories

### Technical References
- [Blender API](/.bmad-core/data/bpy-*.md)
- [ComfyUI API Guide](/.bmad-core/data/comfyui-api-guide.md)
- [CrewAI Framework](https://docs.crewai.com/)

The addon transforms Blender from a 3D modeling tool into a complete regenerative film studio where creative intent drives automated content creation.