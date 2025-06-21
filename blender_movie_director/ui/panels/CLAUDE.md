# UI Panels

## Role
Custom Blender panels providing native UI integration for the Movie Director addon. Located in 3D Viewport sidebar and Properties Editor.

## Panel Structure
- **Main Panel** - Project overview and generation status
- **Agent Panels** - Controls for each film crew agent
- **Asset Panels** - Character and style management
- **Shot Panels** - Shot properties and generation controls

## Implementation Pattern
```python
class MOVIE_DIRECTOR_PT_main_panel(Panel):
    bl_label = "Movie Director"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Movie Director"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene.movie_director
        
        # Project info
        layout.prop(scene, "project_name")
        layout.prop(scene, "generation_status")
```

## Panel Categories
- **Project Management** - Overall project controls
- **Film Crew** - Agent status and controls  
- **Assets** - Character/style browser and creation
- **Production** - Shot generation and assembly

## Design Guidelines
- Follow **Blender UI conventions**
- Use **consistent spacing** and layout
- Display **real-time status** updates
- Provide **contextual controls**

## Reference
- [bpy.types.Panel](/.bmad-core/data/bpy-context-guide.md)