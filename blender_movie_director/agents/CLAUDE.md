# AI Film Crew Agents

## Overview

The agent system implements the BMAD methodology as defined in the [Project Plan](/.bmad-core/CLAUDE.md) by structuring film production around specialized AI agents. Each agent represents a familiar film crew role and collaborates using the CrewAI framework to transform creative concepts into finished cinematic sequences.

## Agent Architecture

### The 7 Film Crew Agents
As specified in the main project plan:

1. **Producer** (`producer/`) - Master orchestrator and resource manager
   - Interprets user actions from UI
   - Manages project state in .blend file
   - Orchestrates workflow between agents
   - Implements VRAM budgeting system

2. **Screenwriter** (`screenwriter/`) - Script development and narrative structure
   - References [PRD-002: Intelligent Script-to-Shot Breakdown](/.bmad-core/prds/PRD-002-intelligent-script-to-shot-breakdown.md)
   - Transforms concepts into formatted screenplays
   - Parses scripts into Scene/Shot data structures

3. **Casting Director** (`casting_director/`) - Character asset lifecycle management
   - Implements [PRD-003: Character Consistency Engine](/.bmad-core/prds/PRD-003-character-consistency-engine.md)
   - Manages character LoRA training
   - Ensures facial and identity consistency

4. **Art Director** (`art_director/`) - Visual style and aesthetic consistency
   - Follows [PRD-004: Style Consistency Framework](/.bmad-core/prds/PRD-004-style-consistency-framework.md)
   - Maintains cohesive visual look
   - Manages style LoRAs and references

5. **Cinematographer** (`cinematographer/`) - Scene generation and video creation
   - Primary visual generation agent
   - Routes tasks between ComfyUI and Wan2GP
   - Implements camera control strategies

6. **Sound Designer** (`sound_designer/`) - Audio landscape and voice synthesis
   - Integrates RVC for voice cloning
   - Uses AudioLDM for sound effects
   - Synchronizes audio with video

7. **Editor** (`editor/`) - Post-production and final assembly
   - Assembles clips in Blender's VSE
   - Applies video restoration (SeedVR2)
   - Creates final scene cuts

## CrewAI Implementation

### Agent Base Pattern
```python
from crewai import Agent, Tool, Task, Crew

class FilmCrewAgent(Agent):
    """Base class following BMAD agent pattern"""
    
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
Each agent uses tools that wrap backend services:
```python
# Backend service mapping per PRD-001
cinematographer_tools = [
    ComfyUITool(),      # Complex workflows
    Wan2GPTool(),       # Fast previews
    CameraControlTool(), # Shot composition
]

sound_designer_tools = [
    RVCTool(),          # Voice cloning
    AudioLDMTool(),     # Sound effects
]
```

## Workflow Orchestration

### Production Pipeline
Following the regenerative content model from [PRD-007](/.bmad-core/prds/PRD-007-regenerative-content-model.md):

1. **Project Definition** → Stored in .blend file
2. **Asset Creation** → References only, not embedded
3. **Content Generation** → On-demand from parameters
4. **Final Assembly** → Non-destructive editing

### Task Flow
```python
def create_production_crew():
    """Implements the full BMAD agent crew"""
    return Crew(
        agents=[
            producer,
            screenwriter,
            casting_director,
            art_director,
            cinematographer,
            sound_designer,
            editor
        ],
        tasks=production_tasks,
        process=Process.sequential,
        memory=True,
        planning=True
    )
```

## Integration Points

### Backend Services
Per [PRD-001](/.bmad-core/prds/PRD-001-backend-integration-service-layer.md):
- ComfyUI for complex image/video workflows
- Wan2GP for fast video generation
- RVC for voice cloning
- AudioLDM for audio generation
- LiteLLM (library) for text generation

### Blender Data Model
Following the asset structure defined in the project plan:
- Characters → `bpy.types.Object` (Empty)
- Styles → `bpy.types.Object` (Empty)
- Scenes → `bpy.types.Collection`
- Shots → `bpy.types.Object` (Empty)

### UI Integration
- Agents triggered through operators
- Progress displayed in panels
- Results stored as custom properties

## Development Guidelines

### Creating New Agents
1. Extend `FilmCrewAgent` base class
2. Define role matching film crew position
3. Implement tools for specific tasks
4. Handle Blender data appropriately

### Error Handling
- Graceful degradation on backend failure
- User-friendly error messages
- Fallback to simpler models when needed

## Testing
```bash
# Test individual agents
pytest tests/test_agents.py -v

# Test agent integration
pytest tests/test_crew_workflow.py -v
```

## Reference
- [Main Project Plan](/.bmad-core/CLAUDE.md)
- [PRD-001: Backend Integration](/.bmad-core/prds/PRD-001-backend-integration-service-layer.md)
- [CrewAI Documentation](https://docs.crewai.com/)