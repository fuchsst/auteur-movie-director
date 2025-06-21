# Configuration Management

## Overview

Configuration system using **YAML format** for the Movie Director addon, managing templates, hardware optimization, and user preferences. Handles backend URLs, model selection, and workflow customization.

## File Format Standard

**All configuration files use YAML format (.yaml) for:**
- Better readability and maintainability
- Support for comments and documentation
- Simplified parsing and validation
- Industry standard for configuration management

## Configuration Files

### Core Configurations
- `agent_config.yaml` - CrewAI agent definitions and workflow settings
- `backend_services.yaml` - Backend service connections and VRAM management
- `workflow_templates/` - YAML-based generation workflow definitions

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

```yaml
# YAML configuration structure
backend_urls:
  comfyui: "http://localhost:8188"
  wan2gp: "http://localhost:7860"
  litellm: "http://localhost:4000"

quality_presets:
  draft:
    model: "hunyuan_fast"
    steps: 10
  standard:
    model: "hunyuan"
    steps: 20
  high:
    model: "ltxv_13B"
    steps: 30
```

## Python Integration

```python
import yaml

def load_config(config_path):
    """Load YAML configuration file"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

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

## Migration from JSON

All configuration files have been migrated from JSON to YAML format:
- Improved human readability
- Support for inline documentation
- Consistent with modern DevOps practices
- Easier version control and diff tracking

## Reference
- [Addon Preferences](/.bmad-core/data/bpy-utils-guide.md#addon-preferences)
- [YAML Specification](https://yaml.org/spec/)