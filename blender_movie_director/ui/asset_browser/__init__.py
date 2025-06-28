"""
Asset Browser Integration

Deep integration with Blender's Asset Browser for managing generative assets.
Provides visual library for characters, styles, and generated content.
"""

import bpy


def mark_as_movie_director_asset(obj, catalog_name="Movie Director"):
    """Mark an object as a Movie Director asset in the Asset Browser"""
    try:
        # Mark as asset
        obj.asset_mark()

        # Generate preview
        obj.asset_generate_preview()

        # Get or create catalog
        catalog_id = get_or_create_catalog(catalog_name)
        if catalog_id:
            obj.asset_data.catalog_id = catalog_id

        return True
    except Exception as e:
        print(f"Error marking asset: {e}")
        return False


def get_or_create_catalog(catalog_name):
    """Get existing catalog or create new one"""
    try:
        # Check if catalog already exists
        for catalog in bpy.context.preferences.filepaths.asset_libraries:
            if catalog.name == catalog_name:
                return catalog.catalog_id

        # Create new catalog
        bpy.ops.asset.catalog_new()
        catalogs = bpy.context.preferences.filepaths.asset_libraries
        if catalogs:
            newest_catalog = catalogs[-1]
            newest_catalog.name = catalog_name
            return newest_catalog.catalog_id
    except Exception as e:
        print(f"Error creating catalog: {e}")
        return None


class MOVIE_DIRECTOR_OT_mark_asset(bpy.types.Operator):
    """Mark selected object as Movie Director asset"""

    bl_idname = "movie_director.mark_asset"
    bl_label = "Mark as Asset"
    bl_description = "Add selected object to Asset Browser"

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({"ERROR"}, "No object selected")
            return {"CANCELLED"}

        success = mark_as_movie_director_asset(obj)
        if success:
            self.report({"INFO"}, f"Marked {obj.name} as asset")
        else:
            self.report({"ERROR"}, "Failed to mark as asset")

        return {"FINISHED"}


class MOVIE_DIRECTOR_OT_organize_assets(bpy.types.Operator):
    """Organize Movie Director assets in Asset Browser"""

    bl_idname = "movie_director.organize_assets"
    bl_label = "Organize Assets"
    bl_description = "Organize all Movie Director assets by type"

    def execute(self, context):
        organized_count = 0

        # Organize Characters
        characters_collection = bpy.data.collections.get("Characters")
        if characters_collection:
            for obj in characters_collection.objects:
                if hasattr(obj, "movie_director_character"):
                    if mark_as_movie_director_asset(obj, "Characters"):
                        organized_count += 1

        # Organize Styles
        styles_collection = bpy.data.collections.get("Styles")
        if styles_collection:
            for obj in styles_collection.objects:
                if hasattr(obj, "movie_director_style"):
                    if mark_as_movie_director_asset(obj, "Styles"):
                        organized_count += 1

        # Organize Locations
        locations_collection = bpy.data.collections.get("Locations")
        if locations_collection:
            for obj in locations_collection.objects:
                if hasattr(obj, "movie_director_location"):
                    if mark_as_movie_director_asset(obj, "Locations"):
                        organized_count += 1

        self.report({"INFO"}, f"Organized {organized_count} assets")
        return {"FINISHED"}


def register():
    """Register asset browser integration"""
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_mark_asset)
    bpy.utils.register_class(MOVIE_DIRECTOR_OT_organize_assets)


def unregister():
    """Unregister asset browser integration"""
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_organize_assets)
    bpy.utils.unregister_class(MOVIE_DIRECTOR_OT_mark_asset)
