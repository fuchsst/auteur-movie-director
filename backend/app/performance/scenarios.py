"""
Load testing scenarios for the Function Runner Architecture.

Defines various load testing scenarios including baseline, stress, spike,
and endurance tests to validate system performance under different conditions.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import random


class TestType(Enum):
    """Types of performance tests."""
    BASELINE = "baseline"
    STRESS = "stress"
    SPIKE = "spike"
    ENDURANCE = "endurance"
    VOLUME = "volume"
    MIXED = "mixed"


@dataclass
class TaskProfile:
    """Defines a specific task profile for load generation."""
    
    template_id: str
    frequency: float  # tasks per user per minute
    inputs_generator: Optional[str] = None
    quality_distribution: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        if self.quality_distribution is None:
            self.quality_distribution = {'standard': 1.0}
        
        # Ensure distribution sums to 1.0
        total = sum(self.quality_distribution.values())
        if abs(total - 1.0) > 0.01:
            # Normalize
            self.quality_distribution = {
                k: v/total for k, v in self.quality_distribution.items()
            }


@dataclass
class SpikeConfig:
    """Configuration for spike testing scenarios."""
    
    spike_at_seconds: int
    spike_users: int
    spike_duration_seconds: int
    spike_ramp_seconds: int = 30


@dataclass
class PassCriteria:
    """Pass/fail criteria for performance tests."""
    
    max_error_rate: float = 0.01  # 1%
    max_latency_p50: float = 1.0  # seconds
    max_latency_p95: float = 5.0  # seconds
    max_latency_p99: float = 10.0  # seconds
    min_throughput: float = 10.0  # tasks per second
    max_cpu_usage: float = 80.0   # percent
    max_memory_usage: float = 80.0  # percent


@dataclass
class LoadScenario:
    """Complete load testing scenario definition."""
    
    name: str
    description: str
    test_type: TestType
    users: int
    duration_seconds: int
    ramp_up_seconds: int = 60
    cooldown_seconds: int = 30
    tasks: List[TaskProfile] = None
    spike_config: Optional[SpikeConfig] = None
    pass_criteria: Optional[PassCriteria] = None
    pre_warm: bool = True
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
        if self.tags is None:
            self.tags = []


@dataclass
class TestSuiteConfig:
    """Configuration for a complete test suite."""
    
    scenarios: List[LoadScenario]
    name: str = "Function Runner Performance Suite"
    description: str = "Comprehensive performance validation"
    parallel_execution: bool = False
    max_concurrent_scenarios: int = 1
    global_timeout: int = 7200  # 2 hours


class LoadScenarios:
    """Factory class for creating standard load testing scenarios."""
    
    @staticmethod
    def create_standard_scenarios() -> List[LoadScenario]:
        """Create the standard set of load testing scenarios."""
        
        return [
            LoadScenarios.create_baseline_scenario(),
            LoadScenarios.create_stress_scenario(),
            LoadScenarios.create_spike_scenario(),
            LoadScenarios.create_endurance_scenario(),
            LoadScenarios.create_mixed_workload_scenario()
        ]
    
    @staticmethod
    def create_baseline_scenario() -> LoadScenario:
        """Create baseline performance scenario."""
        
        return LoadScenario(
            name="baseline_performance",
            description="Baseline performance test with normal load",
            test_type=TestType.BASELINE,
            users=100,
            duration_seconds=600,  # 10 minutes
            ramp_up_seconds=60,
            cooldown_seconds=60,
            tasks=[
                TaskProfile(
                    template_id="image_generation_v1",
                    frequency=0.5,  # 0.5 tasks per user per minute
                    quality_distribution={'draft': 0.3, 'standard': 0.5, 'high': 0.2}
                ),
                TaskProfile(
                    template_id="text_generation_v1",
                    frequency=1.0,
                    quality_distribution={'standard': 0.7, 'high': 0.3}
                ),
                TaskProfile(
                    template_id="video_generation_v1",
                    frequency=0.1,
                    quality_distribution={'draft': 0.8, 'standard': 0.2}
                )
            ],
            pass_criteria=PassCriteria(
                max_error_rate=0.005,
                max_latency_p50=2.0,
                max_latency_p95=8.0,
                min_throughput=5.0
            ),
            tags=["baseline", "standard", "production"]
        )
    
    @staticmethod
    def create_stress_scenario() -> LoadScenario:
        """Create stress testing scenario."""
        
        return LoadScenario(
            name="stress_test",
            description="High sustained load to find system limits",
            test_type=TestType.STRESS,
            users=1000,
            duration_seconds=1800,  # 30 minutes
            ramp_up_seconds=300,
            cooldown_seconds=120,
            tasks=[
                TaskProfile(
                    template_id="image_generation_v1",
                    frequency=0.2,
                    quality_distribution={'draft': 0.7, 'standard': 0.3}
                ),
                TaskProfile(
                    template_id="text_generation_v1",
                    frequency=0.5,
                    quality_distribution={'standard': 0.8, 'draft': 0.2}
                ),
                TaskProfile(
                    template_id="audio_generation_v1",
                    frequency=0.3,
                    quality_distribution={'standard': 1.0}
                )
            ],
            pass_criteria=PassCriteria(
                max_error_rate=0.05,
                max_latency_p50=10.0,
                max_latency_p95=30.0,
                min_throughput=50.0
            ),
            tags=["stress", "limits", "capacity"]
        )
    
    @staticmethod
    def create_spike_scenario() -> LoadScenario:
        """Create spike testing scenario."""
        
        return LoadScenario(
            name="spike_test",
            description="Sudden load spike handling test",
            test_type=TestType.SPIKE,
            users=100,
            duration_seconds=900,  # 15 minutes
            ramp_up_seconds=30,
            cooldown_seconds=60,
            spike_config=SpikeConfig(
                spike_at_seconds=300,  # Spike at 5 minutes
                spike_users=500,
                spike_duration_seconds=120,
                spike_ramp_seconds=15
            ),
            tasks=[
                TaskProfile(
                    template_id="image_generation_v1",
                    frequency=0.3,
                    quality_distribution={'draft': 0.6, 'standard': 0.4}
                ),
                TaskProfile(
                    template_id="text_generation_v1",
                    frequency=0.7,
                    quality_distribution={'standard': 0.9, 'draft': 0.1}
                )
            ],
            pass_criteria=PassCriteria(
                max_error_rate=0.02,
                max_latency_p50=5.0,
                max_latency_p95=15.0,
                min_throughput=15.0
            ),
            tags=["spike", "burst", "elasticity"]
        )
    
    @staticmethod
    def create_endurance_scenario() -> LoadScenario:
        """Create endurance testing scenario."""
        
        return LoadScenario(
            name="endurance_test",
            description="Long-running stability test",
            test_type=TestType.ENDURANCE,
            users=200,
            duration_seconds=86400,  # 24 hours
            ramp_up_seconds=300,
            cooldown_seconds=300,
            tasks=[
                TaskProfile(
                    template_id="image_generation_v1",
                    frequency=0.1,
                    quality_distribution={'standard': 0.8, 'draft': 0.2}
                ),
                TaskProfile(
                    template_id="text_generation_v1",
                    frequency=0.2,
                    quality_distribution={'standard': 0.9, 'draft': 0.1}
                ),
                TaskProfile(
                    template_id="video_generation_v1",
                    frequency=0.05,
                    quality_distribution={'draft': 1.0}
                )
            ],
            pass_criteria=PassCriteria(
                max_error_rate=0.001,
                max_latency_p50=3.0,
                max_latency_p95=12.0,
                min_throughput=8.0
            ),
            tags=["endurance", "stability", "long-running"]
        )
    
    @staticmethod
    def create_mixed_workload_scenario() -> LoadScenario:
        """Create realistic mixed workload scenario."""
        
        return LoadScenario(
            name="mixed_workload",
            description="Realistic mixed workload simulation",
            test_type=TestType.MIXED,
            users=500,
            duration_seconds=3600,  # 1 hour
            ramp_up_seconds=120,
            cooldown_seconds=120,
            tasks=[
                TaskProfile(
                    template_id="image_generation_v1",
                    frequency=0.3,
                    quality_distribution={'draft': 0.4, 'standard': 0.5, 'high': 0.1}
                ),
                TaskProfile(
                    template_id="video_generation_v1",
                    frequency=0.1,
                    quality_distribution={'draft': 0.6, 'standard': 0.4}
                ),
                TaskProfile(
                    template_id="audio_generation_v1",
                    frequency=0.2,
                    quality_distribution={'standard': 0.8, 'high': 0.2}
                ),
                TaskProfile(
                    template_id="text_generation_v1",
                    frequency=0.5,
                    quality_distribution={'standard': 0.7, 'draft': 0.3}
                )
            ],
            pass_criteria=PassCriteria(
                max_error_rate=0.01,
                max_latency_p50=4.0,
                max_latency_p95=15.0,
                min_throughput=25.0
            ),
            tags=["mixed", "realistic", "production-simulation"]
        )
    
    @staticmethod
    def create_volume_scenario() -> LoadScenario:
        """Create volume testing scenario with large data."""
        
        return LoadScenario(
            name="volume_test",
            description="High volume with large input data",
            test_type=TestType.VOLUME,
            users=50,
            duration_seconds=1800,  # 30 minutes
            ramp_up_seconds=60,
            cooldown_seconds=60,
            tasks=[
                TaskProfile(
                    template_id="high_res_image_generation_v1",
                    frequency=0.1,
                    quality_distribution={'high': 1.0}
                ),
                TaskProfile(
                    template_id="long_video_generation_v1",
                    frequency=0.05,
                    quality_distribution={'standard': 1.0}
                ),
                TaskProfile(
                    template_id="complex_text_generation_v1",
                    frequency=0.2,
                    quality_distribution={'high': 0.8, 'standard': 0.2}
                )
            ],
            pass_criteria=PassCriteria(
                max_error_rate=0.02,
                max_latency_p50=20.0,
                max_latency_p95=60.0,
                min_throughput=1.0
            ),
            tags=["volume", "large-data", "resource-intensive"]
        )
    
    @staticmethod
    def create_ci_scenario() -> LoadScenario:
        """Create CI-friendly scenario with shorter duration."""
        
        return LoadScenario(
            name="ci_quick_test",
            description="Quick CI performance regression check",
            test_type=TestType.BASELINE,
            users=50,
            duration_seconds=300,  # 5 minutes
            ramp_up_seconds=30,
            cooldown_seconds=30,
            tasks=[
                TaskProfile(
                    template_id="image_generation_v1",
                    frequency=0.2,
                    quality_distribution={'standard': 0.8, 'draft': 0.2}
                ),
                TaskProfile(
                    template_id="text_generation_v1",
                    frequency=0.4,
                    quality_distribution={'standard': 1.0}
                )
            ],
            pass_criteria=PassCriteria(
                max_error_rate=0.01,
                max_latency_p50=3.0,
                max_latency_p95=10.0,
                min_throughput=5.0
            ),
            tags=["ci", "quick", "regression"]
        )
    
    @staticmethod
    def create_custom_scenario(config: Dict[str, Any]) -> LoadScenario:
        """Create a custom scenario from configuration."""
        
        return LoadScenario(
            name=config.get('name', 'custom_scenario'),
            description=config.get('description', 'Custom performance test'),
            test_type=TestType(config.get('test_type', 'baseline')),
            users=config.get('users', 100),
            duration_seconds=config.get('duration_seconds', 600),
            ramp_up_seconds=config.get('ramp_up_seconds', 60),
            cooldown_seconds=config.get('cooldown_seconds', 30),
            tasks=[
                TaskProfile(**task_config)
                for task_config in config.get('tasks', [])
            ],
            pass_criteria=PassCriteria(**config.get('pass_criteria', {})),
            tags=config.get('tags', ['custom'])
        )