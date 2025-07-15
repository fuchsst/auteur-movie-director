"""
Template Validation API

Provides endpoints for validating function templates.
"""

import io
import yaml
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, Query, HTTPException
from fastapi.responses import HTMLResponse

from app.templates import (
    TemplateValidationPipeline,
    ValidationContext,
    ValidationResultFormatter,
    OutputFormat,
    TemplateRegistry
)
from app.schemas.templates import ValidationResponse, BatchValidationResponse
from app.core.dependencies import get_template_registry


router = APIRouter(prefix="/templates", tags=["template-validation"])

# Global validation pipeline instance
validation_pipeline = TemplateValidationPipeline()
formatter = ValidationResultFormatter()


@router.post("/validate", response_model=ValidationResponse)
async def validate_template(
    template_file: UploadFile = File(..., description="Template YAML file to validate"),
    strict: bool = Query(False, description="Enable strict validation mode"),
    check_uniqueness: bool = Query(True, description="Check for unique ID/version"),
    check_dependencies: bool = Query(True, description="Validate template dependencies"),
    format: OutputFormat = Query(OutputFormat.JSON, description="Output format")
) -> ValidationResponse:
    """
    Validate a single template file.
    
    The validation process includes:
    - Schema validation against JSON Schema
    - Type checking for inputs/outputs
    - Resource requirement validation
    - Example validation
    - Dependency checking
    - Uniqueness verification
    
    Returns detailed validation results with errors, warnings, and suggestions.
    """
    
    # Parse template file
    try:
        content = await template_file.read()
        template_data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid YAML file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read template file: {str(e)}"
        )
    
    # Get template registry if available
    try:
        registry = get_template_registry()
    except:
        registry = None
    
    # Create validation context
    context = ValidationContext(
        strict_mode=strict,
        check_uniqueness=check_uniqueness,
        check_dependencies=check_dependencies,
        registry=registry
    )
    
    # Run validation
    try:
        result = await validation_pipeline.validate(template_data, context)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )
    
    # Format response based on requested format
    if format == OutputFormat.JSON:
        return ValidationResponse(**formatter.format_json(result))
    else:
        # For other formats, return as formatted string in response
        formatted = formatter.format(result, format)
        return ValidationResponse(
            valid=result.is_valid(),
            template_id=result.template_id,
            version=result.version,
            formatted_output=formatted,
            summary=result.get_summary()
        )


@router.post("/validate/batch", response_model=BatchValidationResponse)
async def validate_templates_batch(
    template_files: List[UploadFile] = File(..., description="Multiple template files to validate"),
    strict: bool = Query(False, description="Enable strict validation mode"),
    check_uniqueness: bool = Query(True, description="Check for unique ID/version"),
    check_dependencies: bool = Query(True, description="Validate template dependencies"),
    format: OutputFormat = Query(OutputFormat.JSON, description="Output format")
) -> BatchValidationResponse:
    """
    Validate multiple template files in batch.
    
    Processes all templates and returns individual results plus a summary.
    Useful for validating template directories or bulk updates.
    """
    
    results = {}
    
    # Get template registry if available
    try:
        registry = get_template_registry()
    except:
        registry = None
    
    # Create validation context
    context = ValidationContext(
        strict_mode=strict,
        check_uniqueness=check_uniqueness,
        check_dependencies=check_dependencies,
        registry=registry
    )
    
    # Process each file
    for template_file in template_files:
        try:
            content = await template_file.read()
            template_data = yaml.safe_load(content)
            
            result = await validation_pipeline.validate(template_data, context)
            results[template_file.filename] = result
            
        except Exception as e:
            # Create error result for failed files
            from app.templates.validation_pipeline import ValidationResult, ValidationIssue, Severity
            
            error_result = ValidationResult(
                template_id=None,
                version=None
            )
            error_result.errors.append(ValidationIssue(
                stage='loading',
                path='',
                message=f"Failed to process file: {str(e)}",
                severity=Severity.CRITICAL
            ))
            results[template_file.filename] = error_result
    
    # Format batch results
    if format == OutputFormat.JSON:
        batch_summary = formatter.format_batch_summary(results, OutputFormat.JSON)
        return BatchValidationResponse(**batch_summary)
    else:
        # For other formats, include formatted summary
        formatted_summary = formatter.format_batch_summary(results, format)
        
        # Create response with individual results
        file_results = {}
        for filename, result in results.items():
            file_results[filename] = {
                "valid": result.is_valid(),
                "template_id": result.template_id,
                "version": result.version,
                "summary": result.get_summary()
            }
        
        return BatchValidationResponse(
            summary={
                "total_files": len(results),
                "valid_files": sum(1 for r in results.values() if r.is_valid()),
                "invalid_files": sum(1 for r in results.values() if not r.is_valid()),
                "total_errors": sum(len(r.errors) for r in results.values()),
                "total_warnings": sum(len(r.warnings) for r in results.values())
            },
            results=file_results,
            formatted_summary=formatted_summary
        )


@router.post("/validate/html", response_class=HTMLResponse)
async def validate_template_html(
    template_file: UploadFile = File(..., description="Template YAML file to validate"),
    strict: bool = Query(False, description="Enable strict validation mode")
) -> HTMLResponse:
    """
    Validate a template and return results as formatted HTML.
    
    Useful for web-based validation tools or documentation generation.
    """
    
    # Parse template file
    try:
        content = await template_file.read()
        template_data = yaml.safe_load(content)
    except Exception as e:
        error_html = f"""
        <div style="color: red; padding: 20px;">
            <h2>Validation Error</h2>
            <p>Failed to parse template file: {str(e)}</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    # Get template registry if available
    try:
        registry = get_template_registry()
    except:
        registry = None
    
    # Create validation context
    context = ValidationContext(
        strict_mode=strict,
        check_uniqueness=True,
        check_dependencies=True,
        registry=registry
    )
    
    # Run validation
    try:
        result = await validation_pipeline.validate(template_data, context)
        html_content = formatter.format_html(result)
    except Exception as e:
        html_content = f"""
        <div style="color: red; padding: 20px;">
            <h2>Validation Failed</h2>
            <p>{str(e)}</p>
        </div>
        """
    
    # Wrap in complete HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Template Validation Result</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    return HTMLResponse(content=full_html)


@router.get("/validate/schema")
async def get_validation_schema():
    """
    Get the JSON Schema used for template validation.
    
    Returns the complete schema definition that templates must conform to.
    This can be used by external tools for pre-validation or IDE support.
    """
    from app.templates.validation_pipeline import SchemaValidator
    
    return {
        "schema": SchemaValidator.TEMPLATE_SCHEMA,
        "description": "JSON Schema for function template validation",
        "version": "1.0.0",
        "links": {
            "documentation": "/docs#/template-validation",
            "examples": "/templates/examples"
        }
    }


@router.get("/validate/rules")
async def get_validation_rules():
    """
    Get detailed information about all validation rules.
    
    Returns a comprehensive list of validation stages and their rules,
    including type constraints, resource limits, and best practices.
    """
    from app.templates.validation_pipeline import TypeValidator
    
    return {
        "stages": [
            {
                "name": "schema",
                "description": "Validates template structure against JSON Schema",
                "rules": [
                    "Template must have required fields: id, name, version, interface, requirements",
                    "ID must contain only lowercase letters, numbers, and underscores",
                    "Version must follow semantic versioning (e.g., 1.0.0)",
                    "Category must be one of: generation, processing, analysis, utility"
                ]
            },
            {
                "name": "types",
                "description": "Validates parameter types and constraints",
                "valid_types": list(TypeValidator.VALID_TYPES),
                "type_constraints": TypeValidator.TYPE_CONSTRAINTS,
                "rules": [
                    "All parameters must have a valid type",
                    "Constraints must be appropriate for the parameter type",
                    "Default values must match type and satisfy constraints",
                    "Enum values must be unique"
                ]
            },
            {
                "name": "resources",
                "description": "Validates resource requirements",
                "rules": [
                    "GPU templates must specify VRAM requirements",
                    "CPU cores must be at least 1",
                    "Memory requirements must be positive",
                    "Model sizes should be reasonable",
                    "Quality presets must match input enum values"
                ]
            },
            {
                "name": "examples",
                "description": "Validates template examples",
                "rules": [
                    "Examples must have unique names",
                    "Example inputs must include all required parameters",
                    "Example inputs must pass parameter validation",
                    "Unknown parameters generate warnings"
                ]
            },
            {
                "name": "dependencies",
                "description": "Validates template dependencies",
                "rules": [
                    "No circular dependencies allowed",
                    "Parent templates must exist",
                    "Model dependencies must be valid"
                ]
            },
            {
                "name": "uniqueness",
                "description": "Validates template uniqueness",
                "rules": [
                    "Template ID and version combination must be unique",
                    "Checks against template registry if available"
                ]
            }
        ]
    }