"""
Quality Preset System

Provides intuitive quality presets (draft, standard, high, ultra) that automatically
configure generation parameters across different function types.
"""

from .models import QualityPreset, QualityLevel
from .presets import QualityPresetManager, CustomPresetBuilder
from .exceptions import PresetNotFoundError, PresetIncompatibleError
from .calculation import ParameterCalculator
from .comparison import QualityComparisonService, ComparisonResult
from .recommendation import QualityRecommendationEngine, QualityRecommendation
from .impact import QualityImpactEstimator, QualityImpact
from .storage import PresetStorage

__all__ = [
    "QualityPreset",
    "QualityLevel",
    "QualityPresetManager",
    "CustomPresetBuilder",
    "ParameterCalculator",
    "QualityComparisonService",
    "ComparisonResult",
    "QualityRecommendationEngine",
    "QualityRecommendation",
    "QualityImpactEstimator",
    "QualityImpact",
    "PresetStorage",
    "PresetNotFoundError",
    "PresetIncompatibleError",
]