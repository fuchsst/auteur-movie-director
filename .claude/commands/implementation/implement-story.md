# Implement User Story

Implements a specific user story using the Developer persona and established BMAD development patterns for the Blender Movie Director addon.

$ARGUMENTS: story_id, implementation_approach (agent/ui/backend/integration), test_first (true/false)

## Task
Execute complete story implementation following BMAD development practices, ensuring proper integration with the film crew agent architecture and Blender addon patterns.

## Developer Persona Application  
Use the Developer persona from `.bmad-core/personas/developer.md`:
- **Technical Implementation** - Code development following established patterns
- **Testing Integration** - Test-driven development and validation
- **Code Quality** - Adherence to project standards and best practices
- **Documentation** - Inline and API documentation creation
- **Integration Focus** - Proper component integration and system cohesion

## Implementation Workflow
```bash
# 1. Story Analysis and Planning
- Review story acceptance criteria
- Analyze technical requirements and dependencies
- Select appropriate implementation templates
- Plan testing approach

# 2. Development Environment Setup
- Ensure Blender addon development environment is ready
- Activate appropriate backend services if needed
- Prepare test data and fixtures

# 3. Implementation Execution
# Based on story type, follow appropriate pattern:
```

## Implementation Patterns by Component

### Agent Implementation
For film crew agent stories:
```python
# Use agent template from blender_movie_director/agents/{agent_name}/
class {AgentName}Agent(CrewAgent):
    def __init__(self):
        super().__init__(
            role="{agent_role}",
            goal="{agent_goal}",
            backstory="{agent_backstory}",
            tools=[{agent_tools}]
        )
    
    def execute_task(self, task_data):
        # Agent-specific implementation
        pass
```

### UI Component Implementation  
For Blender UI stories:
```python
# Panel implementation
class {COMPONENT_NAME}_PT_panel(bpy.types.Panel):
    bl_label = "{Panel Title}"
    bl_idname = "MOVIEDIR_{COMPONENT_NAME}_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Movie Director'
    
    def draw(self, context):
        # UI implementation following Blender patterns
        pass

# Operator implementation
class {COMPONENT_NAME}_OT_operator(bpy.types.Operator):
    bl_idname = "movie_director.{operation_name}"
    bl_label = "{Operation Label}"
    
    def execute(self, context):
        # Operation implementation
        return {'FINISHED'}
```

### Backend Integration Implementation
For backend service stories:
```python
# API client implementation
class {ServiceName}Client:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.session = requests.Session()
    
    def execute_workflow(self, workflow_data):
        # Backend service integration
        pass
```

## Testing Implementation
Each story implementation includes:
- **Unit Tests** - Component-specific functionality testing
- **Integration Tests** - Agent interaction and backend service testing
- **UI Tests** - Blender addon user interface validation
- **End-to-End Tests** - Complete workflow testing

## Code Quality Standards
Implementation must follow:
- **PEP 8** - Python code style guidelines
- **Type Hints** - Proper type annotation for better code clarity
- **Documentation** - Docstrings and inline comments
- **Error Handling** - Robust error handling and user feedback
- **Logging** - Appropriate logging for debugging and monitoring

## Integration Validation
Ensure proper integration with:
- **Film Crew Agents** - Agent orchestration and communication
- **Asset Data Model** - Custom property and data structure usage
- **Workflow Templates** - ComfyUI/Wan2GP template integration
- **Blender Systems** - Native Blender API and UI integration

## Output Artifacts
- Complete implementation following story acceptance criteria
- Comprehensive test suite with high coverage
- Updated documentation and code comments  
- Integration validation with existing system components
- Story marked as complete with validation evidence