# ComfyUI Workflow Templates

## Role
Pre-configured ComfyUI workflow JSON files for complex image/video generation tasks. Provides standardized workflows with placeholder injection for customization.

## Workflow Categories
- **Character Generation** - IPAdapter, InstantID, ReActor workflows
- **Style Application** - LoRA and style model integration
- **Video Effects** - LayerFlow, Any-to-Bokeh, advanced compositing
- **Camera Control** - 3D reprojection and complex movements

## Template Structure
```json
{
  "workflow_name": "character_consistency",
  "description": "Generate character with LoRA consistency",
  "nodes": {
    "load_lora": {
      "class_type": "LoraLoader",
      "inputs": {
        "lora_name": "{{character_lora_path}}"
      }
    }
  }
}
```

## Workflow Templates
- **character_creation.json** - Basic character generation
- **character_advanced.json** - Multi-tier character consistency
- **style_application.json** - Style LoRA application
- **layerflow_compositing.json** - Foreground/background separation
- **bokeh_enhancement.json** - Cinematic depth effects

## Parameter Injection
- **{{character_lora_path}}** - Character LoRA file path
- **{{style_lora_path}}** - Style LoRA file path
- **{{prompt}}** - Generation prompt text
- **{{seed}}** - Random seed value

## Usage Pattern
```python
def execute_workflow_template(template_name, parameters):
    template = load_workflow_template(template_name)
    workflow = inject_parameters(template, parameters)
    return comfyui_client.queue_prompt(workflow)
```

## Reference
- [ComfyUI API Guide](/.bmad-core/data/comfyui-api-guide.md)