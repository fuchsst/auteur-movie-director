"""
Blender UI Panels

Custom panels providing native Blender integration for the Movie Director addon.
Located in 3D Viewport sidebar with intuitive film production controls.
"""

import bpy
from bpy.types import Panel

# Import service status panels
from .service_status_panel import (
    MOVIE_DIRECTOR_PT_service_status,
    MOVIE_DIRECTOR_PT_service_config,
)


class MOVIE_DIRECTOR_PT_main_panel(Panel):
    """Main Movie Director panel"""

    bl_label = "Movie Director"
    bl_idname = "MOVIE_DIRECTOR_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Movie Director"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        project = scene.movie_director

        # Project header
        box = layout.box()
        box.label(text="Project", icon="FILE_MOVIE")
        box.prop(project, "project_name", text="")
        box.prop(project, "target_resolution")

        # Project initialization
        if not project.project_name or project.project_name == "Untitled Film":
            layout.operator("movie_director.init_project", icon="PLUS")

        # Backend status
        row = layout.row()
        row.prop(project, "backend_status", text="Backend")
        if project.backend_status == "CONNECTED":
            row.label(text="", icon="LINKED")
        elif project.backend_status == "ERROR":
            row.label(text="", icon="ERROR")
        else:
            row.label(text="", icon="UNLINKED")


class MOVIE_DIRECTOR_PT_assets_panel(Panel):
    """Assets management panel"""

    bl_label = "Assets"
    bl_idname = "MOVIE_DIRECTOR_PT_assets_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Movie Director"
    bl_parent_id = "MOVIE_DIRECTOR_PT_main_panel"

    def draw(self, context):
        layout = self.layout

        # Characters
        box = layout.box()
        box.label(text="Characters", icon="OUTLINER_OB_ARMATURE")
        box.operator("movie_director.create_character", icon="PLUS")

        # Display existing characters
        characters_collection = bpy.data.collections.get("Characters")
        if characters_collection:
            for obj in characters_collection.objects:
                if hasattr(obj, "movie_director_character"):
                    row = box.row()
                    row.label(text=obj.name, icon="USER")

        # Styles
        box = layout.box()
        box.label(text="Styles", icon="MATERIAL")
        box.operator("movie_director.create_style", icon="PLUS")

        # Display existing styles
        styles_collection = bpy.data.collections.get("Styles")
        if styles_collection:
            for obj in styles_collection.objects:
                if hasattr(obj, "movie_director_style"):
                    row = box.row()
                    row.label(text=obj.name, icon="BRUSH_DATA")

        # Locations
        box = layout.box()
        box.label(text="Locations", icon="WORLD")
        box.operator("movie_director.create_location", icon="PLUS")


class MOVIE_DIRECTOR_PT_production_panel(Panel):
    """Production workflow panel"""

    bl_label = "Production"
    bl_idname = "MOVIE_DIRECTOR_PT_production_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Movie Director"
    bl_parent_id = "MOVIE_DIRECTOR_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        project = scene.movie_director

        # Scene creation
        box = layout.box()
        box.label(text="Scenes", icon="SEQUENCE")
        box.operator("movie_director.create_scene", icon="PLUS")

        # Shot creation
        box = layout.box()
        box.label(text="Shots", icon="CAMERA_DATA")
        box.operator("movie_director.create_shot", icon="PLUS")

        # Generation controls
        box = layout.box()
        box.label(text="Generation", icon="PLAY")

        if project.generation_active:
            box.label(text="Generation in progress...", icon="TIME")
        else:
            box.operator("movie_director.generate_shot", icon="RENDER_ANIMATION")


class MOVIE_DIRECTOR_PT_shot_properties(Panel):
    """Shot properties panel - context sensitive"""

    bl_label = "Shot Properties"
    bl_idname = "MOVIE_DIRECTOR_PT_shot_properties"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Movie Director"
    bl_parent_id = "MOVIE_DIRECTOR_PT_main_panel"

    @classmethod
    def poll(cls, context):
        """Only show when a shot object is selected"""
        obj = context.active_object
        return (
            obj and hasattr(obj, "movie_director_shot") and obj.movie_director_shot.shot_number > 0
        )

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        shot = obj.movie_director_shot

        # Shot info
        layout.prop(shot, "shot_number")
        layout.prop(shot, "generation_status")

        # Content
        box = layout.box()
        box.label(text="Content", icon="FILE_TEXT")
        box.prop(shot, "dialogue_text", text="Dialogue")
        box.prop(shot, "camera_notes", text="Camera")

        # Generated files
        if shot.video_clip_path:
            box = layout.box()
            box.label(text="Generated Files", icon="FILE_MOVIE")
            box.prop(shot, "video_clip_path", text="Video")
            if shot.audio_path:
                box.prop(shot, "audio_path", text="Audio")


def register():
    """Register all panels"""
    # Register service status panels first (they appear at top)
    bpy.utils.register_class(MOVIE_DIRECTOR_PT_service_status)
    bpy.utils.register_class(MOVIE_DIRECTOR_PT_service_config)
    
    # Register main panels
    bpy.utils.register_class(MOVIE_DIRECTOR_PT_main_panel)
    bpy.utils.register_class(MOVIE_DIRECTOR_PT_assets_panel)
    bpy.utils.register_class(MOVIE_DIRECTOR_PT_production_panel)
    bpy.utils.register_class(MOVIE_DIRECTOR_PT_shot_properties)


def unregister():
    """Unregister all panels"""
    # Unregister in reverse order
    bpy.utils.unregister_class(MOVIE_DIRECTOR_PT_shot_properties)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_PT_production_panel)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_PT_assets_panel)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_PT_main_panel)
    
    # Unregister service status panels last
    bpy.utils.unregister_class(MOVIE_DIRECTOR_PT_service_config)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_PT_service_status)
