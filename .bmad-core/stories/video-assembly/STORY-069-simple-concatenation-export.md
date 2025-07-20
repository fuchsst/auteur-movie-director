# User Story: STORY-069 - Simple Concatenation and Export

## Story Description
**As a** filmmaker
**I want** to concatenate shots into a single video file
**So that** I can create basic final cuts without complex editing features

## Acceptance Criteria

### Functional Requirements
- [ ] Sequential shot concatenation in story order
- [ ] Automatic ordering based on act/chapter/scene structure
- [ ] Basic transition handling (simple cuts)
- [ ] Output file naming based on project and timestamp
- [ ] Save to project exports directory
- [ ] Basic metadata preservation (project info, creation date)

### Technical Requirements
- [ ] Shot ordering algorithm based on story hierarchy
- [ ] File naming convention implementation
- [ ] Directory structure integration (06_Exports/)
- [ ] Basic metadata embedding in output file
- [ ] Progress tracking for concatenation steps
- [ ] Cleanup of temporary files after completion

### Quality Requirements
- [ ] Unit tests for ordering algorithm
- [ ] Integration tests for file operations
- [ ] E2E tests for complete concatenation flow
- [ ] Performance tests for large shot counts
- [ ] File integrity verification tests

## Implementation Notes

### Technical Approach
- **Ordering**: Parse story structure from project.json
- **Concatenation**: Use MoviePy concatenate_videoclips
- **Naming**: Automatic naming with project name + timestamp
- **Storage**: Standard project directory structure

### Component Structure
```
app/services/assembly/
├── concatenation_engine.py
├── story_ordering.py
├── file_naming.py
├── metadata_embedder.py
└── cleanup_manager.py
```

### Shot Ordering Logic
```python
def order_shots_by_story(shots):
    """
    Order shots by: Act → Chapter → Scene → Shot Number
    """
    return sorted(shots, key=lambda s: (
        s.act_number,
        s.chapter_number,
        s.scene_number,
        s.shot_number
    ))
```

### File Naming Convention
```
{project_name}_{timestamp}_{quality}_{format}.{extension}
Example: "MyFilm_20241215_143022_HD_mp4.mp4"
```

### Directory Integration
```
workspace/
└── MyFilm/
    └── 06_Exports/
        └── MyFilm_20241215_143022_HD_mp4.mp4
```

### API Integration
- **Project API**: Get story structure and shot order
- **File API**: Handle file operations in project directories
- **Progress API**: Update frontend with concatenation status

### Testing Strategy
- **Unit Tests**: Ordering algorithm, file naming
- **Integration Tests**: Directory operations, file handling
- **E2E Tests**: Complete concatenation workflow
- **Performance Tests**: 100+ shot concatenation

## Story Size: **Medium (8 story points)**

## Sprint Assignment: **Sprint 2-3 (Phase 1)**

## Dependencies
- **STORY-068**: Basic MoviePy pipeline
- **Project Structure**: Directory organization
- **Story System**: Narrative hierarchy parsing

## Success Criteria
- 10 shots concatenate in correct story order
- Output file saved with proper naming
- Metadata includes project information
- Cleanup removes all temporary files
- Performance handles 50+ shots efficiently