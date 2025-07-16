"""
Quality System Exceptions
"""


class QualityException(Exception):
    """Base exception for quality system"""
    pass


class PresetNotFoundError(QualityException):
    """Raised when a quality preset is not found"""
    pass


class PresetIncompatibleError(QualityException):
    """Raised when a preset is incompatible with a template"""
    pass


class PresetValidationError(QualityException):
    """Raised when preset validation fails"""
    pass


class ParameterCalculationError(QualityException):
    """Raised when parameter calculation fails"""
    pass