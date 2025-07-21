# Story: STORY-095 - Quality Tier Workflow Mapping

## Story Description
As a system architect, I need a simple quality tier system that maps user-selected quality levels to specific ComfyUI workflows so that deterministic workflow selection is achieved without complex resource analysis.

## Acceptance Criteria
- [ ] Three-tier quality system (Low/Standard/High) with fixed mappings
- [ ] Direct workflow selection based on user choice
- [ ] Simple manifest.yaml file per quality tier
- [ ] Clear directory structure for quality tiers
- [ ] No resource-based routing or fallback mechanisms
- [ ] User selection is applied directly
- [ ] Fixed quality-to-workflow mapping

## Technical Details

### Quality Tier Mapping System
```python
# backend/app/services/quality_tier_mapper.py
from typing import Dict
from dataclasses import dataclass

@dataclass
class QualityTierConfig:
    tier: str
    workflow_path: str
    description: str
    default_parameters: Dict

class QualityTierMapper:
    def __init__(self, workflows_root: str):
        self.workflows_root = workflows_root
        self.quality_mappings = self._load_quality_mappings()
    
    def get_workflow_path(
        self, 
        task_type: str, 
        quality_tier: str
    ) -> str:
        """Get workflow path for given task type and quality tier"""
        
        mapping_key = f"{task_type}_{quality_tier}"
        if mapping_key not in self.quality_mappings:
            # Default to standard quality if tier not found
            mapping_key = f"{task_type}_standard"
        
        return self.quality_mappings[mapping_key].workflow_path
    
    def get_available_tiers(self, task_type: str) -> Dict[str, str]:
        """Get available quality tiers for task type"""
        
        tiers = {}
        for key, config in self.quality_mappings.items():
            if key.startswith(f"{task_type}_"):
                tier = key.split('_')[1]
                tiers[tier] = config.description
        
        return tiers
    
    def _load_quality_mappings(self) -> Dict[str, QualityTierConfig]:
        """Load quality tier mappings from configuration"""
        
        return {
            "character_portrait_low": QualityTierConfig(
                tier="low",
                workflow_path="library/image_generation/character_portrait/low_v1",
                description="Fast generation with basic quality",
                default_parameters={"steps": 20, "cfg_scale": 7}
            ),
            "character_portrait_standard": QualityTierConfig(
                tier="standard",
                workflow_path="library/image_generation/character_portrait/standard_v1",
                description="Balanced quality and performance",
                default_parameters={"steps": 30, "cfg_scale": 7}
            ),
            "character_portrait_high": QualityTierConfig(
                tier="high",
                workflow_path="library/image_generation/character_portrait/high_v1",
                description="Maximum quality with higher detail",
                default_parameters={"steps": 50, "cfg_scale": 8}
            )
        }
```

### Simplified Manifest Structure
```yaml
# /comfyui_workflows/library/image_generation/character_portrait/high_v1/manifest.yaml
schema_version: "1.0"
metadata:
  name: "Character Portrait - High Quality"
  version: "1.0.0"
  description: "Maximum quality character portrait generation"
  
quality_tier:
  tier: "high"
  task_type: "character_portrait"
  
parameters:
  steps:
    type: integer
    default: 50
    min: 30
    max: 100
  
  cfg_scale:
    type: float
    default: 8.0
    min: 5.0
    max: 15.0
  
  positive_prompt:
    type: string
    required: true
  
  negative_prompt:
    type: string
    default: "low quality, blurry, distorted"
```

### Quality Selection API
```python
# backend/app/api/v1/quality.py
from fastapi import APIRouter, HTTPException
from typing import Dict, List

router = APIRouter(prefix="/api/v1/quality", tags=["quality"])

@router.get("/tiers/{task_type}")
async def get_quality_tiers(task_type: str):
    """Get available quality tiers for task type"""
    
    mapper = QualityTierMapper("/comfyui_workflows")
    tiers = mapper.get_available_tiers(task_type)
    
    if not tiers:
        raise HTTPException(
            status_code=404, 
            detail=f"No quality tiers found for task type: {task_type}"
        )
    
    return {
        "task_type": task_type,
        "available_tiers": tiers,
        "default_tier": "standard"
    }

@router.post("/select-workflow")
async def select_quality_workflow(request: Dict):
    """Select workflow based on quality tier"""
    
    task_type = request.get("task_type")
    quality_tier = request.get("quality_tier", "standard")
    
    mapper = QualityTierMapper("/comfyui_workflows")
    workflow_path = mapper.get_workflow_path(task_type, quality_tier)
    
    return {
        "task_type": task_type,
        "selected_tier": quality_tier,
        "workflow_path": workflow_path,
        "status": "selected"
    }
```

### Quality Tier Directory Structure
```
/comfyui_workflows/
├── library/
│   ├── image_generation/
│   │   ├── character_portrait/
│   │   │   ├── low_v1/
│   │   │   │   ├── workflow_api.json
│   │   │   │   ├── manifest.yaml
│   │   │   │   └── README.md
│   │   │   ├── standard_v1/
│   │   │   │   ├── workflow_api.json
│   │   │   │   ├── manifest.yaml
│   │   │   │   └── README.md
│   │   │   └── high_v1/
│   │   │       ├── workflow_api.json
│   │   │       ├── manifest.yaml
│   │   │       └── README.md
│   │   ├── scene_generation/
│   │   │   ├── low_v1/
│   │   │   ├── standard_v1/
│   │   │   └── high_v1/
│   │   └── video_generation/
│   │       ├── low_v1/
│   │       ├── standard_v1/
│   │       └── high_v1/
```

## Test Requirements
- Quality tier mapping accuracy
- Workflow path resolution
- API endpoint functionality
- Manifest validation
- Directory structure validation

## Definition of Done
- Quality tiers map directly to workflows
- User selection is applied without modification
- All quality tiers have valid workflows
- API endpoints return correct mappings
- Directory structure follows specification
- Unit tests validate all mappings