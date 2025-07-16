"""
Quality Recommendation Engine

Recommends quality presets based on use case and context.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .models import QualityPreset, QualityLevel

logger = logging.getLogger(__name__)


class UseCase(str, Enum):
    """Common use cases for content generation"""
    PREVIEW = "preview"
    ITERATION = "iteration"
    REVIEW = "review"
    CLIENT_PRESENTATION = "client_presentation"
    FINAL_DELIVERY = "final_delivery"
    SOCIAL_MEDIA = "social_media"
    PRINT = "print"
    BROADCAST = "broadcast"
    WEB = "web"
    MOBILE = "mobile"


@dataclass
class RecommendationContext:
    """Context for quality recommendation"""
    use_case: Optional[UseCase] = None
    output_type: Optional[str] = None  # image, video, audio, text
    target_platform: Optional[str] = None
    time_constraint: Optional[float] = None  # seconds
    budget_constraint: Optional[float] = None
    quality_requirement: Optional[str] = None  # minimum, balanced, maximum
    resolution: Optional[Tuple[int, int]] = None
    duration: Optional[float] = None  # for video/audio
    file_size_limit: Optional[float] = None  # MB
    hardware_constraints: Optional[Dict[str, Any]] = None
    previous_presets: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradeOffs:
    """Quality vs resource trade-offs"""
    time_factor: float
    cost_factor: float
    quality_gain: float
    resource_usage: float
    file_size_factor: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'time_factor': round(self.time_factor, 2),
            'cost_factor': round(self.cost_factor, 2),
            'quality_gain': round(self.quality_gain, 2),
            'resource_usage': round(self.resource_usage, 2),
            'file_size_factor': round(self.file_size_factor, 2)
        }


@dataclass
class QualityRecommendation:
    """Quality preset recommendation"""
    recommended_preset: str
    confidence: float
    reasoning: str
    trade_offs: TradeOffs
    alternatives: List[Dict[str, Any]]
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'recommended_preset': self.recommended_preset,
            'confidence': round(self.confidence, 2),
            'reasoning': self.reasoning,
            'trade_offs': self.trade_offs.to_dict(),
            'alternatives': self.alternatives,
            'warnings': self.warnings
        }


class QualityRecommendationEngine:
    """Recommend quality presets based on use case"""
    
    def __init__(self, preset_manager=None):
        self.preset_manager = preset_manager
        
        # Use case to preset mappings
        self.use_case_mappings = {
            UseCase.PREVIEW: 'draft',
            UseCase.ITERATION: 'draft',
            UseCase.REVIEW: 'standard',
            UseCase.CLIENT_PRESENTATION: 'high',
            UseCase.FINAL_DELIVERY: 'ultra',
            UseCase.SOCIAL_MEDIA: 'standard',
            UseCase.PRINT: 'ultra',
            UseCase.BROADCAST: 'high',
            UseCase.WEB: 'standard',
            UseCase.MOBILE: 'standard'
        }
        
        # Platform-specific adjustments
        self.platform_adjustments = {
            'instagram': {'max_resolution': (1080, 1080), 'preferred_quality': 'standard'},
            'twitter': {'max_resolution': (1920, 1080), 'preferred_quality': 'standard'},
            'youtube': {'max_resolution': (3840, 2160), 'preferred_quality': 'high'},
            'tiktok': {'max_resolution': (1080, 1920), 'preferred_quality': 'standard'},
            'web': {'max_resolution': (1920, 1080), 'preferred_quality': 'standard'},
            'print_a4': {'min_resolution': (2480, 3508), 'preferred_quality': 'ultra'},
            'print_poster': {'min_resolution': (4000, 6000), 'preferred_quality': 'ultra'}
        }
    
    async def recommend(self, context: RecommendationContext) -> QualityRecommendation:
        """Recommend quality preset based on context"""
        
        # Start with rule-based recommendation
        preset_id = await self._rule_based_recommendation(context)
        confidence = 0.9
        
        # Adjust based on constraints
        if context.time_constraint:
            preset_id, time_confidence = await self._adjust_for_time_constraint(
                preset_id, context.time_constraint
            )
            confidence *= time_confidence
        
        if context.budget_constraint:
            preset_id, budget_confidence = await self._adjust_for_budget_constraint(
                preset_id, context.budget_constraint
            )
            confidence *= budget_confidence
        
        if context.hardware_constraints:
            preset_id, hw_confidence = await self._adjust_for_hardware_constraints(
                preset_id, context.hardware_constraints
            )
            confidence *= hw_confidence
        
        # Get preset details
        if self.preset_manager:
            preset = await self.preset_manager.get_preset(preset_id)
        else:
            # Import here to avoid circular dependency
            from .presets import QualityPresetManager
            manager = QualityPresetManager()
            preset = await manager.get_preset(preset_id)
        if not preset:
            # Import here to avoid circular dependency
            from .presets import QualityPresetManager
            preset = QualityPresetManager.BUILTIN_PRESETS['standard']
            preset_id = 'standard'
        
        # Calculate trade-offs
        trade_offs = self._calculate_trade_offs(preset, context)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(preset, context)
        
        # Get alternatives
        alternatives = await self._get_alternatives(preset_id, context)
        
        # Generate warnings
        warnings = self._generate_warnings(preset, context)
        
        return QualityRecommendation(
            recommended_preset=preset_id,
            confidence=confidence,
            reasoning=reasoning,
            trade_offs=trade_offs,
            alternatives=alternatives,
            warnings=warnings
        )
    
    async def _rule_based_recommendation(self, context: RecommendationContext) -> str:
        """Simple rule-based recommendation"""
        
        # Use case mapping
        if context.use_case and context.use_case in self.use_case_mappings:
            return self.use_case_mappings[context.use_case]
        
        # Quality requirement mapping
        if context.quality_requirement:
            if context.quality_requirement == 'minimum':
                return 'draft'
            elif context.quality_requirement == 'maximum':
                return 'ultra'
            else:
                return 'standard'
        
        # Platform-specific recommendations
        if context.target_platform and context.target_platform in self.platform_adjustments:
            platform_config = self.platform_adjustments[context.target_platform]
            return platform_config.get('preferred_quality', 'standard')
        
        # Default to standard
        return 'standard'
    
    async def _adjust_for_time_constraint(self, 
                                        preset_id: str, 
                                        time_constraint: float) -> Tuple[str, float]:
        """Adjust recommendation based on time constraints"""
        preset = await self.preset_manager.get_preset(preset_id)
        if not preset:
            return preset_id, 1.0
        
        # Estimate time for current preset
        estimated_time = 60.0 * preset.time_multiplier  # Base 60 seconds
        
        if estimated_time > time_constraint:
            # Need faster preset
            if preset_id == 'ultra':
                return 'high', 0.9
            elif preset_id == 'high':
                return 'standard', 0.8
            elif preset_id == 'standard':
                return 'draft', 0.7
        
        return preset_id, 1.0
    
    async def _adjust_for_budget_constraint(self,
                                          preset_id: str,
                                          budget_constraint: float) -> Tuple[str, float]:
        """Adjust recommendation based on budget constraints"""
        preset = await self.preset_manager.get_preset(preset_id)
        if not preset:
            return preset_id, 1.0
        
        # Simple cost estimation
        base_cost = 0.01
        estimated_cost = base_cost * preset.cost_multiplier
        
        if estimated_cost > budget_constraint:
            # Need cheaper preset
            if preset_id == 'ultra':
                return 'high', 0.9
            elif preset_id == 'high':
                return 'standard', 0.8
            elif preset_id == 'standard':
                return 'draft', 0.7
        
        return preset_id, 1.0
    
    async def _adjust_for_hardware_constraints(self,
                                             preset_id: str,
                                             hardware_constraints: Dict[str, Any]) -> Tuple[str, float]:
        """Adjust recommendation based on hardware constraints"""
        preset = await self.preset_manager.get_preset(preset_id)
        if not preset:
            return preset_id, 1.0
        
        # Check VRAM constraint
        available_vram = hardware_constraints.get('vram_gb', float('inf'))
        required_vram = 8.0 * preset.resource_multiplier  # Base 8GB
        
        if required_vram > available_vram:
            # Need less demanding preset
            if preset_id == 'ultra' and available_vram >= 12:
                return 'high', 0.9
            elif preset_id in ['ultra', 'high'] and available_vram >= 8:
                return 'standard', 0.8
            elif available_vram < 8:
                return 'draft', 0.7
        
        return preset_id, 1.0
    
    def _calculate_trade_offs(self, preset: QualityPreset, context: RecommendationContext) -> TradeOffs:
        """Calculate quality vs time/cost trade-offs"""
        
        # Import here to avoid circular dependency
        from .presets import QualityPresetManager
        base_preset = QualityPresetManager.BUILTIN_PRESETS['standard']
        
        # Calculate quality gain based on level
        quality_gains = {
            QualityLevel.DRAFT: 0.7,
            QualityLevel.STANDARD: 1.0,
            QualityLevel.HIGH: 1.3,
            QualityLevel.ULTRA: 1.5
        }
        
        # File size estimation
        file_size_factors = {
            QualityLevel.DRAFT: 0.5,
            QualityLevel.STANDARD: 1.0,
            QualityLevel.HIGH: 1.8,
            QualityLevel.ULTRA: 3.0
        }
        
        return TradeOffs(
            time_factor=preset.time_multiplier / base_preset.time_multiplier,
            cost_factor=preset.cost_multiplier / base_preset.cost_multiplier,
            quality_gain=quality_gains.get(preset.level, 1.0),
            resource_usage=preset.resource_multiplier,
            file_size_factor=file_size_factors.get(preset.level, 1.0)
        )
    
    def _generate_reasoning(self, preset: QualityPreset, context: RecommendationContext) -> str:
        """Generate human-readable reasoning for recommendation"""
        
        reasons = []
        
        # Use case reasoning
        if context.use_case:
            use_case_reasons = {
                UseCase.PREVIEW: "Draft quality is ideal for quick previews and iterations",
                UseCase.ITERATION: "Draft quality allows rapid experimentation",
                UseCase.REVIEW: "Standard quality provides good balance for review purposes",
                UseCase.CLIENT_PRESENTATION: "High quality ensures professional presentation",
                UseCase.FINAL_DELIVERY: "Ultra quality maximizes output quality for delivery",
                UseCase.SOCIAL_MEDIA: "Standard quality is optimized for social platforms",
                UseCase.PRINT: "Ultra quality ensures maximum detail for print",
                UseCase.BROADCAST: "High quality meets broadcast standards"
            }
            if context.use_case in use_case_reasons:
                reasons.append(use_case_reasons[context.use_case])
        
        # Constraint reasoning
        if context.time_constraint:
            reasons.append(f"Selected to meet {context.time_constraint}s time constraint")
        
        if context.budget_constraint:
            reasons.append(f"Optimized for ${context.budget_constraint} budget")
        
        if context.hardware_constraints:
            vram = context.hardware_constraints.get('vram_gb')
            if vram:
                reasons.append(f"Compatible with {vram}GB VRAM availability")
        
        # Platform reasoning
        if context.target_platform:
            reasons.append(f"Optimized for {context.target_platform} platform requirements")
        
        # Quality level reasoning
        quality_descriptions = {
            QualityLevel.DRAFT: "providing fast results with acceptable quality",
            QualityLevel.STANDARD: "balancing quality and performance",
            QualityLevel.HIGH: "delivering enhanced quality for professional use",
            QualityLevel.ULTRA: "maximizing quality for final production"
        }
        
        if preset.level in quality_descriptions:
            reasons.append(f"{preset.name} quality recommended, {quality_descriptions[preset.level]}")
        
        return ". ".join(reasons) if reasons else f"Recommended {preset.name} quality for optimal results"
    
    async def _get_alternatives(self, recommended_id: str, context: RecommendationContext) -> List[Dict[str, Any]]:
        """Get alternative preset recommendations"""
        
        alternatives = []
        preset_order = ['draft', 'standard', 'high', 'ultra']
        
        for preset_id in preset_order:
            if preset_id == recommended_id:
                continue
            
            preset = await self.preset_manager.get_preset(preset_id)
            if not preset:
                continue
            
            # Calculate suitability score
            score = self._calculate_alternative_score(preset, context)
            
            # Generate reason for alternative
            if preset.level < QualityLevel.STANDARD:
                reason = "Faster option with reduced quality"
            elif preset.level > QualityLevel.HIGH:
                reason = "Higher quality at increased time/cost"
            else:
                reason = "Balanced alternative"
            
            alternatives.append({
                'preset_id': preset_id,
                'name': preset.name,
                'score': round(score, 2),
                'reason': reason,
                'time_multiplier': preset.time_multiplier,
                'cost_multiplier': preset.cost_multiplier
            })
        
        # Sort by score
        alternatives.sort(key=lambda x: x['score'], reverse=True)
        
        return alternatives[:3]  # Return top 3 alternatives
    
    def _calculate_alternative_score(self, preset: QualityPreset, context: RecommendationContext) -> float:
        """Calculate suitability score for alternative preset"""
        score = 0.5  # Base score
        
        # Adjust based on use case
        if context.use_case:
            expected_preset = self.use_case_mappings.get(context.use_case)
            if expected_preset:
                # Import here to avoid circular dependency
                from .presets import QualityPresetManager
                expected_level = QualityPresetManager.BUILTIN_PRESETS[expected_preset].level
                level_diff = abs(preset.level - expected_level)
                score -= level_diff * 0.1
        
        # Adjust based on constraints
        if context.time_constraint:
            if preset.time_multiplier * 60 <= context.time_constraint:
                score += 0.2
            else:
                score -= 0.2
        
        if context.budget_constraint:
            if preset.cost_multiplier * 0.01 <= context.budget_constraint:
                score += 0.1
            else:
                score -= 0.1
        
        return max(0, min(1, score))
    
    def _generate_warnings(self, preset: QualityPreset, context: RecommendationContext) -> List[str]:
        """Generate warnings for the recommendation"""
        warnings = []
        
        # Time warnings
        if preset.time_multiplier > 3.0:
            warnings.append(f"This preset will take {preset.time_multiplier}x longer than standard quality")
        
        # Resource warnings
        if preset.resource_multiplier > 1.5:
            warnings.append(f"Requires {preset.resource_multiplier}x more resources than standard")
        
        # Resolution warnings
        if context.resolution:
            width, height = context.resolution
            if preset.level == QualityLevel.DRAFT and (width > 1920 or height > 1080):
                warnings.append("Draft quality may produce visible artifacts at high resolutions")
            elif preset.level == QualityLevel.ULTRA and (width < 1024 and height < 1024):
                warnings.append("Ultra quality provides minimal benefit at low resolutions")
        
        # Platform warnings
        if context.target_platform:
            platform_config = self.platform_adjustments.get(context.target_platform, {})
            max_res = platform_config.get('max_resolution')
            if max_res and context.resolution:
                if context.resolution[0] > max_res[0] or context.resolution[1] > max_res[1]:
                    warnings.append(f"Output resolution exceeds {context.target_platform} limits")
        
        # File size warnings
        if context.file_size_limit:
            estimated_size = 10 * preset.resource_multiplier  # Base 10MB estimate
            if estimated_size > context.file_size_limit:
                warnings.append(f"Output may exceed {context.file_size_limit}MB file size limit")
        
        return warnings