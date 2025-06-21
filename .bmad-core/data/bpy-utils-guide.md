# bpy.utils Guide for Movie Director Addon

## Overview

`bpy.utils` provides essential utility functions for addon development, including registration systems, file path management, and extension utilities. For the Movie Director addon, these utilities are crucial for proper addon lifecycle management and cross-platform compatibility.

## Core Utility Functions

### Addon Registration System
```python
import bpy
from bpy.utils import register_class, unregister_class

# Basic class registration
def register():
    """Register all addon classes with Blender"""
    # Register property groups first
    register_class(MovieDirectorProperties)
    register_class(CharacterAssetProperties)
    
    # Register operators
    register_class(MOVIE_DIRECTOR_OT_generate_character)
    register_class(MOVIE_DIRECTOR_OT_generate_shot)
    
    # Register UI panels
    register_class(MOVIE_DIRECTOR_PT_main_panel)
    register_class(MOVIE_DIRECTOR_PT_character_panel)
    
    # Attach properties to Blender types
    bpy.types.Scene.movie_director = bpy.props.PointerProperty(
        type=MovieDirectorProperties
    )

def unregister():
    """Unregister all addon classes"""
    # Remove properties first
    del bpy.types.Scene.movie_director
    
    # Unregister in reverse order
    unregister_class(MOVIE_DIRECTOR_PT_character_panel)
    unregister_class(MOVIE_DIRECTOR_PT_main_panel)
    unregister_class(MOVIE_DIRECTOR_OT_generate_shot)
    unregister_class(MOVIE_DIRECTOR_OT_generate_character)
    unregister_class(CharacterAssetProperties)
    unregister_class(MovieDirectorProperties)
```

### File Path Management
```python
import bpy
import os
from bpy.utils import extension_path_user, user_resource

def get_addon_directory():
    """Get the addon's installation directory"""
    return os.path.dirname(os.path.realpath(__file__))

def get_user_data_directory():
    """Get user-specific data directory for the addon"""
    # Creates directory if it doesn't exist
    return extension_path_user(__package__, create=True)

def get_addon_preferences_directory():
    """Get directory for addon preferences and configuration"""
    return user_resource('CONFIG', path='blender', create=True)

def get_addon_cache_directory():
    """Get directory for temporary addon data"""
    return user_resource('CACHE', path='blender', create=True)

# Example usage for Movie Director addon
def setup_addon_directories():
    """Set up all required directories for Movie Director addon"""
    directories = {
        'user_data': get_user_data_directory(),
        'models': os.path.join(get_user_data_directory(), 'models'),
        'workflows': os.path.join(get_user_data_directory(), 'workflows'),
        'generated': os.path.join(get_user_data_directory(), 'generated'),
        'cache': get_addon_cache_directory()
    }
    
    # Create directories if they don't exist
    for name, path in directories.items():
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"Created {name} directory: {path}")
    
    return directories
```

### Resource Path Management
```python
def get_resource_path(resource_type, create=False):
    """Get platform-appropriate resource paths"""
    # Available resource types:
    # 'DATAFILES', 'CONFIG', 'SCRIPTS', 'AUTOSAVE', 'TEMPDIR', 'CACHE'
    return user_resource(resource_type, create=create)

def get_addon_config_file():
    """Get path to addon configuration file"""
    config_dir = user_resource('CONFIG', create=True)
    return os.path.join(config_dir, 'movie_director_config.json')

def get_vram_profiles_file():
    """Get path to VRAM profiles configuration"""
    addon_data = get_user_data_directory()
    return os.path.join(addon_data, 'vram_profiles.json')

def get_workflow_templates_directory():
    """Get directory containing ComfyUI workflow templates"""
    addon_data = get_user_data_directory()
    workflows_dir = os.path.join(addon_data, 'workflows')
    
    # Create subdirectories for different workflow types
    subdirs = ['comfyui', 'wan2gp', 'character', 'style', 'video', 'audio']
    for subdir in subdirs:
        subdir_path = os.path.join(workflows_dir, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path, exist_ok=True)
    
    return workflows_dir
```

## Addon-Specific Utilities

### Dynamic Class Registration
```python
def register_classes(class_list):
    """Register multiple classes with error handling"""
    for cls in class_list:
        try:
            register_class(cls)
        except ValueError as e:
            print(f"Failed to register {cls.__name__}: {e}")

def unregister_classes(class_list):
    """Unregister multiple classes with error handling"""
    for cls in reversed(class_list):  # Reverse order for dependencies
        try:
            unregister_class(cls)
        except ValueError as e:
            print(f"Failed to unregister {cls.__name__}: {e}")

# Movie Director addon class management
CLASSES = [
    # Property groups
    MovieDirectorProperties,
    CharacterAssetProperties,
    ShotProperties,
    
    # Operators
    MOVIE_DIRECTOR_OT_generate_character,
    MOVIE_DIRECTOR_OT_train_character_lora,
    MOVIE_DIRECTOR_OT_generate_shot,
    MOVIE_DIRECTOR_OT_assemble_scene,
    
    # Panels
    MOVIE_DIRECTOR_PT_main_panel,
    MOVIE_DIRECTOR_PT_character_panel,
    MOVIE_DIRECTOR_PT_shot_panel,
    MOVIE_DIRECTOR_PT_generation_panel,
]

def register():
    register_classes(CLASSES)
    # Additional registration code...

def unregister():
    # Cleanup code...
    unregister_classes(CLASSES)
```

### Extension and Version Management
```python
def get_addon_version():
    """Get current addon version from bl_info"""
    if hasattr(bpy.context, 'preferences'):
        addon_prefs = bpy.context.preferences.addons.get(__package__)
        if addon_prefs and hasattr(addon_prefs, 'bl_info'):
            return addon_prefs.bl_info.get('version', (0, 0, 0))
    return (0, 0, 0)

def check_blender_version(min_version):
    """Check if Blender version meets minimum requirements"""
    return bpy.app.version >= min_version

def check_addon_compatibility():
    """Check if addon is compatible with current Blender version"""
    min_version = (4, 0, 0)  # Movie Director requires Blender 4.0+
    
    if not check_blender_version(min_version):
        version_str = ".".join(map(str, min_version))
        current_str = ".".join(map(str, bpy.app.version))
        raise RuntimeError(
            f"Movie Director requires Blender {version_str} or later. "
            f"Current version: {current_str}"
        )
```

### Module and Package Management
```python
def safe_import_module(module_name, package=None):
    """Safely import a module with error handling"""
    try:
        if package:
            return __import__(module_name, fromlist=[package])
        else:
            return __import__(module_name)
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")
        return None

def check_dependencies():
    """Check if required dependencies are available"""
    required_modules = {
        'requests': 'HTTP client for backend communication',
        'json': 'JSON processing for workflows and configs',
        'asyncio': 'Async operations for non-blocking generation',
        'threading': 'Background task management',
    }
    
    missing_modules = []
    for module_name, description in required_modules.items():
        if not safe_import_module(module_name):
            missing_modules.append((module_name, description))
    
    if missing_modules:
        print("Missing required modules:")
        for module_name, description in missing_modules:
            print(f"  - {module_name}: {description}")
        return False
    
    return True
```

## File System Utilities

### Safe File Operations
```python
def safe_write_json(filepath, data):
    """Safely write JSON data to file"""
    try:
        # Ensure directory exists
        directory = os.path.dirname(filepath)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Write to temporary file first
        temp_filepath = filepath + '.tmp'
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        os.replace(temp_filepath, filepath)
        return True
        
    except Exception as e:
        print(f"Failed to write JSON to {filepath}: {e}")
        # Cleanup temp file if it exists
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return False

def safe_read_json(filepath):
    """Safely read JSON data from file"""
    try:
        if not os.path.exists(filepath):
            return None
            
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        print(f"Failed to read JSON from {filepath}: {e}")
        return None

def ensure_directory_exists(directory_path):
    """Ensure directory exists, create if necessary"""
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Failed to create directory {directory_path}: {e}")
        return False
```

### Temporary File Management
```python
import tempfile

def create_temp_directory():
    """Create temporary directory for addon operations"""
    return tempfile.mkdtemp(prefix='movie_director_')

def cleanup_temp_directory(temp_dir):
    """Clean up temporary directory"""
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Failed to cleanup temp directory {temp_dir}: {e}")

class TempDirectoryManager:
    """Context manager for temporary directories"""
    def __init__(self):
        self.temp_dir = None
    
    def __enter__(self):
        self.temp_dir = create_temp_directory()
        return self.temp_dir
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir:
            cleanup_temp_directory(self.temp_dir)

# Usage example
def process_with_temp_files():
    with TempDirectoryManager() as temp_dir:
        # Use temp_dir for operations
        workflow_file = os.path.join(temp_dir, 'workflow.json')
        # Files automatically cleaned up when exiting context
```

## Initialization and Cleanup

### Addon Initialization
```python
def initialize_addon():
    """Initialize addon on registration"""
    print("Initializing Movie Director addon...")
    
    # Check compatibility
    check_addon_compatibility()
    
    # Check dependencies
    if not check_dependencies():
        raise RuntimeError("Missing required dependencies")
    
    # Set up directories
    directories = setup_addon_directories()
    print(f"Addon data directory: {directories['user_data']}")
    
    # Initialize configuration
    config_file = get_addon_config_file()
    if not os.path.exists(config_file):
        default_config = {
            'version': get_addon_version(),
            'backend_urls': {
                'comfyui': 'http://localhost:8188',
                'wan2gp': 'http://localhost:7860',
                'litellm': 'http://localhost:4000'
            },
            'vram_budget': 'balanced',
            'default_quality': 'standard'
        }
        safe_write_json(config_file, default_config)
    
    print("Movie Director addon initialized successfully")

def cleanup_addon():
    """Cleanup addon on unregistration"""
    print("Cleaning up Movie Director addon...")
    
    # Cancel any running operations
    # (This would be implemented based on actual async operations)
    
    # Clear temporary files
    cache_dir = get_addon_cache_directory()
    if os.path.exists(cache_dir):
        try:
            import shutil
            shutil.rmtree(cache_dir)
        except Exception as e:
            print(f"Failed to clear cache: {e}")
    
    print("Movie Director addon cleanup complete")

# Integration with register/unregister
def register():
    register_classes(CLASSES)
    initialize_addon()

def unregister():
    cleanup_addon()
    unregister_classes(CLASSES)
```

## Best Practices

### 1. Use Extension Paths for User Data
```python
# GOOD: Platform-appropriate user data location
user_dir = extension_path_user(__package__, create=True)

# AVOID: Hardcoded paths
user_dir = "/home/user/.blender/addons/movie_director"  # Linux only!
```

### 2. Handle Registration Errors Gracefully
```python
# GOOD: Error handling in registration
def register():
    try:
        register_classes(CLASSES)
    except Exception as e:
        print(f"Failed to register Movie Director addon: {e}")
        # Cleanup partial registration
        unregister()
        raise

# AVOID: Unhandled registration failures
def register():
    register_classes(CLASSES)  # May fail partially
```

### 3. Use Relative Imports for Addon Modules
```python
# GOOD: Relative imports within addon
from .agents import cinematographer
from .ui import panels
from .utils import vram_manager

# AVOID: Absolute imports that may break
import movie_director.agents.cinematographer  # Fragile
```

### 4. Provide Clear Error Messages
```python
# GOOD: Informative error messages
def validate_installation():
    if not check_blender_version((4, 0, 0)):
        raise RuntimeError(
            "Movie Director requires Blender 4.0 or later. "
            "Please update Blender and try again."
        )

# AVOID: Cryptic error messages
def validate_installation():
    assert bpy.app.version >= (4, 0, 0)  # Unclear to users
```

This utilities guide ensures robust addon lifecycle management and cross-platform compatibility for the Movie Director addon while following Blender's best practices for addon development.