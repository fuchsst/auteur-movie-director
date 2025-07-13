# User Story: Git Service Extensions

**Story ID**: STORY-034  
**Epic**: EPIC-002 - Project & Asset Management System  
**Story Points**: 5  
**Priority**: Medium  
**Sprint**: Git Sprint (Week 7-8)  

## Story Description

**As a** power user  
**I want** advanced Git features integrated into the platform  
**So that** I can manage project history and collaborate effectively  

## Acceptance Criteria

### Functional Requirements
- [ ] Auto-commit on significant changes
- [ ] Retrieve commit history with diffs
- [ ] Rollback to previous commits
- [ ] Branch creation and switching (future)
- [ ] Commit message templates
- [ ] Batch changes before committing
- [ ] Ignore temporary/cache files
- [ ] Tag important versions

### Technical Requirements
- [ ] Extended GitService methods:
  ```python
  async def auto_commit(project_id: str, changes: List[str])
  async def get_history(project_id: str, limit: int = 50)
  async def rollback(project_id: str, commit_hash: str)
  async def create_tag(project_id: str, tag_name: str)
  ```
- [ ] Smart commit batching:
  - Batch window: 5 minutes
  - Max batch size: 50 files
  - Immediate commit for major changes
- [ ] Commit message generation:
  - Descriptive based on changes
  - Include changed file categories
  - Reference take numbers
- [ ] API endpoints:
  ```
  POST /api/v1/git/{project}/commit
  GET  /api/v1/git/{project}/history
  POST /api/v1/git/{project}/rollback
  POST /api/v1/git/{project}/tags
  ```

### Quality Requirements
- [ ] Commit operations < 2 seconds
- [ ] History retrieval < 1 second
- [ ] No repository corruption
- [ ] Thread-safe operations
- [ ] Clear rollback warnings
- [ ] Comprehensive logging

## Implementation Notes

### Technical Approach
1. **Auto-commit Logic**:
   ```python
   class AutoCommitManager:
       def __init__(self, batch_window=300):  # 5 minutes
           self.pending_changes = {}
           self.timers = {}
           
       async def track_change(self, project_id: str, file_path: str):
           # Add to pending changes
           # Reset/start timer
           # Check if immediate commit needed
           
       async def commit_batch(self, project_id: str):
           # Generate commit message
           # Execute commit
           # Clear pending changes
   ```

2. **Commit Message Templates**:
   ```python
   def generate_commit_message(changes: List[FileChange]) -> str:
       # Analyze changes
       # Group by type
       # Generate descriptive message
       # Examples:
       # "Add 3 character assets and update scene composition"
       # "Generate take_015 for shot_003 with style adjustments"
       # "Update project settings and clean up exports"
   ```

3. **History Response Format**:
   ```json
   {
     "commits": [
       {
         "hash": "abc123",
         "message": "Generate take_015 for shot_003",
         "author": "user@example.com",
         "timestamp": "2025-01-15T10:00:00Z",
         "stats": {
           "files_changed": 5,
           "additions": 100,
           "deletions": 20
         },
         "files": [
           "03_Renders/shot_003/take_015/output.mp4"
         ]
       }
     ]
   }
   ```

### Dependencies
- STORY-026 (Basic Git integration)
- Git 2.25+ with porcelain commands
- Background task processing
- No agent dependencies

### Integration Points
- Triggered by file operations
- UI shows commit history
- Rollback confirmation dialog
- WebSocket notifications

## Testing Strategy

### Unit Tests
```python
def test_auto_commit_batching():
    # Test batch window behavior
    
def test_commit_message_generation():
    # Test various change scenarios
    
def test_rollback_safety():
    # Test rollback warnings
    
def test_concurrent_commits():
    # Test thread safety
```

### Integration Tests
- Make changes and verify auto-commit
- Test rollback functionality
- Verify history accuracy
- Test tag creation
- Validate performance

## Definition of Done
- [ ] Auto-commit fully functional
- [ ] History API implemented
- [ ] Rollback with safety checks
- [ ] Tag support added
- [ ] Commit messages descriptive
- [ ] Performance targets met
- [ ] Thread safety verified
- [ ] API documentation complete
- [ ] All tests passing