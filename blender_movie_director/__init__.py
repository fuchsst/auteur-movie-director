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
    "author": "BMAD Development Team",
    "description": "AI-powered generative film studio integrated into Blender",
    "location": "View3D > Sidebar > Movie Director",
    "warning": "Early development version - requires local ComfyUI/Wan2GP setup",
    "doc_url": "",
    "tracker_url": "",
}

import bpy
from . import ui
from . import producer
from . import agents
from . import backend

def register():
    """Register all addon components"""
    ui.register()
    producer.register()
    agents.register()
    backend.register()
    
    print("Blender Movie Director addon registered successfully")

def unregister():
    """Unregister all addon components"""
    backend.unregister()
    agents.unregister()
    producer.unregister()
    ui.unregister()
    
    print("Blender Movie Director addon unregistered")

if __name__ == "__main__":
    register()