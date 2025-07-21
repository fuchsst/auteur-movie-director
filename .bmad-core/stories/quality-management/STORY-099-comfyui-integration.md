# Story: STORY-100 - ComfyUI Quality Integration

## Story Description
As a backend engineer, I need to integrate the quality tier system with ComfyUI workflow execution so that user-selected quality tiers are correctly mapped to specific ComfyUI workflows with appropriate parameters.

## Acceptance Criteria
- [ ] Quality tier selection maps to ComfyUI workflow execution
- [ ] Workflow parameters populated from quality configuration
- [ ] Task execution respects quality tier settings
- [ ] Error handling for missing workflows
- [ ] Basic execution status tracking
- [ ] No resource-based routing or fallback systems
- [ ] Simple parameter injection based on quality tier

## Technical Details

### ComfyUI Quality Integration Service
```python
# backend/app/services/comfyui_quality_integration.py
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class ComfyUIQualityIntegration:
    def __init__(self, 
                 workflows_root: str,
                 quality_config_manager):
        self.workflows_root = Path(workflows_root)
        self.quality_config = quality_config_manager
    
    def prepare_workflow_execution(
        self,
        task_type: str,
        quality_tier: str,
        user_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare ComfyUI workflow execution based on quality tier"""
        
        # Get quality tier configuration
        quality_config = self.quality_config.get_quality_config(
            task_type, quality_tier
        )
        
        if not quality_config:
            raise ValueError(
                f"No configuration found for {task_type}/{quality_tier}"
            )
        
        # Load workflow API
        workflow_path = quality_config["workflow_path"]
        workflow_file = self.workflows_root / workflow_path / "workflow_api.json"
        
        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_file}")
        
        with open(workflow_file, 'r') as f:
            workflow_api = json.load(f)
        
        # Merge quality parameters with user parameters
        final_parameters = self._merge_parameters(
            quality_config["parameters"],
            user_parameters
        )
        
        # Update workflow with parameters
        updated_workflow = self._update_workflow_parameters(
            workflow_api,
            final_parameters
        )
        
        return {
            "workflow_api": updated_workflow,
            "workflow_path": str(workflow_path),
            "quality_tier": quality_tier,
            "parameters": final_parameters
        }
    
    def _merge_parameters(
        self,
        quality_params: Dict[str, Any],
        user_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge quality tier parameters with user parameters"""
        
        # Quality parameters take precedence unless explicitly overridden
        merged = quality_params.copy()
        
        # Allow user to override specific parameters
        for key, value in user_params.items():
            if key in merged:
                # Validate parameter compatibility
                if self._is_compatible(key, merged[key], value):
                    merged[key] = value
                else:
                    # Use quality tier value
                    continue
            else:
                # Add new user parameter
                merged[key] = value
        
        return merged
    
    def _is_compatible(self, key: str, quality_value: Any, user_value: Any) -> bool:
        """Check if user parameter is compatible with quality tier"""
        
        # Basic compatibility checks
        if key in ["steps", "cfg_scale"]:
            # Ensure user doesn't set values below minimum
            min_values = {"steps": 10, "cfg_scale": 1.0}
            if isinstance(user_value, (int, float)):
                return user_value >= min_values.get(key, 0)
        
        return True
    
    def _update_workflow_parameters(
        self,
        workflow_api: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update workflow API with merged parameters"""
        
        updated_workflow = workflow_api.copy()
        
        # Map common parameters to workflow nodes
        parameter_mapping = {
            "steps": ["KSampler", "steps"],
            "cfg_scale": ["KSampler", "cfg"],
            "width": ["EmptyLatentImage", "width"],
            "height": ["EmptyLatentImage", "height"],
            "positive_prompt": ["CLIPTextEncode", "text"],
            "negative_prompt": ["CLIPTextEncode", "text"],
            "seed": ["KSampler", "seed"],
            "sampler_name": ["KSampler", "sampler_name"],
            "scheduler": ["KSampler", "scheduler"]
        }
        
        for param_key, value in parameters.items():
            if param_key in parameter_mapping:
                node_type, input_key = parameter_mapping[param_key]
                
                # Find and update the appropriate node
                for node_id, node_data in updated_workflow.items():
                    if node_data.get("class_type") == node_type:
                        if "inputs" in node_data and input_key in node_data["inputs"]:
                            node_data["inputs"][input_key] = value
        
        return updated_workflow
```

### Task Execution Service
```python
# backend/app/services/quality_task_executor.py
import asyncio
from typing import Dict, Any
import uuid
from datetime import datetime

class QualityTaskExecutor:
    def __init__(self, 
                 comfyui_integration: ComfyUIQualityIntegration,
                 task_storage):
        self.integration = comfyui_integration
        self.storage = task_storage
    
    async def execute_quality_task(
        self,
        task_type: str,
        quality_tier: str,
        user_parameters: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Execute task with quality tier selection"""
        
        task_id = str(uuid.uuid4())
        
        try:
            # Prepare workflow execution
            execution_data = self.integration.prepare_workflow_execution(
                task_type, quality_tier, user_parameters
            )
            
            # Store task information
            task_record = {
                "task_id": task_id,
                "user_id": user_id,
                "task_type": task_type,
                "quality_tier": quality_tier,
                "parameters": user_parameters,
                "workflow_path": execution_data["workflow_path"],
                "status": "prepared",
                "created_at": datetime.now().isoformat()
            }
            
            self.storage.store_task(task_record)
            
            # Queue for execution (would integrate with celery)
            execution_result = await self._queue_workflow_execution(
                task_id,
                execution_data["workflow_api"],
                execution_data["workflow_path"]
            )
            
            return {
                "task_id": task_id,
                "status": "queued",
                "quality_tier": quality_tier,
                "workflow_path": execution_data["workflow_path"],
                "estimated_time": self._estimate_time(task_type, quality_tier)
            }
            
        except Exception as e:
            # Store failed task
            task_record = {
                "task_id": task_id,
                "user_id": user_id,
                "task_type": task_type,
                "quality_tier": quality_tier,
                "parameters": user_parameters,
                "status": "failed",
                "error": str(e),
                "created_at": datetime.now().isoformat()
            }
            
            self.storage.store_task(task_record)
            
            raise ValueError(f"Failed to prepare quality task: {str(e)}")
    
    async def _queue_workflow_execution(
        self,
        task_id: str,
        workflow_api: Dict[str, Any],
        workflow_path: str
    ) -> Dict[str, Any]:
        """Queue workflow for execution via celery"""
        
        # This would integrate with celery
        # For now, return mock response
        return {
            "task_id": task_id,
            "status": "queued",
            "workflow_path": workflow_path
        }
    
    def _estimate_time(self, task_type: str, quality_tier: str) -> int:
        """Estimate task execution time in seconds"""
        
        time_estimates = {
            "character_portrait": {
                "low": 30,
                "standard": 60,
                "high": 120
            },
            "scene_generation": {
                "low": 45,
                "standard": 90,
                "high": 180
            },
            "video_generation": {
                "low": 120,
                "standard": 300,
                "high": 600
            }
        }
        
        return time_estimates.get(task_type, {}).get(quality_tier, 60)
```

### API Endpoints
```python
# backend/app/api/v1/quality_execution.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/quality-execution", tags=["quality-execution"])

@router.post("/execute")
async def execute_quality_task(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Execute task with quality tier selection"""
    
    required_fields = ["task_type", "quality_tier", "user_parameters", "user_id"]
    for field in required_fields:
        if field not in request:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    try:
        executor = QualityTaskExecutor(
            comfyui_integration=ComfyUIQualityIntegration(
                workflows_root="/comfyui_workflows",
                quality_config_manager=QualityConfigManager(
                    "/comfyui_workflows/config/quality_mappings.yaml"
                )
            ),
            task_storage=TaskStorage()
        )
        
        result = await executor.execute_quality_task(
            task_type=request["task_type"],
            quality_tier=request["quality_tier"],
            user_parameters=request["user_parameters"],
            user_id=request["user_id"]
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get task execution status"""
    
    storage = TaskStorage()
    task = storage.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@router.get("/available/{task_type}")
async def get_available_quality_tiers(task_type: str) -> Dict[str, Any]:
    """Get available quality tiers for task type"""
    
    config_manager = QualityConfigManager(
        "/comfyui_workflows/config/quality_mappings.yaml"
    )
    
    tiers = config_manager.get_available_tiers(task_type)
    if not tiers:
        raise HTTPException(status_code=404, detail="Task type not supported")
    
    available_configs = {}
    for tier in tiers:
        config = config_manager.get_quality_config(task_type, tier)
        if config:
            available_configs[tier] = {
                "description": config["description"],
                "parameters": config["parameters"]
            }
    
    return {
        "task_type": task_type,
        "available_tiers": available_configs
    }
```

### Parameter Validation Service
```python
# backend/app/services/parameter_validator.py
class ParameterValidator:
    def __init__(self):
        self.validation_rules = {
            "steps": {"min": 1, "max": 100, "type": int},
            "cfg_scale": {"min": 1.0, "max": 20.0, "type": float},
            "width": {"min": 64, "max": 2048, "type": int},
            "height": {"min": 64, "max": 2048, "type": int},
            "seed": {"min": 0, "max": 2**32-1, "type": int},
            "prompt": {"type": str, "max_length": 2000},
            "negative_prompt": {"type": str, "max_length": 1000}
        }
    
    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        quality_tier: str
    ) -> Dict[str, Any]:
        """Validate and sanitize user parameters"""
        
        validated = {}
        
        for key, value in parameters.items():
            if key not in self.validation_rules:
                # Allow unknown parameters for flexibility
                validated[key] = value
                continue
            
            rule = self.validation_rules[key]
            
            try:
                # Type validation
                if rule["type"] == int:
                    value = int(value)
                elif rule["type"] == float:
                    value = float(value)
                elif rule["type"] == str:
                    value = str(value)
                
                # Range validation
                if "min" in rule:
                    value = max(rule["min"], value)
                if "max" in rule:
                    value = min(rule["max"], value)
                if "max_length" in rule and isinstance(value, str):
                    value = value[:rule["max_length"]]
                
                validated[key] = value
                
            except (ValueError, TypeError):
                # Skip invalid parameters
                continue
        
        return validated
```

### Error Handling
```python
# backend/app/services/quality_exceptions.py
class QualityTierError(Exception):
    """Base exception for quality tier errors"""
    pass

class InvalidQualityTierError(QualityTierError):
    """Invalid quality tier specified"""
    pass

class WorkflowNotFoundError(QualityTierError):
    """Specified workflow not found"""
    pass

class ParameterValidationError(QualityTierError):
    """Invalid parameters provided"""
    pass

class QualityExecutionError(QualityTierError):
    """Error during quality task execution"""
    pass
```

## Test Requirements
- Quality tier to workflow mapping accuracy
- Parameter merging correctness
- Workflow API updating functionality
- Task execution flow
- Error handling completeness
- API endpoint functionality

## Definition of Done
- Quality tiers correctly map to ComfyUI workflows
- Parameters are properly injected into workflows
- Task execution respects quality tier selection
- Error handling covers all edge cases
- API endpoints work correctly
- No resource-based routing or fallback systems present