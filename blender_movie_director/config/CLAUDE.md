# Configuration Management

## Overview

Configuration system for the Movie Director addon, managing templates, hardware optimization, and user preferences. Handles backend URLs, model selection, and workflow customization.

## Components

### Templates (`templates/`)
Default configuration templates for different use cases:
- Generation quality presets
- Backend service configurations  
- Model selection guidelines

### Hardware (`hardware/`)
Hardware detection and optimization:
- GPU capability detection
- Model compatibility checking
- Performance recommendations

## Configuration Pattern

```python
# Default configuration structure
DEFAULT_CONFIG = {
    "backend_urls": {
        "comfyui": "http://localhost:8188",
        "wan2gp": "http://localhost:7860", 
        "litellm": "http://localhost:4000"
    },
    "quality_presets": {
        "draft": {"model": "hunyuan_fast"},
        "standard": {"model": "hunyuan"},
        "high": {"model": "ltxv_13B"}
    }
}
```

## Hardware Optimization

```python
def detect_optimal_settings():
    """Detect hardware and recommend settings"""
    gpu_info = get_gpu_info()
    
    if gpu_info.vram < 8:
        return "conservative_mode"
    elif gpu_info.vram >= 24:
        return "high_performance_mode"
    else:
        return "balanced_mode"
```

## Reference
- [Addon Preferences](/.bmad-core/data/bpy-utils-guide.md#addon-preferences)