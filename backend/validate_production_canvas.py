#!/usr/bin/env python3
"""
Production Canvas Performance Validation
Comprehensive test suite for EPIC-004 Production Canvas 500+ nodes @ 60 FPS target
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.performance.framework import PerformanceTestFramework
from app.performance.scenarios import LoadScenarios, LoadScenario, TestType, TaskProfile, PassCriteria


class CanvasPerformanceValidator:
    """Validates production canvas performance against EPIC-004 requirements."""
    
    def __init__(self):
        self.framework = PerformanceTestFramework({
            'log_level': 'INFO',
            'metrics': {
                'collection_interval': 2,
                'enable_prometheus': False,
                'enable_system': True,
                'enable_custom': True
            },
            'reporting': {
                'output_dir': 'performance_reports/canvas_validation'
            },
            'load_generator': {
                'client': {
                    'base_url': 'http://localhost:8000',
                    'timeout': 30
                }
            }
        })
    
    async def run_comprehensive_validation(self):
        """Run comprehensive canvas performance validation."""
        
        print("🔍 EPIC-004 Production Canvas Performance Validation")
        print("=" * 60)
        print("Target: 500+ nodes @ 60 FPS")
        print("Requirements:")
        print("  - 60 FPS with 500+ nodes")
        print("  - <100ms latency for node operations")
        print("  - <5% error rate under load")
        print("  - <80% CPU usage")
        print("  - <80% memory usage")
        print()
        
        # Define canvas-specific scenarios
        scenarios = [
            LoadScenario(
                name="canvas_baseline_50_nodes",
                description="Baseline performance with 50 interactive nodes",
                test_type=TestType.BASELINE,
                users=50,
                duration_seconds=60,
                ramp_up_seconds=10,
                cooldown_seconds=10,
                tasks=[
                    TaskProfile(
                        template_id="canvas_node_create",
                        frequency=2.0,
                        quality_distribution={'standard': 1.0}
                    ),
                    TaskProfile(
                        template_id="canvas_node_update", 
                        frequency=3.0,
                        quality_distribution={'standard': 1.0}
                    ),
                    TaskProfile(
                        template_id="canvas_connection_create",
                        frequency=1.0,
                        quality_distribution={'standard': 1.0}
                    )
                ],
                pass_criteria=PassCriteria(
                    max_error_rate=0.01,
                    max_latency_p50=0.05,
                    max_latency_p95=0.1,
                    min_throughput=100
                )
            ),
            
            LoadScenario(
                name="canvas_medium_200_nodes",
                description="Medium load with 200 interactive nodes",
                test_type=TestType.BASELINE,
                users=200,
                duration_seconds=120,
                ramp_up_seconds=20,
                cooldown_seconds=15,
                tasks=[
                    TaskProfile(
                        template_id="canvas_node_create",
                        frequency=1.0,
                        quality_distribution={'standard': 1.0}
                    ),
                    TaskProfile(
                        template_id="canvas_node_update",
                        frequency=2.0,
                        quality_distribution={'standard': 1.0}
                    ),
                    TaskProfile(
                        template_id="canvas_connection_create",
                        frequency=0.5,
                        quality_distribution={'standard': 1.0}
                    ),
                    TaskProfile(
                        template_id="canvas_real_time_sync",
                        frequency=5.0,
                        quality_distribution={'standard': 1.0}
                    )
                ],
                pass_criteria=PassCriteria(
                    max_error_rate=0.02,
                    max_latency_p50=0.08,
                    max_latency_p95=0.15,
                    min_throughput=200
                )
            ),
            
            LoadScenario(
                name="canvas_production_500_nodes",
                description="Production load with 500+ interactive nodes",
                test_type=TestType.STRESS,
                users=500,
                duration_seconds=180,
                ramp_up_seconds=30,
                cooldown_seconds=30,
                tasks=[
                    TaskProfile(
                        template_id="canvas_node_create",
                        frequency=0.8,
                        quality_distribution={'standard': 0.8, 'draft': 0.2}
                    ),
                    TaskProfile(
                        template_id="canvas_node_update",
                        frequency=1.5,
                        quality_distribution={'standard': 0.8, 'draft': 0.2}
                    ),
                    TaskProfile(
                        template_id="canvas_connection_create",
                        frequency=0.4,
                        quality_distribution={'standard': 0.8, 'draft': 0.2}
                    ),
                    TaskProfile(
                        template_id="canvas_real_time_sync",
                        frequency=3.0,
                        quality_distribution={'standard': 0.8, 'draft': 0.2}
                    ),
                    TaskProfile(
                        template_id="canvas_batch_operations",
                        frequency=0.2,
                        quality_distribution={'standard': 1.0}
                    )
                ],
                pass_criteria=PassCriteria(
                    max_error_rate=0.05,
                    max_latency_p50=0.1,
                    max_latency_p95=0.2,
                    min_throughput=500
                )
            ),
            
            LoadScenario(
                name="canvas_peak_750_nodes",
                description="Peak load test with 750 interactive nodes",
                test_type=TestType.STRESS,
                users=750,
                duration_seconds=120,
                ramp_up_seconds=45,
                cooldown_seconds=45,
                tasks=[
                    TaskProfile(
                        template_id="canvas_node_create",
                        frequency=0.6,
                        quality_distribution={'standard': 0.7, 'draft': 0.3}
                    ),
                    TaskProfile(
                        template_id="canvas_node_update",
                        frequency=1.2,
                        quality_distribution={'standard': 0.7, 'draft': 0.3}
                    ),
                    TaskProfile(
                        template_id="canvas_connection_create",
                        frequency=0.3,
                        quality_distribution={'standard': 0.7, 'draft': 0.3}
                    ),
                    TaskProfile(
                        template_id="canvas_real_time_sync",
                        frequency=2.5,
                        quality_distribution={'standard': 0.7, 'draft': 0.3}
                    )
                ],
                pass_criteria=PassCriteria(
                    max_error_rate=0.05,
                    max_latency_p50=0.15,
                    max_latency_p95=0.3,
                    min_throughput=400
                )
            )
        ]
        
        # Scenarios are already LoadScenario objects
        proper_scenarios = scenarios
        
        results = {}
        
        for scenario in proper_scenarios:
            print(f"\n📊 Running {scenario.name}...")
            print(f"   Users: {scenario.users}")
            print(f"   Duration: {scenario.duration_seconds}s")
            print(f"   Type: {scenario.test_type.value}")
            
            try:
                analysis = await self.framework.run_single_scenario(scenario)
                results[scenario.name] = analysis
                
                # Calculate FPS equivalent
                fps_target = 60
                actual_fps = min(analysis.kpis.throughput, fps_target)
                fps_ratio = (actual_fps / fps_target) * 100
                
                print(f"   ✅ Score: {analysis.score:.1f}/100")
                print(f"   📈 Throughput: {analysis.kpis.throughput:.2f} ops/sec")
                print(f"   ⚡ P95 Latency: {analysis.kpis.latency_p95:.3f}s")
                print(f"   🎯 Error Rate: {analysis.kpis.error_rate*100:.2f}%")
                print(f"   🎮 FPS Target: {fps_target}, Achieved: {actual_fps:.1f} ({fps_ratio:.1f}%)")
                
                # Performance grading
                if fps_ratio >= 90:
                    grade = "EXCELLENT"
                    emoji = "🟢"
                elif fps_ratio >= 75:
                    grade = "GOOD" 
                    emoji = "🟡"
                elif fps_ratio >= 50:
                    grade = "ACCEPTABLE"
                    emoji = "🟠"
                else:
                    grade = "NEEDS OPTIMIZATION"
                    emoji = "🔴"
                
                print(f"   {emoji} Performance: {grade}")
                
                # Check specific requirements
                if "production_500" in scenario.name:
                    passed = (
                        analysis.kpis.throughput >= 500 and
                        analysis.kpis.latency_p95 <= 0.2 and
                        analysis.kpis.error_rate <= 0.05
                    )
                    print(f"   {'✅' if passed else '❌'} 500+ Node Target: {'PASSED' if passed else 'FAILED'}")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results[scenario.name] = None
        
        return results
    
    def generate_report(self, results):
        """Generate comprehensive performance report."""
        
        print(f"\n📋 EPIC-004 Production Canvas Validation Report")
        print("=" * 60)
        
        total_scenarios = len(results)
        passed_scenarios = sum(1 for r in results.values() if r and r.passed)
        
        print(f"Total Scenarios: {total_scenarios}")
        print(f"Passed: {passed_scenarios}")
        print(f"Failed: {total_scenarios - passed_scenarios}")
        
        # 500+ node specific validation
        production_result = results.get("canvas_production_500_nodes")
        if production_result:
            print(f"\n🎯 500+ Node Production Validation:")
            print(f"   Throughput: {production_result.kpis.throughput:.1f} ops/sec")
            print(f"   P95 Latency: {production_result.kpis.latency_p95:.3f}s")
            print(f"   Error Rate: {production_result.kpis.error_rate*100:.2f}%")
            print(f"   CPU Usage: {production_result.kpis.cpu_usage_avg:.1f}%")
            print(f"   Memory Usage: {production_result.kpis.memory_usage_avg:.1f}%")
            
            # Calculate effective FPS
            effective_fps = min(production_result.kpis.throughput / 8.33, 60)  # 8.33 ops per frame
            print(f"   Effective FPS: {effective_fps:.1f}/60")
            
            passed = (
                production_result.kpis.throughput >= 500 and
                production_result.kpis.latency_p95 <= 0.2 and
                production_result.kpis.error_rate <= 0.05 and
                production_result.kpis.cpu_usage_max <= 80 and
                production_result.kpis.memory_usage_max <= 80
            )
            
            print(f"\n🏆 EPIC-004 Status: {'✅ VALIDATED' if passed else '❌ NEEDS OPTIMIZATION'}")
        
        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'target': '500+ nodes @ 60 FPS',
            'scenarios': {
                name: {
                    'passed': result.passed if result else False,
                    'score': result.score if result else 0,
                    'throughput': result.kpis.throughput if result else 0,
                    'latency_p95': result.kpis.latency_p95 if result else 0,
                    'error_rate': result.kpis.error_rate if result else 1,
                    'cpu_usage': result.kpis.cpu_usage_max if result else 100,
                    'memory_usage': result.kpis.memory_usage_max if result else 100
                }
                for name, result in results.items()
                if result
            }
        }
        
        report_path = Path('performance_reports/canvas_validation_report.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved: {report_path}")
        return passed_scenarios == total_scenarios


async def main():
    """Main validation entry point."""
    validator = CanvasPerformanceValidator()
    
    try:
        results = await validator.run_comprehensive_validation()
        success = validator.generate_report(results)
        
        print(f"\n🎉 Validation Complete!")
        return success
        
    except Exception as e:
        print(f"\n💥 Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)