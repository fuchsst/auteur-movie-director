# Blender Movie Director - Main Addon Module

## Overview

The main addon module implementing a BMAD-architected generative film studio for Blender. This module transforms Blender into a local-first, agent-driven production environment capable of creating complete cinematic sequences through specialized AI agents.

## Architecture

### Core Components
- **Producer Agent** (`agents/producer/`) - Master orchestrator managing workflow and resource allocation
- **Film Crew Agents** (`agents/`) - Specialized AI agents for each production role
- **Backend Integration** (`backend/`) - API clients for ComfyUI, Wan2GP, and LiteLLM
- **Blender UI** (`ui/`) - Native panels, operators, and property integration
- **Configuration** (`config/`) - Templates and hardware optimization
- **Workflows** (`workflows/`) - Pre-configured templates for generative tasks

### Data Model
The addon treats creative elements as interconnected "Generative Assets" stored directly in the .blend file:
- 🎭 **Characters** - Empty objects with LoRA and voice model paths
- 🎨 **Styles** - Visual aesthetic definitions and style LoRAs  
- 🗺️ **Locations** - Environment settings and lighting descriptions
- 🎬 **Scenes** - Collections containing shot sequences
- 🎥 **Shots** - Individual video clips with dialogue and camera notes

## Development Patterns

### Agent Implementation
```python
# Each agent follows CrewAI patterns
from crewai import Agent, Tool, Task

class CinematographerAgent(Agent):
    role = "Expert in cinematic visual storytelling"
    goal = "Transform script descriptions into compelling video clips"
    backstory = "Professional cinematographer with expertise in camera work and composition"
```

### Blender Integration
```python
# Use native Blender patterns
import bpy
from bpy.props import StringProperty, PointerProperty
from bpy.types import Panel, Operator, PropertyGroup

class MOVIE_DIRECTOR_PT_main_panel(Panel):
    bl_label = "Movie Director"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Movie Director"
```

### Asset Management
```python
# Store data in .blend file custom properties
scene.movie_director.project_name = "My Film"
character_obj.movie_director.character_lora_path = "//assets/character.safetensors"
```

## Key Integration Points

- **Agents** communicate via CrewAI framework
- **Backend** services accessed through async API clients  
- **UI** panels trigger agent workflows through operators
- **Assets** managed through Blender's Asset Browser integration
- **Workflows** selected automatically based on task requirements

## Reference Documentation

- [CrewAI Framework](/.bmad-core/data/blender-addon-development-kb.md#crew-ai-integration)
- [Blender API Patterns](/.bmad-core/data/bpy-*.md)
- [Backend Integration](/.bmad-core/data/*-api-guide.md)

## Development Flow

1. **Script Development** → Screenwriter agent → Scene/Shot objects created
2. **Asset Creation** → Casting/Art Director agents → Character/Style assets
3. **Video Generation** → Cinematographer agent → Shot video clips  
4. **Audio Creation** → Sound Designer agent → Dialogue and effects
5. **Final Assembly** → Editor agent → VSE sequence composition

The addon transforms Blender from a 3D modeling tool into a complete generative film studio.