"""
Blender UI Integration Module

Provides native Blender UI components for the Movie Director addon,
including panels, operators, and property integration.
"""

import bpy
from . import panels
from . import operators  
from . import properties
from . import asset_browser

def register():
    """Register all UI components"""
    properties.register()
    operators.register()
    panels.register()
    asset_browser.register()
    
    print("Movie Director UI components registered")

def unregister():
    """Unregister all UI components"""
    asset_browser.unregister()
    panels.unregister()
    operators.unregister()
    properties.unregister()
    
    print("Movie Director UI components unregistered")