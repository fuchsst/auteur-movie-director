# Story: STORY-096 - ComfyUI Workflow Quality Integration

## Story Description
As a backend engineer, I need to integrate ComfyUI workflows with a simple quality tier system so that each quality level has a corresponding workflow configuration with basic parameters.

## Acceptance Criteria
- [ ] ComfyUI workflow manifests include quality tier specification
- [ ] Simple manifest.yaml file per quality tier
- [ ] Quality-based workflow directory structure implemented
- [ ] Basic parameter configuration per tier
- [ ] Workflow discovery by quality tier and task type
- [ ] No resource requirements or performance metrics
- [ ] Fixed quality tier selection

## Technical Details

### Simplified ComfyUI Workflow Manifest
```yaml
# Simplified manifest.yaml for quality tiers
schema_version: "1.0"
metadata:
  name: "Character Portrait - Standard Quality"
  version: "1.0.0"
  description: "Balanced quality character portrait generation"
  
quality_tier:
  tier: "standard"
  task_type: "character_portrait"
  
parameters:
  positive_prompt:
    type: string
    required: true
    
  negative_prompt:
    type: string
    default: "low quality, blurry"
    
  steps:
    type: integer
    default: 30
    
  cfg_scale:
    type: float
    default: 7.0
```

### Quality Tier Directory Structure
```
/comfyui_workflows/
├── library/
│   ├── image_generation/
│   │   ├── character_portrait/
│   │   │   ├── high_v1/
│   │   │   │   ├── workflow_api.json
│   │   │   │   ├── manifest.yaml
│   │   │   │   └── README.md
│   │   │   ├── standard_v1/
│   │   │   │   ├── workflow_api.json
│   │   │   │   ├── manifest.yaml
│   │   │   │   └── README.md
│   │   │   └── low_v1/
│   │   │       ├── workflow_api.json
│   │   │       ├── manifest.yaml
│   │   │       └── README.md
│   │   ├── scene_generation/
│   │   │   ├── high_v1/
│   │   │   ├── standard_v1/
│   │   │   └── low_v1/
│   │   └── video_generation/
│   │       ├── high_v1/
│   │       ├── standard_v1/
│   │       └── low_v1/
```

### Manifest Validation System
```python
# backend/app/services/manifest_validator.py
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, validator

class ResourceRequirements(BaseModel):
    min_vram_mb: int
    min_ram_mb: int
    estimated_time_seconds: int
    model_size_mb: int
    
    @validator('min_vram_mb')
    def validate_vram(cls, v):
        if v < 512:
            raise ValueError("min_vram_mb must be at least 512 MB")
        return v

class QualityTierConfig(BaseModel):
    tier: str
    task_type: str

class Manifest(BaseModel):
    schema_version: str
    metadata: Dict
    quality_tier: QualityTierConfig
    resource_requirements: ResourceRequirements
    dependencies: Dict
    parameters: Dict
    
    @validator('quality_tier')
    def validate_tier(cls, v):
        valid_tiers = {"low", "standard", "high"}
        if v.tier not in valid_tiers:
            raise ValueError(f"tier must be one of {valid_tiers}")
        return v

class ManifestValidator:
    def __init__(self, comfyui_workflows_path: str):
        self.workflows_path = comfyui_workflows_path
        
    def validate_manifest(self, manifest_path: str) -> List[str]:
        """Validate manifest file and return list of errors"""
        errors = []
        
        try:
            with open(manifest_path, 'r') as f:
                data = yaml.safe_load(f)
                
            # Validate against schema
            manifest = Manifest(**data)
            
            # Validate workflow file exists
            workflow_path = manifest_path.replace('manifest.yaml', 'workflow_api.json')
            if not os.path.exists(workflow_path):
                errors.append(f"Referenced workflow file not found: {workflow_path}")
                
            # Validate dependencies
            errors.extend(self._validate_dependencies(manifest))
            
        except Exception as e:
            errors.append(str(e))
            
        return errors
```

### Workflow Discovery Service
```python
# backend/app/services/workflow_discovery.py
from typing import Dict, List, Optional
import os
import yaml
from pathlib import Path

class WorkflowDiscovery:
    def __init__(self, workflows_root: str):
        self.workflows_root = Path(workflows_root)
        
    def find_workflows_by_quality(
        self, 
        task_type: str, 
        quality_tier: str
    ) -> List[Dict]:
        """Find all workflows matching task type and quality tier"""
        search_path = self.workflows_root / task_type / f"{quality_tier}_*"
        workflows = []
        
        for manifest_path in search_path.glob("**/manifest.yaml"):
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
                
            if manifest.get('quality_tier', {}).get('tier') == quality_tier:
                workflows.append({
                    'path': str(manifest_path.parent),
                    'manifest': manifest,
                    'version': manifest['metadata']['version']
                })
                
        return sorted(workflows, key=lambda x: x['version'], reverse=True)
    
    def get_quality_tiers_for_task(self, task_type: str) -> List[str]:
        """Get all available quality tiers for a task type"""
        task_path = self.workflows_root / task_type
        if not task_path.exists():
            return []
            
        tiers = set()
        for tier_dir in task_path.glob("*"):
            if tier_dir.is_dir():
                tier = tier_dir.name.split('_')[0]
                tiers.add(tier)
                
        return sorted(tiers)
```

### Automated Manifest Generation
```python
# backend/app/services/manifest_generator.py
class ManifestGenerator:
    def __init__(self, comfyui_workflows_path: str):
        self.workflows_path = comfyui_workflows_path
        
    def generate_from_workflow(
        self, 
        workflow_api_path: str, 
        quality_tier: str,
        task_type: str
    ) -> Dict:
        """Generate manifest from ComfyUI workflow API format"""
        
        # Load workflow API JSON
        with open(workflow_api_path, 'r') as f:
            workflow = json.load(f)
        
        # Analyze resource requirements
        resource_req = self._analyze_resource_requirements(workflow)
        
        # Generate manifest structure
        manifest = {
            'schema_version': '1.0',
            'metadata': {
                'name': f"{task_type.title()} - {quality_tier.title()} Quality",
                'version': '1.0.0',
                'author': 'Auteur System',
                'description': f"{quality_tier.title()} quality {task_type.replace('_', ' ')}"
            },
            'quality_tier': {
                'tier': quality_tier,
                'task_type': task_type
            },
            'resource_requirements': resource_req,
            'dependencies': self._extract_dependencies(workflow),
            'parameters': self._extract_parameters(workflow)
        }
        
        return manifest
```

## Integration Points
- Quality Router (STORY-095) for tier-based selection
- Resource Monitor (STORY-092) for requirement validation
- Function Runner for workflow execution
- Git LFS for model storage

## Test Requirements
- Manifest validation accuracy
- Workflow discovery correctness
- Resource requirement extraction
- Dependency validation
- Version control integration

## Definition of Done
- All workflows have valid manifest.yaml files
- Quality tiers properly mapped to workflows
- Resource requirements accurately declared
- Manifest validation passes for all workflows
- Discovery service returns correct workflows