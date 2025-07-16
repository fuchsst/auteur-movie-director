"""
Quality Preset API Endpoints

Provides REST API for quality preset management and application.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from ...quality import (
    QualityPresetManager,
    CustomPresetBuilder,
    QualityComparisonService,
    QualityRecommendationEngine,
    QualityImpactEstimator,
    PresetStorage,
    PresetNotFoundError,
    PresetIncompatibleError,
    QualityLevel,
    UseCase,
    RecommendationContext
)
from ...templates.registry import TemplateRegistry
from ...core.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality", tags=["quality"])


# Request/Response Models
class QualityPresetResponse(BaseModel):
    """Quality preset response model"""
    id: str
    name: str
    description: str
    level: int
    is_custom: bool
    base_preset: Optional[str]
    time_multiplier: float
    resource_multiplier: float
    cost_multiplier: float
    parameters: Dict[str, Dict[str, Any]]
    usage_count: int
    created_at: Optional[str]
    updated_at: Optional[str]


class CreatePresetRequest(BaseModel):
    """Create custom preset request"""
    name: str = Field(..., description="Preset name")
    description: str = Field(..., description="Preset description")
    level: int = Field(..., ge=1, le=4, description="Quality level (1-4)")
    base_preset: Optional[str] = Field(None, description="Base preset to inherit from")
    time_multiplier: float = Field(1.0, gt=0, description="Time multiplier")
    resource_multiplier: float = Field(1.0, gt=0, description="Resource multiplier")
    cost_multiplier: float = Field(1.0, gt=0, description="Cost multiplier")
    parameters: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Function-specific parameters")


class UpdatePresetRequest(BaseModel):
    """Update preset request"""
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Dict[str, Any]]] = None
    time_multiplier: Optional[float] = None
    resource_multiplier: Optional[float] = None
    cost_multiplier: Optional[float] = None


class ApplyPresetRequest(BaseModel):
    """Apply preset to inputs request"""
    template_id: str = Field(..., description="Function template ID")
    preset_id: str = Field(..., description="Quality preset ID")
    inputs: Dict[str, Any] = Field(..., description="Base inputs for the function")


class ComparisonRequest(BaseModel):
    """Quality comparison request"""
    template_id: str = Field(..., description="Function template ID")
    inputs: Dict[str, Any] = Field(..., description="Base inputs for comparison")
    presets: Optional[List[str]] = Field(None, description="Presets to compare (default: all)")
    include_analysis: bool = Field(True, description="Include detailed analysis")


class RecommendationRequest(BaseModel):
    """Quality recommendation request"""
    use_case: Optional[str] = Field(None, description="Use case (preview, review, final, etc.)")
    output_type: Optional[str] = Field(None, description="Output type (image, video, audio, text)")
    target_platform: Optional[str] = Field(None, description="Target platform")
    time_constraint: Optional[float] = Field(None, description="Time constraint in seconds")
    budget_constraint: Optional[float] = Field(None, description="Budget constraint")
    quality_requirement: Optional[str] = Field(None, description="Quality requirement (minimum, balanced, maximum)")
    resolution: Optional[List[int]] = Field(None, description="Target resolution [width, height]")
    duration: Optional[float] = Field(None, description="Duration for video/audio")
    file_size_limit: Optional[float] = Field(None, description="File size limit in MB")


class ImpactEstimateRequest(BaseModel):
    """Impact estimation request"""
    template_id: str = Field(..., description="Function template ID")
    preset_id: str = Field(..., description="Quality preset ID")
    inputs: Dict[str, Any] = Field(..., description="Function inputs")


# Dependencies
async def get_preset_manager() -> QualityPresetManager:
    """Get quality preset manager instance"""
    storage = PresetStorage()
    return QualityPresetManager(storage=storage)


async def get_template_registry() -> TemplateRegistry:
    """Get template registry instance"""
    return TemplateRegistry()


async def get_comparison_service() -> QualityComparisonService:
    """Get comparison service instance"""
    return QualityComparisonService()


async def get_recommendation_engine(
    preset_manager: QualityPresetManager = Depends(get_preset_manager)
) -> QualityRecommendationEngine:
    """Get recommendation engine instance"""
    return QualityRecommendationEngine(preset_manager)


async def get_impact_estimator() -> QualityImpactEstimator:
    """Get impact estimator instance"""
    return QualityImpactEstimator()


# Endpoints
@router.get("/presets", response_model=List[QualityPresetResponse])
async def list_presets(
    include_custom: bool = Query(True, description="Include custom presets"),
    include_shared: bool = Query(True, description="Include shared presets"),
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager)
):
    """List all available quality presets"""
    try:
        # Get user presets
        presets = await preset_manager.list_presets(
            include_custom=include_custom,
            user_id=current_user if include_custom else None
        )
        
        # Add shared presets if requested
        if include_shared and preset_manager.storage:
            shared = await preset_manager.storage.get_shared_presets()
            presets.extend(shared)
        
        # Convert to response format
        return [
            QualityPresetResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                level=p.level.value,
                is_custom=p.is_custom,
                base_preset=p.base_preset,
                time_multiplier=p.time_multiplier,
                resource_multiplier=p.resource_multiplier,
                cost_multiplier=p.cost_multiplier,
                parameters=p.parameters,
                usage_count=p.usage_count,
                created_at=p.created_at.isoformat() if p.created_at else None,
                updated_at=p.updated_at.isoformat() if p.updated_at else None
            )
            for p in presets
        ]
        
    except Exception as e:
        logger.error(f"Failed to list presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets/{preset_id}", response_model=QualityPresetResponse)
async def get_preset(
    preset_id: str,
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager)
):
    """Get a specific quality preset"""
    try:
        preset = await preset_manager.get_preset(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
        
        return QualityPresetResponse(
            id=preset.id,
            name=preset.name,
            description=preset.description,
            level=preset.level.value,
            is_custom=preset.is_custom,
            base_preset=preset.base_preset,
            time_multiplier=preset.time_multiplier,
            resource_multiplier=preset.resource_multiplier,
            cost_multiplier=preset.cost_multiplier,
            parameters=preset.parameters,
            usage_count=preset.usage_count,
            created_at=preset.created_at.isoformat() if preset.created_at else None,
            updated_at=preset.updated_at.isoformat() if preset.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presets", response_model=QualityPresetResponse)
async def create_preset(
    request: CreatePresetRequest,
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager)
):
    """Create a custom quality preset"""
    try:
        # Build preset
        builder = CustomPresetBuilder()
        builder.with_name(request.name)
        builder.with_description(request.description)
        builder.with_level(QualityLevel(request.level))
        
        if request.base_preset:
            builder.based_on(request.base_preset)
        
        builder.with_time_multiplier(request.time_multiplier)
        builder.with_resource_multiplier(request.resource_multiplier)
        builder.with_cost_multiplier(request.cost_multiplier)
        
        # Add parameters
        for func_type, params in request.parameters.items():
            builder.with_parameters(func_type, params)
        
        # Build and save
        preset = builder.build()
        saved_preset = await preset_manager.create_custom_preset(preset, current_user)
        
        return QualityPresetResponse(
            id=saved_preset.id,
            name=saved_preset.name,
            description=saved_preset.description,
            level=saved_preset.level.value,
            is_custom=saved_preset.is_custom,
            base_preset=saved_preset.base_preset,
            time_multiplier=saved_preset.time_multiplier,
            resource_multiplier=saved_preset.resource_multiplier,
            cost_multiplier=saved_preset.cost_multiplier,
            parameters=saved_preset.parameters,
            usage_count=saved_preset.usage_count,
            created_at=saved_preset.created_at.isoformat() if saved_preset.created_at else None,
            updated_at=saved_preset.updated_at.isoformat() if saved_preset.updated_at else None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/presets/{preset_id}", response_model=QualityPresetResponse)
async def update_preset(
    preset_id: str,
    request: UpdatePresetRequest,
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager)
):
    """Update a custom quality preset"""
    try:
        # Prepare updates
        updates = {}
        if request.name is not None:
            updates['name'] = request.name
        if request.description is not None:
            updates['description'] = request.description
        if request.parameters is not None:
            updates['parameters'] = request.parameters
        if request.time_multiplier is not None:
            updates['time_multiplier'] = request.time_multiplier
        if request.resource_multiplier is not None:
            updates['resource_multiplier'] = request.resource_multiplier
        if request.cost_multiplier is not None:
            updates['cost_multiplier'] = request.cost_multiplier
        
        # Update preset
        updated_preset = await preset_manager.update_custom_preset(
            preset_id, updates, current_user
        )
        
        return QualityPresetResponse(
            id=updated_preset.id,
            name=updated_preset.name,
            description=updated_preset.description,
            level=updated_preset.level.value,
            is_custom=updated_preset.is_custom,
            base_preset=updated_preset.base_preset,
            time_multiplier=updated_preset.time_multiplier,
            resource_multiplier=updated_preset.resource_multiplier,
            cost_multiplier=updated_preset.cost_multiplier,
            parameters=updated_preset.parameters,
            usage_count=updated_preset.usage_count,
            created_at=updated_preset.created_at.isoformat() if updated_preset.created_at else None,
            updated_at=updated_preset.updated_at.isoformat() if updated_preset.updated_at else None
        )
        
    except PresetNotFoundError:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/presets/{preset_id}")
async def delete_preset(
    preset_id: str,
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager)
):
    """Delete a custom quality preset"""
    try:
        success = await preset_manager.delete_custom_preset(preset_id, current_user)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete preset")
        
        return {"message": f"Preset '{preset_id}' deleted successfully"}
        
    except PresetNotFoundError:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply")
async def apply_preset(
    request: ApplyPresetRequest,
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager),
    template_registry: TemplateRegistry = Depends(get_template_registry)
):
    """Apply a quality preset to function inputs"""
    try:
        # Get template
        template = template_registry.get_template(request.template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{request.template_id}' not found")
        
        # Apply preset
        final_params = await preset_manager.apply_preset(
            request.preset_id,
            template,
            request.inputs
        )
        
        return {
            "template_id": request.template_id,
            "preset_id": request.preset_id,
            "final_parameters": final_params
        }
        
    except PresetNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PresetIncompatibleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to apply preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_quality(
    request: ComparisonRequest,
    current_user: str = Depends(get_current_user),
    comparison_service: QualityComparisonService = Depends(get_comparison_service)
):
    """Compare outputs across different quality presets"""
    try:
        result = await comparison_service.generate_comparison(
            template_id=request.template_id,
            inputs=request.inputs,
            presets=request.presets,
            include_analysis=request.include_analysis
        )
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to generate comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{comparison_id}")
async def get_comparison(
    comparison_id: str,
    current_user: str = Depends(get_current_user),
    comparison_service: QualityComparisonService = Depends(get_comparison_service)
):
    """Get a previous comparison result"""
    try:
        result = await comparison_service.get_comparison(comparison_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Comparison '{comparison_id}' not found")
        
        return result.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get comparison {comparison_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend_quality(
    request: RecommendationRequest,
    current_user: str = Depends(get_current_user),
    recommendation_engine: QualityRecommendationEngine = Depends(get_recommendation_engine)
):
    """Get quality preset recommendation based on context"""
    try:
        # Build context
        context = RecommendationContext(
            use_case=UseCase(request.use_case) if request.use_case else None,
            output_type=request.output_type,
            target_platform=request.target_platform,
            time_constraint=request.time_constraint,
            budget_constraint=request.budget_constraint,
            quality_requirement=request.quality_requirement,
            resolution=tuple(request.resolution) if request.resolution else None,
            duration=request.duration,
            file_size_limit=request.file_size_limit
        )
        
        # Get recommendation
        recommendation = await recommendation_engine.recommend(context)
        
        return recommendation.to_dict()
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate")
async def estimate_impact(
    request: ImpactEstimateRequest,
    current_user: str = Depends(get_current_user),
    preset_manager: QualityPresetManager = Depends(get_preset_manager),
    template_registry: TemplateRegistry = Depends(get_template_registry),
    impact_estimator: QualityImpactEstimator = Depends(get_impact_estimator)
):
    """Estimate the impact of quality settings"""
    try:
        # Get template and preset
        template = template_registry.get_template(request.template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{request.template_id}' not found")
        
        preset = await preset_manager.get_preset(request.preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{request.preset_id}' not found")
        
        # Estimate impact
        impact = await impact_estimator.estimate_impact(
            template=template,
            preset=preset,
            inputs=request.inputs
        )
        
        return impact.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to estimate impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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