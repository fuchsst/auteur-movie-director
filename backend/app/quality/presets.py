"""
Quality Preset Definitions and Management

Core module for quality preset system that defines built-in presets
and manages custom user presets.
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..templates.base import FunctionTemplate
from .models import QualityPreset, QualityLevel
from .exceptions import PresetNotFoundError, PresetIncompatibleError

logger = logging.getLogger(__name__)


class QualityPresetManager:
    """Manage quality presets across all function types"""
    
    # Built-in presets
    BUILTIN_PRESETS = {
        'draft': QualityPreset(
            id='draft',
            name='Draft',
            description='Fast generation for previews and iterations',
            level=QualityLevel.DRAFT,
            time_multiplier=0.3,
            resource_multiplier=0.5,
            cost_multiplier=0.25,
            parameters={
                'image_generation': {
                    'steps': 15,
                    'cfg_scale': 7.0,
                    'sampler': 'euler',
                    'resolution_scale': 0.75
                },
                'video_generation': {
                    'fps': 12,
                    'frames': 24,
                    'resolution_scale': 0.5,
                    'motion_quality': 'low'
                },
                'audio_generation': {
                    'sample_rate': 22050,
                    'bitrate': 128,
                    'processing_quality': 'fast'
                }
            },
            resource_scaling={
                'cpu': 0.5,
                'memory': 0.6,
                'gpu_memory': 0.7
            }
        ),
        'standard': QualityPreset(
            id='standard',
            name='Standard',
            description='Balanced quality and speed for most use cases',
            level=QualityLevel.STANDARD,
            time_multiplier=1.0,
            resource_multiplier=1.0,
            cost_multiplier=1.0,
            parameters={
                'image_generation': {
                    'steps': 30,
                    'cfg_scale': 7.5,
                    'sampler': 'dpm++_2m',
                    'resolution_scale': 1.0
                },
                'video_generation': {
                    'fps': 24,
                    'frames': 48,
                    'resolution_scale': 1.0,
                    'motion_quality': 'medium'
                },
                'audio_generation': {
                    'sample_rate': 44100,
                    'bitrate': 192,
                    'processing_quality': 'balanced'
                }
            },
            resource_scaling={
                'cpu': 1.0,
                'memory': 1.0,
                'gpu_memory': 1.0
            }
        ),
        'high': QualityPreset(
            id='high',
            name='High Quality',
            description='Enhanced quality for professional use',
            level=QualityLevel.HIGH,
            time_multiplier=2.5,
            resource_multiplier=1.5,
            cost_multiplier=2.0,
            parameters={
                'image_generation': {
                    'steps': 50,
                    'cfg_scale': 8.0,
                    'sampler': 'dpm++_2m_karras',
                    'resolution_scale': 1.0,
                    'enable_hr_fix': True,
                    'hr_scale': 2.0
                },
                'video_generation': {
                    'fps': 30,
                    'frames': 90,
                    'resolution_scale': 1.0,
                    'motion_quality': 'high',
                    'interpolation': True
                },
                'audio_generation': {
                    'sample_rate': 48000,
                    'bitrate': 256,
                    'processing_quality': 'high',
                    'enable_enhancement': True
                }
            },
            resource_scaling={
                'cpu': 1.2,
                'memory': 1.5,
                'gpu_memory': 1.5
            }
        ),
        'ultra': QualityPreset(
            id='ultra',
            name='Ultra Quality',
            description='Maximum quality for final production',
            level=QualityLevel.ULTRA,
            time_multiplier=5.0,
            resource_multiplier=2.0,
            cost_multiplier=4.0,
            parameters={
                'image_generation': {
                    'steps': 100,
                    'cfg_scale': 8.5,
                    'sampler': 'dpm++_3m_sde_karras',
                    'resolution_scale': 1.0,
                    'enable_hr_fix': True,
                    'hr_scale': 2.0,
                    'hr_steps': 20,
                    'enable_refinement': True
                },
                'video_generation': {
                    'fps': 60,
                    'frames': 180,
                    'resolution_scale': 1.0,
                    'motion_quality': 'ultra',
                    'interpolation': True,
                    'temporal_coherence': True
                },
                'audio_generation': {
                    'sample_rate': 96000,
                    'bitrate': 320,
                    'processing_quality': 'ultra',
                    'enable_enhancement': True,
                    'enable_mastering': True
                }
            },
            resource_scaling={
                'cpu': 1.5,
                'memory': 2.0,
                'gpu_memory': 2.0
            }
        )
    }
    
    def __init__(self, storage=None):
        self.storage = storage
        self.presets = {**self.BUILTIN_PRESETS}
        self._custom_presets: Dict[str, QualityPreset] = {}
        
        # Lazy imports to avoid circular dependencies
        self._parameter_calculator = None
        self._compatibility_checker = None
    
    @property
    def parameter_calculator(self):
        if self._parameter_calculator is None:
            from .calculation import ParameterCalculator
            self._parameter_calculator = ParameterCalculator()
        return self._parameter_calculator
    
    @property
    def compatibility_checker(self):
        if self._compatibility_checker is None:
            from .compatibility import CompatibilityChecker
            self._compatibility_checker = CompatibilityChecker()
        return self._compatibility_checker
    
    async def apply_preset(self, 
                          preset_id: str,
                          template: FunctionTemplate,
                          base_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply quality preset to function inputs"""
        
        preset = await self.get_preset(preset_id)
        if not preset:
            raise PresetNotFoundError(f"Preset '{preset_id}' not found")
        
        # Check compatibility
        compatibility = await self.compatibility_checker.check(preset, template)
        if not compatibility.is_compatible:
            raise PresetIncompatibleError(
                f"Preset '{preset_id}' incompatible with template '{template.id}': "
                f"{compatibility.reason}"
            )
        
        # Calculate final parameters
        final_params = await self.parameter_calculator.calculate(
            preset=preset,
            template=template,
            base_inputs=base_inputs
        )
        
        # Add quality metadata
        final_params['_quality_preset'] = {
            'id': preset.id,
            'name': preset.name,
            'level': preset.level.value,
            'estimated_time': self._estimate_time(preset, template),
            'estimated_cost': self._estimate_cost(preset, template)
        }
        
        # Track usage
        await self._track_usage(preset_id)
        
        return final_params
    
    async def get_preset(self, preset_id: str) -> Optional[QualityPreset]:
        """Get preset by ID"""
        # Check built-in presets
        if preset_id in self.presets:
            return self.presets[preset_id]
        
        # Check custom presets
        if preset_id in self._custom_presets:
            return self._custom_presets[preset_id]
        
        # Try loading from storage
        if self.storage:
            preset = await self.storage.get_preset(preset_id)
            if preset:
                self._custom_presets[preset_id] = preset
                return preset
        
        return None
    
    async def list_presets(self, include_custom: bool = True, user_id: Optional[str] = None) -> List[QualityPreset]:
        """List all available presets"""
        presets = list(self.presets.values())
        
        if include_custom:
            # Add custom presets from memory
            presets.extend(self._custom_presets.values())
            
            # Load from storage if available
            if self.storage and user_id:
                stored_presets = await self.storage.get_user_presets(user_id)
                for preset in stored_presets:
                    if preset.id not in self._custom_presets:
                        self._custom_presets[preset.id] = preset
                        presets.append(preset)
        
        return sorted(presets, key=lambda p: (p.level, p.name))
    
    async def create_custom_preset(self, preset: QualityPreset, user_id: str) -> QualityPreset:
        """Create and save a custom preset"""
        if not preset.is_custom:
            preset.is_custom = True
        
        preset.created_by = user_id
        preset.created_at = datetime.now()
        preset.updated_at = datetime.now()
        
        # Apply inheritance if specified
        if preset.base_preset:
            preset = await self._apply_inheritance(preset)
        
        # Save to storage
        if self.storage:
            await self.storage.save_preset(preset, user_id)
        
        # Cache in memory
        self._custom_presets[preset.id] = preset
        
        logger.info(f"Created custom preset: {preset.id} for user {user_id}")
        return preset
    
    async def update_custom_preset(self, preset_id: str, updates: Dict[str, Any], user_id: str) -> QualityPreset:
        """Update an existing custom preset"""
        preset = await self.get_preset(preset_id)
        
        if not preset:
            raise PresetNotFoundError(f"Preset '{preset_id}' not found")
        
        if not preset.is_custom:
            raise ValueError("Cannot update built-in preset")
        
        if preset.created_by != user_id:
            raise ValueError("Cannot update preset created by another user")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(preset, key):
                setattr(preset, key, value)
        
        preset.updated_at = datetime.now()
        
        # Save to storage
        if self.storage:
            await self.storage.update_preset(preset, user_id)
        
        # Update cache
        self._custom_presets[preset_id] = preset
        
        return preset
    
    async def delete_custom_preset(self, preset_id: str, user_id: str) -> bool:
        """Delete a custom preset"""
        preset = await self.get_preset(preset_id)
        
        if not preset:
            raise PresetNotFoundError(f"Preset '{preset_id}' not found")
        
        if not preset.is_custom:
            raise ValueError("Cannot delete built-in preset")
        
        if preset.created_by != user_id:
            raise ValueError("Cannot delete preset created by another user")
        
        # Remove from storage
        if self.storage:
            await self.storage.delete_preset(preset_id, user_id)
        
        # Remove from cache
        self._custom_presets.pop(preset_id, None)
        
        return True
    
    def _estimate_time(self, preset: QualityPreset, template: FunctionTemplate) -> float:
        """Estimate execution time for preset and template"""
        base_time = template.resources.estimated_time_seconds or 60.0
        return base_time * preset.time_multiplier
    
    def _estimate_cost(self, preset: QualityPreset, template: FunctionTemplate) -> float:
        """Estimate cost for preset and template"""
        # Base cost calculation (simplified)
        base_cost = 0.01  # Base cost per execution
        resource_cost = template.resources.vram_gb * 0.001  # Cost per GB of VRAM
        return (base_cost + resource_cost) * preset.cost_multiplier
    
    async def _track_usage(self, preset_id: str):
        """Track preset usage statistics"""
        preset = await self.get_preset(preset_id)
        if preset:
            preset.usage_count += 1
            if preset.is_custom and self.storage:
                await self.storage.update_usage_stats(preset_id, preset.usage_count)
    
    async def _apply_inheritance(self, preset: QualityPreset) -> QualityPreset:
        """Apply inheritance from base preset"""
        base = await self.get_preset(preset.base_preset)
        if not base:
            logger.warning(f"Base preset '{preset.base_preset}' not found for inheritance")
            return preset
        
        # Inherit values not explicitly set
        if preset.time_multiplier == 1.0:
            preset.time_multiplier = base.time_multiplier
        if preset.resource_multiplier == 1.0:
            preset.resource_multiplier = base.resource_multiplier
        if preset.cost_multiplier == 1.0:
            preset.cost_multiplier = base.cost_multiplier
        
        # Merge parameters
        for func_type, params in base.parameters.items():
            if func_type not in preset.parameters:
                preset.parameters[func_type] = params.copy()
            else:
                # Merge with base, custom values override
                merged = params.copy()
                merged.update(preset.parameters[func_type])
                preset.parameters[func_type] = merged
        
        # Merge resource scaling
        if not preset.resource_scaling:
            preset.resource_scaling = base.resource_scaling.copy()
        else:
            merged_scaling = base.resource_scaling.copy()
            merged_scaling.update(preset.resource_scaling)
            preset.resource_scaling = merged_scaling
        
        return preset


class CustomPresetBuilder:
    """Builder for creating custom quality presets"""
    
    def __init__(self):
        self.preset = QualityPreset(
            id=f"custom_{uuid.uuid4().hex[:8]}",
            name="Custom Preset",
            description="",
            level=QualityLevel.STANDARD,
            is_custom=True
        )
    
    def with_name(self, name: str) -> 'CustomPresetBuilder':
        self.preset.name = name
        return self
    
    def with_description(self, description: str) -> 'CustomPresetBuilder':
        self.preset.description = description
        return self
    
    def with_level(self, level: QualityLevel) -> 'CustomPresetBuilder':
        self.preset.level = level
        return self
    
    def based_on(self, base_preset_id: str) -> 'CustomPresetBuilder':
        """Inherit from existing preset"""
        self.preset.base_preset = base_preset_id
        return self
    
    def with_parameters(self, 
                       function_type: str,
                       parameters: Dict[str, Any]) -> 'CustomPresetBuilder':
        """Set parameters for specific function type"""
        if function_type not in self.preset.parameters:
            self.preset.parameters[function_type] = {}
        self.preset.parameters[function_type].update(parameters)
        return self
    
    def with_time_multiplier(self, multiplier: float) -> 'CustomPresetBuilder':
        self.preset.time_multiplier = multiplier
        return self
    
    def with_resource_multiplier(self, multiplier: float) -> 'CustomPresetBuilder':
        self.preset.resource_multiplier = multiplier
        return self
    
    def with_cost_multiplier(self, multiplier: float) -> 'CustomPresetBuilder':
        self.preset.cost_multiplier = multiplier
        return self
    
    def with_resource_scaling(self, resource: str, scale: float) -> 'CustomPresetBuilder':
        self.preset.resource_scaling[resource] = scale
        return self
    
    def build(self) -> QualityPreset:
        """Build and validate the preset"""
        # Validate preset
        if not self.preset.name:
            raise ValueError("Preset must have a name")
        
        if not self.preset.description:
            self.preset.description = f"Custom {self.preset.level.name.lower()} quality preset"
        
        return self.preset