# User Story: Project Scaffolding Service

**Story ID**: STORY-025  
**Epic**: EPIC-002 - Project & Asset Management System  
**Story Points**: 5  
**Priority**: Critical  
**Sprint**: Foundation Sprint (Week 1-2)  
**Status**: ✅ Completed  
**Implementation Date**: 2025-01-13  

## Story Description

**As a** filmmaker using the platform  
**I want** to create new projects with a standardized structure in one click  
**So that** I can start working immediately without manual setup  

## Acceptance Criteria

### Functional Requirements
- [ ] Single-click project creation from UI with name input
- [ ] Directory structure created according to PRD-002 specification
- [ ] project.json manifest generated with:
  - Unique UUID
  - Project name and creation timestamp
  - Initial metadata (creator, version, structure version)
  - Empty canvas state
- [ ] Initial .gitignore created with platform defaults
- [ ] Initial .gitattributes configured for LFS patterns
- [ ] Project validation passes after creation
- [ ] Success notification shows project location

### Technical Requirements
- [ ] Service implemented in `backend/app/services/workspace.py`
- [ ] API endpoint `POST /api/v1/workspace/projects` accepts project name
- [ ] Structure creation is atomic (all or nothing)
- [ ] Proper error handling for:
  - Duplicate project names
  - Invalid characters in names
  - Insufficient permissions
  - Disk space issues
- [ ] WebSocket notification on completion
- [ ] Project structure follows exact specification:
  ```
  PROJECT_NAME/
  ├── project.json
  ├── .gitignore
  ├── .gitattributes
  ├── 01_Assets/
  │   ├── Characters/
  │   ├── Styles/
  │   └── Locations/
  ├── 02_Story/
  ├── 03_Renders/
  ├── 04_Compositions/
  ├── 05_Audio/
  └── 06_Exports/
  ```

### Quality Requirements
- [ ] Unit tests cover all creation scenarios
- [ ] Integration test validates full structure
- [ ] Performance: < 2 seconds for creation
- [ ] Concurrent creation handles race conditions
- [ ] API documentation includes examples
- [ ] Error messages are user-friendly

## Implementation Notes

### Technical Approach
1. **Backend Service Implementation**:
   ```python
   class WorkspaceService:
       async def create_project(self, name: str, creator: str) -> Project:
           # Validate name
           # Generate UUID
           # Create directory structure
           # Generate project.json
           # Create Git files
           # Return project instance
   ```

2. **Project Manifest Schema**:
   ```json
   {
     "id": "uuid-v4",
     "name": "Project Name",
     "version": "1.0.0",
     "structure_version": "1.0",
     "created_at": "2025-01-15T10:00:00Z",
     "created_by": "user@example.com",
     "metadata": {
       "description": "",
       "tags": [],
       "settings": {}
     },
     "canvas_state": null
   }
   ```

3. **API Contract**:
   - Request: `{"name": "My New Project"}`
   - Response: `{"id": "uuid", "path": "/workspace/projects/My_New_Project"}`

### Dependencies
- EPIC-001 stories completed:
  - STORY-004 (File Management API) - For filesystem operations
  - STORY-001 (FastAPI Setup) - For API framework
- No external agent dependencies
- Filesystem permissions configured

### Integration Points
- GitService will be integrated in STORY-026
- Frontend will consume via API client
- WebSocket will notify project browser

## Testing Strategy

### Unit Tests
```python
def test_create_project_success():
    # Test successful project creation
    
def test_create_project_duplicate_name():
    # Test handling of duplicate names
    
def test_create_project_invalid_characters():
    # Test name validation
    
def test_create_project_atomic_failure():
    # Test rollback on partial failure
```

### Integration Tests
- End-to-end project creation flow
- Verify all directories and files created
- Test concurrent project creation
- Validate project.json schema

## Definition of Done
- [x] Code implemented and passing all tests
- [x] API endpoint documented in OpenAPI spec
- [x] Code reviewed and approved
- [x] Performance benchmarks met
- [x] Error scenarios handled gracefully
- [x] WebSocket notifications working
- [x] Manual testing completed

## Implementation Notes

### Changes Made:
1. Updated `WorkspaceService` to match PRD-002 directory structure (removed extra directories)
2. Added `.gitattributes` generation with Git LFS patterns for media files
3. Added WebSocket notification on project creation
4. Fixed datetime deprecation warnings by using `timezone.utc`
5. Added comprehensive test suite with 15 test cases covering all acceptance criteria
6. Added missing image formats (PNG, JPG, JPEG, GIF, WEBP) to Git LFS extensions

### Test Coverage:
- All 15 tests passing
- Covers all functional requirements
- Includes performance testing (< 2 seconds)
- Validates atomic creation and error handling
- Tests concurrent project creation