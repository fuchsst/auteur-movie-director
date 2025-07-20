# User Story: STORY-071 - CMX3600 EDL Format Generator

## Story Description
**As a** professional editor
**I want** industry-standard EDL files in CMX3600 format
**So that** I can seamlessly integrate with professional NLE workflows

## Acceptance Criteria

### Functional Requirements
- [ ] Generate valid CMX3600 format EDL files
- [ ] Include comprehensive story metadata (acts, chapters, scenes)
- [ ] Preserve take information and generation parameters
- [ ] Support for standard EDL fields (TITLE, FCM, etc.)
- [ ] Professional compatibility with Adobe Premiere, DaVinci Resolve, Final Cut Pro
- [ ] Automatic EDL file naming and organization

### Technical Requirements
- [ ] CMX3600 format compliance validation
- [ ] Story structure mapping to EDL events
- [ ] Take metadata extraction and inclusion
- [ ] Timecode calculation and formatting
- [ ] File path resolution for source media
- [ ] UTF-8 text encoding for international support

### Quality Requirements
- [ ] Unit tests for EDL format validation
- [ ] Integration tests with major NLEs
- [ ] Round-trip testing (EDL → NLE → EDL)
- [ ] Performance tests for large projects
- [ ] Format compliance verification tests

## Implementation Notes

### Technical Approach
- **Format**: CMX3600 standard compliance
- **Metadata**: Comprehensive story structure preservation
- **Integration**: Project directory structure mapping
- **Validation**: Professional NLE compatibility testing

### Component Structure
```
app/services/assembly/
├── edl_generator.py
├── cmx3600_formatter.py
├── story_metadata_extractor.py
├── timecode_calculator.py
└── edl_validator.py
```

### CMX3600 Format Structure
```
TITLE: MyFilm_Assembly
FCM: NON-DROP FRAME

001  AX       V     C        00:00:00:00 00:00:05:12 00:00:00:00 00:00:05:12
* FROM CLIP NAME: Shot_001_Act1_Scene1_Take3
* COMMENT: Act 1, Scene 1, Beat: Setup
```

### Story Metadata Mapping
```python
class EDLMetadata:
    act_number: int
    chapter_number: int  
    scene_number: int
    beat_type: str
    take_number: int
    generation_params: dict
    character_assets: list[str]
    style_assets: list[str]
```

### Directory Integration
```
workspace/
└── MyFilm/
    └── 04_Project_Files/
        └── assemblies/
            └── MyFilm_Edit_20241215_143022.edl
```

### API Endpoints Required
- `POST /api/v1/assembly/edl` - Generate EDL file
- `GET /api/v1/assembly/edl/{id}` - Get EDL content
- `GET /api/v1/assembly/edl/{id}/validate` - Validate format
- `POST /api/v1/assembly/edl/{id}/export` - Export for NLE

### Professional NLE Testing
- **Adobe Premiere Pro**: Import and timeline validation
- **DaVinci Resolve**: Color and metadata preservation
- **Final Cut Pro**: XML conversion compatibility
- **Avid Media Composer**: Professional broadcast validation

### Testing Strategy
- **Unit Tests**: Format compliance, metadata extraction
- **Integration Tests**: NLE import/export workflows
- **Validation Tests**: CMX3600 format verification
- **Round-trip Tests**: EDL → NLE → EDL integrity

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 3-4 (Phase 2)**

## Dependencies
- **STORY-069**: Simple concatenation for basic EDL
- **Story System**: Narrative structure data
- **Take System**: Take metadata extraction
- **Project Structure**: File organization

## Success Criteria
- EDL imports correctly into Adobe Premiere Pro
- All story metadata preserved in EDL comments
- Take information included for each shot
- Professional format compliance verified
- Large projects (500+ shots) handle efficiently