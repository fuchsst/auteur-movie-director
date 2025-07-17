"""
CI/CD integration for performance testing.

Provides automated performance regression detection and reporting
for continuous integration pipelines.
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict, dataclass

from .framework import PerformanceTestFramework
from .scenarios import TestSuiteConfig, LoadScenarios
from .analyzer import PerformanceAnalysis
from .report import ReportGenerator

logger = logging.getLogger(__name__)


@dataclass
class RegressionResult:
    """Result of performance regression check."""
    
    passed: bool
    regressions: List[Dict[str, Any]]
    report_path: str
    summary: str
    details: Dict[str, Any]


@dataclass
class CITestConfig:
    """Configuration for CI performance tests."""
    
    test_name: str
    commit_sha: str
    branch: str
    author: str
    max_duration_minutes: int = 15
    regression_threshold: float = 1.2
    parallel_jobs: int = 1
    fail_on_regression: bool = True


class PerformanceCI:
    """Integrates performance testing with CI/CD pipelines."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CI performance testing integration.
        
        Args:
            config: Configuration for CI integration
        """
        self.config = config or {}
        self.results_dir = Path(self.config.get('results_dir', 'ci_performance_results'))
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.test_framework = PerformanceTestFramework(self.config.get('framework', {}))
        self.report_generator = ReportGenerator(self.config.get('reporting', {}))
        
        logger.info("Performance CI integration initialized")
    
    async def run_performance_regression_check(self, 
                                             ci_config: CITestConfig) -> RegressionResult:
        """
        Run performance regression check for CI.
        
        Args:
            ci_config: CI test configuration
            
        Returns:
            Regression check results
        """
        
        logger.info(f"Running CI performance regression check: {ci_config.test_name}")
        
        # Create CI-specific test configuration
        test_config = TestSuiteConfig(
            scenarios=[
                LoadScenarios.create_ci_scenario()
            ],
            name=f"CI Regression Check - {ci_config.commit_sha[:8]}",
            description=f"Automated performance regression check for commit {ci_config.commit_sha}",
            max_concurrent_scenarios=1
        )
        
        try:
            # Run performance tests
            results = await self.test_framework.run_test_suite(test_config)
            
            # Analyze results
            analysis = results.scenario_results.get("ci_quick_test")
            if not analysis:
                raise ValueError("CI test scenario not found in results")
            
            # Load baseline for comparison
            baseline = await self._load_ci_baseline()
            
            # Check for regressions
            regressions = []
            if baseline:
                regressions = await self._identify_regressions(analysis, baseline, ci_config)
            
            # Generate report
            report_path = await self._generate_ci_report(
                ci_config, results, analysis, regressions
            )
            
            # Determine pass/fail
            passed = not (regressions and ci_config.fail_on_regression)
            
            # Create summary
            summary = self._create_summary(ci_config, analysis, regressions)
            
            # Save results
            await self._save_ci_results(ci_config, results, analysis, regressions)
            
            return RegressionResult(
                passed=passed,
                regressions=regressions,
                report_path=report_path,
                summary=summary,
                details={
                    "commit_sha": ci_config.commit_sha,
                    "branch": ci_config.branch,
                    "author": ci_config.author,
                    "score": analysis.score,
                    "total_tests": 1,
                    "passed_tests": 1 if analysis.passed else 0
                }
            )
            
        except Exception as e:
            logger.error(f"CI performance check failed: {e}")
            return RegressionResult(
                passed=False,
                regressions=[],
                report_path="",
                summary=f"CI performance check failed: {str(e)}",
                details={"error": str(e)}
            )
    
    async def _load_ci_baseline(self) -> Optional[Dict[str, Any]]:
        """Load baseline for CI performance comparison."""
        
        baseline_file = self.results_dir / "ci_baseline.json"
        
        if not baseline_file.exists():
            logger.warning("No CI baseline found, skipping regression check")
            return None
        
        try:
            with open(baseline_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading CI baseline: {e}")
            return None
    
    async def _identify_regressions(self, 
                                  analysis: PerformanceAnalysis,
                                  baseline: Dict[str, Any],
                                  ci_config: CITestConfig) -> List[Dict[str, Any]]:
        """Identify performance regressions."""
        
        regressions = []
        
        # Check key metrics
        metrics_to_check = [
            ('throughput', analysis.kpis.throughput),
            ('error_rate', analysis.kpis.error_rate),
            ('latency_p95', analysis.kpis.latency_p95),
            ('latency_p99', analysis.kpis.latency_p99),
            ('cpu_usage_avg', analysis.kpis.cpu_usage_avg),
            ('memory_usage_avg', analysis.kpis.memory_usage_avg)
        ]
        
        for metric_name, current_value in metrics_to_check:
            if metric_name in baseline:
                baseline_value = baseline[metric_name].get('mean', 0)
                
                # Calculate regression thresholds
                if metric_name == 'throughput':
                    # Lower throughput is regression
                    threshold = baseline_value * 0.8  # 20% degradation
                    if current_value < threshold:
                        regressions.append({
                            'metric': metric_name,
                            'baseline': baseline_value,
                            'current': current_value,
                            'change_percent': ((current_value - baseline_value) / baseline_value) * 100,
                            'severity': 'high' if current_value < baseline_value * 0.7 else 'medium',
                            'threshold': threshold
                        })
                else:
                    # Higher values are regression for other metrics
                    threshold = baseline_value * ci_config.regression_threshold
                    if current_value > threshold:
                        regressions.append({
                            'metric': metric_name,
                            'baseline': baseline_value,
                            'current': current_value,
                            'change_percent': ((current_value - baseline_value) / baseline_value) * 100,
                            'severity': 'high' if current_value > baseline_value * 1.5 else 'medium',
                            'threshold': threshold
                        })
        
        return regressions
    
    async def _generate_ci_report(self, 
                                ci_config: CITestConfig,
                                results, 
                                analysis: PerformanceAnalysis,
                                regressions: List[Dict[str, Any]]) -> str:
        """Generate CI-specific performance report."""
        
        report_data = {
            'ci_info': {
                'test_name': ci_config.test_name,
                'commit_sha': ci_config.commit_sha,
                'branch': ci_config.branch,
                'author': ci_config.author,
                'timestamp': datetime.now().isoformat()
            },
            'performance_summary': {
                'score': analysis.score,
                'passed': analysis.passed,
                'regressions_found': len(regressions) > 0,
                'regression_count': len(regressions)
            },
            'key_metrics': {
                'throughput': analysis.kpis.throughput,
                'error_rate': analysis.kpis.error_rate,
                'latency_p95': analysis.kpis.latency_p95,
                'latency_p99': analysis.kpis.latency_p99,
                'cpu_usage': analysis.kpis.cpu_usage_avg,
                'memory_usage': analysis.kpis.memory_usage_avg
            },
            'regressions': regressions,
            'bottlenecks': [
                {
                    'type': b.type,
                    'description': b.description,
                    'severity': b.severity
                }
                for b in analysis.bottlenecks
            ],
            'recommendations': [
                {
                    'description': r.description,
                    'priority': r.priority,
                    'impact': r.estimated_impact
                }
                for r in analysis.recommendations
            ]
        }
        
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ci_report_{ci_config.commit_sha[:8]}_{timestamp}.json"
        report_path = self.results_dir / filename
        
        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Error generating CI report: {e}")
            return ""
    
    def _create_summary(self, 
                       ci_config: CITestConfig,
                       analysis: PerformanceAnalysis,
                       regressions: List[Dict[str, Any]]) -> str:
        """Create summary message for CI."""
        
        if regressions:
            regression_list = ", ".join([f"{r['metric']} ({r['change_percent']:.1f}%)" 
                                         for r in regressions])
            return (f"Performance regression detected: {regression_list}. "
                   f"Score: {analysis.score:.1f}/100")
        else:
            return (f"Performance regression check passed. "
                   f"Score: {analysis.score:.1f}/100")
    
    async def _save_ci_results(self, 
                             ci_config: CITestConfig,
                             results, 
                             analysis: PerformanceAnalysis,
                             regressions: List[Dict[str, Any]]):
        """Save CI test results for future reference."""
        
        result_data = {
            'ci_config': asdict(ci_config),
            'timestamp': datetime.now().isoformat(),
            'performance': {
                'score': analysis.score,
                'passed': analysis.passed,
                'kpis': {
                    'throughput': analysis.kpis.throughput,
                    'error_rate': analysis.kpis.error_rate,
                    'latency_p50': analysis.kpis.latency_p50,
                    'latency_p95': analysis.kpis.latency_p95,
                    'latency_p99': analysis.kpis.latency_p99,
                    'cpu_usage_avg': analysis.kpis.cpu_usage_avg,
                    'memory_usage_avg': analysis.kpis.memory_usage_avg
                },
                'regressions': regressions,
                'bottlenecks': len(analysis.bottlenecks),
                'anomalies': len(analysis.anomalies)
            }
        }
        
        filename = f"ci_result_{ci_config.commit_sha[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = self.results_dir / filename
        
        try:
            with open(file_path, 'w') as f:
                json.dump(result_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving CI results: {e}")
    
    async def update_ci_baseline(self, 
                               analysis: PerformanceAnalysis,
                               commit_sha: str):
        """Update CI baseline with new performance metrics."""
        
        baseline_data = {
            'updated_at': datetime.now().isoformat(),
            'commit_sha': commit_sha,
            'throughput': {
                'mean': analysis.kpis.throughput,
                'threshold': analysis.kpis.throughput * 0.8
            },
            'error_rate': {
                'mean': analysis.kpis.error_rate,
                'threshold': analysis.kpis.error_rate * 2.0
            },
            'latency_p95': {
                'mean': analysis.kpis.latency_p95,
                'threshold': analysis.kpis.latency_p95 * 1.2
            },
            'latency_p99': {
                'mean': analysis.kpis.latency_p99,
                'threshold': analysis.kpis.latency_p99 * 1.2
            },
            'cpu_usage_avg': {
                'mean': analysis.kpis.cpu_usage_avg,
                'threshold': analysis.kpis.cpu_usage_avg * 1.2
            },
            'memory_usage_avg': {
                'mean': analysis.kpis.memory_usage_avg,
                'threshold': analysis.kpis.memory_usage_avg * 1.2
            }
        }
        
        baseline_file = self.results_dir / "ci_baseline.json"
        
        try:
            with open(baseline_file, 'w') as f:
                json.dump(baseline_data, f, indent=2)
            
            logger.info(f"CI baseline updated with commit {commit_sha}")
            
        except Exception as e:
            logger.error(f"Error updating CI baseline: {e}")
    
    async def run_full_performance_suite(self, 
                                       commit_sha: str,
                                       branch: str,
                                       author: str) -> Dict[str, Any]:
        """Run full performance test suite for CI."""
        
        logger.info(f"Running full performance suite for commit {commit_sha}")
        
        # Create comprehensive test configuration
        test_config = TestSuiteConfig(
            scenarios=LoadScenarios.create_standard_scenarios(),
            name=f"Full Performance Suite - {commit_sha[:8]}",
            description=f"Comprehensive performance validation for commit {commit_sha}",
            max_concurrent_scenarios=1
        )
        
        try:
            # Run tests
            results = await self.test_framework.run_test_suite(test_config)
            
            # Generate summary
            summary = {
                'commit_sha': commit_sha,
                'branch': branch,
                'author': author,
                'timestamp': datetime.now().isoformat(),
                'total_scenarios': len(results.scenario_results),
                'passed_scenarios': sum(1 for a in results.scenario_results.values() if a.passed),
                'failed_scenarios': sum(1 for a in results.scenario_results.values() if not a.passed),
                'average_score': sum(a.score for a in results.scenario_results.values()) / len(results.scenario_results) if results.scenario_results else 0,
                'scenarios': {}
            }
            
            for name, analysis in results.scenario_results.items():
                summary['scenarios'][name] = {
                    'passed': analysis.passed,
                    'score': analysis.score,
                    'throughput': analysis.kpis.throughput,
                    'error_rate': analysis.kpis.error_rate,
                    'latency_p95': analysis.kpis.latency_p95
                }
            
            # Save summary
            filename = f"full_suite_{commit_sha[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = self.results_dir / filename
            
            with open(file_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Full performance suite completed: {summary['passed_scenarios']}/{summary['total_scenarios']} passed")
            
            return summary
            
        except Exception as e:
            logger.error(f"Full performance suite failed: {e}")
            return {
                'error': str(e),
                'commit_sha': commit_sha,
                'timestamp': datetime.now().isoformat()
            }