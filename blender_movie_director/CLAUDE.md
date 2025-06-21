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

### Data Model - Regenerative Content Architecture
The addon follows a **regenerative content model** where only project definitions are stored in the .blend file, while all generated content exists as file references that can be recreated at any time:

**Stored in .blend file (Persistent Project Data):**
- 🎭 **Characters** - Descriptions, prompts, reference image paths, LoRA training parameters
- 🎨 **Styles** - Visual aesthetic definitions, style prompts, reference image paths  
- 🗺️ **Locations** - Environment descriptions, lighting notes, reference materials
- 🎬 **Scenes** - Narrative structure, scene descriptions, location assignments
- 🎥 **Shots** - Dialogue text, camera directions, generation parameters, character/style assignments

**Generated Content (File References Only):**
- Character LoRA models (.safetensors) - Regenerated from reference images and parameters
- Style LoRA models (.safetensors) - Recreated from style definitions and training data
- Video clips (.mp4) - Regenerated from shot parameters and current model versions
- Audio tracks (.wav) - Recreated from dialogue text and voice model settings
- Images (.png) - Thumbnails and reference materials

**Benefits of Regenerative Architecture:**
- **Version Control Friendly** - .blend files remain small and manageable
- **Model Evolution** - Content automatically improves as AI models are updated
- **Storage Efficiency** - Generated assets don't bloat project files
- **Collaboration** - Teams share project definitions, not large generated files
- **Iterative Refinement** - Easy to regenerate content with modified parameters

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

### Asset Management - Regenerative Model
```python
# Store project definitions in .blend file custom properties
scene.movie_director.project_name = "My Film"
character_obj.movie_director_character.description = "Young warrior with determined expression"
character_obj.movie_director_character.reference_images_path = "//references/warrior_ref/"

# Generated content stored as file references only
character_obj.movie_director_character.character_lora_path = "//generated/character_warrior.safetensors"
shot_obj.movie_director_shot.video_clip_path = "//generated/shot_001.mp4"

# Regeneration workflow
def regenerate_character_assets(character_obj):
    """Regenerate all character content from stored definitions"""
    # Read stored parameters
    description = character_obj.movie_director_character.description
    ref_path = character_obj.movie_director_character.reference_images_path
    
    # Trigger regeneration via backend
    casting_director.regenerate_character_lora(description, ref_path)
    
    # Update file reference paths
    character_obj.movie_director_character.character_lora_path = new_lora_path
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

## Development Flow - Regenerative Workflow

1. **Project Definition** → Screenwriter agent → Scene/Shot definitions stored in .blend
2. **Asset Definition** → Casting/Art Director agents → Character/Style parameters stored
3. **Content Generation** → Cinematographer agent → Video clips generated and referenced  
4. **Audio Generation** → Sound Designer agent → Audio tracks generated and referenced
5. **Final Assembly** → Editor agent → VSE sequence with generated file references

**Regeneration Triggers:**
- Model updates → Automatically regenerate all content with improved quality
- Parameter changes → Regenerate specific assets with modified settings
- Batch regeneration → Recreate entire project with new models/settings
- Selective regeneration → Update only specific shots/characters/styles

**Version Control Benefits:**
- .blend files remain small (KB vs GB) containing only project logic
- Generated assets stored separately and can be gitignored
- Teams collaborate on creative intent, not generated files
- Easy to experiment with different AI models and settings

The addon transforms Blender from a 3D modeling tool into a complete regenerative film studio where creative intent drives automated content creation.