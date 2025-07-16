"""
Quality Comparison Tools

Compare outputs across different quality presets for A/B testing
and quality analysis.
"""

import uuid
import time
import asyncio
import statistics
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ComparisonAnalysis:
    """Analysis of quality differences"""
    time_ratios: Dict[str, float] = field(default_factory=dict)
    quality_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    resource_usage: Dict[str, Dict[str, float]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    best_value_preset: Optional[str] = None
    fastest_acceptable_preset: Optional[str] = None


@dataclass
class ComparisonResult:
    """Result of quality comparison"""
    comparison_id: str
    template_id: str
    inputs: Dict[str, Any]
    results: Dict[str, Any]
    timings: Dict[str, float]
    analysis: ComparisonAnalysis
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'comparison_id': self.comparison_id,
            'template_id': self.template_id,
            'inputs': self.inputs,
            'results': self.results,
            'timings': self.timings,
            'analysis': {
                'time_ratios': self.analysis.time_ratios,
                'quality_metrics': self.analysis.quality_metrics,
                'resource_usage': self.analysis.resource_usage,
                'recommendations': self.analysis.recommendations,
                'best_value_preset': self.analysis.best_value_preset,
                'fastest_acceptable_preset': self.analysis.fastest_acceptable_preset
            },
            'created_at': self.created_at.isoformat()
        }


class QualityComparisonService:
    """Compare outputs across different quality presets"""
    
    def __init__(self, function_runner=None):
        self.function_runner = function_runner
        self.comparison_cache = {}
        self.analysis_functions = {
            'image': self._analyze_image_quality,
            'video': self._analyze_video_quality,
            'audio': self._analyze_audio_quality,
            'text': self._analyze_text_quality
        }
    
    async def generate_comparison(self,
                                 template_id: str,
                                 inputs: Dict[str, Any],
                                 presets: List[str] = None,
                                 include_analysis: bool = True) -> ComparisonResult:
        """Generate outputs with different quality presets for comparison"""
        
        if not presets:
            presets = ['draft', 'standard', 'high', 'ultra']
        
        comparison_id = str(uuid.uuid4())
        
        # Submit tasks for each preset
        tasks = []
        for preset_id in presets:
            task_inputs = {**inputs, 'quality': preset_id}
            
            if self.function_runner:
                task = await self.function_runner.submit_task(
                    template_id=template_id,
                    inputs=task_inputs,
                    metadata={
                        'comparison_id': comparison_id,
                        'quality_preset': preset_id
                    }
                )
                tasks.append((preset_id, task))
            else:
                # Mock task for testing
                tasks.append((preset_id, self._create_mock_task(template_id, task_inputs)))
        
        # Wait for all tasks to complete
        results = {}
        timings = {}
        resource_usage = {}
        
        for preset_id, task in tasks:
            start_time = time.time()
            try:
                if hasattr(task, 'wait'):
                    result = await task.wait(timeout=600)  # 10 min timeout
                else:
                    # Mock result
                    await asyncio.sleep(0.1)  # Simulate processing
                    result = await task
                
                results[preset_id] = result
                timings[preset_id] = time.time() - start_time
                
                # Extract resource usage if available
                if isinstance(result, dict) and 'metadata' in result:
                    resource_usage[preset_id] = result['metadata'].get('resource_usage', {})
                
            except asyncio.TimeoutError:
                results[preset_id] = {'error': 'Timeout after 10 minutes'}
                timings[preset_id] = 600.0
            except Exception as e:
                results[preset_id] = {'error': str(e)}
                timings[preset_id] = time.time() - start_time
        
        # Analyze differences
        analysis = ComparisonAnalysis()
        if include_analysis:
            analysis = await self._analyze_results(results, timings, resource_usage, template_id)
        
        comparison_result = ComparisonResult(
            comparison_id=comparison_id,
            template_id=template_id,
            inputs=inputs,
            results=results,
            timings=timings,
            analysis=analysis
        )
        
        # Cache result
        self.comparison_cache[comparison_id] = comparison_result
        
        return comparison_result
    
    async def get_comparison(self, comparison_id: str) -> Optional[ComparisonResult]:
        """Retrieve a previous comparison result"""
        return self.comparison_cache.get(comparison_id)
    
    async def _analyze_results(self, 
                             results: Dict[str, Any],
                             timings: Dict[str, float],
                             resource_usage: Dict[str, Dict[str, float]],
                             template_id: str) -> ComparisonAnalysis:
        """Analyze quality differences between results"""
        
        analysis = ComparisonAnalysis()
        
        # Time analysis
        valid_timings = {k: v for k, v in timings.items() if v is not None and v < 600}
        if valid_timings:
            base_time = valid_timings.get('standard', 1.0)
            if base_time > 0:
                analysis.time_ratios = {
                    k: round(v / base_time, 2) for k, v in valid_timings.items()
                }
        
        # Resource usage analysis
        analysis.resource_usage = resource_usage
        
        # Quality metrics analysis
        valid_results = {k: v for k, v in results.items() if not isinstance(v, dict) or 'error' not in v}
        if valid_results:
            # Determine output type from template
            output_type = self._get_output_type(template_id)
            if output_type in self.analysis_functions:
                analysis.quality_metrics = await self.analysis_functions[output_type](valid_results)
        
        # Generate recommendations
        analysis.recommendations = self._generate_recommendations(
            analysis.time_ratios,
            analysis.quality_metrics,
            resource_usage
        )
        
        # Determine best presets
        analysis.best_value_preset = self._find_best_value_preset(
            analysis.time_ratios,
            analysis.quality_metrics
        )
        analysis.fastest_acceptable_preset = self._find_fastest_acceptable_preset(
            analysis.time_ratios,
            analysis.quality_metrics
        )
        
        return analysis
    
    def _get_output_type(self, template_id: str) -> str:
        """Determine output type from template ID"""
        # Simple heuristic based on template ID
        if any(x in template_id.lower() for x in ['image', 'img', 'photo']):
            return 'image'
        elif any(x in template_id.lower() for x in ['video', 'animation', 'motion']):
            return 'video'
        elif any(x in template_id.lower() for x in ['audio', 'sound', 'music', 'voice']):
            return 'audio'
        elif any(x in template_id.lower() for x in ['text', 'llm', 'generate']):
            return 'text'
        return 'unknown'
    
    async def _analyze_image_quality(self, results: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Analyze image quality metrics"""
        metrics = {}
        
        for preset_id, result in results.items():
            if isinstance(result, dict) and 'output' in result:
                # In a real implementation, we would analyze the actual image
                # For now, use placeholder metrics
                metrics[preset_id] = {
                    'resolution': self._get_resolution_score(preset_id),
                    'sharpness': self._get_sharpness_score(preset_id),
                    'artifacts': self._get_artifact_score(preset_id),
                    'color_accuracy': self._get_color_score(preset_id),
                    'overall': self._get_overall_score(preset_id)
                }
        
        return metrics
    
    async def _analyze_video_quality(self, results: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Analyze video quality metrics"""
        metrics = {}
        
        for preset_id, result in results.items():
            if isinstance(result, dict) and 'output' in result:
                metrics[preset_id] = {
                    'resolution': self._get_resolution_score(preset_id),
                    'frame_consistency': self._get_consistency_score(preset_id),
                    'motion_smoothness': self._get_smoothness_score(preset_id),
                    'compression_artifacts': self._get_artifact_score(preset_id),
                    'overall': self._get_overall_score(preset_id)
                }
        
        return metrics
    
    async def _analyze_audio_quality(self, results: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Analyze audio quality metrics"""
        metrics = {}
        
        for preset_id, result in results.items():
            if isinstance(result, dict) and 'output' in result:
                metrics[preset_id] = {
                    'clarity': self._get_clarity_score(preset_id),
                    'noise_level': self._get_noise_score(preset_id),
                    'dynamic_range': self._get_dynamic_range_score(preset_id),
                    'frequency_response': self._get_frequency_score(preset_id),
                    'overall': self._get_overall_score(preset_id)
                }
        
        return metrics
    
    async def _analyze_text_quality(self, results: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Analyze text quality metrics"""
        metrics = {}
        
        for preset_id, result in results.items():
            if isinstance(result, dict) and 'output' in result:
                metrics[preset_id] = {
                    'coherence': self._get_coherence_score(preset_id),
                    'creativity': self._get_creativity_score(preset_id),
                    'accuracy': self._get_accuracy_score(preset_id),
                    'fluency': self._get_fluency_score(preset_id),
                    'overall': self._get_overall_score(preset_id)
                }
        
        return metrics
    
    def _generate_recommendations(self,
                                time_ratios: Dict[str, float],
                                quality_metrics: Dict[str, Dict[str, float]],
                                resource_usage: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Time-based recommendations
        if 'draft' in time_ratios and time_ratios['draft'] < 0.5:
            recommendations.append("Draft quality is significantly faster (>50% time reduction) - ideal for iterations")
        
        if 'ultra' in time_ratios and time_ratios['ultra'] > 3.0:
            recommendations.append("Ultra quality takes 3x+ longer - reserve for final outputs only")
        
        # Quality-based recommendations
        if quality_metrics:
            draft_quality = quality_metrics.get('draft', {}).get('overall', 0)
            standard_quality = quality_metrics.get('standard', {}).get('overall', 0)
            
            if draft_quality > 0 and standard_quality > 0:
                quality_diff = (standard_quality - draft_quality) / standard_quality
                if quality_diff < 0.15:  # Less than 15% quality difference
                    recommendations.append("Draft quality is within 15% of standard - consider using for most tasks")
        
        # Resource-based recommendations
        if resource_usage:
            ultra_vram = resource_usage.get('ultra', {}).get('vram_gb', 0)
            if ultra_vram > 20:
                recommendations.append(f"Ultra quality requires {ultra_vram:.1f}GB VRAM - ensure GPU compatibility")
        
        return recommendations
    
    def _find_best_value_preset(self,
                              time_ratios: Dict[str, float],
                              quality_metrics: Dict[str, Dict[str, float]]) -> Optional[str]:
        """Find preset with best quality/time ratio"""
        if not quality_metrics or not time_ratios:
            return 'standard'
        
        scores = {}
        for preset_id in ['draft', 'standard', 'high', 'ultra']:
            if preset_id in quality_metrics and preset_id in time_ratios:
                quality = quality_metrics[preset_id].get('overall', 0)
                time_ratio = time_ratios[preset_id]
                if time_ratio > 0:
                    # Higher score is better (quality per time unit)
                    scores[preset_id] = quality / time_ratio
        
        if scores:
            return max(scores, key=scores.get)
        return 'standard'
    
    def _find_fastest_acceptable_preset(self,
                                      time_ratios: Dict[str, float],
                                      quality_metrics: Dict[str, Dict[str, float]]) -> Optional[str]:
        """Find fastest preset with acceptable quality (>70%)"""
        acceptable_threshold = 0.7
        
        candidates = []
        for preset_id in ['draft', 'standard', 'high', 'ultra']:
            if preset_id in quality_metrics:
                quality = quality_metrics[preset_id].get('overall', 0)
                if quality >= acceptable_threshold:
                    time_ratio = time_ratios.get(preset_id, float('inf'))
                    candidates.append((preset_id, time_ratio))
        
        if candidates:
            # Sort by time ratio and return fastest
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]
        
        return 'standard'
    
    async def _create_mock_task(self, template_id: str, inputs: Dict[str, Any]):
        """Create mock task for testing"""
        # Simulate different execution times based on quality
        quality = inputs.get('quality', 'standard')
        delay_map = {
            'draft': 0.1,
            'standard': 0.3,
            'high': 0.7,
            'ultra': 1.5
        }
        
        await asyncio.sleep(delay_map.get(quality, 0.3))
        
        return {
            'output': f"Mock output for {quality} quality",
            'metadata': {
                'quality': quality,
                'resource_usage': {
                    'cpu': 0.5 * delay_map.get(quality, 1.0),
                    'memory_gb': 2.0 * delay_map.get(quality, 1.0),
                    'vram_gb': 4.0 * delay_map.get(quality, 1.0)
                }
            }
        }
    
    # Placeholder scoring methods - in production these would analyze actual outputs
    def _get_resolution_score(self, preset_id: str) -> float:
        scores = {'draft': 0.6, 'standard': 0.8, 'high': 0.9, 'ultra': 1.0}
        return scores.get(preset_id, 0.8)
    
    def _get_sharpness_score(self, preset_id: str) -> float:
        scores = {'draft': 0.5, 'standard': 0.75, 'high': 0.9, 'ultra': 0.95}
        return scores.get(preset_id, 0.75)
    
    def _get_artifact_score(self, preset_id: str) -> float:
        scores = {'draft': 0.4, 'standard': 0.7, 'high': 0.85, 'ultra': 0.95}
        return scores.get(preset_id, 0.7)
    
    def _get_color_score(self, preset_id: str) -> float:
        scores = {'draft': 0.7, 'standard': 0.85, 'high': 0.92, 'ultra': 0.98}
        return scores.get(preset_id, 0.85)
    
    def _get_consistency_score(self, preset_id: str) -> float:
        scores = {'draft': 0.5, 'standard': 0.75, 'high': 0.88, 'ultra': 0.95}
        return scores.get(preset_id, 0.75)
    
    def _get_smoothness_score(self, preset_id: str) -> float:
        scores = {'draft': 0.4, 'standard': 0.7, 'high': 0.85, 'ultra': 0.93}
        return scores.get(preset_id, 0.7)
    
    def _get_clarity_score(self, preset_id: str) -> float:
        scores = {'draft': 0.6, 'standard': 0.8, 'high': 0.9, 'ultra': 0.97}
        return scores.get(preset_id, 0.8)
    
    def _get_noise_score(self, preset_id: str) -> float:
        scores = {'draft': 0.5, 'standard': 0.75, 'high': 0.88, 'ultra': 0.95}
        return scores.get(preset_id, 0.75)
    
    def _get_dynamic_range_score(self, preset_id: str) -> float:
        scores = {'draft': 0.6, 'standard': 0.8, 'high': 0.9, 'ultra': 0.95}
        return scores.get(preset_id, 0.8)
    
    def _get_frequency_score(self, preset_id: str) -> float:
        scores = {'draft': 0.5, 'standard': 0.8, 'high': 0.9, 'ultra': 0.98}
        return scores.get(preset_id, 0.8)
    
    def _get_coherence_score(self, preset_id: str) -> float:
        scores = {'draft': 0.7, 'standard': 0.85, 'high': 0.92, 'ultra': 0.96}
        return scores.get(preset_id, 0.85)
    
    def _get_creativity_score(self, preset_id: str) -> float:
        scores = {'draft': 0.8, 'standard': 0.85, 'high': 0.88, 'ultra': 0.9}
        return scores.get(preset_id, 0.85)
    
    def _get_accuracy_score(self, preset_id: str) -> float:
        scores = {'draft': 0.6, 'standard': 0.8, 'high': 0.9, 'ultra': 0.95}
        return scores.get(preset_id, 0.8)
    
    def _get_fluency_score(self, preset_id: str) -> float:
        scores = {'draft': 0.7, 'standard': 0.85, 'high': 0.92, 'ultra': 0.96}
        return scores.get(preset_id, 0.85)
    
    def _get_overall_score(self, preset_id: str) -> float:
        scores = {'draft': 0.6, 'standard': 0.8, 'high': 0.9, 'ultra': 0.95}
        return scores.get(preset_id, 0.8)