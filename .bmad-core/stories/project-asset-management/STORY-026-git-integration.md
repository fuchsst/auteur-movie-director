# User Story: Git Integration

**Story ID**: STORY-026  
**Epic**: EPIC-002 - Project & Asset Management System  
**Story Points**: 5  
**Priority**: Critical  
**Sprint**: Foundation Sprint (Week 1-2)  

## Story Description

**As a** content creator  
**I want** my projects to be version-controlled automatically  
**So that** I never lose work and can track all changes  

## Acceptance Criteria

### Functional Requirements
- [ ] Git repository initialized for new projects automatically
- [ ] Git LFS configured with comprehensive media patterns
- [ ] Initial commit created with message "Initial project setup"
- [ ] .gitignore includes platform-specific exclusions
- [ ] Git config sets user info from current session
- [ ] Repository status accessible via API
- [ ] LFS tracks files > 10MB automatically

### Technical Requirements
- [ ] GitService implemented in `backend/app/services/git.py`
- [ ] GitLFSService implemented in `backend/app/services/git_lfs.py`
- [ ] API endpoints:
  - `POST /api/v1/git/{project}/init` (if manual init needed)
  - `GET /api/v1/git/{project}/status`
  - `GET /api/v1/git/{project}/config`
- [ ] Git operations are atomic and thread-safe
- [ ] Proper error handling for:
  - Git not installed
  - LFS not installed
  - Permission issues
  - Corrupted repositories
- [ ] Git LFS patterns comprehensive:
  ```gitattributes
  # Images
  *.png filter=lfs diff=lfs merge=lfs -text
  *.jpg filter=lfs diff=lfs merge=lfs -text
  *.jpeg filter=lfs diff=lfs merge=lfs -text
  *.gif filter=lfs diff=lfs merge=lfs -text
  *.webp filter=lfs diff=lfs merge=lfs -text
  
  # Video
  *.mp4 filter=lfs diff=lfs merge=lfs -text
  *.mov filter=lfs diff=lfs merge=lfs -text
  *.avi filter=lfs diff=lfs merge=lfs -text
  *.webm filter=lfs diff=lfs merge=lfs -text
  
  # Audio
  *.wav filter=lfs diff=lfs merge=lfs -text
  *.mp3 filter=lfs diff=lfs merge=lfs -text
  *.flac filter=lfs diff=lfs merge=lfs -text
  
  # 3D/AI Models
  *.safetensors filter=lfs diff=lfs merge=lfs -text
  *.ckpt filter=lfs diff=lfs merge=lfs -text
  *.bin filter=lfs diff=lfs merge=lfs -text
  ```

### Quality Requirements
- [ ] Unit tests for all Git operations
- [ ] Integration tests with real Git commands
- [ ] Performance: Git init < 1 second
- [ ] Handles concurrent Git operations safely
- [ ] Graceful degradation if Git/LFS unavailable
- [ ] Clear error messages for users

## Implementation Notes

### Technical Approach
1. **GitService Core Methods**:
   ```python
   class GitService:
       async def init_repository(self, project_path: str) -> bool:
           # Initialize Git repo
           # Configure Git LFS
           # Set local config
           # Create initial commit
           
       async def get_status(self, project_path: str) -> GitStatus:
           # Return current status
           
       async def add_and_commit(self, project_path: str, message: str):
           # Stage all changes
           # Create commit
   ```

2. **GitLFSService Integration**:
   ```python
   class GitLFSService:
       def setup_lfs(self, repo_path: str):
           # Install LFS hooks
           # Configure tracking patterns
           
       def track_file(self, repo_path: str, file_path: str):
           # Add file to LFS if needed
   ```

3. **Integration with Project Creation**:
   - Called automatically after directory structure created
   - Wrapped in try/catch to not block project creation
   - Logs warnings if Git operations fail

### Dependencies
- STORY-025 must be complete (provides project structure)
- Git 2.25+ installed on system
- Git LFS 2.9+ installed on system
- No agent dependencies

### Integration Points
- WorkspaceService calls GitService.init_repository
- Future stories will use for commits (STORY-034)
- Status endpoint used by frontend

## Testing Strategy

### Unit Tests
```python
def test_init_repository_success():
    # Test successful repo initialization
    
def test_lfs_pattern_configuration():
    # Verify all patterns tracked
    
def test_init_without_git_installed():
    # Test graceful failure
    
def test_concurrent_git_operations():
    # Test thread safety
```

### Integration Tests
- Create project and verify Git repo exists
- Verify LFS hooks installed
- Test large file automatic tracking
- Validate initial commit created

## Definition of Done
- [ ] GitService fully implemented
- [ ] GitLFSService tracking patterns working
- [ ] API endpoints documented
- [ ] All tests passing
- [ ] Error handling comprehensive
- [ ] Performance benchmarks met
- [ ] Code reviewed and approved
- [ ] Manual testing with large files