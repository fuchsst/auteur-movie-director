# Wan2GP Backend Integration

## Role
Fast video generation service with multiple model support. Specialized for quick previews, efficient generation, and model-native camera control.

## Capabilities  
- **Multiple Models** - Hunyuan, LTX-Video, VACE, Phantom variants
- **Fast Generation** - Optimized for speed and efficiency
- **Model-Native Control** - Built-in camera movement parameters
- **Resource Efficient** - Lower VRAM requirements

## Client Implementation
```python
class Wan2GPClient:
    def __init__(self, base_url="http://localhost:7860"):
        self.base_url = base_url
        self.client = GradioClient(base_url)
    
    def generate_text_to_video(self, prompt, model="hunyuan"):
        """Generate video using specified model"""
        endpoint = self.model_endpoints[model]
        return self.client.predict(prompt, api_name=endpoint)
```

## Model Selection
- **hunyuan_fast** - Quick previews and rough cuts
- **hunyuan** - Standard quality generation
- **ltxv_13B_distilled** - Balanced quality/speed
- **hunyuan_i2v** - Image-to-video generation

## Use Cases
- Script preview generation
- Quick iteration and testing
- Fast camera movement application
- Resource-constrained environments

## Reference
- [Wan2GP API Guide](/.bmad-core/data/wan2gp-api-guide.md)
- [Client Core](/.bmad-core/data/wan2gp-client-core.md)