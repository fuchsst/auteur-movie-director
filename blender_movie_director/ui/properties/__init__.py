"""
Custom Property Definitions

Defines the generative asset data model using Blender's property system.
Properties are stored directly in .blend files for project portability.
"""

import bpy
from bpy.props import (
    StringProperty, BoolProperty, IntProperty, FloatProperty,
    PointerProperty, CollectionProperty, EnumProperty
)
from bpy.types import PropertyGroup

class MovieDirectorCharacterProperties(PropertyGroup):
    """Character asset properties"""
    name: StringProperty(name="Character Name", default="")
    description: StringProperty(name="Description", default="")
    reference_images_path: StringProperty(name="Reference Images", subtype='DIR_PATH', default="")
    character_lora_path: StringProperty(name="Character LoRA", subtype='FILE_PATH', default="")
    voice_model_path: StringProperty(name="Voice Model", subtype='FILE_PATH', default="")
    is_trained: BoolProperty(name="LoRA Trained", default=False)

class MovieDirectorStyleProperties(PropertyGroup):
    """Style asset properties"""
    name: StringProperty(name="Style Name", default="")
    description: StringProperty(name="Description", default="")
    reference_images_path: StringProperty(name="Reference Images", subtype='DIR_PATH', default="")
    style_lora_path: StringProperty(name="Style LoRA", subtype='FILE_PATH', default="")
    
class MovieDirectorLocationProperties(PropertyGroup):
    """Location asset properties"""
    name: StringProperty(name="Location Name", default="")
    description: StringProperty(name="Description", default="")
    reference_images_path: StringProperty(name="Reference Images", subtype='DIR_PATH', default="")
    lighting_description: StringProperty(name="Lighting Notes", default="")

class MovieDirectorShotProperties(PropertyGroup):
    """Shot properties"""
    shot_number: IntProperty(name="Shot Number", default=1)
    dialogue_text: StringProperty(name="Dialogue", default="")
    camera_notes: StringProperty(name="Camera Direction", default="")
    video_clip_path: StringProperty(name="Generated Video", subtype='FILE_PATH', default="")
    audio_path: StringProperty(name="Audio Track", subtype='FILE_PATH', default="")
    generation_status: EnumProperty(
        name="Status",
        items=[
            ('PENDING', "Pending", "Not yet generated"),
            ('GENERATING', "Generating", "Currently being generated"),
            ('COMPLETED', "Completed", "Generation finished"),
            ('ERROR', "Error", "Generation failed")
        ],
        default='PENDING'
    )

class MovieDirectorSceneProperties(PropertyGroup):
    """Scene properties"""
    scene_number: IntProperty(name="Scene Number", default=1)
    location: PointerProperty(name="Location", type=bpy.types.Object)

class MovieDirectorProjectProperties(PropertyGroup):
    """Main project properties"""
    project_name: StringProperty(name="Project Name", default="Untitled Film")
    target_resolution: EnumProperty(
        name="Target Resolution",
        items=[
            ('720P', "720p", "1280x720"),
            ('1080P', "1080p", "1920x1080"),
            ('4K', "4K", "3840x2160")
        ],
        default='1080P'
    )
    generation_active: BoolProperty(name="Generation Active", default=False)
    backend_status: EnumProperty(
        name="Backend Status",
        items=[
            ('DISCONNECTED', "Disconnected", "Backend services not connected"),
            ('CONNECTED', "Connected", "Backend services ready"),
            ('ERROR', "Error", "Backend connection error")
        ],
        default='DISCONNECTED'
    )

def register():
    """Register property groups"""
    bpy.utils.register_class(MovieDirectorCharacterProperties)
    bpy.utils.register_class(MovieDirectorStyleProperties)
    bpy.utils.register_class(MovieDirectorLocationProperties)
    bpy.utils.register_class(MovieDirectorShotProperties)
    bpy.utils.register_class(MovieDirectorSceneProperties)
    bpy.utils.register_class(MovieDirectorProjectProperties)
    
    # Attach properties to Blender data structures
    bpy.types.Scene.movie_director = PointerProperty(type=MovieDirectorProjectProperties)
    bpy.types.Object.movie_director_character = PointerProperty(type=MovieDirectorCharacterProperties)
    bpy.types.Object.movie_director_style = PointerProperty(type=MovieDirectorStyleProperties)
    bpy.types.Object.movie_director_location = PointerProperty(type=MovieDirectorLocationProperties)
    bpy.types.Object.movie_director_shot = PointerProperty(type=MovieDirectorShotProperties)
    bpy.types.Collection.movie_director_scene = PointerProperty(type=MovieDirectorSceneProperties)

def unregister():
    """Unregister property groups"""
    del bpy.types.Collection.movie_director_scene
    del bpy.types.Object.movie_director_shot
    del bpy.types.Object.movie_director_location
    del bpy.types.Object.movie_director_style
    del bpy.types.Object.movie_director_character
    del bpy.types.Scene.movie_director
    
    bpy.utils.unregister_class(MovieDirectorProjectProperties)
    bpy.utils.unregister_class(MovieDirectorSceneProperties)
    bpy.utils.unregister_class(MovieDirectorShotProperties)
    bpy.utils.unregister_class(MovieDirectorLocationProperties)
    bpy.utils.unregister_class(MovieDirectorStyleProperties)
    bpy.utils.unregister_class(MovieDirectorCharacterProperties)