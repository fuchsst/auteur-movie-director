# Story: Project Structure Definition

**Story ID**: STORY-002  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Infrastructure  
**Points**: 5 (Medium)  
**Priority**: Critical  

## Story Description
As a developer, I need to implement a **programmatically enforced** project structure that serves as the foundation for the Project-as-Repository architectural model. This structure must be treated as an API contract where any deviation is a breaking change. The implementation must include automated scaffolding through the Makefile command system, ensuring that every project follows the exact same directory hierarchy with mandatory Git LFS configuration.

## Acceptance Criteria

### Functional Requirements
- [ ] Workspace/Project two-tier hierarchy is enforced programmatically
- [ ] Project creation is automated via `make new-project` command (mission-critical)
- [ ] Numbered directory structure (01_Assets through 06_Exports) is created exactly as specified
- [ ] Git repository initializes with mandatory Git LFS configuration
- [ ] .gitattributes template is automatically applied with proper LFS tracking rules
- [ ] Project.json schema is defined, validated, and serves as single source of truth
- [ ] Directory structure deviation triggers validation errors (structure as API contract)

### Technical Requirements
- [ ] Implement workspace directory creation with strict validation
- [ ] Create automated scaffolding function that enforces exact structure
- [ ] Define TypeScript/Python models for project.json with schema validation
- [ ] Use GitPython for repository initialization with Git LFS setup
- [ ] Generate .gitattributes from template with proper file type tracking
- [ ] Implement structure validation that treats deviations as breaking changes
- [ ] Ensure cross-platform path compatibility while maintaining structure integrity
- [ ] Integrate with Makefile command system for `make new-project`

### Project Structure Requirements (API Contract)
```
workspace/                    # Two-tier hierarchy root
└── {project-name}/          # Project-as-Repository
    ├── .git/                # Git repository with LFS
    ├── .gitattributes       # Auto-generated LFS tracking rules
    ├── project.json         # Project manifest (source of truth)
    ├── 01_Assets/           # Source materials (numbered for consistency)
    │   ├── Scripts/         # Screenplay files (.fountain, .md)
    │   ├── Characters/      # Character definitions & LoRAs
    │   ├── Styles/          # Visual style references
    │   ├── Environments/    # Location assets & references
    │   └── Audio/           # Sound effects & music
    ├── 02_Generated/        # AI-generated content
    │   ├── Images/          # Generated frames & stills
    │   ├── Videos/          # Generated video clips
    │   ├── Audio/           # Generated dialogue & sounds
    │   └── Metadata/        # Generation parameters & logs
    ├── 03_Takes/            # Version history (non-destructive)
    │   └── {timestamp}/     # Timestamped snapshots
    ├── 04_Previews/         # Working previews
    │   ├── Dailies/         # Low-res daily outputs
    │   └── Rough_Cuts/      # Assembly edits
    ├── 05_Production/       # Production workspace
    │   ├── Scenes/          # Scene organization
    │   ├── Shots/           # Shot breakdowns
    │   └── Timelines/       # Edit timelines
    └── 06_Exports/          # Final deliverables
        ├── EDL/             # Edit decision lists
        ├── Masters/         # Final renders
        └── Deliverables/    # Distribution formats
```

**CRITICAL**: This structure is programmatically enforced. Any deviation is a breaking change to the system.

## Implementation Notes

### Project.json Schema
```typescript
interface ProjectManifest {
  id: string;           // UUID
  name: string;         // Human-readable name
  created: string;      // ISO 8601 timestamp
  modified: string;     // ISO 8601 timestamp
  version: string;      // Schema version (1.0.0)
  quality: 'draft' | 'standard' | 'premium';
  
  settings: {
    fps: number;        // Default 24
    resolution: [number, number];  // [1920, 1080]
    aspectRatio: string;  // "16:9"
  };
  
  canvas: {
    nodes: any[];       // Node positions/data
    edges: any[];       // Connections
    viewport: {         // Camera position
      x: number;
      y: number;
      zoom: number;
    };
  };
  
  metadata: {
    gitCommit?: string;
    lastExport?: string;
    totalFrames?: number;
  };
}
```

### Python Service Implementation
```python
# backend/app/services/workspace.py
class WorkspaceService:
    # Numbered directories as API contract
    REQUIRED_STRUCTURE = [
        "01_Assets/Scripts",
        "01_Assets/Characters",
        "01_Assets/Styles",
        "01_Assets/Environments",
        "01_Assets/Audio",
        "02_Generated/Images",
        "02_Generated/Videos",
        "02_Generated/Audio",
        "02_Generated/Metadata",
        "03_Takes",
        "04_Previews/Dailies",
        "04_Previews/Rough_Cuts",
        "05_Production/Scenes",
        "05_Production/Shots",
        "05_Production/Timelines",
        "06_Exports/EDL",
        "06_Exports/Masters",
        "06_Exports/Deliverables"
    ]
    
    def create_project_structure(self, project_name: str) -> Path:
        """Create enforced project directory structure"""
        
    def initialize_git_with_lfs(self, project_path: Path) -> None:
        """Initialize Git repository with LFS and .gitattributes template"""
        
    def generate_gitattributes(self, project_path: Path) -> None:
        """Generate .gitattributes with proper LFS tracking rules"""
        
    def validate_structure(self, project_path: Path) -> bool:
        """Validate project structure integrity (breaking change detection)"""
        
    def create_project_manifest(self, project_path: Path, config: dict) -> None:
        """Create and save project.json as source of truth"""
```

### Makefile Integration
```makefile
# Makefile command for automated project creation
new-project:
	@echo "Creating new Auteur project..."
	@python scripts/create_project.py $(NAME)
```

## Dependencies
- GitPython library for Git operations with LFS support
- git-lfs binary must be installed on system
- JSON schema validation library (jsonschema)
- File system permissions for directory creation
- Makefile command integration
- .gitattributes template file

## Testing Criteria
- [ ] `make new-project` command creates complete structure
- [ ] All numbered directories (01-06) are created in exact order
- [ ] Git LFS is properly initialized and configured
- [ ] .gitattributes is generated with correct tracking rules
- [ ] Structure validation detects any deviations
- [ ] Invalid project names are rejected with clear errors
- [ ] Project.json validates against schema
- [ ] Cross-platform compatibility is verified
- [ ] Attempting to modify structure programmatically fails validation

## Definition of Done
- [ ] Workspace service implements enforced structure creation
- [ ] `make new-project` command is integrated and tested
- [ ] Project.json schema defined in both TypeScript and Python
- [ ] Git initialization includes LFS and .gitattributes template
- [ ] Structure validation prevents any deviations
- [ ] Unit tests verify structure enforcement
- [ ] Integration tests confirm Project-as-Repository model
- [ ] Documentation clearly states structure is API contract
- [ ] Cross-platform path handling verified
- [ ] Breaking change detection is implemented

## Story Links
- **Depends On**: STORY-001-development-environment-setup
- **Blocks**: STORY-004-file-management-api, All subsequent stories
- **Related PRD**: PRD-004-project-asset-management
- **Architecture**: Project-as-Repository model, Structure as API Contract

## Additional Notes
- This story establishes the foundational architecture for the entire system
- The numbered directory structure (01-06) is chosen for consistent ordering
- Git LFS configuration is mandatory to handle large media files
- The structure serves as an API contract - tools and scripts depend on exact paths
- Automated scaffolding via Makefile is mission-critical, not a nice-to-have