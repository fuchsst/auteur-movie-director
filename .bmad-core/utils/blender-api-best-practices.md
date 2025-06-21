# Blender API Best Practices for Addon Development

## Core Principles

### 1. Blender Integration Patterns
Follow these fundamental patterns for professional Blender addon development:

- **Use bpy.utils.register_class()** for proper class registration
- **Implement proper register()/unregister()** functions with error handling
- **Store data in scene.custom_properties** for project portability
- **Use bpy.utils.extension_path_user()** for user-specific file storage
- **Respect bpy.app.online_access** for internet connectivity

### 2. UI Development Best Practices

#### Panel Structure
```python
class MOVIE_DIRECTOR_PT_main_panel(bpy.types.Panel):
    bl_label = "Movie Director"
    bl_idname = "MOVIE_DIRECTOR_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Movie Director'
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        # Use layout.box() for visual grouping
        # Use layout.row() and layout.column() for organization
        # Use layout.separator() for spacing
```

#### Operator Implementation
```python
class MOVIE_DIRECTOR_OT_generate_video(bpy.types.Operator):
    bl_idname = "movie_director.generate_video"
    bl_label = "Generate Video"
    bl_description = "Generate video clip using AI"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            # Implement operation logic
            self.report({'INFO'}, "Video generation completed")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Video generation failed: {str(e)}")
            return {'CANCELLED'}
```

#### Custom Properties
```python
class MovieDirectorProperties(bpy.types.PropertyGroup):
    characters: bpy.props.CollectionProperty(type=CharacterAsset)
    styles: bpy.props.CollectionProperty(type=StyleAsset)
    
    show_advanced: bpy.props.BoolProperty(
        name="Show Advanced Options",
        description="Display advanced generation settings",
        default=False
    )

def register():
    bpy.utils.register_class(MovieDirectorProperties)
    bpy.types.Scene.movie_director = bpy.props.PointerProperty(type=MovieDirectorProperties)
```

### 3. Performance Optimization

#### Efficient List Operations
```python
# Good: Use extend() for multiple items
items = []
items.extend(new_items)

# Good: Use list comprehensions
filtered_items = [item for item in items if item.enabled]

# Avoid: Multiple append() calls in loops
# for item in new_items:
#     items.append(item)  # Inefficient
```

#### String Operations
```python
# Good: Use startswith() and endswith()
if filename.endswith('.blend'):
    process_file(filename)

# Good: Use join() for string concatenation
path = os.path.join(base_path, 'subfolder', 'file.txt')

# Avoid: String slicing for simple checks
# if filename[-6:] == '.blend':  # Less efficient
```

#### Avoid Blocking Operations
```python
import asyncio
import bpy

class AsyncOperator(bpy.types.Operator):
    bl_idname = "movie_director.async_operation"
    bl_label = "Async Operation"
    
    def execute(self, context):
        # Start async operation without blocking UI
        asyncio.create_task(self.async_work())
        return {'FINISHED'}
    
    async def async_work(self):
        # Long-running operation
        result = await some_long_operation()
        # Update UI from main thread
        bpy.app.timers.register(lambda: self.update_ui(result))
```

### 4. Memory Management

#### VRAM Considerations
```python
class VRAMManager:
    def __init__(self):
        self.allocated_memory = {}
        self.memory_limit = self.get_gpu_memory()
    
    def check_memory_available(self, required_gb):
        current_usage = sum(self.allocated_memory.values())
        return (current_usage + required_gb) <= self.memory_limit
    
    def allocate_memory(self, task_id, memory_gb):
        if self.check_memory_available(memory_gb):
            self.allocated_memory[task_id] = memory_gb
            return True
        return False
    
    def free_memory(self, task_id):
        if task_id in self.allocated_memory:
            del self.allocated_memory[task_id]
```

#### Resource Cleanup
```python
class ResourceManager:
    def __enter__(self):
        self.temp_files = []
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up temporary files
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# Usage
with ResourceManager() as rm:
    # Operations that create temporary resources
    pass  # Automatic cleanup
```

### 5. Error Handling Patterns

#### Graceful Error Recovery
```python
def safe_operation(self, context):
    try:
        result = self.risky_operation()
        return {'FINISHED'}
    except MemoryError:
        self.report({'ERROR'}, "Insufficient memory. Try reducing quality settings.")
        return {'CANCELLED'}
    except ConnectionError:
        self.report({'WARNING'}, "Backend unavailable. Some features disabled.")
        return self.fallback_operation(context)
    except Exception as e:
        self.report({'ERROR'}, f"Unexpected error: {str(e)}")
        return {'CANCELLED'}
```

#### User-Friendly Messages
```python
def report_progress(self, context, stage, progress):
    message = f"{stage}: {int(progress * 100)}% complete"
    self.report({'INFO'}, message)
    
    # Update UI progress bar
    context.scene.movie_director.generation_progress = progress
    
    # Force UI refresh
    bpy.context.area.tag_redraw()
```

### 6. File and Path Management

#### Safe Path Handling
```python
import bpy
import os

def get_addon_directory():
    """Get addon's installation directory"""
    return os.path.dirname(os.path.realpath(__file__))

def get_user_directory():
    """Get user-specific addon directory"""
    return bpy.utils.extension_path_user(__package__, create=True)

def safe_file_path(filename):
    """Create safe file path in user directory"""
    user_dir = get_user_directory()
    # Sanitize filename
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    return os.path.join(user_dir, safe_name)
```

#### Asset Management
```python
def mark_as_asset(obj, catalog_name="Movie Director"):
    """Mark Blender object as asset for Asset Browser"""
    if obj:
        obj.asset_mark()
        obj.asset_generate_preview()
        
        # Assign to catalog
        catalog_id = create_or_get_catalog(catalog_name)
        obj.asset_data.catalog_id = catalog_id

def create_or_get_catalog(catalog_name):
    """Create or get asset catalog"""
    # Implementation for catalog management
    pass
```

### 7. Async and Threading

#### Safe UI Updates from Threads
```python
import threading
import bpy

def background_task(callback):
    """Run task in background thread"""
    def worker():
        try:
            result = perform_long_operation()
            # Schedule UI update on main thread
            bpy.app.timers.register(lambda: callback(result))
        except Exception as e:
            bpy.app.timers.register(lambda: callback(None, str(e)))
    
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

def update_ui_with_result(result, error=None):
    """Update UI from main thread"""
    if error:
        # Handle error
        pass
    else:
        # Update with result
        pass
```

### 8. Testing and Debugging

#### Debug Logging
```python
import logging

# Set up addon-specific logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def debug_log(message, level=logging.INFO):
    """Log debug message with context"""
    logger.log(level, f"[Movie Director] {message}")

# Usage
debug_log("Starting video generation", logging.INFO)
debug_log(f"VRAM usage: {vram_usage}GB", logging.DEBUG)
```

#### Unit Testing
```python
import unittest
import bpy

class TestMovieDirectorOperations(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        bpy.ops.wm.read_factory_settings(use_empty=True)
        
    def test_character_creation(self):
        """Test character asset creation"""
        initial_count = len(bpy.context.scene.movie_director.characters)
        bpy.ops.movie_director.add_character(name="Test Character")
        final_count = len(bpy.context.scene.movie_director.characters)
        self.assertEqual(final_count, initial_count + 1)
        
    def tearDown(self):
        """Clean up after test"""
        pass
```

## Integration with CrewAI

### Agent Tool Implementation
```python
from crewai.tools import BaseTool

class BlenderAssetTool(BaseTool):
    name = "blender_asset_manager"
    description = "Manage Blender assets for film production"
    
    def __init__(self, context):
        super().__init__()
        self.context = context
    
    def _run(self, action: str, asset_name: str, **kwargs):
        """Execute asset management action"""
        try:
            if action == "create_character":
                return self.create_character(asset_name, **kwargs)
            elif action == "apply_style":
                return self.apply_style(asset_name, **kwargs)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}
    
    def create_character(self, name, reference_images=None):
        """Create character asset in Blender"""
        # Implementation using Blender API
        pass
```

### State Management
```python
class ProjectStateManager:
    """Manage project state across agent interactions"""
    
    def __init__(self, context):
        self.context = context
        self.scene = context.scene
        
    def get_project_state(self):
        """Get current project state for agents"""
        return {
            'characters': [self.character_to_dict(c) for c in self.scene.movie_director.characters],
            'scenes': [self.scene_to_dict(s) for s in self.scene.movie_director.scenes],
            'generation_status': self.scene.movie_director.generation_status
        }
    
    def update_project_state(self, updates):
        """Update project state from agent results"""
        for key, value in updates.items():
            if hasattr(self.scene.movie_director, key):
                setattr(self.scene.movie_director, key, value)
```

These patterns ensure robust, performant, and user-friendly Blender addon development while maintaining compatibility with Blender's ecosystem and best practices.