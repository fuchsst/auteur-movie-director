# Complete Agent Development Cycle

Implements a complete BMAD film crew agent following the established architecture and CrewAI integration patterns.

$ARGUMENTS: agent_name (screenwriter/casting_director/art_director/cinematographer/sound_designer/editor), complexity (basic/advanced)

## Task
Develop a complete BMAD film crew agent with full Blender integration, CrewAI framework implementation, and backend service integration. Follows the established agent architecture from CLAUDE.md.

## BMAD Agent Architecture
This command implements agents following our film crew metaphor:
- **Agent Logic** - CrewAI agent with role, goal, and backstory
- **Tools Integration** - Backend API clients and workflow templates
- **UI Components** - Blender panels and operators
- **Workflow Templates** - ComfyUI/Wan2GP configurations
- **Asset Integration** - Generative asset data model

## Execution Flow
```bash
# 1. Define Agent Requirements
claude exec define-agent-requirements $agent_name

# 2. Implement Core Agent Logic
claude exec implement-agent-core $agent_name

# 3. Build Agent UI Components
claude exec implement-agent-ui $agent_name

# 4. Create Workflow Templates
claude exec implement-agent-workflows $agent_name

# 5. Validate Agent Integration
claude exec validate-agent $agent_name

# 6. Update Project Status
claude exec update-project-status
```

## Agent Implementation Structure
Based on `blender_movie_director/agents/{agent_name}/`:
- `__init__.py` - Agent class with CrewAI integration
- `tools.py` - Backend integration tools
- `workflows.py` - Template management
- `ui.py` - Blender UI components (panels/operators)
- `tests.py` - Agent-specific testing

## Film Crew Agent Specifications
Each agent follows the CLAUDE.md specifications:
- **Screenwriter** - LLM-based story development and script structuring
- **Casting Director** - Character asset creation and consistency management
- **Art Director** - Style definition and visual consistency
- **Cinematographer** - Video generation and camera control
- **Sound Designer** - Audio creation and synchronization  
- **Editor** - Final assembly and post-production

## Integration Points
- CrewAI framework for agent orchestration
- Backend API clients (ComfyUI, Wan2GP, LiteLLM)
- Blender custom properties for asset data model
- Asset Browser integration for visual asset management
- Workflow template system for generative tasks