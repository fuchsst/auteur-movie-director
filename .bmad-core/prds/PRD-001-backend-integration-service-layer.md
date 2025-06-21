# Product Requirements Document: Backend Integration Service Layer

**Version:** 1.0  
**Date:** 2025-01-21  
**Owner:** BMAD Business Analyst  
**Status:** Draft - Stakeholder Review  
**PRD ID:** PRD-001  
**Dependencies:** None (Foundation layer for all other PRD systems)  

---

## Executive Summary

### Business Justification
The Backend Integration Service Layer is the foundational infrastructure component that transforms the Blender Movie Director from a non-functional UI prototype into a complete generative film studio. This layer serves as the critical bridge between Blender's native interface and the powerful AI generation backends (ComfyUI, Wan2GP, LiteLLM), enabling users to create professional-quality video content entirely within their familiar Blender environment.

This foundation layer directly enables the regenerative content model that defines the entire platform: users define project parameters once in the .blend file, while the backend service layer orchestrates unlimited content generation and regeneration from those stored definitions. This architectural approach ensures project portability, version control compatibility, and eliminates the traditional file management burden of generative workflows.

### Target User Personas
- **Independent Filmmakers** - Creating short films and concept videos on limited budgets
- **Content Creators** - YouTubers, social media creators needing high-quality video content
- **Concept Artists** - Visualizing ideas for pre-production and pitching
- **Advertising Agencies** - Rapid prototyping of video advertisements and promotional content
- **Educational Institutions** - Teaching film production and AI integration

### Expected Impact on Film Production Workflow
- **Workflow Transformation**: Reduce video production time from weeks to hours through intelligent automation
- **Cost Reduction**: Eliminate need for expensive production equipment and teams (90%+ cost savings)
- **Creative Democratization**: Enable solo creators to produce studio-quality content without technical barriers
- **Market Positioning**: Establish Blender as the premier platform for AI-assisted filmmaking
- **Professional Adoption**: Enable broadcast-quality content creation for sub-$5K budgets

---

## Problem Statement

### Current Limitations in Generative Film Production
1. **Fragmented Workflow**: Artists must juggle multiple disconnected tools (ComfyUI web interface, command-line tools, manual file management)
2. **Technical Barriers**: Complex backend setup and API knowledge required for AI generation
3. **No Resource Management**: Manual VRAM monitoring leads to crashes and failed generations
4. **Poor User Experience**: Context switching between applications breaks creative flow
5. **Inconsistent Results**: Lack of automated asset management leads to style/character inconsistencies

### Pain Points in Existing Blender Workflows
- **No AI Integration**: Blender has powerful 3D capabilities but zero native AI generation support
- **Manual Asset Management**: Artists manually import/organize generated content
- **Complex Setup**: Current AI tools require technical expertise to configure and operate
- **Resource Conflicts**: Multiple AI models competing for limited VRAM cause system instability

### Gaps in Agent-Based Film Creation Pipeline
- **Non-Functional Agents**: Current agent framework lacks backend execution capabilities
- **Missing Orchestration**: No actual workflow coordination between specialized agents
- **Template Isolation**: Workflow templates exist but cannot be executed
- **Status Blindness**: UI shows placeholder status without real progress tracking

---

## Solution Overview

### Feature Description within BMAD Agent Framework
The Backend Integration Service Layer implements a robust, async-first architecture that enables the Producer agent to orchestrate complex generative workflows across multiple AI backends. This service layer acts as the "nervous system" of the generative film studio, coordinating between the Blender UI, specialized film crew agents, and external AI services.

**Core Components:**
1. **Unified API Client Manager** - Abstracted interfaces for ComfyUI, Wan2GP, and LiteLLM
2. **Workflow Execution Engine** - Template-driven, parameter-injection workflow runner
3. **VRAM Budget Manager** - Intelligent resource allocation and model lifecycle management
4. **Task Queue System** - Async job management with progress tracking and error recovery
5. **File Management Service** - Generated asset organization and Blender integration

### Integration with Existing Film Crew Agents
- **Screenwriter Agent**: Uses LiteLLM client for script development and analysis
- **Casting Director Agent**: Leverages ComfyUI workflows for character consistency and LoRA training
- **Cinematographer Agent**: Orchestrates video generation across ComfyUI and Wan2GP backends
- **Sound Designer Agent**: Integrates RVC voice synthesis, AudioLDM sound effects, and music generation APIs
- **Art Director Agent**: Coordinates with style consistency framework for visual coherence
- **Environment Director Agent**: Manages environment generation and multi-angle consistency
- **Editor Agent**: Manages final assembly and imports generated content into Blender VSE

### Backend Service Requirements
- **ComfyUI Server**: WebSocket client for complex image/video workflow execution and LoRA training
- **Wan2GP Server**: Gradio client integration for fast video preview generation and CausVid models
- **LiteLLM Server**: OpenAI-compatible client for text generation and script analysis with local models
- **RVC Integration**: Voice cloning and character dialogue generation
- **AudioLDM Integration**: Sound effect and ambient audio generation
- **Health Monitoring**: Continuous service availability checking and automatic reconnection
- **Load Balancing**: Intelligent routing based on system capabilities and task requirements

---

## User Stories & Acceptance Criteria

### Epic 1: Basic Backend Connectivity
**As a filmmaker using Blender Movie Director, I want the addon to automatically connect to my local AI services so that I can start creating content immediately without technical setup.**

#### User Story 1.1: Service Discovery and Connection
- **Given** I have ComfyUI, Wan2GP, and LiteLLM running locally
- **When** I load the Movie Director addon in Blender  
- **Then** the addon automatically discovers and connects to available services
- **And** displays connection status in the main panel
- **And** shows which AI capabilities are available

#### User Story 1.2: Health Monitoring and Recovery
- **Given** I'm working on a film project with active AI generation
- **When** a backend service becomes unavailable
- **Then** the addon detects the disconnection within 30 seconds
- **And** automatically attempts reconnection every 30 seconds
- **And** notifies me of service status changes
- **And** gracefully handles in-progress tasks

### Epic 2: Workflow Execution Engine
**As a content creator, I want to generate character images and videos by clicking buttons in Blender, without needing to understand the technical complexity of AI workflows.**

#### User Story 2.1: Character Generation with Multi-Tier Consistency
- **Given** I have created a character asset with reference images
- **When** I click "Generate Character Variations" 
- **Then** the system loads the appropriate ComfyUI workflow template based on consistency tier
- **And** injects character-specific parameters (reference image paths, descriptions, LoRA paths if available)
- **And** executes the workflow on the ComfyUI backend with optimal VRAM management
- **And** imports generated images back into Blender as assets with regenerative parameters
- **And** updates the character's asset browser preview and usage tracking

#### User Story 2.2: Integrated Shot Generation with Audio
- **Given** I have defined a shot with dialogue, camera notes, and linked characters/environments
- **When** I click "Generate Shot"
- **Then** the system selects optimal backend (ComfyUI vs Wan2GP) based on complexity and character/style requirements
- **And** loads appropriate video generation workflow with character LoRAs, style parameters, and environment context
- **And** generates dialogue audio using character-specific RVC voice models
- **And** executes coordinated video and audio generation with real-time progress updates
- **And** imports final video clip and synchronized audio into Blender VSE at correct timeline position

### Epic 3: Resource Management
**As a user with limited VRAM, I want the system to automatically manage AI model loading/unloading so that I can run complex workflows without crashes.**

#### User Story 3.1: VRAM Budget Management
- **Given** I'm attempting to generate content that requires more VRAM than available
- **When** the system calculates resource requirements
- **Then** it automatically breaks the workflow into sequential steps
- **And** loads only required models for each step
- **And** unloads models between steps to free memory
- **And** provides clear feedback about memory optimization steps taken

#### User Story 3.2: Intelligent Backend Selection
- **Given** I request video generation for a shot
- **When** the system has multiple backend options available
- **Then** it selects the optimal backend based on:
  - Available VRAM vs model requirements
  - Desired quality level (draft vs final)
  - Character/style consistency needs
  - Estimated processing time
- **And** provides rationale for backend selection in progress panel

### Epic 4: Audio Integration and Coordination
**As a filmmaker, I want audio generation to be seamlessly integrated with video generation so that I can create complete audiovisual content without manual synchronization.**

#### User Story 4.1: Character Voice Generation
- **Given** I have a character with dialogue in a shot
- **When** the shot generation includes voice requirements
- **Then** the system automatically generates character dialogue using RVC voice models
- **And** synchronizes voice generation with video generation timing
- **And** imports audio tracks with proper character attribution and scene linkage
- **And** maintains voice consistency across all character appearances

#### User Story 4.2: Music and Sound Effects Integration
- **Given** I have scenes requiring background music or sound effects
- **When** I generate scene content with audio requirements
- **Then** the system generates appropriate music using scene mood and style context
- **And** creates sound effects based on scene action descriptions
- **And** coordinates audio generation with visual content for proper timing
- **And** organizes all audio assets with scene usage tracking and cross-references

---

## Technical Requirements

### Blender Addon Architecture Constraints

#### 1. Threading and Async Operations
- **Requirement**: All backend operations must be non-blocking to Blender UI
- **Implementation**: Use `threading.Thread` for API calls with `queue.Queue` for result handling
- **Constraint**: Blender's operator system requires main thread updates for UI refresh
- **Solution**: Implement timer-based polling for progress updates using `bpy.app.timers`

#### 2. Python Environment Integration
- **Requirement**: Backend clients must work within Blender's Python environment
- **Dependencies**: `requests`, `websocket-client`, `gradio_client`, `pyyaml`
- **Constraint**: Avoid dependencies that conflict with Blender's built-in packages
- **Installation**: Provide automated dependency installation for common platforms

#### 3. File Path Management and Regenerative Content Model
- **Requirement**: Handle both absolute and relative paths for cross-platform compatibility
- **Integration**: Use Blender's `bpy.path` utilities for path resolution
- **Storage**: Generated assets stored as file references only; all project definitions in .blend file
- **Regenerative Architecture**: Content can be regenerated from stored parameters at any time
- **Cleanup**: Implement automatic cleanup of temporary files on project close

### CrewAI Framework Integration

#### 1. Tool Integration Pattern
```python
@tool("Generate Video Clip")
def generate_video_clip_tool(prompt: str, character_refs: List[str], style_path: str) -> str:
    """Generate video clip using optimal backend selection"""
    backend = backend_service.select_optimal_backend(
        task_type="video_generation",
        complexity_score=calculate_complexity(prompt, character_refs)
    )
    
    workflow_template = template_engine.load_template(
        backend_type=backend.type,
        template_name="video_generation"
    )
    
    result = workflow_executor.execute_async(
        template=workflow_template,
        parameters={
            "video_prompt": prompt,
            "character_references": character_refs,
            "style_lora_path": style_path
        }
    )
    
    return result.video_path
```

#### 2. Agent-Backend Communication
- **Async Execution**: Agents submit tasks to backend queue and receive completion callbacks
- **Progress Tracking**: Real-time status updates propagated to UI panels
- **Error Handling**: Structured error responses with recovery suggestions
- **State Management**: Task state persisted in .blend file for session recovery

### Backend API Requirements

#### 1. ComfyUI Integration
- **WebSocket Client**: Real-time workflow execution and progress monitoring
- **Workflow Templates**: YAML-based templates with parameter injection
- **Model Management**: API calls for loading/unloading models based on VRAM availability
- **File Handling**: Direct integration with ComfyUI's output directory structure

#### 2. Wan2GP Integration  
- **Gradio Client**: HTTP-based API for fast video generation
- **Quality Presets**: Configurable quality/speed tradeoffs for different use cases
- **Batch Processing**: Support for multiple shots with consistent parameters
- **Format Handling**: Direct MP4 output compatible with Blender VSE

#### 3. LiteLLM Integration
- **OpenAI Compatibility**: Standard chat completion API for script development
- **Model Selection**: Automatic selection between available local models (Llama, GOAT-70B-Storytelling)
- **Context Management**: Maintain conversation context for iterative script development
- **Structured Output**: Support for JSON-formatted responses for data extraction

#### 4. Audio Service Integration
- **RVC Integration**: Character voice model training and dialogue generation
- **AudioLDM Integration**: Sound effect and ambient audio generation from text descriptions
- **Music Generation**: Scene-appropriate music composition with mood and style coordination
- **Audio Synchronization**: Timing coordination between audio and visual generation workflows

### Performance and Resource Considerations

#### 1. VRAM Management
- **Dynamic Profiling**: Runtime detection of available GPU memory
- **Model Footprint Database**: Pre-calculated VRAM requirements for all supported models
- **Sequential Execution**: Automatic workflow segmentation for memory-constrained systems
- **Optimization Strategies**: Model quantization and precision reduction when appropriate

#### 2. Storage Management and Regenerative Content Model
- **Generated Asset Organization**: Hierarchical directory structure by project/scene/shot
- **File Reference Storage**: Only file paths stored in .blend; content regenerated as needed
- **Temporary File Cleanup**: Automatic cleanup of intermediate generation files
- **Asset Caching**: Intelligent caching of frequently used character/style assets
- **Disk Space Monitoring**: Warnings when project storage approaches limits
- **Regenerative Architecture**: All content can be recreated from stored project definitions

#### 3. Network Optimization
- **Local-First Design**: All backends run locally to avoid network dependencies
- **Connection Pooling**: Efficient reuse of HTTP connections for API calls
- **Retry Logic**: Exponential backoff for transient network failures
- **Timeout Management**: Configurable timeouts based on operation complexity

---

## Success Metrics

### User Adoption within Blender Workflow
**Primary KPIs:**
- **Daily Active Users**: Target 500+ DAU within 6 months of release
- **Session Duration**: Average session >30 minutes indicating productive workflow
- **Feature Adoption Rate**: >80% of users complete end-to-end film generation within first week
- **Retention Rate**: 70% monthly active user retention after initial onboarding

**Measurement Methods:**
- Anonymous telemetry collection with user consent
- In-addon usage analytics (button clicks, feature usage, error rates)
- User survey feedback on workflow integration
- Community forum engagement and support requests

### Generative Content Quality Improvements
**Quality Metrics:**
- **Character Consistency Score**: >85% visual similarity across shots using same character
- **Style Coherence**: >90% of users rate final output as "stylistically consistent"
- **Technical Quality**: Generated videos meet broadcast standards (resolution, frame rate, compression)
- **Artistic Merit**: User satisfaction rating >4.0/5.0 for creative output quality

**Measurement Methods:**
- Automated computer vision analysis for character/style consistency
- User surveys rating output quality and artistic satisfaction
- Community showcase submissions and feedback
- Professional filmmaker evaluation panels

### Production Workflow Efficiency Gains
**Efficiency Metrics:**
- **Time to First Output**: Reduce concept-to-video time from 8+ hours to <30 minutes
- **Iteration Speed**: Enable >10 creative iterations per hour vs <2 with traditional tools
- **Setup Time**: <5 minutes from Blender startup to first generation vs >60 minutes traditional
- **Resource Utilization**: >90% uptime for backend services during active sessions

**Measurement Methods:**
- Time-based analytics tracking key workflow milestones
- User productivity surveys comparing pre/post adoption workflows
- System performance monitoring (uptime, response times, error rates)
- Cost analysis comparing traditional vs AI-assisted production methods

### Technical Performance Benchmarks
**System Performance:**
- **Response Time**: <3 seconds for workflow initiation, <30 seconds for simple generations
- **Reliability**: >99% uptime for backend integration layer
- **Resource Efficiency**: Optimal VRAM utilization with <5% waste on multi-model workflows
- **Error Rate**: <2% unrecoverable errors across all backend operations

**User Experience:**
- **Ease of Use**: >90% of new users complete tutorial without external help
- **Error Recovery**: Average error resolution time <2 minutes with guided recovery
- **Learning Curve**: Productive workflow achievement within <4 hours of first use
- **Documentation**: Support ticket resolution rate >95% using provided documentation

---

## Risk Assessment & Mitigation

### Technical Risks

#### High Risk: Backend Service Dependencies
- **Risk**: External AI services (ComfyUI, Wan2GP) may be unstable or incompatible
- **Probability**: Medium (40%)
- **Impact**: High - Core functionality unavailable
- **Mitigation Strategy**: 
  - Implement robust health checking and automatic recovery
  - Provide fallback mechanisms and graceful degradation
  - Develop comprehensive testing suite for backend compatibility
  - Create mock backends for development and testing

#### Medium Risk: VRAM Management Complexity
- **Risk**: Inaccurate VRAM profiling leads to crashes or poor performance
- **Probability**: Medium (30%)
- **Impact**: Medium - User frustration and workflow interruption
- **Mitigation Strategy**:
  - Extensive testing across different GPU configurations
  - Conservative memory estimates with safety margins
  - User-configurable memory limits and manual overrides
  - Clear error messages with resolution guidance

#### Medium Risk: Blender API Changes
- **Risk**: Future Blender updates break addon compatibility
- **Probability**: Low (15%)
- **Impact**: High - Addon becomes non-functional
- **Mitigation Strategy**:
  - Follow Blender development roadmap and test against beta releases
  - Use stable, well-documented Blender APIs
  - Implement version checking and compatibility warnings
  - Maintain backward compatibility for recent Blender versions

### Business Risks

#### High Risk: User Adoption Barriers
- **Risk**: Complex setup process prevents mainstream adoption
- **Probability**: Medium (35%)  
- **Impact**: High - Product fails to reach target market
- **Mitigation Strategy**:
  - Provide automated backend installation scripts
  - Create comprehensive video tutorials and documentation
  - Implement guided onboarding flow within addon
  - Partner with community for setup assistance and troubleshooting

#### Medium Risk: Performance Expectations
- **Risk**: Users expect faster generation times than technically possible
- **Probability**: High (50%)
- **Impact**: Medium - User dissatisfaction despite functional product
- **Mitigation Strategy**:
  - Set clear expectations about generation times in documentation
  - Provide real-time estimates and progress feedback
  - Offer multiple quality/speed tradeoff options
  - Educate users about hardware requirements and optimization

### Regulatory and Ethical Risks

#### Low Risk: AI Content Attribution
- **Risk**: Generated content attribution and licensing concerns
- **Probability**: Low (10%)
- **Impact**: Medium - Legal complications for commercial users
- **Mitigation Strategy**:
  - Clear documentation about AI-generated content rights
  - Metadata tracking of generation parameters and models used
  - User education about commercial use considerations
  - Legal disclaimer and user agreement

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Weeks 1-4)
*Foundation for PRD-002, PRD-003, PRD-004, and PRD-005*
**Deliverables:**
- Basic API client implementations for all backends (ComfyUI, Wan2GP, LiteLLM, RVC, AudioLDM)
- Health monitoring and connection management system with automatic service discovery
- Simple workflow template loading and parameter injection system
- Basic async task execution with progress callbacks and error handling
- Regenerative content model foundation with file reference storage

**Success Criteria:**
- Successfully connect to and communicate with all backend services
- Execute simple workflows (text generation, basic image generation)
- Handle connection failures gracefully with user notification

### Phase 2: Advanced Workflow Execution (Weeks 5-8)
*Enables PRD-002 script breakdown and PRD-005 environment generation workflows*  
**Deliverables:**
- Complete VRAM budgeting system with dynamic model management and multi-system coordination
- Complex workflow template support (multi-node ComfyUI workflows, character LoRA training)
- File management integration with Blender asset system and Asset Browser
- Comprehensive error handling and recovery mechanisms with user guidance
- Audio integration foundation with RVC and AudioLDM connectivity

**Success Criteria:**
- Execute complex character generation workflows without VRAM crashes
- Automatic import of generated assets into Blender with proper organization
- Robust error recovery with clear user guidance

### Phase 3: Full Agent Integration (Weeks 9-12)
*Supports PRD-003 character, PRD-004 style, and PRD-005 environment consistency*
**Deliverables:**
- Full CrewAI tool integration for all film crew agents with cross-system coordination
- UI integration with real-time progress updates and unified navigation framework
- Complete audio integration with character voice models and sound effect generation
- Cross-PRD workflow coordination for character-environment-style integration
- Performance optimization and intelligent caching across all systems

**Success Criteria:**
- End-to-end film generation workflow from script to final video with synchronized audio
- Sub-30 minute generation time for short film sequences with character, style, and environment consistency
- Professional-quality output suitable for broadcast television and commercial film production
- Seamless integration across all five PRD systems with unified user experience

### Phase 4: Production Polish and Community Integration (Weeks 13-16)
*Production-ready integration for all dependent PRDs (001-005)*
**Deliverables:**
- Comprehensive error handling and user guidance with context-aware recovery workflows
- Performance profiling and optimization for complex multi-system operations
- Complete user documentation and tutorial creation covering all integrated systems
- Community feedback integration and bug fixes with automated testing suite
- Professional workflow validation with industry standard compliance testing

**Success Criteria:**
- >95% workflow success rate in user testing across all integrated systems
- Documentation enables successful setup for 90% of target users without external support
- Performance meets all technical benchmarks outlined in success metrics for production use
- Professional quality validation with broadcast television standard compliance
- Complete regenerative content model implementation with version control compatibility

---

## Stakeholder Sign-Off

### Development Team Approval
- [ ] **Technical Lead** - Architecture and implementation feasibility confirmed
- [ ] **UI/UX Designer** - Integration approach preserves user experience quality  
- [ ] **QA Lead** - Testing strategy and acceptance criteria validated

### Business Stakeholder Approval  
- [ ] **Product Owner** - Business requirements and success metrics approved
- [ ] **Community Manager** - User adoption strategy and support model confirmed
- [ ] **Release Manager** - Implementation timeline and deliverables agreed upon

### Technical Review Board
- [ ] **Backend Architecture** - Service integration approach technically sound
- [ ] **Performance Engineering** - Resource management strategy validated
- [ ] **Security Review** - Local-first architecture security implications assessed

---

**Next Steps:**
1. Technical design document creation based on approved requirements
2. Development environment setup and dependency analysis  
3. Sprint planning and task breakdown for Phase 1 implementation
4. User research interviews to validate assumptions and refine user stories

---

## Cross-PRD Integration Specifications

### Complex Multi-System Workflows

#### Character-Environment-Style Coordination Workflow
- **Trigger**: Shot generation with character, environment, and style requirements
- **Systems Involved**: PRD-001 (Backend), PRD-003 (Character), PRD-004 (Style), PRD-005 (Environment)
- **Coordination Logic**: Backend service orchestrates sequential loading of character LoRA, style parameters, and environment context for unified generation
- **Error Handling**: Fallback to baseline consistency if resource constraints prevent full coordination
- **Performance Impact**: Additional 15-30% generation time for coordinated workflows

#### Scene-Wide Consistency Validation
- **Trigger**: Complete scene generation with multiple shots
- **Systems Involved**: All PRDs (001-005)
- **Process**: Automated cross-shot analysis for character, style, and environment consistency
- **Validation Metrics**: Character similarity >85%, style coherence >90%, environment continuity >80%
- **Remediation**: Automatic regeneration recommendations for inconsistent elements

### Resource Management Coordination

#### VRAM Arbitration for Multi-System Operations
- **Priority System**: Character LoRA (highest) > Style LoRA > Environment > Audio processing
- **Sequential Loading**: Dynamic model unloading/loading based on shot requirements
- **Memory Budgeting**: Real-time VRAM allocation across all active systems
- **User Feedback**: Clear indication of memory-based processing decisions

### UI Navigation Framework

#### Cross-System Navigation Pattern
- **Asset Browser Integration**: Unified asset browser showing characters, styles, environments with cross-references
- **Scene-Centric Navigation**: Scene properties panel with direct links to all related assets
- **Asset Usage Tracking**: "Used In" sections showing scene/shot relationships for each asset type
- **Quick Access Operators**: Context-sensitive buttons for asset creation and modification

#### Progress and Status Coordination
- **Unified Progress Panel**: Single panel showing all active backend operations across systems
- **Status Hierarchy**: System status > workflow status > individual task status
- **Error Consolidation**: Centralized error reporting with system-specific remediation
- **Resource Monitoring**: Real-time VRAM and processing status visible in main panel

### Coordinated Error Handling Strategy

#### Error Classification and Routing
- **Backend Connection Errors**: PRD-001 handles with automatic reconnection and user notification
- **Generation Failures**: Route to appropriate system (PRD-003/004/005) with context preservation
- **Resource Constraints**: VRAM management system provides optimization recommendations
- **User Input Errors**: Context-aware validation with system-specific error messages

#### Error Recovery Workflows
- **Graceful Degradation**: Automatic fallback to lower-fidelity options when high-fidelity fails
- **State Preservation**: All error states preserved for user review and manual intervention
- **Recovery Guidance**: Step-by-step recovery instructions with system-specific context
- **Learning Integration**: Error patterns used to improve future workflow optimization

---

*This PRD represents the foundational requirements for transforming Blender Movie Director from concept to functional generative film studio. Implementation of this Backend Integration Service Layer enables all subsequent agent functionality and unlocks the full potential of AI-assisted filmmaking within Blender.*