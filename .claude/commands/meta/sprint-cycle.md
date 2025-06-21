# Complete Sprint Execution Cycle

Executes a complete BMAD sprint cycle for the Blender Movie Director addon development.

$ARGUMENTS: sprint_number, sprint_goal, duration (1-4 weeks)

## Task
Execute a complete sprint following BMAD methodology with proper planning, implementation, validation, and retrospective phases. Ensures systematic progress toward the generative film studio vision.

## BMAD Sprint Framework
This command implements the full BMAD sprint methodology:
- **Sprint Planning** - Scrum Master persona with capacity planning
- **Story Implementation** - Developer personas with agent-specific expertise
- **Continuous Validation** - QA Engineer persona with testing throughout
- **Sprint Review** - Product Owner persona with stakeholder feedback
- **Retrospective** - Team reflection and process improvement

## Execution Flow
```bash
# 1. Sprint Planning Phase
claude exec plan-sprint $sprint_number

# 2. Implementation Phase (Daily Execution)
for day in $(seq 1 $sprint_duration_days); do
    # Implement prioritized stories
    claude exec implement-stories --daily-capacity
    
    # Continuous validation
    claude exec validate-implementation --incremental
    
    # Track progress
    claude exec update-project-status --daily
done

# 3. Sprint Review
claude exec review-sprint $sprint_number

# 4. Sprint Retrospective
claude exec retrospective-sprint $sprint_number
```

## Sprint Planning Integration
Uses BMAD planning artifacts:
- **Backlog Refinement** - User stories from `.bmad-core/stories/`
- **Capacity Planning** - Team velocity and agent complexity estimates
- **Definition of Done** - Quality criteria from `.bmad-core/checklists/`
- **Sprint Goal** - Aligned with generative film studio milestones

## Story Implementation Patterns
Each story implementation follows:
- Agent-specific development templates
- Blender addon development patterns (bpy integration)
- CrewAI framework integration
- Backend service integration (ComfyUI/Wan2GP/LiteLLM)
- Test-driven development with validation

## Progress Tracking
Sprint metrics and artifacts:
- Story completion tracking
- Agent implementation progress
- Blender addon functionality validation
- Backend integration health
- Code quality metrics
- Documentation updates

## Sprint Review Focus Areas
- **Addon Functionality** - Blender integration demonstrations
- **Agent Capabilities** - Film crew agent feature showcases  
- **Backend Integration** - Generative workflow demonstrations
- **User Experience** - UI/UX validation and feedback
- **Technical Debt** - Code quality and architecture review