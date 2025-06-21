# bpy.context Guide for Movie Director Addon

## Overview

`bpy.context` provides dynamic access to Blender's current state, including active objects, modes, scenes, and UI areas. For the Movie Director addon, context is essential for determining when UI elements should be shown and ensuring operations are performed on the correct objects.

## Core Context Attributes

### Scene and Object Access
```python
# Current scene - where all movie director data is stored
current_scene = bpy.context.scene
movie_props = current_scene.movie_director

# Active object - could be character, style, or shot asset
active_obj = bpy.context.active_object

# Selected objects - for batch operations
selected_objs = bpy.context.selected_objects

# Active collection - for organizing shots and scenes
active_collection = bpy.context.collection
```

### Mode and UI Information
```python
# Current mode - important for UI panel visibility
current_mode = bpy.context.mode  # 'OBJECT', 'EDIT_MESH', etc.

# UI area and region - for context-sensitive panels
area = bpy.context.area          # '3D_VIEWPORT', 'PROPERTIES', etc.
region = bpy.context.region      # 'UI', 'HEADER', etc.

# View layer - for visibility management
view_layer = bpy.context.view_layer
```

## Movie Director Context Patterns

### Safe Context Access
```python
def safe_get_movie_props(context):
    """Safely get movie director properties from context"""
    scene = getattr(context, 'scene', None)
    if scene and hasattr(scene, 'movie_director'):
        return scene.movie_director
    return None

def safe_get_active_character(context):
    """Get active character asset if available"""
    obj = context.active_object
    if obj and hasattr(obj, 'movie_director'):
        if obj.movie_director.asset_type == 'character':
            return obj
    return None
```

### Context Validation for Operators
```python
class MOVIE_DIRECTOR_OT_generate_shot(bpy.types.Operator):
    bl_idname = "movie_director.generate_shot"
    bl_label = "Generate Shot"
    
    @classmethod
    def poll(cls, context):
        """Only enable when valid shot object is selected"""
        obj = context.active_object
        return (obj and 
                hasattr(obj, 'movie_director') and 
                obj.movie_director.asset_type == 'shot')
    
    def execute(self, context):
        shot_obj = context.active_object
        # Safe to proceed - poll() ensures valid context
        return self.generate_shot_video(context, shot_obj)
```

### Panel Context Sensitivity
```python
class MOVIE_DIRECTOR_PT_character_panel(bpy.types.Panel):
    bl_label = "Character Assets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Movie Director'
    
    @classmethod
    def poll(cls, context):
        """Show panel only in Object mode with movie director scene"""
        return (context.mode == 'OBJECT' and 
                hasattr(context.scene, 'movie_director'))
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Context-aware UI based on selected object
        active_obj = context.active_object
        if active_obj and hasattr(active_obj, 'movie_director'):
            asset_type = active_obj.movie_director.asset_type
            if asset_type == 'character':
                self.draw_character_properties(layout, active_obj)
            else:
                layout.label(text=f"Selected: {asset_type.title()} Asset")
        else:
            self.draw_character_creation(layout, scene)
```

## Context-Aware Operations

### Dynamic UI Updates
```python
def update_ui_based_on_context(context):
    """Update UI elements based on current context"""
    scene = context.scene
    movie_props = scene.movie_director
    
    # Update progress indicators
    if movie_props.generation_active:
        movie_props.ui_status = "Generating..."
    else:
        movie_props.ui_status = "Ready"
    
    # Force UI redraw
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
```

### Context-Sensitive Asset Creation
```python
def create_asset_in_context(context, asset_type, name):
    """Create asset in appropriate context location"""
    # Use current collection as parent
    collection = context.collection
    
    # Create asset object
    asset_obj = bpy.data.objects.new(name, None)
    asset_obj.movie_director.asset_type = asset_type
    
    # Link to current context
    collection.objects.link(asset_obj)
    
    # Make active for immediate editing
    context.view_layer.objects.active = asset_obj
    asset_obj.select_set(True)
    
    return asset_obj
```

## Best Practices

### 1. Always Validate Context
```python
# WRONG: Assume context is valid
def bad_context_usage():
    obj = bpy.context.active_object
    obj.location = (0, 0, 0)  # Crashes if no active object

# CORRECT: Validate first
def safe_context_usage():
    obj = bpy.context.active_object
    if obj:
        obj.location = (0, 0, 0)
```

### 2. Use Context in Appropriate Methods
```python
# UI drawing methods receive context parameter
def draw(self, context):
    scene = context.scene  # Use parameter, not bpy.context
    
# Operators receive context in execute/invoke
def execute(self, context):
    return self.do_work(context)  # Pass context through
```

### 3. Context-Aware Error Handling
```python
def generate_with_context_validation(context):
    """Validate all required context before generation"""
    errors = []
    
    # Check scene setup
    if not hasattr(context.scene, 'movie_director'):
        errors.append("Movie Director not initialized")
    
    # Check active object
    if not context.active_object:
        errors.append("No active object selected")
    
    # Check mode
    if context.mode != 'OBJECT':
        errors.append("Must be in Object mode")
    
    if errors:
        return {'CANCELLED'}, errors
    
    return {'FINISHED'}, []
```

### 4. Efficient Context Usage
```python
# INEFFICIENT: Multiple context lookups
def inefficient_context_usage():
    if bpy.context.active_object:
        name = bpy.context.active_object.name
        location = bpy.context.active_object.location
        rotation = bpy.context.active_object.rotation_euler

# EFFICIENT: Store context reference
def efficient_context_usage():
    obj = bpy.context.active_object
    if obj:
        name = obj.name
        location = obj.location
        rotation = obj.rotation_euler
```

## Context Integration for Film Production

### Scene Context Management
```python
def setup_film_context(context, project_name):
    """Initialize scene for film production context"""
    scene = context.scene
    scene.name = f"{project_name}_Master"
    
    # Initialize movie director properties
    if not hasattr(scene, 'movie_director'):
        # Properties would be registered with scene
        pass
    
    # Set up collections for organization
    characters_col = bpy.data.collections.new("Characters")
    styles_col = bpy.data.collections.new("Styles")
    scenes_col = bpy.data.collections.new("Scenes")
    
    context.scene.collection.children.link(characters_col)
    context.scene.collection.children.link(styles_col)
    context.scene.collection.children.link(scenes_col)
```

### Production Context Switching
```python
def switch_to_character_context(context, character_name):
    """Switch context for character asset work"""
    # Find character object
    char_obj = None
    for obj in context.scene.objects:
        if (hasattr(obj, 'movie_director') and 
            obj.movie_director.asset_type == 'character' and
            obj.movie_director.character_name == character_name):
            char_obj = obj
            break
    
    if char_obj:
        # Clear selection
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select and activate character
        char_obj.select_set(True)
        context.view_layer.objects.active = char_obj
        
        return True
    return False
```

This context guide ensures that all Movie Director addon operations are context-aware and provide a smooth user experience within Blender's interface paradigms.