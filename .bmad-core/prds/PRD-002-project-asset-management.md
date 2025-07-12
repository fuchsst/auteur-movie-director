# Product Requirements Document: Project & Asset Management

## Executive Summary

### Business Justification
The file-based project and asset management system revolutionizes creative production by treating every project as a self-contained, version-controlled unit. This Git-native approach eliminates the chaos of traditional file management while enabling unprecedented collaboration and portability:
- **100% Project Portability**: Projects are self-contained repositories that work anywhere
- **Zero Data Loss Guarantee**: Complete version history through Git + LFS
- **Instant Project Creation**: Automated scaffolding in < 5 seconds
- **Non-Destructive Workflow**: Unlimited takes preserve every creative iteration
- **Professional Standards**: Industry-compliant structure for AI-powered production

### Target User Personas
- **Independent Creators**: Need organized, portable project containers
- **Production Teams**: Require conflict-free collaboration on complex projects
- **Creative Agencies**: Demand reusable assets across multiple productions
- **Freelancers**: Must deliver complete, self-contained projects to clients
- **Educational Institutions**: Teaching next-generation production workflows

### Expected Impact
- Transform chaotic file management into predictable workflows
- Enable true creative experimentation without fear of loss
- Support distributed teams working on same project simultaneously
- Establish new industry standard for AI project organization
- Reduce project handoff time from days to minutes

## Problem Statement

### Current Limitations
1. **Organizational Chaos**: Every creator invents their own folder structure
2. **Version Hell**: Final_v2_REALLY_FINAL_USE_THIS_ONE.mp4
3. **Asset Sprawl**: Files scattered across drives, cloud services, emails
4. **Fragile References**: Moving projects breaks all asset links
5. **No Time Machine**: Yesterday's good version is gone forever

### Pain Points
- "Where did I save that render from last week?"
- "Someone overwrote the good version!"
- "The project is 50GB, how do I send it?"
- "This works on my machine but breaks on yours"
- "We need to go back to Tuesday's version"

### Industry Gaps
- No standard for organizing AI-generated content
- Version control systems not designed for creative workflows
- Large media files still problematic for collaboration
- Missing integration between creation and version control
- No portable project format for generative media

## Solution Overview

### Revolutionary Project-as-Repository Model
Every project IS a Git repository with standardized structure and integrated large file support:

**Two-Tier Organization**
1. **Workspace Level**: Shared studio resources
   - Pipeline Templates
   - Stock Media Library
   - Brand Assets
   - Reusable Components

2. **Project Level**: Self-contained productions
   - Standardized folder structure
   - Git version control built-in
   - project.json manifest
   - Automatic LFS for media files

### Core Innovation: The Takes System
Non-destructive generation workflow where every AI creation is preserved:
```
SHOT-010_v01_take01.mp4
SHOT-010_v01_take02.mp4  ← Each generation preserved
SHOT-010_v01_take03.mp4  ← Easy comparison
SHOT-010_v01_take04.mp4  ← Choose the best
```

## User Stories & Acceptance Criteria

### Epic 1: Instant Project Scaffolding
**As a** creator starting a new project  
**I want to** have everything organized automatically  
**So that** I can start creating immediately

**Acceptance Criteria:**
- [ ] Single click creates complete project structure
- [ ] Git repository initialized with proper .gitignore
- [ ] LFS configured for all media types
- [ ] project.json created with UUID and metadata
- [ ] Initial commit made with timestamp

### Epic 2: Workspace Asset Library
**As a** creative professional  
**I want to** reuse assets across projects  
**So that** I maintain consistency and save time

**Acceptance Criteria:**
- [ ] Drag assets from workspace library to project
- [ ] Automatic copying with reference tracking
- [ ] Preview thumbnails for all visual assets
- [ ] Metadata preservation during copy
- [ ] Usage tracking across projects

### Epic 3: Takes Gallery System
**As an** artist exploring options  
**I want to** generate multiple variations  
**So that** I can select the best result

**Acceptance Criteria:**
- [ ] Each generation creates numbered take
- [ ] Visual gallery shows all takes
- [ ] Side-by-side comparison view
- [ ] One-click active take selection
- [ ] Metadata preserves generation parameters

### Epic 4: Seamless Git Integration
**As a** user unfamiliar with Git  
**I want to** benefit from version control  
**So that** I never lose work

**Acceptance Criteria:**
- [ ] Auto-commit on significant changes
- [ ] Visual timeline of project history
- [ ] One-click rollback to any point
- [ ] Branch creation for experiments
- [ ] Merge resolution for collaboration

### Epic 5: Project Portability
**As a** freelancer delivering work  
**I want to** package complete projects  
**So that** clients can open them anywhere

**Acceptance Criteria:**
- [ ] Export project as self-contained archive
- [ ] Include all dependencies and assets
- [ ] Preserve complete Git history
- [ ] Platform-agnostic format
- [ ] One-click project import

## Technical Requirements

### Development Environment Requirements
- **Git and Git LFS**: Mandatory prerequisites for project creation
- **Automated Scaffolding**: Project structure must be created programmatically
- **Structure Enforcement**: Backend must validate directory layout before operations
- **Template System**: Reusable .gitignore and .gitattributes templates

### Repository Infrastructure Requirements
- **Local Git Server Option**: Support for on-premise Git hosting
- **LFS Storage Backend**: Configurable location for large file storage
- **CI/CD Integration**: Hooks for automated asset processing pipelines
- **Backup Strategy**: Automated repository and LFS backup procedures

### Standardized Project Structure
```
/Generative_Studio_Workspace/
├── Projects/
│   └── MyFilm/
│       ├── project.json         # Project manifest & settings
│       ├── .git/                # Version control
│       ├── .gitignore           # Ignore temp files
│       ├── .gitattributes       # LFS configuration
│       ├── 01_Assets/           # Source materials
│       │   ├── Audio/
│       │   ├── Images/
│       │   └── Video/
│       ├── 02_Source_Creative/  # Canvas saves & scripts
│       │   ├── canvas_graphs/
│       │   ├── story/          # Hierarchical story structure
│       │   │   ├── project_meta.json  # Story framework metadata
│       │   │   ├── concept.md         # Initial concept & logline
│       │   │   ├── outline.md         # Full narrative structure
│       │   │   ├── act_1_setup/       # Act I (25% of story)
│       │   │   │   ├── act_meta.json  # Act purpose & plot points
│       │   │   │   ├── chapter_01_hook/
│       │   │   │   │   ├── chapter_meta.json  # Seven-point mapping
│       │   │   │   │   ├── scene_01_opening_image/
│       │   │   │   │   │   ├── scene_meta.json  # Beat & emotion
│       │   │   │   │   │   ├── beat_sheet.md    # Scene details
│       │   │   │   │   │   ├── shot_001/
│       │   │   │   │   │   │   ├── prompt.json  # Shot parameters
│       │   │   │   │   │   │   └── metadata.json # Camera specs
│       │   │   │   │   │   └── shot_002/
│       │   │   │   │   └── scene_02_setup/
│       │   │   │   └── chapter_02_catalyst/
│       │   │   │       └── scene_03_theme_stated/
│       │   │   ├── act_2_confrontation/  # Act II (50% of story)
│       │   │   │   ├── chapter_03_plot_point_1/
│       │   │   │   ├── chapter_04_pinch_point_1/
│       │   │   │   ├── chapter_05_midpoint/
│       │   │   │   ├── chapter_06_pinch_point_2/
│       │   │   │   └── chapter_07_plot_point_2/
│       │   │   └── act_3_resolution/     # Act III (25% of story)
│       │   │       └── chapter_08_climax/
│       │   └── notes/
│       ├── 03_Renders/          # Generated content mirrors story hierarchy
│       │   ├── act_1_setup/
│       │   │   └── chapter_01_hook/
│       │   │       └── scene_01_opening_image/
│       │   │           └── shot_001/
│       │   │               ├── take_001.mp4
│       │   │               ├── take_002.mp4
│       │   │               └── take_003.mp4
│       │   └── ...
│       ├── 04_Project_Files/    # External app files
│       ├── 05_Cache/            # Temporary (git-ignored)
│       └── 06_Exports/          # Final deliverables
└── Library/                     # Workspace-level assets
    ├── Pipeline_Templates/
    ├── Stock_Media/
    ├── Characters/
    ├── Styles/
    └── Locations/
```

### Asset Browser Implementation
The left panel's Asset Browser provides intuitive organization and discovery:

#### Asset Categories
- **Locations**: Environmental settings and backgrounds
- **Characters**: Reusable character definitions with AI models
- **Music**: Audio tracks and sound libraries
- **Styles**: Visual style definitions for consistent aesthetics

#### Asset Abstraction
Each asset in the browser represents a collection of related files:
- User sees: "Alex" (character)
- System manages: character.json, reference images, LoRA files, voice models
- This abstraction simplifies creative workflows by hiding technical complexity

#### Browser Features
- Hierarchical folder structure within each category
- Visual previews for all asset types
- Drag-and-drop to Production Canvas creates AssetNodes
- Right-click context menu with "Find Usages" option
- Search and filter capabilities across all assets

### Project Manifest Specification
```json
{
    "version": "1.0",
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "My Awesome Film",
    "created": "2025-01-02T10:00:00Z",
    "modified": "2025-01-02T15:30:00Z",
    "quality": "standard",
    "canvas": {
        "nodes": [...],
        "edges": [...],
        "viewport": { "x": 0, "y": 0, "zoom": 1.0 }
    },
    "assets": {
        "characters": [
            {
                "id": "char-001",
                "name": "Hero Character",
                "source": "Library/Characters/hero.json",
                "extractedFrom": "story"  # Auto-created from script
            }
        ],
        "locations": [
            {
                "id": "loc-001",
                "name": "Dark Forest",
                "source": "Library/Locations/dark_forest.json",
                "extractedFrom": "story"
            }
        ],
        "styles": [
            {
                "id": "style-001",
                "name": "Film Noir",
                "source": "Library/Styles/noir.json",
                "inferredFrom": "genre"  # From story metadata
            }
        ]
    },
    "story": {
        "hasBreakdown": true,
        "structure": {
            "type": "three_act",
            "framework": "seven_point",
            "beat_system": "blake_snyder"
        },
        "conceptFile": "02_Source_Creative/story/concept.md",
        "outlineFile": "02_Source_Creative/story/outline.md",
        "metadataFile": "02_Source_Creative/story/project_meta.json",
        "acts": [
            {
                "id": "act_1",
                "name": "Setup",
                "type": "setup",
                "target_percentage": 25,
                "plot_points": ["hook", "plot_point_1"],
                "path": "02_Source_Creative/story/act_1_setup/"
            },
            {
                "id": "act_2",
                "name": "Confrontation",
                "type": "confrontation",
                "target_percentage": 50,
                "plot_points": ["pinch_point_1", "midpoint", "pinch_point_2", "plot_point_2"],
                "path": "02_Source_Creative/story/act_2_confrontation/"
            },
            {
                "id": "act_3",
                "name": "Resolution",
                "type": "resolution",
                "target_percentage": 25,
                "plot_points": ["climax", "resolution"],
                "path": "02_Source_Creative/story/act_3_resolution/"
            }
        ],
        "narrative_arc": {
            "emotional_curve": [],
            "tension_points": [],
            "pacing_rhythm": []
        }
    },
    "settings": {
        "frameRate": 24,
        "resolution": "1920x1080",
        "colorSpace": "sRGB",
        "audioSampleRate": 48000
    }
}
```

### Story Metadata Specification

Each level of the story hierarchy includes metadata files that capture narrative structure:

#### project_meta.json (Story Root)
```json
{
    "structure": "three_act",
    "genre": "thriller",
    "framework": "seven_point",
    "beat_sheet": "blake_snyder",
    "created": "2025-01-02T10:00:00Z",
    "theme": "Power corrupts absolutely",
    "logline": "A detective must confront their own dark past..."
}
```

#### act_meta.json (Act Level)
```json
{
    "act_number": 1,
    "act_type": "setup",
    "purpose": "Establish world, introduce protagonist, present inciting incident",
    "plot_points": ["hook", "inciting_incident", "plot_point_1"],
    "target_duration": 25,
    "emotional_arc": "comfort_to_disruption"
}
```

#### chapter_meta.json (Chapter Level)
```json
{
    "chapter_number": 1,
    "plot_point": "hook",
    "seven_point_function": "starting_point",
    "purpose": "Grab audience attention and establish status quo",
    "scenes_count": 3,
    "beats": ["opening_image", "setup", "theme_stated"]
}
```

#### scene_meta.json (Scene Level)
```json
{
    "scene_number": 1,
    "beat": "opening_image",
    "emotional_state": "ordinary_world",
    "conflict_level": 0,
    "location": "loc-001",
    "characters": ["char-001", "char-002"],
    "duration_estimate": "2:30",
    "mood": "mysterious",
    "tension": 3
}
```

### Git LFS Configuration
```gitattributes
# Images
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.exr filter=lfs diff=lfs merge=lfs -text

# Video
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.webm filter=lfs diff=lfs merge=lfs -text

# Audio
*.wav filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.flac filter=lfs diff=lfs merge=lfs -text

# 3D Models
*.glb filter=lfs diff=lfs merge=lfs -text
*.gltf filter=lfs diff=lfs merge=lfs -text
*.usdz filter=lfs diff=lfs merge=lfs -text

# AI Models (if stored)
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.ckpt filter=lfs diff=lfs merge=lfs -text
```

### Dependency Tracking System

#### Find Usages Workflow
Enables users to track where assets are used across the project:

1. **Initiation Points**:
   - Right-click asset in Asset Browser → "Find Usages"
   - Right-click AssetNode on canvas → "Find Usages"

2. **Processing**:
   - Client-side search through project.json graph data
   - Identifies all edges originating from asset's UUID
   - No backend round-trip required for instant results

3. **UI Response**:
   - Canvas: Highlights all dependent ShotNodes with visual effect
   - Properties Panel: Lists all usages with clickable navigation
   - Cross-scene navigation: Click to jump to any usage location

#### Reverse Navigation
From any shot back to its constituent assets:

1. **Shot Selection**: Click ShotNode or Project Browser item
2. **Properties Display**: Right panel shows all connected assets
3. **Asset Links**: Interactive list of Characters, Styles, etc.
4. **Navigation**: Click asset link to select its node on canvas

#### Dependency Benefits
- **Impact Analysis**: See what's affected before changing an asset
- **Reuse Tracking**: Identify commonly used assets
- **Cleanup**: Find unused assets in the project
- **Collaboration**: Understand asset relationships across team work

### Automated Git Operations
```javascript
class ProjectManager {
    async createProject(name, workspace) {
        const projectPath = path.join(workspace, 'Projects', name);
        
        // 1. Create standardized structure
        await this.scaffoldDirectories(projectPath);
        
        // 2. Initialize Git with LFS
        await git.init(projectPath);
        await this.configureLFS(projectPath);
        
        // 3. Create project manifest
        const manifest = this.generateManifest(name);
        await fs.writeJson(path.join(projectPath, 'project.json'), manifest);
        
        // 4. Initial commit
        await git.add(projectPath, '.');
        await git.commit(projectPath, {
            message: `Initial project creation: ${name}`,
            author: { name: 'Generative Media Studio' }
        });
        
        return projectPath;
    }
    
    async autoCommit(projectPath, message) {
        // Smart auto-commit with batching
        if (this.hasPendingChanges(projectPath)) {
            await git.add(projectPath, '.');
            await git.commit(projectPath, {
                message: `Auto-save: ${message}`,
                author: { name: 'Studio Auto-Save' }
            });
        }
    }
}
```

### Testing Infrastructure Requirements
- **Project Structure Validation**: Automated tests verify scaffolding correctness
- **Git LFS Integration Tests**: Verify large file handling across operations
- **Performance Benchmarks**: Project creation and asset loading speed tests
- **Concurrency Testing**: Multi-user project access scenarios
- **Migration Testing**: Verify project structure upgrades work correctly

### Development Workflow Integration
- **Makefile Commands**: `make new-project` for standardized creation
- **Environment Variables**: `WORKSPACE_ROOT` configuration
- **Docker Volume Mounts**: Workspace accessible to all containers
- **Git Hooks**: Pre-commit validation of project structure
- **CI/CD Pipeline**: Automated testing of project operations

## Success Metrics

### Efficiency Metrics
- **Project Creation**: < 5 seconds from click to ready
- **Asset Discovery**: < 1 second search results
- **Take Generation**: < 100ms file naming
- **Commit Performance**: < 2 seconds for auto-save
- **Sync Speed**: > 50MB/s for LFS transfers

### Reliability Metrics
- **Data Integrity**: 100% file recovery capability
- **Corruption Rate**: < 0.001% over 5 years
- **Merge Success**: > 95% automatic resolution
- **History Depth**: Unlimited with < 1GB overhead
- **Backup Coverage**: Every change captured

### Collaboration Metrics
- **Team Size**: Support 50+ concurrent users
- **Conflict Rate**: < 5% require manual intervention
- **Lock Latency**: < 500ms for binary files
- **Branch Performance**: < 5s for creation/switch
- **Merge Time**: < 30s for typical project

## Risk Assessment

### Technical Risks
1. **LFS Storage Costs**: Large media accumulation
   - *Mitigation*: Periodic cleanup, deduplication
2. **Git Performance**: Large repos slow down
   - *Mitigation*: Shallow clones, sparse checkout
3. **Merge Complexity**: Binary conflicts unresolvable
   - *Mitigation*: Locking protocol, clear ownership

### User Adoption Risks
1. **Git Learning Curve**: Version control concepts
   - *Mitigation*: Visual UI hides Git complexity
2. **Structure Enforcement**: Users want flexibility
   - *Mitigation*: Custom folders within structure
3. **Migration Friction**: Legacy project conversion
   - *Mitigation*: Automated import wizard

## Development Roadmap

### Phase 1: Core Infrastructure (Week 1-2)
- Project scaffolding system
- Git/LFS integration
- project.json specification
- Basic file operations

### Phase 2: Takes System (Week 3-4)
- Take naming conventions
- Gallery UI implementation
- Comparison tools
- Active take selection

### Phase 3: Workspace Library (Week 5-6)
- Asset categorization
- Thumbnail generation
- Drag-drop interface
- Usage tracking

### Phase 4: Collaboration Features (Week 7-8)
- File locking system
- Conflict resolution UI
- Team activity feed
- Permission management

### Story-Driven Asset Creation

When the Story Breakdown System (PRD-007) analyzes scripts, it automatically:

1. **Character Extraction**: Creates Character assets from named entities
2. **Location Discovery**: Identifies and creates Location assets from scene headings
3. **Style Inference**: Suggests visual Style assets based on genre and tone
4. **Asset Linking**: Bidirectional references between story elements and assets

This integration ensures that creative vision flows seamlessly from narrative to visual production, with all necessary assets automatically prepared for the Production Canvas.

## Future Vision

### Advanced Features
- **AI Asset Tagging**: Automatic content analysis
- **Smart Templates**: Learn from successful projects
- **Cloud Sync**: Distributed team support
- **Blockchain Provenance**: Immutable creation history
- **Project Analytics**: Usage patterns and insights

### Ecosystem Integration
- Direct cloud storage backends
- CI/CD pipeline support
- External tool plugins
- Marketplace integration
- Educational resources

---

**Document Version**: 2.0  
**Created**: 2025-01-02  
**Last Updated**: 2025-01-02  
**Status**: Final Draft  
**Owner**: Generative Media Studio Product Team