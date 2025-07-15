"""
Function Template System

Provides a centralized registry for AI function templates with validation,
versioning, and resource requirement mapping.
"""

from .base import FunctionTemplate, FunctionInterface, InputParameter, OutputParameter, ParameterType
from .registry import TemplateRegistry, TemplateInfo
from .validation import TemplateValidator, TemplateValidationError
from .validation_pipeline import (
    TemplateValidationPipeline,
    ValidationContext,
    ValidationResult,
    ValidationIssue,
    Severity,
    SchemaValidator,
    TypeValidator,
    ResourceValidator,
    ExampleValidator,
    DependencyValidator,
    UniquenessValidator
)
from .validation_formatter import ValidationResultFormatter, OutputFormat
from .exceptions import TemplateNotFoundError, TemplateLoadError

__all__ = [
    "FunctionTemplate",
    "FunctionInterface", 
    "InputParameter",
    "OutputParameter",
    "ParameterType",
    "TemplateRegistry",
    "TemplateInfo",
    "TemplateValidator",
    "TemplateValidationError",
    "TemplateValidationPipeline",
    "ValidationContext",
    "ValidationResult",
    "ValidationIssue",
    "Severity",
    "SchemaValidator",
    "TypeValidator",
    "ResourceValidator",
    "ExampleValidator",
    "DependencyValidator",
    "UniquenessValidator",
    "ValidationResultFormatter",
    "OutputFormat",
    "TemplateNotFoundError",
    "TemplateLoadError",
]