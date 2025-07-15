"""
Template System Exceptions
"""

class TemplateException(Exception):
    """Base exception for template system"""
    pass


class TemplateNotFoundError(TemplateException):
    """Raised when a template cannot be found"""
    pass


class TemplateLoadError(TemplateException):
    """Raised when a template fails to load"""
    pass


class TemplateValidationError(TemplateException):
    """Raised when template validation fails"""
    pass