"""
API Endpoints for Function Template Management

Provides REST API for template discovery, validation, and management.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from pydantic import BaseModel
import yaml
import json
import tempfile

from app.templates import (
    TemplateRegistry, TemplateInfo, TemplateValidator,
    TemplateValidationError, TemplateNotFoundError
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


# Request/Response Models
class TemplateListResponse(BaseModel):
    """Response for template listing"""
    templates: List[TemplateInfo]
    total: int
    categories: List[str]
    tags: List[str]


class TemplateDetailResponse(BaseModel):
    """Detailed template information"""
    id: str
    name: str
    version: str
    category: str
    description: str
    author: str
    tags: List[str]
    interface: Dict[str, Any]
    requirements: Dict[str, Any]
    examples: List[Dict[str, Any]]
    openapi_schema: Dict[str, Any]


class TemplateValidationRequest(BaseModel):
    """Template validation request"""
    definition: Dict[str, Any]


class TemplateValidationResponse(BaseModel):
    """Template validation response"""
    valid: bool
    errors: List[str]
    warnings: List[str]


class InputValidationRequest(BaseModel):
    """Input validation request"""
    template_id: str
    version: Optional[str] = None
    inputs: Dict[str, Any]


class InputValidationResponse(BaseModel):
    """Input validation response"""
    valid: bool
    validated_inputs: Optional[Dict[str, Any]] = None
    errors: List[str]
    resource_requirements: Optional[Dict[str, Any]] = None


class TemplateResourceRequirements(BaseModel):
    """Resource requirements response"""
    gpu: bool
    vram_gb: float
    cpu_cores: int
    memory_gb: float
    disk_gb: float
    estimated_time_seconds: Optional[float] = None


# Initialize template registry
template_dirs = [Path(d) for d in settings.TEMPLATE_DIRECTORIES]
template_registry = TemplateRegistry(template_dirs)


@router.on_event("startup")
async def startup_event():
    """Initialize template registry on startup"""
    await template_registry.initialize()


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    template_registry.shutdown()


@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[List[str]] = Query(None, description="Filter by tags"),
    gpu_only: bool = Query(False, description="Only show GPU-requiring templates")
) -> TemplateListResponse:
    """
    List all available function templates.
    
    Optionally filter by category, tags, or GPU requirement.
    """
    try:
        # Get templates
        templates = template_registry.list_templates(category=category, tags=tag)
        
        # Apply GPU filter
        if gpu_only:
            templates = [t for t in templates if t.requires_gpu]
        
        # Get all categories and tags
        categories = template_registry.get_categories()
        all_tags = template_registry.get_all_tags()
        
        return TemplateListResponse(
            templates=templates,
            total=len(templates),
            categories=categories,
            tags=all_tags
        )
    
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=TemplateDetailResponse)
async def get_template(
    template_id: str,
    version: Optional[str] = Query(None, description="Specific version (latest if not specified)")
) -> TemplateDetailResponse:
    """
    Get detailed information about a specific template.
    
    Returns full template definition including interface, requirements, and examples.
    """
    try:
        template = template_registry.get_template(template_id, version)
        
        return TemplateDetailResponse(
            id=template.id,
            name=template.name,
            version=template.version,
            category=template.category,
            description=template.description,
            author=template.author,
            tags=template.tags,
            interface={
                "inputs": {
                    name: param.dict() for name, param in template.interface.inputs.items()
                },
                "outputs": {
                    name: param.dict() for name, param in template.interface.outputs.items()
                }
            },
            requirements={
                "resources": template.resources.dict(),
                "models": [m.dict() for m in template.models],
                "quality_presets": {
                    name: preset.dict() for name, preset in template.quality_presets.items()
                }
            },
            examples=[ex.dict() for ex in template.examples],
            openapi_schema=template.to_openapi_schema()
        )
    
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}/versions")
async def get_template_versions(template_id: str) -> Dict[str, Any]:
    """Get all available versions of a template"""
    try:
        versions = template_registry.get_template_versions(template_id)
        return {
            "template_id": template_id,
            "versions": versions,
            "latest": versions[0] if versions else None
        }
    
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting versions for {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=TemplateValidationResponse)
async def validate_template(
    request: TemplateValidationRequest
) -> TemplateValidationResponse:
    """
    Validate a template definition.
    
    Checks schema compliance and business rules.
    """
    try:
        validator = TemplateValidator()
        errors = validator.validate(request.definition)
        
        # Check for warnings (non-critical issues)
        warnings = []
        if 'template' in request.definition:
            tmpl = request.definition['template']
            if not tmpl.get('examples'):
                warnings.append("No examples provided")
            if not tmpl.get('tags'):
                warnings.append("No tags specified")
        
        return TemplateValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    except Exception as e:
        logger.error(f"Error validating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-inputs", response_model=InputValidationResponse)
async def validate_inputs(
    request: InputValidationRequest
) -> InputValidationResponse:
    """
    Validate inputs for a specific template.
    
    Returns validated inputs and calculated resource requirements.
    """
    try:
        # Get template
        template = template_registry.get_template(request.template_id, request.version)
        
        # Validate inputs
        errors = []
        validated_inputs = None
        resource_requirements = None
        
        try:
            validated_inputs = template.validate_inputs(request.inputs)
            resource_requirements = template.get_resource_requirements(validated_inputs)
        except TemplateValidationError as e:
            errors.append(str(e))
        
        return InputValidationResponse(
            valid=len(errors) == 0,
            validated_inputs=validated_inputs,
            errors=errors,
            resource_requirements=resource_requirements.dict() if resource_requirements else None
        )
    
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error validating inputs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}/resources", response_model=TemplateResourceRequirements)
async def get_resource_requirements(
    template_id: str,
    version: Optional[str] = Query(None),
    quality: str = Query("standard", description="Quality preset")
) -> TemplateResourceRequirements:
    """
    Get resource requirements for a template.
    
    Optionally specify quality level for adjusted requirements.
    """
    try:
        template = template_registry.get_template(template_id, version)
        
        # Get base requirements
        base_inputs = {"quality": quality} if quality else {}
        requirements = template.get_resource_requirements(base_inputs)
        
        return TemplateResourceRequirements(**requirements.dict())
    
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting resource requirements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_template(
    file: UploadFile = File(..., description="Template definition file (YAML/JSON)")
) -> Dict[str, Any]:
    """
    Upload and validate a new template definition.
    
    Does not register the template, only validates it.
    """
    try:
        # Read file content
        content = await file.read()
        
        # Parse based on file extension
        if file.filename.endswith('.json'):
            definition = json.loads(content)
        else:
            definition = yaml.safe_load(content)
        
        # Validate
        validator = TemplateValidator()
        errors = validator.validate(definition)
        
        if errors:
            return {
                "status": "invalid",
                "errors": errors,
                "message": "Template validation failed"
            }
        
        # Extract basic info
        tmpl = definition['template']
        return {
            "status": "valid",
            "template_id": tmpl['id'],
            "version": tmpl['version'],
            "name": tmpl['name'],
            "message": "Template is valid and can be registered"
        }
    
    except Exception as e:
        logger.error(f"Error uploading template: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{template_id}/reload")
async def reload_template(
    template_id: str,
    version: str = Query(..., description="Template version")
) -> Dict[str, str]:
    """
    Force reload a template from disk.
    
    Useful for development when templates are modified.
    """
    try:
        template_registry.reload_template(template_id, version)
        return {
            "status": "success",
            "message": f"Template {template_id}@{version} reloaded"
        }
    
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reloading template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-capability")
async def search_by_capability(
    input_type: Optional[str] = Query(None, description="Required input type"),
    output_type: Optional[str] = Query(None, description="Required output type"),
    gpu_available: bool = Query(True, description="GPU available")
) -> List[TemplateInfo]:
    """
    Search templates by capability requirements.
    
    Find templates that match specific input/output types and resource constraints.
    """
    try:
        matching_templates = []
        
        for template_info in template_registry.list_templates():
            # Get full template
            template = template_registry.get_template(template_info.id, template_info.version)
            
            # Check GPU requirement
            if template.resources.gpu and not gpu_available:
                continue
            
            # Check input type
            if input_type:
                has_input = any(
                    param.type.value == input_type 
                    for param in template.interface.inputs.values()
                )
                if not has_input:
                    continue
            
            # Check output type
            if output_type:
                has_output = any(
                    param.type.value == output_type 
                    for param in template.interface.outputs.values()
                )
                if not has_output:
                    continue
            
            matching_templates.append(template_info)
        
        return matching_templates
    
    except Exception as e:
        logger.error(f"Error searching templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))