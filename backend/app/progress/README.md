# Progress Tracking System

A comprehensive real-time progress tracking system for AI generation tasks with WebSocket streaming, ETA prediction, and preview generation.

## Features

- **Real-time Updates**: WebSocket-based progress streaming with sub-second latency
- **Multi-stage Tracking**: Configurable stages for different task types
- **ETA Prediction**: Machine learning-based completion time estimates
- **Preview Generation**: Automatic preview images during execution
- **Batch Progress**: Aggregated progress for multiple tasks
- **Resource Monitoring**: CPU/GPU/Memory usage tracking
- **Persistent Storage**: Redis-backed progress data with 24-hour retention
- **Offline Support**: Progress survives connection drops and server restarts

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Function Runner │────▶│ Progress Tracker │────▶│ WebSocket       │
│                 │     │                  │     │ Manager         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌──────────────┐          ┌─────────────┐
                        │    Redis     │          │   Clients   │
                        │   Storage    │          │ (Frontend)  │
                        └──────────────┘          └─────────────┘
```

## Usage

### Basic Progress Tracking

```python
from app.progress import ProgressTracker, ProgressContext
from app.core.dependencies import get_progress_tracker

# Get tracker instance
tracker = await get_progress_tracker()

# Use context manager for automatic tracking
async with ProgressContext(
    tracker, 
    task_id="task-123",
    template_id="stable-diffusion-xl",
    template_category="image_generation"
) as ctx:
    
    # Get callback for function runner
    callback = ctx.get_callback()
    
    # Update progress
    await callback('execution_progress', {
        'step': 15,
        'total_steps': 30,
        'preview_path': '/tmp/preview.png'
    })
```

### Manual Progress Updates

```python
# Create task progress
progress = await tracker.create_task_progress(
    task_id="task-456",
    template_id="video-gen-v1",
    template_category="video_generation"
)

# Update stage
await tracker.update_stage(
    task_id="task-456",
    stage=2,  # Frame generation stage
    status=StageStatus.IN_PROGRESS,
    progress=0.5,
    message="Generating frame 15/30"
)
```

### WebSocket Subscription

```javascript
// Frontend WebSocket connection
const ws = new WebSocket('ws://localhost:8000/api/v1/progress/ws?client_id=user-123');

// Subscribe to task progress
ws.send(JSON.stringify({
    type: 'subscribe',
    task_ids: ['task-123', 'task-456']
}));

// Receive updates
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'progress.update') {
        console.log(`Task ${message.task_id}: ${message.data.overall_progress}%`);
    }
};
```

## Stage Configuration

### Default Stage Templates

The system provides pre-configured stages for common task types:

```python
# Image Generation
stages = [
    Stage('queue', 'Waiting in queue', weight=0.05),
    Stage('model_loading', 'Loading models', weight=0.15),
    Stage('generation', 'Generating image', weight=0.70),
    Stage('post_processing', 'Post-processing', weight=0.10)
]

# Video Generation
stages = [
    Stage('queue', 'Waiting in queue', weight=0.02),
    Stage('model_loading', 'Loading models', weight=0.08),
    Stage('frame_generation', 'Generating frames', weight=0.80),
    Stage('video_encoding', 'Encoding video', weight=0.10)
]
```

### Custom Stages

Register custom stages for specific templates:

```python
from app.progress import StageManager, Stage

custom_stages = [
    Stage('preprocessing', 'Preparing data', weight=0.2),
    Stage('analysis', 'Analyzing content', weight=0.3),
    Stage('synthesis', 'Synthesizing output', weight=0.4),
    Stage('validation', 'Validating results', weight=0.1)
]

StageManager.register_template_stages('my-custom-template', custom_stages)
```

## API Endpoints

### REST API

```bash
# Get task progress
GET /api/v1/progress/tasks/{task_id}

# Get task logs
GET /api/v1/progress/tasks/{task_id}/logs?since=2024-01-01&level=info

# Get batch progress
GET /api/v1/progress/batch/{batch_id}?task_ids=task1,task2,task3

# Get task history
GET /api/v1/progress/tasks/{task_id}/history
```

### WebSocket API

```javascript
// Subscribe to tasks
{
    "type": "subscribe",
    "task_ids": ["task-123", "task-456"]
}

// Unsubscribe
{
    "type": "unsubscribe", 
    "task_ids": ["task-123"]
}

// Get current progress
{
    "type": "get_progress",
    "task_id": "task-123"
}

// Get batch progress
{
    "type": "get_batch_progress",
    "batch_id": "batch-001",
    "task_ids": ["task-1", "task-2", "task-3"]
}
```

## Progress Data Model

### TaskProgress

```python
{
    "task_id": "task-123",
    "template_id": "stable-diffusion-xl",
    "status": "executing",
    "current_stage": 2,
    "total_stages": 4,
    "overall_progress": 65.5,
    "eta": "2024-01-15T10:30:00",
    "preview_url": "/api/v1/previews/task-123_50.png",
    "stages": {
        "0": {
            "name": "queue",
            "status": "completed",
            "progress": 1.0,
            "duration": 5.2
        },
        "1": {
            "name": "model_loading", 
            "status": "completed",
            "progress": 1.0,
            "duration": 12.8
        },
        "2": {
            "name": "generation",
            "status": "in_progress",
            "progress": 0.65,
            "message": "Step 20/30"
        }
    },
    "resource_usage": {
        "cpu_percent": 45.2,
        "memory_mb": 2048,
        "gpu_percent": 87.5,
        "gpu_memory_mb": 6144
    }
}
```

## ETA Prediction

The system uses historical task data to predict completion times:

1. **Data Collection**: Stores execution times for each stage
2. **Similar Task Matching**: Finds tasks with same template and quality
3. **Statistical Analysis**: Uses 75th percentile for conservative estimates
4. **Confidence Adjustment**: Applies confidence factor based on data quality

```python
# Record completion for future predictions
await eta_predictor.record_completion(
    task_id="task-123",
    template_id="stable-diffusion-xl",
    quality="high",
    stage_durations={0: 5.0, 1: 15.0, 2: 120.0, 3: 10.0},
    total_duration=150.0,
    resource_config={"gpu": "A100"}
)
```

## Preview Generation

Automatic preview generation during task execution:

- Generates previews at 25%, 50%, and 75% progress
- Supports image and video frame previews
- Caches previews to avoid redundant generation
- Configurable preview intervals

## Performance Considerations

- **Update Frequency**: Progress updates throttled to 100ms intervals
- **Cache Strategy**: In-memory cache for active tasks, Redis for persistence
- **WebSocket Scaling**: Supports 1000+ concurrent connections
- **Preview Overhead**: < 500ms generation time
- **Redis TTL**: 24-hour retention for completed tasks

## Error Handling

The progress system gracefully handles:
- Connection drops (progress persisted in Redis)
- Worker failures (status marked as failed)
- Invalid updates (logged but ignored)
- Preview generation errors (task continues)

## Testing

Run the progress tracking tests:

```bash
pytest backend/tests/test_progress_tracker.py -v
```

## Future Enhancements

- [ ] GraphQL subscriptions support
- [ ] Progress analytics dashboard
- [ ] Custom preview generators
- [ ] Progress replay for debugging
- [ ] Multi-language progress messages