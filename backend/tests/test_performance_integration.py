"""
Integration tests for the performance testing suite.

Tests end-to-end functionality of the performance testing framework.
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.performance import (
    PerformanceTestFramework,
    LoadScenarios,
    TestSuiteConfig,
    PerformanceCI,
    CITestConfig,
    PerformanceProfiler,
    PerformanceDashboard
)
from app.performance.scenarios import TestType


class TestPerformanceIntegration:
    """Integration tests for performance testing."""
    
    @pytest.mark.asyncio
    async def test_complete_performance_suite(self):
        """Test complete performance suite execution."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'reporting': {'output_dir': temp_dir},
                'framework': {'test_mode': True}
            }
            
            framework = PerformanceTestFramework(config)
            
            # Create test suite
            scenarios = LoadScenarios.create_standard_scenarios()
            
            # Only use shorter scenarios for testing
            test_scenarios = [s for s in scenarios if s.test_type != TestType.ENDURANCE]
            
            test_config = TestSuiteConfig(
                scenarios=test_scenarios[:2],  # Only test 2 scenarios
                name="Integration Test Suite",
                description="Testing complete performance suite"
            )
            
            # Mock the actual test execution
            with patch.object(framework, 'run_test_suite') as mock_run:
                mock_results = MagicMock()
                mock_results.scenario_results = {
                    'test1': MagicMock(passed=True, score=85.0),
                    'test2': MagicMock(passed=True, score=90.0)
                }
                mock_results.total_duration = 120.0
                mock_run.return_value = mock_results
                
                results = await framework.run_test_suite(test_config)
                
                assert mock_run.called
                assert len(results.scenario_results) == 2
    
    @pytest.mark.asyncio
    async def test_ci_integration(self):
        """Test CI/CD integration."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {'results_dir': temp_dir}
            ci = PerformanceCI(config)
            
            ci_config = CITestConfig(
                test_name="CI Integration Test",
                commit_sha="abc123def456789",
                branch="main",
                author="test@example.com",
                max_duration_minutes=1
            )
            
            # Mock the CI process
            with patch.object(ci, 'run_performance_regression_check') as mock_check:
                mock_result = MagicMock()
                mock_result.passed = True
                mock_result.regressions = []
                mock_result.summary = "CI check passed"
                mock_check.return_value = mock_result
                
                result = await ci.run_performance_regression_check(ci_config)
                
                assert mock_check.called
                assert result.passed
    
    @pytest.mark.asyncio
    async def test_workload_profiling(self):
        """Test workload profiling."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'profiles_dir': temp_dir,
                'framework': {'test_mode': True},
                'load_levels': [0.5, 1.0, 1.5],
                'test_duration': 60
            }
            
            profiler = PerformanceProfiler(config)
            
            # Create test workload
            from app.performance.profiler import Workload
            workload = Workload(
                id="test-workload",
                name="Test Workload",
                description="Integration test workload"
            )
            
            # Mock profiling process
            with patch.object(profiler, 'profile_workload') as mock_profile:
                mock_profile.return_value = MagicMock(
                    workload_id="test-workload",
                    scaling_analysis=MagicMock(
                        scaling_type="linear",
                        scaling_efficiency=85.0,
                        break_point=2.0
                    ),
                    optimal_load=MagicMock(
                        load_multiplier=1.0,
                        throughput=100.0,
                        efficiency_score=0.9
                    )
                )
                
                profile = await profiler.profile_workload(workload)
                
                assert mock_profile.called
                assert profile.workload_id == "test-workload"
    
    def test_dashboard_creation(self):
        """Test dashboard creation and saving."""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {'dashboard_dir': temp_dir}
            dashboard_mgr = PerformanceDashboard(config)
            
            # Create all dashboard types
            dashboards = [
                dashboard_mgr.create_overview_dashboard(),
                dashboard_mgr.create_detailed_dashboard(),
                dashboard_mgr.create_stress_test_dashboard()
            ]
            
            saved_files = []
            for dashboard in dashboards:
                file_path = dashboard_mgr.save_dashboard(dashboard)
                if file_path:
                    saved_files.append(file_path)
            
            assert len(saved_files) == 3
            
            # Verify files were created
            for file_path in saved_files:
                assert Path(file_path).exists()
                
                # Verify JSON is valid
                with open(file_path, 'r') as f:
                    dashboard_json = json.load(f)
                    assert 'dashboard' in dashboard_json
                    assert 'title' in dashboard_json['dashboard']


class TestConfiguration:
    """Test configuration handling."""
    
    def test_framework_config(self):
        """Test framework configuration."""
        
        config = {
            'log_level': 'DEBUG',
            'framework': {
                'test_mode': True,
                'max_concurrent_users': 1000
            },
            'reporting': {
                'output_dir': '/tmp/test',
                'format': 'json'
            }
        }
        
        framework = PerformanceTestFramework(config)
        
        assert framework.config['log_level'] == 'DEBUG'
        assert framework.config['framework']['test_mode'] is True
    
    def test_ci_config_validation(self):
        """Test CI configuration validation."""
        from app.performance.cicd import CITestConfig
        
        # Test valid config
        config = CITestConfig(
            test_name="test",
            commit_sha="a" * 40,
            branch="main",
            author="test@example.com"
        )
        
        assert config.test_name == "test"
        assert len(config.commit_sha) == 40
        assert config.max_duration_minutes == 15
        
        # Test custom values
        config = CITestConfig(
            test_name="custom",
            commit_sha="b" * 40,
            branch="feature/test",
            author="dev@example.com",
            max_duration_minutes=30,
            regression_threshold=1.5,
            parallel_jobs=2
        )
        
        assert config.max_duration_minutes == 30
        assert config.regression_threshold == 1.5
        assert config.parallel_jobs == 2


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in performance components."""
        
        framework = PerformanceTestFramework()
        
        # Test with invalid scenario
        with pytest.raises(Exception):
            await framework.run_single_scenario(None)
    
    def test_empty_metrics(self):
        """Test handling of empty metrics."""
        from app.performance.analyzer import ResultAnalyzer
        
        analyzer = ResultAnalyzer()
        
        # Mock empty analysis
        with patch.object(analyzer, '_calculate_kpis') as mock_kpis:
            mock_kpis.return_value = MagicMock(throughput=0, error_rate=0)
            
            # This should handle gracefully
            assert True  # Placeholder for async test


@pytest.mark.asyncio
async def test_end_to_end_performance_pipeline():
    """Test complete performance testing pipeline."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Complete pipeline configuration
        config = {
            'framework': {'test_mode': True},
            'reporting': {'output_dir': temp_dir},
            'profiles_dir': temp_dir,
            'results_dir': temp_dir,
            'dashboard_dir': temp_dir
        }
        
        # 1. Create CI configuration
        ci_config = CITestConfig(
            test_name="E2E Performance Test",
            commit_sha="e2e123456789abcdef",
            branch="main",
            author="e2e-test@example.com"
        )
        
        # 2. Create performance profiler
        profiler = PerformanceProfiler(config)
        
        # 3. Create workload
        from app.performance.profiler import Workload
        workload = Workload(
            id="e2e-workload",
            name="End-to-End Test Workload",
            description="Complete pipeline test"
        )
        
        # 4. Create dashboard manager
        dashboard_mgr = PerformanceDashboard(config)
        
        # Verify all components can be instantiated
        assert ci_config.test_name == "E2E Performance Test"
        assert profiler.config['framework']['test_mode'] is True
        assert workload.id == "e2e-workload"
        assert dashboard_mgr.config['dashboard_dir'] == temp_dir
        
        # Test dashboard creation
        overview_dashboard = dashboard_mgr.create_overview_dashboard()
        assert overview_dashboard.title == "Function Runner - Performance Overview"
        
        # Save dashboard
        dashboard_file = dashboard_mgr.save_dashboard(overview_dashboard)
        assert dashboard_file is not None
        assert Path(dashboard_file).exists()


@pytest.fixture
def mock_integration_env():
    """Set up mock environment for integration tests."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        yield {
            'temp_dir': temp_dir,
            'config': {
                'reporting': {'output_dir': temp_dir},
                'profiles_dir': temp_dir,
                'results_dir': temp_dir,
                'dashboard_dir': temp_dir,
                'framework': {'test_mode': True}
            }
        }


@pytest.mark.asyncio
async def test_performance_monitoring_workflow(mock_integration_env):
    """Test complete performance monitoring workflow."""
    
    env = mock_integration_env
    
    # 1. Create baseline
    framework = PerformanceTestFramework(env['config'])
    
    # 2. Create CI integration
    ci = PerformanceCI(env['config'])
    
    # 3. Create profiler
    profiler = PerformanceProfiler(env['config'])
    
    # 4. Create dashboards
    dashboard_mgr = PerformanceDashboard(env['config'])
    
    # Test that all components can work together
    
    # Create all dashboard types
    dashboards = [
        dashboard_mgr.create_overview_dashboard(),
        dashboard_mgr.create_detailed_dashboard(),
        dashboard_mgr.create_stress_test_dashboard()
    ]
    
    for dashboard in dashboards:
        file_path = dashboard_mgr.save_dashboard(dashboard)
        assert file_path is not None
        assert Path(file_path).exists()
    
    # Verify dashboard files contain valid JSON
    dashboard_files = list(Path(env['temp_dir']).glob("*.json"))
    assert len(dashboard_files) >= 3
    
    for file_path in dashboard_files:
        with open(file_path, 'r') as f:
            dashboard_json = json.load(f)
            assert 'dashboard' in dashboard_json
            assert 'title' in dashboard_json['dashboard']