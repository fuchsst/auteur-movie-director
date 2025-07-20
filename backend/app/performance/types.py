"""
Type definitions for performance testing framework.

This module contains all shared type definitions to prevent circular imports.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TestMetrics:
    """Metrics collected during performance testing."""
    
    scenario_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    average_latency: float
    p95_latency: float
    p99_latency: float
    throughput_per_second: float
    error_rate: float
    resource_usage: Dict[str, Any]
    error_details: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat()
        }


@dataclass
class TestResults:
    """Results from a complete performance test run."""
    
    test_name: str
    config: Dict[str, Any]
    metrics: TestMetrics
    raw_data: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "config": self.config,
            "metrics": self.metrics.to_dict(),
            "raw_data": self.raw_data,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PerformanceAnalysis:
    """Analysis results from performance testing."""
    
    baseline_comparison: Dict[str, Any]
    bottleneck_analysis: Dict[str, Any]
    scaling_recommendations: List[str]
    resource_optimization: Dict[str, Any]
    regression_indicators: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)