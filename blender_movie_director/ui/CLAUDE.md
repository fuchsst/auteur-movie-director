# Blender UI Integration

## Overview

Native Blender UI components that provide seamless integration with the Movie Director addon. All UI elements follow Blender's design patterns and integrate deeply with the film crew agent system.

## UI Architecture

### Components
- **Panels** (`panels/`) - Custom UI panels in 3D Viewport sidebar and Properties Editor
- **Operators** (`operators/`) - Button actions that trigger agent workflows
- **Properties** (`properties/`) - Custom property definitions for generative assets
- **Asset Browser** (`asset_browser/`) - Integration with Blender's Asset Browser

### UI Integration Pattern
```python
class MOVIE_DIRECTOR_PT_agent_panel(Panel):
    bl_label = "Film Crew"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Movie Director"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Agent status and controls
        layout.prop(scene.movie_director, "generation_active")
        layout.operator("movie_director.generate_shot")
```

### Operator Pattern
```python
class MOVIE_DIRECTOR_OT_generate_shot(Operator):
    bl_idname = "movie_director.generate_shot"
    bl_label = "Generate Shot"
    
    def execute(self, context):
        # Trigger Cinematographer agent
        shot_obj = context.active_object
        cinematographer.generate_shot(shot_obj)
        return {'FINISHED'}
```

## Development Guidelines

- Use **bpy.types** for all UI classes
- Store state in **custom properties** 
- Trigger agents through **operators**
- Display progress in **panels**

## Reference
- [bpy.types Guide](/.bmad-core/data/bpy-context-guide.md)
- [Property Patterns](/.bmad-core/data/bpy-props-guide.md)