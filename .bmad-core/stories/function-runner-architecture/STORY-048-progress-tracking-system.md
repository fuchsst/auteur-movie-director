# Story: Progress Tracking System

**Story ID**: STORY-048  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Feature  
**Points**: 7 (Large)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description
As a user, I want detailed real-time progress updates for all AI generation tasks with stage information, time estimates, and preview images, so that I can monitor long-running operations and make informed decisions about whether to wait or cancel tasks.

## Acceptance Criteria

### Functional Requirements
- [ ] Real-time progress updates via WebSocket for all tasks
- [ ] Multi-stage progress tracking (queue, preparation, execution, finalization)
- [ ] ETA calculation based on historical data and current progress
- [ ] Preview generation at configurable intervals
- [ ] Progress persistence across connection drops
- [ ] Batch progress aggregation for multiple tasks
- [ ] Resource usage visualization during execution
- [ ] Detailed logs available for debugging

### Technical Requirements
- [ ] Implement `ProgressTracker` with stage management
- [ ] WebSocket event stream for progress updates
- [ ] Progress data persistence in Redis
- [ ] ETA prediction algorithm with learning
- [ ] Preview image generation and caching
- [ ] Progress aggregation for batch operations
- [ ] Metrics collection for progress accuracy
- [ ] RESTful fallback for progress queries

### Quality Requirements
- [ ] Progress updates every 100ms during active stages
- [ ] ETA accuracy within 20% for repeated tasks
- [ ] Preview generation < 500ms overhead
- [ ] Support for 1000+ concurrent task tracking
- [ ] Progress data retention for 24 hours
- [ ] WebSocket reconnection < 2 seconds
- [ ] Zero progress loss during worker restarts

## Implementation Notes

### Progress Tracking Architecture
```python
class ProgressTracker:
    """Comprehensive progress tracking for function execution"""
    
    def __init__(self, redis_client: Redis, ws_manager: WebSocketManager):
        self.redis = redis_client
        self.ws_manager = ws_manager
        self.eta_predictor = ETAPredictor()
        self.preview_generator = PreviewGenerator()
        
    async def create_task_progress(self, task_id: str, 
                                  template_id: str,
                                  total_stages: int = 4) -> TaskProgress:
        """Initialize progress tracking for a task"""
        progress = TaskProgress(
            task_id=task_id,
            template_id=template_id,
            status='queued',
            current_stage=0,
            total_stages=total_stages,
            stages={
                0: StageProgress(name='queue', status='pending'),
                1: StageProgress(name='preparation', status='pending'),
                2: StageProgress(name='execution', status='pending'),
                3: StageProgress(name='finalization', status='pending')
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store in Redis
        await self.redis.setex(
            f"progress:{task_id}",
            86400,  # 24 hour TTL
            progress.json()
        )
        
        # Send initial progress
        await self.broadcast_progress(task_id, progress)
        
        return progress
    
    async def update_stage(self, task_id: str, stage: int, 
                          status: str, progress: float = 0.0,
                          message: str = None, metadata: dict = None):
        """Update progress for a specific stage"""
        task_progress = await self.get_progress(task_id)
        if not task_progress:
            return
        
        # Update stage
        stage_data = task_progress.stages[stage]
        stage_data.status = status
        stage_data.progress = progress
        stage_data.message = message
        stage_data.metadata = metadata or {}
        
        if status == 'in_progress' and not stage_data.started_at:
            stage_data.started_at = datetime.now()
        elif status in ['completed', 'failed'] and not stage_data.completed_at:
            stage_data.completed_at = datetime.now()
        
        # Update overall progress
        task_progress.current_stage = stage
        task_progress.overall_progress = self._calculate_overall_progress(task_progress)
        task_progress.updated_at = datetime.now()
        
        # Calculate ETA
        if status == 'in_progress':
            task_progress.eta = await self.eta_predictor.predict(
                template_id=task_progress.template_id,
                current_stage=stage,
                stage_progress=progress,
                historical_data=await self._get_historical_data(task_progress.template_id)
            )
        
        # Generate preview if applicable
        if stage == 2 and progress > 0.3 and progress < 0.9:  # During execution
            await self._maybe_generate_preview(task_id, task_progress, metadata)
        
        # Save and broadcast
        await self.save_progress(task_id, task_progress)
        await self.broadcast_progress(task_id, task_progress)
    
    def _calculate_overall_progress(self, task_progress: TaskProgress) -> float:
        """Calculate overall progress across all stages"""
        total_weight = 0
        weighted_progress = 0
        
        # Stage weights (can be customized per template)
        weights = {0: 0.05, 1: 0.15, 2: 0.70, 3: 0.10}
        
        for stage_id, stage in task_progress.stages.items():
            weight = weights.get(stage_id, 0.25)
            total_weight += weight
            
            if stage.status == 'completed':
                weighted_progress += weight
            elif stage.status == 'in_progress':
                weighted_progress += weight * stage.progress
        
        return (weighted_progress / total_weight) * 100 if total_weight > 0 else 0
```

### Stage Progress Management
```python
@dataclass
class StageProgress:
    """Progress information for a single stage"""
    name: str
    status: str  # pending, in_progress, completed, failed, skipped
    progress: float = 0.0  # 0-1
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def elapsed(self) -> Optional[timedelta]:
        if self.started_at:
            end = self.completed_at or datetime.now()
            return end - self.started_at
        return None

class StageManager:
    """Manages execution stages for different function types"""
    
    # Default stages for different function categories
    STAGE_DEFINITIONS = {
        'image_generation': [
            Stage('queue', 'Waiting in queue', weight=0.05),
            Stage('model_loading', 'Loading models', weight=0.15),
            Stage('generation', 'Generating image', weight=0.70),
            Stage('post_processing', 'Post-processing', weight=0.10)
        ],
        'video_generation': [
            Stage('queue', 'Waiting in queue', weight=0.02),
            Stage('model_loading', 'Loading models', weight=0.08),
            Stage('frame_generation', 'Generating frames', weight=0.80),
            Stage('video_encoding', 'Encoding video', weight=0.10)
        ],
        'audio_generation': [
            Stage('queue', 'Waiting in queue', weight=0.05),
            Stage('text_processing', 'Processing text', weight=0.10),
            Stage('synthesis', 'Synthesizing audio', weight=0.75),
            Stage('normalization', 'Normalizing audio', weight=0.10)
        ]
    }
    
    def get_stages_for_template(self, template: FunctionTemplate) -> List[Stage]:
        """Get stage definitions for a template"""
        category = template.category
        return self.STAGE_DEFINITIONS.get(category, self._get_default_stages())
```

### ETA Prediction
```python
class ETAPredictor:
    """Predict task completion time based on historical data"""
    
    def __init__(self):
        self.history_cache = TTLCache(maxsize=1000, ttl=3600)
        
    async def predict(self, template_id: str, current_stage: int,
                     stage_progress: float, 
                     historical_data: List[TaskHistory]) -> datetime:
        """Predict completion time for task"""
        
        # Get similar tasks
        similar_tasks = self._filter_similar_tasks(historical_data, template_id)
        
        if not similar_tasks:
            # Fallback to simple estimate
            return self._simple_estimate(current_stage, stage_progress)
        
        # Calculate remaining time based on historical data
        remaining_time = self._calculate_remaining_time(
            similar_tasks, current_stage, stage_progress
        )
        
        # Apply confidence factor based on data quality
        confidence = self._calculate_confidence(similar_tasks)
        adjusted_time = remaining_time * (1 + (1 - confidence) * 0.5)
        
        return datetime.now() + timedelta(seconds=adjusted_time)
    
    def _calculate_remaining_time(self, similar_tasks: List[TaskHistory],
                                 current_stage: int, 
                                 stage_progress: float) -> float:
        """Calculate remaining time based on similar tasks"""
        
        # Get stage durations from similar tasks
        stage_durations = defaultdict(list)
        
        for task in similar_tasks:
            for stage_id, duration in task.stage_durations.items():
                stage_durations[stage_id].append(duration)
        
        # Calculate median duration for each stage
        median_durations = {}
        for stage_id, durations in stage_durations.items():
            median_durations[stage_id] = statistics.median(durations)
        
        # Calculate remaining time
        remaining = 0
        
        # Remaining time in current stage
        if current_stage in median_durations:
            remaining += median_durations[current_stage] * (1 - stage_progress)
        
        # Time for remaining stages
        for stage_id in range(current_stage + 1, max(median_durations.keys()) + 1):
            if stage_id in median_durations:
                remaining += median_durations[stage_id]
        
        return remaining
    
    async def record_completion(self, task_id: str, 
                              template_id: str,
                              stage_durations: Dict[int, float]):
        """Record task completion for future predictions"""
        history = TaskHistory(
            task_id=task_id,
            template_id=template_id,
            stage_durations=stage_durations,
            completed_at=datetime.now()
        )
        
        # Store in database for long-term analysis
        await self._store_history(history)
```

### Preview Generation
```python
class PreviewGenerator:
    """Generate preview images during task execution"""
    
    def __init__(self):
        self.preview_cache = {}
        self.generation_locks = {}
    
    async def generate_preview(self, task_id: str, 
                             task_data: dict,
                             stage_progress: float) -> Optional[str]:
        """Generate preview image for current progress"""
        
        # Check if preview generation is appropriate
        if not self._should_generate_preview(task_data, stage_progress):
            return None
        
        # Avoid generating too frequently
        cache_key = f"{task_id}:{int(stage_progress * 10)}"
        if cache_key in self.preview_cache:
            return self.preview_cache[cache_key]
        
        # Ensure only one preview generation per task at a time
        if task_id in self.generation_locks:
            return None
        
        self.generation_locks[task_id] = True
        
        try:
            # Generate preview based on task type
            preview_data = await self._generate_preview_data(task_data, stage_progress)
            
            if preview_data:
                # Store preview
                preview_url = await self._store_preview(task_id, preview_data)
                self.preview_cache[cache_key] = preview_url
                return preview_url
                
        finally:
            del self.generation_locks[task_id]
        
        return None
    
    def _should_generate_preview(self, task_data: dict, progress: float) -> bool:
        """Determine if preview should be generated"""
        # Generate at 25%, 50%, 75% progress
        return progress in [0.25, 0.5, 0.75] or abs(progress - 0.25) < 0.05 or \
               abs(progress - 0.5) < 0.05 or abs(progress - 0.75) < 0.05
```

### WebSocket Progress Streaming
```python
class ProgressWebSocketHandler:
    """Handle WebSocket connections for progress updates"""
    
    def __init__(self, tracker: ProgressTracker):
        self.tracker = tracker
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)
    
    async def handle_subscribe(self, ws: WebSocket, message: dict):
        """Handle progress subscription request"""
        task_ids = message.get('task_ids', [])
        client_id = message.get('client_id')
        
        # Subscribe to task progress
        for task_id in task_ids:
            self.subscriptions[task_id].add(client_id)
            
            # Send current progress
            progress = await self.tracker.get_progress(task_id)
            if progress:
                await ws.send_json({
                    'type': 'progress.update',
                    'task_id': task_id,
                    'data': progress.dict()
                })
    
    async def broadcast_progress(self, task_id: str, progress: TaskProgress):
        """Broadcast progress to subscribed clients"""
        if task_id not in self.subscriptions:
            return
        
        message = {
            'type': 'progress.update',
            'task_id': task_id,
            'data': {
                'status': progress.status,
                'current_stage': progress.current_stage,
                'overall_progress': progress.overall_progress,
                'eta': progress.eta.isoformat() if progress.eta else None,
                'stages': {
                    str(k): {
                        'name': v.name,
                        'status': v.status,
                        'progress': v.progress,
                        'message': v.message
                    } for k, v in progress.stages.items()
                },
                'preview_url': progress.preview_url,
                'updated_at': progress.updated_at.isoformat()
            }
        }
        
        # Send to all subscribed clients
        for client_id in self.subscriptions[task_id]:
            await self.ws_manager.send_to_client(client_id, message)
```

### Progress API Endpoints
```python
@router.get("/tasks/{task_id}/progress")
async def get_task_progress(task_id: str) -> ProgressResponse:
    """Get current progress for a task"""
    progress = await progress_tracker.get_progress(task_id)
    
    if not progress:
        raise HTTPException(404, "Task not found")
    
    return ProgressResponse(
        task_id=task_id,
        status=progress.status,
        overall_progress=progress.overall_progress,
        current_stage=progress.current_stage,
        stages=[
            StageResponse(
                id=stage_id,
                name=stage.name,
                status=stage.status,
                progress=stage.progress,
                message=stage.message,
                duration=stage.duration.total_seconds() if stage.duration else None
            )
            for stage_id, stage in progress.stages.items()
        ],
        eta=progress.eta,
        preview_url=progress.preview_url
    )

@router.get("/tasks/{task_id}/logs")
async def get_task_logs(
    task_id: str,
    since: Optional[datetime] = None,
    level: Optional[str] = None
) -> LogsResponse:
    """Get execution logs for a task"""
    logs = await log_manager.get_task_logs(
        task_id, 
        since=since,
        level=level
    )
    
    return LogsResponse(
        task_id=task_id,
        logs=[
            LogEntry(
                timestamp=log.timestamp,
                level=log.level,
                message=log.message,
                metadata=log.metadata
            )
            for log in logs
        ]
    )

@router.ws("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for real-time progress"""
    await websocket.accept()
    
    handler = ProgressWebSocketHandler(progress_tracker)
    
    try:
        while True:
            message = await websocket.receive_json()
            
            if message['type'] == 'subscribe':
                await handler.handle_subscribe(websocket, message)
            elif message['type'] == 'unsubscribe':
                await handler.handle_unsubscribe(websocket, message)
                
    except WebSocketDisconnect:
        await handler.cleanup(websocket)
```

### Batch Progress Aggregation
```python
class BatchProgressAggregator:
    """Aggregate progress for batch operations"""
    
    def aggregate_batch_progress(self, 
                               batch_id: str,
                               task_progresses: List[TaskProgress]) -> BatchProgress:
        """Calculate aggregated progress for a batch"""
        
        if not task_progresses:
            return BatchProgress(batch_id=batch_id, overall_progress=0)
        
        # Calculate statistics
        total_tasks = len(task_progresses)
        completed_tasks = sum(1 for p in task_progresses if p.status == 'completed')
        failed_tasks = sum(1 for p in task_progresses if p.status == 'failed')
        
        # Calculate overall progress
        total_progress = sum(p.overall_progress for p in task_progresses)
        overall_progress = total_progress / total_tasks
        
        # Estimate batch ETA
        etas = [p.eta for p in task_progresses if p.eta and p.status == 'in_progress']
        batch_eta = max(etas) if etas else None
        
        return BatchProgress(
            batch_id=batch_id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            overall_progress=overall_progress,
            eta=batch_eta,
            task_summaries=[
                TaskSummary(
                    task_id=p.task_id,
                    status=p.status,
                    progress=p.overall_progress
                )
                for p in task_progresses
            ]
        )
```

## Dependencies
- **STORY-041**: Worker Pool Management - executes tasks being tracked
- **STORY-047**: Function Runner API Client - consumes progress updates
- **STORY-005**: WebSocket Service - provides real-time communication
- Redis for progress data persistence
- WebSocket for real-time updates

## Testing Criteria
- [ ] Unit tests for progress calculation logic
- [ ] Integration tests for WebSocket streaming
- [ ] ETA prediction accuracy tests
- [ ] Preview generation tests
- [ ] Load tests with 1000+ concurrent tasks
- [ ] Connection resilience tests
- [ ] Progress persistence tests
- [ ] API endpoint tests

## Definition of Done
- [ ] ProgressTracker with all features implemented
- [ ] WebSocket streaming working reliably
- [ ] ETA prediction algorithm trained and tested
- [ ] Preview generation integrated
- [ ] Batch progress aggregation working
- [ ] Progress persistence in Redis
- [ ] API endpoints documented
- [ ] Performance meets update frequency requirements
- [ ] Documentation includes progress tracking guide
- [ ] Code review passed with test coverage > 85%

## Story Links
- **Depends On**: STORY-041, STORY-005
- **Blocks**: STORY-051 (Integration & Testing)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/progress/tracking_design.md