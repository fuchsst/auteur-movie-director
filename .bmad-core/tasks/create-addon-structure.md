# create-addon-structure

## Task Overview
Create a professional Blender addon directory structure with proper bl_info, registration patterns, and Blender 4.0+ compatibility.

## Objective
Establish the foundational addon structure following Blender best practices, including proper package organization, registration/unregistration, and self-contained deployment patterns.

## Key Requirements
- [ ] Proper bl_info dictionary with all required fields
- [ ] Clean register() and unregister() functions
- [ ] Modular package structure (ui/, agents/, backend/, etc.)
- [ ] Self-contained dependency management
- [ ] Cross-version compatibility (Blender 4.0+)
- [ ] Proper use of bpy.utils.extension_path_user for user files

## Implementation Steps

### 1. Create Main Addon Structure
```
addon_name/
├── __init__.py          # Main addon file with bl_info and registration
├── ui/                  # UI panels, operators, properties
│   ├── __init__.py
│   ├── panels.py
│   ├── operators.py
│   └── properties.py
├── agents/              # CrewAI film crew agents
│   ├── __init__.py
│   ├── producer.py
│   ├── cinematographer.py
│   └── ...
├── backend/             # API clients for generative engines
│   ├── __init__.py
│   ├── comfyui_client.py
│   ├── wan2gp_client.py
│   └── litellm_client.py
├── workflows/           # Workflow templates
│   ├── comfyui/
│   └── wan2gp/
├── config/              # Configuration files
│   ├── vram_profiles.json
│   └── settings.json
└── utils/               # Utility functions
    ├── __init__.py
    ├── asset_manager.py
    └── blender_integration.py
```

### 2. Implement bl_info Dictionary
```python
bl_info = {
    "name": "Blender Movie Director",
    "blender": (4, 0, 0),
    "category": "Sequencer",
    "version": (0, 1, 0),
    "author": "BMAD Development Team",
    "description": "AI-powered generative film studio integrated into Blender",
    "location": "View3D > Sidebar > Movie Director",
    "warning": "Early development version - requires local AI backends",
    "doc_url": "",
    "tracker_url": "",
}
```

### 3. Registration Pattern
```python
import bpy

# Import all modules
from . import ui
from . import agents
from . import backend
from . import utils

def register():
    """Register all addon components"""
    try:
        ui.register()
        agents.register()
        backend.register()
        utils.register()
        print("Blender Movie Director registered successfully")
    except Exception as e:
        print(f"Registration failed: {e}")
        unregister()  # Clean up on failure
        raise

def unregister():
    """Unregister all addon components"""
    try:
        utils.unregister()
        backend.unregister()
        agents.unregister()
        ui.unregister()
    except Exception as e:
        print(f"Unregistration error: {e}")
```

### 4. Module Registration Pattern
Each submodule should follow this pattern:
```python
# In each __init__.py
def register():
    # Register classes, properties, etc.
    pass

def unregister():
    # Unregister in reverse order
    pass
```

## Blender Best Practices Integration

### Self-Contained Deployment
- Bundle all dependencies as submodules
- Use `bpy.utils.extension_path_user()` for user data
- Never write to addon directory (read-only filesystem support)

### Performance Considerations
- Lazy loading of heavy modules
- Efficient import patterns
- Minimal startup overhead

### Error Handling
- Graceful registration failure recovery
- Clear error messages for users
- Dependency validation

## Success Criteria
- [ ] Addon loads successfully in Blender 4.0+
- [ ] Clean registration/unregistration without errors
- [ ] Proper package organization
- [ ] Self-contained deployment ready
- [ ] All modules import correctly
- [ ] No console errors during startup

## Related Tasks
- `design-ui-panels.md` - UI structure design
- `implement-crewai-agents.md` - Agent system implementation
- `setup-custom-properties.md` - Data model integration

## Dependencies
- `blender-addon-standards` checklist
- `addon-init-template` template
- `blender-api-patterns` utils