"""Template-related response schemas"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TemplateInfo(BaseModel):
    """Basic template information"""
    id: str
    name: str
    version: str
    category: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    requires_gpu: bool = False


class TemplateListResponse(BaseModel):
    """Response for template listing"""
    templates: List[TemplateInfo]
    total: int


class TemplateDetailResponse(BaseModel):
    """Detailed template information"""
    template: Dict[str, Any]
    schema: Dict[str, Any]


class ValidationIssueResponse(BaseModel):
    """Single validation issue"""
    stage: str
    path: str
    message: str
    severity: str
    suggestion: Optional[str] = None


class ValidationSummary(BaseModel):
    """Validation result summary"""
    errors: int
    warnings: int
    info: int
    critical: int


class ValidationResponse(BaseModel):
    """Template validation response"""
    valid: bool
    template_id: Optional[str] = None
    version: Optional[str] = None
    errors: List[ValidationIssueResponse] = Field(default_factory=list)
    warnings: List[ValidationIssueResponse] = Field(default_factory=list)
    info: List[ValidationIssueResponse] = Field(default_factory=list)
    stages_completed: List[str] = Field(default_factory=list)
    summary: ValidationSummary
    duration_ms: float
    cached: bool = False
    formatted_output: Optional[str] = None


class BatchValidationSummary(BaseModel):
    """Batch validation summary"""
    total_files: int
    valid_files: int
    invalid_files: int
    total_errors: int
    total_warnings: int


class FileValidationResult(BaseModel):
    """Validation result for a single file"""
    valid: bool
    template_id: Optional[str] = None
    version: Optional[str] = None
    summary: ValidationSummary


class BatchValidationResponse(BaseModel):
    """Batch template validation response"""
    summary: BatchValidationSummary
    results: Dict[str, FileValidationResult]
    formatted_summary: Optional[str] = None