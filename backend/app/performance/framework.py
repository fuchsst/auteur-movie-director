"""
Core performance testing framework for the Function Runner Architecture.

Provides the main entry point and orchestration for running comprehensive
performance tests against the system.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from .scenarios import LoadScenario, TestSuiteConfig
from .generator import LoadGenerator
from .metrics import MetricsCollector, TestMetrics
from .analyzer import ResultAnalyzer, PerformanceAnalysis
from .report import ReportGenerator

logger = logging.getLogger(__name__)


@dataclass
class TestResults:
    """Container for comprehensive test results."""
    
    scenario_results: Dict[str, PerformanceAnalysis]
    start_time: datetime
    end_time: datetime
    total_duration: float
    environment_info: Dict[str, Any]
    
    def __init__(self):
        self.scenario_results = {}
        self.start_time = datetime.now()
        self.environment_info = {}


class PerformanceTestFramework:
    """
    Main framework for running comprehensive performance tests.
    
    This class orchestrates load generation, metrics collection,
    analysis, and reporting for performance testing scenarios.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the performance testing framework.
        
        Args:
            config: Optional configuration dictionary for customizing behavior
        """
        self.config = config or {}
        self.load_generator = LoadGenerator(self.config.get('load_generator', {}))
        self.metrics_collector = MetricsCollector(self.config.get('metrics', {}))
        self.result_analyzer = ResultAnalyzer(self.config.get('analyzer', {}))
        self.report_generator = ReportGenerator(self.config.get('reporting', {}))
        
        self.test_results = TestResults()
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging for performance testing."""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('performance_test.log'),
                logging.StreamHandler()
            ]
        )
    
    async def run_test_suite(self, config: TestSuiteConfig) -> TestResults:
        """
        Run a complete performance test suite.
        
        Args:
            config: Test suite configuration defining scenarios to run
            
        Returns:
            Comprehensive test results including analysis and reports
        """
        logger.info(f"Starting performance test suite with {len(config.scenarios)} scenarios")
        
        self.test_results = TestResults()
        self.test_results.start_time = datetime.now()
        
        try:
            # Collect environment information
            await self._collect_environment_info()
            
            # Run each test scenario
            for scenario in config.scenarios:
                logger.info(f"Running scenario: {scenario.name}")
                
                # Prepare environment
                await self._prepare_environment(scenario)
                
                # Start metrics collection
                metrics_task = asyncio.create_task(
                    self.metrics_collector.collect_during_test(scenario)
                )
                
                # Run load test
                load_results = await self.load_generator.run_scenario(scenario)
                
                # Stop metrics collection
                metrics = await metrics_task
                
                # Analyze results
                analysis = await self.result_analyzer.analyze(
                    load_results, metrics, scenario
                )
                
                self.test_results.scenario_results[scenario.name] = analysis
                
                # Log results
                self._log_scenario_results(scenario.name, analysis)
                
                # Cool down between tests
                if scenario.cooldown_seconds > 0:
                    logger.info(f"Cooling down for {scenario.cooldown_seconds} seconds")
                    await asyncio.sleep(scenario.cooldown_seconds)
            
            self.test_results.end_time = datetime.now()
            self.test_results.total_duration = (
                self.test_results.end_time - self.test_results.start_time
            ).total_seconds()
            
            # Generate comprehensive report
            await self._generate_final_report(config)
            
            logger.info("Test suite completed successfully")
            return self.test_results
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            raise
    
    async def run_single_scenario(self, scenario: LoadScenario) -> PerformanceAnalysis:
        """
        Run a single performance test scenario.
        
        Args:
            scenario: The load scenario to execute
            
        Returns:
            Performance analysis for the single scenario
        """
        logger.info(f"Running single scenario: {scenario.name}")
        
        # Prepare environment
        await self._prepare_environment(scenario)
        
        # Start metrics collection
        metrics_task = asyncio.create_task(
            self.metrics_collector.collect_during_test(scenario)
        )
        
        # Run load test
        load_results = await self.load_generator.run_scenario(scenario)
        
        # Stop metrics collection
        metrics = await metrics_task
        
        # Analyze results
        analysis = await self.result_analyzer.analyze(
            load_results, metrics, scenario
        )
        
        # Generate individual report
        await self.report_generator.generate_single_scenario_report(
            scenario, analysis
        )
        
        return analysis
    
    async def _prepare_environment(self, scenario: LoadScenario):
        """Prepare the testing environment for a scenario."""
        logger.info(f"Preparing environment for scenario: {scenario.name}")
        
        # Ensure services are healthy
        await self._verify_services_health()
        
        # Clean up any previous test data
        await self._cleanup_test_data()
        
        # Pre-warm caches if needed
        if scenario.pre_warm:
            await self._prewarm_caches()
    
    async def _verify_services_health(self):
        """Verify all required services are healthy."""
        # Implementation would check Redis, Celery workers, etc.
        logger.debug("Verifying services health")
        
    async def _cleanup_test_data(self):
        """Clean up any test data from previous runs."""
        # Implementation would clean test queues, databases, etc.
        logger.debug("Cleaning up test data")
    
    async def _prewarm_caches(self):
        """Pre-warm any caches to ensure consistent test conditions."""
        logger.debug("Pre-warming caches")
    
    async def _collect_environment_info(self):
        """Collect information about the test environment."""
        import platform
        import psutil
        
        self.test_results.environment_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_total': psutil.disk_usage('/').total,
            'test_framework_version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        }
    
    def _log_scenario_results(self, scenario_name: str, analysis: PerformanceAnalysis):
        """Log the results of a scenario."""
        logger.info(f"Scenario {scenario_name} results:")
        logger.info(f"  Passed: {analysis.passed}")
        logger.info(f"  Throughput: {analysis.kpis.throughput:.2f} tasks/sec")
        logger.info(f"  Error Rate: {analysis.kpis.error_rate:.4f}")
        logger.info(f"  Latency P95: {analysis.kpis.latency_p95:.3f}s")
        logger.info(f"  CPU Usage: {analysis.kpis.cpu_usage_avg:.1f}%")
        
        if analysis.bottlenecks:
            logger.warning(f"  Bottlenecks detected: {len(analysis.bottlenecks)}")
            for bottleneck in analysis.bottlenecks:
                logger.warning(f"    - {bottleneck.description}")
    
    async def _generate_final_report(self, config: TestSuiteConfig):
        """Generate the final comprehensive test report."""
        logger.info("Generating final test report")
        
        await self.report_generator.generate_suite_report(
            config, self.test_results
        )
    
    async def establish_baseline(self, 
                               scenario: LoadScenario, 
                               repetitions: int = 3) -> Dict[str, Any]:
        """
        Establish performance baseline for a scenario.
        
        Args:
            scenario: The scenario to baseline
            repetitions: Number of times to repeat the test
            
        Returns:
            Baseline performance metrics
        """
        logger.info(f"Establishing baseline for {scenario.name}")
        
        results = []
        
        for i in range(repetitions):
            logger.info(f"Baseline run {i+1}/{repetitions}")
            analysis = await self.run_single_scenario(scenario)
            results.append(analysis.kpis)
        
        # Calculate average and standard deviation
        baseline = self._calculate_baseline_stats(results)
        
        # Save baseline
        await self._save_baseline(scenario.name, baseline)
        
        return baseline
    
    def _calculate_baseline_stats(self, results: List) -> Dict[str, Any]:
        """Calculate baseline statistics from multiple runs."""
        import statistics
        
        metrics = {}
        
        # Calculate for each metric
        for metric_name in ['throughput', 'error_rate', 'latency_p50', 'latency_p95', 
                          'latency_p99', 'cpu_usage_avg', 'memory_usage_avg']:
            values = [getattr(result, metric_name) for result in results]
            metrics[metric_name] = {
                'mean': statistics.mean(values),
                'stddev': statistics.stdev(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values)
            }
        
        return metrics
    
    async def _save_baseline(self, scenario_name: str, baseline: Dict[str, Any]):
        """Save baseline metrics to storage."""
        baseline_dir = Path("performance_baselines")
        baseline_dir.mkdir(exist_ok=True)
        
        baseline_file = baseline_dir / f"{scenario_name}_baseline.json"
        
        import json
        with open(baseline_file, 'w') as f:
            json.dump(baseline, f, indent=2, default=str)
    
    async def load_baseline(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Load baseline metrics for a scenario."""
        baseline_file = Path(f"performance_baselines/{scenario_name}_baseline.json")
        
        if not baseline_file.exists():
            return None
        
        import json
        with open(baseline_file, 'r') as f:
            return json.load(f)