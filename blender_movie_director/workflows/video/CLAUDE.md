# Video Generation Workflows

## Role
Core video generation workflows for translating script descriptions into moving images. Handles camera control, effects, and quality optimization.

## Video Generation Types
- **Text-to-Video** - Generate from script descriptions
- **Image-to-Video** - Animate from reference images
- **Character Video** - Character-focused generation
- **Camera Controlled** - Specific camera movements

## Workflow Categories
- **Basic Generation** - Standard text-to-video
- **Character Integration** - Character LoRA + video
- **Style Application** - Style-consistent video
- **Camera Control** - Model-native and 3D reprojection
- **Effects Enhancement** - LayerFlow, bokeh, restoration

## Advanced Techniques
```python
def generate_advanced_shot(shot_obj):
    """Generate shot with advanced techniques"""
    
    if shot_obj.requires_layerflow:
        # Generate separate layers
        fg_video = generate_foreground_layer(shot_obj)
        bg_video = generate_background_layer(shot_obj)
        return composite_layers(fg_video, bg_video)
    
    if shot_obj.requires_bokeh:
        # Apply cinematic depth effects
        base_video = generate_base_video(shot_obj)
        return apply_bokeh_enhancement(base_video)
```

## Camera Control Methods
1. **Model-Native** - Fast, built-in camera parameters
2. **3D Reprojection** - Complex movements via point clouds
3. **Template-Based** - Pre-defined camera movements
4. **Custom Control** - User-defined camera paths

## Quality Optimization
- **Backend Selection** - Choose optimal generation service
- **Model Selection** - Select appropriate model for quality/speed
- **Parameter Tuning** - Optimize generation parameters
- **Post-Processing** - SeedVR2 restoration and enhancement

## Reference
- [Cinematographer](/../agents/cinematographer/CLAUDE.md)
- [Video Generation APIs](/.bmad-core/data/)