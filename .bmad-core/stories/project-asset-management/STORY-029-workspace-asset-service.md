# User Story: Workspace Asset Service

**Story ID**: STORY-029  
**Epic**: EPIC-002 - Project & Asset Management System  
**Story Points**: 5  
**Priority**: High  
**Sprint**: Asset Sprint (Week 3-4)  

## Story Description

**As a** creative professional  
**I want** a centralized library of reusable assets  
**So that** I can quickly access characters, styles, and locations across projects  

## Acceptance Criteria

### Functional Requirements
- [ ] Asset categories: Characters, Styles, Locations, Music
- [ ] Assets stored in workspace-level library
- [ ] Each asset has metadata JSON file
- [ ] Asset preview images generated/stored
- [ ] Import assets from files with validation
- [ ] List assets by category with filtering
- [ ] Search assets by name and tags
- [ ] Asset versioning support

### Technical Requirements
- [ ] AssetService in `backend/app/services/assets.py`
- [ ] Asset storage structure:
  ```
  workspace/
  └── Library/
      ├── Characters/
      │   └── {asset_name}/
      │       ├── asset.json
      │       ├── preview.png
      │       └── model.safetensors
      ├── Styles/
      ├── Locations/
      └── Music/
  ```
- [ ] API endpoints:
  ```
  GET    /api/v1/workspace/assets
  GET    /api/v1/workspace/assets/{category}
  GET    /api/v1/workspace/assets/{category}/{id}
  POST   /api/v1/workspace/assets/{category}
  DELETE /api/v1/workspace/assets/{category}/{id}
  ```
- [ ] Metadata schema validation
- [ ] File type validation per category
- [ ] Automatic thumbnail generation

### Quality Requirements
- [ ] Unit tests for asset operations
- [ ] Integration tests with filesystem
- [ ] Performance: List 1000 assets < 500ms
- [ ] Concurrent access handling
- [ ] Storage optimization (deduplication)
- [ ] Clear error messages

## Implementation Notes

### Technical Approach
1. **Asset Metadata Schema**:
   ```json
   {
     "id": "uuid",
     "name": "Character Name",
     "category": "Characters",
     "type": "lora",
     "version": "1.0",
     "created_at": "2025-01-15T10:00:00Z",
     "updated_at": "2025-01-15T10:00:00Z",
     "tags": ["female", "fantasy", "warrior"],
     "metadata": {
       "description": "A fierce warrior character",
       "model_info": {
         "base_model": "SDXL",
         "training_steps": 5000
       }
     },
     "files": {
       "model": "model.safetensors",
       "preview": "preview.png",
       "config": "config.json"
     }
   }
   ```

2. **Service Implementation**:
   ```python
   class AssetService:
       async def import_asset(
           self,
           category: str,
           name: str,
           files: Dict[str, UploadFile],
           metadata: Dict
       ) -> Asset:
           # Validate category
           # Generate UUID
           # Create asset directory
           # Save files
           # Generate preview if needed
           # Create asset.json
           # Return asset instance
   ```

3. **Preview Generation**:
   - Images: Resize to 512x512
   - Videos: Extract frame at 1s
   - Audio: Generate waveform
   - 3D: Render thumbnail

### Dependencies
- File management utilities (EPIC-001)
- Image processing library (Pillow)
- No direct agent dependencies
- Storage permissions configured

### Integration Points
- Asset Browser UI will consume this API
- Project copy operations use this service
- Future: AI models may reference assets

## Testing Strategy

### Unit Tests
```python
def test_import_character_asset():
    # Test character import with LoRA
    
def test_asset_categorization():
    # Test category validation
    
def test_duplicate_asset_handling():
    # Test name collision resolution
    
def test_asset_search():
    # Test search functionality
```

### Integration Tests
- Import various file types
- Verify storage structure
- Test concurrent imports
- Validate preview generation

## Definition of Done
- [ ] AssetService fully implemented
- [ ] All CRUD operations working
- [ ] Preview generation functional
- [ ] API endpoints documented
- [ ] Metadata validation complete
- [ ] Tests achieving 90% coverage
- [ ] Performance benchmarks met
- [ ] Code reviewed and approved