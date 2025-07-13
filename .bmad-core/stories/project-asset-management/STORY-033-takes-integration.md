# User Story: Takes Integration

**Story ID**: STORY-033  
**Epic**: EPIC-002 - Project & Asset Management System  
**Story Points**: 3  
**Priority**: High  
**Sprint**: Takes Sprint (Week 5-6)  

## Story Description

**As a** platform developer  
**I want** takes to be fully integrated with Git LFS and thumbnails  
**So that** the system provides a complete versioning solution  

## Acceptance Criteria

### Functional Requirements
- [ ] Automatic thumbnail generation for each take
- [ ] Git LFS tracking for all take media files
- [ ] Cleanup of orphaned takes (no parent shot)
- [ ] Take metadata includes generation parameters
- [ ] Bulk operations on takes (delete old, archive)
- [ ] Take comparison metadata extraction
- [ ] Storage usage tracking per project

### Technical Requirements
- [ ] Thumbnail service in `backend/app/services/thumbnails.py`
- [ ] Integration with existing TakesService
- [ ] Thumbnail specifications:
  - Format: PNG
  - Size: 512x512px
  - Video: Frame at 1 second
  - Image: Scaled with aspect ratio
- [ ] Git LFS automatic tracking for:
  - Take output files (mp4, png, etc.)
  - Generated thumbnails
- [ ] Cleanup job for orphaned files
- [ ] Storage metrics API endpoint

### Quality Requirements
- [ ] Thumbnail generation < 2 seconds
- [ ] No storage leaks from deleted takes
- [ ] Git LFS tracking 100% reliable
- [ ] Concurrent thumbnail generation
- [ ] Graceful handling of corrupt media
- [ ] Storage metrics accurate ±1MB

## Implementation Notes

### Technical Approach
1. **Thumbnail Service**:
   ```python
   class ThumbnailService:
       async def generate_thumbnail(
           self,
           source_path: str,
           output_path: str,
           size: Tuple[int, int] = (512, 512)
       ) -> bool:
           # Detect media type
           # Extract frame or scale image
           # Save as PNG
           # Return success status
   ```

2. **Enhanced Take Creation**:
   ```python
   async def create_take_with_media(
       self,
       project_id: str,
       shot_id: str,
       media_file: str,
       metadata: dict
   ) -> Take:
       # Create take directory
       # Copy media file
       # Generate thumbnail
       # Add to Git LFS
       # Create take metadata
       # Git commit
   ```

3. **Storage Metrics**:
   ```json
   {
     "project_id": "uuid",
     "total_size_bytes": 1073741824,
     "takes_count": 45,
     "breakdown": {
       "renders": 900000000,
       "thumbnails": 50000000,
       "assets": 123741824
     }
   }
   ```

### Dependencies
- STORY-021 (Takes Service base)
- STORY-026 (Git LFS setup)
- FFmpeg for video thumbnails
- Pillow for image processing
- No agent dependencies

### Integration Points
- Called after every generation
- Cleanup runs on take deletion
- Storage metrics in project API
- Thumbnail URLs in take metadata

## Testing Strategy

### Unit Tests
```python
def test_thumbnail_generation_image():
    # Test image thumbnail creation
    
def test_thumbnail_generation_video():
    # Test video frame extraction
    
def test_lfs_tracking_verification():
    # Verify files tracked in LFS
    
def test_storage_cleanup():
    # Test orphan file removal
```

### Integration Tests
- Generate take with thumbnail
- Verify Git LFS tracking
- Delete take and check cleanup
- Test concurrent operations
- Validate storage metrics

## Definition of Done
- [ ] Thumbnail generation working
- [ ] Git LFS integration complete
- [ ] Cleanup job implemented
- [ ] Storage metrics accurate
- [ ] All media types supported
- [ ] Error handling robust
- [ ] Performance targets met
- [ ] Tests passing
- [ ] Documentation updated