# UI Properties

## Role
Custom property definitions for storing Movie Director data directly in Blender's data structures. Enables project portability and native integration.

## Property Groups
- **MovieDirectorProperties** - Main scene-level properties
- **CharacterAssetProperties** - Character-specific data
- **ShotProperties** - Individual shot information
- **StyleProperties** - Visual style definitions

## Implementation Pattern
```python
class MovieDirectorProperties(PropertyGroup):
    project_name: StringProperty(
        name="Project Name",
        description="Name of the film project",
        default="Untitled Film"
    )
    
    generation_active: BoolProperty(
        name="Generation Active",
        description="AI generation in progress",
        default=False
    )
    
    generation_progress: FloatProperty(
        name="Progress",
        description="Current generation progress",
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='PERCENTAGE'
    )
```

## Property Categories
- **Project Data** - Film-level information
- **Generation State** - Current operation status
- **Asset References** - Paths to generated content
- **Configuration** - User preferences and settings

## Storage Strategy
- Store in **.blend file** for portability
- Use **relative paths** for asset references
- Implement **update callbacks** for reactive UI
- Follow **Blender property conventions**

## Reference
- [bpy.props Guide](/.bmad-core/data/bpy-props-guide.md)