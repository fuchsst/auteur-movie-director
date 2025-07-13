# User Story: Asset Operations

**Story ID**: STORY-031  
**Epic**: EPIC-002 - Project & Asset Management System  
**Story Points**: 5  
**Priority**: High  
**Sprint**: Asset Sprint (Week 3-4)  

## Story Description

**As a** filmmaker  
**I want** to copy assets from the library to my projects  
**So that** I can use shared resources while maintaining project independence  

## Acceptance Criteria

### Functional Requirements
- [ ] Copy asset from workspace library to project
- [ ] Preserve all metadata during copy
- [ ] Update project references automatically
- [ ] Handle duplicate asset names
- [ ] Support batch copying
- [ ] Track asset usage across projects
- [ ] Option to link vs copy (future)
- [ ] Undo copy operation

### Technical Requirements
- [ ] API endpoint: `POST /api/v1/projects/{id}/assets/copy`
- [ ] Atomic copy operations (all or nothing)
- [ ] File integrity verification (checksums)
- [ ] Metadata transformation for project context
- [ ] Reference tracking in project.json
- [ ] Efficient file copying (hard links where possible)
- [ ] WebSocket notification on completion
- [ ] Git LFS tracking for copied files

### Quality Requirements
- [ ] Copy 1GB asset < 5 seconds
- [ ] Handles filesystem errors gracefully
- [ ] Concurrent operations supported
- [ ] No data corruption on failure
- [ ] Clear progress indication
- [ ] Detailed operation logs

## Implementation Notes

### Technical Approach
1. **Copy Operation Flow**:
   ```python
   class AssetOperations:
       async def copy_to_project(
           self,
           asset_id: str,
           project_id: str,
           target_category: str
       ) -> AssetCopy:
           # Validate asset exists
           # Check project structure
           # Generate unique name if needed
           # Copy files with progress
           # Update metadata
           # Add to Git LFS
           # Update project.json references
           # Send completion notification
   ```

2. **Project Asset Reference**:
   ```json
   {
     "assets": {
       "characters": [
         {
           "id": "uuid",
           "name": "Hero Character",
           "source": "workspace_library",
           "original_id": "library_asset_uuid",
           "copied_at": "2025-01-15T10:00:00Z",
           "files": {
             "model": "01_Assets/Characters/Hero/model.safetensors",
             "preview": "01_Assets/Characters/Hero/preview.png"
           }
         }
       ]
     }
   }
   ```

3. **Duplicate Handling**:
   - Check for existing asset with same name
   - Auto-increment: "Character" → "Character_2"
   - Option to replace or rename
   - Preserve original metadata

### Dependencies
- STORY-029 (Asset Service)
- STORY-025 (Project structure)
- STORY-026 (Git LFS integration)
- File operations from EPIC-001
- No agent dependencies

### Integration Points
- Called from Asset Browser drag-drop
- Updates project.json
- Triggers Git commit
- WebSocket progress updates

## Testing Strategy

### Unit Tests
```python
def test_copy_asset_success():
    # Test successful copy operation
    
def test_duplicate_name_handling():
    # Test auto-renaming
    
def test_copy_large_file():
    # Test progress tracking
    
def test_copy_failure_rollback():
    # Test atomic operation
```

### Integration Tests
- Copy asset and verify in project
- Test Git LFS tracking
- Verify metadata preservation
- Test concurrent copies
- Validate reference updates

## Definition of Done
- [ ] Copy operation fully functional
- [ ] Metadata preservation verified
- [ ] Git LFS integration working
- [ ] Progress tracking implemented
- [ ] Error handling comprehensive
- [ ] Performance targets met
- [ ] API documentation complete
- [ ] All tests passing
- [ ] Code reviewed and approved