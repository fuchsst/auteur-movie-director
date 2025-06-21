# Backend Integration Layer

## Overview

The backend layer provides unified API integration with local generative services. It abstracts the complexity of multiple AI backends behind consistent Python interfaces, enabling intelligent task routing and robust error handling.

## Backend Services

### Generative Engines
- **ComfyUI** (`comfyui/`) - Complex image/video workflows with advanced compositing
- **Wan2GP** (`wan2gp/`) - Fast video generation with multiple model support  
- **LiteLLM** (`litellm/`) - Text generation for script development and prompts

### Integration Architecture

```python
# Backend client pattern
class BackendClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.client = None
        self.is_connected = False
    
    async def generate(self, prompt, config):
        """Unified generation interface"""
        pass
    
    def check_health(self):
        """Service health verification"""
        pass
```

## Task Routing Logic

### Intelligent Backend Selection
```python
def select_optimal_backend(task_type, complexity, available_resources):
    """Route tasks to most appropriate backend"""
    
    if task_type == "quick_preview":
        return wan2gp_client  # Fast generation
    elif task_type == "character_consistency":
        return comfyui_client  # Advanced workflows
    elif task_type == "text_generation":
        return litellm_client  # Language models
    
    # Fallback logic for resource constraints
    if available_resources.vram < 8:
        return wan2gp_client  # More efficient
    else:
        return comfyui_client  # Higher quality
```

### Workflow Templates
```python
# Template-based workflow management
class WorkflowTemplate:
    def __init__(self, template_path):
        self.template = load_json(template_path)
    
    def customize(self, **parameters):
        """Insert job-specific parameters"""
        workflow = self.template.copy()
        for key, value in parameters.items():
            workflow = replace_placeholder(workflow, key, value)
        return workflow
```

## API Client Implementation

### ComfyUI Integration
```python
# ComfyUI workflow execution
async def execute_comfyui_workflow(workflow_json, inputs):
    client = ComfyUIClient("http://localhost:8188")
    
    # Customize workflow with inputs
    workflow = customize_workflow(workflow_json, inputs)
    
    # Submit to ComfyUI
    result = await client.queue_prompt(workflow)
    return result
```

### Wan2GP Integration  
```python
# Wan2GP model-specific generation
async def generate_with_wan2gp(prompt, model="hunyuan"):
    client = Wan2GPClient("http://localhost:7860")
    
    # Route to appropriate model endpoint
    result = await client.generate_text_to_video(prompt, model)
    return result
```

### LiteLLM Integration
```python
# Text generation with model flexibility
async def generate_text(prompt, model="llama3"):
    client = LiteLLMClient("http://localhost:4000")
    
    # Unified API for multiple LLM providers
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```

## Error Handling & Resilience

### Connection Management
```python
class RobustBackendClient:
    def __init__(self, primary_url, fallback_url=None):
        self.primary = BackendClient(primary_url)
        self.fallback = BackendClient(fallback_url) if fallback_url else None
    
    async def generate_with_fallback(self, *args, **kwargs):
        try:
            return await self.primary.generate(*args, **kwargs)
        except ConnectionError:
            if self.fallback:
                return await self.fallback.generate(*args, **kwargs)
            raise
```

### Resource Monitoring
- **Health Checks** - Periodic service availability verification
- **Load Balancing** - Distribute tasks across available backends
- **Graceful Degradation** - Fallback to simpler models when needed

## Development Patterns

### Async Operations
```python
# Non-blocking generation for UI responsiveness
async def async_generate_shot(shot_obj):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, generate_shot, shot_obj)
    
    # Update UI on main thread
    bpy.app.timers.register(lambda: update_shot_ui(shot_obj, result))
```

### Configuration Management
- **Service URLs** stored in addon preferences
- **Model Selection** based on hardware capabilities
- **Template Paths** for workflow customization

## Reference Documentation

- [ComfyUI API Guide](/.bmad-core/data/comfyui-api-guide.md)
- [Wan2GP Integration](/.bmad-core/data/wan2gp-api-guide.md)
- [Async Patterns](/.bmad-core/data/bpy-utils-guide.md#async-operations)

The backend layer ensures reliable, efficient access to generative AI capabilities while maintaining system responsiveness.