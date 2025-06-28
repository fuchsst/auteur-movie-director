"""
Blender Movie Director - A BMAD-Architected Generative Film Studio for Blender

A comprehensive addon that transforms Blender into a local-first, agent-driven
generative film studio capable of creating complete cinematic sequences.
"""

bl_info = {
    "name": "Blender Movie Director",
    "blender": (4, 0, 0),  # Minimum version 4.0, compatible up to 4.4+
    "category": "Sequencer",
    "version": (0, 1, 0),
    "author": "BMAD Development Team",
    "description": "AI-powered generative film studio integrated into Blender",
    "location": "View3D > Sidebar > Movie Director",
    "warning": "Early development version - requires local AI backend services",
    "doc_url": "https://github.com/yourusername/blender-movie-director",
    "tracker_url": "https://github.com/yourusername/blender-movie-director/issues",
}

import logging

# Only import bpy and addon modules when running inside Blender
try:
    import bpy

    _IN_BLENDER = True
except ImportError:
    _IN_BLENDER = False
    bpy = None

# Only import addon modules when in Blender
if _IN_BLENDER:
    from . import agents, backend, preferences, ui

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register():
    """Register all addon components"""
    if not _IN_BLENDER:
        logger.warning("Register called outside of Blender environment")
        return

    # Register preferences first
    preferences.register()

    # Register core components
    backend.register()
    agents.register()
    ui.register()

    # Auto-discover services on startup if enabled
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs.auto_discover_on_startup:
            # Defer discovery to avoid blocking startup
            bpy.app.timers.register(
                lambda: bpy.ops.movie_director.discover_services("INVOKE_DEFAULT"),
                first_interval=2.0,
            )
    except:
        pass

    logger.info("Blender Movie Director addon registered successfully")


def unregister():
    """Unregister all addon components"""
    if not _IN_BLENDER:
        logger.warning("Unregister called outside of Blender environment")
        return

    # Unregister in reverse order
    ui.unregister()
    agents.unregister()
    backend.unregister()
    preferences.unregister()

    logger.info("Blender Movie Director addon unregistered")


if __name__ == "__main__":
    register()
