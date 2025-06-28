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
from bpy.types import Panel, Operator, PropertyGroup

# Simple test operator following the tutorial pattern
class MOVIE_DIRECTOR_OT_test_operator(bpy.types.Operator):
    """Test operator for Movie Director addon"""
    bl_idname = "movie_director.test_operator"
    bl_label = "Test Movie Director"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.report({'INFO'}, "Movie Director addon is working!")
        print("Movie Director: Test operator executed successfully")
        return {'FINISHED'}

# Simple panel following the tutorial pattern
class MOVIE_DIRECTOR_PT_main_panel(bpy.types.Panel):
    """Main panel for Movie Director"""
    bl_label = "Movie Director"
    bl_idname = "MOVIE_DIRECTOR_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Movie Director'

    def draw(self, context):
        layout = self.layout
        
        # Add a simple test button
        layout.operator("movie_director.test_operator")
        
        # Add some info text
        box = layout.box()
        box.label(text="Movie Director v0.1.0", icon='CAMERA_DATA')
        box.label(text="AI-powered film studio")

def register():
    """Register all addon components"""
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_test_operator)
    bpy.utils.register_class(MOVIE_DIRECTOR_PT_main_panel)
    
    print("Blender Movie Director addon registered successfully")

def unregister():
    """Unregister all addon components"""
    bpy.utils.unregister_class(MOVIE_DIRECTOR_PT_main_panel)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_test_operator)
    
    print("Blender Movie Director addon unregistered")

if __name__ == "__main__":
    register()
