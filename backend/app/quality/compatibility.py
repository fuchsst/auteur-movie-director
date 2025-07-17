"""
Quality Preset Compatibility Checking

Ensures that quality presets are compatible with function templates
and validates parameter compatibility.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..templates.base import FunctionTemplate
from .models import QualityPreset

logger = logging.getLogger(__name__)


@dataclass
class CompatibilityResult:
    """Result of compatibility check"""
    is_compatible: bool
    reason: Optional[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []


class CompatibilityChecker:
    """Check compatibility between presets and templates"""
    
    def __init__(self):
        self.category_mappings = {
            'image_generation': ['image', 'img2img', 'inpainting', 'upscaling'],
            'video_generation': ['video', 'animation', 'motion'],
            'audio_generation': ['audio', 'music', 'voice', 'sound']
        }
    
    async def check(self, preset: QualityPreset, template: FunctionTemplate) -> CompatibilityResult:
        """Check if preset is compatible with template"""
        
        # Check category compatibility
        category_result = self._check_category_compatibility(preset, template)
        if not category_result.is_compatible:
            return category_result
        
        # Check parameter compatibility
        param_result = self._check_parameter_compatibility(preset, template)
        if not param_result.is_compatible:
            return param_result
        
        # Check resource compatibility
        resource_result = self._check_resource_compatibility(preset, template)
        if not resource_result.is_compatible:
            return resource_result
        
        # All checks passed, merge warnings and suggestions
        return CompatibilityResult(
            is_compatible=True,
            warnings=category_result.warnings + param_result.warnings + resource_result.warnings,
            suggestions=category_result.suggestions + param_result.suggestions + resource_result.suggestions
        )
    
    def _check_category_compatibility(self, preset: QualityPreset, template: FunctionTemplate) -> CompatibilityResult:
        """Check if preset has parameters for template category"""
        
        # Find matching category
        template_category = template.category.lower()
        matched_category = None
        
        for category, aliases in self.category_mappings.items():
            if template_category in aliases or template_category == category:
                matched_category = category
                break
        
        if not matched_category:
            # Unknown category, check if preset has any matching parameters
            for param_category in preset.parameters.keys():
                if template_category in param_category or param_category in template_category:
                    matched_category = param_category
                    break
        
        if matched_category and matched_category in preset.parameters:
            return CompatibilityResult(is_compatible=True)
        
        # No matching category found
        if not preset.parameters:
            # Preset has no specific parameters, it's universal
            return CompatibilityResult(
                is_compatible=True,
                warnings=[f"Preset '{preset.name}' has no specific parameters for '{template.category}' category"]
            )
        
        return CompatibilityResult(
            is_compatible=False,
            reason=f"Preset '{preset.name}' does not support '{template.category}' category",
            suggestions=[f"Use a preset that supports {template.category} or create a custom preset"]
        )
    
    def _check_parameter_compatibility(self, preset: QualityPreset, template: FunctionTemplate) -> CompatibilityResult:
        """Check if preset parameters are compatible with template inputs"""
        
        warnings = []
        suggestions = []
        
        # Get relevant preset parameters
        template_category = self._get_template_category(template)
        preset_params = preset.parameters.get(template_category, {})
        
        if not preset_params:
            # No specific parameters for this category
            return CompatibilityResult(is_compatible=True)
        
        # Check each preset parameter
        for param_name, param_value in preset_params.items():
            # Special handling for certain parameters
            if param_name == 'resolution_scale':
                # This is a modifier, not a direct parameter
                continue
            
            # Check if template accepts this parameter
            if param_name not in template.interface.inputs:
                # Parameter not in template inputs
                if param_name in ['enable_hr_fix', 'hr_scale', 'hr_steps', 'enable_refinement']:
                    # These are optional enhancement parameters
                    warnings.append(f"Optional parameter '{param_name}' may not be supported by template")
                else:
                    warnings.append(f"Parameter '{param_name}' from preset not found in template inputs")
            else:
                # Validate parameter value against template constraints
                input_param = template.interface.inputs[param_name]
                if input_param.constraints:
                    if input_param.constraints.enum and param_value not in input_param.constraints.enum:
                        return CompatibilityResult(
                            is_compatible=False,
                            reason=f"Preset value '{param_value}' for '{param_name}' not in allowed values: {input_param.constraints.enum}"
                        )
                    
                    if input_param.constraints.min_value is not None and param_value < input_param.constraints.min_value:
                        suggestions.append(f"Preset value for '{param_name}' ({param_value}) is below minimum ({input_param.constraints.min_value})")
                    
                    if input_param.constraints.max_value is not None and param_value > input_param.constraints.max_value:
                        suggestions.append(f"Preset value for '{param_name}' ({param_value}) exceeds maximum ({input_param.constraints.max_value})")
        
        return CompatibilityResult(
            is_compatible=True,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _check_resource_compatibility(self, preset: QualityPreset, template: FunctionTemplate) -> CompatibilityResult:
        """Check if preset resource requirements are compatible with template"""
        
        warnings = []
        
        # Calculate scaled resource requirements
        scaled_vram = template.resources.vram_gb * preset.resource_multiplier
        scaled_memory = template.resources.memory_gb * preset.resource_multiplier
        
        # Check against common limits
        if scaled_vram > 24.0:  # Common GPU VRAM limit
            warnings.append(f"Preset '{preset.name}' may require {scaled_vram:.1f}GB VRAM, which exceeds common GPU limits")
        
        if scaled_memory > 64.0:  # Reasonable system memory limit
            warnings.append(f"Preset '{preset.name}' may require {scaled_memory:.1f}GB RAM, which is very high")
        
        # Check time multiplier
        if preset.time_multiplier > 10.0:
            warnings.append(f"Preset '{preset.name}' will take {preset.time_multiplier}x longer than standard")
        
        return CompatibilityResult(
            is_compatible=True,
            warnings=warnings
        )
    
    def _get_template_category(self, template: FunctionTemplate) -> str:
        """Get the category key for preset parameters"""
        template_category = template.category.lower()
        
        # Map to standard categories
        for category, aliases in self.category_mappings.items():
            if template_category in aliases or template_category == category:
                return category
        
        # Return original if no mapping found
        return template_category