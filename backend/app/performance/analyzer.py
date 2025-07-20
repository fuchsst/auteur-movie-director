"""
Performance analysis engine for identifying bottlenecks and regressions.

Analyzes collected metrics to identify performance issues, compare against
baselines, and provide actionable recommendations.
"""

import asyncio
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from .metrics import TestMetrics
from .scenarios import LoadScenario, PassCriteria
from .types import TestResults, PerformanceAnalysis

logger = logging.getLogger(__name__)


@dataclass
class PerformanceKPIs:
    """Key Performance Indicators for performance analysis."""
    
    throughput: float = 0.0  # tasks per second
    error_rate: float = 0.0  # percentage
    
    latency_p50: float = 0.0  # seconds
    latency_p95: float = 0.0  # seconds
    latency_p99: float = 0.0  # seconds
    latency_max: float = 0.0  # seconds
    
    max_concurrent_tasks: int = 0
    avg_queue_depth: float = 0.0
    
    cpu_usage_avg: float = 0.0  # percentage
    cpu_usage_max: float = 0.0  # percentage
    memory_usage_avg: float = 0.0  # percentage
    memory_usage_max: float = 0.0  # percentage
    
    worker_efficiency: float = 0.0  # percentage
    resource_utilization: float = 0.0  # percentage


@dataclass
class Bottleneck:
    """Identified system bottleneck."""
    
    type: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    impact: str  # 'throughput', 'latency', 'availability', 'resources'
    value: float
    threshold: float
    recommendations: List[str]
    timestamp: datetime


@dataclass
class Anomaly:
    """Detected performance anomaly."""
    
    type: str
    description: str
    severity: str
    start_time: datetime
    duration: float  # seconds
    metrics_affected: List[str]
    value: float
    expected_range: Tuple[float, float]


@dataclass
class BaselineComparison:
    """Comparison against baseline metrics."""
    
    metric_name: str
    current_value: float
    baseline_value: float
    change_percent: float
    status: str  # 'improved', 'degraded', 'regression', 'stable'
    threshold: float
    severity: str


@dataclass
class PerformanceRecommendation:
    """Actionable performance recommendation."""
    
    category: str
    description: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    estimated_impact: str
    implementation_effort: str  # 'low', 'medium', 'high'
    specific_actions: List[str]
    expected_improvement: Optional[float] = None  # percentage


@dataclass
class PerformanceAnalysis:
    """Complete performance analysis results."""
    
    scenario_name: str
    analysis_time: datetime
    
    kpis: PerformanceKPIs
    bottlenecks: List[Bottleneck]
    anomalies: List[Anomaly]
    baseline_comparisons: List[BaselineComparison]
    recommendations: List[PerformanceRecommendation]
    
    passed: bool = False
    score: float = 0.0  # Overall performance score (0-100)


class ResultAnalyzer:
    """Analyzes performance test results to identify issues and opportunities."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the result analyzer.
        
        Args:
            config: Configuration for analysis parameters
        """
        self.config = config or {}
        self.baseline_dir = Path(self.config.get('baseline_dir', 'performance_baselines'))
        
        # Analysis thresholds
        self.latency_regression_threshold = self.config.get('latency_regression_threshold', 1.2)  # 20%
        self.error_rate_regression_threshold = self.config.get('error_rate_regression_threshold', 2.0)  # 100%
        self.throughput_regression_threshold = self.config.get('throughput_regression_threshold', 0.8)  # -20%
        
        logger.info("Result analyzer initialized")
    
    async def analyze(self, 
                     load_results: Any,
                     metrics: TestMetrics,
                     scenario: LoadScenario) -> PerformanceAnalysis:
        """
        Perform comprehensive performance analysis.
        
        Args:
            load_results: Load testing results
            metrics: Collected metrics
            scenario: Test scenario
            
        Returns:
            Complete performance analysis
        """
        
        logger.info(f"Analyzing performance for scenario: {scenario.name}")
        
        analysis = PerformanceAnalysis(
            scenario_name=scenario.name,
            analysis_time=datetime.now()
        )
        
        try:
            # Calculate KPIs
            analysis.kpis = await self._calculate_kpis(load_results, metrics)
            
            # Identify bottlenecks
            analysis.bottlenecks = await self._identify_bottlenecks(analysis.kpis, metrics, scenario)
            
            # Detect anomalies
            analysis.anomalies = await self._detect_anomalies(metrics)
            
            # Compare with baseline
            baseline = await self._load_baseline(scenario.name)
            if baseline:
                analysis.baseline_comparisons = await self._compare_with_baseline(
                    analysis.kpis, baseline
                )
            
            # Generate recommendations
            analysis.recommendations = await self._generate_recommendations(
                analysis, scenario
            )
            
            # Evaluate pass/fail
            analysis.passed = await self._evaluate_pass_criteria(analysis, scenario)
            
            # Calculate overall score
            analysis.score = await self._calculate_performance_score(analysis)
            
            logger.info(f"Analysis complete for {scenario.name}: "
                       f"passed={analysis.passed}, score={analysis.score:.1f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            raise
    
    async def _calculate_kpis(self, load_results: Any, metrics: TestMetrics) -> PerformanceKPIs:
        """Calculate key performance indicators."""
        
        kpis = PerformanceKPIs()
        
        try:
            # Throughput calculation
            if load_results and hasattr(load_results, 'duration_seconds'):
                duration = max(load_results.duration_seconds, 1)  # Avoid division by zero
                kpis.throughput = load_results.total_completed / duration
            
            # Error rate calculation
            if load_results and hasattr(load_results, 'total_submitted') and load_results.total_submitted > 0:
                kpis.error_rate = load_results.total_errors / load_results.total_submitted
            
            # Latency metrics
            if metrics.app_metrics:
                latest_app = metrics.app_metrics[-1]
                kpis.latency_p50 = latest_app.submit_latency_p50
                kpis.latency_p95 = latest_app.submit_latency_p95
                kpis.latency_p99 = latest_app.submit_latency_p99
                kpis.latency_max = max(m.submit_latency_p99 for m in metrics.app_metrics)
            
            # Queue and worker metrics
            if metrics.app_metrics:
                kpis.max_concurrent_tasks = max(m.active_tasks for m in metrics.app_metrics)
                kpis.avg_queue_depth = statistics.mean(m.queue_depth for m in metrics.app_metrics)
            
            # System metrics
            if metrics.system_metrics:
                kpis.cpu_usage_avg = statistics.mean(m.cpu_usage for m in metrics.system_metrics)
                kpis.cpu_usage_max = max(m.cpu_usage for m in metrics.system_metrics)
                kpis.memory_usage_avg = statistics.mean(m.memory_usage for m in metrics.system_metrics)
                kpis.memory_usage_max = max(m.memory_usage for m in metrics.system_metrics)
            
            # Calculate efficiency metrics
            if kpis.cpu_usage_avg > 0 and kpis.throughput > 0:
                kpis.worker_efficiency = min(100.0, (kpis.throughput / kpis.cpu_usage_avg) * 100)
            
            kpis.resource_utilization = max(kpis.cpu_usage_max, kpis.memory_usage_max)
            
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
        
        return kpis
    
    async def _identify_bottlenecks(self, 
                                  kpis: PerformanceKPIs,
                                  metrics: TestMetrics,
                                  scenario: LoadScenario) -> List[Bottleneck]:
        """Identify system bottlenecks."""
        
        bottlenecks = []
        
        # CPU bottleneck
        if kpis.cpu_usage_max > 85:
            bottlenecks.append(Bottleneck(
                type="cpu",
                description="High CPU usage indicating CPU bottleneck",
                severity="high" if kpis.cpu_usage_max > 95 else "medium",
                impact="throughput",
                value=kpis.cpu_usage_max,
                threshold=85.0,
                recommendations=[
                    "Scale up worker instances",
                    "Optimize task processing algorithms",
                    "Consider CPU-intensive task offloading"
                ],
                timestamp=datetime.now()
            ))
        
        # Memory bottleneck
        if kpis.memory_usage_max > 85:
            bottlenecks.append(Bottleneck(
                type="memory",
                description="High memory usage indicating memory pressure",
                severity="high" if kpis.memory_usage_max > 95 else "medium",
                impact="availability",
                value=kpis.memory_usage_max,
                threshold=85.0,
                recommendations=[
                    "Scale up memory resources",
                    "Implement memory-efficient processing",
                    "Add memory monitoring and alerting"
                ],
                timestamp=datetime.now()
            ))
        
        # Queue bottleneck
        if kpis.avg_queue_depth > 1000:
            bottlenecks.append(Bottleneck(
                type="queue",
                description="High queue depth indicating processing bottleneck",
                severity="high" if kpis.avg_queue_depth > 5000 else "medium",
                impact="latency",
                value=kpis.avg_queue_depth,
                threshold=1000.0,
                recommendations=[
                    "Scale up worker pool",
                    "Optimize task batching",
                    "Consider priority-based processing"
                ],
                timestamp=datetime.now()
            ))
        
        # Latency bottleneck
        if kpis.latency_p95 > 10:
            bottlenecks.append(Bottleneck(
                type="latency",
                description="High latency indicating system slowdown",
                severity="high" if kpis.latency_p95 > 30 else "medium",
                impact="latency",
                value=kpis.latency_p95,
                threshold=10.0,
                recommendations=[
                    "Scale up processing resources",
                    "Optimize task scheduling",
                    "Review task complexity and resource requirements"
                ],
                timestamp=datetime.now()
            ))
        
        # Error rate bottleneck
        if kpis.error_rate > 0.05:
            bottlenecks.append(Bottleneck(
                type="error_rate",
                description="High error rate indicating system instability",
                severity="critical" if kpis.error_rate > 0.1 else "high",
                impact="availability",
                value=kpis.error_rate,
                threshold=0.05,
                recommendations=[
                    "Investigate error sources",
                    "Implement retry mechanisms",
                    "Review resource limits and timeouts"
                ],
                timestamp=datetime.now()
            ))
        
        return bottlenecks
    
    async def _detect_anomalies(self, metrics: TestMetrics) -> List[Anomaly]:
        """Detect performance anomalies using statistical methods."""
        
        anomalies = []
        
        try:
            # Detect latency anomalies
            if metrics.app_metrics:
                latencies = [m.submit_latency_p95 for m in metrics.app_metrics]
                anomalies.extend(self._detect_metric_anomalies(
                    latencies, "latency_p95", "Latency spike detected"
                ))
            
            # Detect throughput anomalies
            if metrics.app_metrics:
                throughputs = [m.task_complete_rate for m in metrics.app_metrics]
                anomalies.extend(self._detect_metric_anomalies(
                    throughputs, "throughput", "Throughput drop detected"
                ))
            
            # Detect memory anomalies
            if metrics.system_metrics:
                memory_usage = [m.memory_usage for m in metrics.system_metrics]
                anomalies.extend(self._detect_metric_anomalies(
                    memory_usage, "memory_usage", "Memory usage anomaly"
                ))
            
            # Detect CPU anomalies
            if metrics.system_metrics:
                cpu_usage = [m.cpu_usage for m in metrics.system_metrics]
                anomalies.extend(self._detect_metric_anomalies(
                    cpu_usage, "cpu_usage", "CPU usage anomaly"
                ))
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
        
        return anomalies
    
    def _detect_metric_anomalies(self, 
                               values: List[float], 
                               metric_name: str, 
                               description: str) -> List[Anomaly]:
        """Detect anomalies in a specific metric using statistical methods."""
        
        anomalies = []
        
        if len(values) < 10:
            return anomalies
        
        try:
            # Calculate statistics
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            
            # Define anomaly thresholds
            threshold_low = mean - 3 * stdev
            threshold_high = mean + 3 * stdev
            
            # Check for anomalies
            for i, value in enumerate(values):
                if value < threshold_low or value > threshold_high:
                    severity = "high" if abs(value - mean) > 4 * stdev else "medium"
                    
                    anomalies.append(Anomaly(
                        type=metric_name,
                        description=f"{description}: {value:.2f} (expected: {mean:.2f} ± {2*stdev:.2f})",
                        severity=severity,
                        start_time=datetime.now(),
                        duration=0.0,  # Would be calculated from time series
                        metrics_affected=[metric_name],
                        value=value,
                        expected_range=(threshold_low, threshold_high)
                    ))
        
        except statistics.StatisticsError:
            pass  # Not enough data for anomaly detection
        
        return anomalies
    
    async def _load_baseline(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Load baseline metrics for comparison."""
        
        baseline_file = self.baseline_dir / f"{scenario_name}_baseline.json"
        
        if not baseline_file.exists():
            return None
        
        try:
            with open(baseline_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading baseline: {e}")
            return None
    
    async def _compare_with_baseline(self, 
                                   current_kpis: PerformanceKPIs,
                                   baseline: Dict[str, Any]) -> List[BaselineComparison]:
        """Compare current metrics against baseline."""
        
        comparisons = []
        
        metric_mapping = {
            'throughput': current_kpis.throughput,
            'error_rate': current_kpis.error_rate,
            'latency_p50': current_kpis.latency_p50,
            'latency_p95': current_kpis.latency_p95,
            'latency_p99': current_kpis.latency_p99,
            'cpu_usage_avg': current_kpis.cpu_usage_avg,
            'memory_usage_avg': current_kpis.memory_usage_avg
        }
        
        for metric_name, current_value in metric_mapping.items():
            if metric_name in baseline:
                baseline_data = baseline[metric_name]
                baseline_value = baseline_data.get('mean', 0)
                threshold = baseline_data.get('threshold', 1.2)
                
                change_percent = ((current_value - baseline_value) / baseline_value) * 100
                
                # Determine status
                if metric_name == 'throughput':
                    # Higher is better
                    if change_percent > 10:
                        status = 'improved'
                        severity = 'low'
                    elif change_percent < -20:
                        status = 'regression'
                        severity = 'high'
                    elif change_percent < -10:
                        status = 'degraded'
                        severity = 'medium'
                    else:
                        status = 'stable'
                        severity = 'low'
                else:
                    # Lower is better for most metrics
                    if change_percent < -10:
                        status = 'improved'
                        severity = 'low'
                    elif change_percent > 20:
                        status = 'regression'
                        severity = 'high'
                    elif change_percent > 10:
                        status = 'degraded'
                        severity = 'medium'
                    else:
                        status = 'stable'
                        severity = 'low'
                
                comparisons.append(BaselineComparison(
                    metric_name=metric_name,
                    current_value=current_value,
                    baseline_value=baseline_value,
                    change_percent=change_percent,
                    status=status,
                    threshold=threshold,
                    severity=severity
                ))
        
        return comparisons
    
    async def _generate_recommendations(self, 
                                      analysis: PerformanceAnalysis,
                                      scenario: LoadScenario) -> List[PerformanceRecommendation]:
        """Generate actionable performance recommendations."""
        
        recommendations = []
        
        # Analyze bottlenecks
        for bottleneck in analysis.bottlenecks:
            if bottleneck.severity in ['high', 'critical']:
                recommendations.append(PerformanceRecommendation(
                    category=bottleneck.type,
                    description=f"Address {bottleneck.type} bottleneck",
                    priority=bottleneck.severity,
                    estimated_impact=bottleneck.impact,
                    implementation_effort='medium',
                    specific_actions=bottleneck.recommendations
                ))
        
        # Analyze regressions
        for comparison in analysis.baseline_comparisons:
            if comparison.status == 'regression':
                recommendations.append(PerformanceRecommendation(
                    category='regression',
                    description=f"Fix {comparison.metric_name} regression",
                    priority='high',
                    estimated_impact='throughput',
                    implementation_effort='medium',
                    specific_actions=[
                        f"Investigate recent changes affecting {comparison.metric_name}",
                        "Review resource allocation",
                        "Consider rollback if severe"
                    ],
                    expected_improvement=abs(comparison.change_percent)
                ))
        
        # General optimization recommendations
        if analysis.kpis.latency_p95 > 5:
            recommendations.append(PerformanceRecommendation(
                category='latency',
                description="Optimize task processing latency",
                priority='medium',
                estimated_impact='latency',
                implementation_effort='high',
                specific_actions=[
                    "Profile task processing bottlenecks",
                    "Implement task caching",
                    "Optimize resource allocation",
                    "Consider async processing improvements"
                ],
                expected_improvement=20.0
            ))
        
        if analysis.kpis.resource_utilization > 70:
            recommendations.append(PerformanceRecommendation(
                category='resource',
                description="Optimize resource utilization",
                priority='medium',
                estimated_impact='efficiency',
                implementation_effort='medium',
                specific_actions=[
                    "Implement resource monitoring",
                    "Add auto-scaling based on load",
                    "Optimize task scheduling",
                    "Review resource limits"
                ],
                expected_improvement=15.0
            ))
        
        return recommendations
    
    async def _evaluate_pass_criteria(self, 
                                    analysis: PerformanceAnalysis,
                                    scenario: LoadScenario) -> bool:
        """Evaluate if performance meets pass criteria."""
        
        if not scenario.pass_criteria:
            return True  # No criteria defined
        
        criteria = scenario.pass_criteria
        
        checks = [
            analysis.kpis.error_rate <= criteria.max_error_rate,
            analysis.kpis.latency_p50 <= criteria.max_latency_p50,
            analysis.kpis.latency_p95 <= criteria.max_latency_p95,
            analysis.kpis.latency_p99 <= criteria.max_latency_p99,
            analysis.kpis.throughput >= criteria.min_throughput,
            analysis.kpis.cpu_usage_max <= criteria.max_cpu_usage,
            analysis.kpis.memory_usage_max <= criteria.max_memory_usage,
        ]
        
        # Check for critical bottlenecks
        critical_bottlenecks = [b for b in analysis.bottlenecks if b.severity == 'critical']
        if critical_bottlenecks:
            return False
        
        return all(checks)
    
    async def _calculate_performance_score(self, analysis: PerformanceAnalysis) -> float:
        """Calculate overall performance score (0-100)."""
        
        score = 100.0
        
        # Penalize based on error rate
        score -= min(50.0, analysis.kpis.error_rate * 1000)
        
        # Penalize based on latency
        latency_penalty = min(30.0, (analysis.kpis.latency_p95 - 1.0) * 10)
        score -= max(0.0, latency_penalty)
        
        # Penalize based on resource usage
        resource_penalty = min(20.0, (analysis.kpis.resource_utilization - 50.0) * 0.5)
        score -= max(0.0, resource_penalty)
        
        # Penalize based on bottlenecks
        bottleneck_penalty = len(analysis.bottlenecks) * 5
        score -= min(30.0, bottleneck_penalty)
        
        # Penalize based on regressions
        regression_penalty = len([c for c in analysis.baseline_comparisons 
                                if c.status == 'regression']) * 10
        score -= min(20.0, regression_penalty)
        
        return max(0.0, min(100.0, score))