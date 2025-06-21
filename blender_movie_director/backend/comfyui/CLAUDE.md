# ComfyUI Backend Integration

## Role
Handles complex image/video workflows with advanced compositing capabilities. Primary backend for character generation, style application, and sophisticated video effects.

## Capabilities
- **Complex Workflows** - Multi-node compositing and effects
- **Character Consistency** - IPAdapter, InstantID, ReActor integration
- **Style Application** - LoRA and style model integration
- **Advanced Effects** - LayerFlow, Any-to-Bokeh, 3D reprojection

## Client Implementation
```python
class ComfyUIClient:
    def __init__(self, base_url="http://localhost:8188"):
        self.base_url = base_url
        self.client = None
    
    async def queue_prompt(self, workflow_json):
        """Execute ComfyUI workflow"""
        response = await self.client.post("/prompt", json=workflow_json)
        return await self.poll_result(response.json()["prompt_id"])
```

## Workflow Management
- **Template Loading** - Load workflow JSON templates
- **Parameter Injection** - Insert job-specific inputs
- **Queue Management** - Handle workflow execution
- **Result Polling** - Monitor generation progress

## Use Cases
- Character generation with LoRA consistency
- Style-consistent video generation
- Advanced compositing with multiple layers
- High-quality final shot rendering

## Reference
- [ComfyUI API Guide](/.bmad-core/data/comfyui-api-guide.md)