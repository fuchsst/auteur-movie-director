# AI Film Crew Agents

## Overview

The agent system implements the BMAD methodology by structuring film production around specialized AI agents, each representing a familiar film crew role. These agents collaborate using the CrewAI framework to transform creative concepts into finished cinematic sequences.

## Agent Architecture

### Film Crew Agents
- **Producer** (`producer/`) - Master orchestrator and resource manager
- **Screenwriter** (`screenwriter/`) - Script development and narrative structure
- **Casting Director** (`casting_director/`) - Character asset lifecycle management
- **Art Director** (`art_director/`) - Visual style and aesthetic consistency
- **Cinematographer** (`cinematographer/`) - Scene generation and video creation
- **Sound Designer** (`sound_designer/`) - Audio landscape and voice synthesis
- **Editor** (`editor/`) - Post-production and final assembly

### Agent Implementation Pattern

```python
from crewai import Agent, Tool, Task, Crew

class FilmCrewAgent(Agent):
    """Base class for all film crew agents"""
    
    def __init__(self, role, goal, backstory, tools):
        super().__init__(
            role=role,
            goal=goal, 
            backstory=backstory,
            tools=tools,
            verbose=True,
            allow_delegation=False
        )
```

### Tool Integration
Each agent is equipped with specialized tools that wrap backend API clients:

```python
# Example: Cinematographer tools
cinematographer_tools = [
    generate_video_clip_tool,      # ComfyUI/Wan2GP integration
    apply_camera_control_tool,     # Model-native camera control
    layerflow_compositing_tool,    # Advanced layer generation
    bokeh_enhancement_tool         # Cinematic post-processing
]
```

## Workflow Orchestration

### CrewAI Task Management
```python
def create_film_production_crew():
    crew = Crew(
        agents=[screenwriter, casting_director, cinematographer, sound_designer, editor],
        tasks=[script_task, character_task, video_task, audio_task, assembly_task],
        process=Process.sequential,
        memory=True,
        planning=True
    )
    return crew
```

### Agent Communication
- **Sequential Execution** - Output of one agent becomes input for the next
- **Asset Sharing** - Agents access shared Blender data structures
- **Status Updates** - Real-time progress updates through UI panels

## Development Guidelines

### Agent Creation
1. Define clear **role**, **goal**, and **backstory**
2. Implement specialized **tools** for backend integration
3. Handle **Blender data** through custom properties
4. Provide **error handling** and fallback strategies

### Backend Integration
```python
# Each agent tool wraps backend API calls
@tool("Generate Video Clip")
def generate_video_clip_tool(prompt: str, style_path: str) -> str:
    """Generate video clip using ComfyUI or Wan2GP"""
    backend = select_optimal_backend(prompt, available_vram)
    result = backend.generate_video(prompt, style_path)
    return result.video_path
```

### UI Integration
- Agents triggered through **Blender operators**
- Progress displayed in **custom panels**
- Results stored in **scene custom properties**

## Reference Documentation

- [CrewAI Framework](/.bmad-core/data/blender-addon-development-kb.md#crew-ai-integration)
- [Backend API Integration](/.bmad-core/data/comfyui-api-guide.md)
- [Wan2GP Integration](/.bmad-core/data/wan2gp-api-guide.md)

The agent system transforms complex generative workflows into intuitive film production metaphors.