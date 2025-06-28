# Wan2GP Backend Integration

## Role
Fast video generation service with multiple model support. Specialized for quick previews, efficient generation, and model-native camera control.

## Architecture
- **`client.py`** - Main Wan2GPClient with full API implementation
- **`schemas.py`** - Pydantic models for type safety and validation
- **`enums.py`** - All API constants, models, and recommended settings
- **`__init__.py`** - Lean interface with convenience functions

## Usage

### Quick Integration
```python
from blender_movie_director.backend.wan2gp import get_client, quick_video

# Singleton client access
client = get_client("http://localhost:7860")

# Quick preview (2s, fast)
video_path = quick_video("A cat walking in a garden")

# High quality (8s, best)
result = client.generate_high_quality("Epic battle scene")

# VACE ControlNet
result = client.generate_with_control(
    prompt="Replace person with robot",
    control_video_path="/path/to/control.mp4"
)
```

### Model Selection
- **ltxv_13B_distilled** - Fastest (< 1 min, 4 steps)
- **hunyuan** - Best quality (superior text adherence)
- **vace_14B** - Advanced control (video-to-video, inpainting)
- **t2v_1.3B** - Fast, low VRAM (6GB minimum)

### Error Handling
```python
result = client.generate_high_quality("prompt")
if result.success:
    video_path = result.video_path
else:
    print(f"Generation failed: {result.error_message}")
```

## Key Features
- **Type Safety**: Full Pydantic validation
- **31+ Models**: Complete Wan2GP model suite
- **File Handling**: Proper `handle_file()` usage for uploads
- **Connection Management**: Automatic reconnection, graceful degradation
- **Queue Management**: Abort, clear, status monitoring

## Best Practices
1. Use `quick_video()` for iteration, `generate_high_quality()` for final output
2. Always check `result.success` before using `result.video_path`
3. Use singleton client via `get_client()` for efficiency
4. Validate file paths exist before passing to generation methods
