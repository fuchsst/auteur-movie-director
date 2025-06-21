# Wan2GP Configuration Templates

## Role
Configuration templates for Wan2GP video generation tasks. Provides model-specific settings and parameter optimization for different use cases.

## Template Categories
- **Model Configurations** - Settings for each Wan2GP model
- **Quality Presets** - Speed vs quality optimization
- **Camera Control** - Model-native movement parameters
- **Batch Settings** - Multi-shot generation configurations

## Template Structure
```json
{
  "template_name": "hunyuan_standard",
  "model": "hunyuan",
  "description": "Standard Hunyuan generation",
  "parameters": {
    "resolution": "1280x720",
    "fps": 24,
    "duration": 4.0,
    "guidance_scale": 7.5
  }
}
```

## Configuration Templates
- **t2v_draft.json** - Fast preview generation
- **hunyuan_standard.json** - Balanced quality/speed
- **ltxv_high_quality.json** - Maximum quality settings
- **i2v_standard.json** - Image-to-video conversion
- **camera_control.json** - Movement parameter templates

## Model-Specific Settings
- **Hunyuan Fast** - Optimized for speed
- **Hunyuan Standard** - Balanced settings
- **LTX-Video** - High quality parameters
- **Avatar Models** - Character-focused settings

## Usage Pattern
```python
def apply_wan2gp_template(template_name, custom_params=None):
    template = load_wan2gp_template(template_name)
    config = template.copy()
    
    if custom_params:
        config.update(custom_params)
    
    return wan2gp_client.generate_with_config(config)
```

## Reference
- [Wan2GP API Guide](/.bmad-core/data/wan2gp-api-guide.md)