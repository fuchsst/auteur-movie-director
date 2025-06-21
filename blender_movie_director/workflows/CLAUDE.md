# Workflow Templates & Automation

## Overview

Pre-configured workflow templates for generative tasks. These templates standardize common operations and ensure consistent, repeatable results across different backends.

## Template Organization

### Backend-Specific Templates
- **ComfyUI** (`comfyui/`) - Complex image/video workflow YAML files
- **Wan2GP** (`wan2gp/`) - Model configuration YAML templates
- **Character** (`character/`) - Character generation workflows
- **Style** (`style/`) - Style consistency workflows  
- **Video** (`video/`) - Video generation workflows
- **Audio** (`audio/`) - Audio generation workflows

## Template Engine

```python
import yaml

class WorkflowTemplate:
    def __init__(self, template_path):
        with open(template_path, 'r') as file:
            self.template = yaml.safe_load(file)
    
    def customize(self, **params):
        """Insert job-specific parameters"""
        workflow = self.template.copy()
        return replace_placeholders(workflow, params)
```

## Template Selection

```python
def select_workflow_template(task_type, complexity):
    """Intelligent template selection"""
    
    if task_type == "character_generation":
        if complexity == "basic":
            return "character/basic_character.yaml"
        else:
            return "character/advanced_character.yaml"
    
    elif task_type == "video_generation":
        return "video/standard_video.yaml"
```

## YAML Template Format

```yaml
workflow_name: "Character Creation"
description: "Generate consistent character images"
version: "1.0"

nodes:
  "1":
    class_type: "CheckpointLoaderSimple"
    inputs:
      ckpt_name: "{model_name}"
      
parameter_mapping:
  model_name: "Base model for character generation"
  
requirements:
  vram_estimate: "6GB"
  processing_time: "30-60 seconds"
```

## Development Guidelines

- Store templates as **YAML files** (.yaml)
- Use **placeholder syntax** for customization
- Include **parameter mapping** documentation
- Add **requirements** and **metadata**
- Test templates with **different parameters**
- Version templates for **compatibility**

## Reference
- [ComfyUI Workflows](/.bmad-core/data/comfyui-api-guide.md)
- [Template Patterns](/.bmad-core/data/wan2gp-api-guide.md)