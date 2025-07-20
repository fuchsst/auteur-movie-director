"""
Report generation for performance testing results.

Generates comprehensive HTML and JSON reports for performance test results,
including visualizations and actionable insights.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .types import TestResults
from .analyzer import PerformanceAnalysis
from .scenarios import TestSuiteConfig

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive performance test reports."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the report generator.
        
        Args:
            config: Configuration for report generation
        """
        self.config = config or {}
        self.output_dir = Path(self.config.get('output_dir', 'performance_reports'))
        self.output_dir.mkdir(exist_ok=True)
        
        # Ensure subdirectories exist
        (self.output_dir / 'json').mkdir(exist_ok=True)
        (self.output_dir / 'html').mkdir(exist_ok=True)
        
        logger.info(f"Report generator initialized, output directory: {self.output_dir}")
    
    async def generate_suite_report(self, 
                                  config: TestSuiteConfig, 
                                  results: TestResults) -> str:
        """
        Generate comprehensive report for a complete test suite.
        
        Args:
            config: Test suite configuration
            results: Test suite results
            
        Returns:
            Path to generated report
        """
        
        report_data = {
            'suite_info': {
                'name': config.name,
                'description': config.description,
                'total_scenarios': len(config.scenarios),
                'execution_time': {
                    'start': results.start_time.isoformat(),
                    'end': results.end_time.isoformat(),
                    'duration_seconds': results.total_duration
                }
            },
            'environment': results.environment_info,
            'scenarios': {},
            'summary': {
                'total_passed': 0,
                'total_failed': 0,
                'average_score': 0.0,
                'critical_issues': []
            }
        }
        
        # Process each scenario
        total_score = 0.0
        critical_issues = []
        
        for scenario_name, analysis in results.scenario_results.items():
            scenario_data = self._format_analysis(analysis)
            report_data['scenarios'][scenario_name] = scenario_data
            
            if analysis.passed:
                report_data['summary']['total_passed'] += 1
            else:
                report_data['summary']['total_failed'] += 1
            
            total_score += analysis.score
            
            # Collect critical issues
            for bottleneck in analysis.bottlenecks:
                if bottleneck.severity == 'critical':
                    critical_issues.append({
                        'scenario': scenario_name,
                        'issue': bottleneck.description,
                        'type': bottleneck.type
                    })
            
            for anomaly in analysis.anomalies:
                if anomaly.severity == 'critical':
                    critical_issues.append({
                        'scenario': scenario_name,
                        'issue': anomaly.description,
                        'type': 'anomaly'
                    })
        
        report_data['summary']['average_score'] = (
            total_score / len(results.scenario_results) 
            if results.scenario_results else 0.0
        )
        report_data['summary']['critical_issues'] = critical_issues
        
        # Generate reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"performance_suite_{timestamp}"
        
        # JSON report
        json_path = self.output_dir / 'json' / f"{base_filename}.json"
        await self._write_json_report(report_data, json_path)
        
        # HTML report
        html_path = self.output_dir / 'html' / f"{base_filename}.html"
        await self._write_html_report(report_data, html_path)
        
        logger.info(f"Suite report generated: {json_path} and {html_path}")
        return str(html_path)
    
    async def generate_single_scenario_report(self, 
                                            scenario, 
                                            analysis: PerformanceAnalysis) -> str:
        """
        Generate report for a single scenario.
        
        Args:
            scenario: Test scenario
            analysis: Performance analysis
            
        Returns:
            Path to generated report
        """
        
        report_data = {
            'scenario': {
                'name': scenario.name,
                'description': scenario.description,
                'type': scenario.test_type.value,
                'config': {
                    'users': scenario.users,
                    'duration': scenario.duration_seconds,
                    'ramp_up': scenario.ramp_up_seconds
                }
            },
            'analysis': self._format_analysis(analysis)
        }
        
        # Generate reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"scenario_{scenario.name}_{timestamp}"
        
        json_path = self.output_dir / 'json' / f"{base_filename}.json"
        await self._write_json_report(report_data, json_path)
        
        html_path = self.output_dir / 'html' / f"{base_filename}.html"
        await self._write_html_report(report_data, html_path)
        
        logger.info(f"Scenario report generated: {html_path}")
        return str(html_path)
    
    def _format_analysis(self, analysis: PerformanceAnalysis) -> Dict[str, Any]:
        """Format analysis data for report."""
        
        return {
            'summary': {
                'passed': analysis.passed,
                'score': round(analysis.score, 1),
                'timestamp': analysis.analysis_time.isoformat()
            },
            'kpis': {
                'throughput': {
                    'value': round(analysis.kpis.throughput, 2),
                    'unit': 'tasks/sec'
                },
                'error_rate': {
                    'value': round(analysis.kpis.error_rate * 100, 2),
                    'unit': '%'
                },
                'latency': {
                    'p50': round(analysis.kpis.latency_p50, 3),
                    'p95': round(analysis.kpis.latency_p95, 3),
                    'p99': round(analysis.kpis.latency_p99, 3),
                    'unit': 'seconds'
                },
                'resources': {
                    'cpu_avg': round(analysis.kpis.cpu_usage_avg, 1),
                    'cpu_max': round(analysis.kpis.cpu_usage_max, 1),
                    'memory_avg': round(analysis.kpis.memory_usage_avg, 1),
                    'memory_max': round(analysis.kpis.memory_usage_max, 1),
                    'unit': '%'
                }
            },
            'bottlenecks': [
                {
                    'type': b.type,
                    'description': b.description,
                    'severity': b.severity,
                    'impact': b.impact,
                    'value': b.value,
                    'threshold': b.threshold,
                    'recommendations': b.recommendations
                }
                for b in analysis.bottlenecks
            ],
            'anomalies': [
                {
                    'type': a.type,
                    'description': a.description,
                    'severity': a.severity,
                    'start_time': a.start_time.isoformat(),
                    'duration': a.duration,
                    'metrics_affected': a.metrics_affected,
                    'value': a.value,
                    'expected_range': a.expected_range
                }
                for a in analysis.anomalies
            ],
            'baseline_comparisons': [
                {
                    'metric': c.metric_name,
                    'current': round(c.current_value, 3),
                    'baseline': round(c.baseline_value, 3),
                    'change_percent': round(c.change_percent, 1),
                    'status': c.status,
                    'severity': c.severity
                }
                for c in analysis.baseline_comparisons
            ],
            'recommendations': [
                {
                    'category': r.category,
                    'description': r.description,
                    'priority': r.priority,
                    'estimated_impact': r.estimated_impact,
                    'implementation_effort': r.implementation_effort,
                    'specific_actions': r.specific_actions,
                    'expected_improvement': r.expected_improvement
                }
                for r in analysis.recommendations
            ]
        }
    
    async def _write_json_report(self, report_data: Dict[str, Any], path: Path):
        """Write JSON report."""
        
        try:
            with open(path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error writing JSON report: {e}")
    
    async def _write_html_report(self, report_data: Dict[str, Any], path: Path):
        """Write HTML report with visualizations."""
        
        html_content = self._generate_html_content(report_data)
        
        try:
            with open(path, 'w') as f:
                f.write(html_content)
        except Exception as e:
            logger.error(f"Error writing HTML report: {e}")
    
    def _generate_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content for the report."""
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Test Report - {report_data['suite_info']['name']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .section {{
            padding: 20px 30px;
            border-bottom: 1px solid #eee;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}
        .severity-critical {{ color: #e74c3c; }}
        .severity-high {{ color: #f39c12; }}
        .severity-medium {{ color: #f1c40f; }}
        .severity-low {{ color: #27ae60; }}
        
        .bottleneck, .anomaly, .recommendation {{
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #ccc;
            background: #f8f9fa;
        }}
        .bottleneck.critical {{ border-left-color: #e74c3c; }}
        .bottleneck.high {{ border-left-color: #f39c12; }}
        .bottleneck.medium {{ border-left-color: #f1c40f; }}
        .bottleneck.low {{ border-left-color: #27ae60; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .status-passed {{ color: #27ae60; font-weight: bold; }}
        .status-failed {{ color: #e74c3c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Performance Test Report</h1>
            <h2>{report_data['suite_info']['name']}</h2>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>Summary</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{report_data['summary']['total_passed']}</div>
                    <div class="metric-label">Scenarios Passed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{report_data['summary']['total_failed']}</div>
                    <div class="metric-label">Scenarios Failed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{report_data['summary']['average_score']:.1f}</div>
                    <div class="metric-label">Average Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{report_data['suite_info']['total_scenarios']}</div>
                    <div class="metric-label">Total Scenarios</div>
                </div>
            </div>
        </div>
        
        <!-- Scenarios -->
        <div class="section">
            <h2>Scenario Results</h2>
            {self._generate_scenarios_html(report_data['scenarios'])}
        </div>
        
        <!-- Critical Issues -->
        {self._generate_critical_issues_html(report_data['summary']['critical_issues'])}
        
        <!-- Environment -->
        <div class="section">
            <h2>Environment</h2>
            <table>
                <tr><th>Property</th><th>Value</th></tr>
                {self._generate_environment_html(report_data['environment'])}
            </table>
        </div>
    </div>
</body>
</html>
"""
    
    def _generate_scenarios_html(self, scenarios: Dict[str, Any]) -> str:
        """Generate HTML for scenarios section."""
        
        html = ""
        for name, scenario in scenarios.items():
            status_class = "status-passed" if scenario['summary']['passed'] else "status-failed"
            
            html += f"""
            <div class="section">
                <h3>{name} <span class="{status_class}">
                    {'PASSED' if scenario['summary']['passed'] else 'FAILED'}
                </span></h3>
                <p>Score: {scenario['summary']['score']}/100</p>
                
                <h4>Key Metrics</h4>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">{scenario['kpis']['throughput']['value']}</div>
                        <div class="metric-label">Throughput (tasks/sec)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{scenario['kpis']['error_rate']['value']}%</div>
                        <div class="metric-label">Error Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{scenario['kpis']['latency']['p95']}s</div>
                        <div class="metric-label">P95 Latency</div>
                    </div>
                </div>
                
                {self._generate_bottlenecks_html(scenario['bottlenecks'])}
                {self._generate_recommendations_html(scenario['recommendations'])}
            </div>
            """
        
        return html
    
    def _generate_bottlenecks_html(self, bottlenecks: List[Dict[str, Any]]) -> str:
        """Generate HTML for bottlenecks."""
        
        if not bottlenecks:
            return ""
        
        html = "<h4>Bottlenecks</h4>"
        for bottleneck in bottlenecks:
            html += f"""
            <div class="bottleneck {bottleneck['severity']}">
                <strong>{bottleneck['type'].upper()}</strong> - {bottleneck['description']}
                <br>Value: {bottleneck['value']}, Threshold: {bottleneck['threshold']}
                <br><strong>Recommendations:</strong> {', '.join(bottleneck['recommendations'])}
            </div>
            """
        
        return html
    
    def _generate_recommendations_html(self, recommendations: List[Dict[str, Any]]) -> str:
        """Generate HTML for recommendations."""
        
        if not recommendations:
            return ""
        
        html = "<h4>Recommendations</h4>"
        for rec in recommendations:
            html += f"""
            <div class="recommendation">
                <strong>{rec['priority'].upper()}</strong> - {rec['description']}
                <br>Impact: {rec['estimated_impact']}, Effort: {rec['implementation_effort']}
                <br><strong>Actions:</strong> {', '.join(rec['specific_actions'])}
            </div>
            """
        
        return html
    
    def _generate_critical_issues_html(self, issues: List[Dict[str, Any]]) -> str:
        """Generate HTML for critical issues."""
        
        if not issues:
            return ""
        
        html = """
        <div class="section">
            <h2>Critical Issues</h2>
            <table>
                <tr><th>Scenario</th><th>Type</th><th>Issue</th></tr>
        """
        
        for issue in issues:
            html += f"""
                <tr>
                    <td>{issue['scenario']}</td>
                    <td>{issue['type']}</td>
                    <td>{issue['issue']}</td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        """
        
        return html
    
    def _generate_environment_html(self, environment: Dict[str, Any]) -> str:
        """Generate HTML for environment information."""
        
        html = ""
        for key, value in environment.items():
            html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
        
        return html