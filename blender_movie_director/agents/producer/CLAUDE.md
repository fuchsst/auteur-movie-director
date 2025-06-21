# Producer Agent - Master Orchestrator

## Role
Master agent responsible for overall project management, workflow orchestration between agents, and resource management. Acts as the central coordinator of the film production pipeline.

## Responsibilities
- **UI Interpretation** - Listen for user actions from Blender panels
- **State Management** - Manage project state in .blend file custom properties  
- **Workflow Orchestration** - Direct task flow between specialized agents
- **Task Routing** - Select optimal backend for each generation task
- **Resource Management** - Monitor system capabilities and optimize performance

## Implementation Pattern
```python
class ProducerAgent(Agent):
    role = "Film Production Coordinator"
    goal = "Orchestrate seamless film production workflow"
    backstory = "Experienced producer managing complex film projects"
    
    def coordinate_production(self, user_request):
        # Parse request and create task sequence
        # Assign tasks to appropriate agents
        # Monitor progress and handle errors
```

## Key Functions
- **Project Initialization** - Set up .blend file structure
- **Agent Coordination** - Manage CrewAI crew execution
- **Progress Tracking** - Update UI with generation status
- **Error Recovery** - Handle agent failures gracefully

## Reference
- [CrewAI Framework](/.bmad-core/data/blender-addon-development-kb.md)