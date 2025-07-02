# Story: Project Structure Definition

**Story ID**: STORY-002  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Infrastructure  
**Points**: 3 (Small)  
**Priority**: High  

## Story Description
As a developer, I need to implement the workspace and project directory structure so that projects are organized consistently and support the file-based regenerative content model with Git integration.

## Acceptance Criteria

### Functional Requirements
- [ ] Workspace directory is created at configured location
- [ ] New projects create proper directory structure
- [ ] Project.json schema is defined and validated
- [ ] Git repository initializes automatically for new projects
- [ ] Directory structure supports all required asset types

### Technical Requirements
- [ ] Implement workspace directory creation with error handling
- [ ] Create project directory scaffolding function
- [ ] Define TypeScript/Python models for project.json
- [ ] Use GitPython for repository initialization
- [ ] Ensure cross-platform path compatibility

### Project Structure Requirements
```
workspace/
└── {project-name}/
    ├── .git/              # Git repository
    ├── project.json       # Project manifest
    ├── assets/            # Source assets
    │   ├── scripts/       # Screenplay files
    │   ├── characters/    # Character definitions
    │   ├── styles/        # Style references
    │   ├── environments/  # Location assets
    │   └── audio/         # Sound assets
    ├── generated/         # AI-generated content
    │   ├── images/        # Generated frames
    │   ├── videos/        # Generated clips
    │   ├── audio/         # Generated sounds
    │   └── metadata/      # Generation parameters
    └── exports/           # Final outputs
        ├── edl/           # Edit decision lists
        ├── previews/      # Low-res previews
        └── renders/       # Final renders
```

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
    def create_project_structure(self, project_name: str) -> Path:
        """Create complete project directory structure"""
        
    def initialize_git_repo(self, project_path: Path) -> None:
        """Initialize Git repository with .gitignore"""
        
    def create_project_manifest(self, project_path: Path, config: dict) -> None:
        """Create and save project.json"""
```

## Dependencies
- GitPython library for Git operations
- JSON schema validation library
- File system permissions for directory creation

## Testing Criteria
- [ ] Project creation works with valid names
- [ ] Invalid names are rejected with clear errors
- [ ] Git initializes with proper .gitignore
- [ ] Project.json validates against schema
- [ ] Directories created with correct permissions

## Definition of Done
- [ ] Workspace service implemented with all methods
- [ ] Project.json schema defined in both TypeScript and Python
- [ ] Git initialization includes appropriate .gitignore
- [ ] Unit tests cover all creation scenarios
- [ ] Cross-platform path handling verified

## Story Links
- **Depends On**: STORY-001-development-environment-setup
- **Blocks**: STORY-004-file-management-api
- **Related PRD**: PRD-004-project-asset-management