# Wan2GP API Guide for Movie Director Addon

## Overview

Wan2GP (Gradio-based video generation service) provides fast video generation capabilities for the Movie Director addon. It serves as one of the two primary backends for the Cinematographer agent, specializing in quick previews and efficient video generation tasks with support for multiple video models including Hunyuan Video, LTX-Video, and specialized variants.

## Guide Structure

This guide is organized into focused modules:

### 1. [Core Client Implementation](wan2gp-client-core.md)
- Basic connection management
- Available models and endpoints
- Core generation functions
- Error handling patterns

### 2. [Movie Director Integration](wan2gp-movie-director-integration.md)
- Cinematographer agent integration
- Shot generation workflows
- Batch processing
- Advanced features and templates

## Quick Start

### Basic Setup
```python
from .wan2gp_client import Wan2GPClient

# Initialize client
client = Wan2GPClient("http://localhost:7860")

# Connect to service
if client.connect():
    print("Connected to Wan2GP service")
else:
    print("Failed to connect to Wan2GP service")

# Check health
if client.check_health():
    print("Wan2GP service is healthy")
```

### Simple Video Generation
```python
# Generate video from text
result = client.generate_text_to_video(
    prompt="A serene mountain landscape at sunset",
    model="hunyuan"
)

if result["success"]:
    print(f"Video generated: {result['video_path']}")
else:
    print(f"Generation failed: {result['error']}")
```

### Image-to-Video Generation
```python
# Generate video from image
result = client.generate_image_to_video(
    image_path="/path/to/image.jpg",
    model="hunyuan_i2v",
    prompt="Camera slowly zooms out"
)

if result["success"]:
    print(f"Video generated: {result['video_path']}")
```

## Model Selection Guide

### For Movie Director Workflows

**Quick Previews:**
- `hunyuan_fast` - Fast generation for script previews
- `t2v_1.3B` - Lightweight model for rough cuts

**Standard Generation:**
- `hunyuan` - Balanced quality and speed
- `ltxv_13B_distilled` - Optimized LTX-Video variant

**High Quality Final Shots:**
- `ltxv_13B` - Full precision LTX-Video
- `vace_14B` - High-end VACE model

**Specialized Content:**
- `hunyuan_avatar` - Character-focused shots
- `fantasy` - Fantasy/stylized content
- `hunyuan_custom_audio` - Audio-guided generation

## Integration with Movie Director Agents

### Cinematographer Agent
```python
from .wan2gp_cinematographer import Wan2GPCinematographer

# Initialize cinematographer with Wan2GP backend
cinematographer = Wan2GPCinematographer()
cinematographer.setup_connection()

# Generate shot preview
shot_obj = bpy.context.active_object
preview_result = cinematographer.generate_shot_preview(shot_obj)

# Generate final shot
final_result = cinematographer.generate_shot_final(shot_obj)
```

### Batch Scene Processing
```python
# Generate all shots in a scene
scene_shots = get_scene_shots("Scene_01")
results = cinematographer.generate_scene_batch(
    scene_shots, 
    quality="standard"
)

# Process results
for shot_result in results:
    shot = shot_result["shot"]
    result = shot_result["result"]
    
    if result["success"]:
        print(f"Shot {shot.name} generated successfully")
    else:
        print(f"Shot {shot.name} failed: {result['error']}")
```

## Advanced Features

### Camera Control Integration
```python
# Apply camera movements to shots
camera_movements = ["zoom_in", "pan_right"]
result = cinematographer.generate_with_camera_control(
    shot_obj, 
    camera_movements
)
```

### Template-Based Generation
```python
from .wan2gp_templates import Wan2GPConfigTemplates

# Use predefined templates
template_config = Wan2GPConfigTemplates.apply_template(
    "character_focus", 
    "Close-up of protagonist looking determined"
)

result = client.generate_text_to_video(
    template_config["prompt"],
    model=template_config["model"]
)
```

## Error Handling and Fallbacks

### Robust Generation with Fallbacks
```python
# Generate with automatic fallback
result = cinematographer.generate_with_fallback(
    prompt="Epic battle scene",
    primary_model="ltxv_13B",
    fallback_model="hunyuan"
)

if result.get("used_fallback"):
    print(f"Used fallback model due to: {result['primary_error']}")
```

### Connection Recovery
```python
# Automatic reconnection handling
def safe_generation(prompt, model):
    try:
        return client.generate_text_to_video(prompt, model)
    except ConnectionError:
        if client.connect():
            return client.generate_text_to_video(prompt, model)
        else:
            raise RuntimeError("Could not reconnect to Wan2GP service")
```

## Performance Considerations

### Model Performance Characteristics

| Model | Speed | Quality | VRAM Usage | Best Use Case |
|-------|-------|---------|------------|---------------|
| hunyuan_fast | Very Fast | Good | Low | Previews, rough cuts |
| hunyuan | Fast | High | Medium | Standard generation |
| ltxv_13B_distilled | Medium | High | Medium | Balanced quality/speed |
| ltxv_13B | Slow | Very High | High | Final shots |
| vace_14B | Very Slow | Excellent | Very High | Hero shots |

### VRAM Optimization
```python
# For limited VRAM environments
def optimize_for_vram(available_vram_gb):
    if available_vram_gb < 8:
        return ["hunyuan_fast", "t2v_1.3B"]
    elif available_vram_gb < 16:
        return ["hunyuan", "ltxv_13B_distilled"]
    else:
        return ["ltxv_13B", "vace_14B"]

# Select appropriate models based on hardware
available_models = optimize_for_vram(12)  # 12GB VRAM
```

## Monitoring and Debugging

### Generation Monitoring
```python
def monitor_generation_progress(shot_obj):
    """Monitor generation progress and update UI"""
    while shot_obj.movie_director.generation_status == "in_progress":
        # Update progress bar
        progress = get_generation_progress(shot_obj)
        shot_obj.movie_director.generation_progress = progress
        
        # Force UI redraw
        bpy.context.area.tag_redraw()
        
        time.sleep(1)
```

### Debug Information
```python
def log_generation_details(result):
    """Log detailed generation information for debugging"""
    metadata = result.get("metadata", {})
    
    print(f"Model: {metadata.get('model', 'unknown')}")
    print(f"Endpoint: {metadata.get('endpoint', 'unknown')}")
    print(f"Prompt: {metadata.get('prompt', 'unknown')}")
    
    if not result["success"]:
        print(f"Error: {result['error']}")
        print(f"Error Type: {classify_error(result['error'])}")
```

## Best Practices Summary

1. **Always check connection status** before attempting generation
2. **Use appropriate models** for different quality requirements
3. **Implement fallback strategies** for robust operation
4. **Monitor VRAM usage** and select models accordingly
5. **Handle errors gracefully** with clear user feedback
6. **Use async operations** to maintain UI responsiveness
7. **Leverage templates** for consistent generation settings

For detailed implementation examples, see the specialized guide files linked above.