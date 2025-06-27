# User Story: Health Monitoring Dashboard

**Story ID:** STORY-008  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** UI Integration  
**Story Points:** 5  
**Priority:** Medium (P2)  

---

## Story Description

**As a** power user managing multiple AI backends  
**I want** detailed health metrics and performance data  
**So that** I can optimize my generation pipeline and troubleshoot issues  

## Acceptance Criteria

### Functional Requirements
- [ ] Display real-time performance metrics per service
- [ ] Show historical uptime percentages
- [ ] Track response time trends
- [ ] Monitor queue depths and processing times
- [ ] Display resource usage (if available)
- [ ] Export metrics data for analysis
- [ ] Set performance alert thresholds
- [ ] Compare metrics across services

### Technical Requirements
- [ ] Implement metrics collection system
- [ ] Store metrics in efficient data structure
- [ ] Calculate rolling averages and percentiles
- [ ] Update dashboard without UI blocking
- [ ] Support metric data persistence
- [ ] Implement data visualization
- [ ] Configurable metric retention period
- [ ] Thread-safe metric updates

### Quality Requirements
- [ ] Dashboard updates every 1-5 seconds
- [ ] Minimal memory footprint (<10MB)
- [ ] Clear data visualization
- [ ] Responsive to panel resizing
- [ ] Accurate metric calculations
- [ ] Smooth UI transitions
- [ ] Export in standard formats (CSV/JSON)
- [ ] No performance impact on operations

## Implementation Notes

### Technical Approach

**Metrics Collection System:**
```python
from dataclasses import dataclass
from collections import deque
import statistics

@dataclass
class ServiceMetrics:
    service_name: str
    response_times: deque  # Rolling window
    success_count: int = 0
    error_count: int = 0
    last_error_time: float = 0
    uptime_start: float = 0
    downtime_total: float = 0
    
    def __post_init__(self):
        self.response_times = deque(maxlen=1000)
        
    def record_request(self, duration: float, success: bool):
        """Record a service request"""
        self.response_times.append(duration)
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            self.last_error_time = time.time()
            
    def get_statistics(self):
        """Calculate current statistics"""
        if not self.response_times:
            return {}
            
        return {
            'avg_response_time': statistics.mean(self.response_times),
            'median_response_time': statistics.median(self.response_times),
            'p95_response_time': statistics.quantiles(self.response_times, n=20)[18],
            'success_rate': self.success_count / (self.success_count + self.error_count),
            'uptime_percentage': self.calculate_uptime(),
            'requests_per_minute': self.calculate_rpm()
        }
```

**Health Dashboard Panel:**
```python
class MOVIE_DIRECTOR_PT_health_dashboard(Panel):
    bl_label = "Health Monitoring"
    bl_idname = "MOVIE_DIRECTOR_PT_health_dashboard"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Movie Director"
    bl_parent_id = "MOVIE_DIRECTOR_PT_connection_status"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.movie_director_props
        
        # Time range selector
        row = layout.row()
        row.prop(props, "metrics_time_range", expand=True)
        
        # Backend service metrics
        layout.label(text="Backend Services:", icon='LINKED')
        for service in props.backend_services:
            if service.status == 'connected':
                self.draw_service_metrics(layout, service)
                
        # LLM metrics
        layout.separator()
        layout.label(text="LLM Integration:", icon='TEXT')
        if props.llm_status.configured:
            self.draw_llm_metrics(layout, props.llm_status)
                
        # Export button
        layout.operator("movie_director.export_metrics", 
                       icon='EXPORT')
```

**Service Metrics Display:**
```python
def draw_service_metrics(self, layout, service):
    """Draw metrics for a single service"""
    metrics = get_service_metrics(service.name)
    stats = metrics.get_statistics()
    
    box = layout.box()
    box.label(text=service.name, icon='GRAPH')
    
    # Performance metrics
    col = box.column(align=True)
    
    # Response time with visual bar
    row = col.row()
    row.label(text="Avg Response:")
    self.draw_metric_bar(row, stats['avg_response_time'], 
                        max_value=1000, unit="ms")
    
    # Success rate with percentage
    row = col.row()
    row.label(text="Success Rate:")
    self.draw_percentage_bar(row, stats['success_rate'])
    
    # Uptime
    row = col.row()
    row.label(text="Uptime:")
    row.label(text=f"{stats['uptime_percentage']:.1f}%")
    
    # Queue depth (if available)
    if queue_depth := service.get_queue_depth():
        row = col.row()
        row.label(text="Queue:")
        row.label(text=str(queue_depth))

def draw_llm_metrics(self, layout, llm_status):
    """Draw metrics for LLM integration"""
    metrics = get_llm_metrics()
    
    box = layout.box()
    box.label(text="Language Models", icon='TEXT')
    
    col = box.column(align=True)
    
    # Active model
    row = col.row()
    row.label(text="Active Model:")
    row.label(text=llm_status.active_model)
    
    # Token usage
    if token_stats := metrics.get('token_usage'):
        row = col.row()
        row.label(text="Tokens Used:")
        row.label(text=f"{token_stats['total']:,}")
        
        row = col.row()
        row.label(text="Avg Response:")
        self.draw_metric_bar(row, token_stats['avg_response_time'], 
                            max_value=2000, unit="ms")
    
    # Cost tracking
    if cost_data := metrics.get('cost_estimate'):
        row = col.row()
        row.label(text="Est. Cost:")
        row.label(text=f"${cost_data['total']:.2f}")
        
def draw_metric_bar(self, layout, value, max_value, unit=""):
    """Draw a visual metric bar"""
    # Calculate bar width
    factor = min(value / max_value, 1.0)
    
    # Color based on value
    if factor < 0.5:
        icon = 'SEQUENCE_COLOR_01'  # Green
    elif factor < 0.8:
        icon = 'SEQUENCE_COLOR_03'  # Yellow
    else:
        icon = 'SEQUENCE_COLOR_05'  # Red
        
    # Draw bar
    split = layout.split(factor=factor)
    split.label(text="", icon=icon)
    split.label(text=f"{value:.1f}{unit}")
```

**Metrics History Visualization:**
```python
class MOVIE_DIRECTOR_OT_show_metrics_graph(Operator):
    bl_idname = "movie_director.show_metrics_graph"
    bl_label = "Metrics History"
    bl_description = "Show detailed metrics history"
    
    service: StringProperty()
    
    def invoke(self, context, event):
        # Create a temporary image for the graph
        self.create_metrics_graph()
        return context.window_manager.invoke_props_dialog(self, width=800)
        
    def create_metrics_graph(self):
        """Generate metrics visualization"""
        import matplotlib.pyplot as plt
        from io import BytesIO
        
        metrics = get_service_metrics(self.service)
        
        # Create time series plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
        
        # Response times
        times = list(metrics.response_times)
        ax1.plot(times, label='Response Time (ms)')
        ax1.set_ylabel('Response Time (ms)')
        ax1.legend()
        
        # Success rate
        # Calculate rolling success rate
        window_size = 50
        success_rates = calculate_rolling_success_rate(metrics, window_size)
        ax2.plot(success_rates, label='Success Rate', color='green')
        ax2.set_ylabel('Success Rate (%)')
        ax2.set_ylim(0, 105)
        ax2.legend()
        
        # Save to buffer
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Load into Blender image
        self.graph_image = bpy.data.images.new("metrics_graph", 800, 600)
        self.graph_image.pixels = [...] # Load from buffer
```

**Metrics Export:**
```python
class MOVIE_DIRECTOR_OT_export_metrics(Operator):
    bl_idname = "movie_director.export_metrics"
    bl_label = "Export Metrics"
    
    filepath: StringProperty(subtype='FILE_PATH')
    format: EnumProperty(
        items=[
            ('CSV', "CSV", "Comma-separated values"),
            ('JSON', "JSON", "JavaScript Object Notation")
        ]
    )
    
    def execute(self, context):
        metrics_data = collect_all_metrics()
        
        if self.format == 'CSV':
            self.export_csv(metrics_data)
        else:
            self.export_json(metrics_data)
            
        self.report({'INFO'}, f"Metrics exported to {self.filepath}")
        return {'FINISHED'}
```

### Metrics to Track

**Backend Services:**
1. **Performance**: Response time, throughput
2. **Reliability**: Success rate, uptime
3. **Resource**: Queue depth, memory usage
4. **Errors**: Error rate, error types
5. **Usage**: Request count, peak times

**LLM Integration:**
1. **Usage**: Token count, model distribution
2. **Performance**: Response latency
3. **Cost**: Estimated spend by model
4. **Availability**: Active models count

### Data Retention
- Real-time: Last 5 minutes (1s granularity)
- Recent: Last hour (10s granularity)
- Historical: Last 24 hours (1min granularity)

## Testing Strategy

### Unit Tests
```python
class TestMetricsCollection(unittest.TestCase):
    def test_metric_recording(self):
        # Record various metrics
        # Verify calculations
        
    def test_rolling_windows(self):
        # Test data retention
        # Verify old data removed
        
    def test_statistics_calculation(self):
        # Test percentile calculations
        # Verify accuracy
```

### Performance Tests
- Verify low overhead
- Test with high-frequency updates
- Memory usage monitoring

## Dependencies
- STORY-002-003: Backend clients provide metrics
- STORY-004: LLM Integration Layer provides usage stats
- STORY-010: Health check service feeds data
- Metrics visualization library (optional)

## Related Stories
- Extends STORY-005 (Connection Status Panel)
- Uses data from STORY-010 (Health Check Service)
- Supports STORY-011 (Automatic Reconnection)

## Definition of Done
- [ ] Metrics collection working
- [ ] Dashboard displays all metrics
- [ ] Historical data retained properly
- [ ] Export functionality works
- [ ] Performance impact <1%
- [ ] Visual elements clear
- [ ] Documentation complete
- [ ] No memory leaks

---

**Sign-off:**
- [ ] Development Lead
- [ ] Performance Engineer
- [ ] QA Engineer