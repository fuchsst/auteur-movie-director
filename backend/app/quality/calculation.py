"""
Parameter Calculation System

Calculates final parameters based on quality presets and template requirements.
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from ..templates.base import FunctionTemplate
from .models import QualityPreset, QualityLevel

logger = logging.getLogger(__name__)


class BaseCalculator(ABC):
    """Base class for parameter calculators"""
    
    @abstractmethod
    async def calculate(self, 
                       params: Dict[str, Any],
                       preset: QualityPreset,
                       template: FunctionTemplate) -> Dict[str, Any]:
        """Calculate parameters for specific function type"""
        pass


class ImageParameterCalculator(BaseCalculator):
    """Calculate image generation parameters"""
    
    async def calculate(self,
                       params: Dict[str, Any],
                       preset: QualityPreset,
                       template: FunctionTemplate) -> Dict[str, Any]:
        """Apply image-specific calculations"""
        
        # Adjust sampler based on quality
        if preset.level >= QualityLevel.HIGH and params.get('sampler') == 'euler':
            # Upgrade to better sampler for high quality
            params['sampler'] = 'dpm++_2m_karras'
        
        # Enable advanced features for high/ultra
        if preset.level >= QualityLevel.HIGH:
            params['enable_attention_slicing'] = False  # Better quality
            params['enable_vae_slicing'] = False
            
            # Add upscaling for ultra quality
            if preset.level == QualityLevel.ULTRA and 'enable_hr_fix' not in params:
                params['enable_hr_fix'] = True
                params['hr_scale'] = 2.0
                params['hr_steps'] = 20
        
        # Adjust CFG scale based on resolution
        if params.get('width', 512) > 1024:
            params['cfg_scale'] = params.get('cfg_scale', 7.5) + 0.5
        
        # Apply resolution scaling
        if 'resolution_scale' in preset.parameters.get('image_generation', {}):
            scale = preset.parameters['image_generation']['resolution_scale']
            if scale != 1.0:
                params['width'] = int(params.get('width', 512) * scale)
                params['height'] = int(params.get('height', 512) * scale)
        
        # Ensure minimum quality for production
        if preset.level >= QualityLevel.HIGH:
            if params.get('steps', 0) < 30:
                params['steps'] = 30
        
        return params


class VideoParameterCalculator(BaseCalculator):
    """Calculate video generation parameters"""
    
    async def calculate(self,
                       params: Dict[str, Any],
                       preset: QualityPreset,
                       template: FunctionTemplate) -> Dict[str, Any]:
        """Apply video-specific calculations"""
        
        # Apply frame interpolation for smooth motion
        if preset.level >= QualityLevel.HIGH:
            params['interpolation'] = True
            params['interpolation_factor'] = 2
        
        # Enable temporal coherence for ultra quality
        if preset.level == QualityLevel.ULTRA:
            params['temporal_coherence'] = True
            params['motion_smoothing'] = True
        
        # Adjust keyframe interval based on quality
        if 'keyframe_interval' in params:
            if preset.level == QualityLevel.DRAFT:
                params['keyframe_interval'] = min(params['keyframe_interval'] * 2, 60)
            elif preset.level == QualityLevel.ULTRA:
                params['keyframe_interval'] = max(params['keyframe_interval'] // 2, 1)
        
        # Apply resolution scaling
        if 'resolution_scale' in preset.parameters.get('video_generation', {}):
            scale = preset.parameters['video_generation']['resolution_scale']
            if scale != 1.0:
                params['width'] = int(params.get('width', 1280) * scale)
                params['height'] = int(params.get('height', 720) * scale)
        
        # Ensure minimum FPS for quality levels
        min_fps = {
            QualityLevel.DRAFT: 12,
            QualityLevel.STANDARD: 24,
            QualityLevel.HIGH: 30,
            QualityLevel.ULTRA: 60
        }
        
        if params.get('fps', 24) < min_fps.get(preset.level, 24):
            params['fps'] = min_fps[preset.level]
        
        return params


class AudioParameterCalculator(BaseCalculator):
    """Calculate audio generation parameters"""
    
    async def calculate(self,
                       params: Dict[str, Any],
                       preset: QualityPreset,
                       template: FunctionTemplate) -> Dict[str, Any]:
        """Apply audio-specific calculations"""
        
        # Enable audio enhancement for high quality
        if preset.level >= QualityLevel.HIGH:
            params['enable_enhancement'] = True
            params['noise_reduction'] = True
        
        # Enable mastering for ultra quality
        if preset.level == QualityLevel.ULTRA:
            params['enable_mastering'] = True
            params['normalize'] = True
            params['eq_preset'] = 'professional'
        
        # Adjust processing based on content type
        if params.get('content_type') == 'voice':
            if preset.level >= QualityLevel.HIGH:
                params['voice_enhancement'] = True
                params['de_essing'] = True
        elif params.get('content_type') == 'music':
            if preset.level >= QualityLevel.HIGH:
                params['stereo_width'] = 1.2
                params['harmonic_enhancement'] = True
        
        # Ensure minimum quality settings
        min_sample_rate = {
            QualityLevel.DRAFT: 22050,
            QualityLevel.STANDARD: 44100,
            QualityLevel.HIGH: 48000,
            QualityLevel.ULTRA: 96000
        }
        
        if params.get('sample_rate', 44100) < min_sample_rate.get(preset.level, 44100):
            params['sample_rate'] = min_sample_rate[preset.level]
        
        return params


class TextParameterCalculator(BaseCalculator):
    """Calculate text generation parameters"""
    
    async def calculate(self,
                       params: Dict[str, Any],
                       preset: QualityPreset,
                       template: FunctionTemplate) -> Dict[str, Any]:
        """Apply text-specific calculations"""
        
        # Adjust model parameters based on quality
        quality_settings = {
            QualityLevel.DRAFT: {
                'temperature': 0.8,
                'top_p': 0.9,
                'max_tokens': 512,
                'repetition_penalty': 1.1
            },
            QualityLevel.STANDARD: {
                'temperature': 0.7,
                'top_p': 0.92,
                'max_tokens': 1024,
                'repetition_penalty': 1.15
            },
            QualityLevel.HIGH: {
                'temperature': 0.6,
                'top_p': 0.95,
                'max_tokens': 2048,
                'repetition_penalty': 1.2,
                'beam_search': True,
                'num_beams': 3
            },
            QualityLevel.ULTRA: {
                'temperature': 0.5,
                'top_p': 0.98,
                'max_tokens': 4096,
                'repetition_penalty': 1.25,
                'beam_search': True,
                'num_beams': 5,
                'early_stopping': True
            }
        }
        
        # Apply quality settings
        settings = quality_settings.get(preset.level, {})
        for key, value in settings.items():
            if key not in params:
                params[key] = value
        
        return params


class ParameterCalculator:
    """Calculate final parameters based on quality preset"""
    
    def __init__(self):
        self.calculators = {
            'image_generation': ImageParameterCalculator(),
            'video_generation': VideoParameterCalculator(),
            'audio_generation': AudioParameterCalculator(),
            'text_generation': TextParameterCalculator()
        }
    
    async def calculate(self,
                       preset: QualityPreset,
                       template: FunctionTemplate,
                       base_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final parameters for execution"""
        
        # Start with base inputs
        final_params = base_inputs.copy()
        
        # Get template category
        category = self._get_template_category(template)
        
        # Apply preset parameters
        if category in preset.parameters:
            preset_params = preset.parameters[category]
            # Only apply parameters that aren't already set by user
            for key, value in preset_params.items():
                if key not in final_params and key != 'resolution_scale':
                    final_params[key] = value
        
        # Apply calculator-specific logic
        calculator = self.calculators.get(category)
        if calculator:
            final_params = await calculator.calculate(
                final_params, preset, template
            )
        
        # Apply global scaling
        final_params = self._apply_global_scaling(
            final_params, preset, template
        )
        
        # Add quality metadata
        final_params['_quality_level'] = preset.level.value
        final_params['_quality_preset_id'] = preset.id
        
        return final_params
    
    def _get_template_category(self, template: FunctionTemplate) -> str:
        """Get the category key for calculations"""
        template_category = template.category.lower()
        
        # Map common aliases
        category_mappings = {
            'image': 'image_generation',
            'img2img': 'image_generation',
            'inpainting': 'image_generation',
            'upscaling': 'image_generation',
            'video': 'video_generation',
            'animation': 'video_generation',
            'motion': 'video_generation',
            'audio': 'audio_generation',
            'music': 'audio_generation',
            'voice': 'audio_generation',
            'sound': 'audio_generation',
            'text': 'text_generation',
            'llm': 'text_generation'
        }
        
        return category_mappings.get(template_category, template_category)
    
    def _apply_global_scaling(self,
                            params: Dict[str, Any],
                            preset: QualityPreset,
                            template: FunctionTemplate) -> Dict[str, Any]:
        """Apply global quality scaling to parameters"""
        
        # Scale iterations/steps based on time multiplier
        if 'steps' in params and preset.time_multiplier != 1.0:
            # Steps are already set by preset, don't scale again
            pass
        elif 'iterations' in params:
            params['iterations'] = int(params['iterations'] * preset.time_multiplier)
        
        # Scale batch size based on resource availability
        if 'batch_size' in params and preset.resource_multiplier < 1.0:
            # Reduce batch size for draft quality
            params['batch_size'] = max(1, int(params['batch_size'] * preset.resource_multiplier))
        
        # Add resource hints
        params['_resource_hints'] = {
            'memory_multiplier': preset.resource_multiplier,
            'time_multiplier': preset.time_multiplier,
            'priority': self._get_priority_from_level(preset.level)
        }
        
        return params
    
    def _get_priority_from_level(self, level: QualityLevel) -> str:
        """Convert quality level to execution priority"""
        priority_map = {
            QualityLevel.DRAFT: 'low',
            QualityLevel.STANDARD: 'normal',
            QualityLevel.HIGH: 'high',
            QualityLevel.ULTRA: 'critical'
        }
        return priority_map.get(level, 'normal')