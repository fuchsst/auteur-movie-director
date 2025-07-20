# User Story: STORY-076 - Real-time Progress Tracking

## Story Description
**As a** filmmaker
**I want** real-time progress updates during video assembly
**So that** I can monitor long-running processes and make informed decisions

## Acceptance Criteria

### Functional Requirements
- [ ] Real-time progress percentage updates
- [ ] Detailed step-by-step progress messages
- [ ] Estimated time remaining calculation
- [ ] Pause/resume functionality for assembly jobs
- [ ] Progress visualization in UI (progress bars, status indicators)
- [ ] Email/SMS notifications on completion (configurable)

### Technical Requirements
- [ ] WebSocket-based real-time communication
- [ ] Background task management with Celery/Redis
- [ ] Progress state persistence across server restarts
- [ ] Scalable progress tracking for multiple concurrent jobs
- [ ] Efficient database queries for progress updates
- [ ] Error state handling and recovery

### Quality Requirements
- [ ] Real-time latency < 1 second for progress updates
- [ ] Accurate time estimation algorithms
- [ ] Resilient to network interruptions
- [ ] Comprehensive error handling and user feedback
- [ ] Performance testing for concurrent users

## Implementation Notes

### Technical Approach
- **Real-time**: WebSocket connections for instant updates
- **Background**: Celery tasks with Redis for job management
- **Persistence**: Database state for job recovery
- **Scalability**: Horizontal scaling support

### Component Structure
```
app/services/progress/
├── websocket_manager.py
├── progress_tracker.py
├── time_estimator.py
├── notification_service.py
└── job_recovery.py

frontend/src/lib/services/
├── websocket-client.ts
├── progress-store.ts
├── notification-service.ts
└── progress-visualization.ts
```

### WebSocket Message Schema
```typescript
interface ProgressUpdate {
  jobId: string;
  type: 'assembly' | 'export' | 'edl';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  progress: number; // 0-100
  currentStep: string;
  totalSteps: number;
  estimatedTimeRemaining: number; // seconds
  processingSpeed: number; // MB/s or shots/minute
  lastUpdate: string;
}
```

### Progress Tracking Algorithm
```python
class ProgressTracker:
    def __init__(self):
        self.total_work = 0
        self.completed_work = 0
        self.start_time = None
        self.current_step = ""
    
    def update_progress(self, step_name: str, work_done: int, total_work: int):
        self.current_step = step_name
        self.completed_work = work_done
        self.total_work = total_work
        
        progress = (work_done / total_work) * 100
        eta = self.calculate_eta()
        
        self.emit_update({
            "progress": progress,
            "current_step": step_name,
            "estimated_time_remaining": eta
        })
    
    def calculate_eta(self) -> int:
        elapsed = time.time() - self.start_time
        rate = self.completed_work / elapsed if elapsed > 0 else 0
        remaining = self.total_work - self.completed_work
        return int(remaining / rate) if rate > 0 else 0
```

### UI Progress Visualization
```svelte
<!-- ProgressBar.svelte -->
<script lang="ts">
  import { progressStore } from '$lib/stores/progress';
  
  export let jobId: string;
  
  $: progress = $progressStore[jobId];
</script>

<div class="progress-container">
  <div class="progress-bar">
    <div class="progress-fill" style="width: {progress?.progress || 0}%"></div>
  </div>
  <div class="progress-info">
    <span>{progress?.currentStep}</span>
    <span>{progress?.estimatedTimeRemaining}s remaining</span>
  </div>
</div>
```

### Processing Steps Breakdown
```
Assembly Process Steps:
1. Validate input parameters (5%)
2. Load and validate source files (10%)
3. Extract story metadata (15%)
4. Generate EDL file (20%)
5. Process video concatenation (35%)
6. Apply format encoding (45%)
7. Final file validation (50%)
8. Move to exports directory (55%)
9. Update project metadata (60%)
10. Generate thumbnails/previews (65%)
11. Cleanup temporary files (70%)
12. Send completion notification (100%)
```

### Background Job Management
```python
@celery_app.task(bind=True)
def assemble_video_task(self, project_id, assembly_config):
    tracker = ProgressTracker(job_id=self.request.id)
    
    try:
        # Step 1: Validation
        tracker.update_progress("Validating inputs", 1, 12)
        validate_inputs(project_id, assembly_config)
        
        # Step 2: File validation
        tracker.update_progress("Validating source files", 2, 12)
        validate_source_files(project_id)
        
        # Continue with remaining steps...
        
    except Exception as e:
        tracker.update_status("failed", str(e))
        raise
    
    tracker.update_progress("Completed", 12, 12)
```

### Real-time Communication
```python
class WebSocketManager:
    def __init__(self):
        self.connections = {}
    
    async def broadcast_progress(self, job_id: str, progress_data: dict):
        message = {
            "type": "progress_update",
            "jobId": job_id,
            "data": progress_data
        }
        
        for connection in self.connections.get(job_id, []):
            await connection.send_json(message)
```

### Notification System
```python
class NotificationService:
    def send_completion_notification(self, user_email: str, job_data: dict):
        subject = f"Video Assembly Complete: {job_data['project_name']}"
        body = f"""
        Your video assembly has been completed successfully!
        
        Project: {job_data['project_name']}
        Format: {job_data['format']}
        Duration: {job_data['duration']}
        File Size: {job_data['file_size']}
        
        Download link: {job_data['download_url']}
        """
        
        send_email(user_email, subject, body)
```

### API Endpoints Required
- `POST /api/v1/assembly/jobs/{id}/pause` - Pause job
- `POST /api/v1/assembly/jobs/{id}/resume` - Resume job
- `GET /api/v1/assembly/jobs/{id}/progress` - Get progress
- `GET /api/v1/assembly/jobs/{id}/websocket` - WebSocket connection
- `POST /api/v1/assembly/jobs/{id}/notifications` - Configure notifications

### Testing Strategy
- **Unit Tests**: Progress calculation, ETA estimation
- **Integration Tests**: WebSocket communication, job management
- **Load Tests**: Multiple concurrent progress updates
- **Recovery Tests**: Server restart and job recovery
- **Real-time Tests**: Latency and accuracy validation

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 5-6 (Phase 3)**

## Dependencies
- **STORY-068**: MoviePy pipeline for progress hooks
- **STORY-075**: Multi-format export for format-specific progress
- **WebSocket Service**: Real-time communication infrastructure
- **Redis**: Background job queue and state management

## Success Criteria
- Progress updates reflect actual processing stages
- ETA calculations accurate within 10% for large projects
- WebSocket connections maintain <1s latency
- Job recovery works after server restart
- Multiple concurrent jobs tracked accurately
- Notifications sent successfully on completion
- Pause/resume functionality works correctly
- UI progress visualization updates smoothly

## Performance Targets
- **Latency**: <1 second for progress updates
- **Accuracy**: ETA within 10% of actual time
- **Scalability**: 100+ concurrent jobs
- **Recovery**: <5 seconds job state restoration
- **Throughput**: 1000+ progress messages/second