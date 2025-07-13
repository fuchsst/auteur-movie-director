# User Story: Git Performance Optimization

**Story ID**: STORY-036  
**Epic**: EPIC-002 - Project & Asset Management System  
**Story Points**: 3  
**Priority**: Medium  
**Sprint**: Optimization Sprint (Week 9)  

## Story Description

**As a** user with large projects  
**I want** Git operations to remain fast as my project grows  
**So that** version control doesn't slow down my workflow  

## Acceptance Criteria

### Functional Requirements
- [ ] Git operations fast on 10GB+ repositories
- [ ] History loads incrementally (pagination)
- [ ] Background operations don't block UI
- [ ] Cache frequently accessed data
- [ ] Optimize for media-heavy projects
- [ ] Progress indicators for long operations

### Technical Requirements
- [ ] Implement Git performance optimizations:
  - Shallow clones with depth limit
  - Sparse checkout for large projects
  - Packfile optimization
  - Reference caching
- [ ] Background task queue for:
  - Auto-commits
  - History fetching
  - Garbage collection
- [ ] Redis caching for:
  - Recent commits
  - File status
  - Repository statistics
- [ ] Performance monitoring endpoints

### Quality Requirements
- [ ] Status check < 500ms (cached)
- [ ] Commit operation < 2s (typical)
- [ ] History fetch < 1s (first page)
- [ ] No UI blocking ever
- [ ] Memory usage < 500MB
- [ ] Cache hit rate > 80%

## Implementation Notes

### Technical Approach
1. **Performance Manager**:
   ```python
   class GitPerformanceManager:
       def __init__(self, redis_client):
           self.cache = redis_client
           self.metrics = {}
           
       async def get_status_cached(self, project_id: str):
           # Check cache first
           # Fetch if stale
           # Update cache
           
       async def optimize_repository(self, project_id: str):
           # Run git gc
           # Optimize packfiles
           # Clean reflog
   ```

2. **Background Tasks**:
   ```python
   @celery_app.task
   def background_commit(project_id: str, file_paths: List[str]):
       # Perform commit without blocking
       # Send WebSocket notification
       
   @celery_app.task
   def fetch_history_page(project_id: str, page: int):
       # Fetch history chunk
       # Cache results
   ```

3. **Caching Strategy**:
   ```python
   CACHE_KEYS = {
       "status": "git:status:{project_id}",
       "history": "git:history:{project_id}:{page}",
       "stats": "git:stats:{project_id}"
   }
   
   CACHE_TTL = {
       "status": 30,      # 30 seconds
       "history": 300,    # 5 minutes
       "stats": 3600      # 1 hour
   }
   ```

### Dependencies
- STORY-034 (Git service extensions)
- Redis for caching
- Celery for background tasks
- Git 2.25+ with performance features
- No agent dependencies

### Integration Points
- All Git operations use cache
- Background tasks via Celery
- Performance metrics API
- WebSocket for progress

## Testing Strategy

### Unit Tests
```python
def test_cache_hit_performance():
    # Test cached response time
    
def test_large_repo_operations():
    # Test with 10GB repository
    
def test_background_task_queuing():
    # Test task execution
    
def test_memory_usage_limits():
    # Monitor memory consumption
```

### Performance Tests
- Load test with large repos
- Measure operation times
- Profile memory usage
- Test cache effectiveness
- Concurrent operation handling

## Definition of Done
- [ ] Caching layer implemented
- [ ] Background tasks working
- [ ] Performance targets met
- [ ] Monitoring in place
- [ ] Large repo tests pass
- [ ] Memory usage optimal
- [ ] Documentation updated
- [ ] Code reviewed