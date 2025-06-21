# Configuration Templates

## Role
Default configuration templates for different use cases, quality presets, and backend settings. Provides standardized configurations for consistent results.

## Template Categories
- **Quality Presets** - Draft, standard, high quality configurations
- **Backend Configs** - Service URL and connection settings
- **Model Selection** - Guidelines for different hardware tiers
- **Workflow Presets** - Common generation scenarios

## Template Structure
```json
{
  "quality_presets": {
    "draft": {
      "backend": "wan2gp",
      "model": "hunyuan_fast",
      "description": "Fast preview generation"
    },
    "standard": {
      "backend": "wan2gp", 
      "model": "hunyuan",
      "description": "Balanced quality and speed"
    },
    "high": {
      "backend": "comfyui",
      "model": "ltxv_13B",
      "description": "High quality final shots"
    }
  }
}
```

## Default Configurations
- **Backend URLs** - localhost service endpoints
- **Model Mappings** - Hardware-appropriate model selection
- **Generation Parameters** - Optimized settings for different scenarios
- **User Preferences** - Default UI and behavior settings

## Template Usage
- Loaded at **addon initialization**
- Applied based on **user selection**
- Customizable through **addon preferences**
- Validated for **compatibility**

## Reference
- [Configuration Management](../CLAUDE.md)