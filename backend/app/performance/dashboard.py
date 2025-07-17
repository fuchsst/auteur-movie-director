"""
Performance monitoring dashboards for real-time metrics visualization.

Provides integration with Grafana for creating and managing performance
dashboards that display real-time metrics during testing and production.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DashboardPanel:
    """Configuration for a Grafana dashboard panel."""
    
    title: str
    type: str  # 'graph', 'singlestat', 'table', 'heatmap', etc.
    targets: List[Dict[str, str]]
    grid_pos: Dict[str, int]  # x, y, w, h
    options: Optional[Dict[str, Any]] = None
    thresholds: Optional[List[Dict[str, Any]]] = None


@dataclass
class Dashboard:
    """Complete dashboard configuration."""
    
    title: str
    panels: List[DashboardPanel]
    tags: List[str]
    refresh: str = "30s"
    timezone: str = "browser"
    time_from: str = "now-1h"
    time_to: str = "now"


class PerformanceDashboard:
    """Manages performance monitoring dashboards."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the dashboard manager.
        
        Args:
            config: Configuration for dashboard management
        """
        self.config = config or {}
        self.grafana_url = self.config.get('grafana_url', 'http://localhost:3000')
        self.datasource_name = self.config.get('datasource_name', 'Prometheus')
        self.dashboard_dir = Path(self.config.get('dashboard_dir', 'grafana_dashboards'))
        self.dashboard_dir.mkdir(exist_ok=True)
        
        logger.info(f"Performance dashboard manager initialized")
    
    def create_overview_dashboard(self) -> Dashboard:
        """Create overview dashboard with key metrics."""
        
        panels = [
            DashboardPanel(
                title="Task Throughput",
                type="graph",
                targets=[
                    {
                        "expr": "rate(task_submitted_total[1m])",
                        "legendFormat": "Tasks Submitted"
                    },
                    {
                        "expr": "rate(task_completed_total[1m])",
                        "legendFormat": "Tasks Completed"
                    },
                    {
                        "expr": "rate(task_errors_total[1m])",
                        "legendFormat": "Tasks Failed"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 12, "h": 8}
            ),
            DashboardPanel(
                title="Latency Percentiles",
                type="graph",
                targets=[
                    {
                        "expr": "histogram_quantile(0.5, task_submit_latency_seconds)",
                        "legendFormat": "p50"
                    },
                    {
                        "expr": "histogram_quantile(0.95, task_submit_latency_seconds)",
                        "legendFormat": "p95"
                    },
                    {
                        "expr": "histogram_quantile(0.99, task_submit_latency_seconds)",
                        "legendFormat": "p99"
                    }
                ],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 8}
            ),
            DashboardPanel(
                title="Queue Depth",
                type="graph",
                targets=[
                    {
                        "expr": "celery_queue_length",
                        "legendFormat": "Queue Length"
                    }
                ],
                grid_pos={"x": 0, "y": 8, "w": 8, "h": 8}
            ),
            DashboardPanel(
                title="Active Workers",
                type="graph",
                targets=[
                    {
                        "expr": "worker_pool_active_count",
                        "legendFormat": "Active Workers"
                    }
                ],
                grid_pos={"x": 8, "y": 8, "w": 8, "h": 8}
            ),
            DashboardPanel(
                title="System Resources",
                type="graph",
                targets=[
                    {
                        "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[1m])) * 100)",
                        "legendFormat": "CPU Usage %"
                    },
                    {
                        "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
                        "legendFormat": "Memory Usage %"
                    }
                ],
                grid_pos={"x": 16, "y": 8, "w": 8, "h": 8}
            ),
            DashboardPanel(
                title="Error Rate",
                type="singlestat",
                targets=[
                    {
                        "expr": "rate(task_errors_total[1m]) / rate(task_submitted_total[1m]) * 100",
                        "legendFormat": "Error Rate %"
                    }
                ],
                grid_pos={"x": 0, "y": 16, "w": 6, "h": 4},
                options={
                    "colorMode": "value",
                    "fieldOptions": {
                        "calcs": ["last"],
                        "defaults": {
                            "unit": "percent"
                        }
                    }
                },
                thresholds=[
                    {"color": "green", "value": 0},
                    {"color": "yellow", "value": 1},
                    {"color": "red", "value": 5}
                ]
            ),
            DashboardPanel(
                title="Current Throughput",
                type="singlestat",
                targets=[
                    {
                        "expr": "rate(task_completed_total[1m])",
                        "legendFormat": "Tasks/sec"
                    }
                ],
                grid_pos={"x": 6, "y": 16, "w": 6, "h": 4},
                options={
                    "colorMode": "value",
                    "fieldOptions": {
                        "calcs": ["last"],
                        "defaults": {
                            "unit": "reqps"
                        }
                    }
                }
            )
        ]
        
        return Dashboard(
            title="Function Runner - Performance Overview",
            panels=panels,
            tags=["performance", "function-runner", "overview"]
        )
    
    def create_detailed_dashboard(self) -> Dashboard:
        """Create detailed dashboard with comprehensive metrics."""
        
        panels = [
            # Template-specific metrics
            DashboardPanel(
                title="Template Usage",
                type="graph",
                targets=[
                    {
                        "expr": "increase(task_submitted_total{template_id=\"image_generation_v1\"}[1m])",
                        "legendFormat": "Image Generation"
                    },
                    {
                        "expr": "increase(task_submitted_total{template_id=\"text_generation_v1\"}[1m])",
                        "legendFormat": "Text Generation"
                    },
                    {
                        "expr": "increase(task_submitted_total{template_id=\"video_generation_v1\"}[1m])",
                        "legendFormat": "Video Generation"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 12, "h": 8}
            ),
            
            # Quality distribution
            DashboardPanel(
                title="Quality Distribution",
                type="graph",
                targets=[
                    {
                        "expr": "increase(task_submitted_total{quality=\"draft\"}[1m])",
                        "legendFormat": "Draft"
                    },
                    {
                        "expr": "increase(task_submitted_total{quality=\"standard\"}[1m])",
                        "legendFormat": "Standard"
                    },
                    {
                        "expr": "increase(task_submitted_total{quality=\"high\"}[1m])",
                        "legendFormat": "High"
                    }
                ],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 8}
            ),
            
            # Worker performance
            DashboardPanel(
                title="Worker Performance",
                type="graph",
                targets=[
                    {
                        "expr": "worker_task_processing_time_seconds",
                        "legendFormat": "Processing Time"
                    },
                    {
                        "expr": "worker_memory_usage_percent",
                        "legendFormat": "Memory Usage %"
                    },
                    {
                        "expr": "worker_cpu_usage_percent",
                        "legendFormat": "CPU Usage %"
                    }
                ],
                grid_pos={"x": 0, "y": 8, "w": 12, "h": 8}
            ),
            
            # Error analysis
            DashboardPanel(
                title="Error Analysis",
                type="graph",
                targets=[
                    {
                        "expr": "increase(task_errors_total{error_type=\"timeout\"}[1m])",
                        "legendFormat": "Timeouts"
                    },
                    {
                        "expr": "increase(task_errors_total{error_type=\"validation\"}[1m])",
                        "legendFormat": "Validation Errors"
                    },
                    {
                        "expr": "increase(task_errors_total{error_type=\"resource\"}[1m])",
                        "legendFormat": "Resource Errors"
                    }
                ],
                grid_pos={"x": 12, "y": 8, "w": 12, "h": 8}
            ),
            
            # Resource heatmap
            DashboardPanel(
                title="Resource Usage Heatmap",
                type="heatmap",
                targets=[
                    {
                        "expr": "worker_resource_usage_percent",
                        "legendFormat": "Resource Usage"
                    }
                ],
                grid_pos={"x": 0, "y": 16, "w": 24, "h": 8}
            )
        ]
        
        return Dashboard(
            title="Function Runner - Detailed Performance",
            panels=panels,
            tags=["performance", "function-runner", "detailed"]
        )
    
    def create_stress_test_dashboard(self) -> Dashboard:
        """Create dashboard optimized for stress testing."""
        
        panels = [
            # Stress indicators
            DashboardPanel(
                title="System Load",
                type="graph",
                targets=[
                    {
                        "expr": "node_load1",
                        "legendFormat": "Load 1min"
                    },
                    {
                        "expr": "node_load5",
                        "legendFormat": "Load 5min"
                    },
                    {
                        "expr": "node_load15",
                        "legendFormat": "Load 15min"
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 12, "h": 8}
            ),
            
            # Memory pressure
            DashboardPanel(
                title="Memory Pressure",
                type="graph",
                targets=[
                    {
                        "expr": "node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100",
                        "legendFormat": "Available Memory %"
                    }
                ],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 8}
            ),
            
            # Disk I/O
            DashboardPanel(
                title="Disk I/O",
                type="graph",
                targets=[
                    {
                        "expr": "rate(node_disk_io_time_seconds_total[1m]) * 100",
                        "legendFormat": "I/O Utilization %"
                    }
                ],
                grid_pos={"x": 0, "y": 8, "w": 24, "h": 8}
            ),
            
            # Network saturation
            DashboardPanel(
                title="Network Saturation",
                type="graph",
                targets=[
                    {
                        "expr": "rate(node_network_receive_bytes_total[1m])",
                        "legendFormat": "Receive"
                    },
                    {
                        "expr": "rate(node_network_transmit_bytes_total[1m])",
                        "legendFormat": "Transmit"
                    }
                ],
                grid_pos={"x": 0, "y": 16, "w": 24, "h": 8}
            )
        ]
        
        return Dashboard(
            title="Function Runner - Stress Test",
            panels=panels,
            tags=["performance", "function-runner", "stress-test"],
            refresh="5s"
        )
    
    def generate_dashboard_json(self, dashboard: Dashboard) -> str:
        """Generate Grafana dashboard JSON configuration."""
        
        dashboard_json = {
            "dashboard": {
                "id": None,
                "title": dashboard.title,
                "tags": dashboard.tags,
                "timezone": dashboard.timezone,
                "refresh": dashboard.refresh,
                "time": {
                    "from": dashboard.time_from,
                    "to": dashboard.time_to
                },
                "panels": []
            },
            "folderId": 0,
            "overwrite": True
        }
        
        for i, panel in enumerate(dashboard.panels):
            panel_json = {
                "id": i + 1,
                "title": panel.title,
                "type": panel.type,
                "targets": panel.targets,
                "gridPos": panel.grid_pos,
                "datasource": self.datasource_name
            }
            
            if panel.options:
                panel_json.update(panel.options)
            
            if panel.thresholds:
                panel_json["thresholds"] = panel.thresholds
            
            dashboard_json["dashboard"]["panels"].append(panel_json)
        
        return json.dumps(dashboard_json, indent=2)
    
    def save_dashboard(self, dashboard: Dashboard, filename: Optional[str] = None):
        """Save dashboard configuration to file."""
        
        if not filename:
            filename = f"{dashboard.title.lower().replace(' ', '_')}.json"
        
        file_path = self.dashboard_dir / filename
        
        try:
            dashboard_json = self.generate_dashboard_json(dashboard)
            
            with open(file_path, 'w') as f:
                f.write(dashboard_json)
            
            logger.info(f"Dashboard saved: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving dashboard: {e}")
            return None
    
    def create_all_dashboards(self) -> List[str]:
        """Create and save all performance dashboards."""
        
        dashboards = [
            self.create_overview_dashboard(),
            self.create_detailed_dashboard(),
            self.create_stress_test_dashboard()
        ]
        
        saved_files = []
        
        for dashboard in dashboards:
            file_path = self.save_dashboard(dashboard)
            if file_path:
                saved_files.append(file_path)
        
        logger.info(f"Created {len(saved_files)} performance dashboards")
        return saved_files