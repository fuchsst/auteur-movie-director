# Epic: Project & Asset Management System

**Epic ID**: EPIC-002  
**Based on**: PRD-002-project-asset-management  
**Target Milestone**: Q1 2025 - Foundation Release  
**Status**: 📋 Ready for Development  
**Epic Points**: 76  
**Team Size**: 3 developers (1 frontend, 2 backend)  

## Epic Description

Implement a revolutionary file-based project and asset management system that treats every project as a self-contained, version-controlled Git repository. This system establishes the foundation for organized, portable, and collaborative AI-powered film production workflows with built-in version control and large file support.

## Business Value

### Impact on Generative Film Production Workflow
- **100% Project Portability**: Self-contained repositories work anywhere without dependency issues
- **Zero Data Loss**: Complete version history through Git + LFS integration
- **Instant Organization**: < 5 second automated project scaffolding
- **Creative Freedom**: Non-destructive takes system preserves all iterations

### User Experience Improvements
- Eliminates "Final_v2_REALLY_FINAL.mp4" chaos through structured versioning
- Visual gallery for comparing multiple generated takes
- Intuitive asset organization with workspace library
- Git complexity hidden behind user-friendly UI

### Technical Capability Enhancements
- Industry-standard project structure for AI content
- Seamless Git LFS integration for media files up to 2GB
- Automated dependency tracking across assets
- RESTful API for all project operations

### Platform Foundation Benefits
- Standardized project structure enables future feature development
- Version control provides experiment safety net
- Asset library creates reusable component ecosystem
- Metadata preservation supports iterative improvement

## Scope & Boundaries

### In Scope
**Core Project Management**
- Project scaffolding with standardized directory structure
- Git repository initialization with LFS configuration
- Project manifest (project.json) generation and management
- Project browser with visual gallery and metadata
- Import/export of complete projects

**Version Control Integration**
- Automated Git operations (init, add, commit)
- Git LFS setup and file tracking
- Visual Git history timeline
- Basic rollback functionality
- Auto-commit with intelligent batching

**Asset Library System**
- Workspace-level asset organization
- Asset categories (Characters, Locations, Styles, Music)
- Asset browser with hierarchical navigation
- Asset import with metadata preservation
- Copy assets from library to projects

**Takes Management**
- Deterministic take naming (take_001, take_002)
- Non-destructive file versioning
- Takes gallery with visual comparison
- Active take selection mechanism
- Metadata preservation for each take

**File Operations**
- Structure validation and enforcement
- File upload with automatic LFS tracking
- Thumbnail generation for visual assets
- Safe file operations with error recovery

### Out of Scope
**Canvas Integration (PRD-004)**
- Drag-and-drop from asset browser to canvas
- Asset node creation and management
- Visual workflow connections
- Real-time canvas updates

**AI Execution (PRD-003)**
- Model execution and orchestration
- Generation parameter management
- Progress tracking for AI operations
- Resource allocation and scheduling

**Story Generation (PRD-007)**
- Automated story structure creation
- AI-powered narrative development
- Character and location extraction from scripts
- Beat sheet generation

**Future Enhancements**
- Cloud sync and distributed teams
- Advanced Git operations (rebase, cherry-pick)
- AI-powered asset tagging
- Blockchain provenance
- Analytics and insights

## Acceptance Criteria

### Functional Criteria
- [x] Single-click project creation with structure in < 5 seconds
- [x] Git repository initialized with proper .gitignore
- [x] Git LFS configured for media types (images, video, audio, 3D)
- [x] project.json manifest created with UUID and metadata
- [x] Initial commit made with descriptive timestamp
- [ ] Visual project browser showing thumbnails
- [ ] Asset browser with category organization
- [ ] Copy assets from workspace library to projects
- [x] Each generation creates numbered take with metadata
- [ ] Visual takes gallery with comparison view
- [ ] One-click active take selection
- [x] Auto-commit on significant changes
- [ ] Git history timeline visualization
- [ ] Project export as self-contained archive

### Technical Criteria
- [x] Project structure validation before operations
- [x] RESTful API endpoints for all operations
- [x] WebSocket notifications for long operations
- [x] Stream-based file operations for large files
- [x] Atomic Git operations with rollback
- [ ] File locking for concurrent access
- [x] Comprehensive error handling
- [ ] Performance benchmarks met

### Quality Criteria
- [x] Service unit test coverage > 80%
- [ ] Integration tests for workflows
- [ ] E2E tests for user journeys
- [x] API documentation (OpenAPI)
- [ ] User documentation
- [x] Code style compliance
- [ ] Accessibility (WCAG 2.1 AA)
- [ ] Performance profiling

## Epic Decomposition

### Story Group 1: Project Foundation (18 points)
1. **STORY-025**: Project Scaffolding Service (5 pts)
   - Implement directory structure creation
   - Generate project.json manifest
   - Validate structure integrity

2. **STORY-026**: Git Integration (5 pts)
   - Initialize Git repositories
   - Configure Git LFS patterns
   - Create initial commit

3. **STORY-027**: Project API Endpoints (3 pts)
   - CRUD operations for projects
   - List projects with filtering
   - Structure validation endpoint

4. **STORY-028**: Project Browser UI (5 pts)
   - Visual gallery component
   - Thumbnail generation
   - Create/open/delete UI

### Story Group 2: Asset Management (18 points)
5. **STORY-029**: Workspace Asset Service (5 pts)
   - Asset categorization system
   - Metadata schema definition
   - File organization logic

6. **STORY-030**: Asset Browser Component (8 pts)
   - Hierarchical folder navigation
   - Visual preview generation
   - Search and filter UI

7. **STORY-031**: Asset Operations (5 pts)
   - Copy from library to project
   - Metadata preservation
   - Duplicate detection

### Story Group 3: Takes System (13 points)
8. **STORY-021**: Takes Service (5 pts) ✅ Partially Complete
   - Deterministic naming
   - Directory management
   - Metadata handling

9. **STORY-032**: Takes Gallery UI (5 pts)
   - Visual gallery component
   - Comparison view
   - Selection interface

10. **STORY-033**: Takes Integration (3 pts)
    - Thumbnail generation
    - Git LFS tracking
    - Cleanup operations

### Story Group 4: Git Operations (16 points)
11. **STORY-034**: Git Service Extensions (5 pts)
    - Auto-commit logic
    - History retrieval
    - Rollback operations

12. **STORY-035**: Git UI Components (8 pts)
    - History timeline
    - Commit browser
    - Rollback interface

13. **STORY-036**: Git Performance (3 pts)
    - Optimize large repos
    - Implement caching
    - Background operations

### Story Group 5: Import/Export (11 points)
14. **STORY-037**: Project Export (5 pts)
    - Archive generation
    - Dependency bundling
    - Progress tracking

15. **STORY-038**: Project Import (6 pts)
    - Archive extraction
    - Structure validation
    - Migration support

## Integration Points

### Backend Services
- **WorkspaceService**: Core project operations
- **GitService**: Version control management
- **GitLFSService**: Large file handling
- **TakesService**: Version management
- **FileService**: Safe file operations

### Frontend Components
- **ProjectBrowser**: Project selection UI
- **AssetBrowser**: Asset library navigation
- **TakesGallery**: Version comparison
- **GitTimeline**: History visualization

### API Structure
```
/api/v1/workspace/
  /projects/              # Project management
  /assets/                # Workspace assets
  /structure/validate     # Structure checking

/api/v1/takes/
  /{project}/{shot}/      # Takes operations

/api/v1/git/
  /{project}/status       # Repository status
  /{project}/history      # Commit history
  /{project}/commit       # Manual commits
```

## Technical Architecture Decisions

### File System Design
- **Project Root**: Workspace-relative paths
- **Atomic Operations**: Use temp files and rename
- **Validation**: Check structure before operations
- **Error Recovery**: Rollback on failure

### Git Strategy
- **Shallow Clones**: For performance
- **Auto-commit**: Batch changes for efficiency
- **LFS Patterns**: Comprehensive media coverage
- **Ignore Patterns**: Exclude temp/cache files

### Concurrency Handling
- **File Locks**: OS-level for writes
- **Queue System**: Redis for long operations
- **Optimistic UI**: Update immediately, rollback on error

## Risk Mitigation

### Technical Risks
1. **Git Performance**
   - Monitor repository size
   - Implement shallow clones
   - Use sparse checkout

2. **Storage Growth**
   - LFS garbage collection
   - Retention policies
   - Storage monitoring

3. **File Conflicts**
   - Clear locking strategy
   - Conflict detection
   - User notification

## Success Metrics

### Performance
- Project creation < 5 seconds
- Asset search < 1 second
- File operations > 50MB/s
- Git operations < 2 seconds

### Quality
- Zero data loss incidents
- 99.9% operation success rate
- < 0.1% file corruption rate

### Adoption
- 90% projects use takes system
- Average 15 assets per project
- 80% use Git features

## Dependencies

- EPIC-001: Web Platform Foundation (80% complete)
- Git 2.25+ and Git LFS 2.9+
- ffmpeg for thumbnails
- Node.js 20+ and Python 3.11+

## Definition of Done

### Story Level
- Tests written and passing
- API documented
- UI responsive
- Code reviewed

### Epic Level
- All acceptance criteria met
- Performance targets achieved
- Documentation complete
- Security review passed
- Team trained

## Notes

This epic focuses exclusively on the file management and version control aspects of the platform. Integration with the Production Canvas (PRD-004) and AI execution (PRD-003) will be handled in their respective epics.

The takes system is a critical differentiator that enables non-destructive experimentation. Priority should be given to making this system intuitive and reliable.

Story structure directories are included as part of the project scaffolding, but automated story generation is explicitly excluded from this epic (handled in PRD-007).