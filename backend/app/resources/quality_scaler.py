"""
Quality-based resource scaling for different quality presets
"""

from typing import Dict, Optional, Any
import logging

from .models import ResourceSpec

logger = logging.getLogger(__name__)


class QualityResourceScaler:
    """Scale resources based on quality settings"""
    
    # Base resource multipliers for quality levels
    QUALITY_MULTIPLIERS = {
        'draft': {
            'cpu': 0.5,
            'memory': 0.7,
            'gpu_memory': 0.8,
            'time': 0.5,
            'priority': -1
        },
        'standard': {
            'cpu': 1.0,
            'memory': 1.0,
            'gpu_memory': 1.0,
            'time': 1.0,
            'priority': 0
        },
        'high': {
            'cpu': 1.5,
            'memory': 1.3,
            'gpu_memory': 1.2,
            'time': 2.0,
            'priority': 1
        },
        'ultra': {
            'cpu': 2.0,
            'memory': 1.5,
            'gpu_memory': 1.4,
            'time': 4.0,
            'priority': 2
        }
    }
    
    # Task-specific scaling overrides
    TASK_SPECIFIC_SCALING = {
        'image_generation': {
            'draft': {'gpu_memory': 0.6, 'time': 0.3},
            'high': {'gpu_memory': 1.5, 'time': 3.0},
            'ultra': {'gpu_memory': 2.0, 'time': 6.0}
        },
        'video_generation': {
            'draft': {'memory': 0.5, 'gpu_memory': 0.7, 'time': 0.4},
            'high': {'memory': 1.5, 'gpu_memory': 1.3, 'time': 2.5},
            'ultra': {'memory': 2.0, 'gpu_memory': 1.6, 'time': 5.0}
        },
        'audio_generation': {
            'draft': {'cpu': 0.7, 'memory': 0.8},
            'high': {'cpu': 1.3, 'memory': 1.2},
            'ultra': {'cpu': 1.5, 'memory': 1.3}
        }
    }
    
    def __init__(self, custom_multipliers: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Initialize quality scaler.
        
        Args:
            custom_multipliers: Optional custom quality multipliers
        """
        self.multipliers = self.QUALITY_MULTIPLIERS.copy()
        if custom_multipliers:
            self.multipliers.update(custom_multipliers)
    
    def scale_requirements(self, 
                          base_requirements: ResourceSpec,
                          quality: str,
                          task_type: Optional[str] = None,
                          custom_scaling: Optional[Dict[str, float]] = None) -> ResourceSpec:
        """
        Scale resource requirements based on quality.
        
        Args:
            base_requirements: Base resource requirements
            quality: Quality level (draft, standard, high, ultra)
            task_type: Optional task type for specific scaling
            custom_scaling: Optional custom scaling factors
            
        Returns:
            Scaled resource requirements
        """
        # Get base multipliers
        multipliers = self.multipliers.get(quality, self.multipliers['standard']).copy()
        
        # Apply task-specific scaling
        if task_type and task_type in self.TASK_SPECIFIC_SCALING:
            task_scaling = self.TASK_SPECIFIC_SCALING[task_type].get(quality, {})
            multipliers.update(task_scaling)
        
        # Apply custom scaling
        if custom_scaling:
            multipliers.update(custom_scaling)
        
        # Scale resources
        scaled = ResourceSpec(
            cpu_cores=max(0.1, base_requirements.cpu_cores * multipliers.get('cpu', 1.0)),
            memory_gb=max(0.1, base_requirements.memory_gb * multipliers.get('memory', 1.0)),
            gpu_count=base_requirements.gpu_count,  # Don't scale GPU count
            gpu_memory_gb=max(0.0, base_requirements.gpu_memory_gb * multipliers.get('gpu_memory', 1.0)),
            gpu_compute_capability=base_requirements.gpu_compute_capability,
            disk_gb=base_requirements.disk_gb * multipliers.get('disk', 1.0),
            network_bandwidth_mbps=base_requirements.network_bandwidth_mbps
        )
        
        # Round to reasonable precision
        scaled.cpu_cores = round(scaled.cpu_cores, 1)
        scaled.memory_gb = round(scaled.memory_gb, 1)
        scaled.gpu_memory_gb = round(scaled.gpu_memory_gb, 1)
        scaled.disk_gb = round(scaled.disk_gb, 1)
        
        logger.debug(f"Scaled requirements for {quality} quality: {base_requirements} -> {scaled}")
        
        return scaled
    
    def estimate_duration(self, 
                         base_duration: float,
                         quality: str,
                         task_type: Optional[str] = None) -> float:
        """
        Estimate task duration based on quality.
        
        Args:
            base_duration: Base duration in seconds
            quality: Quality level
            task_type: Optional task type for specific scaling
            
        Returns:
            Estimated duration in seconds
        """
        # Get time multiplier
        multipliers = self.multipliers.get(quality, self.multipliers['standard'])
        time_multiplier = multipliers.get('time', 1.0)
        
        # Apply task-specific time scaling
        if task_type and task_type in self.TASK_SPECIFIC_SCALING:
            task_scaling = self.TASK_SPECIFIC_SCALING[task_type].get(quality, {})
            time_multiplier = task_scaling.get('time', time_multiplier)
        
        estimated = base_duration * time_multiplier
        
        logger.debug(f"Estimated duration for {quality} quality: {base_duration}s -> {estimated}s")
        
        return estimated
    
    def get_priority(self, quality: str) -> int:
        """
        Get priority value for quality level.
        
        Args:
            quality: Quality level
            
        Returns:
            Priority value (higher is more priority)
        """
        multipliers = self.multipliers.get(quality, self.multipliers['standard'])
        return multipliers.get('priority', 0)
    
    def get_quality_info(self, quality: str) -> Dict[str, Any]:
        """
        Get information about a quality level.
        
        Args:
            quality: Quality level
            
        Returns:
            Quality level information
        """
        if quality not in self.multipliers:
            return {
                "valid": False,
                "error": f"Unknown quality level: {quality}"
            }
        
        multipliers = self.multipliers[quality]
        
        return {
            "valid": True,
            "quality": quality,
            "multipliers": {
                "cpu": multipliers.get('cpu', 1.0),
                "memory": multipliers.get('memory', 1.0),
                "gpu_memory": multipliers.get('gpu_memory', 1.0),
                "time": multipliers.get('time', 1.0)
            },
            "priority": multipliers.get('priority', 0),
            "description": self._get_quality_description(quality)
        }
    
    def _get_quality_description(self, quality: str) -> str:
        """Get human-readable description of quality level"""
        descriptions = {
            'draft': "Fast preview with reduced quality - CPU only, minimal resources",
            'standard': "Balanced quality and speed - Default GPU acceleration",
            'high': "Enhanced quality with longer processing - Optimized GPU usage",
            'ultra': "Maximum quality for professional output - Full GPU utilization"
        }
        return descriptions.get(quality, "Custom quality level")
    
    def recommend_quality(self,
                         available_resources: ResourceSpec,
                         required_resources: ResourceSpec,
                         preferred_quality: str = 'standard') -> str:
        """
        Recommend best quality level based on available resources.
        
        Args:
            available_resources: Available resources
            required_resources: Required resources for standard quality
            preferred_quality: Preferred quality if possible
            
        Returns:
            Recommended quality level
        """
        # Try preferred quality first
        scaled = self.scale_requirements(required_resources, preferred_quality)
        if scaled.fits_within(available_resources):
            return preferred_quality
        
        # Try each quality level from highest to lowest
        quality_order = ['ultra', 'high', 'standard', 'draft']
        
        for quality in quality_order:
            scaled = self.scale_requirements(required_resources, quality)
            if scaled.fits_within(available_resources):
                if quality != preferred_quality:
                    logger.info(f"Recommended {quality} quality instead of {preferred_quality} due to resource constraints")
                return quality
        
        # If even draft doesn't fit, return it anyway with warning
        logger.warning(f"No quality level fits within available resources, defaulting to draft")
        return 'draft'
    
    def get_all_quality_requirements(self,
                                   base_requirements: ResourceSpec,
                                   task_type: Optional[str] = None) -> Dict[str, ResourceSpec]:
        """
        Get resource requirements for all quality levels.
        
        Args:
            base_requirements: Base resource requirements
            task_type: Optional task type
            
        Returns:
            Dict mapping quality level to resource requirements
        """
        requirements = {}
        
        for quality in self.multipliers:
            requirements[quality] = self.scale_requirements(
                base_requirements,
                quality,
                task_type
            )
        
        return requirements