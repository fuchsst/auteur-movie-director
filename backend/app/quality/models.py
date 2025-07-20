"""
Quality System Data Models

Defines the core data structures used throughout the quality preset system.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import IntEnum, Enum


class QualityLevel(IntEnum):
    """Quality level enumeration"""
    DRAFT = 1
    STANDARD = 2
    HIGH = 3
    ULTRA = 4


@dataclass
class QualityPreset:
    """Definition of a quality preset"""
    id: str
    name: str
    description: str
    level: QualityLevel
    is_custom: bool = False
    base_preset: Optional[str] = None  # For inheritance
    
    # Global multipliers
    time_multiplier: float = 1.0
    resource_multiplier: float = 1.0
    cost_multiplier: float = 1.0
    
    # Parameter overrides by function type
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Resource requirements scaling
    resource_scaling: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    usage_count: int = 0
    average_satisfaction: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'level': self.level.value,
            'is_custom': self.is_custom,
            'base_preset': self.base_preset,
            'time_multiplier': self.time_multiplier,
            'resource_multiplier': self.resource_multiplier,
            'cost_multiplier': self.cost_multiplier,
            'parameters': self.parameters,
            'resource_scaling': self.resource_scaling,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'usage_count': self.usage_count,
            'average_satisfaction': self.average_satisfaction,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QualityPreset':
        """Create from dictionary"""
        # Convert level back to enum
        data['level'] = QualityLevel(data['level'])
        
        # Convert datetime strings
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)


class UseCase(Enum):
    """Use case enumeration for quality recommendations"""
    PREVIEW = "preview"
    REVIEW = "review"
    FINAL = "final"
    EXPERIMENT = "experiment"
    QUICK_TEST = "quick_test"
    PRODUCTION = "production"


@dataclass
class RecommendationContext:
    """Context for quality preset recommendations"""
    use_case: Optional[UseCase] = None
    output_type: Optional[str] = None  # image, video, audio, text
    target_platform: Optional[str] = None
    time_constraint: Optional[float] = None  # seconds
    budget_constraint: Optional[float] = None  # cost units
    quality_requirement: Optional[str] = None  # minimum, balanced, maximum
    resolution: Optional[tuple] = None  # (width, height)
    duration: Optional[float] = None  # seconds
    file_size_limit: Optional[float] = None  # MB
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'use_case': self.use_case.value if self.use_case else None,
            'output_type': self.output_type,
            'target_platform': self.target_platform,
            'time_constraint': self.time_constraint,
            'budget_constraint': self.budget_constraint,
            'quality_requirement': self.quality_requirement,
            'resolution': list(self.resolution) if self.resolution else None,
            'duration': self.duration,
            'file_size_limit': self.file_size_limit
        }