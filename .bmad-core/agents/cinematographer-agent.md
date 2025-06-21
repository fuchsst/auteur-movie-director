# Cinematographer Agent

## Agent Profile
```yaml
agent:
  name: Cinematographer
  title: Visual Generation & Camera Control Specialist
  icon: 🎬
  focus: Video generation, camera movement, visual composition, shot creation
  specialization: AI video models, camera techniques, advanced compositing
```

## Role & Responsibilities

### Primary Function
The Cinematographer agent is the primary visual workhorse, responsible for translating written shot descriptions into compelling moving video clips. This agent handles the complex task of visual storytelling through AI-generated video content.

### Core Capabilities
- **Video Generation**: Create video clips from script descriptions using multiple AI models
- **Camera Control**: Implement both model-native and 3D reprojection camera movements
- **Visual Composition**: Apply cinematographic principles to AI-generated content
- **Advanced Effects**: Integrate LayerFlow, Any-to-Bokeh, and other enhancement techniques
- **Intelligent Routing**: Select optimal backend and model for each shot requirement

## Technical Implementation

### Dual Backend Strategy

#### Backend 1: Wan2GP (Fast Preview & Simple Shots)
```python
wan2gp_models:
  - CausVid: Fast preview generation
  - Hunyuan_Video: High-quality standard shots
  - model_native_camera: Built-in camera controls (zoom, pan, tilt)
```

#### Backend 2: ComfyUI (Complex & High-Quality Shots)
```python
comfyui_models:
  - LTX_Video: High-fidelity video generation
  - FLUX_based: Advanced style control
  - LayerFlow: Foreground/background separation
  - Custom_Workflows: Project-specific templates
```

### Camera Control Spectrum

#### Model-Native Control (Fast)
```python
camera_parameters:
  - zoom: "slow zoom in", "quick zoom out"
  - pan: "pan left", "follow character"  
  - tilt: "tilt up", "dutch angle"
  - movement: "tracking shot", "dolly forward"
```

#### 3D Reprojection Control (Advanced)
```python
advanced_camera_workflow:
  - depth_estimation: Generate depth maps from keyframe
  - point_cloud_generation: Convert to 3D space
  - camera_path_application: Apply complex virtual camera movements
  - composition_preservation: Maintain visual integrity
```

### Advanced Compositing Techniques

#### LayerFlow Integration
```python
def generate_layered_video(shot_description, character_assets, style_assets):
    """Generate separate foreground/background layers"""
    foreground_clip = generate_character_layer(character_assets)
    background_clip = generate_environment_layer(shot_description)
    
    # Import to Blender compositor with alpha channels
    import_to_compositor(foreground_clip, background_clip)
    return {"foreground": foreground_clip, "background": background_clip}
```

#### Any-to-Bokeh Enhancement
```python
def apply_cinematic_bokeh(video_clip, focus_settings):
    """Add realistic depth-aware bokeh effects"""
    bokeh_workflow = load_workflow_template("any_to_bokeh.json")
    bokeh_workflow["focus_distance"] = focus_settings.distance
    bokeh_workflow["aperture"] = focus_settings.aperture
    bokeh_workflow["input_video"] = video_clip
    
    return execute_comfyui_workflow(bokeh_workflow)
```

## CrewAI Tools
```python
tools:
  - video_generation_tool: Generate video clips from descriptions
  - camera_control_tool: Apply camera movements and techniques
  - layered_composition_tool: Create foreground/background separation
  - cinematic_enhancement_tool: Apply bokeh, color grading, effects
  - shot_routing_tool: Select optimal backend for each shot
  - template_manager: Manage ComfyUI workflow templates
```

## Workflow Integration

### Shot Generation Pipeline
1. **Shot Analysis**: Parse shot description for technical requirements
2. **Backend Selection**: Route to Wan2GP or ComfyUI based on complexity
3. **Asset Integration**: Incorporate character LoRAs and style models
4. **Generation Execution**: Execute video generation with VRAM management
5. **Post-Processing**: Apply enhancements (bokeh, restoration, etc.)
6. **Blender Import**: Import final clip with proper metadata

### Intelligent Task Routing
```python
def route_shot_generation(shot_object):
    """Intelligently route shots to appropriate backend"""
    shot_complexity = analyze_shot_complexity(shot_object)
    
    if shot_complexity.is_preview or shot_complexity.simple_movement:
        return route_to_wan2gp(shot_object)
    elif shot_complexity.needs_character_lora or shot_complexity.advanced_effects:
        return route_to_comfyui(shot_object)
    else:
        return route_based_on_vram_availability(shot_object)
```

### Template Workflow Management
```python
workflow_templates = {
    "character_closeup": "character_close_shot.json",
    "establishing_shot": "wide_establishing.json", 
    "action_sequence": "dynamic_action.json",
    "dialogue_scene": "conversational_medium.json",
    "artistic_transition": "creative_transition.json"
}

def load_and_customize_workflow(template_name, shot_data):
    """Load ComfyUI template and customize for specific shot"""
    template = load_json_template(workflow_templates[template_name])
    
    # Customize with shot-specific data
    template["prompt"] = shot_data.description
    template["character_lora"] = shot_data.character_assets
    template["style_lora"] = shot_data.style_assets
    template["camera_movement"] = shot_data.camera_direction
    
    return template
```

## Advanced Features

### 3D Reprojection Camera System
```python
def complex_camera_movement(shot_description, camera_notes):
    """Implement complex camera movements via 3D reprojection"""
    # Generate initial keyframe
    keyframe = generate_base_frame(shot_description)
    
    # Create depth map
    depth_map = estimate_depth(keyframe)
    
    # Convert to 3D point cloud
    point_cloud = depth_to_pointcloud(depth_map)
    
    # Apply virtual camera path
    camera_path = parse_camera_movement(camera_notes)
    final_video = apply_camera_path(point_cloud, camera_path)
    
    return final_video
```

### Style Consistency Integration
```python
def apply_style_consistency(video_clip, style_assets):
    """Ensure visual consistency with Art Director specifications"""
    for style_asset in style_assets:
        if style_asset.type == "lora":
            video_clip = apply_style_lora(video_clip, style_asset.path)
        elif style_asset.type == "reference":
            video_clip = apply_style_transfer(video_clip, style_asset.reference)
    
    return video_clip
```

### VRAM-Aware Generation
```python
def generate_with_vram_management(workflow, shot_data):
    """Execute video generation with VRAM budgeting"""
    required_vram = calculate_workflow_vram(workflow)
    
    if vram_manager.check_availability(required_vram):
        return execute_workflow_direct(workflow)
    else:
        return execute_workflow_sequential(workflow, shot_data)
```

## Quality Standards
- **Resolution**: Minimum 1080p, preferably 4K for final output
- **Frame Rate**: Consistent 24fps for cinematic quality
- **Color Space**: Rec.709 or DCI-P3 for professional workflows
- **Compression**: High-quality codecs suitable for post-production

## Performance Considerations
- **Model Selection**: Balance quality vs. speed based on shot importance
- **VRAM Optimization**: Sequential model loading for complex workflows
- **Cache Management**: Reuse generated elements where possible
- **Parallel Processing**: Utilize multiple GPUs when available

## Integration Points
- **Input**: Shot objects from Screenwriter, character/style assets from Casting/Art Directors
- **Output**: Video clips → Editor for final assembly
- **Resource Coordination**: VRAM management with other intensive agents
- **Quality Feedback**: Communicate generation results back to Producer

## Error Handling
- **Generation Failures**: Multiple fallback strategies (model switching, quality reduction)
- **VRAM Overflow**: Automatic workflow segmentation
- **Template Errors**: Robust workflow validation and error recovery
- **File System Issues**: Safe handling of large video files

## UI Integration
```python
def create_cinematographer_ui(shot_object):
    """Create Blender UI for shot generation"""
    layout.prop(shot_object.movie_director, "shot_description")
    layout.prop(shot_object.movie_director, "camera_direction")
    layout.prop(shot_object.movie_director, "quality_preset")
    layout.operator("movie_director.generate_shot", text="Generate Video")
    
    if shot_object.movie_director.generated_video_path:
        layout.prop(shot_object.movie_director, "generated_video_path")
        layout.operator("movie_director.preview_shot", text="Preview in VSE")
```

This agent represents the creative and technical heart of the visual generation pipeline, transforming narrative concepts into compelling cinematic sequences while maintaining professional quality standards and technical efficiency.