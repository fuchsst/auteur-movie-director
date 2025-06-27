# Product Requirements Document: Regenerative Content Model & Asset Management

**Version:** 1.0  
**Date:** 2025-01-27  
**Owner:** BMAD Business Analyst  
**Status:** Draft - Stakeholder Review  
**PRD ID:** PRD-007  
**Dependencies:** Backend Integration Service Layer (PRD-001), Node-Based Production Canvas (PRD-006)

---

## Executive Summary

### Business Justification
The Regenerative Content Model represents a paradigm shift in how generative AI content is managed within creative production workflows. Instead of storing large generated files that consume disk space and complicate version control, this system stores only the creative intent and generation parameters within the .blend file, while generated content exists as lightweight file references that can be recreated on demand.

This architectural approach solves critical pain points in AI-assisted filmmaking: project files remain small and portable, version control becomes manageable, creative iterations are unlimited, and projects can evolve with improving AI models. By separating creative decisions from generated outputs, filmmakers gain unprecedented flexibility to iterate, experiment, and refine their vision without the traditional constraints of file management.

The regenerative model transforms the .blend file into a "digital DNA" of the film - a complete blueprint that can regenerate all content while remaining small enough to email, version control with Git, and share across teams.

### Target User Personas
- **Version Control Users** - Developers and technical artists using Git for project management
- **Collaborative Teams** - Multiple artists working on the same project across locations
- **Iterative Creators** - Filmmakers who constantly refine and experiment with variations
- **Storage-Conscious Users** - Artists working with limited disk space or cloud storage
- **Archive-Focused Users** - Studios needing long-term project preservation
- **Model Evolution Adopters** - Users wanting to leverage improving AI models over time

### Expected Impact on Film Production Workflow
- **Storage Efficiency**: Reduce project storage requirements by 95%+ (GB to MB)
- **Version Control**: Enable Git-based workflows for complete film projects
- **Iteration Freedom**: Unlimited creative variations without storage penalties
- **Collaboration Enhancement**: Share complete projects via simple file transfer
- **Future-Proofing**: Projects can improve as AI models evolve

---

## Problem Statement

### Current Limitations in Generative Film Production
1. **Storage Explosion**: Generated videos, images, and audio quickly consume terabytes
2. **Version Control Impossibility**: Large binary files make Git workflows impractical
3. **Iteration Penalties**: Each variation multiplies storage requirements
4. **Sharing Difficulties**: Project files too large for easy collaboration
5. **Model Lock-In**: Content tied to specific model versions becomes outdated

### Pain Points in Existing Blender Workflows
- **File Management Complexity**: Manual tracking of hundreds of generated files
- **Broken References**: Moving projects breaks links to external media
- **Duplication Waste**: Similar variations store redundant data
- **No Regeneration**: Lost files cannot be recreated from project data
- **Collaboration Barriers**: Large files prevent efficient team workflows

### Gaps in Agent-Based Film Creation Pipeline
- **No Generation Memory**: Agents don't remember how content was created
- **Missing Parameter Storage**: Generation settings lost after creation
- **No Regeneration Logic**: Can't recreate content from stored parameters
- **Asset Lifecycle Gaps**: No system for managing generative vs. static assets
- **Version Evolution**: No mechanism to upgrade content with new models

---

## Solution Overview

### Feature Description within BMAD Agent Framework
The Regenerative Content Model implements a comprehensive asset management system where all creative decisions, parameters, and relationships are stored within the .blend file, while generated content exists as external files that can be regenerated at any time. This system treats generated content as a "cache" that can be cleared, moved, or recreated without losing the creative intent.

**Core Capabilities:**
1. **Parameter Persistence** - All generation parameters stored with assets in .blend file
2. **Reference Management** - Lightweight file references instead of embedded media
3. **Regeneration Engine** - One-click regeneration of any or all content
4. **Version Migration** - Upgrade content using newer models while preserving intent
5. **Selective Generation** - Generate only what's needed for current work
6. **Dependency Tracking** - Understand regeneration impact across assets
7. **Storage Optimization** - Automatic cleanup and space management

### Integration with Existing Film Crew Agents

**Agent Parameter Memory:**
- Each agent stores complete parameters for content it generates
- Parameters include model versions, seeds, prompts, and settings
- Agents can reconstruct exact workflows from stored parameters
- Version compatibility tracked for model evolution

**Regeneration Orchestration:**
- Producer agent manages regeneration workflows
- Maintains regeneration queue with dependency ordering
- Optimizes regeneration based on available resources
- Provides progress tracking and error recovery

**Asset Lifecycle Management:**
- Agents understand difference between source and generated assets
- Automatic marking of regeneratable vs. non-regeneratable content
- Cleanup policies for temporary and outdated generations
- Migration workflows for model version updates

### Backend Service Requirements

**Parameter Storage System:**
- JSON-based parameter serialization within .blend file
- Versioned parameter schemas for backward compatibility
- Compression for efficient storage of complex parameters
- Validation system for parameter integrity

**Regeneration API:**
- Batch regeneration endpoints for efficiency
- Priority queue system for selective regeneration
- Progress tracking with cancellation support
- Error recovery with partial regeneration

**File Reference System:**
- Relative path management for portability
- Missing file detection and reporting
- Automatic path resolution across platforms
- Reference validation and repair tools

---

## User Stories & Acceptance Criteria

### Epic 1: Regenerative Asset Foundation
**As a filmmaker, I want my project to store creative parameters instead of large files, so I can manage projects efficiently and iterate freely.**

#### User Story 1.1: Parameter-Based Asset Creation
- **Given** I generate any content (image, video, audio) using the addon
- **When** the generation completes
- **Then** all generation parameters are stored in the asset's properties
- **And** only a file reference is saved, not the actual content
- **And** the .blend file size remains small
- **And** I can see regeneration options for the asset

**Acceptance Criteria:**
- Generation parameters completely captured and stored
- File references use relative paths for portability
- .blend file growth <1KB per generated asset
- Regenerate button visible on all generated assets

#### User Story 1.2: Project Portability
- **Given** I have a project with hundreds of generated assets
- **When** I save and share the .blend file
- **Then** the file remains small enough for email (<25MB)
- **And** recipients can regenerate all content locally
- **And** creative intent is perfectly preserved
- **And** no large media files need to be transferred

**Acceptance Criteria:**
- .blend file size scales with creative complexity, not output size
- Complete project restoration from .blend file alone
- Cross-platform path resolution works correctly
- Clear indication of what needs regeneration

### Epic 2: Selective Regeneration
**As a director, I want to regenerate specific content on demand, so I can work efficiently and update only what I need.**

#### User Story 2.1: Individual Asset Regeneration
- **Given** I have a generated asset that I want to update
- **When** I click "Regenerate" on that asset
- **Then** only that asset is regenerated using stored parameters
- **And** the process uses the currently configured models
- **And** dependent assets are marked as potentially affected
- **And** I can choose to update dependencies or keep them

**Acceptance Criteria:**
- Single-asset regeneration completes without affecting others
- Model version changes are detected and reported
- Dependency impact analysis is accurate
- User has full control over cascade updates

#### User Story 2.2: Batch Regeneration Management
- **Given** I want to regenerate multiple assets (scene, character set, etc.)
- **When** I select multiple assets or use batch regeneration
- **Then** the system optimizes the regeneration order
- **And** shared resources (models, LoRAs) are loaded efficiently
- **And** progress is shown for the entire batch
- **And** failures don't stop other regenerations

**Acceptance Criteria:**
- Intelligent batching based on resource requirements
- Overall and per-asset progress tracking
- Graceful handling of individual failures
- Efficient resource utilization

### Epic 3: Version Evolution
**As a studio, I want projects to improve over time as AI models advance, while maintaining creative consistency.**

#### User Story 3.1: Model Version Migration
- **Given** new improved models are available
- **When** I open an older project
- **Then** I'm notified about available model updates
- **And** I can preview how updates would affect my content
- **And** I can selectively update specific asset types
- **And** original parameters are preserved for rollback

**Acceptance Criteria:**
- Clear notification of available improvements
- Non-destructive preview system
- Selective update capabilities
- Complete rollback functionality

#### User Story 3.2: Creative Intent Preservation
- **Given** I regenerate content with newer models
- **When** the regeneration completes
- **Then** the creative intent (composition, style, mood) is maintained
- **And** technical quality improves (resolution, coherence)
- **And** character/style consistency is preserved
- **And** I can compare old vs. new versions

**Acceptance Criteria:**
- Consistency scoring between versions
- Side-by-side comparison tools
- Automatic style/character reference updating
- Creative parameter translation between model versions

### Epic 4: Storage Management
**As a user with limited disk space, I want intelligent storage management, so I can work on large projects without running out of space.**

#### User Story 4.1: Automatic Cleanup
- **Given** I'm working on a project with many iterations
- **When** disk space becomes limited
- **Then** the system identifies safe-to-delete content
- **And** suggests cleanup options preserving recent work
- **And** ensures all cleaned content can be regenerated
- **And** provides clear space savings estimates

**Acceptance Criteria:**
- Intelligent identification of cleanup candidates
- Never deletes non-regeneratable content
- Clear communication of space savings
- One-click cleanup execution

#### User Story 4.2: Working Set Management
- **Given** I'm focusing on specific scenes
- **When** I mark my working set
- **Then** the system generates only required content
- **And** other content remains as parameters only
- **And** I can expand the working set as needed
- **And** background generation fills in as I work

**Acceptance Criteria:**
- Clear working set definition tools
- Lazy generation based on viewport/timeline
- Background generation during idle time
- Smooth transition as working set expands

---

## Technical Requirements

### Blender Addon Architecture Constraints

#### 1. Parameter Storage Schema
```python
class RegenerativeAssetProperties(PropertyGroup):
    """Base properties for all regenerative assets"""
    
    # Generation Metadata
    generation_timestamp: StringProperty(name="Generation Timestamp")
    generation_version: StringProperty(name="Model Version Used")
    can_regenerate: BoolProperty(name="Can Regenerate", default=True)
    
    # Parameter Storage
    generation_params_json: StringProperty(
        name="Generation Parameters",
        description="Complete parameters for regeneration",
        subtype='NONE',  # Store as raw JSON
        maxlen=0  # Unlimited length
    )
    
    # File Reference
    output_path: StringProperty(
        name="Output Path",
        description="Relative path to generated file",
        subtype='FILE_PATH'
    )
    file_exists: BoolProperty(name="File Exists", default=False)
    file_hash: StringProperty(name="File Hash", description="For change detection")
    
    # Dependency Tracking
    depends_on: CollectionProperty(
        name="Dependencies",
        type=PropertyGroup,
        description="Other assets this depends on"
    )
    
    def get_generation_params(self):
        """Deserialize generation parameters"""
        if self.generation_params_json:
            return json.loads(self.generation_params_json)
        return {}
    
    def set_generation_params(self, params):
        """Serialize generation parameters"""
        self.generation_params_json = json.dumps(params, indent=2)
    
    def check_file_exists(self):
        """Verify output file exists"""
        if self.output_path:
            abs_path = bpy.path.abspath(self.output_path)
            self.file_exists = os.path.exists(abs_path)
        return self.file_exists
```

#### 2. Regeneration Operators
```python
class MOVIE_DIRECTOR_OT_regenerate_asset(Operator):
    """Regenerate asset from stored parameters"""
    bl_idname = "movie_director.regenerate_asset"
    bl_label = "Regenerate Asset"
    bl_options = {'REGISTER', 'UNDO'}
    
    asset_id: StringProperty(name="Asset ID")
    use_latest_model: BoolProperty(name="Use Latest Model", default=False)
    
    def execute(self, context):
        asset = self.get_asset_by_id(self.asset_id)
        if not asset or not asset.can_regenerate:
            self.report({'ERROR'}, "Asset cannot be regenerated")
            return {'CANCELLED'}
        
        # Get stored parameters
        params = asset.get_generation_params()
        
        # Update model version if requested
        if self.use_latest_model:
            params = self.migrate_parameters(params, asset.generation_version)
        
        # Queue regeneration
        regeneration_queue.add_task(
            asset_id=self.asset_id,
            params=params,
            priority=RegenerationPriority.USER_REQUESTED
        )
        
        self.report({'INFO'}, f"Regeneration queued for {asset.name}")
        return {'FINISHED'}

class MOVIE_DIRECTOR_OT_regenerate_missing(Operator):
    """Regenerate all missing files"""
    bl_idname = "movie_director.regenerate_missing"
    bl_label = "Regenerate Missing Files"
    
    def execute(self, context):
        missing_assets = self.find_missing_assets(context)
        
        if not missing_assets:
            self.report({'INFO'}, "No missing files found")
            return {'FINISHED'}
        
        # Queue all missing assets for regeneration
        for asset in missing_assets:
            regeneration_queue.add_task(
                asset_id=asset.id,
                params=asset.get_generation_params(),
                priority=RegenerationPriority.MISSING_FILE
            )
        
        self.report({'INFO'}, f"Queued {len(missing_assets)} assets for regeneration")
        return {'FINISHED'}
```

#### 3. Path Management System
```python
class RegenerativePathManager:
    """Manages file paths for regenerative content"""
    
    @staticmethod
    def get_project_content_dir(blend_path):
        """Get content directory relative to .blend file"""
        blend_dir = os.path.dirname(blend_path)
        blend_name = os.path.splitext(os.path.basename(blend_path))[0]
        return os.path.join(blend_dir, f"{blend_name}_generated")
    
    @staticmethod
    def make_relative_path(abs_path, blend_path):
        """Convert absolute path to relative for portability"""
        try:
            return os.path.relpath(abs_path, os.path.dirname(blend_path))
        except ValueError:
            # Different drives on Windows
            return abs_path
    
    @staticmethod
    def resolve_path(relative_path, blend_path):
        """Resolve relative path to absolute"""
        if os.path.isabs(relative_path):
            return relative_path
        blend_dir = os.path.dirname(blend_path)
        return os.path.abspath(os.path.join(blend_dir, relative_path))
    
    @staticmethod
    def organize_by_type(content_dir, asset_type, asset_name):
        """Create organized directory structure"""
        type_dir = os.path.join(content_dir, asset_type.lower())
        asset_dir = os.path.join(type_dir, sanitize_filename(asset_name))
        os.makedirs(asset_dir, exist_ok=True)
        return asset_dir
```

### CrewAI Framework Integration

#### 1. Agent Parameter Capture
```python
class RegenerativeAgentMixin:
    """Mixin for agents to support regenerative content"""
    
    def capture_generation_params(self, task, result):
        """Capture all parameters used in generation"""
        params = {
            'task': task.description,
            'agent': self.__class__.__name__,
            'timestamp': datetime.now().isoformat(),
            'model_version': self.get_model_version(),
            'random_seed': getattr(task, 'seed', None),
            'backend_config': self.get_backend_config(),
            'inputs': self.serialize_inputs(task),
            'workflow_template': getattr(task, 'workflow_template', None),
        }
        
        # Agent-specific parameters
        params.update(self.get_agent_specific_params(task))
        
        return params
    
    def regenerate_from_params(self, params):
        """Regenerate content from stored parameters"""
        # Reconstruct task from parameters
        task = self.reconstruct_task(params)
        
        # Check model compatibility
        if not self.is_compatible_version(params['model_version']):
            task = self.migrate_task(task, params['model_version'])
        
        # Execute regeneration
        result = self.execute(task)
        
        # Update stored parameters if models changed
        if self.get_model_version() != params['model_version']:
            params['model_version'] = self.get_model_version()
            params['migrated_from'] = params.get('model_version')
        
        return result, params
```

#### 2. Regeneration Queue System
```python
class RegenerationQueue:
    """Manages regeneration tasks with priority and optimization"""
    
    def __init__(self, backend_integration):
        self.backend = backend_integration
        self.queue = PriorityQueue()
        self.active_tasks = {}
        self.completed_tasks = {}
        
    def add_task(self, asset_id, params, priority):
        """Add regeneration task to queue"""
        task = RegenerationTask(
            asset_id=asset_id,
            params=params,
            priority=priority,
            dependencies=self.analyze_dependencies(asset_id)
        )
        self.queue.put((priority.value, task))
        
    def process_queue(self):
        """Process regeneration queue with optimization"""
        batch = self.build_optimal_batch()
        
        for task in batch:
            self.active_tasks[task.asset_id] = task
            
            try:
                # Regenerate using appropriate agent
                agent = self.get_agent_for_params(task.params)
                result, updated_params = agent.regenerate_from_params(task.params)
                
                # Update asset with new file reference
                self.update_asset_reference(task.asset_id, result, updated_params)
                
                self.completed_tasks[task.asset_id] = task
                
            except RegenerationError as e:
                self.handle_regeneration_error(task, e)
            
            finally:
                del self.active_tasks[task.asset_id]
    
    def build_optimal_batch(self):
        """Build batch optimizing for shared resources"""
        batch = []
        model_groups = defaultdict(list)
        
        # Group by model requirements
        while not self.queue.empty() and len(batch) < MAX_BATCH_SIZE:
            priority, task = self.queue.get()
            model_key = self.get_model_key(task.params)
            model_groups[model_key].append(task)
        
        # Order to minimize model loading/unloading
        for model_key in sorted(model_groups.keys(), key=self.estimate_load_time):
            batch.extend(model_groups[model_key])
        
        return batch
```

### Performance and Resource Considerations

#### 1. Storage Optimization
- **Lazy Generation**: Only generate content when actually needed
- **Progressive Loading**: Generate low-res previews first, full quality on demand
- **Cleanup Policies**: Automatic removal of old generations with safe regeneration
- **Compression**: Use efficient formats for generated content storage

#### 2. Regeneration Performance
- **Batch Processing**: Group regenerations by model/resource requirements
- **Incremental Updates**: Only regenerate changed dependencies
- **Parallel Execution**: Multiple regenerations when resources allow
- **Cache Management**: Keep frequently used content readily available

#### 3. File Management
- **Path Validation**: Continuous validation of file references
- **Auto-Repair**: Automatic fixing of broken paths when possible
- **Migration Tools**: Update paths when moving projects
- **Cleanup Safety**: Never delete non-regeneratable content

---

## Success Metrics

### Storage and Efficiency
**Primary KPIs:**
- **Storage Reduction**: >90% reduction in project storage requirements
- **Transfer Efficiency**: Average .blend file <50MB for feature-length projects
- **Regeneration Speed**: <5 minutes to regenerate typical scene assets
- **Cache Hit Rate**: >80% of content available without regeneration

**Measurement Methods:**
- Storage comparison between traditional and regenerative projects
- File size analytics across user projects
- Regeneration timing studies
- Cache efficiency monitoring

### Workflow Enhancement
**Productivity Metrics:**
- **Version Control Adoption**: >60% of users using Git with projects
- **Collaboration Increase**: 3x increase in project sharing
- **Iteration Velocity**: 5x more variations explored per project
- **Model Migration**: >40% of users upgrading projects with new models

**Measurement Methods:**
- Git integration usage analytics
- Project sharing statistics
- Variation counting per project
- Model version migration tracking

### Reliability and Trust
**System Reliability:**
- **Regeneration Success Rate**: >99% successful regeneration
- **Parameter Integrity**: Zero parameter corruption incidents
- **Path Resolution**: >95% automatic path resolution success
- **Recovery Success**: 100% recovery from missing files

**Measurement Methods:**
- Automated regeneration testing
- Parameter validation checking
- Path resolution analytics
- Recovery scenario testing

---

## Risk Assessment & Mitigation

### Technical Risks

#### High Risk: Parameter Storage Reliability
- **Risk**: Generation parameters could be lost or corrupted
- **Probability**: Low (20%)
- **Impact**: High - Permanent loss of creative work
- **Mitigation Strategy**:
  - Multiple parameter backup locations within .blend
  - Validation on every save
  - Parameter export tools for external backup
  - Corruption detection and recovery

#### Medium Risk: Model Deprecation
- **Risk**: Old models become unavailable for regeneration
- **Probability**: Medium (40%)
- **Impact**: Medium - Some content cannot be regenerated
- **Mitigation Strategy**:
  - Model version archive system
  - Parameter migration tools
  - Fallback to similar models
  - Warning system for deprecated content

### User Trust Risks

#### High Risk: Regeneration Differences
- **Risk**: Regenerated content differs from original
- **Probability**: Medium (35%)
- **Impact**: High - Loss of user trust
- **Mitigation Strategy**:
  - Deterministic generation with fixed seeds
  - Visual comparison tools
  - Option to preserve original files
  - Clear communication about variations

#### Medium Risk: Performance Perception
- **Risk**: Regeneration time frustrates users
- **Probability**: High (50%)
- **Impact**: Medium - Workflow disruption
- **Mitigation Strategy**:
  - Smart caching strategies
  - Background regeneration
  - Progressive quality loading
  - Clear progress communication

---

## Implementation Roadmap

### Phase 1: Core Parameter System (Weeks 1-3)
**Deliverables:**
- Parameter storage schema implementation
- Basic regeneration operators
- Path management system
- File reference validation

**Success Criteria:**
- Parameters correctly stored for all generation types
- Basic regeneration works for simple assets
- Paths remain valid after project moves
- No growth in .blend file size

### Phase 2: Regeneration Engine (Weeks 4-6)
**Deliverables:**
- Complete regeneration queue system
- Agent parameter capture integration
- Batch optimization algorithms
- Progress tracking UI

**Success Criteria:**
- Queue processes efficiently
- All agents support regeneration
- Batch processing improves performance
- Users informed of progress

### Phase 3: Advanced Features (Weeks 7-9)
**Deliverables:**
- Model version migration system
- Working set management
- Automatic cleanup tools
- Comparison utilities

**Success Criteria:**
- Projects upgrade smoothly
- Storage efficiently managed
- Safe cleanup operations
- Easy comparison of versions

### Phase 4: Polish and Optimization (Weeks 10-12)
**Deliverables:**
- Performance optimizations
- Advanced caching strategies
- Comprehensive testing
- User documentation

**Success Criteria:**
- Regeneration performance acceptable
- Cache hit rates meet targets
- System reliability proven
- Users understand benefits

---

## Cross-PRD Integration Specifications

### Backend Integration
- **Integration**: PRD-007 → PRD-001
- **Process**: Backend service stores and retrieves generation parameters
- **Parameter Format**: Standardized JSON schema across all backends
- **Queue Management**: Backend integration handles regeneration queue

### Node Canvas Display
- **Integration**: PRD-007 → PRD-006
- **Process**: Nodes show regeneration status and options
- **Visual Indicators**: Missing files, outdated versions, regeneration progress
- **Quick Actions**: Regenerate buttons directly on nodes

### Asset-Specific Regeneration
- **Integration**: PRD-007 → PRD-003/004/005
- **Process**: Each asset type has specialized regeneration logic
- **Consistency**: Character/Style/Environment consistency maintained
- **Dependencies**: Proper handling of asset interdependencies

---

## Stakeholder Sign-Off

### Development Team Approval
- [ ] **Technical Lead** - Parameter storage architecture approved
- [ ] **Backend Specialist** - Regeneration API design validated
- [ ] **QA Lead** - Testing strategy comprehensive

### Business Stakeholder Approval
- [ ] **Product Owner** - Business value clearly demonstrated
- [ ] **Community Manager** - User benefits well articulated
- [ ] **Support Lead** - Support implications understood

### User Representative Review
- [ ] **Power User** - Advanced features meet needs
- [ ] **Storage-Limited User** - Storage benefits significant
- [ ] **Collaborative User** - Sharing improvements valuable

---

**Next Steps:**
1. Design detailed parameter schema for each content type
2. Create regeneration API specification
3. Develop path management testing suite
4. Plan user education on regenerative concepts

---

*This PRD establishes the Regenerative Content Model as the foundational architecture that enables Blender Movie Director to manage limitless creative iterations while maintaining tiny file sizes, perfect portability, and future-proof flexibility.*