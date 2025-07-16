# Error Handling and Recovery System

A comprehensive error handling system with automatic recovery, circuit breakers, compensation logic, and self-healing mechanisms for the Function Runner architecture.

## Features

- **Error Classification**: Automatic categorization of errors with recovery strategies
- **Recovery Strategies**: Multiple recovery patterns (retry, queue, fail-fast, dead letter)
- **Circuit Breakers**: Fault tolerance for external service calls
- **Compensation Logic**: Automatic rollback for failed operations
- **Error Analytics**: Real-time error pattern analysis and anomaly detection
- **Self-Healing**: Automatic remediation for common system issues
- **Alert System**: Configurable alerts for critical errors and anomalies

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Function Runner │────▶│ Error Classifier │────▶│ Recovery Manager│
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌──────────────┐          ┌─────────────────┐
                        │   Analytics  │          │ Circuit Breaker │
                        │              │          │                 │
                        └──────────────┘          └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌──────────────┐          ┌─────────────────┐
                        │ Self-Healing │          │  Compensation   │
                        │              │          │                 │
                        └──────────────┘          └─────────────────┘
```

## Error Categories

### 1. Transient Errors
- **Examples**: Connection reset, timeout, network issues
- **Strategy**: Retry with exponential backoff
- **Recovery**: Automatic retry up to 3 times

### 2. Resource Errors
- **Examples**: Out of memory, GPU unavailable, disk full
- **Strategy**: Queue and wait for resources
- **Recovery**: Task queued until resources available

### 3. Validation Errors
- **Examples**: Invalid input, schema validation failure
- **Strategy**: Fail fast with user notification
- **Recovery**: No automatic recovery, user intervention required

### 4. Permanent Errors
- **Examples**: Permission denied, model not found
- **Strategy**: Move to dead letter queue
- **Recovery**: Manual intervention required

## Usage

### Basic Error Handling

```python
from app.error_handling import ErrorHandlingIntegration
from app.core.dependencies import get_error_handler

# Get error handler
error_handler = await get_error_handler()

# Wrap task execution
result = await error_handler.wrap_task_execution(
    task_id="task-123",
    template_id="stable-diffusion",
    operation_type="image_generation",
    task_data={"prompt": "A beautiful landscape"},
    execute_func=generate_image
)
```

### Using Decorators

```python
from app.error_handling import with_error_handling

class ImageGenerator:
    def __init__(self):
        self._error_handler = error_handler
    
    @with_error_handling(operation_type="image_generation", service="comfyui")
    async def generate(self, task_id: str, template_id: str, prompt: str):
        # Your generation logic here
        return await self._generate_image(prompt)
```

### Context Manager

```python
from app.error_handling import ErrorHandlingContext

async with ErrorHandlingContext(
    error_handler,
    task_id="task-456",
    template_id="video-gen",
    operation_type="video_generation",
    task_data=task_data
) as ctx:
    # Record operations for compensation
    ctx.record_operation("file_upload", {"file_path": "/tmp/input.mp4"})
    ctx.record_operation("resource_allocation", {"allocation_id": "gpu-123"})
    
    # Execute task
    result = await generate_video(task_data)
```

## Circuit Breakers

Circuit breakers protect against cascading failures:

```python
# Use circuit breaker for external calls
result = await error_handler.protect_external_call(
    service="comfyui",
    func=call_comfyui_api,
    workflow_data=workflow,
    fallback=cached_result  # Optional fallback
)
```

### Circuit Breaker States
- **Closed**: Normal operation, requests pass through
- **Open**: Failures exceeded threshold, requests fail immediately
- **Half-Open**: Testing if service recovered

## Self-Healing

The system automatically detects and heals common issues:

### Monitored Issues
- Unresponsive workers
- Queue backlogs
- Resource leaks
- High CPU usage
- Low disk space
- Model corruption

### Healing Actions
- Restart workers
- Scale resources
- Clear caches
- Throttle processing
- Archive old files

## Error Analytics

### Real-time Analysis

```python
# Get error analysis
analysis = await error_handler.get_error_analysis()

# Returns:
{
    "error_analysis": {
        "total_errors": 42,
        "error_rate": 0.05,
        "error_distribution": {
            "transient": 30,
            "resource": 8,
            "validation": 3,
            "permanent": 1
        },
        "anomalies": [...],
        "recommendations": [...]
    },
    "circuit_breakers": {...},
    "recovery": {...},
    "self_healing": {...}
}
```

### Anomaly Detection
- High error rates
- Frequent specific errors
- Error spikes
- Critical error thresholds
- Recovery failures

## API Endpoints

```bash
# Error analysis
GET /api/v1/errors/analysis?window_minutes=5

# Error statistics
GET /api/v1/errors/stats

# Circuit breaker status
GET /api/v1/errors/circuit-breakers
POST /api/v1/errors/circuit-breakers/{service}/reset

# Recovery statistics
GET /api/v1/errors/recovery/stats

# Self-healing
GET /api/v1/errors/self-healing/stats
POST /api/v1/errors/self-healing/diagnose

# Task error history
GET /api/v1/errors/task/{task_id}/history

# System health
GET /api/v1/errors/health
```

## Configuration

### Alert Thresholds

```python
# Update alert thresholds
PUT /api/v1/errors/alerts/thresholds
{
    "error_rate": 0.15,  # 15% error rate
    "specific_error_count": 20,
    "recovery_failure_rate": 0.25
}
```

### Circuit Breaker Settings

```python
# Add custom circuit breaker
circuit_breakers.add_breaker(
    service="my_service",
    failure_threshold=5,
    recovery_timeout=120,
    success_threshold=3
)
```

## Monitoring

### WebSocket Real-time Monitoring

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/errors/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'error') {
        console.log('Error detected:', data);
    }
};
```

### Metrics
- Total errors by category
- Recovery success rates
- Circuit breaker health
- Self-healing effectiveness
- Error trends over time

## Best Practices

1. **Use appropriate error categories** in your exceptions
2. **Implement compensation logic** for critical operations
3. **Monitor circuit breaker states** for external dependencies
4. **Configure alert thresholds** based on your SLAs
5. **Review dead letter queue** regularly
6. **Test recovery strategies** with chaos engineering

## Testing

Run the error handling tests:

```bash
pytest backend/tests/test_error_handling.py -v
```

## Future Enhancements

- [ ] Machine learning for error prediction
- [ ] Distributed tracing integration
- [ ] Custom recovery strategy plugins
- [ ] Error replay capabilities
- [ ] Advanced chaos engineering tools