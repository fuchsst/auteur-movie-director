# bpy.props Guide for Movie Director Addon

## Overview

`bpy.props` defines custom properties for storing addon data directly in Blender's data structures. For the Movie Director addon, properties store all generative asset metadata, production settings, and workflow state within the .blend file.

## Core Property Types

### Basic Property Types
```python
import bpy
from bpy.props import (
    BoolProperty, IntProperty, FloatProperty, StringProperty,
    EnumProperty, PointerProperty, CollectionProperty
)

# Boolean properties for toggles and states
generation_active: BoolProperty(
    name="Generation Active",
    description="Whether AI generation is currently running",
    default=False
)

# Integer properties for counts and indices
shot_number: IntProperty(
    name="Shot Number",
    description="Sequential shot number in scene",
    default=1,
    min=1,
    max=9999
)

# Float properties for values and percentages
generation_progress: FloatProperty(
    name="Generation Progress",
    description="Current generation progress",
    default=0.0,
    min=0.0,
    max=1.0,
    subtype='PERCENTAGE'
)

# String properties for text and file paths
character_name: StringProperty(
    name="Character Name",
    description="Name of the character asset",
    default="",
    maxlen=64
)

# File path properties
character_lora_path: StringProperty(
    name="Character LoRA Path",
    description="Path to trained character LoRA file",
    default="",
    subtype='FILE_PATH'
)
```

### Enum Properties for Selections
```python
# Asset type enumeration
asset_type: EnumProperty(
    name="Asset Type",
    description="Type of generative asset",
    items=[
        ('character', "Character", "Character asset with LoRA and voice model"),
        ('style', "Style", "Visual style asset with style LoRA"),
        ('location', "Location", "Environment/location asset"),
        ('shot', "Shot", "Individual shot with video and audio"),
    ],
    default='character'
)

# Generation quality presets
quality_preset: EnumProperty(
    name="Quality Preset",
    description="Generation quality and speed preset",
    items=[
        ('draft', "Draft", "Fast generation for previews"),
        ('standard', "Standard", "Balanced quality and speed"),
        ('high', "High Quality", "Best quality, slower generation"),
        ('ultra', "Ultra", "Maximum quality for final shots"),
    ],
    default='standard'
)

# Backend selection
backend_preference: EnumProperty(
    name="Backend",
    description="Preferred generation backend",
    items=[
        ('auto', "Auto", "Automatically select based on task"),
        ('comfyui', "ComfyUI", "Use ComfyUI for generation"),
        ('wan2gp', "Wan2GP", "Use Wan2GP for generation"),
    ],
    default='auto'
)
```

## Movie Director Property Groups

### Main Movie Director Properties
```python
class MovieDirectorProperties(bpy.types.PropertyGroup):
    """Main property group for movie director addon"""
    
    # Project metadata
    project_name: StringProperty(
        name="Project Name",
        description="Name of the film project",
        default="Untitled Film"
    )
    
    project_description: StringProperty(
        name="Description",
        description="Brief description of the project",
        default=""
    )
    
    # Generation settings
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
    
    generation_status: StringProperty(
        name="Status",
        description="Current generation status message",
        default="Ready"
    )
    
    # Backend configuration
    comfyui_url: StringProperty(
        name="ComfyUI URL",
        description="URL for ComfyUI backend",
        default="http://localhost:8188"
    )
    
    wan2gp_url: StringProperty(
        name="Wan2GP URL", 
        description="URL for Wan2GP backend",
        default="http://localhost:7860"
    )
    
    litellm_url: StringProperty(
        name="LiteLLM URL",
        description="URL for LiteLLM backend",
        default="http://localhost:4000"
    )
    
    # VRAM management
    available_vram: FloatProperty(
        name="Available VRAM",
        description="Available GPU VRAM in GB",
        default=24.0,
        min=1.0,
        max=80.0
    )
    
    vram_budget_mode: EnumProperty(
        name="VRAM Budget Mode",
        description="VRAM management strategy",
        items=[
            ('conservative', "Conservative", "Use minimal VRAM with sequential loading"),
            ('balanced', "Balanced", "Balance VRAM usage and performance"),
            ('aggressive', "Aggressive", "Use maximum VRAM for speed"),
        ],
        default='balanced'
    )
```

### Character Asset Properties
```python
class CharacterAssetProperties(bpy.types.PropertyGroup):
    """Properties for character assets"""
    
    character_name: StringProperty(
        name="Character Name",
        description="Name of the character",
        default=""
    )
    
    character_description: StringProperty(
        name="Description",
        description="Character description and traits",
        default=""
    )
    
    # Reference materials
    reference_images_path: StringProperty(
        name="Reference Images",
        description="Directory containing reference images",
        default="",
        subtype='DIR_PATH'
    )
    
    # Trained models
    character_lora_path: StringProperty(
        name="Character LoRA",
        description="Path to trained character LoRA file",
        default="",
        subtype='FILE_PATH'
    )
    
    rvc_voice_model_path: StringProperty(
        name="RVC Voice Model",
        description="Path to trained RVC voice model",
        default="",
        subtype='FILE_PATH'
    )
    
    # Training status
    lora_training_status: EnumProperty(
        name="LoRA Training Status",
        description="Status of character LoRA training",
        items=[
            ('not_started', "Not Started", "Training not yet begun"),
            ('in_progress', "In Progress", "Currently training"),
            ('completed', "Completed", "Training finished successfully"),
            ('failed', "Failed", "Training failed"),
        ],
        default='not_started'
    )
    
    voice_training_status: EnumProperty(
        name="Voice Training Status", 
        description="Status of RVC voice training",
        items=[
            ('not_started', "Not Started", "Training not yet begun"),
            ('in_progress', "In Progress", "Currently training"),
            ('completed', "Completed", "Training finished successfully"),
            ('failed', "Failed", "Training failed"),
        ],
        default='not_started'
    )
```

### Shot Properties
```python
class ShotProperties(bpy.types.PropertyGroup):
    """Properties for shot objects"""
    
    shot_number: IntProperty(
        name="Shot Number",
        description="Sequential shot number",
        default=1,
        min=1
    )
    
    scene_name: StringProperty(
        name="Scene Name",
        description="Name of the scene this shot belongs to",
        default=""
    )
    
    # Script content
    dialogue: StringProperty(
        name="Dialogue",
        description="Character dialogue for this shot",
        default=""
    )
    
    action_description: StringProperty(
        name="Action",
        description="Description of action in this shot",
        default=""
    )
    
    camera_direction: StringProperty(
        name="Camera Direction",
        description="Camera movement and framing notes",
        default=""
    )
    
    # Generated content paths
    generated_video_path: StringProperty(
        name="Generated Video",
        description="Path to generated video file",
        default="",
        subtype='FILE_PATH'
    )
    
    generated_audio_path: StringProperty(
        name="Generated Audio",
        description="Path to generated audio file", 
        default="",
        subtype='FILE_PATH'
    )
    
    # Asset references
    characters_in_shot: CollectionProperty(
        type=bpy.types.PropertyGroup,  # Would be CharacterReference
        name="Characters in Shot"
    )
    
    style_reference: PointerProperty(
        type=bpy.types.Object,
        name="Style Reference",
        description="Style asset to apply to this shot"
    )
    
    # Generation settings
    generation_quality: EnumProperty(
        name="Quality",
        description="Generation quality for this shot",
        items=[
            ('draft', "Draft", "Fast preview generation"),
            ('final', "Final", "High quality final generation"),
        ],
        default='draft'
    )
```

## Property Update Callbacks

### Reactive Property Updates
```python
def update_generation_progress(self, context):
    """Update UI when generation progress changes"""
    # Force UI redraw
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
    
    # Update status message
    progress = self.generation_progress
    if progress >= 1.0:
        self.generation_status = "Generation Complete"
        self.generation_active = False
    elif progress > 0.0:
        self.generation_status = f"Generating... {int(progress * 100)}%"

def update_backend_url(self, context):
    """Validate backend URL when changed"""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(self.comfyui_url):
        self.comfyui_url = "http://localhost:8188"

# Apply update callbacks to properties
generation_progress: FloatProperty(
    name="Generation Progress",
    description="Current generation progress",
    default=0.0,
    min=0.0,
    max=1.0,
    subtype='PERCENTAGE',
    update=update_generation_progress
)

comfyui_url: StringProperty(
    name="ComfyUI URL",
    description="URL for ComfyUI backend",
    default="http://localhost:8188",
    update=update_backend_url
)
```

### Advanced Property Patterns
```python
def get_available_characters(self, context):
    """Dynamic enum items for character selection"""
    items = [('none', "None", "No character selected")]
    
    # Find all character assets
    for obj in context.scene.objects:
        if (hasattr(obj, 'movie_director') and 
            hasattr(obj.movie_director, 'asset_type') and
            obj.movie_director.asset_type == 'character'):
            char_name = obj.movie_director.character_name or obj.name
            items.append((obj.name, char_name, f"Character: {char_name}"))
    
    return items

# Dynamic enum property
character_selection: EnumProperty(
    name="Character",
    description="Select character for this shot",
    items=get_available_characters
)
```

## Property Registration

### Scene-Level Properties
```python
def register():
    """Register property groups with Blender"""
    # Register property group classes
    bpy.utils.register_class(MovieDirectorProperties)
    bpy.utils.register_class(CharacterAssetProperties)
    bpy.utils.register_class(ShotProperties)
    
    # Attach to scene for project-wide access
    bpy.types.Scene.movie_director = PointerProperty(
        type=MovieDirectorProperties,
        name="Movie Director",
        description="Movie Director addon properties"
    )
    
    # Attach to objects for asset-specific properties
    bpy.types.Object.movie_director = PointerProperty(
        type=CharacterAssetProperties,  # Could be union of asset types
        name="Movie Director Asset",
        description="Movie Director asset properties"
    )

def unregister():
    """Unregister properties when addon is disabled"""
    # Remove properties
    del bpy.types.Scene.movie_director
    del bpy.types.Object.movie_director
    
    # Unregister classes
    bpy.utils.unregister_class(ShotProperties)
    bpy.utils.unregister_class(CharacterAssetProperties)
    bpy.utils.unregister_class(MovieDirectorProperties)
```

## Best Practices

### 1. Use Appropriate Property Types
```python
# GOOD: Specific subtypes for file paths
lora_path: StringProperty(subtype='FILE_PATH')
image_dir: StringProperty(subtype='DIR_PATH')

# GOOD: Proper min/max for numeric values  
shot_number: IntProperty(min=1, max=9999)
vram_gb: FloatProperty(min=1.0, max=80.0)

# GOOD: Percentage subtype for progress
progress: FloatProperty(subtype='PERCENTAGE', min=0.0, max=1.0)
```

### 2. Provide Clear Descriptions
```python
# GOOD: Descriptive names and descriptions
character_lora_path: StringProperty(
    name="Character LoRA File",
    description="Path to trained character LoRA model (.safetensors)",
    subtype='FILE_PATH'
)

# AVOID: Vague descriptions
path: StringProperty(name="Path", description="A file path")
```

### 3. Use Update Callbacks Wisely
```python
# GOOD: Lightweight updates
def update_progress(self, context):
    if self.generation_progress >= 1.0:
        self.generation_active = False

# AVOID: Heavy operations in updates
def bad_update(self, context):
    # Don't do expensive operations in update callbacks
    regenerate_all_assets(context)  # Too heavy!
```

### 4. Organize Properties Logically
```python
class WellOrganizedProperties(bpy.types.PropertyGroup):
    """Properties organized in logical groups"""
    
    # Project identification
    project_name: StringProperty(...)
    project_description: StringProperty(...)
    
    # Generation settings
    generation_active: BoolProperty(...)
    generation_progress: FloatProperty(...)
    
    # Backend configuration
    comfyui_url: StringProperty(...)
    wan2gp_url: StringProperty(...)
```

### 5. Handle Property Migration
```python
def migrate_properties():
    """Handle property changes between addon versions"""
    scene = bpy.context.scene
    
    # Check for old property names and migrate
    if hasattr(scene.movie_director, 'old_property_name'):
        scene.movie_director.new_property_name = scene.movie_director.old_property_name
        # Note: Can't actually delete old properties, but can mark as deprecated
```

This properties guide ensures that all Movie Director addon data is properly stored, organized, and accessible within Blender's data structures, making projects portable and preserving all generative film production metadata.