"""
Performance profiling system for the Function Runner Architecture.

Creates detailed performance profiles for different workloads and identifies
optimal operating points and resource limits.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics
from pathlib import Path

from .scenarios import LoadScenario, TestType, TaskProfile
from .framework import PerformanceTestFramework
from .analyzer import PerformanceAnalysis, PerformanceKPIs

logger = logging.getLogger(__name__)


@dataclass
class Workload:
    """Represents a workload for performance profiling."""
    
    id: str
    name: str
    description: str = ""
    base_users: int = 100
    base_duration: int = 300
    
    def create_scenario(self, load_multiplier: float, duration: Optional[int] = None) -> LoadScenario:
        """Create a LoadScenario for this workload at the specified load multiplier."""
        
        users = int(self.base_users * load_multiplier)
        duration_seconds = duration or int(self.base_duration * load_multiplier)
        
        return LoadScenario(
            name=f"{self.name}_{load_multiplier}x",
            description=f"{self.description} at {load_multiplier}x load",
            test_type=TestType.MIXED,
            users=users,
            duration_seconds=duration_seconds,
            ramp_up_seconds=min(60, duration_seconds // 5),
            cooldown_seconds=min(30, duration_seconds // 10),
            tasks=[
                TaskProfile(
                    template_id="image_generation_v1",
                    frequency=0.3,
                    quality_distribution={'standard': 0.7, 'draft': 0.3}
                ),
                TaskProfile(
                    template_id="text_generation_v1",
                    frequency=0.5,
                    quality_distribution={'standard': 0.9, 'draft': 0.1}
                ),
                TaskProfile(
                    template_id="video_generation_v1",
                    frequency=0.2,
                    quality_distribution={'draft': 1.0}
                )
            ],
            tags=["profiling", f"load_{load_multiplier}x"]
        )


@dataclass
class ScalingDataPoint:
    """Data point for scaling analysis."""
    
    load_multiplier: float
    throughput: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    active_workers: int
    queue_depth: float
    resource_efficiency: float


@dataclass
class OptimalLoad:
    """Optimal operating point."""
    
    load_multiplier: float
    throughput: float
    latency_p95: float
    efficiency_score: float
    resource_utilization: float
    max_sustainable_load: float


@dataclass
class ResourceLimits:
    """Identified system resource limits."""
    
    cpu_limit: float
    memory_limit: float
    disk_io_limit: float
    network_limit: float
    concurrent_task_limit: int
    queue_capacity: int
    scaling_break_point: float


@dataclass
class ScalingAnalysis:
    """Scaling characteristics analysis."""
    
    scaling_type: str  # 'linear', 'sublinear', 'exponential', 'logarithmic'
    scaling_efficiency: float  # percentage
    efficiency_at_load: Dict[float, float]
    break_point: float  # load multiplier where system breaks
    optimal_range: Tuple[float, float]
    
    def __post_init__(self):
        if isinstance(self.optimal_range, list):
            self.optimal_range = tuple(self.optimal_range)


@dataclass
class PerformanceProfile:
    """Complete performance profile for a workload."""
    
    workload_id: str
    workload_name: str
    profile_date: datetime
    
    scaling_data: List[ScalingDataPoint]
    scaling_analysis: ScalingAnalysis
    optimal_load: OptimalLoad
    resource_limits: ResourceLimits
    
    # Performance characteristics
    baseline_throughput: float
    max_throughput: float
    min_latency: float
    max_latency: float
    
    # Resource efficiency
    cpu_efficiency: float
    memory_efficiency: float
    
    # Recommendations
    scaling_recommendations: List[str]
    optimization_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'workload_id': self.workload_id,
            'workload_name': self.workload_name,
            'profile_date': self.profile_date.isoformat(),
            'scaling_data': [asdict(point) for point in self.scaling_data],
            'scaling_analysis': asdict(self.scaling_analysis),
            'optimal_load': asdict(self.optimal_load),
            'resource_limits': asdict(self.resource_limits),
            'baseline_throughput': self.baseline_throughput,
            'max_throughput': self.max_throughput,
            'min_latency': self.min_latency,
            'max_latency': self.max_latency,
            'cpu_efficiency': self.cpu_efficiency,
            'memory_efficiency': self.memory_efficiency,
            'scaling_recommendations': self.scaling_recommendations,
            'optimization_suggestions': self.optimization_suggestions
        }


class PerformanceProfiler:
    """Creates detailed performance profiles for workloads."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the performance profiler.
        
        Args:
            config: Configuration for profiling
        """
        self.config = config or {}
        self.profiles_dir = Path(self.config.get('profiles_dir', 'performance_profiles'))
        self.profiles_dir.mkdir(exist_ok=True)
        
        self.test_framework = PerformanceTestFramework(self.config.get('framework', {}))
        
        # Profiling configuration
        self.load_levels = self.config.get('load_levels', [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0])
        self.test_duration = self.config.get('test_duration', 300)  # 5 minutes
        self.stabilization_time = self.config.get('stabilization_time', 30)  # 30 seconds
        
        logger.info("Performance profiler initialized")
    
    async def profile_workload(self, workload: Workload) -> PerformanceProfile:
        """
        Create detailed performance profile for a workload.
        
        Args:
            workload: The workload to profile
            
        Returns:
            Complete performance profile
        """
        
        logger.info(f"Profiling workload: {workload.id}")
        
        profile = PerformanceProfile(
            workload_id=workload.id,
            workload_name=workload.name,
            profile_date=datetime.now(),
            scaling_data=[],
            scaling_analysis=ScalingAnalysis(
                scaling_type="unknown",
                scaling_efficiency=0.0,
                efficiency_at_load={},
                break_point=0.0,
                optimal_range=(0.0, 0.0)
            ),
            optimal_load=OptimalLoad(
                load_multiplier=0.0,
                throughput=0.0,
                latency_p95=0.0,
                efficiency_score=0.0,
                resource_utilization=0.0,
                max_sustainable_load=0.0
            ),
            resource_limits=ResourceLimits(
                cpu_limit=0.0,
                memory_limit=0.0,
                disk_io_limit=0.0,
                network_limit=0.0,
                concurrent_task_limit=0,
                queue_capacity=0,
                scaling_break_point=0.0
            ),
            baseline_throughput=0.0,
            max_throughput=0.0,
            min_latency=0.0,
            max_latency=0.0,
            cpu_efficiency=0.0,
            memory_efficiency=0.0,
            scaling_recommendations=[],
            optimization_suggestions=[]
        )
        
        try:
            # Test at different load levels
            for load_multiplier in self.load_levels:
                logger.info(f"Testing at load multiplier: {load_multiplier}")
                
                # Create scenario for this load level
                scenario = workload.create_scenario(
                    load_multiplier=load_multiplier,
                    duration=self.test_duration
                )
                
                # Run test
                analysis = await self.test_framework.run_single_scenario(scenario)
                
                # Collect data point
                data_point = self._create_scaling_data_point(
                    load_multiplier, analysis
                )
                profile.scaling_data.append(data_point)
                
                # Brief pause between tests
                await asyncio.sleep(self.stabilization_time)
            
            # Analyze scaling characteristics
            profile.scaling_analysis = await self._analyze_scaling(profile)
            
            # Find optimal operating point
            profile.optimal_load = await self._find_optimal_load(profile)
            
            # Identify resource limits
            profile.resource_limits = await self._identify_limits(profile)
            
            # Calculate performance characteristics
            await self._calculate_performance_characteristics(profile)
            
            # Calculate efficiency metrics
            await self._calculate_efficiency_metrics(profile)
            
            # Generate recommendations
            await self._generate_recommendations(profile)
            
            # Save profile
            await self._save_profile(profile)
            
            logger.info(f"Profiling completed for {workload.id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error profiling workload {workload.id}: {e}")
            raise
    
    def _create_scaling_data_point(self, 
                                 load_multiplier: float,
                                 analysis: PerformanceAnalysis) -> ScalingDataPoint:
        """Create a scaling data point from analysis results."""
        
        return ScalingDataPoint(
            load_multiplier=load_multiplier,
            throughput=analysis.kpis.throughput,
            latency_p50=analysis.kpis.latency_p50,
            latency_p95=analysis.kpis.latency_p95,
            latency_p99=analysis.kpis.latency_p99,
            error_rate=analysis.kpis.error_rate,
            cpu_usage=analysis.kpis.cpu_usage_avg,
            memory_usage=analysis.kpis.memory_usage_avg,
            active_workers=analysis.kpis.max_concurrent_tasks,
            queue_depth=analysis.kpis.avg_queue_depth,
            resource_efficiency=analysis.kpis.worker_efficiency
        )
    
    async def _analyze_scaling(self, profile: PerformanceProfile) -> ScalingAnalysis:
        """Analyze scaling characteristics."""
        
        if not profile.scaling_data:
            return ScalingAnalysis(
                scaling_type="unknown",
                scaling_efficiency=0.0,
                efficiency_at_load={},
                break_point=0.0,
                optimal_range=(0.0, 0.0)
            )
        
        # Calculate scaling efficiency
        baseline_point = profile.scaling_data[0]  # 0.25 multiplier
        max_point = profile.scaling_data[-1]      # Highest multiplier
        
        expected_throughput = baseline_point.throughput * max_point.load_multiplier
        actual_throughput = max_point.throughput
        
        scaling_efficiency = (actual_throughput / expected_throughput) * 100 if expected_throughput > 0 else 0
        
        # Determine scaling type
        if scaling_efficiency > 90:
            scaling_type = "linear"
        elif scaling_efficiency > 70:
            scaling_type = "sublinear"
        elif scaling_efficiency > 40:
            scaling_type = "logarithmic"
        else:
            scaling_type = "exponential"
        
        # Find break point
        break_point = await self._find_break_point(profile)
        
        # Calculate efficiency at each load level
        efficiency_at_load = {}
        for point in profile.scaling_data:
            if point.load_multiplier > 0:
                expected = baseline_point.throughput * point.load_multiplier
                actual = point.throughput
                efficiency = (actual / expected) * 100 if expected > 0 else 0
                efficiency_at_load[point.load_multiplier] = efficiency
        
        # Determine optimal range
        optimal_range = await self._calculate_optimal_range(profile)
        
        return ScalingAnalysis(
            scaling_type=scaling_type,
            scaling_efficiency=scaling_efficiency,
            efficiency_at_load=efficiency_at_load,
            break_point=break_point,
            optimal_range=optimal_range
        )
    
    async def _find_break_point(self, profile: PerformanceProfile) -> float:
        """Find the load multiplier where system performance degrades significantly."""
        
        if len(profile.scaling_data) < 2:
            return 1.0
        
        # Look for significant degradation in efficiency or increase in error rate
        for i, point in enumerate(profile.scaling_data):
            if point.error_rate > 0.05 or point.latency_p99 > 10.0:
                return point.load_multiplier
        
        # If no obvious break point, use the highest tested load
        return profile.scaling_data[-1].load_multiplier
    
    async def _calculate_optimal_range(self, profile: PerformanceProfile) -> Tuple[float, float]:
        """Calculate the optimal operating range."""
        
        if not profile.scaling_data:
            return (0.5, 1.0)
        
        # Find range with good efficiency and acceptable latency
        optimal_points = []
        for point in profile.scaling_data:
            if (point.error_rate < 0.01 and
                point.latency_p95 < 2.0 and
                point.resource_efficiency > 70):
                optimal_points.append(point.load_multiplier)
        
        if optimal_points:
            return (min(optimal_points), max(optimal_points))
        else:
            return (0.5, 1.0)
    
    async def _find_optimal_load(self, profile: PerformanceProfile) -> OptimalLoad:
        """Find the optimal operating load."""
        
        if not profile.scaling_data:
            return OptimalLoad(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Calculate efficiency score for each point
        best_point = None
        best_score = 0.0
        
        for point in profile.scaling_data:
            # Score based on throughput, latency, and efficiency
            throughput_score = point.throughput / max(p.throughput for p in profile.scaling_data)
            latency_score = 1.0 - min(1.0, point.latency_p95 / 5.0)  # Normalize to 5s target
            efficiency_score = point.resource_efficiency / 100.0
            error_score = 1.0 - point.error_rate
            
            total_score = (throughput_score * 0.4 + 
                         latency_score * 0.3 + 
                         efficiency_score * 0.2 + 
                         error_score * 0.1)
            
            if total_score > best_score:
                best_score = total_score
                best_point = point
        
        if best_point:
            return OptimalLoad(
                load_multiplier=best_point.load_multiplier,
                throughput=best_point.throughput,
                latency_p95=best_point.latency_p95,
                efficiency_score=best_score,
                resource_utilization=best_point.cpu_usage,
                max_sustainable_load=profile.scaling_analysis.break_point
            )
        else:
            return OptimalLoad(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    async def _identify_limits(self, profile: PerformanceProfile) -> ResourceLimits:
        """Identify system resource limits."""
        
        # Analyze the data to find limits
        max_cpu = max(point.cpu_usage for point in profile.scaling_data)
        max_memory = max(point.memory_usage for point in profile.scaling_data)
        
        # Estimate other limits based on observed data
        max_concurrent = max(point.active_workers for point in profile.scaling_data)
        max_queue = max(point.queue_depth for point in profile.scaling_data)
        
        return ResourceLimits(
            cpu_limit=max_cpu * 1.2,  # Add 20% buffer
            memory_limit=max_memory * 1.2,
            disk_io_limit=100.0,  # Placeholder
            network_limit=100.0,  # Placeholder
            concurrent_task_limit=int(max_concurrent * 1.5),
            queue_capacity=int(max_queue * 2.0),
            scaling_break_point=profile.scaling_analysis.break_point
        )
    
    async def _calculate_performance_characteristics(self, profile: PerformanceProfile):
        """Calculate overall performance characteristics."""
        
        if not profile.scaling_data:
            return
        
        # Baseline throughput (at lowest load)
        profile.baseline_throughput = profile.scaling_data[0].throughput
        
        # Maximum throughput achieved
        profile.max_throughput = max(point.throughput for point in profile.scaling_data)
        
        # Latency ranges
        profile.min_latency = min(point.latency_p50 for point in profile.scaling_data)
        profile.max_latency = max(point.latency_p99 for point in profile.scaling_data)
    
    async def _calculate_efficiency_metrics(self, profile: PerformanceProfile):
        """Calculate resource efficiency metrics."""
        
        if not profile.scaling_data:
            return
        
        # CPU efficiency
        cpu_usage = [point.cpu_usage for point in profile.scaling_data]
        throughput = [point.throughput for point in profile.scaling_data]
        
        if cpu_usage and throughput:
            profile.cpu_efficiency = statistics.mean(throughput) / statistics.mean(cpu_usage) * 100
        
        # Memory efficiency
        memory_usage = [point.memory_usage for point in profile.scaling_data]
        if memory_usage and throughput:
            profile.memory_efficiency = statistics.mean(throughput) / statistics.mean(memory_usage) * 100
    
    async def _generate_recommendations(self, profile: PerformanceProfile):
        """Generate scaling and optimization recommendations."""
        
        recommendations = []
        suggestions = []
        
        # Scaling recommendations
        if profile.scaling_analysis.scaling_efficiency < 80:
            recommendations.append(
                f"Scaling efficiency is {profile.scaling_analysis.scaling_efficiency:.1f}% - "
                f"consider optimizing task scheduling and resource allocation"
            )
        
        if profile.scaling_analysis.break_point < 1.5:
            recommendations.append(
                f"System breaks at {profile.scaling_analysis.break_point}x load - "
                f"consider horizontal scaling or optimization"
            )
        
        # Optimization suggestions
        optimal = profile.optimal_load
        if optimal.load_multiplier < 1.0:
            suggestions.append(
                f"Optimal load is {optimal.load_multiplier}x - consider load balancing"
            )
        
        if profile.resource_limits.cpu_limit > 80:
            suggestions.append(
                "High CPU usage detected - consider CPU optimization or scaling"
            )
        
        if profile.resource_limits.memory_limit > 80:
            suggestions.append(
                "High memory usage detected - consider memory optimization"
            )
        
        profile.scaling_recommendations = recommendations
        profile.optimization_suggestions = suggestions
    
    async def _save_profile(self, profile: PerformanceProfile):
        """Save performance profile to file."""
        
        filename = f"{profile.workload_id}_{profile.profile_date.strftime('%Y%m%d_%H%M%S')}.json"
        file_path = self.profiles_dir / filename
        
        try:
            with open(file_path, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            
            logger.info(f"Performance profile saved: {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
    
    async def load_profile(self, workload_id: str) -> Optional[PerformanceProfile]:
        """Load performance profile for a workload."""
        
        # Find the most recent profile for the workload
        profile_files = list(self.profiles_dir.glob(f"{workload_id}_*.json"))
        
        if not profile_files:
            return None
        
        # Get the most recent file
        latest_file = max(profile_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to dataclass
            profile = PerformanceProfile(
                workload_id=data['workload_id'],
                workload_name=data['workload_name'],
                profile_date=datetime.fromisoformat(data['profile_date']),
                scaling_data=[
                    ScalingDataPoint(**point) 
                    for point in data['scaling_data']
                ],
                scaling_analysis=ScalingAnalysis(**data['scaling_analysis']),
                optimal_load=OptimalLoad(**data['optimal_load']),
                resource_limits=ResourceLimits(**data['resource_limits']),
                baseline_throughput=data['baseline_throughput'],
                max_throughput=data['max_throughput'],
                min_latency=data['min_latency'],
                max_latency=data['max_latency'],
                cpu_efficiency=data['cpu_efficiency'],
                memory_efficiency=data['memory_efficiency'],
                scaling_recommendations=data['scaling_recommendations'],
                optimization_suggestions=data['optimization_suggestions']
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
            return None
    
    async def compare_profiles(self, 
                             profile1: PerformanceProfile,
                             profile2: PerformanceProfile) -> Dict[str, Any]:
        """Compare two performance profiles."""
        
        return {
            'workload': profile1.workload_id,
            'comparison_date': datetime.now().isoformat(),
            'throughput_improvement': (
                (profile2.max_throughput - profile1.max_throughput) / 
                profile1.max_throughput * 100
            ) if profile1.max_throughput > 0 else 0,
            'latency_improvement': (
                (profile1.min_latency - profile2.min_latency) / 
                profile1.min_latency * 100
            ) if profile1.min_latency > 0 else 0,
            'scaling_efficiency_change': (
                profile2.scaling_analysis.scaling_efficiency - 
                profile1.scaling_analysis.scaling_efficiency
            ),
            'optimal_load_change': (
                profile2.optimal_load.load_multiplier - 
                profile1.optimal_load.load_multiplier
            ),
            'resource_limit_changes': {
                'cpu_limit_change': profile2.resource_limits.cpu_limit - profile1.resource_limits.cpu_limit,
                'memory_limit_change': profile2.resource_limits.memory_limit - profile1.resource_limits.memory_limit,
                'concurrent_task_limit_change': profile2.resource_limits.concurrent_task_limit - profile1.resource_limits.concurrent_task_limit
            }
        }