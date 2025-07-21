# Story: STORY-099 - Quality Workflow Configuration

## Story Description
As a system administrator, I need to configure and manage the fixed mapping between quality tiers and ComfyUI workflows so that users have consistent quality options across different task types.

## Acceptance Criteria
- [ ] Fixed quality-to-workflow mapping configuration
- [ ] Workflow manifest management per quality tier
- [ ] Task type specific quality configurations
- [ ] Simple configuration file format
- [ ] Validation of workflow existence
- [ ] Easy addition of new task types
- [ ] No dynamic routing or resource analysis

## Technical Details

### Configuration File Format
```yaml
# /comfyui_workflows/config/quality_mappings.yaml
version: "1.0"
mappings:
  character_portrait:
    low:
      workflow_path: "library/image_generation/character_portrait/low_v1"
      description: "Fast character portrait generation"
      parameters:
        steps: 20
        cfg_scale: 7.0
        width: 512
        height: 512
    
    standard:
      workflow_path: "library/image_generation/character_portrait/standard_v1"
      description: "Balanced quality character portrait"
      parameters:
        steps: 30
        cfg_scale: 7.0
        width: 512
        height: 512
    
    high:
      workflow_path: "library/image_generation/character_portrait/high_v1"
      description: "High quality character portrait with details"
      parameters:
        steps: 50
        cfg_scale: 8.0
        width: 768
        height: 768

  scene_generation:
    low:
      workflow_path: "library/image_generation/scene_generation/low_v1"
      description: "Basic scene generation"
      parameters:
        steps: 25
        cfg_scale: 7.0
        width: 768
        height: 512
    
    standard:
      workflow_path: "library/image_generation/scene_generation/standard_v1"
      description: "Standard scene generation"
      parameters:
        steps: 35
        cfg_scale: 7.5
        width: 1024
        height: 576
    
    high:
      workflow_path: "library/image_generation/scene_generation/high_v1"
      description: "Detailed scene generation"
      parameters:
        steps: 60
        cfg_scale: 8.5
        width: 1280
        height: 720

  video_generation:
    low:
      workflow_path: "library/video_generation/low_v1"
      description: "Fast video generation"
      parameters:
        steps: 15
        fps: 8
        duration: 3.0
    
    standard:
      workflow_path: "library/video_generation/standard_v1"
      description: "Balanced video quality"
      parameters:
        steps: 25
        fps: 12
        duration: 5.0
    
    high:
      workflow_path: "library/video_generation/high_v1"
      description: "High quality video"
      parameters:
        steps: 40
        fps: 24
        duration: 10.0
```

### Configuration Management Service
```python
# backend/app/services/quality_config_manager.py
import yaml
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class QualityTierConfig:
    workflow_path: str
    description: str
    parameters: Dict

@dataclass
class TaskTypeConfig:
    task_type: str
    tiers: Dict[str, QualityTierConfig]

class QualityConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load quality mapping configuration"""
        if not os.path.exists(self.config_path):
            return self._create_default_config()
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _create_default_config(self) -> Dict:
        """Create default configuration if none exists"""
        default_config = {
            "version": "1.0",
            "mappings": {
                "character_portrait": {
                    "low": {
                        "workflow_path": "library/image_generation/character_portrait/low_v1",
                        "description": "Fast character portrait generation",
                        "parameters": {"steps": 20, "cfg_scale": 7.0}
                    },
                    "standard": {
                        "workflow_path": "library/image_generation/character_portrait/standard_v1",
                        "description": "Balanced quality character portrait",
                        "parameters": {"steps": 30, "cfg_scale": 7.0}
                    },
                    "high": {
                        "workflow_path": "library/image_generation/character_portrait/high_v1",
                        "description": "High quality character portrait",
                        "parameters": {"steps": 50, "cfg_scale": 8.0}
                    }
                }
            }
        }
        
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        return default_config
    
    def get_workflow_path(self, task_type: str, quality_tier: str) -> Optional[str]:
        """Get workflow path for task type and quality tier"""
        
        mappings = self.config.get("mappings", {})
        if task_type not in mappings:
            return None
        
        tiers = mappings[task_type]
        if quality_tier not in tiers:
            return None
        
        return tiers[quality_tier]["workflow_path"]
    
    def get_quality_config(self, task_type: str, quality_tier: str) -> Optional[Dict]:
        """Get full configuration for task type and quality tier"""
        
        mappings = self.config.get("mappings", {})
        if task_type not in mappings:
            return None
        
        tiers = mappings[task_type]
        return tiers.get(quality_tier)
    
    def get_available_tiers(self, task_type: str) -> List[str]:
        """Get available quality tiers for task type"""
        
        mappings = self.config.get("mappings", {})
        if task_type not in mappings:
            return []
        
        return list(mappings[task_type].keys())
    
    def get_task_types(self) -> List[str]:
        """Get all configured task types"""
        
        return list(self.config.get("mappings", {}).keys())
    
    def add_task_type(self, task_type: str, tiers: Dict[str, Dict]) -> bool:
        """Add new task type with quality tiers"""
        
        if task_type in self.config.get("mappings", {}):
            return False  # Task type already exists
        
        if "mappings" not in self.config:
            self.config["mappings"] = {}
        
        self.config["mappings"][task_type] = tiers
        self._save_config()
        return True
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
```

### Manifest Validation Service
```python
# backend/app/services/workflow_validator.py
import os
import json
from typing import List, Dict

class WorkflowValidator:
    def __init__(self, workflows_root: str):
        self.workflows_root = workflows_root
    
    def validate_workflow_path(self, workflow_path: str) -> bool:
        """Validate that workflow path exists and contains required files"""
        
        full_path = os.path.join(self.workflows_root, workflow_path)
        
        # Check if directory exists
        if not os.path.exists(full_path):
            return False
        
        # Check for required files
        workflow_file = os.path.join(full_path, "workflow_api.json")
        manifest_file = os.path.join(full_path, "manifest.yaml")
        
        return os.path.exists(workflow_file) and os.path.exists(manifest_file)
    
    def validate_all_mappings(self, config: Dict) -> List[Dict[str, str]]:
        """Validate all workflow mappings in configuration"""
        
        errors = []
        mappings = config.get("mappings", {})
        
        for task_type, tiers in mappings.items():
            for tier, config in tiers.items():
                workflow_path = config.get("workflow_path")
                if not workflow_path:
                    errors.append({
                        "task_type": task_type,
                        "tier": tier,
                        "error": "Missing workflow_path"
                    })
                    continue
                
                if not self.validate_workflow_path(workflow_path):
                    errors.append({
                        "task_type": task_type,
                        "tier": tier,
                        "error": f"Invalid workflow path: {workflow_path}"
                    })
        
        return errors
    
    def get_missing_workflows(self, config: Dict) -> List[str]:
        """Get list of missing workflow paths"""
        
        missing = []
        mappings = config.get("mappings", {})
        
        for task_type, tiers in mappings.items():
            for tier, config in tiers.items():
                workflow_path = config.get("workflow_path")
                if workflow_path and not self.validate_workflow_path(workflow_path):
                    missing.append(workflow_path)
        
        return missing
```

### Configuration API
```python
# backend/app/api/v1/quality_config.py
from fastapi import APIRouter, HTTPException
from typing import Dict, List

router = APIRouter(prefix="/api/v1/quality-config", tags=["quality-config"])

@router.get("/mappings")
async def get_all_mappings() -> Dict:
    """Get all quality tier mappings"""
    
    config_manager = QualityConfigManager("/comfyui_workflows/config/quality_mappings.yaml")
    return config_manager.config.get("mappings", {})

@router.get("/mappings/{task_type}")
async def get_task_mapping(task_type: str) -> Dict:
    """Get quality tier mappings for specific task type"""
    
    config_manager = QualityConfigManager("/comfyui_workflows/config/quality_mappings.yaml")
    
    if task_type not in config_manager.get_task_types():
        raise HTTPException(status_code=404, detail="Task type not found")
    
    return config_manager.config["mappings"][task_type]

@router.get("/tiers/{task_type}")
async def get_available_tiers(task_type: str) -> List[str]:
    """Get available quality tiers for task type"""
    
    config_manager = QualityConfigManager("/comfyui_workflows/config/quality_mappings.yaml")
    tiers = config_manager.get_available_tiers(task_type)
    
    if not tiers:
        raise HTTPException(status_code=404, detail="Task type not supported")
    
    return tiers

@router.post("/validate")
async def validate_configuration() -> Dict:
    """Validate current configuration"""
    
    config_manager = QualityConfigManager("/comfyui_workflows/config/quality_mappings.yaml")
    validator = WorkflowValidator("/comfyui_workflows")
    
    errors = validator.validate_all_mappings(config_manager.config)
    missing = validator.get_missing_workflows(config_manager.config)
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "missing_workflows": missing,
        "total_mappings": len(config_manager.get_task_types()) * 3  # 3 tiers per task
    }
```

### Simple Configuration CLI
```python
# backend/scripts/manage_quality_config.py
import argparse
import yaml
import sys
from pathlib import Path

class QualityConfigCLI:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
    
    def list_mappings(self):
        """List all quality tier mappings"""
        if not self.config_path.exists():
            print("No configuration found")
            return
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        print("Quality Tier Mappings:")
        print("=" * 50)
        
        for task_type, tiers in config.get("mappings", {}).items():
            print(f"\n{task_type}:")
            for tier, config in tiers.items():
                print(f"  {tier}: {config['workflow_path']}")
                print(f"    Description: {config['description']}")
    
    def add_mapping(self, task_type: str, tier: str, workflow_path: str, description: str):
        """Add new quality tier mapping"""
        config = {}
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        
        if "mappings" not in config:
            config["mappings"] = {}
        
        if task_type not in config["mappings"]:
            config["mappings"][task_type] = {}
        
        config["mappings"][task_type][tier] = {
            "workflow_path": workflow_path,
            "description": description,
            "parameters": {}
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print(f"Added mapping: {task_type}/{tier} -> {workflow_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage quality tier mappings")
    parser.add_argument("--config", default="/comfyui_workflows/config/quality_mappings.yaml")
    parser.add_argument("action", choices=["list", "add"])
    parser.add_argument("--task-type")
    parser.add_argument("--tier")
    parser.add_argument("--workflow-path")
    parser.add_argument("--description")
    
    args = parser.parse_args()
    
    cli = QualityConfigCLI(args.config)
    
    if args.action == "list":
        cli.list_mappings()
    elif args.action == "add":
        if not all([args.task_type, args.tier, args.workflow_path, args.description]):
            print("Missing required arguments for add action")
            sys.exit(1)
        cli.add_mapping(args.task_type, args.tier, args.workflow_path, args.description)
```

## Test Requirements
- Configuration file validation
- Workflow path existence checking
- API endpoint functionality
- Configuration management CLI
- Fixed mapping accuracy

## Definition of Done
- Configuration file format is established
- All task types have quality tier mappings
- Workflow paths are validated
- API endpoints return correct mappings
- CLI tool for configuration management works
- No dynamic routing or resource analysis present