# User Story: Project Export

**Story ID**: STORY-037  
**Epic**: EPIC-002 - Project & Asset Management System  
**Story Points**: 5  
**Priority**: Medium  
**Sprint**: Import/Export Sprint (Week 9-10)  

## Story Description

**As a** filmmaker  
**I want** to export my entire project as a portable archive  
**So that** I can share it with collaborators or archive it externally  

## Acceptance Criteria

### Functional Requirements
- [ ] Export complete project as ZIP/TAR archive
- [ ] Include all Git history and LFS files
- [ ] Preserve project structure exactly
- [ ] Option to exclude cache/temp files
- [ ] Option to include dependencies
- [ ] Progress tracking for large exports
- [ ] Resume interrupted exports
- [ ] Export manifest with metadata

### Technical Requirements
- [ ] Export service in `backend/app/services/export.py`
- [ ] API endpoint: `POST /api/v1/projects/{id}/export`
- [ ] Stream-based archive creation
- [ ] Export options:
  ```json
  {
    "format": "zip",  // or "tar.gz"
    "include_history": true,
    "include_cache": false,
    "compress_media": false,
    "split_size_mb": 2000  // Split large archives
  }
  ```
- [ ] Progress via WebSocket
- [ ] Temporary file cleanup
- [ ] Export manifest format:
  ```json
  {
    "export_version": "1.0",
    "project_id": "uuid",
    "exported_at": "2025-01-15T10:00:00Z",
    "export_options": {},
    "statistics": {
      "total_files": 1234,
      "total_size_bytes": 5000000000,
      "git_commits": 45
    }
  }
  ```

### Quality Requirements
- [ ] Export 10GB project < 5 minutes
- [ ] Memory efficient streaming
- [ ] Resumable on failure
- [ ] Archive integrity verification
- [ ] Clear progress indication
- [ ] No data loss or corruption

## Implementation Notes

### Technical Approach
1. **Export Service**:
   ```python
   class ProjectExportService:
       async def export_project(
           self,
           project_id: str,
           options: ExportOptions,
           progress_callback: Callable
       ) -> str:
           # Validate project exists
           # Create temp directory
           # Bundle Git repository
           # Resolve LFS objects
           # Create archive stream
           # Track progress
           # Return archive path
   ```

2. **Streaming Archive Creation**:
   ```python
   async def create_archive_stream(
       source_dir: str,
       output_path: str,
       format: str = "zip"
   ):
       # Use Python zipfile/tarfile
       # Stream files without loading
       # Handle large files specially
       # Update progress periodically
   ```

3. **LFS Object Bundling**:
   ```python
   async def bundle_lfs_objects(repo_path: str, archive: ZipFile):
       # Get LFS object list
       # Copy from .git/lfs/objects
       # Maintain directory structure
       # Update pointers if needed
   ```

### Dependencies
- Git and Git LFS commands
- Python archive libraries
- Stream processing utilities
- WebSocket for progress
- No agent dependencies

### Integration Points
- UI export dialog
- Progress notification area
- Download manager
- Storage cleanup jobs

## Testing Strategy

### Unit Tests
```python
def test_export_small_project():
    # Test basic export functionality
    
def test_export_with_lfs():
    # Test LFS object inclusion
    
def test_export_resume():
    # Test interrupted export resume
    
def test_export_options():
    # Test various option combinations
```

### Integration Tests
- Export real project
- Verify archive contents
- Test import roundtrip
- Large project export
- Progress tracking accuracy

## Definition of Done
- [ ] Export service implemented
- [ ] All options functional
- [ ] Progress tracking working
- [ ] LFS objects included
- [ ] Archive integrity verified
- [ ] Performance targets met
- [ ] API documentation complete
- [ ] Error handling robust
- [ ] Tests passing