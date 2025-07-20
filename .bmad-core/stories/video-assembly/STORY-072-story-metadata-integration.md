# User Story: STORY-072 - Story Metadata Integration

## Story Description
**As a** filmmaker
**I want** comprehensive story metadata preserved in the assembly process
**So that** the narrative structure and creative intent remain intact through post-production

## Acceptance Criteria

### Functional Requirements
- [ ] Extract story structure from project.json (acts, chapters, scenes)
- [ ] Map narrative beats to timeline positions
- [ ] Include character development arcs in metadata
- [ ] Preserve emotional beat sheet information
- [ ] Generate structural markers for timeline navigation
- [ ] Include generation parameters and prompts

### Technical Requirements
- [ ] Parse story hierarchy from project structure
- [ ] Calculate timeline positions for story elements
- [ ] Create metadata extraction pipeline
- [ ] Generate timeline markers for NLEs
- [ ] Store metadata in EDL comments and sidecar files
- [ ] Validate metadata completeness and accuracy

### Quality Requirements
- [ ] Unit tests for metadata extraction
- [ ] Integration tests for story structure parsing
- [ ] Validation tests for timeline accuracy
- [ ] Performance tests for large projects
- [ ] Metadata round-trip testing

## Implementation Notes

### Technical Approach
- **Parsing**: Story structure extraction from project.json
- **Calculation**: Timeline position mapping
- **Storage**: EDL comments and JSON sidecar files
- **Validation**: Accuracy and completeness checks

### Component Structure
```
app/services/metadata/
├── story_structure_parser.py
├── timeline_calculator.py
├── metadata_extractor.py
├── marker_generator.py
└── metadata_validator.py
```

### Story Structure Data Model
```python
class StoryStructure:
    acts: List[Act]
    chapters: List[Chapter]
    scenes: List[Scene]
    beats: List[Beat]
    characters: List[CharacterArc]

class Act:
    number: int
    title: str
    start_time: float
    end_time: float
    emotional_arc: str

class Beat:
    type: str  # "all_is_lost", "climax", etc.
    position: float  # Timeline position
    intensity: float  # 0.0 to 1.0
    description: str
```

### Timeline Calculation
```python
def calculate_story_timeline(shots, story_structure):
    """
    Map story elements to timeline positions based on shot durations
    """
    timeline = []
    current_time = 0.0
    
    for shot in shots:
        # Map story elements to this shot's time range
        story_elements = get_story_elements_for_shot(shot)
        timeline.extend(map_to_timeline(story_elements, current_time, shot.duration))
        current_time += shot.duration
    
    return timeline
```

### Metadata Storage Formats
```
# EDL Comments
* FROM CLIP NAME: Shot_001
* COMMENT: Act 1, Scene 3, Beat: Inciting Incident, Character: John
* METADATA: {"generation_params": {"cfg_scale": 7.5, "seed": 12345}}

# Sidecar JSON
{
  "story_structure": {
    "acts": [...],
    "beats": [...],
    "character_arcs": [...]
  },
  "timeline_markers": [...]
}
```

### Integration Points
- **Project System**: Story structure extraction
- **Take System**: Generation parameters from takes
- **EDL System**: Metadata embedding in EDL files
- **NLE Integration**: Timeline markers for professional tools

### API Endpoints Required
- `GET /api/v1/projects/{id}/story-structure` - Get story data
- `POST /api/v1/assembly/metadata` - Generate metadata
- `GET /api/v1/assembly/metadata/{id}` - Get metadata
- `POST /api/v1/assembly/markers` - Generate timeline markers

### Professional Integration
- **Adobe Premiere**: Marker import via XML
- **DaVinci Resolve**: Timeline markers via EDL
- **Final Cut Pro**: XML metadata integration
- **Professional Workflows**: Industry standard metadata

### Testing Strategy
- **Unit Tests**: Story parsing, timeline calculation
- **Integration Tests**: Metadata extraction pipeline
- **Validation Tests**: Timeline accuracy verification
- **NLE Tests**: Professional tool compatibility

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 3-4 (Phase 2)**

## Dependencies
- **STORY-071**: EDL generation for metadata embedding
- **Story System**: Narrative structure data access
- **Take System**: Generation parameter extraction
- **Project Structure**: File organization for sidecar files

## Success Criteria
- Complete story structure extracted from project
- Timeline positions calculated accurately for all elements
- Metadata embedded correctly in EDL files
- Timeline markers import successfully into Adobe Premiere
- Large projects (500+ shots) handle metadata efficiently
- Character arcs and emotional beats preserved accurately