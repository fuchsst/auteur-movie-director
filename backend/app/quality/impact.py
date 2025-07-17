"""
Quality Impact Estimation

Estimates the impact of quality settings on execution time, resource usage,
and output quality.
"""

import hashlib
import statistics
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from ..templates.base import FunctionTemplate
from .models import QualityPreset, QualityLevel

logger = logging.getLogger(__name__)


@dataclass
class TimeEstimate:
    """Time estimation for execution"""
    min_seconds: float
    max_seconds: float
    expected_seconds: float
    confidence: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'min_seconds': round(self.min_seconds, 1),
            'max_seconds': round(self.max_seconds, 1),
            'expected_seconds': round(self.expected_seconds, 1),
            'confidence': round(self.confidence, 2)
        }


@dataclass
class ResourceEstimate:
    """Resource requirement estimation"""
    cpu_cores: int
    memory_gb: float
    vram_gb: float
    disk_gb: float
    network_mbps: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cpu_cores': self.cpu_cores,
            'memory_gb': round(self.memory_gb, 1),
            'vram_gb': round(self.vram_gb, 1),
            'disk_gb': round(self.disk_gb, 1),
            'network_mbps': round(self.network_mbps, 1)
        }


@dataclass
class QualityMetrics:
    """Expected quality metrics"""
    resolution: Optional[Tuple[int, int]] = None
    detail_level: float = 0.8  # 0-1 scale
    artifact_level: float = 0.2  # 0-1 scale (lower is better)
    consistency: float = 0.8  # 0-1 scale
    accuracy: float = 0.8  # 0-1 scale
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'detail_level': round(self.detail_level, 2),
            'artifact_level': round(self.artifact_level, 2),
            'consistency': round(self.consistency, 2),
            'accuracy': round(self.accuracy, 2)
        }
        if self.resolution:
            result['resolution'] = list(self.resolution)
        return result


@dataclass
class QualityImpact:
    """Complete quality impact assessment"""
    estimated_time: TimeEstimate
    time_confidence: float
    resource_requirements: ResourceEstimate
    quality_metrics: QualityMetrics
    cost_estimate: float
    sample_outputs: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'estimated_time': self.estimated_time.to_dict(),
            'time_confidence': round(self.time_confidence, 2),
            'resource_requirements': self.resource_requirements.to_dict(),
            'quality_metrics': self.quality_metrics.to_dict(),
            'cost_estimate': round(self.cost_estimate, 4),
            'sample_outputs': self.sample_outputs,
            'warnings': self.warnings
        }


@dataclass
class TaskExecution:
    """Historical task execution data"""
    template_id: str
    preset_id: str
    input_hash: str
    duration: float
    resource_usage: Dict[str, float]
    output_metrics: Dict[str, Any]
    timestamp: datetime


class HistoricalDataStore:
    """Store and retrieve historical execution data"""
    
    def __init__(self):
        self.executions: List[TaskExecution] = []
        self.cache = {}
    
    async def find_similar(self, 
                          template_id: str,
                          preset_id: str,
                          input_hash: str,
                          limit: int = 10) -> List[TaskExecution]:
        """Find similar historical executions"""
        
        # Exact matches first
        exact_matches = [
            e for e in self.executions
            if e.template_id == template_id 
            and e.preset_id == preset_id
            and e.input_hash == input_hash
        ]
        
        if len(exact_matches) >= limit:
            return exact_matches[:limit]
        
        # Same template and preset
        similar = [
            e for e in self.executions
            if e.template_id == template_id 
            and e.preset_id == preset_id
            and e.input_hash != input_hash
        ]
        
        # Combine and return
        results = exact_matches + similar
        return results[:limit]
    
    async def add_execution(self, execution: TaskExecution):
        """Add new execution data"""
        self.executions.append(execution)
        
        # Keep only recent data (last 1000 executions)
        if len(self.executions) > 1000:
            self.executions = self.executions[-1000:]


class QualityImpactEstimator:
    """Estimate impact of quality settings on outputs"""
    
    def __init__(self):
        self.historical_data = HistoricalDataStore()
        self.base_estimates = {
            'image_generation': {'time': 30, 'vram': 6, 'memory': 8},
            'video_generation': {'time': 120, 'vram': 10, 'memory': 16},
            'audio_generation': {'time': 45, 'vram': 4, 'memory': 8},
            'text_generation': {'time': 20, 'vram': 8, 'memory': 12}
        }
        
    async def estimate_impact(self,
                            template: FunctionTemplate,
                            preset: QualityPreset,
                            inputs: Dict[str, Any]) -> QualityImpact:
        """Estimate the impact of quality settings"""
        
        # Get historical data for similar tasks
        input_hash = self._hash_inputs(inputs)
        similar_tasks = await self.historical_data.find_similar(
            template_id=template.id,
            preset_id=preset.id,
            input_hash=input_hash
        )
        
        # Calculate estimates
        time_estimate = await self._estimate_time(template, preset, similar_tasks, inputs)
        resource_estimate = await self._estimate_resources(template, preset, inputs)
        quality_metrics = self._estimate_quality_metrics(preset, inputs)
        
        # Calculate confidence based on historical data
        confidence = self._calculate_confidence(similar_tasks)
        
        # Estimate cost
        cost_estimate = self._estimate_cost(time_estimate, resource_estimate)
        
        # Get sample outputs if available
        sample_outputs = await self._get_sample_outputs(template, preset, similar_tasks)
        
        # Generate warnings
        warnings = self._generate_warnings(template, preset, inputs, resource_estimate)
        
        return QualityImpact(
            estimated_time=time_estimate,
            time_confidence=confidence,
            resource_requirements=resource_estimate,
            quality_metrics=quality_metrics,
            cost_estimate=cost_estimate,
            sample_outputs=sample_outputs,
            warnings=warnings
        )
    
    def _hash_inputs(self, inputs: Dict[str, Any]) -> str:
        """Create hash of inputs for similarity matching"""
        # Exclude quality preset from hash
        filtered_inputs = {k: v for k, v in inputs.items() if k != 'quality'}
        
        # Convert to string and hash
        input_str = str(sorted(filtered_inputs.items()))
        return hashlib.md5(input_str.encode()).hexdigest()[:8]
    
    async def _estimate_time(self,
                           template: FunctionTemplate,
                           preset: QualityPreset,
                           historical: List[TaskExecution],
                           inputs: Dict[str, Any] = None) -> TimeEstimate:
        """Estimate execution time"""
        
        # Get base time from template or defaults
        category = template.category.lower()
        base_config = self.base_estimates.get(
            self._normalize_category(category),
            {'time': 60}
        )
        base_time = template.resources.estimated_time_seconds or base_config['time']
        
        if historical and len(historical) >= 3:
            # Use historical data
            times = [t.duration for t in historical]
            median_time = statistics.median(times)
            
            if len(times) > 1:
                std_dev = statistics.stdev(times)
                return TimeEstimate(
                    min_seconds=max(1, median_time - std_dev),
                    max_seconds=median_time + std_dev,
                    expected_seconds=median_time,
                    confidence=min(0.95, 0.7 + len(times) * 0.02)
                )
            else:
                return TimeEstimate(
                    min_seconds=median_time * 0.8,
                    max_seconds=median_time * 1.2,
                    expected_seconds=median_time,
                    confidence=0.7
                )
        else:
            # Use multipliers
            expected = base_time * preset.time_multiplier
            
            # Adjust based on input complexity
            if inputs:
                complexity_factor = self._calculate_complexity_factor(template, preset, inputs)
            else:
                complexity_factor = 1.0
            expected *= complexity_factor
            
            return TimeEstimate(
                min_seconds=expected * 0.7,
                max_seconds=expected * 1.5,
                expected_seconds=expected,
                confidence=0.5
            )
    
    async def _estimate_resources(self,
                                template: FunctionTemplate,
                                preset: QualityPreset,
                                inputs: Dict[str, Any]) -> ResourceEstimate:
        """Estimate resource requirements"""
        
        # Start with template requirements
        base_resources = template.resources
        category = self._normalize_category(template.category.lower())
        defaults = self.base_estimates.get(category, {})
        
        # Apply preset scaling
        vram_gb = (base_resources.vram_gb or defaults.get('vram', 6)) * preset.resource_multiplier
        memory_gb = (base_resources.memory_gb or defaults.get('memory', 8)) * preset.resource_multiplier
        
        # Adjust for resolution/size
        if 'width' in inputs and 'height' in inputs:
            resolution_factor = (inputs['width'] * inputs['height']) / (1024 * 1024)  # Relative to 1024x1024
            vram_gb *= max(0.5, min(2.0, resolution_factor))
            memory_gb *= max(0.8, min(1.5, resolution_factor))
        
        # Adjust for batch size
        batch_size = inputs.get('batch_size', 1)
        if batch_size > 1:
            vram_gb *= (1 + (batch_size - 1) * 0.3)  # Not linear scaling
            memory_gb *= (1 + (batch_size - 1) * 0.2)
        
        return ResourceEstimate(
            cpu_cores=base_resources.cpu_cores,
            memory_gb=round(memory_gb, 1),
            vram_gb=round(vram_gb, 1),
            disk_gb=base_resources.disk_gb * preset.resource_multiplier,
            network_mbps=10.0 if preset.level >= QualityLevel.HIGH else 5.0
        )
    
    def _estimate_quality_metrics(self, preset: QualityPreset, inputs: Dict[str, Any]) -> QualityMetrics:
        """Estimate output quality metrics"""
        
        # Base quality scores by level
        quality_scores = {
            QualityLevel.DRAFT: {
                'detail_level': 0.6,
                'artifact_level': 0.4,
                'consistency': 0.7,
                'accuracy': 0.7
            },
            QualityLevel.STANDARD: {
                'detail_level': 0.8,
                'artifact_level': 0.2,
                'consistency': 0.85,
                'accuracy': 0.85
            },
            QualityLevel.HIGH: {
                'detail_level': 0.9,
                'artifact_level': 0.1,
                'consistency': 0.92,
                'accuracy': 0.92
            },
            QualityLevel.ULTRA: {
                'detail_level': 0.95,
                'artifact_level': 0.05,
                'consistency': 0.95,
                'accuracy': 0.95
            }
        }
        
        scores = quality_scores.get(preset.level, quality_scores[QualityLevel.STANDARD])
        
        # Determine output resolution if applicable
        resolution = None
        if 'width' in inputs and 'height' in inputs:
            scale = preset.parameters.get('image_generation', {}).get('resolution_scale', 1.0)
            resolution = (
                int(inputs['width'] * scale),
                int(inputs['height'] * scale)
            )
        
        return QualityMetrics(
            resolution=resolution,
            detail_level=scores['detail_level'],
            artifact_level=scores['artifact_level'],
            consistency=scores['consistency'],
            accuracy=scores['accuracy']
        )
    
    def _calculate_confidence(self, similar_tasks: List[TaskExecution]) -> float:
        """Calculate confidence based on historical data"""
        if not similar_tasks:
            return 0.5
        
        # More historical data = higher confidence
        base_confidence = min(0.9, 0.5 + len(similar_tasks) * 0.05)
        
        # Check consistency of historical data
        if len(similar_tasks) > 2:
            times = [t.duration for t in similar_tasks]
            mean_time = statistics.mean(times)
            std_dev = statistics.stdev(times)
            cv = std_dev / mean_time if mean_time > 0 else 1.0
            
            # Lower coefficient of variation = higher confidence
            consistency_factor = max(0.5, 1.0 - cv)
            base_confidence *= consistency_factor
        
        return round(base_confidence, 2)
    
    def _estimate_cost(self, time_estimate: TimeEstimate, resource_estimate: ResourceEstimate) -> float:
        """Estimate execution cost"""
        # Simple cost model
        compute_cost_per_hour = 0.10  # $0.10 per compute hour
        gpu_cost_per_hour = 0.50  # $0.50 per GPU hour
        
        hours = time_estimate.expected_seconds / 3600
        
        # Base compute cost
        cost = hours * compute_cost_per_hour
        
        # Add GPU cost if using GPU
        if resource_estimate.vram_gb > 0:
            cost += hours * gpu_cost_per_hour * (resource_estimate.vram_gb / 8.0)  # Scaled by VRAM usage
        
        return cost
    
    async def _get_sample_outputs(self,
                                template: FunctionTemplate,
                                preset: QualityPreset,
                                similar_tasks: List[TaskExecution]) -> List[Dict[str, Any]]:
        """Get sample outputs from similar executions"""
        samples = []
        
        # In a real implementation, this would retrieve actual output samples
        # For now, return metadata about expected outputs
        for i, task in enumerate(similar_tasks[:3]):
            samples.append({
                'sample_id': f"sample_{i+1}",
                'preset': preset.id,
                'execution_time': task.duration,
                'quality_metrics': task.output_metrics,
                'thumbnail': f"/api/samples/{template.id}/{preset.id}/{i+1}/thumbnail"
            })
        
        return samples
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category name for lookups"""
        mappings = {
            'image': 'image_generation',
            'img2img': 'image_generation',
            'video': 'video_generation',
            'audio': 'audio_generation',
            'text': 'text_generation'
        }
        
        for key, value in mappings.items():
            if key in category:
                return value
        
        return category
    
    def _calculate_complexity_factor(self, template: FunctionTemplate, preset: QualityPreset, inputs: Dict[str, Any]) -> float:
        """Calculate complexity factor based on inputs"""
        factor = 1.0
        
        # Resolution complexity
        if 'width' in inputs and 'height' in inputs:
            pixels = inputs['width'] * inputs['height']
            if pixels > 2048 * 2048:
                factor *= 1.5
            elif pixels > 4096 * 4096:
                factor *= 2.0
        
        # Batch size complexity
        batch_size = inputs.get('batch_size', 1)
        if batch_size > 1:
            factor *= (1 + (batch_size - 1) * 0.7)  # Sub-linear scaling
        
        # Duration complexity (for video/audio)
        duration = inputs.get('duration', 0)
        if duration > 30:
            factor *= (1 + (duration - 30) / 60)  # Linear scaling after 30s
        
        return factor
    
    def _generate_warnings(self,
                         template: FunctionTemplate,
                         preset: QualityPreset,
                         inputs: Dict[str, Any],
                         resources: ResourceEstimate) -> List[str]:
        """Generate warnings about potential issues"""
        warnings = []
        
        # Resource warnings
        if resources.vram_gb > 24:
            warnings.append(f"Requires {resources.vram_gb:.1f}GB VRAM - may exceed typical GPU capacity")
        
        if resources.memory_gb > 64:
            warnings.append(f"Requires {resources.memory_gb:.1f}GB RAM - ensure sufficient system memory")
        
        # Quality warnings
        if preset.level == QualityLevel.DRAFT:
            if inputs.get('width', 0) > 1920 or inputs.get('height', 0) > 1080:
                warnings.append("Draft quality may show visible artifacts at high resolutions")
        
        # Time warnings
        if preset.time_multiplier > 5:
            warnings.append(f"Ultra quality takes {preset.time_multiplier}x longer - consider for final output only")
        
        # Batch warnings
        batch_size = inputs.get('batch_size', 1)
        if batch_size > 4 and preset.level >= QualityLevel.HIGH:
            warnings.append(f"Large batch size ({batch_size}) with {preset.name} quality may cause memory issues")
        
        return warnings