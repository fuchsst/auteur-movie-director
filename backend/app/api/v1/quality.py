"""
Quality Management API Endpoints

Provides REST API endpoints for quality tier management and workflow mapping.
Maps user-selected quality tiers (Low/Standard/High) to fixed workflow configurations.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from ...services.quality_config_manager import QualityConfigManager, QualityTierMapper
from ...services.quality_validator import QualityValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality", tags=["quality"])


# Request/Response Models
class QualitySelectionRequest(BaseModel):
    """Quality tier selection request"""
    task_type: str = Field(..., description="Type of generation task")
    quality_tier: str = Field(..., description="Quality tier (low, standard, high)")
    user_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User-provided parameters to merge")

class QualitySelectionResponse(BaseModel):
    """Quality tier selection response"""
    task_type: str
    quality_tier: str
    workflow_path: str
    parameters: Dict[str, Any]
    description: str
    estimated_time: Optional[int] = None

class QualityTierResponse(BaseModel):
    """Available quality tier response"""
    tier: str
    description: str
    estimated_time: Optional[int] = None
    parameters_preview: Dict[str, Any]

class TaskQualityResponse(BaseModel):
    """Task quality tiers response"""
    task_type: str
    available_tiers: List[QualityTierResponse]

class ValidationReport(BaseModel):
    """Configuration validation report"""
    valid: bool
    issues: List[str]
    warnings: List[str]
    summary: Dict[str, int]


# Dependencies
def get_config_manager() -> QualityConfigManager:
    """Get quality configuration manager instance."""
    from backend.app.core.config import settings
    config_path = settings.QUALITY_CONFIG_PATH or "/comfyui_workflows/config/quality_mappings.yaml"
    return QualityConfigManager(config_path)

def get_tier_mapper(config_manager: QualityConfigManager = Depends(get_config_manager)) -> QualityTierMapper:
    """Get quality tier mapper instance."""
    return QualityTierMapper(config_manager)


# Endpoints
@router.get("/tiers/{task_type}", response_model=TaskQualityResponse)
async def get_quality_tiers(
    task_type: str,
    config_manager: QualityConfigManager = Depends(get_config_manager)
) -> TaskQualityResponse:
    """
    Get available quality tiers for a specific task type.
    
    Args:
        task_type: Type of generation task
        
    Returns:
        Available quality tiers with descriptions and parameters
    """
    available_tiers = config_manager.get_available_tiers(task_type)
    
    if not available_tiers:
        raise HTTPException(
            status_code=404,
            detail=f"Task type '{task_type}' not found or has no quality tiers"
        )
    
    tier_responses = []
    for tier in available_tiers:
        config = config_manager.get_quality_config(task_type, tier)
        if config:
            tier_responses.append(QualityTierResponse(
                tier=tier,
                description=config['description'],
                parameters_preview=config['parameters']
            ))
    
    return TaskQualityResponse(
        task_type=task_type,
        available_tiers=tier_responses
    )


@router.get("/tiers", response_model=Dict[str, List[str]])
async def get_all_quality_tiers(
    config_manager: QualityConfigManager = Depends(get_config_manager)
) -> Dict[str, List[str]]:
    """
    Get all available quality tier mappings.
    
    Returns:
        Dictionary mapping all task types to their available quality tiers
    """
    tier_mapper = QualityTierMapper(config_manager)
    return tier_mapper.get_available_mappings()


@router.post("/select", response_model=QualitySelectionResponse)
async def select_quality_tier(
    request: QualitySelectionRequest,
    tier_mapper: QualityTierMapper = Depends(get_tier_mapper)
) -> QualitySelectionResponse:
    """
    Select quality tier and get corresponding workflow configuration.
    
    Args:
        request: Quality selection request with task type and tier
        
    Returns:
        Complete workflow configuration for the selected quality tier
    """
    try:
        workflow_config = tier_mapper.map_to_workflow(
            request.task_type,
            request.quality_tier
        )
        
        # Merge user parameters with quality defaults
        final_parameters = {**workflow_config['parameters'], **request.user_parameters}
        
        return QualitySelectionResponse(
            task_type=request.task_type,
            quality_tier=request.quality_tier,
            workflow_path=workflow_config['workflow_path'],
            parameters=final_parameters,
            description=workflow_config['description']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/validate", response_model=ValidationReport)
async def validate_configuration(
    workflows_root: str = "/comfyui_workflows",
    config_path: str = "/comfyui_workflows/config/quality_mappings.yaml"
) -> ValidationReport:
    """
    Validate quality configuration and workflow mappings.
    
    Args:
        workflows_root: Root directory for ComfyUI workflows
        config_path: Path to quality mappings configuration
        
    Returns:
        Comprehensive validation report
    """
    validator = QualityValidator(workflows_root, config_path)
    report = validator.validate_all()
    
    return ValidationReport(
        valid=report['valid'],
        issues=report['issues'],
        warnings=report['warnings'],
        summary=report['summary']
    )


@router.get("/validate/{task_type}/{quality_tier}")
async def validate_specific_mapping(
    task_type: str,
    quality_tier: str,
    workflows_root: str = "/comfyui_workflows",
    config_manager: QualityConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    Validate a specific quality tier mapping.
    
    Args:
        task_type: Type of generation task
        quality_tier: Quality tier to validate
        workflows_root: Root directory for ComfyUI workflows
        
    Returns:
        Validation result for the specific mapping
    """
    # Check if mapping exists
    config = config_manager.get_quality_config(task_type, quality_tier)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Mapping not found for task '{task_type}' and tier '{quality_tier}'"
        )
    
    # Validate workflow directory
    validator = QualityValidator(workflows_root, "/comfyui_workflows/config/quality_mappings.yaml")
    workflow_path = config['workflow_path']
    validation_result = validator.validate_workflow_directory(workflow_path)
    
    return {
        "task_type": task_type,
        "quality_tier": quality_tier,
        "workflow_path": workflow_path,
        "valid": validation_result['valid'],
        "issues": validation_result['issues']
    }


@router.get("/health")
async def health_check(
    config_manager: QualityConfigManager = Depends(get_config_manager)
) -> Dict[str, str]:
    """
    Health check endpoint for quality system.
    
    Returns:
        Health status of the quality system
    """
    try:
        # Basic health check
        config = config_manager.get_all_configurations()
        if not config.get('mappings'):
            return {"status": "unhealthy", "reason": "No quality mappings configured"}
        
        return {"status": "healthy", "version": config.get('version', 'unknown')}
        
    except Exception as e:
        return {"status": "unhealthy", "reason": str(e)}


# Utility endpoints

@router.get("/descriptions")
async def get_quality_descriptions(
    config_manager: QualityConfigManager = Depends(get_config_manager)
) -> Dict[str, Dict[str, str]]:
    """
    Get descriptions for all quality tiers across all task types.
    
    Returns:
        Nested dictionary of task types to quality tier descriptions
    """
    all_config = config_manager.get_all_configurations()
    mappings = all_config.get('mappings', {})
    
    descriptions = {}
    for task_type, tiers in mappings.items():
        descriptions[task_type] = {
            tier: config['description']
            for tier, config in tiers.items()
        }
    
    return descriptions


@router.get("/parameters/{task_type}/{quality_tier}")
async def get_quality_parameters(
    task_type: str,
    quality_tier: str,
    config_manager: QualityConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """
    Get parameters for a specific quality tier.
    
    Args:
        task_type: Type of generation task
        quality_tier: Quality tier
        
    Returns:
        Parameters dictionary for the quality tier
    """
    config = config_manager.get_quality_config(task_type, quality_tier)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Parameters not found for task '{task_type}' and tier '{quality_tier}'"
        )
    
    return {
        "task_type": task_type,
        "quality_tier": quality_tier,
        "parameters": config['parameters']
    }


@router.post("/presets/{preset_id}/share")
async def share_preset(
    preset_id: str,
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager)
):
    """Share a custom preset with all users"""
    try:
        if not preset_manager.storage:
            raise HTTPException(status_code=501, detail="Sharing not available")
        
        success = await preset_manager.storage.share_preset(preset_id, current_user)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to share preset")
        
        return {"message": f"Preset '{preset_id}' shared successfully"}
        
    except PresetNotFoundError:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to share preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presets/{preset_id}/export")
async def export_preset(
    preset_id: str,
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager)
):
    """Export a preset for sharing"""
    try:
        if not preset_manager.storage:
            raise HTTPException(status_code=501, detail="Export not available")
        
        export_path = await preset_manager.storage.export_preset(preset_id, current_user)
        if not export_path:
            raise HTTPException(status_code=500, detail="Failed to export preset")
        
        # In production, this would return a download URL
        return {
            "message": f"Preset '{preset_id}' exported successfully",
            "export_path": export_path
        }
        
    except PresetNotFoundError:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    except Exception as e:
        logger.error(f"Failed to export preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presets/import")
async def import_preset(
    preset_data: Dict[str, Any] = Body(...),
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager)
):
    """Import a preset from exported data"""
    try:
        if not preset_manager.storage:
            raise HTTPException(status_code=501, detail="Import not available")
        
        imported_preset = await preset_manager.storage.import_preset(preset_data, current_user)
        
        return QualityPresetResponse(
            id=imported_preset.id,
            name=imported_preset.name,
            description=imported_preset.description,
            level=imported_preset.level.value,
            is_custom=imported_preset.is_custom,
            base_preset=imported_preset.base_preset,
            time_multiplier=imported_preset.time_multiplier,
            resource_multiplier=imported_preset.resource_multiplier,
            cost_multiplier=imported_preset.cost_multiplier,
            parameters=imported_preset.parameters,
            usage_count=imported_preset.usage_count,
            created_at=imported_preset.created_at.isoformat() if imported_preset.created_at else None,
            updated_at=imported_preset.updated_at.isoformat() if imported_preset.updated_at else None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to import preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))