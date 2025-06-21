# Blender Movie Director - Addon Architecture

## Architecture Overview
The Blender Movie Director addon follows a three-tier architecture designed for optimal integration with Blender while maintaining separation of concerns and modularity.

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Layer (Blender Native)               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │   Panels    │ │  Operators  │ │ Properties  │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Orchestration Layer (CrewAI Agents)          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  Producer   │ │Cinematographer│ │Sound Designer│          │
│  │   Agent     │ │    Agent    │ │    Agent    │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              Backend Layer (Generative Engines)             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │   ComfyUI   │ │   Wan2GP    │ │  LiteLLM    │            │
│  │   Server    │ │   Server    │ │   Server    │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure
```
blender_movie_director/
├── __init__.py                 # Main addon registration
├── ui/                         # Blender UI components
│   ├── __init__.py
│   ├── panels.py              # UI panels for 3D Viewport sidebar
│   ├── operators.py           # Blender operators for user actions
│   └── properties.py          # Custom properties and data structures
├── agents/                     # CrewAI film crew agents
│   ├── __init__.py
│   ├── base_agent.py          # Base agent class with common functionality
│   ├── producer.py            # Producer agent (master orchestrator)
│   ├── screenwriter.py        # Script development agent
│   ├── casting_director.py    # Character asset management agent
│   ├── art_director.py        # Style management agent
│   ├── cinematographer.py     # Video generation agent
│   ├── sound_designer.py      # Audio generation agent
│   └── editor.py              # Post-production assembly agent
├── backend/                    # API clients for generative engines
│   ├── __init__.py
│   ├── comfyui_client.py      # ComfyUI API client and workflow management
│   ├── wan2gp_client.py       # Wan2GP gradio client integration
│   ├── litellm_client.py      # LiteLLM server client for LLM operations
│   └── vram_manager.py        # VRAM budgeting and resource management
├── workflows/                  # Workflow templates and configurations
│   ├── comfyui/               # ComfyUI workflow JSON templates
│   │   ├── character_generation.json
│   │   ├── video_generation.json
│   │   └── style_transfer.json
│   ├── wan2gp/                # Wan2GP configuration templates
│   │   ├── quick_preview.json
│   │   └── high_quality.json
│   └── vram_profiles.json     # Model VRAM requirement profiles
├── config/                     # Configuration and settings
│   ├── default_settings.json
│   └── backend_configs.json
└── utils/                      # Utility functions and helpers
    ├── __init__.py
    ├── asset_manager.py       # Generative asset data model management
    ├── blender_integration.py # Blender-specific utility functions
    └── file_manager.py        # File handling and path management
```

## Core Components

### 1. UI Layer (Blender Native)
**Purpose:** Provide native Blender interface integration  
**Technologies:** bpy (Blender Python API), Blender UI system  
**Key Files:** `ui/panels.py`, `ui/operators.py`, `ui/properties.py`

#### Panels
- Main Movie Director panel in 3D Viewport sidebar
- Hierarchical panel structure for different production phases
- Context-sensitive UI that adapts to current project state

#### Operators
- User-triggered actions (button clicks, menu selections)
- Async operations that don't block the UI
- Progress reporting and error handling

#### Properties
- Custom properties stored in scene/object data
- Property groups for complex data structures
- Update callbacks for reactive UI behavior

### 2. Orchestration Layer (CrewAI Agents)
**Purpose:** AI agent coordination and workflow management  
**Technologies:** CrewAI, Python asyncio  
**Key Files:** `agents/*.py`

#### Producer Agent (Master Orchestrator)
```python
class ProducerAgent:
    """Master orchestrator managing entire production pipeline"""
    responsibilities = [
        "Project state management",
        "Resource allocation and VRAM budgeting", 
        "Workflow coordination between agents",
        "Error recovery and fallback strategies"
    ]
```

#### Specialized Film Crew Agents
- **Screenwriter:** Script development, scene breakdown, character extraction
- **Casting Director:** Character asset creation, LoRA training, reference management
- **Art Director:** Style definition, style model training, consistency enforcement
- **Cinematographer:** Video generation, camera control, visual effects
- **Sound Designer:** Voice cloning, sound effects, audio synchronization
- **Editor:** Post-production assembly, quality enhancement, export

### 3. Backend Layer (Generative Engines)
**Purpose:** Interface with external generative AI services  
**Technologies:** HTTP APIs, asyncio, gradio_client  
**Key Files:** `backend/*.py`

#### ComfyUI Integration
```python
class ComfyUIClient:
    """Client for ComfyUI workflow execution"""
    features = [
        "Workflow template management",
        "Dynamic parameter injection",
        "Progress monitoring and result retrieval",
        "Model loading and memory management"
    ]
```

#### Wan2GP Integration
- Gradio client for specialized video generation
- Configuration template system
- Resource-aware task routing

#### LiteLLM Integration
- Local LLM server communication
- Text generation for script development
- Context management and conversation state

## Data Architecture

### Generative Asset Data Model
```python
# Stored as Blender custom properties
class GenerativeAsset:
    """Base class for all generative assets"""
    
class Character(GenerativeAsset):
    name: str
    description: str
    reference_images: List[str]
    lora_model_path: str
    voice_model_path: str

class Style(GenerativeAsset):
    name: str
    description: str
    reference_images: List[str]
    style_lora_path: str

class Scene(GenerativeAsset):
    name: str
    script_content: str
    shots: List[Shot]
    location: Location

class Shot(GenerativeAsset):
    shot_number: int
    dialogue: str
    action_description: str
    camera_notes: str
    characters: List[Character]
    style: Style
    video_path: str
    audio_path: str
```

### State Management
- Project state stored in .blend file custom properties
- Asset relationships maintained through Blender's data structure
- Atomic operations with proper undo/redo support

## Resource Management Architecture

### VRAM Budgeting System
```python
class VRAMManager:
    """Dynamic VRAM budgeting and model management"""
    
    def check_workflow_feasibility(self, workflow):
        """Validate if workflow can execute within VRAM limits"""
        
    def execute_sequential_loading(self, workflow):
        """Load models sequentially if parallel loading exceeds VRAM"""
        
    def monitor_usage(self):
        """Real-time VRAM usage monitoring"""
```

### Performance Optimization Patterns
- Lazy loading of heavy components
- Model caching and intelligent unloading  
- Background processing with progress reporting
- Efficient Python patterns (avoid try/except in loops)

## Error Handling Strategy

### Graceful Degradation
```python
class ErrorRecoverySystem:
    """Comprehensive error handling and recovery"""
    
    strategies = [
        "Backend unavailability fallbacks",
        "Resource exhaustion recovery",
        "Model loading failure handling",
        "Network connectivity issues"
    ]
```

### User Communication
- Clear error messages with actionable solutions
- Progress indicators for long-running operations
- Status reporting in Blender's UI

## Integration Patterns

### Blender Best Practices
- Proper bl_info metadata and registration
- Self-contained deployment with bundled dependencies
- Use of `bpy.utils.extension_path_user` for user data
- Respect for `bpy.app.online_access` setting

### CrewAI Integration
- Agent specialization mapped to film production roles
- Task-based workflow decomposition
- Tool integration for backend communication
- State preservation across agent interactions

### Backend Communication
- Async API calls to prevent UI blocking
- Robust error handling and retry mechanisms
- Workflow template parameterization
- Resource-aware task scheduling

## Security Considerations
- Local-first operation minimizes data exposure
- Sandboxed execution of generative workflows
- Secure file handling and path validation
- No credential storage in addon code

## Scalability Architecture
- Modular agent system allows easy addition of new capabilities
- Plugin architecture for custom workflow templates
- Configurable resource limits for different hardware tiers
- Future-ready for cloud processing integration

## Testing Architecture
- Unit tests for individual components
- Integration tests for agent coordination
- Performance tests for resource management
- UI tests for Blender integration
- End-to-end tests for complete workflows