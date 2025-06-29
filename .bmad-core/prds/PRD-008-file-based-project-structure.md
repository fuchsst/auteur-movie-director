# Product Requirements Document: File-Based Project Structure & Version Control System

**Version:** 1.0  
**Date:** 2025-01-29  
**Owner:** BMAD Business Analyst  
**Status:** Web Architecture Foundation  
**PRD ID:** PRD-008  
**Dependencies:** PRD-001 (Backend Integration), PRD-006 (Node Canvas), PRD-007 (Regenerative Model)

---

## Executive Summary

### Business Justification
The File-Based Project Structure & Version Control System establishes the foundational storage architecture that enables Movie Director to function as a professional, collaborative filmmaking platform. This system provides a standardized, self-contained project organization that seamlessly integrates with Git version control, enabling complete project portability, team collaboration, and the regenerative content model that defines the platform.

By implementing a rigorous separation between shared workspace resources and self-contained projects, combined with Git Large File Storage (LFS) for efficient media handling, this architecture enables artists to work naturally with high-level creative concepts (Characters, Styles, Locations) while maintaining complete version history and preparing for future cloud deployment.

### Target User Personas
- **Independent Filmmakers** - Managing complex projects with clear organization
- **Collaborative Teams** - Sharing projects through Git repositories
- **Studios** - Standardizing project structure across productions
- **Educational Institutions** - Teaching professional project organization
- **Remote Productions** - Enabling distributed workflows through Git
- **Archive-Focused Organizations** - Long-term preservation with complete history

### Expected Impact on Film Production Workflow
- **Project Portability**: Self-contained projects that can be moved, shared, or archived
- **Version Control**: Complete history of creative decisions and iterations
- **Team Collaboration**: Git-based workflows for distributed teams
- **Storage Efficiency**: Git LFS handles large media files intelligently
- **Future Scalability**: Cloud-ready structure for S3 deployment

---

## Problem Statement

### Current Limitations in File Management
1. **Chaotic Organization**: No standardized structure leads to lost assets
2. **Version Confusion**: Files like "Final_v2_FINAL_USE_THIS.mp4"
3. **No History Tracking**: Cannot revert to previous versions
4. **Collaboration Barriers**: File sharing through manual transfers
5. **Storage Bloat**: Duplicated files across projects

### Pain Points in Creative Workflows
- **Asset Scatter**: Creative elements spread across arbitrary folders
- **No Reusability**: Common assets duplicated in every project
- **Manual Scaffolding**: Artists create folder structures inconsistently
- **Binary File Issues**: Git repositories become enormous with media
- **Path Dependencies**: Projects break when moved to different locations

### Gaps in Current Solutions
- **No Workspace/Project Separation**: Everything mixed together
- **Poor Git Integration**: Large files corrupt repository performance
- **No Programmatic Access**: Hard-coded paths throughout code
- **Missing Standards**: Every artist organizes differently
- **No Cloud Preparation**: Local-only structures don't scale

---

## Solution Overview

### Feature Description within Web Architecture
The File-Based Project Structure implements a two-tier organizational model with a clear separation between the global Workspace (shared resources) and individual Projects (self-contained productions). Each project is initialized as an independent Git repository with Git LFS configured for media files, enabling efficient version control and future cloud deployment.

**Core Components:**
1. **Workspace/Project Dichotomy** - Global library vs self-contained projects
2. **Standardized Directory Structure** - Consistent organization with numeric prefixes
3. **Git + LFS Hybrid Strategy** - Text files in Git, binary media in LFS
4. **Project-as-Repository Model** - Each project is an independent Git repo
5. **Programmatic Path Management** - Centralized Python module for all file operations
6. **Automated Project Scaffolding** - One-click project creation with structure
7. **Asset Organization** - Characters, Styles, Locations in standard folders
8. **Immutable Outputs** - Generated content never overwrites previous versions
9. **Cloud Storage Mapping** - S3-compatible structure for future migration
10. **Archive Support** - Projects can be bundled for long-term storage

### Integration with Platform Architecture
**Frontend Integration:**
- File picker defaults to correct directories
- Asset gallery reads from standardized locations
- Canvas saves to predictable paths
- Project creation UI triggers scaffolding

**Backend Integration:**
- Path resolution service provides file access
- Git operations wrapped in API endpoints
- LFS management automated
- File watchers trigger regeneration

**Regenerative Model Support:**
- Parameters in Git-tracked JSON
- Generated media in LFS-tracked files
- Clear separation of source vs derivative
- Enables complete regeneration from parameters

### Backend Service Architecture
**File Management Service:**
- Project scaffolding automation
- Path resolution and validation
- Directory watching for changes
- File operation queueing

**Git Integration Service:**
- Automated commits on save
- Branch management for experiments
- LFS tracking configuration
- History browsing API

**Archive Service:**
- Project bundling with Git history
- Selective LFS object inclusion
- Compression and encryption
- Cloud storage upload

---

## User Stories & Acceptance Criteria

### Epic 1: Workspace and Project Management
**As a filmmaker, I want a clear separation between shared resources and individual projects so that I can reuse assets efficiently.**

#### User Story 1.1: Workspace Library Access
- **Given** I have common assets like logos and music
- **When** I create a new project
- **Then** I can access workspace library resources
- **And** they are not duplicated in my project
- **And** changes to library assets reflect everywhere
- **And** my project remains portable

**Acceptance Criteria:**
- Workspace at `/Generative_Studio_Workspace/`
- Library contains Pipeline_Templates, Stock_Media
- Projects reference but don't copy library assets
- Library is read-only from project context

#### User Story 1.2: Self-Contained Projects
- **Given** I need to share or archive a project
- **When** I package the project folder
- **Then** it contains everything needed
- **And** internal references remain valid
- **And** Git history is preserved
- **And** can be opened on another machine

**Acceptance Criteria:**
- Project folder contains all project-specific assets
- No absolute paths in project files
- Git repository initialized in project root
- Works after moving to different location

### Epic 2: Standardized Project Structure
**As a team, we want consistent project organization so anyone can navigate any project.**

#### User Story 2.1: Automated Project Creation
- **Given** I want to start a new film project
- **When** I click "New Project" and enter details
- **Then** the complete folder structure is created
- **And** Git repository is initialized
- **And** LFS is configured correctly
- **And** initial commit is made

**Acceptance Criteria:**
- Creates all numbered directories (01-06)
- Generates project.json with UUID
- Copies .gitignore and .gitattributes templates
- Makes initial Git commit

#### User Story 2.2: Asset Organization
- **Given** I have characters, styles, and locations
- **When** I create these assets
- **Then** they are organized in standard folders
- **And** each has consistent internal structure
- **And** the UI knows where to find them
- **And** they appear in the asset browser

**Acceptance Criteria:**
- Characters in `01_Assets/Generative_Assets/Characters/`
- Each character folder has reference_images/, description.txt
- Styles and Locations follow same pattern
- Asset browser reads from these locations

### Epic 3: Version Control Integration
**As a filmmaker, I want complete version history so I can experiment freely and revert changes.**

#### User Story 3.1: Automatic Git Tracking
- **Given** I make changes to my project
- **When** I save my work
- **Then** changes are tracked in Git
- **And** large files use Git LFS
- **And** commit messages are meaningful
- **And** I can see history in the UI

**Acceptance Criteria:**
- Canvas saves trigger Git operations
- Media files automatically use LFS
- Commits include descriptive messages
- History viewable without command line

#### User Story 3.2: Efficient Media Handling
- **Given** my project has large video files
- **When** I commit changes
- **Then** only LFS pointers are in Git
- **And** actual media is in LFS storage
- **And** clone/pull operations are fast
- **And** I can work with partial checkouts

**Acceptance Criteria:**
- .gitattributes configured for all media types
- Repository size remains small (<100MB)
- Can clone without downloading all media
- Selective LFS pull supported

### Epic 4: Programmatic Path Management
**As a developer, I want centralized path handling so the codebase remains maintainable.**

#### User Story 4.1: Path Resolution API
- **Given** code needs to access project files
- **When** it requests a file path
- **Then** it uses the central path module
- **And** paths are constructed correctly
- **And** works cross-platform
- **And** no hard-coded paths exist

**Acceptance Criteria:**
- All paths through project_paths.py
- Uses pathlib for platform independence
- Functions for each asset type
- No string concatenation for paths

#### User Story 4.2: Resilient Path Changes
- **Given** we need to rename a directory
- **When** we update the path module
- **Then** all code continues working
- **And** only one place needs changing
- **And** no broken references
- **And** tests verify path integrity

**Acceptance Criteria:**
- Directory renames require single change
- Comprehensive path tests
- No hard-coded paths in codebase
- Path validation on startup

### Epic 5: Cloud and Archive Preparation
**As a studio, I want cloud-ready structure so we can scale to distributed teams.**

#### User Story 5.1: S3-Compatible Organization
- **Given** we plan to use cloud storage
- **When** we design the file structure
- **Then** it maps directly to S3 buckets
- **And** supports multi-tenancy patterns
- **And** enables efficient caching
- **And** preserves Git functionality

**Acceptance Criteria:**
- Structure works with S3 paths
- Supports prefix-based tenant isolation
- Git LFS can use S3 backend
- Local/cloud structure identical

#### User Story 5.2: Project Archival
- **Given** a project is complete
- **When** I archive it
- **Then** it creates a single bundle
- **And** includes Git history
- **And** includes necessary LFS objects
- **And** can be restored later

**Acceptance Criteria:**
- Archive includes .git directory
- Selective LFS object inclusion
- Compressed archive format
- Restore preserves full history

---

## Technical Requirements

### Directory Structure Specification

#### 1. Workspace Root Structure
```
/Generative_Studio_Workspace/
├── Library/
│   ├── Branding/               # Logos, fonts, style guides
│   ├── LUTs_and_Presets/      # Color grading, effects
│   ├── Stock_Media/           # Licensed music, SFX, footage
│   └── Pipeline_Templates/    # Reusable ComfyUI workflows
└── Projects/                  # All individual projects
```

#### 2. Project Directory Structure
```
/Projects/PROJECT_NAME/
├── project.json               # Project manifest with UUID
├── .git/                     # Git repository
├── .gitignore               # Ignore patterns
├── .gitattributes           # LFS configuration
├── 01_Assets/               # Raw source materials
│   ├── Source_Media/        # Camera footage, audio
│   ├── AI_Models/          # Project-specific models
│   └── Generative_Assets/  # Creative elements
│       ├── Characters/CHARACTER_NAME/
│       │   ├── reference_images/
│       │   ├── description.txt
│       │   ├── voice_sample.wav
│       │   └── model.safetensors
│       ├── Styles/STYLE_NAME/
│       │   ├── reference_images/
│       │   └── keywords.txt
│       └── Locations/LOCATION_NAME/
│           ├── reference_images/
│           ├── environment_map.hdr
│           └── description.txt
├── 02_Source_Creative/      # Human-edited files
│   ├── Canvases/           # Node graph JSONs
│   ├── Scripts/            # Screenplays, notes
│   └── Prompts/            # Reusable text prompts
├── 03_Renders/             # Generated outputs
│   └── SCENE_NAME/
│       └── SHOT_NAME/
│           ├── SHOT-001_v01_take01.mp4
│           ├── SHOT-001_v01_take02.mp4
│           └── SHOT-001_v02_take01.mp4
├── 04_Project_Files/       # App-specific files
│   ├── Auto_Saves/        # Canvas backups
│   └── EDLs/              # Edit decision lists
├── 05_Cache/              # Temporary files (git-ignored)
│   ├── thumbnails/
│   └── control_maps/
└── 06_Exports/            # Final deliverables (git-ignored)
```

### Path Management Module

```python
# project_paths.py
from pathlib import Path
from typing import Optional

class ProjectPaths:
    """Centralized path management for project structure"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root)
        self.library = self.workspace_root / "Library"
        self.projects = self.workspace_root / "Projects"
    
    def get_project_root(self, project_name: str) -> Path:
        """Get root directory for a project"""
        return self.projects / project_name
    
    def get_character_asset_path(self, project_root: Path, character_name: str) -> Path:
        """Get path to character asset directory"""
        return project_root / "01_Assets" / "Generative_Assets" / "Characters" / character_name
    
    def get_style_asset_path(self, project_root: Path, style_name: str) -> Path:
        """Get path to style asset directory"""
        return project_root / "01_Assets" / "Generative_Assets" / "Styles" / style_name
    
    def get_canvas_path(self, project_root: Path, canvas_name: str = "main_canvas") -> Path:
        """Get path to canvas JSON file"""
        return project_root / "02_Source_Creative" / "Canvases" / f"{canvas_name}.json"
    
    def get_shot_render_path(self, project_root: Path, scene: str, shot: str, 
                           version: int, take: int) -> Path:
        """Get path for rendered shot output"""
        filename = f"SHOT-{shot}_v{version:02d}_take{take:02d}.mp4"
        return project_root / "03_Renders" / scene / shot / filename
    
    def get_cache_dir(self, project_root: Path) -> Path:
        """Get cache directory (git-ignored)"""
        return project_root / "05_Cache"
    
    def validate_project_structure(self, project_root: Path) -> bool:
        """Verify project has correct structure"""
        required_dirs = [
            "01_Assets", "02_Source_Creative", "03_Renders",
            "04_Project_Files", "05_Cache", "06_Exports"
        ]
        return all((project_root / d).exists() for d in required_dirs)
```

### Git Configuration Templates

#### .gitignore Template
```gitignore
# Cache and temporary files
05_Cache/
*.tmp
*.temp

# Final exports (tracked separately)
06_Exports/

# OS-specific files
.DS_Store
Thumbs.db
*.swp

# Python
__pycache__/
*.pyc
.env

# IDE
.vscode/
.idea/

# Logs
*.log
```

#### .gitattributes Template
```gitattributes
# Text files
*.json text
*.txt text
*.md text
*.py text
*.js text
*.svelte text

# Images (Git LFS)
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
*.gif filter=lfs diff=lfs merge=lfs -text
*.psd filter=lfs diff=lfs merge=lfs -text

# Video (Git LFS)
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text
*.mkv filter=lfs diff=lfs merge=lfs -text

# Audio (Git LFS)
*.wav filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.flac filter=lfs diff=lfs merge=lfs -text

# AI Models (Git LFS)
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.ckpt filter=lfs diff=lfs merge=lfs -text
*.pth filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text

# 3D and Environmental Files (Git LFS)
*.fbx filter=lfs diff=lfs merge=lfs -text
*.obj filter=lfs diff=lfs merge=lfs -text
*.hdr filter=lfs diff=lfs merge=lfs -text
*.exr filter=lfs diff=lfs merge=lfs -text
*.gltf filter=lfs diff=lfs merge=lfs -text
*.glb filter=lfs diff=lfs merge=lfs -text
```

### Project Manifest Schema

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "title": "My Awesome Film",
  "description": "A noir-style detective story",
  "created_at": "2025-01-29T10:00:00Z",
  "modified_at": "2025-01-29T14:30:00Z",
  "version": "1.0.0",
  "settings": {
    "aspect_ratio": "16:9",
    "resolution": "1920x1080",
    "frame_rate": 24
  },
  "canvas_path": "02_Source_Creative/Canvases/main_canvas.json",
  "metadata": {
    "genre": "noir",
    "duration_estimate": "5-7 minutes",
    "team_size": 3
  }
}
```

### Automated Project Scaffolding

```python
import json
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import uuid

class ProjectScaffolder:
    """Automates project structure creation"""
    
    def __init__(self, workspace_root: Path, template_dir: Path):
        self.workspace_root = Path(workspace_root)
        self.template_dir = Path(template_dir)
        self.paths = ProjectPaths(workspace_root)
    
    def create_project(self, project_name: str, title: str, 
                      description: str = "") -> Path:
        """Create a new project with complete structure"""
        
        # Create project root
        project_root = self.paths.get_project_root(project_name)
        if project_root.exists():
            raise ValueError(f"Project {project_name} already exists")
        
        project_root.mkdir(parents=True)
        
        # Create directory structure
        directories = [
            "01_Assets/Source_Media",
            "01_Assets/AI_Models",
            "01_Assets/Generative_Assets/Characters",
            "01_Assets/Generative_Assets/Styles",
            "01_Assets/Generative_Assets/Locations",
            "02_Source_Creative/Canvases",
            "02_Source_Creative/Scripts",
            "02_Source_Creative/Prompts",
            "03_Renders",
            "04_Project_Files/Auto_Saves",
            "04_Project_Files/EDLs",
            "05_Cache/thumbnails",
            "05_Cache/control_maps",
            "06_Exports"
        ]
        
        for dir_path in directories:
            (project_root / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create project.json
        project_data = {
            "uuid": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "modified_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "settings": {
                "aspect_ratio": "16:9",
                "resolution": "1920x1080",
                "frame_rate": 24
            },
            "canvas_path": "02_Source_Creative/Canvases/main_canvas.json",
            "metadata": {}
        }
        
        with open(project_root / "project.json", "w") as f:
            json.dump(project_data, f, indent=2)
        
        # Copy template files
        shutil.copy(self.template_dir / ".gitignore", project_root)
        shutil.copy(self.template_dir / ".gitattributes", project_root)
        
        # Initialize Git repository
        subprocess.run(["git", "init"], cwd=project_root, check=True)
        subprocess.run(["git", "lfs", "install"], cwd=project_root, check=True)
        
        # Create initial canvas
        initial_canvas = {
            "version": "1.0",
            "nodes": [],
            "edges": [],
            "viewport": {"x": 0, "y": 0, "zoom": 1}
        }
        
        canvas_path = self.paths.get_canvas_path(project_root)
        with open(canvas_path, "w") as f:
            json.dump(initial_canvas, f, indent=2)
        
        # Initial commit
        subprocess.run(["git", "add", "."], cwd=project_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"Initial project structure for '{title}'"],
            cwd=project_root, check=True
        )
        
        return project_root
```

### Performance Optimizations

#### 1. File System Efficiency
- Use pathlib for all path operations
- Cache frequently accessed paths
- Implement file watchers for changes
- Batch file operations when possible

#### 2. Git Performance
- Configure Git LFS for parallel uploads
- Use shallow clones for faster checkout
- Implement progress reporting for operations
- Regular maintenance with `git gc`

#### 3. Storage Optimization
- Automatic cache cleanup
- Compress archived projects
- Deduplicate similar files
- Monitor disk usage

---

## Success Metrics

### Project Organization
**Primary KPIs:**
- **Structure Compliance**: 100% projects follow standard
- **Creation Time**: <5 seconds to scaffold project
- **Navigation Speed**: Find any asset in <3 clicks
- **Error Reduction**: 90% fewer missing file errors

**Measurement Methods:**
- Automated structure validation
- Project creation timing
- User navigation tracking
- Error log analysis

### Version Control Effectiveness
**Git Metrics:**
- **Repository Size**: <100MB for code/structure
- **Clone Speed**: <30 seconds without media
- **Commit Frequency**: Average 10+ commits/day
- **History Usage**: 50% of users access history

**LFS Metrics:**
- **Media Handling**: 100% large files in LFS
- **Transfer Speed**: 10MB/s+ for media
- **Storage Efficiency**: 50% reduction vs duplicates
- **Selective Sync**: 80% use partial checkout

### Collaboration Success
**Team Metrics:**
- **Merge Conflicts**: <5% on structure files
- **Sharing Speed**: <1 minute to share project
- **Onboarding Time**: <30 minutes for new users
- **Cross-Platform**: Works on Win/Mac/Linux

**Cloud Readiness:**
- **S3 Compatibility**: Structure maps directly
- **Migration Time**: <1 hour to cloud
- **Multi-tenancy**: Supports isolation patterns
- **Archive Success**: 100% restoration rate

---

## Risk Assessment & Mitigation

### Technical Risks

#### High Risk: Git LFS Complexity
- **Risk**: Users unfamiliar with Git LFS make mistakes
- **Impact**: Repository corruption, lost media
- **Mitigation**: 
  - Automated LFS setup and configuration
  - UI hides Git complexity
  - Regular training and documentation
  - Automated integrity checks

#### Medium Risk: Path Dependencies
- **Risk**: Hard-coded paths break portability
- **Impact**: Projects fail when moved
- **Mitigation**:
  - Enforce path module usage
  - Automated path validation
  - Relative path enforcement
  - Regular portability tests

### Business Risks

#### High Risk: Change Resistance
- **Risk**: Artists resist structured organization
- **Impact**: Low adoption, inconsistent usage
- **Mitigation**:
  - Gradual rollout with training
  - Show clear benefits
  - Automate everything possible
  - Gather and implement feedback

---

## Implementation Roadmap

### Phase 1: Core Structure (Weeks 1-2)
**Deliverables:**
- Path management module
- Directory structure specification
- Git configuration templates
- Basic scaffolding script

**Success Criteria:**
- Can create compliant projects
- Path module comprehensive
- Git/LFS working correctly

### Phase 2: Automation (Weeks 3-4)
**Deliverables:**
- Full project scaffolder
- API integration endpoints
- File watcher implementation
- Auto-commit functionality

**Success Criteria:**
- One-click project creation
- Changes tracked automatically
- No manual Git commands needed

### Phase 3: UI Integration (Weeks 5-6)
**Deliverables:**
- Project creation dialog
- Asset browser integration
- History viewer
- File picker enhancements

**Success Criteria:**
- Seamless UI experience
- Structure invisible to users
- Natural asset workflows

### Phase 4: Cloud Preparation (Weeks 7-8)
**Deliverables:**
- S3 mapping documentation
- Archive functionality
- Multi-tenancy design
- Migration tools

**Success Criteria:**
- Projects cloud-ready
- Successful archive/restore
- Multi-tenant isolation proven

---

## Architectural Compliance Requirements

### Draft4_Canvas.md File Storage Strategy Integration
**Project-as-Repository Model:**\n- Implement exact project-as-repository model from draft4_canvas.md architectural blueprint\n- Each project as independent Git repository with complete version control\n- Git LFS integration for binary media files per exact specifications\n- Project.json as machine-readable manifest serving as project identity card\n- Canvas JSON files stored in `02_Source_Creative/Canvases/` for SvelteFlow integration\n\n**RESTful API Integration:**\n- FastAPI endpoints for project CRUD operations following exact Table 3 specifications\n- `GET /api/v1/projects/{id}` - Retrieve full project state via project.json manifest\n- `PUT /api/v1/projects/{id}` - Save project state with version conflict handling\n- Database-file system synchronization with project metadata in PostgreSQL\n- File path abstraction - never expose file paths to frontend, use ID resolution only\n\n### Draft4_Filestructure.md Exact Compliance\n**Workspace/Project Dichotomy:**\n- Implement exact two-tier model: Workspace (global resources) vs Projects (self-contained)\n- Workspace at `/Generative_Studio_Workspace/` with Library subdirectory\n- Projects directory containing independent, portable project folders\n- Clear separation of shared resources vs project-specific assets\n- Pipeline Templates in workspace Library for reuse across projects\n\n**Directory Structure (Exact Match Required):**\n- Follow exact numeric prefix organization from draft4_filestructure.md\n- `01_Assets/` - Raw source materials (Source_Media, AI_Models, Generative_Assets)\n- `02_Source_Creative/` - Human-edited files (Canvases, Scripts, Prompts)\n- `03_Renders/` - Generated outputs with immutable naming\n- `04_Project_Files/` - Application-specific files (Auto_Saves, EDLs)\n- `05_Cache/` - Transient data (Git ignored)\n- `06_Exports/` - Final deliverables (Git ignored)\n\n**Git LFS Configuration (Exact .gitattributes):**\n- Text files in standard Git: *.json, *.txt, *.md, *.py, *.js, *.svelte\n- Binary media in LFS: *.png, *.jpg, *.mp4, *.wav, *.safetensors, *.ckpt\n- Atomic versioning with immutable naming: SHOT-XXX_vYY_takeZZ.ext\n- Integration with regenerative content model for parameter tracking\n\n### Cross-PRD Dependencies\n**Backend Integration (PRD-001):**\n- Path Resolution Service providing centralized file access\n- FastAPI endpoints for project scaffolding and management\n- WebSocket integration for real-time file system events\n- Database synchronization for project metadata and structure\n\n**Canvas Integration (PRD-006):**\n- Canvas JSON storage in `02_Source_Creative/Canvases/` directory\n- SvelteFlow graph serialization following exact project structure\n- Real-time canvas saves with Git version tracking\n- Template canvas creation during project scaffolding\n\n**Regenerative Model Integration (PRD-007):**\n- Parameter storage in Git-tracked JSON files\n- Generated content in Git LFS-tracked binary files\n- Clear separation of source (parameters) vs derivative (generated) content\n- Storage lifecycle management and optimization integration\n\n**Asset System Integration (PRD-003, PRD-004, PRD-005):**\n- Character assets in `01_Assets/Generative_Assets/Characters/`\n- Style assets in `01_Assets/Generative_Assets/Styles/`\n- Location assets in `01_Assets/Generative_Assets/Locations/`\n- Standardized asset directory structure for consistency\n\n---\n\n## Implementation Validation\n\n### Core Architecture Validation\n**File Structure Compliance:**\n- Validate exact directory structure matches draft4_filestructure.md specifications\n- Test workspace/project separation with library resource access\n- Ensure Git LFS configuration follows exact .gitattributes template\n- Verify immutable file naming with atomic versioning\n- Test project portability across different environments\n\n**Git Integration Testing:**\n- Project-as-repository model with independent Git histories\n- Git LFS performance with large media files\n- Automated commit hooks for generation results\n- Branch-based experimentation workflows\n- Cross-platform Git operations and compatibility\n\n**Path Resolution Validation:**\n- Centralized path service providing abstracted file access\n- ID-based asset resolution without exposing file paths\n- Cross-project asset template sharing capabilities\n- Integration with regenerative content model file references\n- Performance testing with large project structures\n\n### Cross-System Integration Testing\n**Canvas-File System Coordination:**\n- SvelteFlow canvas saves to correct directory structure\n- Real-time file system events reflected in canvas state\n- Version tracking for canvas modifications\n- Template sharing across projects via file system\n\n**Asset Management Integration:**\n- Character, style, and location assets in standardized directories\n- Asset discovery and indexing across project structure\n- Cross-project asset template sharing and reuse\n- Integration with regenerative content model for asset recreation\n\n**Backend Service Coordination:**\n- FastAPI endpoints for project CRUD operations\n- Database-file system synchronization and consistency\n- WebSocket events for real-time file system changes\n- Celery task integration for background file operations\n\n### Performance and Scalability Testing\n**File System Performance:**\n- Project creation speed (<3 seconds with full Git LFS setup)\n- Large project loading and navigation performance\n- Git operations with extensive LFS usage\n- Cross-platform file system compatibility\n\n**Storage Optimization:**\n- Git LFS efficiency for binary media files\n- Selective LFS pull for bandwidth optimization\n- Storage lifecycle management and cleanup\n- Cross-region storage performance for global teams\n\n---\n\n## Architecture Alignment Summary\n\n### Draft4_Canvas.md Compliance\n✅ **Project-as-Repository**: Independent Git repos per project with complete version control  \n✅ **RESTful API**: FastAPI endpoints following exact Table 3 specifications  \n✅ **File Storage Strategy**: Project.json manifest as machine-readable project identity  \n✅ **Database Integration**: Project metadata in PostgreSQL with file system coordination  \n✅ **Path Abstraction**: No file path exposure to frontend, ID-based resolution only  \n\n### Draft4_Filestructure.md Integration\n✅ **Workspace/Project Model**: Exact two-tier organization with global library separation  \n✅ **Directory Structure**: Complete numeric prefix organization per specifications  \n✅ **Git LFS Configuration**: Exact .gitattributes template with all specified file types  \n✅ **Atomic Versioning**: Immutable naming with complete version tracking  \n✅ **Separation of Concerns**: Source vs derivative, text vs binary, persistent vs transient  \n\n### Cross-System File Integration\n✅ **Canvas Storage** (PRD-006): Canvas JSON in `02_Source_Creative/Canvases/` directory  \n✅ **Asset Organization** (PRD-003, 004, 005): Standardized asset directory structure  \n✅ **Regenerative Model** (PRD-007): Parameter/content separation with Git/LFS hybrid  \n✅ **Backend Services** (PRD-001): Path resolution service and API integration  \n✅ **Version Control**: Complete Git integration with team collaboration support  \n\n### Professional File Management Standards\n✅ **Project Portability**: Self-contained projects with complete version history  \n✅ **Team Collaboration**: Git-based workflows with conflict resolution  \n✅ **Storage Efficiency**: Git LFS optimization for binary media files  \n✅ **Cloud Readiness**: S3-compatible structure for future migration  \n✅ **Archive Support**: Complete project bundling with history preservation  \n\n---\n\n**File Structure Foundation:**\nThis PRD successfully establishes the File-Based Project Structure as the foundational storage architecture that enables all other Movie Director platform features while providing professional-grade project organization, version control, and team collaboration through modern Git workflows and intelligent file management.\n\n---\n\n## Stakeholder Sign-Off

### Development Team Approval
- [ ] **Backend Lead** - Path module architecture approved
- [ ] **Frontend Lead** - UI integration plan validated
- [ ] **DevOps Lead** - Git/LFS strategy confirmed
- [ ] **QA Lead** - Testing approach comprehensive

### Business Stakeholder Approval
- [ ] **Product Owner** - Structure meets user needs
- [ ] **Creative Director** - Asset organization intuitive
- [ ] **IT Manager** - Storage strategy sustainable
- [ ] **CTO** - Cloud migration path clear

---

**Next Steps:**
1. Implement path management module
2. Create scaffolding automation
3. Design project creation UI
4. Test with pilot users
5. Refine based on feedback

---

*This PRD establishes the foundational file structure that enables all other platform features, providing a professional, scalable, and future-proof organization system for generative filmmaking projects.*