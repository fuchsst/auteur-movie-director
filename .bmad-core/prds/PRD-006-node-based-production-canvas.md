# Product Requirements Document: Node-Based Production Canvas

**Version:** 1.0  
**Date:** 2025-01-27  
**Owner:** BMAD Business Analyst  
**Status:** Draft - Stakeholder Review  
**PRD ID:** PRD-006  
**Dependencies:** Backend Integration Service Layer (PRD-001), Intelligent Script-to-Shot Breakdown System (PRD-002), Character Consistency Engine (PRD-003), Style Consistency Framework (PRD-004), Environment Management System (PRD-005)

---

## Executive Summary

### Business Justification
The Node-Based Production Canvas transforms the Blender Movie Director from a panel-driven interface into a visual, intuitive production environment that aligns with Blender's native workflow paradigms. This feature addresses the fundamental challenge of managing complex film production hierarchies by providing a visual graph representation of the entire filmmaking process, from high-level story structure down to individual shot generation.

By leveraging Blender's proven node-based interface paradigm, this system makes the complex relationships between story elements, assets, scenes, and shots immediately visible and manipulable. The visual nature of the canvas dramatically reduces the cognitive load of managing multi-layered film production workflows, enabling filmmakers to focus on creative decisions rather than organizational complexity.

The node canvas serves as the central nervous system of the regenerative content model, where all project definitions are visualized as nodes with connections, while generated content remains as file references that can be regenerated based on the node parameters at any time.

### Target User Personas
- **Visual Thinkers** - Artists who prefer node-based workflows over traditional interfaces
- **Complex Project Managers** - Filmmakers managing multi-scene productions with many assets
- **Technical Directors** - Users who need precise control over generation pipelines
- **3D Artists** - Blender users familiar with shader and geometry nodes
- **Pipeline TDs** - Technical artists building custom workflows
- **Educational Users** - Film schools teaching production pipeline concepts

### Expected Impact on Film Production Workflow
- **Visual Clarity**: Transform abstract production concepts into tangible, visual relationships
- **Workflow Flexibility**: Enable custom pipeline configurations without code modifications
- **3D Integration**: Bridge traditional 3D workflows with AI generation seamlessly
- **Production Scalability**: Manage complex multi-scene films through hierarchical organization
- **Pipeline Customization**: Allow technical users to create entirely new generative workflows

---

## Problem Statement

### Current Limitations in Generative Film Production
1. **Hidden Relationships**: Panel-based UIs obscure the connections between story elements, assets, and outputs
2. **Linear Workflows**: Traditional interfaces force sequential thinking in inherently non-linear creative processes
3. **Pipeline Rigidity**: Hard-coded workflows prevent customization for specific production needs
4. **3D Disconnect**: No integration between Blender's 3D capabilities and AI generation pipelines
5. **Complexity Management**: Large projects become unwieldy without visual organization tools

### Pain Points in Existing Blender Workflows
- **Interface Inconsistency**: Movie Director addon doesn't match Blender's node-based paradigms
- **No Pipeline Visualization**: Users can't see or modify the generation pipeline structure
- **Limited 3D Integration**: Can't use 3D renders as inputs for AI generation
- **No Custom Workflows**: Users stuck with predefined generation paths
- **Poor Scalability**: Panel interfaces become cluttered in complex projects

### Gaps in Agent-Based Film Creation Pipeline
- **No Visual Agent Orchestration**: Agent relationships and data flow invisible to users
- **Missing Pipeline Configuration**: Can't customize which agents process which data
- **No 3D-to-AI Bridge**: Agents can't leverage Blender's 3D rendering capabilities
- **Limited Modularity**: Can't swap or configure generation pipelines per shot
- **No Dependency Visualization**: Asset usage and relationships hidden from view

---

## Solution Overview

### Feature Description within BMAD Agent Framework
The Node-Based Production Canvas introduces a custom node editor within Blender that visualizes and controls the entire generative film production pipeline. This system represents each production element—from story concepts to individual shots—as nodes that can be connected, configured, and executed within a hierarchical graph structure.

**Core Components:**
1. **Hierarchical Node System** - Multi-level graphs supporting project → scene → shot navigation
2. **Production Node Types** - Specialized nodes for each production element (Character, Style, Environment, Shot, etc.)
3. **Blender Integration Nodes** - Direct connections to 3D renders, passes, and masks
4. **Pipeline Configuration** - Modular pipeline nodes pointing to ComfyUI/Wan2GP workflows
5. **Visual Asset Management** - Drag-and-drop asset nodes with relationship visualization
6. **Execution Control** - Generate buttons on nodes with progress visualization
7. **Dependency Tracking** - Visual representation of asset usage across production

### Integration with Existing Film Crew Agents

**Producer Agent Evolution:**
- Interprets node graph structure to orchestrate agent workflows
- Routes execution based on node connections rather than hard-coded logic
- Manages parallel execution of independent node branches
- Provides real-time progress updates directly on nodes

**Visual Agent Orchestration:**
- Each agent's role represented by specific node types and connections
- Data flow between agents visualized as node links
- Agent parameters exposed as node properties
- Pipeline customization through node configuration

**3D-to-AI Bridge:**
- Cinematographer agent receives depth passes, outlines, and masks from Blender nodes
- Art Director agent uses 3D renders for style reference
- Environment Director leverages 3D scenes for spatial consistency
- Character consistency enhanced with 3D pose references

### Backend Service Requirements

**Node System Integration:**
- Custom Blender node tree implementation with hierarchical support
- Asynchronous execution system for non-blocking node operations
- Real-time progress tracking and node state updates
- Pipeline template discovery and validation

**3D Render Pipeline:**
- Automatic render pass extraction (depth, normal, Cryptomatte)
- Custom shader setups for AI-friendly outputs (Canny edges, masks)
- Render result caching and format conversion
- Multi-layer EXR support for complex inputs

**Workflow Template Management:**
- Dynamic discovery of ComfyUI workflow templates
- Pipeline node validation against available backends
- Hot-swappable workflow configurations
- Custom workflow import/export system

---

## User Stories & Acceptance Criteria

### Epic 1: Visual Production Organization
**As a filmmaker, I want to see my entire film structure as a visual graph, so I can understand and manage the relationships between all production elements at a glance.**

#### User Story 1.1: Hierarchical Production Graph
- **Given** I have a multi-scene film project
- **When** I open the Production Canvas node editor
- **Then** I see a top-level graph showing project settings, scenes, and their connections
- **And** I can enter scene nodes to see their internal shot structure
- **And** navigation between levels is smooth and intuitive
- **And** the current context is always clear

**Acceptance Criteria:**
- Hierarchical node groups with Tab navigation
- Clear visual distinction between node levels
- Breadcrumb navigation showing current graph context
- Smooth transitions between graph levels

#### User Story 1.2: Asset Relationship Visualization
- **Given** I have characters, styles, and environments used across multiple shots
- **When** I select an asset in the Asset Manager
- **Then** all nodes using that asset are highlighted in the graph
- **And** I can trace dependencies visually
- **And** usage statistics are displayed
- **And** I can navigate directly to dependent nodes

**Acceptance Criteria:**
- Interactive highlighting system for asset dependencies
- Visual filtering to show only relevant connections
- Usage count badges on asset nodes
- Context menu navigation to dependent nodes

### Epic 2: 3D-to-AI Integration
**As a 3D artist, I want to use my Blender scenes as inputs for AI generation, so I can maintain precise control over composition while leveraging AI for details.**

#### User Story 2.1: Render Pass Integration
- **Given** I have a 3D scene with camera and lighting setup
- **When** I add a Blender Render Input node
- **Then** I can select which render pass to use (depth, normal, diffuse, etc.)
- **And** the pass is automatically rendered and provided to the AI pipeline
- **And** updates to the 3D scene trigger re-rendering
- **And** render settings are optimized for AI consumption

**Acceptance Criteria:**
- Support for all standard Blender render passes
- Automatic format conversion for AI compatibility
- Live preview of render pass in node
- Efficient caching to avoid redundant renders

#### User Story 2.2: Object Mask Generation
- **Given** I have specific objects I want to isolate for generation
- **When** I add an Object Mask Input node
- **Then** I can select objects or collections to mask
- **And** appropriate masks are generated using Cryptomatte or custom shaders
- **And** masks can be used for inpainting or layer separation
- **And** mask preview shows exactly what will be provided to AI

**Acceptance Criteria:**
- Multiple mask generation methods (Cryptomatte, ID pass, custom shader)
- Real-time mask preview in node interface
- Support for animated masks across frame ranges
- Clean black/white output suitable for AI masking

### Epic 3: Modular Pipeline Configuration
**As a technical director, I want to configure custom generation pipelines, so I can optimize workflows for specific production needs.**

#### User Story 3.1: Pipeline Node System
- **Given** I have specific ComfyUI workflows for different generation needs
- **When** I add a Pipeline node to the canvas
- **Then** I can point it to a specific workflow JSON file
- **And** the node validates compatibility with connected inputs
- **And** I can swap pipelines without rewiring the graph
- **And** pipeline parameters are exposed as node properties

**Acceptance Criteria:**
- Dynamic pipeline discovery from template directory
- Validation of input/output compatibility
- Hot-swappable pipeline configurations
- Parameter exposure with appropriate UI controls

#### User Story 3.2: Custom Workflow Creation
- **Given** I have created a new ComfyUI workflow
- **When** I export it and add it to the template library
- **Then** it becomes available as a Pipeline node option
- **And** the system automatically detects required inputs
- **And** I can use it immediately in my production
- **And** it integrates with existing asset management

**Acceptance Criteria:**
- Automatic workflow template discovery
- Input/output requirement detection
- Seamless integration with existing nodes
- Validation and error reporting for incompatible workflows

### Epic 4: Interactive Generation Control
**As a director, I want to control generation directly from the node graph, so I can iterate quickly while maintaining visual context.**

#### User Story 4.1: Node-Based Generation
- **Given** I have configured a Shot node with all inputs
- **When** I click the Generate button on the node
- **Then** generation begins with real-time progress display
- **And** the node shows current processing stage
- **And** I can cancel if needed
- **And** results are automatically connected when complete

**Acceptance Criteria:**
- Generate buttons directly on executable nodes
- Real-time progress indication (percentage, stage)
- Graceful cancellation without losing work
- Automatic result integration into graph

#### User Story 4.2: Parallel Execution Management
- **Given** I have multiple independent shots ready to generate
- **When** I select multiple Shot nodes and initiate generation
- **Then** the system intelligently manages parallel execution
- **And** VRAM usage is optimized across jobs
- **And** progress is shown for each parallel task
- **And** failures don't affect other jobs

**Acceptance Criteria:**
- Multi-selection generation support
- Intelligent VRAM-aware job scheduling
- Individual progress tracking per node
- Isolated error handling per generation

---

## Technical Requirements

### Blender Addon Architecture Constraints

#### 1. Custom Node Tree Implementation
```python
class MovieDirectorNodeTree(NodeTree):
    """The production canvas node tree"""
    bl_idname = 'MovieDirectorNodeTree'
    bl_label = "Movie Director Production Canvas"
    bl_icon = 'SEQUENCE'
    
    def update(self):
        """Handle node graph updates and validation"""
        self.validate_connections()
        self.update_execution_order()
        self.propagate_style_context()

class MovieDirectorNodeCategory(NodeCategory):
    """Organizes nodes into logical categories"""
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'MovieDirectorNodeTree'

# Node Categories
node_categories = [
    MovieDirectorNodeCategory("INPUTS", "Inputs", items=[
        NodeItem("MovieDirectorProjectSettingsNode"),
        NodeItem("MovieDirectorAssetNode"),
        NodeItem("MovieDirectorBlenderRenderNode"),
        NodeItem("MovieDirectorObjectMaskNode"),
    ]),
    MovieDirectorNodeCategory("PRODUCTION", "Production", items=[
        NodeItem("MovieDirectorSceneGroupNode"),
        NodeItem("MovieDirectorShotNode"),
        NodeItem("MovieDirectorCharacterNode"),
        NodeItem("MovieDirectorEnvironmentNode"),
    ]),
    MovieDirectorNodeCategory("PIPELINE", "Pipeline", items=[
        NodeItem("MovieDirectorPipelineNode"),
        NodeItem("MovieDirectorSequenceNode"),
        NodeItem("MovieDirectorFinalOutputNode"),
    ]),
]
```

#### 2. Hierarchical Node Groups
```python
class MovieDirectorSceneGroupNode(NodeCustomGroup):
    """Scene container supporting nested shot graphs"""
    bl_idname = 'MovieDirectorSceneGroupNode'
    bl_label = "Scene"
    
    def init(self, context):
        self.node_tree = bpy.data.node_groups.new(
            name=f"Scene_{self.name}", 
            type='MovieDirectorNodeTree'
        )
        
        # Create group inputs/outputs
        self.add_socket('MovieDirectorLocationSocket', 'Location', 'INPUT')
        self.add_socket('MovieDirectorStyleSocket', 'Style', 'INPUT')
        self.add_socket('MovieDirectorSequenceSocket', 'Sequence', 'OUTPUT')
    
    def free(self):
        """Clean up nested node tree on deletion"""
        if self.node_tree:
            bpy.data.node_groups.remove(self.node_tree)
```

#### 3. Custom Socket Types
```python
class MovieDirectorAssetSocket(NodeSocket):
    """Socket for passing asset references"""
    bl_idname = 'MovieDirectorAssetSocket'
    bl_label = "Asset"
    
    asset_type: EnumProperty(
        items=[
            ('CHARACTER', "Character", "Character asset"),
            ('STYLE', "Style", "Style asset"),
            ('ENVIRONMENT', "Environment", "Environment asset"),
        ]
    )
    
    def draw(self, context, layout, node, text):
        layout.label(text=text)
    
    def draw_color(self, context, node):
        return (0.8, 0.4, 0.2, 1.0)  # Orange for assets

class MovieDirectorPipelineSocket(NodeSocket):
    """Socket for pipeline configurations"""
    bl_idname = 'MovieDirectorPipelineSocket'
    bl_label = "Pipeline"
    
    def draw_color(self, context, node):
        return (0.2, 0.8, 0.2, 1.0)  # Green for pipelines
```

### CrewAI Framework Integration

#### 1. Node-Driven Agent Orchestration
```python
class NodeGraphOrchestrator:
    """Interprets node graphs to orchestrate agent workflows"""
    
    def __init__(self, producer_agent):
        self.producer = producer_agent
        self.execution_queue = []
        self.node_state_map = {}
    
    def analyze_graph(self, node_tree):
        """Convert node graph to executable workflow"""
        # Topological sort for execution order
        execution_order = self.topological_sort(node_tree)
        
        # Build execution plan
        for node in execution_order:
            if self.is_executable_node(node):
                task = self.create_agent_task(node)
                self.execution_queue.append(task)
        
        return self.execution_queue
    
    def create_agent_task(self, node):
        """Convert node configuration to agent task"""
        if node.bl_idname == 'MovieDirectorShotNode':
            return self.create_shot_generation_task(node)
        elif node.bl_idname == 'MovieDirectorCharacterNode':
            return self.create_character_task(node)
        # ... other node types
    
    def execute_node_async(self, node, callback):
        """Execute node with async progress tracking"""
        task = self.create_agent_task(node)
        
        # Start execution in thread
        thread = threading.Thread(
            target=self._execute_with_callback,
            args=(task, node, callback)
        )
        thread.start()
```

#### 2. 3D-to-AI Bridge Implementation
```python
@tool("Extract Blender Render Pass")
def extract_render_pass_tool(
    scene_name: str, 
    camera_name: str, 
    pass_type: str,
    frame: int = None
) -> str:
    """Extract specific render pass for AI consumption"""
    
    # Set up render settings
    scene = bpy.data.scenes[scene_name]
    camera = bpy.data.objects[camera_name]
    
    original_camera = scene.camera
    scene.camera = camera
    
    if frame is not None:
        scene.frame_set(frame)
    
    # Configure pass output
    if pass_type == 'depth':
        scene.view_layers[0].use_pass_z = True
    elif pass_type == 'normal':
        scene.view_layers[0].use_pass_normal = True
    elif pass_type == 'cryptomatte':
        scene.view_layers[0].use_pass_cryptomatte_object = True
    
    # Render to temporary file
    temp_path = get_temp_render_path(pass_type)
    scene.render.filepath = temp_path
    bpy.ops.render.render(write_still=True)
    
    # Convert to AI-friendly format
    processed_path = process_render_for_ai(temp_path, pass_type)
    
    # Restore settings
    scene.camera = original_camera
    
    return processed_path
```

### Performance and Resource Considerations

#### 1. Node Graph Optimization
- **Lazy Evaluation**: Only execute nodes when outputs are needed
- **Caching Strategy**: Cache intermediate results to avoid redundant computation
- **Progress Streaming**: Use WebSocket for real-time progress updates
- **Parallel Execution**: Analyze graph for independent branches that can run simultaneously

#### 2. 3D Render Optimization
- **Viewport Render**: Use viewport render for quick previews
- **Resolution Scaling**: Automatically adjust render resolution for AI inputs
- **Pass Combination**: Render multiple passes in single operation when possible
- **Format Optimization**: Convert renders to optimal formats for AI processing

#### 3. Memory Management
- **Node State Persistence**: Store node states in .blend file for session recovery
- **Selective Loading**: Only load node trees that are actively being edited
- **Result Streaming**: Stream large results directly to disk rather than memory
- **Cleanup Policies**: Automatic cleanup of temporary renders and cached results

---

## Success Metrics

### User Adoption and Workflow Enhancement
**Primary KPIs:**
- **Node Canvas Adoption**: >70% of users prefer node interface over panels within 3 months
- **Workflow Efficiency**: 40% reduction in time to set up complex multi-scene projects
- **3D Integration Usage**: >50% of advanced users utilize 3D-to-AI features
- **Custom Pipeline Creation**: >100 community-shared pipeline templates within 6 months

**Measurement Methods:**
- Usage analytics comparing node vs panel interface time
- User surveys on workflow preference and efficiency
- Community template repository metrics
- Time-motion studies of production setup tasks

### Visual Clarity and Understanding
**Comprehension Metrics:**
- **Relationship Understanding**: 90% of users correctly identify asset dependencies in testing
- **Navigation Efficiency**: <5 seconds average to locate specific production elements
- **Error Reduction**: 60% fewer configuration errors compared to panel interface
- **Learning Curve**: New users productive within 2 hours of node interface training

**Measurement Methods:**
- User testing with relationship identification tasks
- Navigation timing studies across different project sizes
- Error rate comparison between interfaces
- New user onboarding success metrics

### Technical Integration Success
**Integration Metrics:**
- **3D Pass Success Rate**: >95% successful render pass extraction and AI integration
- **Pipeline Flexibility**: Average 3.5 different pipelines used per production
- **Parallel Execution**: 2.5x throughput improvement with parallel node execution
- **Custom Workflow Adoption**: 40% of power users create custom pipelines

**Measurement Methods:**
- Automated testing of render pass extraction
- Pipeline usage analytics and diversity metrics
- Performance benchmarking of parallel execution
- Custom workflow creation and sharing statistics

---

## Risk Assessment & Mitigation

### Technical Risks

#### High Risk: Node System Complexity
- **Risk**: Custom node system becomes too complex for average users
- **Probability**: Medium (40%)
- **Impact**: High - Feature rejection by target audience
- **Mitigation Strategy**:
  - Provide preset node templates for common workflows
  - Progressive disclosure of advanced features
  - Comprehensive interactive tutorials
  - "Simple mode" with reduced node types

#### Medium Risk: 3D Integration Performance
- **Risk**: Render pass extraction slows down generation workflow
- **Probability**: Medium (35%)
- **Impact**: Medium - Workflow efficiency compromised
- **Mitigation Strategy**:
  - Implement aggressive render caching
  - Viewport render options for quick iterations
  - Background rendering during other operations
  - Resolution optimization for AI inputs

### User Experience Risks

#### Medium Risk: Learning Curve Barrier
- **Risk**: Users familiar with panel interfaces struggle with nodes
- **Probability**: High (50%)
- **Impact**: Medium - Slower adoption rate
- **Mitigation Strategy**:
  - Maintain panel interface as alternative
  - Gradual migration path from panels to nodes
  - Video tutorials showing benefits
  - Community showcases of node workflows

#### Low Risk: Graph Complexity Management
- **Risk**: Large productions create unwieldy node graphs
- **Probability**: Low (25%)
- **Impact**: Medium - Reduced usability at scale
- **Mitigation Strategy**:
  - Node grouping and organization tools
  - Graph complexity analysis and warnings
  - Auto-layout algorithms
  - Frame and annotation features

---

## Implementation Roadmap

### Phase 1: Core Node System (Weeks 1-4)
*Foundation for all node-based features*
**Deliverables:**
- Basic custom node tree implementation
- Core node types (Project, Asset, Shot, Scene)
- Node categories and organization
- Basic execution framework

**Success Criteria:**
- Node editor opens and supports basic operations
- Nodes can be created, connected, and configured
- Node state persists in .blend file
- Basic visual hierarchy established

### Phase 2: Hierarchical Navigation and Asset Integration (Weeks 5-8)
*Enables complex production organization*
**Deliverables:**
- Scene group nodes with nested graphs
- Asset node integration with Asset Browser
- Dependency visualization system
- Navigation tools and breadcrumbs

**Success Criteria:**
- Smooth navigation between graph levels
- Asset relationships clearly visualized
- Drag-and-drop from Asset Browser works
- Context always clear to user

### Phase 3: 3D-to-AI Bridge (Weeks 9-12)
*Unlocks advanced creative workflows*
**Deliverables:**
- Blender Render Input nodes
- Object Mask generation nodes
- Render pass optimization
- AI format conversion

**Success Criteria:**
- All major render passes extractable
- Masks generated accurately
- Performance acceptable for iteration
- Results improve AI generation quality

### Phase 4: Pipeline Configuration and Execution (Weeks 13-16)
*Enables full production flexibility*
**Deliverables:**
- Pipeline node system
- Workflow template discovery
- Parallel execution management
- Progress visualization

**Success Criteria:**
- Custom workflows easily integrated
- Parallel execution improves throughput
- Progress clearly communicated
- System remains stable under load

---

## Cross-PRD Integration Specifications

### Script Import to Node Graph
- **Integration**: PRD-002 → PRD-006
- **Process**: Script breakdown automatically creates scene/shot node structure
- **User Experience**: After script import, node graph is pre-populated and organized
- **Technical**: Script parser generates node tree with proper connections

### Asset Nodes and Management
- **Integration**: PRD-003/004/005 → PRD-006
- **Process**: Asset creation in managers automatically creates corresponding nodes
- **Visualization**: Asset nodes show preview images and usage statistics
- **Interaction**: Double-click asset node to open asset properties

### Backend Execution via Nodes
- **Integration**: PRD-006 → PRD-001
- **Process**: Node execution triggers backend API calls through Producer agent
- **Monitoring**: Real-time progress updates flow back to node display
- **Error Handling**: Node states reflect backend errors with clear messaging

### VRAM-Aware Execution
- **Integration**: PRD-006 → PRD-008
- **Process**: Node execution order optimized based on VRAM requirements
- **Visualization**: Nodes show estimated VRAM usage
- **Scheduling**: Parallel execution limited by available VRAM

---

## Stakeholder Sign-Off

### Development Team Approval
- [ ] **Technical Lead** - Node system architecture and implementation plan approved
- [ ] **UI/UX Designer** - Node interface design and user experience validated
- [ ] **Backend Integration Specialist** - 3D-to-AI bridge technically feasible

### Business Stakeholder Approval
- [ ] **Product Owner** - Feature aligns with product vision and user needs
- [ ] **Community Manager** - Node interface attractive to Blender community
- [ ] **Training Lead** - Educational materials plan comprehensive

### User Representative Review
- [ ] **Power User Representative** - Advanced features meet professional needs
- [ ] **New User Representative** - Learning curve acceptable with support materials
- [ ] **3D Artist Representative** - 3D integration features valuable and usable

---

**Next Steps:**
1. Create detailed technical design for custom node tree implementation
2. Design UI mockups for all node types and interactions
3. Develop prototype with core node types for user testing
4. Create comprehensive tutorial plan for node-based workflows

---

*This PRD establishes the Node-Based Production Canvas as the visual control center that transforms Blender Movie Director from a traditional addon into a powerful, flexible, and intuitive generative film production environment that fully embraces Blender's node-based paradigm.*