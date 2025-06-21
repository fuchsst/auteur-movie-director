# Blender Addon Development Stack Preferences

## Development Environment

### Primary Technology Stack
- **Core Platform**: Blender 4.0+ with Python 3.11+
- **UI Framework**: Native Blender bpy.types (Panel, Operator, Property)
- **AI Orchestration**: CrewAI framework for multi-agent coordination
- **Backend Communication**: asyncio + requests for API clients
- **Data Management**: Blender scene custom properties with JSON serialization

### Development Tools
- **IDE**: VS Code with Python and Blender development extensions
- **Debugging**: Blender's built-in Python console and external debugger attachment
- **Version Control**: Git with conventional commits for clear change tracking
- **Testing**: pytest for unit tests, manual testing for UI/UX validation
- **Documentation**: Markdown with embedded code examples

## Backend Integration Stack

### Generative AI Backends
- **ComfyUI**: Primary backend for complex image/video workflows
  - API: HTTP REST API with JSON workflow definitions
  - Communication: Async HTTP client with progress monitoring
  - Workflow Management: Template-based with parameter injection
  
- **Wan2GP**: Secondary backend for specialized video generation
  - API: Gradio client for Python integration
  - Communication: gradio_client library with async wrappers
  - Configuration: JSON-based configuration templates

- **LiteLLM**: Local LLM server for text generation
  - API: OpenAI-compatible REST API
  - Communication: litellm Python client
  - Models: Local deployment (Llama 3, specialized fine-tunes)

### Resource Management
- **VRAM Monitoring**: GPU-ML or similar library for real-time monitoring
- **Model Management**: Custom model loading/unloading with memory tracking
- **Performance Profiling**: Python cProfile with custom metrics
- **Error Handling**: Structured exception handling with user-friendly messages

## Code Organization Preferences

### Project Structure
```
blender_movie_director/
├── __init__.py                 # Addon registration and metadata
├── ui/                         # All Blender UI components
│   ├── panels.py              # UI panels for different workflows
│   ├── operators.py           # User-triggered actions
│   └── properties.py          # Custom data properties
├── agents/                     # CrewAI film crew agents
│   ├── base_agent.py          # Common agent functionality
│   └── [specialized agents]   # Film crew role implementations
├── backend/                    # External service integration
│   ├── base_client.py         # Common API client patterns
│   └── [service clients]      # ComfyUI, Wan2GP, LiteLLM clients
├── workflows/                  # Generative workflow templates
│   ├── comfyui/              # ComfyUI workflow JSON files
│   └── wan2gp/               # Wan2GP configuration files
├── utils/                      # Shared utility functions
│   ├── blender_helpers.py     # Blender-specific utilities
│   ├── vram_manager.py        # Resource management
│   └── file_manager.py        # File operations
└── config/                     # Configuration and settings
    ├── default_settings.json
    └── vram_profiles.json
```

### Coding Standards
- **Python Style**: Follow PEP 8 with 88-character line limit (Black formatter)
- **Naming Conventions**: snake_case for functions/variables, PascalCase for classes
- **Documentation**: Google-style docstrings with type hints
- **Error Handling**: Specific exceptions with clear error messages
- **Async Patterns**: async/await for all I/O operations

## Blender-Specific Preferences

### UI Development Patterns
- **Panel Hierarchy**: Logical grouping with collapsible sections
- **Property Groups**: Custom property groups for complex data structures
- **Operator Design**: Single responsibility with clear success/failure states
- **Icon Usage**: Consistent with Blender's icon system
- **Layout Patterns**: Use layout.box(), layout.row(), layout.column() effectively

### Data Management Patterns
- **Scene Properties**: Store all addon data in scene.movie_director property group
- **Asset Integration**: Use Blender's Asset Browser for generative assets
- **Undo Support**: Ensure all operations support Blender's undo system
- **Property Updates**: Use update callbacks for reactive UI behavior
- **Serialization**: JSON for complex data, native properties for simple data

### Performance Patterns
- **Lazy Loading**: Load heavy resources only when needed
- **Async Operations**: Never block the main thread for long operations
- **Memory Management**: Explicit cleanup of temporary resources
- **UI Efficiency**: Minimize UI refreshes and property updates
- **Caching**: Cache expensive computations and API results

## Testing and Quality Assurance

### Testing Strategy
- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test agent coordination and API communication
- **UI Tests**: Manual testing of user workflows and edge cases
- **Performance Tests**: VRAM usage, generation speed, UI responsiveness
- **Compatibility Tests**: Multiple Blender versions and operating systems

### Quality Metrics
- **Code Coverage**: Aim for >80% coverage of critical paths
- **Performance Benchmarks**: Track generation speed and memory usage
- **User Experience Metrics**: Task completion rates and error frequencies
- **Stability Metrics**: Crash rates and error recovery success
- **Compatibility Matrix**: Support across target platforms and versions

### Code Review Process
- **Architecture Review**: Design decisions and pattern consistency
- **Security Review**: Input validation and resource access control
- **Performance Review**: Efficiency and resource usage optimization
- **UX Review**: User workflow and interface design validation
- **Documentation Review**: Code comments and user documentation accuracy

## Deployment and Distribution

### Packaging Preferences
- **Distribution Format**: Standard Blender addon .zip file
- **Dependency Management**: Bundle all dependencies within addon
- **Version Management**: Semantic versioning with clear changelog
- **Asset Bundling**: Include essential models and workflow templates
- **Documentation**: Comprehensive user guide and API reference

### Installation Strategy
- **Self-Contained**: No external installation steps required
- **Compatibility Check**: Validate Blender version and system requirements
- **Graceful Degradation**: Partial functionality when backends unavailable
- **User Guidance**: Clear setup instructions and troubleshooting guide
- **Update Mechanism**: Support for in-place updates and migration

## Development Workflow

### Feature Development Cycle
1. **Requirements Analysis**: User stories and technical specifications
2. **Architecture Design**: Integration points and data flow design
3. **Implementation**: Incremental development with regular testing
4. **Integration Testing**: Agent coordination and workflow validation
5. **User Testing**: Real-world workflow validation with target users
6. **Performance Optimization**: VRAM usage and speed optimization
7. **Documentation**: User guides and technical documentation
8. **Release Preparation**: Final testing and packaging

### Continuous Improvement
- **User Feedback**: Regular collection and integration of user feedback
- **Performance Monitoring**: Track key metrics and optimization opportunities
- **Technology Updates**: Stay current with Blender API and AI model advances
- **Community Engagement**: Active participation in Blender and AI communities
- **Knowledge Sharing**: Document lessons learned and best practices