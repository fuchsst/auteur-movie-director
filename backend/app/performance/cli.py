"""
Command-line interface for performance testing.

Provides CLI commands for running performance tests and managing performance data.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import uvloop

from .framework import PerformanceTestFramework
from .scenarios import LoadScenarios, TestSuiteConfig
from .cicd import PerformanceCI, CITestConfig
from .profiler import PerformanceProfiler, Workload
from .dashboard import PerformanceDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use uvloop for better async performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file')
@click.pass_context
def cli(ctx, verbose, config):
    """Performance testing CLI for Function Runner Architecture."""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration if provided
    if config:
        with open(config, 'r') as f:
            ctx.obj['config'] = json.load(f)
    else:
        ctx.obj['config'] = {}


@cli.command()
@click.option('--scenario', '-s', default='baseline', 
              type=click.Choice(['baseline', 'stress', 'spike', 'endurance', 'mixed', 'ci']),
              help='Test scenario to run')
@click.option('--users', '-u', type=int, help='Number of concurrent users')
@click.option('--duration', '-d', type=int, help='Test duration in seconds')
@click.option('--output', '-o', type=click.Path(), help='Output directory for reports')
@click.pass_context
def run_scenario(ctx, scenario, users, duration, output):
    """Run a specific performance test scenario."""
    
    config = ctx.obj['config']
    if output:
        config.setdefault('reporting', {})['output_dir'] = output
    
    async def _run():
        framework = PerformanceTestFramework(config)
        
        # Create scenario
        scenario_map = {
            'baseline': LoadScenarios.create_baseline_scenario,
            'stress': LoadScenarios.create_stress_scenario,
            'spike': LoadScenarios.create_spike_scenario,
            'endurance': LoadScenarios.create_endurance_scenario,
            'mixed': LoadScenarios.create_mixed_workload_scenario,
            'ci': LoadScenarios.create_ci_scenario
        }
        
        load_scenario = scenario_map[scenario]()
        
        # Override parameters if provided
        if users:
            load_scenario.users = users
        if duration:
            load_scenario.duration_seconds = duration
        
        click.echo(f"Running {scenario} scenario...")
        click.echo(f"  Users: {load_scenario.users}")
        click.echo(f"  Duration: {load_scenario.duration_seconds}s")
        
        try:
            analysis = await framework.run_single_scenario(load_scenario)
            click.echo(f"\nResults:")
            click.echo(f"  Score: {analysis.score:.1f}/100")
            click.echo(f"  Throughput: {analysis.kpis.throughput:.2f} tasks/sec")
            click.echo(f"  Error Rate: {analysis.kpis.error_rate*100:.2f}%")
            click.echo(f"  Latency P95: {analysis.kpis.latency_p95:.3f}s")
            click.echo(f"  Passed: {'✓' if analysis.passed else '✗'}")
            
            if analysis.bottlenecks:
                click.echo(f"  Bottlenecks: {len(analysis.bottlenecks)}")
                for bottleneck in analysis.bottlenecks:
                    click.echo(f"    - {bottleneck.type}: {bottleneck.description}")
            
        except Exception as e:
            click.echo(f"Error running scenario: {e}", err=True)
            raise click.Abort()
    
    asyncio.run(_run())


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output directory for reports')
@click.option('--exclude', '-e', multiple=True, 
              type=click.Choice(['endurance', 'volume']),
              help='Exclude specific test types')
@click.pass_context
def run_suite(ctx, output, exclude):
    """Run complete performance test suite."""
    
    config = ctx.obj['config']
    if output:
        config.setdefault('reporting', {})['output_dir'] = output
    
    async def _run():
        framework = PerformanceTestFramework(config)
        
        # Create standard scenarios
        scenarios = LoadScenarios.create_standard_scenarios()
        
        # Exclude specific types if requested
        if exclude:
            scenarios = [s for s in scenarios if s.test_type.value not in exclude]
        
        test_config = TestSuiteConfig(
            scenarios=scenarios,
            name="Complete Performance Suite",
            description="Comprehensive performance validation"
        )
        
        click.echo("Running complete performance test suite...")
        click.echo(f"Scenarios to run: {len(scenarios)}")
        
        try:
            results = await framework.run_test_suite(test_config)
            
            passed = sum(1 for a in results.scenario_results.values() if a.passed)
            total = len(results.scenario_results)
            
            click.echo(f"\nSuite Results:")
            click.echo(f"  Passed: {passed}/{total}")
            click.echo(f"  Duration: {results.total_duration:.1f}s")
            click.echo(f"  Average Score: {sum(a.score for a in results.scenario_results.values())/total:.1f}/100")
            
        except Exception as e:
            click.echo(f"Error running suite: {e}", err=True)
            raise click.Abort()
    
    asyncio.run(_run())


@cli.command()
@click.option('--commit-sha', required=True, help='Git commit SHA')
@click.option('--branch', default='main', help='Git branch')
@click.option('--author', default='unknown', help='Commit author')
@click.option('--name', default='CI Performance Check', help='Test name')
@click.option('--max-duration', type=int, default=15, help='Max test duration (minutes)')
@click.option('--no-fail', is_flag=True, help='Don\'t fail on regression')
@click.pass_context
def ci_check(ctx, commit_sha, branch, author, name, max_duration, no_fail):
    """Run CI performance regression check."""
    
    config = ctx.obj['config']
    
    async def _run():
        ci = PerformanceCI(config)
        
        ci_config = CITestConfig(
            test_name=name,
            commit_sha=commit_sha,
            branch=branch,
            author=author,
            max_duration_minutes=max_duration,
            fail_on_regression=not no_fail
        )
        
        click.echo(f"Running CI performance check for commit {commit_sha[:8]}...")
        
        try:
            result = await ci.run_performance_regression_check(ci_config)
            
            click.echo(f"\nCI Results:")
            click.echo(f"  Status: {'PASSED' if result.passed else 'FAILED'}")
            click.echo(f"  Report: {result.report_path}")
            click.echo(f"  Summary: {result.summary}")
            
            if not result.passed:
                click.echo(f"  Regressions: {len(result.regressions)}")
                for regression in result.regressions:
                    click.echo(f"    - {regression['metric']}: {regression['change_percent']:.1f}%")
            
            if not result.passed and not no_fail:
                raise click.Abort()
                
        except Exception as e:
            click.echo(f"Error running CI check: {e}", err=True)
            raise click.Abort()
    
    asyncio.run(_run())


@cli.command()
@click.option('--workload-id', required=True, help='Workload identifier')
@click.option('--workload-name', default='unnamed', help='Workload name')
@click.option('--load-levels', default='0.25,0.5,0.75,1.0,1.25,1.5,2.0', 
              help='Load levels to test (comma-separated)')
@click.option('--duration', type=int, default=300, help='Test duration per level (seconds)')
@click.pass_context
def profile_workload(ctx, workload_id, workload_name, load_levels, duration):
    """Create performance profile for a workload."""
    
    config = ctx.obj['config']
    
    async def _run():
        profiler = PerformanceProfiler(config)
        
        # Parse load levels
        levels = [float(x.strip()) for x in load_levels.split(',')]
        profiler.load_levels = levels
        profiler.test_duration = duration
        
        # Create workload
        workload = Workload(
            id=workload_id,
            name=workload_name,
            description=f"Performance profile for {workload_name}"
        )
        
        click.echo(f"Creating performance profile for {workload_name}...")
        click.echo(f"Load levels: {levels}")
        click.echo(f"Duration per level: {duration}s")
        
        try:
            profile = await profiler.profile_workload(workload)
            
            click.echo(f"\nProfile Results:")
            click.echo(f"  Scaling Type: {profile.scaling_analysis.scaling_type}")
            click.echo(f"  Scaling Efficiency: {profile.scaling_analysis.scaling_efficiency:.1f}%")
            click.echo(f"  Max Throughput: {profile.max_throughput:.2f} tasks/sec")
            click.echo(f"  Break Point: {profile.scaling_analysis.break_point}x load")
            click.echo(f"  Optimal Range: {profile.scaling_analysis.optimal_range}")
            
            click.echo(f"\nResource Limits:")
            click.echo(f"  CPU: {profile.resource_limits.cpu_limit:.1f}%")
            click.echo(f"  Memory: {profile.resource_limits.memory_limit:.1f}%")
            click.echo(f"  Concurrent Tasks: {profile.resource_limits.concurrent_task_limit}")
            
        except Exception as e:
            click.echo(f"Error profiling workload: {e}", err=True)
            raise click.Abort()
    
    asyncio.run(_run())


@cli.command()
@click.option('--type', 'dashboard_type', 
              type=click.Choice(['overview', 'detailed', 'stress']),
              default='overview', help='Dashboard type')
@click.option('--output-dir', type=click.Path(), help='Output directory for dashboards')
def create_dashboard(dashboard_type, output_dir):
    """Create Grafana dashboard configuration."""
    
    config = {}
    if output_dir:
        config['dashboard_dir'] = output_dir
    
    dashboard_mgr = PerformanceDashboard(config)
    
    # Create requested dashboard
    dashboard_map = {
        'overview': dashboard_mgr.create_overview_dashboard,
        'detailed': dashboard_mgr.create_detailed_dashboard,
        'stress': dashboard_mgr.create_stress_test_dashboard
    }
    
    dashboard = dashboard_map[dashboard_type]()
    file_path = dashboard_mgr.save_dashboard(dashboard)
    
    if file_path:
        click.echo(f"Dashboard created: {file_path}")
    else:
        click.echo("Error creating dashboard", err=True)
        raise click.Abort()


@cli.command()
@click.option('--baseline-file', type=click.Path(), help='Baseline file to update')
@click.option('--commit-sha', required=True, help='Git commit SHA')
@click.pass_context
def update_baseline(ctx, baseline_file, commit_sha):
    """Update performance baseline."""
    
    config = ctx.obj['config']
    if baseline_file:
        config.setdefault('ci', {})['baseline_file'] = baseline_file
    
    # This would typically run a full suite and update baseline
    click.echo("Baseline update functionality - run full suite and save results")
    click.echo(f"Commit: {commit_sha}")


if __name__ == '__main__':
    cli()