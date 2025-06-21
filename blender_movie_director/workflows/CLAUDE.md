# Workflow Templates & Automation

## Overview

Pre-configured workflow templates for generative tasks. These templates standardize common operations and ensure consistent, repeatable results across different backends.

## Template Organization

### Backend-Specific Templates
- **ComfyUI** (`comfyui/`) - Complex image/video workflow JSON files
- **Wan2GP** (`wan2gp/`) - Model configuration templates
- **Character** (`character/`) - Character generation workflows
- **Style** (`style/`) - Style consistency workflows  
- **Video** (`video/`) - Video generation workflows
- **Audio** (`audio/`) - Audio generation workflows

## Template Engine

```python
class WorkflowTemplate:
    def __init__(self, template_path):
        self.template = load_json(template_path)
    
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
            return "character/basic_character.json"
        else:
            return "character/advanced_character.json"
    
    elif task_type == "video_generation":
        return "video/standard_video.json"
```

## Development Guidelines

- Store templates as **JSON files**
- Use **placeholder syntax** for customization
- Test templates with **different parameters**
- Version templates for **compatibility**

## Reference
- [ComfyUI Workflows](/.bmad-core/data/comfyui-api-guide.md)
- [Template Patterns](/.bmad-core/data/wan2gp-api-guide.md)