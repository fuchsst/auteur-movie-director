"""
Function Template System

Provides a centralized registry for AI function templates with validation,
versioning, and resource requirement mapping.
"""

from .base import FunctionTemplate, FunctionInterface, InputParameter, OutputParameter, ParameterType
from .registry import TemplateRegistry, TemplateInfo
from .validation import TemplateValidator, TemplateValidationError
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
    "TemplateNotFoundError",
    "TemplateLoadError",
]