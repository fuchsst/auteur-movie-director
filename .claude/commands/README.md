# BMAD Development Commands for Blender Movie Director

Claude commands for developing the Blender Movie Director addon using BMAD (Breakthrough Method of Agile AI-Driven Development) methodology.

## Meta-Commands (Complete BMAD Workflows)

### **`implement-feature`** - Complete Feature Development Cycle
Execute the full BMAD methodology for implementing a complete feature:
```bash
claude exec implement-feature feature_name=character_creation priority=high target_sprint=3
```

### **`agent-development-cycle`** - Complete Agent Implementation  
Develop a complete BMAD film crew agent with full integration:
```bash
claude exec agent-development-cycle agent_name=cinematographer complexity=advanced
```

### **`sprint-cycle`** - Complete Sprint Execution
Execute a complete sprint following BMAD methodology:
```bash
claude exec sprint-cycle sprint_number=1 sprint_goal="Core Agent Architecture" duration=2weeks
```

## Core BMAD Development Commands

### Planning Phase
```bash
# Define product requirements
claude exec define-prd feature_name=video_generation stakeholder_input="filmmaker_interviews"

# Create epic structure
claude exec define-epic epic_name=cinematographer_agent based_on_prd=video_generation

# Break down into stories
claude exec breakdown-stories epic_name=cinematographer_agent story_size_target=medium
```

### Implementation Phase
```bash
# Implement user stories
claude exec implement-story story_id=CINE-001 implementation_approach=agent test_first=true

# Validate implementation
claude exec validate-implementation story_id=CINE-001 validation_scope=all
```

### Management Phase
```bash
# Track project progress
claude exec update-project-status update_scope=daily include_metrics=true

# Sprint planning and review
claude exec plan-sprint sprint_number=2
claude exec review-sprint sprint_number=1
```

## BMAD Methodology Integration

### Film Crew Agent Architecture
Each development command integrates with our established film crew metaphor:
- **🎬 Producer** - Project orchestration and resource management
- **📝 Screenwriter** - Story development and script structuring  
- **🎭 Casting Director** - Character asset management and consistency
- **🎨 Art Director** - Visual style definition and maintenance
- **🎥 Cinematographer** - Video generation and camera control
- **🔊 Sound Designer** - Audio creation and synchronization
- **✂️ Editor** - Final assembly and post-production

### BMAD Personas
Commands utilize established personas from `.bmad-core/personas/`:
- **Business Analyst** - Requirements gathering and analysis
- **Product Owner** - Feature definition and prioritization
- **Development Lead** - Technical architecture and story breakdown
- **Developer** - Implementation and code development
- **QA Engineer** - Testing and quality validation
- **Project Manager** - Progress tracking and stakeholder communication

### Project Structure Integration
Commands work with our established structure:
```
blender_movie_director/
├── agents/           # Film crew agent implementations
├── backend/          # API clients for ComfyUI/Wan2GP/LiteLLM
├── ui/              # Blender panels, operators, properties
├── workflows/       # Generative workflow templates
└── config/          # Configuration and templates
```

## Development Workflow

### 1. Feature Planning
```bash
# Start with requirements definition
claude exec define-prd feature_name=new_feature

# Create epic and stories
claude exec define-epic epic_name=feature_epic
claude exec breakdown-stories epic_name=feature_epic
```

### 2. Sprint Execution
```bash
# Execute complete sprint cycle
claude exec sprint-cycle sprint_number=N sprint_goal="Sprint Goal"

# Or implement individual stories
claude exec implement-story story_id=STORY-001
claude exec validate-implementation story_id=STORY-001
```

### 3. Progress Tracking
```bash
# Regular status updates
claude exec update-project-status update_scope=daily
claude exec update-project-status update_scope=weekly stakeholder_report=true
```

## Quality Standards
All commands enforce:
- **Blender Addon Standards** - Proper bpy API usage and addon patterns
- **CrewAI Integration** - Correct agent implementation and orchestration
- **Code Quality** - PEP 8 compliance, type hints, and documentation
- **Testing Coverage** - Comprehensive unit, integration, and E2E testing
- **BMAD Architecture** - Adherence to established patterns and principles

## Getting Started
1. Initialize your development environment
2. Start with a feature planning session using `define-prd`
3. Use meta-commands for complete workflows or individual commands for specific tasks
4. Track progress with regular status updates

The commands are designed to guide you through the complete BMAD development lifecycle while maintaining the creative vision of a local-first, agent-driven generative film studio.