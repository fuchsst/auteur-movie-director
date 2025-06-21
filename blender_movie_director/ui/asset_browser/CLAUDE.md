# Asset Browser Integration

## Role
Deep integration with Blender's native Asset Browser for managing generative assets. Provides visual library for characters, styles, and other creative elements.

## Asset Integration
- **Character Assets** - Visual character library with previews
- **Style Assets** - Style reference collection
- **Generated Content** - Organized generated media
- **Asset Catalogs** - Structured organization system

## Implementation Pattern
```python
def mark_as_asset(obj, catalog="Movie Director"):
    """Mark object as asset and add to browser"""
    obj.asset_mark()
    obj.asset_generate_preview()
    
    # Assign to catalog
    catalog_id = get_or_create_catalog(catalog)
    obj.asset_data.catalog_id = catalog_id
```

## Asset Categories
- **Characters** - Character objects with LoRA references
- **Styles** - Style definitions and references
- **Locations** - Environment and setting assets
- **Generated Media** - Video and audio clips

## Workflow Integration
1. **Asset Creation** - Automatically mark generated assets
2. **Preview Generation** - Create visual thumbnails
3. **Catalog Assignment** - Organize by type and project
4. **Drag-and-Drop** - Easy reuse across projects

## Benefits
- **Visual Organization** - Browse assets visually
- **Cross-Project Reuse** - Share assets between films
- **Native Integration** - Uses Blender's built-in system
- **Familiar Interface** - Standard Blender workflow

## Reference
- [Asset Browser](/.bmad-core/data/bpy-data-guide.md)