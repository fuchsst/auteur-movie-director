# Story: Worker Health Monitoring

**Story ID**: STORY-043  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Infrastructure  
**Points**: 7 (Large)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description
As a system operator, I want comprehensive health monitoring for all function runner workers with real-time metrics, alerting, and automatic recovery mechanisms, so that I can ensure high availability and quickly identify and resolve performance issues before they impact users.

## Acceptance Criteria

### Functional Requirements
- [ ] Real-time health dashboard showing all worker status and metrics
- [ ] Automatic health checks every 30 seconds with configurable intervals
- [ ] Alert notifications for unhealthy workers via multiple channels
- [ ] Automatic worker restart on health check failures
- [ ] Historical health metrics with 7-day retention
- [ ] Resource usage tracking (CPU, memory, GPU, disk)
- [ ] Task performance metrics (completion rate, error rate, latency)
- [ ] Predictive health analysis to prevent failures

### Technical Requirements
- [ ] Implement health check service with multiple check types
- [ ] Create Prometheus metrics exporter for worker statistics
- [ ] Configure Grafana dashboards for visualization
- [ ] Implement alerting rules with PagerDuty/Slack integration
- [ ] Add distributed tracing with OpenTelemetry
- [ ] Create health status API endpoints
- [ ] Implement metric aggregation and storage
- [ ] Add anomaly detection for performance degradation

### Quality Requirements
- [ ] Health check latency < 100ms per worker
- [ ] Metric collection overhead < 1% CPU usage
- [ ] Alert notification delivery < 30 seconds
- [ ] Health data availability > 99.9%
- [ ] Support for monitoring 100+ workers
- [ ] Metric retention for 7 days minimum
- [ ] Dashboard refresh rate < 5 seconds

## Implementation Notes

### Health Check System
```python
class WorkerHealthMonitor:
    """Comprehensive health monitoring for function runners"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.health_checks = [
            HeartbeatCheck(),
            ResourceCheck(),
            TaskPerformanceCheck(),
            QueueConnectionCheck(),
            ModelLoadingCheck(),
            DiskSpaceCheck()
        ]
        self.alert_manager = AlertManager()
        self.metrics_collector = MetricsCollector()
    
    async def monitor_worker(self, worker_id: str):
        """Continuous health monitoring for a worker"""
        while True:
            try:
                # Run all health checks
                results = await self.run_health_checks(worker_id)
                
                # Calculate overall health score
                health_score = self.calculate_health_score(results)
                
                # Update metrics
                await self.metrics_collector.update_worker_health(
                    worker_id, health_score, results
                )
                
                # Check for issues
                if health_score < 0.7:
                    await self.handle_unhealthy_worker(worker_id, results)
                
                # Predict future issues
                prediction = await self.predict_health_issues(worker_id, results)
                if prediction.likely_failure:
                    await self.alert_manager.send_predictive_alert(
                        worker_id, prediction
                    )
                
            except Exception as e:
                logger.error(f"Health check failed for {worker_id}: {e}")
                await self.alert_manager.send_critical_alert(
                    f"Health monitoring failed for worker {worker_id}"
                )
            
            await asyncio.sleep(self.check_interval)
    
    async def run_health_checks(self, worker_id: str) -> List[HealthCheckResult]:
        """Execute all health checks for a worker"""
        results = []
        
        for check in self.health_checks:
            try:
                result = await check.execute(worker_id)
                results.append(result)
            except Exception as e:
                results.append(HealthCheckResult(
                    check_name=check.name,
                    status='error',
                    message=str(e),
                    metrics={}
                ))
        
        return results
```

### Health Check Types
```python
class HeartbeatCheck(HealthCheck):
    """Verify worker is responsive"""
    
    async def execute(self, worker_id: str) -> HealthCheckResult:
        last_heartbeat = await self.redis.get(f"worker:{worker_id}:heartbeat")
        
        if not last_heartbeat:
            return HealthCheckResult(
                check_name="heartbeat",
                status="critical",
                message="No heartbeat received",
                metrics={"last_seen": None}
            )
        
        time_since = datetime.now() - datetime.fromisoformat(last_heartbeat)
        
        if time_since.seconds > 60:
            status = "critical"
            message = f"No heartbeat for {time_since.seconds}s"
        elif time_since.seconds > 30:
            status = "warning"
            message = f"Delayed heartbeat: {time_since.seconds}s"
        else:
            status = "healthy"
            message = "Heartbeat normal"
        
        return HealthCheckResult(
            check_name="heartbeat",
            status=status,
            message=message,
            metrics={
                "last_heartbeat_seconds": time_since.seconds,
                "timestamp": last_heartbeat
            }
        )

class ResourceCheck(HealthCheck):
    """Monitor resource usage"""
    
    async def execute(self, worker_id: str) -> HealthCheckResult:
        metrics = await self.get_worker_metrics(worker_id)
        
        issues = []
        status = "healthy"
        
        # CPU check
        if metrics.cpu_percent > 90:
            issues.append("High CPU usage")
            status = "warning"
        elif metrics.cpu_percent > 95:
            status = "critical"
        
        # Memory check
        if metrics.memory_percent > 85:
            issues.append("High memory usage")
            status = "warning" if status == "healthy" else status
        elif metrics.memory_percent > 95:
            status = "critical"
        
        # GPU check (if applicable)
        if metrics.gpu_memory_percent and metrics.gpu_memory_percent > 90:
            issues.append("High GPU memory usage")
            status = "critical"
        
        return HealthCheckResult(
            check_name="resources",
            status=status,
            message=", ".join(issues) if issues else "Resources normal",
            metrics={
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "memory_mb": metrics.memory_mb,
                "gpu_memory_percent": metrics.gpu_memory_percent,
                "gpu_utilization": metrics.gpu_utilization
            }
        )

class TaskPerformanceCheck(HealthCheck):
    """Monitor task execution performance"""
    
    async def execute(self, worker_id: str) -> HealthCheckResult:
        # Get recent task statistics
        stats = await self.get_task_stats(worker_id, window_minutes=5)
        
        error_rate = stats.failed / stats.total if stats.total > 0 else 0
        avg_duration = stats.total_duration / stats.completed if stats.completed > 0 else 0
        
        # Determine health status
        if error_rate > 0.1:  # >10% error rate
            status = "critical"
            message = f"High error rate: {error_rate:.1%}"
        elif error_rate > 0.05:  # >5% error rate
            status = "warning"
            message = f"Elevated error rate: {error_rate:.1%}"
        elif avg_duration > stats.expected_duration * 2:
            status = "warning"
            message = f"Slow task execution: {avg_duration:.1f}s avg"
        else:
            status = "healthy"
            message = f"Performance normal ({stats.completed} tasks)"
        
        return HealthCheckResult(
            check_name="task_performance",
            status=status,
            message=message,
            metrics={
                "total_tasks": stats.total,
                "completed_tasks": stats.completed,
                "failed_tasks": stats.failed,
                "error_rate": error_rate,
                "avg_duration_seconds": avg_duration,
                "tasks_per_minute": stats.throughput
            }
        )
```

### Metrics Collection
```python
class MetricsCollector:
    """Collect and export worker metrics"""
    
    def __init__(self):
        # Prometheus metrics
        self.worker_health_gauge = Gauge(
            'worker_health_score', 
            'Overall worker health score',
            ['worker_id']
        )
        self.worker_cpu_gauge = Gauge(
            'worker_cpu_percent',
            'Worker CPU usage percentage',
            ['worker_id']
        )
        self.worker_memory_gauge = Gauge(
            'worker_memory_mb',
            'Worker memory usage in MB',
            ['worker_id']
        )
        self.task_duration_histogram = Histogram(
            'task_duration_seconds',
            'Task execution duration',
            ['worker_id', 'task_type']
        )
        self.task_counter = Counter(
            'task_total',
            'Total tasks processed',
            ['worker_id', 'task_type', 'status']
        )
    
    async def update_worker_health(self, worker_id: str, 
                                  health_score: float, 
                                  check_results: List[HealthCheckResult]):
        """Update Prometheus metrics"""
        
        # Update overall health
        self.worker_health_gauge.labels(worker_id=worker_id).set(health_score)
        
        # Update resource metrics
        for result in check_results:
            if result.check_name == "resources":
                self.worker_cpu_gauge.labels(
                    worker_id=worker_id
                ).set(result.metrics.get('cpu_percent', 0))
                
                self.worker_memory_gauge.labels(
                    worker_id=worker_id
                ).set(result.metrics.get('memory_mb', 0))
        
        # Store in time series database
        await self.store_metrics(worker_id, health_score, check_results)
```

### Alert Management
```python
class AlertManager:
    """Manage health alerts and notifications"""
    
    def __init__(self):
        self.channels = {
            'slack': SlackNotifier(),
            'pagerduty': PagerDutyNotifier(),
            'email': EmailNotifier(),
            'webhook': WebhookNotifier()
        }
        self.alert_rules = self.load_alert_rules()
    
    async def send_alert(self, alert: Alert):
        """Send alert through configured channels"""
        
        # Determine severity and channels
        channels = self.get_channels_for_severity(alert.severity)
        
        # Rate limit checks
        if await self.is_rate_limited(alert):
            logger.info(f"Alert rate limited: {alert.title}")
            return
        
        # Send to each channel
        tasks = []
        for channel_name in channels:
            channel = self.channels.get(channel_name)
            if channel:
                tasks.append(channel.send(alert))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Record alert
        await self.record_alert(alert)
    
    async def send_critical_alert(self, message: str, worker_id: str = None):
        """Send critical alert immediately"""
        alert = Alert(
            severity='critical',
            title='Worker Critical Issue',
            message=message,
            worker_id=worker_id,
            timestamp=datetime.now(),
            metadata={
                'require_acknowledgment': True,
                'escalation_timeout': 300  # 5 minutes
            }
        )
        await self.send_alert(alert)
```

### Health Dashboard API
```python
@router.get("/health/workers")
async def get_worker_health_summary() -> WorkerHealthSummary:
    """Get health summary for all workers"""
    workers = await worker_manager.get_all_workers()
    
    summaries = []
    for worker in workers:
        health_data = await metrics_collector.get_latest_health(worker.id)
        summaries.append(WorkerHealthInfo(
            worker_id=worker.id,
            status=health_data.status,
            health_score=health_data.score,
            last_check=health_data.timestamp,
            issues=health_data.issues,
            metrics=health_data.metrics
        ))
    
    return WorkerHealthSummary(
        total_workers=len(workers),
        healthy_workers=sum(1 for s in summaries if s.status == 'healthy'),
        warning_workers=sum(1 for s in summaries if s.status == 'warning'),
        critical_workers=sum(1 for s in summaries if s.status == 'critical'),
        workers=summaries
    )

@router.get("/health/workers/{worker_id}/history")
async def get_worker_health_history(
    worker_id: str,
    hours: int = 24
) -> List[HealthDataPoint]:
    """Get historical health data for a worker"""
    return await metrics_collector.get_health_history(worker_id, hours)

@router.post("/health/workers/{worker_id}/restart")
async def restart_unhealthy_worker(worker_id: str) -> ActionResult:
    """Manually restart an unhealthy worker"""
    return await worker_manager.restart_worker(worker_id)
```

## Dependencies
- **STORY-041**: Worker Pool Management - monitors workers from the pool
- **STORY-042**: Task Queue Configuration - monitors queue health
- Prometheus for metrics collection
- Grafana for visualization
- AlertManager for notification routing
- Redis for metric storage
- OpenTelemetry for distributed tracing

## Testing Criteria
- [ ] Unit tests for all health check types
- [ ] Integration tests for metric collection pipeline
- [ ] Alert notification tests for all channels
- [ ] Load tests with 100+ monitored workers
- [ ] Failure injection tests for health recovery
- [ ] Dashboard rendering performance tests
- [ ] Historical data query performance tests
- [ ] End-to-end monitoring scenario tests

## Definition of Done
- [ ] All health check types implemented and tested
- [ ] Prometheus metrics exported for all data points
- [ ] Grafana dashboards created with key visualizations
- [ ] Alert rules configured for all severity levels
- [ ] Notification channels integrated and tested
- [ ] Health API endpoints documented in OpenAPI
- [ ] Predictive health analysis algorithm implemented
- [ ] Performance meets latency requirements
- [ ] Documentation includes monitoring guide
- [ ] Code review passed with test coverage > 85%

## Story Links
- **Depends On**: STORY-041 (Worker Pool Management)
- **Blocks**: STORY-051 (Integration & Testing)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/monitoring/health_check_design.md