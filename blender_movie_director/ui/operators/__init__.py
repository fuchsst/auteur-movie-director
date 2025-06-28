"""
Blender Operators

Operators that bridge UI interactions with the agent system,
triggering workflows and managing generative assets.
"""

import bpy
from bpy.props import StringProperty
from bpy.types import Operator

# Import service discovery operators
from . import service_discovery_ops


class MOVIE_DIRECTOR_OT_init_project(Operator):
    """Initialize a new Movie Director project"""

    bl_idname = "movie_director.init_project"
    bl_label = "Initialize Project"
    bl_description = "Set up a new generative film project"

    project_name: StringProperty(name="Project Name", default="New Film")

    def execute(self, context):
        scene = context.scene
        scene.movie_director.project_name = self.project_name

        # Create default collections
        main_collection = bpy.data.collections.new("Movie Director")
        context.scene.collection.children.link(main_collection)

        characters_collection = bpy.data.collections.new("Characters")
        styles_collection = bpy.data.collections.new("Styles")
        locations_collection = bpy.data.collections.new("Locations")
        scenes_collection = bpy.data.collections.new("Scenes")

        main_collection.children.link(characters_collection)
        main_collection.children.link(styles_collection)
        main_collection.children.link(locations_collection)
        main_collection.children.link(scenes_collection)

        self.report({"INFO"}, f"Project '{self.project_name}' initialized")
        return {"FINISHED"}


class MOVIE_DIRECTOR_OT_create_character(Operator):
    """Create a new character asset"""

    bl_idname = "movie_director.create_character"
    bl_label = "Create Character"
    bl_description = "Create a new character for the film"

    character_name: StringProperty(name="Character Name", default="New Character")

    def execute(self, context):
        # Create empty object for character
        bpy.ops.object.empty_add(type="PLAIN_AXES")
        character_obj = context.active_object
        character_obj.name = self.character_name

        # Set character properties
        character_obj.movie_director_character.name = self.character_name

        # Move to Characters collection
        characters_collection = bpy.data.collections.get("Characters")
        if characters_collection:
            context.scene.collection.objects.unlink(character_obj)
            characters_collection.objects.link(character_obj)

        self.report({"INFO"}, f"Character '{self.character_name}' created")
        return {"FINISHED"}


class MOVIE_DIRECTOR_OT_create_style(Operator):
    """Create a new style asset"""

    bl_idname = "movie_director.create_style"
    bl_label = "Create Style"
    bl_description = "Create a new visual style definition"

    style_name: StringProperty(name="Style Name", default="New Style")

    def execute(self, context):
        # Create empty object for style
        bpy.ops.object.empty_add(type="CUBE")
        style_obj = context.active_object
        style_obj.name = self.style_name

        # Set style properties
        style_obj.movie_director_style.name = self.style_name

        # Move to Styles collection
        styles_collection = bpy.data.collections.get("Styles")
        if styles_collection:
            context.scene.collection.objects.unlink(style_obj)
            styles_collection.objects.link(style_obj)

        self.report({"INFO"}, f"Style '{self.style_name}' created")
        return {"FINISHED"}


class MOVIE_DIRECTOR_OT_create_location(Operator):
    """Create a new location asset"""

    bl_idname = "movie_director.create_location"
    bl_label = "Create Location"
    bl_description = "Create a new location for scenes"

    location_name: StringProperty(name="Location Name", default="New Location")

    def execute(self, context):
        # Create empty object for location
        bpy.ops.object.empty_add(type="SPHERE")
        location_obj = context.active_object
        location_obj.name = self.location_name

        # Set location properties
        location_obj.movie_director_location.name = self.location_name

        # Move to Locations collection
        locations_collection = bpy.data.collections.get("Locations")
        if locations_collection:
            context.scene.collection.objects.unlink(location_obj)
            locations_collection.objects.link(location_obj)

        self.report({"INFO"}, f"Location '{self.location_name}' created")
        return {"FINISHED"}


class MOVIE_DIRECTOR_OT_create_scene(Operator):
    """Create a new scene collection"""

    bl_idname = "movie_director.create_scene"
    bl_label = "Create Scene"
    bl_description = "Create a new scene with shot structure"

    scene_name: StringProperty(name="Scene Name", default="Scene 1")

    def execute(self, context):
        # Create scene collection
        scene_collection = bpy.data.collections.new(self.scene_name)
        scene_collection.movie_director_scene.scene_number = len(bpy.data.collections) + 1

        # Link to Scenes collection
        scenes_collection = bpy.data.collections.get("Scenes")
        if scenes_collection:
            scenes_collection.children.link(scene_collection)
        else:
            context.scene.collection.children.link(scene_collection)

        self.report({"INFO"}, f"Scene '{self.scene_name}' created")
        return {"FINISHED"}


class MOVIE_DIRECTOR_OT_create_shot(Operator):
    """Create a new shot in the active scene"""

    bl_idname = "movie_director.create_shot"
    bl_label = "Create Shot"
    bl_description = "Create a new shot for video generation"

    def execute(self, context):
        # Create empty object for shot
        bpy.ops.object.empty_add(type="SINGLE_ARROW")
        shot_obj = context.active_object

        # Set shot properties
        shot_number = (
            len([obj for obj in context.scene.objects if obj.movie_director_shot.shot_number > 0])
            + 1
        )
        shot_obj.name = f"Shot {shot_number:03d}"
        shot_obj.movie_director_shot.shot_number = shot_number

        self.report({"INFO"}, f"Shot {shot_number} created")
        return {"FINISHED"}


class MOVIE_DIRECTOR_OT_generate_shot(Operator):
    """Generate video for a shot"""

    bl_idname = "movie_director.generate_shot"
    bl_label = "Generate Shot"
    bl_description = "Generate video clip for the selected shot"

    def execute(self, context):
        shot_obj = context.active_object

        if not shot_obj or not hasattr(shot_obj, "movie_director_shot"):
            self.report({"ERROR"}, "Please select a shot object")
            return {"CANCELLED"}

        # Set generation status
        shot_obj.movie_director_shot.generation_status = "GENERATING"
        context.scene.movie_director.generation_active = True

        # TODO: Trigger Cinematographer agent
        self.report({"INFO"}, f"Generating video for {shot_obj.name}")
        return {"FINISHED"}


def register():
    """Register all operators"""
    # Register service discovery operators
    service_discovery_ops.register()

    # Register project operators
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_init_project)
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_create_character)
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_create_style)
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_create_location)
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_create_scene)
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_create_shot)
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_generate_shot)


def unregister():
    """Unregister all operators"""
    # Unregister project operators
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_generate_shot)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_create_shot)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_create_scene)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_create_location)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_create_style)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_create_character)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_init_project)

    # Unregister service discovery operators
    service_discovery_ops.unregister()
