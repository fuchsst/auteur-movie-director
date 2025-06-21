# Implement UI Panels

## Task Overview
Implement Blender UI panels that provide seamless access to the Movie Director addon functionality while maintaining Blender's calm and consistent design principles.

## Objective
Create intuitive, responsive UI panels that integrate perfectly with Blender's 3D Viewport sidebar and follow professional addon development standards.

## Key Requirements
- [ ] Follow Blender's UI guidelines for calm, consistent design
- [ ] Implement proper panel hierarchy and organization
- [ ] Create responsive layouts that adapt to sidebar width
- [ ] Use appropriate icons and visual elements
- [ ] Implement progressive disclosure for advanced features
- [ ] Ensure accessibility and keyboard navigation support

## Implementation Steps

### 1. Panel Class Structure
```python
class MovieDirectorMainPanel(bpy.types.Panel):
    bl_label = "Movie Director"
    bl_idname = "VIEW3D_PT_movie_director"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Movie Director'
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        md_props = scene.movie_director
        
        # Project status section
        self.draw_project_status(layout, md_props)
        
        # Main workflow sections
        self.draw_script_section(layout, md_props)
        self.draw_assets_section(layout, md_props)
        self.draw_production_section(layout, md_props)
```

### 2. Progressive Disclosure Implementation
```python
def draw_script_section(self, layout, md_props):
    box = layout.box()
    
    # Collapsible header
    row = box.row()
    icon = 'TRIA_DOWN' if md_props.show_script_section else 'TRIA_RIGHT'
    row.prop(md_props, "show_script_section", icon=icon, emboss=False)
    row.label(text="Script Development", icon='TEXT')
    
    # Content (shown when expanded)
    if md_props.show_script_section:
        col = box.column(align=True)
        col.operator("movie_director.edit_script", text="Open Script Editor")
        
        if md_props.script_content:
            col.separator()
            col.operator("movie_director.breakdown_script", text="Generate Breakdown")
            
            # Show breakdown status
            if md_props.scenes:
                info_box = col.box()
                info_box.label(text=f"Scenes: {len(md_props.scenes)}", icon='OUTLINER')
```

### 3. Asset Management Panel
```python
class AssetManagementPanel(bpy.types.Panel):
    bl_label = "Asset Management"
    bl_parent_id = "VIEW3D_PT_movie_director"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        md_props = scene.movie_director
        
        # Characters section
        self.draw_characters_section(layout, md_props)
        layout.separator()
        
        # Styles section
        self.draw_styles_section(layout, md_props)
        layout.separator()
        
        # Locations section
        self.draw_locations_section(layout, md_props)

    def draw_characters_section(self, layout, md_props):
        box = layout.box()
        
        # Header with add button
        row = box.row()
        row.label(text="Characters", icon='OUTLINER_OB_ARMATURE')
        row.operator("movie_director.add_character", text="", icon='ADD')
        
        # Character list
        if md_props.characters:
            for i, char in enumerate(md_props.characters):
                char_row = box.row()
                char_row.label(text=char.name, icon='USER')
                
                # Quick actions
                ops_row = char_row.row(align=True)
                ops_row.scale_x = 0.7
                
                edit_op = ops_row.operator("movie_director.edit_character", text="", icon='GREASEPENCIL')
                edit_op.character_index = i
                
                if char.needs_lora_training:
                    train_op = ops_row.operator("movie_director.train_character_lora", text="", icon='MOD_FLUIDSIM')
                    train_op.character_index = i
                
                delete_op = ops_row.operator("movie_director.delete_character", text="", icon='X')
                delete_op.character_index = i
        else:
            box.label(text="No characters defined", icon='INFO')
```

### 4. Production Pipeline Panel
```python
class ProductionPanel(bpy.types.Panel):
    bl_label = "Production Pipeline"
    bl_parent_id = "VIEW3D_PT_movie_director"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        md_props = scene.movie_director
        
        # Generation status
        self.draw_generation_status(layout, md_props)
        layout.separator()
        
        # Shot generation
        self.draw_shot_generation(layout, md_props)
        layout.separator()
        
        # Batch operations
        self.draw_batch_operations(layout, md_props)

    def draw_generation_status(self, layout, md_props):
        box = layout.box()
        box.label(text="Generation Status", icon='RENDER_ANIMATION')
        
        if md_props.active_generation_task:
            # Show progress
            progress_row = box.row()
            progress_row.label(text=f"Generating: {md_props.active_generation_task}")
            
            progress_bar = box.row()
            progress_bar.prop(md_props, "generation_progress", slider=True)
            
            # Cancel button
            cancel_row = box.row()
            cancel_row.operator("movie_director.cancel_generation", text="Cancel", icon='X')
        else:
            box.label(text="Ready for generation", icon='CHECKMARK')
```

### 5. Performance and Resource Panel
```python
class ResourceManagementPanel(bpy.types.Panel):
    bl_label = "Resource Management"
    bl_parent_id = "VIEW3D_PT_movie_director"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        md_props = scene.movie_director
        
        # VRAM status
        box = layout.box()
        box.label(text="VRAM Status", icon='MEMORY')
        
        # VRAM usage bar
        vram_row = box.row()
        vram_row.label(text=f"Usage: {md_props.vram_usage_gb:.1f} / {md_props.vram_total_gb:.1f} GB")
        
        usage_bar = box.row()
        usage_bar.prop(md_props, "vram_usage_percent", slider=True)
        
        # Performance settings
        box.separator()
        settings_col = box.column()
        settings_col.prop(md_props, "quality_preset", text="Quality")
        settings_col.prop(md_props, "vram_limit_gb", text="VRAM Limit")
        
        # Backend status
        box.separator()
        backend_col = box.column()
        backend_col.label(text="Backend Status:")
        
        status_grid = backend_col.grid_flow(columns=2, align=True)
        self.draw_backend_status(status_grid, "ComfyUI", md_props.comfyui_connected)
        self.draw_backend_status(status_grid, "Wan2GP", md_props.wan2gp_connected)
        self.draw_backend_status(status_grid, "LiteLLM", md_props.litellm_connected)

    def draw_backend_status(self, layout, name, connected):
        icon = 'CHECKMARK' if connected else 'ERROR'
        color = 'green' if connected else 'red'
        layout.label(text=name, icon=icon)
```

## UI Layout Best Practices

### Visual Hierarchy
- Use boxes (`layout.box()`) to group related functionality
- Use separators (`layout.separator()`) for visual breathing room
- Implement consistent icon usage throughout panels
- Use appropriate label text that's concise and clear

### Responsive Design
```python
def draw_responsive_buttons(self, layout, items, max_columns=3):
    """Draw buttons in responsive grid based on available space"""
    region = bpy.context.region
    ui_scale = bpy.context.preferences.system.ui_scale
    
    # Calculate optimal columns based on region width
    button_width = 100 * ui_scale
    available_width = region.width - 40  # Account for padding
    columns = min(max_columns, max(1, int(available_width / button_width)))
    
    grid = layout.grid_flow(columns=columns, align=True)
    for item in items:
        grid.operator(item.operator, text=item.text, icon=item.icon)
```

### Progressive Disclosure
- Show basic controls by default
- Hide advanced options behind collapsible sections
- Use context-sensitive UI that adapts to project state
- Provide quick access to frequently used functions

## Error Handling and Feedback

### Status Communication
```python
def draw_status_message(self, layout, message_type, message):
    """Draw status messages with appropriate styling"""
    box = layout.box()
    
    icons = {
        'info': 'INFO',
        'warning': 'ERROR',
        'error': 'CANCEL',
        'success': 'CHECKMARK'
    }
    
    box.label(text=message, icon=icons.get(message_type, 'INFO'))
```

### Input Validation
- Provide real-time feedback for invalid inputs
- Show helpful tooltips and descriptions
- Implement clear error messages with suggested solutions
- Use appropriate UI controls for data types

## Success Criteria
- [ ] All panels load without errors in Blender 4.0+
- [ ] UI follows Blender's calm, consistent design guidelines
- [ ] Panels are responsive to different sidebar widths
- [ ] Progressive disclosure works smoothly
- [ ] All interactive elements provide appropriate feedback
- [ ] Keyboard navigation works correctly
- [ ] Performance remains smooth during UI interactions

## Related Tasks
- `setup-custom-properties.md` - Data model for UI state
- `implement-operators.md` - Button functionality
- `create-addon-structure.md` - Overall addon organization

## Dependencies
- `ui-ux-compliance` checklist
- `ui-panel-template` template
- `blender-api-patterns` utils