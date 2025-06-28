"""
Blender Movie Director - A BMAD-Architected Generative Film Studio for Blender

A comprehensive addon that transforms Blender into a local-first, agent-driven
generative film studio capable of creating complete cinematic sequences.
"""

bl_info = {
    "name": "Blender Movie Director",
    "blender": (4, 0, 0),
    "category": "Sequencer",
    "version": (0, 1, 0),
    "author": "Stefan Fuchs",
    "description": "AI-powered generative film studio integrated into Blender",
    "location": "View3D > Sidebar > Movie Director",
    "warning": "Early development version - requires local AI backend services",
    "doc_url": "https://github.com/fuchsst/blender-movie-director",
    "tracker_url": "https://github.com/fuchsst/blender-movie-director/issues",
}

# Add bundled libraries to Python path before any other imports
import sys
import os

# Get the directory containing this file
addon_dir = os.path.dirname(os.path.realpath(__file__))
libs_dir = os.path.join(addon_dir, "libs")

# Add libs directory to Python path if it exists
if os.path.exists(libs_dir) and libs_dir not in sys.path:
    sys.path.insert(0, libs_dir)
    print(f"Blender Movie Director: Added bundled libs to path: {libs_dir}")

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy.types import AddonPreferences

# Import all addon modules
from . import preferences
from .ui import properties, operators, panels
from .backend import service_discovery


class MovieDirectorPreferences(AddonPreferences):
    """Addon preferences for Movie Director"""
    bl_idname = __name__

    # Service configuration
    use_custom_ports = BoolProperty(
        name="Use Custom Ports",
        description="Use custom ports instead of defaults",
        default=False,
    )

    comfyui_port = IntProperty(
        name="ComfyUI Port",
        description="Port for ComfyUI service",
        default=8188,
        min=1,
        max=65535,
    )

    wan2gp_port = IntProperty(
        name="Wan2GP Port", 
        description="Port for Wan2GP service",
        default=7860,
        min=1,
        max=65535,
    )

    rvc_port = IntProperty(
        name="RVC Port",
        description="Port for RVC service", 
        default=7865,
        min=1,
        max=65535,
    )

    audioldm_port = IntProperty(
        name="AudioLDM Port",
        description="Port for AudioLDM service",
        default=7863,
        min=1,
        max=65535,
    )

    # Auto-discovery settings
    auto_discover_on_startup = BoolProperty(
        name="Auto-discover on Startup",
        description="Automatically discover services when addon loads",
        default=True,
    )

    health_check_interval = IntProperty(
        name="Health Check Interval",
        description="Seconds between health checks",
        default=30,
        min=5,
        max=300,
    )

    def draw(self, context):
        layout = self.layout
        
        # Service Configuration
        box = layout.box()
        box.label(text="Service Configuration", icon='PREFERENCES')
        
        box.prop(self, "use_custom_ports")
        
        if self.use_custom_ports:
            col = box.column(align=True)
            col.prop(self, "comfyui_port")
            col.prop(self, "wan2gp_port") 
            col.prop(self, "rvc_port")
            col.prop(self, "audioldm_port")
        
        # Discovery Settings
        box = layout.box()
        box.label(text="Discovery Settings", icon='VIEWZOOM')
        box.prop(self, "auto_discover_on_startup")
        box.prop(self, "health_check_interval")
        
        # Service Discovery Actions
        box = layout.box()
        box.label(text="Service Management", icon='LINKED')
        row = box.row()
        row.operator("movie_director.discover_services", icon='FILE_REFRESH')


# Registration order matters - properties must be registered before operators that use them
_modules = [
    properties,
    operators, 
    panels,
]


def register():
    """Register all addon components"""
    # Register preferences first
    bpy.utils.register_class(MovieDirectorPreferences)
    
    # Register all modules
    for module in _modules:
        if hasattr(module, 'register'):
            module.register()
    
    # Auto-discover services on startup if enabled
    try:
        preferences = bpy.context.preferences.addons[__name__].preferences
        if preferences.auto_discover_on_startup:
            # Use a timer to run discovery after Blender is fully loaded
            bpy.app.timers.register(
                lambda: bpy.ops.movie_director.discover_services(),
                first_interval=2.0
            )
    except:
        # Preferences might not be available during registration
        pass
    
    print("Blender Movie Director addon registered successfully")


def unregister():
    """Unregister all addon components"""
    # Unregister modules in reverse order
    for module in reversed(_modules):
        if hasattr(module, 'unregister'):
            module.unregister()
    
    # Unregister preferences last
    bpy.utils.unregister_class(MovieDirectorPreferences)
    
    print("Blender Movie Director addon unregistered")


if __name__ == "__main__":
    register()
