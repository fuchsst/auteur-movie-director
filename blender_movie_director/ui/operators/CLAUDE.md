# UI Operators

## Role
Blender operators that trigger agent workflows and handle user interactions. Provide the bridge between UI elements and the agent system.

## Operator Categories
- **Agent Triggers** - Start specific agent workflows
- **Asset Creation** - Create character/style/location assets
- **Generation Controls** - Start/stop/monitor generation
- **Project Management** - Initialize and manage projects

## Implementation Pattern
```python
class MOVIE_DIRECTOR_OT_generate_shot(Operator):
    bl_idname = "movie_director.generate_shot"
    bl_label = "Generate Shot"
    bl_description = "Generate video for selected shot"
    
    def execute(self, context):
        shot_obj = context.active_object
        
        # Validate shot object
        if not self.validate_shot(shot_obj):
            return {'CANCELLED'}
        
        # Trigger Cinematographer agent
        cinematographer.generate_shot(shot_obj)
        return {'FINISHED'}
```

## Operator Types
- **Generation Operators** - Trigger AI generation workflows
- **Asset Operators** - Create and manage generative assets
- **Import/Export** - Handle external data
- **Utility Operators** - Helper functions and tools

## Best Practices
- **Validate inputs** before execution
- **Provide user feedback** via reports
- **Handle errors gracefully**
- **Use async patterns** for long operations

## Reference
- [bpy.types.Operator](/.bmad-core/data/bpy-context-guide.md)