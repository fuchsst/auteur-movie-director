# Product Requirements Document: Style Consistency Framework

**Version:** 2.0  
**Date:** 2025-01-29  
**Owner:** BMAD Business Analyst  
**Status:** Web Architecture Pivot  
**PRD ID:** PRD-004  
**Dependencies:** Backend Integration Service Layer (PRD-001), Intelligent Script-to-Shot Breakdown System (PRD-002), Character Consistency Engine (PRD-003), Environment Management System (PRD-005), Node-Based Production Canvas (PRD-006), Regenerative Content Model (PRD-007), File-Based Project Structure (PRD-008)

---

## Executive Summary

### Business Justification
The Style Consistency Framework represents the critical visual coherence layer that transforms Movie Director from a technically functional tool into a professional-grade creative platform capable of producing broadcast-quality content through collaborative web workflows. While character consistency ensures identity across shots, style consistency ensures aesthetic coherence across entire productions, creating the polished, professional appearance that distinguishes commercial-quality content from amateur projects.

This framework addresses the fundamental challenge that prevents generative AI from competing with traditional film production: maintaining a consistent visual language throughout a project. In a web-based collaborative environment, this challenge is amplified as multiple team members work simultaneously on different aspects of the production. The Style Consistency Framework ensures visual coherence regardless of who generates content or which backend processes it.

The system operates on the regenerative content model: teams define style parameters once in the PostgreSQL database as project definitions, and the system maintains that aesthetic across unlimited generations, iterations, and revisions. Style assets exist as parametric definitions with S3 file references to generated content (style LoRAs, color LUTs, reference images), enabling complete style regeneration and modification at any time while supporting real-time collaborative workflows.

### Target User Personas
- **Distributed Creative Teams** - Maintaining brand aesthetic across global team members
- **Digital Agencies** - Ensuring visual consistency for multi-channel campaigns
- **Production Studios** - Coordinating house style across distributed artists
- **Brand Managers** - Enforcing brand guidelines in collaborative content creation
- **Film Schools** - Teaching visual consistency principles through cloud collaboration
- **Freelance Collectives** - Sharing consistent aesthetics across project contributors

### Expected Impact on Film Production Workflow
- **Collaborative Style Development**: Multiple artists refine visual style simultaneously
- **Cloud-Based Consistency**: Leverage powerful servers for advanced style models
- **Real-Time Style Updates**: Visual changes instantly visible to all team members
- **Scalable Style Processing**: Apply complex styles without local hardware limitations
- **Global Style Library**: Share style assets across projects and organizations

---

## Problem Statement

### Current Limitations in Desktop Style Tools
1. **Single-User Style Development**: Visual style locked to individual workstations
2. **No Real-Time Style Sharing**: Team members work on aesthetics in isolation
3. **Hardware-Limited Processing**: Complex style models require expensive local GPUs
4. **File Synchronization Chaos**: Style asset versions conflict across team
5. **Limited Model Access**: Can't leverage cutting-edge style models without setup

### Pain Points in Web-Based Creative Tools
- **No Advanced Style Models**: Web tools lack sophisticated style consistency
- **Fragmented Style Management**: Visual references scattered across services
- **Poor Team Coordination**: No unified style development workflow
- **Limited Processing Power**: Browser-based tools can't handle complex styles
- **No Version Control**: Style iterations lost without proper tracking

### Gaps in Current Web Pipeline
- **Missing Style Enforcement**: No coordinated style application across content
- **No Distributed Training**: Can't leverage cloud GPUs for style model training
- **Limited Real-Time Preview**: Style updates not instantly visible to team
- **Poor Cross-Project Sharing**: Styles locked to single projects

---

## Solution Overview

### Feature Description within Web Architecture
The Style Consistency Framework leverages the distributed web architecture to provide collaborative style development with advanced AI models. Using Function Runner for heterogeneous model execution and Celery for distributed processing, teams can develop, maintain, and apply consistent visual styles across entire productions with real-time synchronization.

**Core Capabilities:**
1. **Collaborative Style Gallery** - Real-time shared style asset library
2. **Cloud-Based Style Training** - Distributed style LoRA training on GPU workers
3. **Advanced Model Integration** - Style Alliance, Apply Style Model via Function Runner
4. **Live Style Preview** - Instant visual updates across all clients
5. **Quality-Tiered Style Application** - Three levels of style quality
6. **Version History** - Complete style evolution tracking
7. **Cross-Project Templates** - Share styles across productions
8. **Team Annotations** - Collaborative notes on style development
9. **Batch Application** - Apply styles to multiple assets in parallel
10. **API Access** - Integrate style system with external tools
11. **Git LFS Integration** - Version control for style assets
12. **File Structure Compliance** - Organized in project hierarchy

**Quality Tier Specifications:**
- **Low Quality**: Basic style transfer, fast application, minimal VRAM
- **Standard Quality**: Enhanced style consistency, balanced performance
- **High Quality**: Maximum style fidelity with advanced models

### Integration with Advanced Style Models
**Function Runner Model Support:**
- **Style Alliance**: Coordinated parameter management across shots
- **Apply Style Model (Adjusted)**: FLUX-optimized style application
- **Custom Style LoRAs**: Team-trained style models
- **Color Science Models**: Advanced color grading algorithms

**Distributed Processing Benefits:**
- Parallel style application across multiple shots
- Real-time progress updates to all team members
- Automatic model selection based on style requirements
- Seamless coordination with character and environment systems

### Backend Service Architecture
**FastAPI Endpoints:**
- Style CRUD operations with team permissions
- Training job submission and monitoring
- Style validation and consistency scoring
- Gallery management and sharing

**Celery Task Processing:**
- Distributed style LoRA training with quality-based queues
- Parallel style application to shots per quality tier
- Batch color grading operations
- Style consistency validation
- Progress streaming to all connected clients

**File Storage Integration:**
- Styles stored in `01_Assets/Generative_Assets/Styles/`
- Reference images in standardized subdirectories
- Style models tracked with Git LFS
- Metadata in version-controlled JSON files

**WebSocket Events:**
- Real-time style preview updates
- Training progress streaming
- Gallery synchronization
- Team collaboration events

---

## User Stories & Acceptance Criteria

### Epic 1: Collaborative Style Development
**As a creative team, we want to develop visual styles together in real-time so that we maintain consistent aesthetic vision across our production.**

#### User Story 1.1: Shared Style Gallery
- **Given** multiple team members working on visual style
- **When** one member creates or updates a style
- **Then** all team members see the change immediately
- **And** can access the same style parameters and references
- **And** see who made what changes and when
- **And** can revert to previous versions if needed

**Acceptance Criteria:**
- Real-time gallery synchronization <500ms
- Version history with visual diff
- User attribution for all changes
- Rollback capability with team notification

#### User Story 1.2: Collaborative Style Refinement
- **Given** a team has created initial style concepts
- **When** they want to refine visual parameters together
- **Then** multiple users can adjust style settings
- **And** see real-time preview updates
- **And** vote on preferred style variations
- **And** reach consensus through visual feedback

**Acceptance Criteria:**
- Multi-user parameter editing
- Live preview generation
- Voting/approval mechanism
- Consensus visualization

### Epic 2: Cloud-Based Style Processing
**As a filmmaker, I want to use powerful style models without local hardware requirements so that I can achieve professional visual consistency.**

#### User Story 2.1: Distributed Style Training
- **Given** I have style reference materials
- **When** I initiate style LoRA training
- **Then** the job is distributed to GPU workers
- **And** progress updates stream to all team members
- **And** the trained model is available immediately
- **And** can be applied from any browser

**Acceptance Criteria:**
- Distributed training across GPU workers
- Real-time progress via WebSocket
- Automatic model deployment
- Cross-device accessibility

#### User Story 2.2: Intelligent Style Application
- **Given** different shots with varying content
- **When** I apply a project style
- **Then** the system adapts style intensity appropriately
- **And** preserves character identity
- **And** maintains environment coherence
- **And** provides consistent results

**Acceptance Criteria:**
- Adaptive style intensity algorithms
- Character preservation logic
- Environment coordination
- Consistency validation

### Epic 3: Style-Character-Environment Coordination
**As a production team, we want styles to work harmoniously with characters and environments so that all elements create a cohesive visual experience.**

#### User Story 3.1: Character-Aware Style Application
- **Given** shots containing established characters
- **When** applying project style
- **Then** character identity is preserved
- **And** style enhances character presentation
- **And** no visual conflicts occur
- **And** team sees coordination status

**Acceptance Criteria:**
- Character identity protection >95%
- Style enhancement algorithms
- Conflict detection system
- Real-time status updates

#### User Story 3.2: Environment Style Integration
- **Given** environments with specific moods
- **When** applying style parameters
- **Then** environment aesthetics are enhanced
- **And** lighting coherence is maintained
- **And** multi-angle consistency is preserved
- **And** style supports narrative mood

**Acceptance Criteria:**
- Environment enhancement metrics
- Lighting consistency >90%
- Multi-angle validation
- Mood preservation scoring

### Epic 4: Professional Color Science
**As a colorist, I want automated color grading that meets broadcast standards so that our content is professionally polished.**

#### User Story 4.1: Cloud Color Grading
- **Given** generated shots with style requirements
- **When** I request color grading
- **Then** professional LUTs are generated
- **And** applied consistently across shots
- **And** exported in industry formats
- **And** work in standard NLEs

**Acceptance Criteria:**
- LUT generation <30 seconds
- Cross-shot consistency >95%
- DaVinci/Premiere compatibility
- Broadcast standard compliance

#### User Story 4.2: Collaborative Color Review
- **Given** color graded sequences
- **When** team reviews results
- **Then** everyone sees the same colors
- **And** can annotate specific issues
- **And** suggest adjustments
- **And** approve final grades together

**Acceptance Criteria:**
- Color-accurate streaming
- Frame-specific annotations
- Adjustment workflow
- Multi-user approval system

### Epic 5: Cross-Project Style Management
**As a studio, we want to build a library of signature styles so that we can maintain brand consistency across all productions.**

#### User Story 5.1: Style Templates
- **Given** successful project styles
- **When** I want to reuse them
- **Then** I can export as templates
- **And** import into new projects
- **And** maintain all parameters
- **And** track usage analytics

**Acceptance Criteria:**
- Template export/import
- Parameter preservation
- Usage tracking
- Version management

#### User Story 5.2: Brand Style Library
- **Given** multiple brand guidelines
- **When** creating content
- **Then** appropriate styles are suggested
- **And** brand compliance is validated
- **And** variations stay within guidelines
- **And** reports demonstrate compliance

**Acceptance Criteria:**
- Brand guideline integration
- Compliance validation
- Variation constraints
- Compliance reporting

---

## Technical Requirements

### Web Application Architecture

#### 1. Frontend Components (SvelteKit)
```typescript
// Style Gallery Component with Real-time Sync
export class StyleGallery extends SvelteComponent {
    private websocket: WebSocket;
    private styles = writable<Style[]>([]);
    
    onMount() {
        // Connect to style updates
        this.websocket = new WebSocket(`${WS_URL}/project/${projectId}/styles`);
        
        // Handle real-time updates
        this.websocket.on('style.update', (data: StyleUpdate) => {
            this.updateStyleInGallery(data);
            this.generateLivePreview(data.styleId);
        });
        
        // Handle training progress
        this.websocket.on('training.progress', (data: TrainingProgress) => {
            this.updateTrainingStatus(data.styleId, data.progress);
        });
    }
    
    async applyStyleToBatch(styleId: string, targetShots: string[]) {
        const response = await fetch(`/api/styles/${styleId}/apply-batch`, {
            method: 'POST',
            body: JSON.stringify({ shots: targetShots })
        });
        
        // Track batch application progress
        this.trackBatchApplication(await response.json());
    }
}

// Color Grading Component
export class ColorGradingPanel extends SvelteComponent {
    private colorSpace = writable('rec709');
    private lutPreview = writable(null);
    
    async generateLUT(styleId: string, colorParams: ColorParameters) {
        const response = await fetch(`/api/styles/${styleId}/generate-lut`, {
            method: 'POST',
            body: JSON.stringify(colorParams)
        });
        
        const lut = await response.json();
        
        // Update preview for all team members
        this.websocket.send({
            type: 'lut.preview',
            styleId,
            lutData: lut
        });
    }
}
```

#### 2. API Endpoints (FastAPI)
```python
@app.post("/api/styles/{style_id}/train")
async def train_style_lora(
    style_id: str,
    training_params: StyleTrainingParameters,
    current_user: User = Depends(get_current_user)
):
    """Submit style LoRA training job"""
    # Validate reference materials
    style = await get_style(style_id)
    if len(style.reference_images) < 10:
        raise HTTPException(400, "Insufficient reference images")
    
    # Queue training with priority
    task = celery_app.send_task(
        'style.train_lora',
        args=[style_id, training_params.dict()],
        priority=calculate_priority(current_user.tier),
        queue='gpu_training'
    )
    
    # Notify team
    await notify_team_websocket(style.project_id, {
        'type': 'training.started',
        'styleId': style_id,
        'initiatedBy': current_user.id
    })
    
    return {"job_id": task.id, "status": "queued"}

@app.post("/api/styles/{style_id}/apply-coordinated")
async def apply_style_with_coordination(
    style_id: str,
    application_params: StyleApplicationParams,
    current_user: User = Depends(get_current_user)
):
    """Apply style with character/environment coordination"""
    # Get style and validate
    style = await get_style(style_id)
    
    # Check for character conflicts
    if application_params.contains_characters:
        character_params = await coordinate_with_characters(
            style_id,
            application_params.character_ids
        )
        application_params.character_preservation = character_params
    
    # Check for environment requirements
    if application_params.environment_id:
        env_params = await coordinate_with_environment(
            style_id,
            application_params.environment_id
        )
        application_params.environment_adaptation = env_params
    
    # Queue coordinated application
    task = celery_app.send_task(
        'style.apply_coordinated',
        args=[style_id, application_params.dict()],
        queue='gpu_style'
    )
    
    return {"task_id": task.id, "coordination": application_params.dict()}
```

#### 3. Style Processing Tasks
```python
@celery_app.task(name='style.train_lora')
def train_style_lora_task(style_id: str, params: Dict):
    """Train style LoRA with distributed processing"""
    
    # Prepare training data
    training_data = prepare_style_training_data(style_id)
    
    # Configure distributed training
    if params.get('use_style_alliance', True):
        workflow = 'style_alliance_lora_training'
    else:
        workflow = 'standard_style_lora_training'
    
    # Execute training
    trainer = DistributedStyleTrainer()
    result = trainer.train(
        workflow=workflow,
        data=training_data,
        params=params,
        progress_callback=lambda p: notify_progress(style_id, p)
    )
    
    # Deploy trained model
    deploy_style_model(style_id, result['model_path'])
    
    return result

@celery_app.task(name='style.generate_lut')
def generate_color_lut_task(style_id: str, color_params: Dict):
    """Generate professional color grading LUT"""
    
    # Analyze style color properties
    style_data = get_style_data(style_id)
    color_analyzer = ColorScienceEngine()
    
    # Generate LUT with mood consideration
    lut_params = color_analyzer.calculate_lut(
        base_palette=style_data['color_palette'],
        mood_target=color_params.get('mood', 'neutral'),
        intensity=color_params.get('intensity', 0.8)
    )
    
    # Create industry-standard LUT
    lut_generator = ProfessionalLUTGenerator()
    lut_file = lut_generator.create(
        params=lut_params,
        format=color_params.get('format', 'cube'),
        color_space=color_params.get('color_space', 'rec709')
    )
    
    # Store and distribute
    lut_url = upload_to_s3(lut_file, f'styles/{style_id}/luts/')
    
    return {"lut_url": lut_url, "parameters": lut_params}
```

#### 4. Style Coordination System
```python
class StyleCoordinationManager:
    """Manages style coordination with characters and environments"""
    
    async def coordinate_with_characters(self, style_id: str, character_ids: List[str]):
        """Ensure style doesn't override character identity"""
        
        coordination_params = {
            'character_preservation_zones': [],
            'style_intensity_map': {},
            'protection_masks': []
        }
        
        for char_id in character_ids:
            character = await get_character(char_id)
            
            # Calculate preservation requirements
            preservation = self.calculate_character_preservation(
                character.visual_features,
                style_intensity=0.8
            )
            
            coordination_params['character_preservation_zones'].append({
                'character_id': char_id,
                'preservation_level': preservation['level'],
                'protected_features': preservation['features']
            })
        
        return coordination_params
    
    async def coordinate_with_environment(self, style_id: str, env_id: str):
        """Adapt style to environment requirements"""
        
        environment = await get_environment(env_id)
        style = await get_style(style_id)
        
        # Analyze compatibility
        compatibility = self.analyze_style_environment_compatibility(
            style.parameters,
            environment.properties
        )
        
        # Generate adaptation parameters
        adaptation = {
            'lighting_adjustment': compatibility['lighting_delta'],
            'color_temperature_shift': compatibility['temperature_shift'],
            'contrast_modification': compatibility['contrast_adapt'],
            'mood_preservation': environment.mood_requirements
        }
        
        return adaptation
```

### Database Schema Extensions

#### PostgreSQL Tables for Style Management
```sql
-- Style assets with collaboration
CREATE TABLE styles (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    name VARCHAR(255),
    description TEXT,
    style_type VARCHAR(50), -- project, scene, shot
    parent_style_id UUID REFERENCES styles(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    parameters JSONB,
    color_palette JSONB
);

-- Style training jobs
CREATE TABLE style_training_jobs (
    id UUID PRIMARY KEY,
    style_id UUID REFERENCES styles(id),
    status VARCHAR(50),
    priority INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    initiated_by UUID REFERENCES users(id),
    training_params JSONB,
    model_url TEXT
);

-- Style applications tracking
CREATE TABLE style_applications (
    id UUID PRIMARY KEY,
    style_id UUID REFERENCES styles(id),
    target_type VARCHAR(50), -- shot, character, environment
    target_id UUID,
    coordination_params JSONB,
    applied_by UUID REFERENCES users(id),
    applied_at TIMESTAMP,
    consistency_score FLOAT
);

-- Brand style library
CREATE TABLE brand_styles (
    id UUID PRIMARY KEY,
    organization_id UUID,
    brand_name VARCHAR(255),
    style_id UUID REFERENCES styles(id),
    compliance_rules JSONB,
    usage_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT false
);

-- Style annotations for collaboration
CREATE TABLE style_annotations (
    id UUID PRIMARY KEY,
    style_id UUID REFERENCES styles(id),
    user_id UUID REFERENCES users(id),
    annotation_type VARCHAR(50),
    content TEXT,
    frame_reference VARCHAR(255),
    created_at TIMESTAMP
);
```

### Performance Optimizations

#### 1. Distributed Style Processing
- GPU worker pools for style training
- Parallel style application across shots
- Intelligent caching of style parameters
- Progressive loading for large galleries

#### 2. Real-time Synchronization
- WebSocket connection pooling
- Differential updates for style changes
- Optimistic UI updates
- Conflict-free replicated data types (CRDTs)

#### 3. Color Science Optimization
- Hardware-accelerated LUT generation
- Color space conversion caching
- Batch color grading operations
- CDN distribution for LUT files

---

## Success Metrics

### Visual Consistency Quality
**Primary KPIs:**
- **Style Coherence**: >90% consistency across productions
- **Color Accuracy**: Delta-E <2.0 for brand colors
- **Professional Approval**: >85% broadcast quality rating
- **Team Satisfaction**: >4.5/5.0 collaboration rating

**Measurement Methods:**
- Automated style consistency analysis
- Professional colorist evaluations
- Team collaboration surveys
- Brand compliance audits

### Collaboration Effectiveness
**Team Metrics:**
- **Concurrent Editors**: Average 3+ per style
- **Iteration Speed**: 5x faster style development
- **Consensus Time**: <30 minutes for approval
- **Global Teams**: 50% with 3+ time zones

**System Metrics:**
- Real-time sync performance
- Conflict resolution success rate
- Version rollback frequency
- Cross-team style sharing

### Technical Performance
**Processing Metrics:**
- **Training Time**: <60 minutes for style LoRA
- **Application Speed**: <2 minutes per shot
- **LUT Generation**: <20 seconds
- **Preview Updates**: <500ms globally

**Scalability Metrics:**
- **Concurrent Styles**: 1000+ per instance
- **Training Jobs**: 50+ simultaneous
- **Storage Efficiency**: <100MB per style
- **API Throughput**: 10,000+ requests/hour

---

## Risk Assessment & Mitigation

### Technical Risks

#### High Risk: Style Model Complexity
- **Risk**: Advanced style models fail in production
- **Impact**: Limited to basic styles only
- **Mitigation**: 
  - Comprehensive model testing
  - Graceful fallback mechanisms
  - Multiple style algorithms
  - Clear capability communication

#### Medium Risk: Color Science Accuracy
- **Risk**: Color grading doesn't match professional standards
- **Impact**: Additional post-production needed
- **Mitigation**:
  - Partnership with color science experts
  - Professional tool integration
  - Calibration workflows
  - Manual override options

### Business Risks

#### High Risk: Brand Compliance
- **Risk**: Generated content violates brand guidelines
- **Impact**: Client rejection, legal issues
- **Mitigation**:
  - Automated compliance checking
  - Brand guideline integration
  - Approval workflows
  - Audit trails

---

## Implementation Roadmap

### Phase 1: Core Style Infrastructure (Weeks 1-4)
**Deliverables:**
- Basic style CRUD with real-time sync
- Style gallery with WebSocket updates
- Simple style application
- Team collaboration features

**Success Criteria:**
- Multi-user style editing functional
- Real-time updates working
- Basic application operational

### Phase 2: Advanced Processing (Weeks 5-8)
**Deliverables:**
- Distributed style training
- Character/environment coordination
- Professional color grading
- Performance optimization

**Success Criteria:**
- Style training operational
- Coordination algorithms working
- LUTs meet broadcast standards

### Phase 3: Brand Integration (Weeks 9-12)
**Deliverables:**
- Brand guideline system
- Compliance validation
- Template management
- Analytics dashboard

**Success Criteria:**
- Brand compliance >95%
- Template system functional
- Analytics providing insights

### Phase 4: Enterprise Features (Weeks 13-16)
**Deliverables:**
- Cross-organization sharing
- Advanced permissions
- API documentation
- Integration tools

**Success Criteria:**
- Sharing system secure
- Permissions granular
- API fully documented
- Third-party integrations working

---

## Stakeholder Sign-Off

### Development Team Approval
- [ ] **Frontend Lead** - Gallery and preview architecture approved
- [ ] **Backend Lead** - Distributed processing design validated
- [ ] **ML Engineer** - Style model integration confirmed
- [ ] **DevOps Lead** - Scalability plan approved

### Business Stakeholder Approval
- [ ] **Product Owner** - Collaboration features meet needs
- [ ] **Brand Manager** - Compliance system adequate
- [ ] **Creative Director** - Quality meets standards
- [ ] **Legal** - IP and compliance handled

---

**Next Steps:**
1. Design collaborative style UI mockups
2. Set up distributed training infrastructure
3. Create color science test suite
4. Plan brand compliance system
5. Design professional integration APIs

---

*This PRD represents the transformation of style consistency from a single-user technical feature to a collaborative creative system, enabling global teams to maintain professional visual coherence through the power of cloud computing and real-time synchronization.*