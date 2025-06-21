# bpy.path Guide for Movie Director Addon

## Overview

`bpy.path` provides utilities for handling file paths in Blender, ensuring cross-platform compatibility and proper path resolution. For the Movie Director addon, path utilities are essential for managing generated content, workflow templates, and asset references across different operating systems.

## Core Path Utilities

### Path Resolution and Conversion
```python
import bpy
import os

# Convert relative paths to absolute
def resolve_absolute_path(relative_path):
    """Convert Blender relative path to absolute path"""
    return bpy.path.abspath(relative_path)

# Convert absolute paths to relative (relative to .blend file)
def make_relative_path(absolute_path):
    """Convert absolute path to Blender relative path"""
    return bpy.path.relpath(absolute_path)

# Clean and normalize paths
def clean_path(file_path):
    """Clean and normalize file path"""
    return bpy.path.clean_name(file_path)

# Example usage for Movie Director
def process_reference_image_path(image_path):
    """Process reference image path for storage"""
    # Convert to absolute for processing
    abs_path = resolve_absolute_path(image_path)
    
    # Verify file exists
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Reference image not found: {abs_path}")
    
    # Store as relative path for portability
    rel_path = make_relative_path(abs_path)
    return rel_path
```

### File Path Management for Assets
```python
def setup_asset_paths(project_name):
    """Set up standardized paths for Movie Director assets"""
    # Get .blend file directory as project root
    blend_file_path = bpy.data.filepath
    if not blend_file_path:
        raise RuntimeError("Please save the .blend file before setting up asset paths")
    
    project_dir = os.path.dirname(blend_file_path)
    
    # Create standardized directory structure
    asset_dirs = {
        'characters': os.path.join(project_dir, 'assets', 'characters'),
        'styles': os.path.join(project_dir, 'assets', 'styles'),
        'locations': os.path.join(project_dir, 'assets', 'locations'),
        'generated': os.path.join(project_dir, 'generated'),
        'videos': os.path.join(project_dir, 'generated', 'videos'),
        'audio': os.path.join(project_dir, 'generated', 'audio'),
        'workflows': os.path.join(project_dir, 'workflows'),
        'references': os.path.join(project_dir, 'references')
    }
    
    # Create directories if they don't exist
    for dir_name, dir_path in asset_dirs.items():
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    
    # Store relative paths for portability
    relative_dirs = {}
    for dir_name, dir_path in asset_dirs.items():
        relative_dirs[dir_name] = make_relative_path(dir_path)
    
    return relative_dirs

def get_character_asset_path(character_name, asset_type='lora'):
    """Get standardized path for character assets"""
    project_dirs = setup_asset_paths("current_project")
    characters_dir = resolve_absolute_path(project_dirs['characters'])
    
    # Create character-specific directory
    char_dir = os.path.join(characters_dir, clean_path(character_name))
    if not os.path.exists(char_dir):
        os.makedirs(char_dir, exist_ok=True)
    
    # Generate asset filename
    asset_extensions = {
        'lora': '.safetensors',
        'voice': '.pth',
        'reference': '_references',
        'config': '.json'
    }
    
    if asset_type == 'reference':
        asset_path = char_dir  # Directory for reference images
    else:
        filename = f"{clean_path(character_name)}{asset_extensions[asset_type]}"
        asset_path = os.path.join(char_dir, filename)
    
    # Return relative path for storage
    return make_relative_path(asset_path)
```

### Generated Content Path Management
```python
def get_shot_output_paths(scene_name, shot_number):
    """Get standardized output paths for shot content"""
    project_dirs = setup_asset_paths("current_project")
    
    # Create scene-specific directory
    scene_dir_name = f"scene_{clean_path(scene_name)}"
    video_scene_dir = os.path.join(
        resolve_absolute_path(project_dirs['videos']), 
        scene_dir_name
    )
    audio_scene_dir = os.path.join(
        resolve_absolute_path(project_dirs['audio']), 
        scene_dir_name
    )
    
    # Create directories
    for directory in [video_scene_dir, audio_scene_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    # Generate shot-specific filenames
    shot_prefix = f"shot_{shot_number:03d}"
    
    paths = {
        'video': os.path.join(video_scene_dir, f"{shot_prefix}.mp4"),
        'audio_dialogue': os.path.join(audio_scene_dir, f"{shot_prefix}_dialogue.wav"),
        'audio_sfx': os.path.join(audio_scene_dir, f"{shot_prefix}_sfx.wav"),
        'audio_ambient': os.path.join(audio_scene_dir, f"{shot_prefix}_ambient.wav"),
        'metadata': os.path.join(video_scene_dir, f"{shot_prefix}_metadata.json")
    }
    
    # Return relative paths for storage
    relative_paths = {}
    for key, path in paths.items():
        relative_paths[key] = make_relative_path(path)
    
    return relative_paths

def get_workflow_template_path(workflow_type, template_name):
    """Get path to workflow template files"""
    project_dirs = setup_asset_paths("current_project")
    workflows_dir = resolve_absolute_path(project_dirs['workflows'])
    
    # Create workflow type directory
    workflow_dir = os.path.join(workflows_dir, workflow_type)
    if not os.path.exists(workflow_dir):
        os.makedirs(workflow_dir, exist_ok=True)
    
    # Generate template filename
    template_filename = f"{clean_path(template_name)}.json"
    template_path = os.path.join(workflow_dir, template_filename)
    
    return make_relative_path(template_path)
```

## Cross-Platform Path Handling

### Safe Path Operations
```python
def safe_join_paths(*path_components):
    """Safely join path components across platforms"""
    # Filter out None and empty components
    clean_components = [str(comp) for comp in path_components if comp]
    
    # Use os.path.join for cross-platform compatibility
    joined_path = os.path.join(*clean_components)
    
    # Normalize path separators
    normalized_path = os.path.normpath(joined_path)
    
    return normalized_path

def ensure_path_exists(file_path):
    """Ensure the directory for a file path exists"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def validate_file_path(file_path, must_exist=True):
    """Validate file path and provide helpful error messages"""
    if not file_path:
        raise ValueError("File path cannot be empty")
    
    # Convert to absolute path for validation
    abs_path = resolve_absolute_path(file_path)
    
    if must_exist and not os.path.exists(abs_path):
        raise FileNotFoundError(f"File not found: {abs_path}")
    
    # Check if parent directory exists (for new files)
    if not must_exist:
        parent_dir = os.path.dirname(abs_path)
        if not os.path.exists(parent_dir):
            raise FileNotFoundError(f"Parent directory not found: {parent_dir}")
    
    return abs_path
```

### Path Utilities for Different Asset Types
```python
class AssetPathManager:
    """Centralized path management for Movie Director assets"""
    
    def __init__(self):
        self.project_dirs = None
        self._initialize_paths()
    
    def _initialize_paths(self):
        """Initialize project directory structure"""
        try:
            self.project_dirs = setup_asset_paths("movie_director_project")
        except RuntimeError:
            # No .blend file saved yet
            self.project_dirs = None
    
    def get_character_lora_path(self, character_name):
        """Get path for character LoRA file"""
        if not self.project_dirs:
            self._initialize_paths()
        
        return get_character_asset_path(character_name, 'lora')
    
    def get_character_voice_path(self, character_name):
        """Get path for character voice model"""
        if not self.project_dirs:
            self._initialize_paths()
        
        return get_character_asset_path(character_name, 'voice')
    
    def get_character_references_path(self, character_name):
        """Get directory path for character reference images"""
        if not self.project_dirs:
            self._initialize_paths()
        
        return get_character_asset_path(character_name, 'reference')
    
    def get_style_asset_path(self, style_name):
        """Get path for style LoRA file"""
        if not self.project_dirs:
            self._initialize_paths()
        
        project_dirs = self.project_dirs
        styles_dir = resolve_absolute_path(project_dirs['styles'])
        
        style_filename = f"{clean_path(style_name)}.safetensors"
        style_path = os.path.join(styles_dir, style_filename)
        
        return make_relative_path(style_path)
    
    def get_shot_video_path(self, scene_name, shot_number):
        """Get path for shot video file"""
        paths = get_shot_output_paths(scene_name, shot_number)
        return paths['video']
    
    def get_shot_audio_path(self, scene_name, shot_number, audio_type='dialogue'):
        """Get path for shot audio file"""
        paths = get_shot_output_paths(scene_name, shot_number)
        audio_key = f'audio_{audio_type}'
        return paths.get(audio_key, paths['audio_dialogue'])
```

## Path Resolution for External Resources

### Workflow Template Paths
```python
def resolve_workflow_template_path(template_name, backend='comfyui'):
    """Resolve path to workflow template"""
    # Try project-specific templates first
    try:
        project_template = get_workflow_template_path(backend, template_name)
        abs_project_path = resolve_absolute_path(project_template)
        if os.path.exists(abs_project_path):
            return project_template
    except:
        pass
    
    # Fall back to addon default templates
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    default_templates_dir = os.path.join(addon_dir, 'templates', backend)
    default_template_path = os.path.join(default_templates_dir, f"{template_name}.json")
    
    if os.path.exists(default_template_path):
        return default_template_path
    
    raise FileNotFoundError(f"Workflow template not found: {template_name}")

def resolve_model_path(model_name, model_type='lora'):
    """Resolve path to AI model files"""
    # Check project-specific models first
    if model_type == 'character_lora':
        # Extract character name from model name
        character_name = model_name.replace('_lora', '')
        return get_character_asset_path(character_name, 'lora')
    
    # Check user data directory
    from bpy.utils import extension_path_user
    user_models_dir = os.path.join(
        extension_path_user(__package__, create=True),
        'models',
        model_type
    )
    
    model_path = os.path.join(user_models_dir, model_name)
    if os.path.exists(model_path):
        return model_path
    
    raise FileNotFoundError(f"Model not found: {model_name}")
```

## Best Practices

### 1. Always Use Relative Paths for Storage
```python
# GOOD: Store relative paths in custom properties
character_obj.movie_director.character_lora_path = make_relative_path(lora_path)

# AVOID: Store absolute paths (breaks portability)
character_obj.movie_director.character_lora_path = "/home/user/models/character.safetensors"
```

### 2. Validate Paths Before Use
```python
# GOOD: Validate paths before operations
def load_character_lora(character_obj):
    lora_path = character_obj.movie_director.character_lora_path
    abs_path = validate_file_path(lora_path, must_exist=True)
    return load_lora_file(abs_path)

# AVOID: Assume paths are valid
def bad_load_character_lora(character_obj):
    lora_path = character_obj.movie_director.character_lora_path
    return load_lora_file(lora_path)  # May fail if path is invalid
```

### 3. Use Cross-Platform Path Operations
```python
# GOOD: Cross-platform path joining
asset_path = safe_join_paths(base_dir, 'characters', character_name, 'model.safetensors')

# AVOID: Platform-specific separators
asset_path = base_dir + '/characters/' + character_name + '/model.safetensors'  # Breaks on Windows
```

### 4. Provide Clear Error Messages for Path Issues
```python
# GOOD: Helpful error messages
def load_asset_with_clear_errors(asset_path):
    try:
        abs_path = validate_file_path(asset_path, must_exist=True)
        return load_asset(abs_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Asset file not found: {asset_path}\n"
            f"Make sure the file exists and the path is correct.\n"
            f"Expected location: {resolve_absolute_path(asset_path)}"
        )

# AVOID: Cryptic error messages
def bad_load_asset(asset_path):
    return load_asset(asset_path)  # Unclear error if file missing
```

This path guide ensures robust, cross-platform file path management for all Movie Director addon assets and generated content, maintaining project portability while providing clear error handling.