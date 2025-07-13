# Epic: Function Runner Architecture

**Epic ID**: EPIC-003  
**Based on**: PRD-003-function-runner-architecture  
**Target Milestone**: Q1 2025 - AI Integration Release  
**Status**: 🚧 IN PROGRESS  
**Epic Points**: 82 (12 Completed)  
**Team Size**: 3 developers (1 frontend, 2 backend)  
**Start Date**: 2025-01-05  

## Epic Description

Implement a lean, scalable architecture for executing AI functions through worker-based Python scripts that communicate with external ComfyUI/Gradio API endpoints. This system provides quality-based routing, template management, and complete abstraction of technical complexity from users while maintaining flexibility to integrate any AI model without core platform changes.

## Business Value

### Impact on Generative Film Production Workflow
- **Infinite Model Support**: Any AI model accessible via API can be integrated
- **Zero User Complexity**: Technical details completely abstracted behind "Create Image" style functions
- **Quality-Based Optimization**: Automatic model/parameter selection based on quality settings
- **Rapid Innovation Adoption**: New models integrated through template updates, not code changes

### User Experience Improvements
- Simple function names describe creative intent, not technical models
- Quality slider automatically optimizes for speed vs. fidelity
- Transparent fallback when preferred quality unavailable
- Progress updates in creative language ("Creating your masterpiece...")

### Technical Capability Enhancements
- Decoupled architecture allows independent scaling of AI services
- Template-based workflow management for easy customization
- Standardized parameter interface across all AI functions
- Built-in A/B testing capability through template variants

### Platform Foundation Benefits
- Clean separation between platform and AI execution
- Reduced infrastructure complexity and maintenance
- Pay-per-use model compatibility (external API services)
- Community template marketplace potential

## Scope & Boundaries

### In Scope
**Worker Infrastructure**
- Lean Python script execution framework
- Task queue integration for job management
- Result collection and progress tracking
- Error handling and retry logic

**Template Management System**
- Quality-based workflow template organization
- Template loading and caching mechanisms
- Parameter merging and validation
- Version management for template updates

**API Client Layer**
- ComfyUI HTTP/WebSocket client implementation
- Gradio client for applicable models
- Standardized request/response handling
- Connection pooling and timeout management

**Quality Abstraction**
- Quality tier definitions (low/standard/high/premium)
- Quality-to-template mapping configuration
- Parameter optimization per quality level
- Resource usage estimation

**Result Handling**
- Output file management and storage
- Thumbnail generation for visual outputs
- Metadata preservation (parameters, timing, etc.)
- Progress notification standardization

### Out of Scope
- Running ComfyUI/Gradio instances (assumed externally available)
- AI model installation or management
- Container orchestration or Docker management
- ComfyUI node or workflow development
- Model training or fine-tuning
- GPU resource management (handled by external services)

## Acceptance Criteria

### Functional Criteria
- [x] Quality-based task routing implemented and tested
- [ ] Worker executes Python scripts successfully
- [ ] Templates load based on function + quality combination
- [ ] Parameters merge correctly (user + quality + defaults)
- [ ] ComfyUI API client handles all workflow operations
- [ ] Results return to correct project location
- [ ] Progress updates stream in real-time
- [ ] Fallback to lower quality works transparently

### Technical Criteria
- [x] Task dispatcher routes based on quality tiers
- [ ] Python scripts follow standardized pattern
- [ ] Template structure supports versioning
- [ ] API clients handle connection failures gracefully
- [ ] Worker pool scales based on queue depth
- [ ] Monitoring tracks success/failure rates
- [ ] Performance meets targets (< 5s overhead)

### Quality Criteria
- [ ] 90%+ test coverage on critical paths
- [ ] Documentation covers template creation
- [ ] Error messages guide user resolution
- [ ] Logging enables rapid debugging
- [ ] Security review of external API calls
- [ ] Load testing validates 100+ concurrent jobs

## Epic Decomposition

### Story Group 1: Worker Infrastructure (20 points)
**Foundation for Python script execution**

- **STORY-041**: Worker Service Implementation (8 points) 🔜
  - Create worker service for executing Python scripts
  - Implement job queue consumption
  - Add error handling and retry logic
  - Status: Not Started

- **STORY-042**: Script Execution Framework (5 points) 🔜
  - Standardize script interface and parameters
  - Implement script loading and validation
  - Add timeout and resource controls
  - Status: Not Started

- **STORY-043**: Result Collection System (7 points) 🔜
  - Design result storage structure
  - Implement file handling for outputs
  - Add metadata tracking
  - Status: Not Started

### Story Group 2: Template Management (18 points)
**Quality-based workflow organization**

- **STORY-044**: Template Directory Structure (5 points) 🔜
  - Create template organization hierarchy
  - Implement template discovery
  - Add validation for template format
  - Status: Not Started

- **STORY-045**: Template Loading Service (8 points) 🔜
  - Build template loading with caching
  - Implement quality-based selection
  - Add template versioning support
  - Status: Not Started

- **STORY-046**: Parameter Translation Engine (5 points) 🔜
  - Create parameter mapping system
  - Implement translation strategies (direct, lookup, file upload)
  - Add validation for required parameters
  - Build style-to-LoRA lookup tables
  - Status: Not Started

### Story Group 3: API Client Layer (22 points)
**External service communication**

- **STORY-047**: ComfyUI Client Implementation (10 points) 🔜
  - Build HTTP/WebSocket client for ComfyUI
  - Implement workflow submission
  - Add progress tracking via WebSocket
  - Status: Not Started

- **STORY-048**: Gradio Client Implementation (5 points) 🔜
  - Create Gradio API client
  - Implement prediction calls
  - Add result polling
  - Status: Not Started

- **STORY-049**: Connection Management (7 points) 🔜
  - Implement connection pooling
  - Add health checking
  - Create failover logic
  - Status: Not Started

### Story Group 4: Quality Abstraction (18 points)
**User-friendly quality system**

- **STORY-013**: Function Runner Foundation (12 points) ✅
  - Task dispatcher with quality mapping
  - WebSocket progress updates
  - Basic pipeline configuration
  - Status: Complete (60%)

- **STORY-050**: Quality Configuration System (6 points) 🔜
  - Extend quality tier definitions
  - Create quality-to-parameter mappings
  - Add resource estimation
  - Status: Not Started

### Story Group 5: Integration & Testing (12 points)
**End-to-end validation**

- **STORY-051**: Integration Testing Suite (8 points) 🔜
  - Create mock ComfyUI/Gradio servers
  - Build end-to-end test scenarios
  - Add performance benchmarks
  - Status: Not Started

- **STORY-052**: Developer Documentation (4 points) 🔜
  - Document template creation process
  - Create integration examples
  - Add troubleshooting guide
  - Status: Not Started

## Integration Points

### With EPIC-001 (Web Platform Foundation)
- WebSocket infrastructure for progress updates
- Task notification system integration
- Frontend node system receives results

### With EPIC-002 (Project & Asset Management)
- Results stored in project structure
- Takes system for version management
- Asset library for template storage

### With Future PRD-004 (Production Canvas)
- Canvas nodes trigger function execution
- Real-time preview of generation progress
- Node parameter interfaces

## Technical Architecture

### Simplified Flow
```
Canvas Node → Task Dispatcher → Worker → Python Script → External API → Results
     ↓              ↓              ↓            ↓              ↓           ↓
"Create Image"  Quality Check   Execute    Call ComfyUI   Process    Store File
```

### Function Interface Definition
Every function in our system implements this standardized interface:

```python
# Base Function Interface
class FunctionInterface(ABC):
    """All functions must implement this interface"""
    
    @abstractmethod
    async def execute(
        self,
        params: dict,              # Node parameters from canvas
        quality: str,              # Quality tier (low/standard/high/premium)
        project_path: str,         # Where to save results
        progress_callback: Callable # For progress updates
    ) -> FunctionResult:
        """Execute the function and return results"""
        pass
    
    @abstractmethod
    def get_parameter_schema(self) -> dict:
        """Return JSON schema for parameter validation"""
        pass
    
    @abstractmethod
    def get_backend_type(self) -> str:
        """Return 'comfyui' or 'gradio'"""
        pass

class FunctionResult:
    """Standardized result format"""
    output_files: list[str]      # Generated files
    metadata: dict               # Generation parameters, timing, etc.
    preview_url: str | None      # Optional preview
    error: str | None            # Error message if failed
```

### ComfyUI Function Implementation
```python
# functions/create_image_comfyui.py
class CreateImageComfyUI(FunctionInterface):
    def __init__(self):
        self.client = ComfyUIClient("http://comfyui:8188")
        
    async def execute(self, params, quality, project_path, progress_callback):
        # 1. Load and prepare workflow
        template = load_template(f"create_image_{quality}")
        workflow = self._prepare_workflow(template, params)
        
        # 2. Submit to ComfyUI
        prompt_id = await self.client.queue_prompt(workflow)
        
        # 3. Stream progress via WebSocket
        async for update in self.client.track_progress(prompt_id):
            progress_callback(update.progress, update.message)
            
        # 4. Collect results
        outputs = await self.client.get_outputs(prompt_id)
        saved_files = await self._save_outputs(outputs, project_path)
        
        return FunctionResult(
            output_files=saved_files,
            metadata={"prompt_id": prompt_id, "quality": quality},
            preview_url=saved_files[0] if saved_files else None
        )
    
    def get_parameter_schema(self):
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Image description"},
                "style": {"type": "string", "enum": ["anime", "realistic", "artistic"]},
                "reference_image": {"type": "string", "format": "file-path"}
            },
            "required": ["prompt"]
        }
    
    def get_backend_type(self):
        return "comfyui"
```

### Gradio Function Implementation
```python
# functions/create_audio_gradio.py
class CreateAudioGradio(FunctionInterface):
    def __init__(self):
        self.client = GradioClient("http://gradio:7860")
        
    async def execute(self, params, quality, project_path, progress_callback):
        # 1. Prepare inputs based on quality
        duration = {"low": 5, "standard": 10, "high": 30}[quality]
        
        # 2. Submit to Gradio
        job = await self.client.submit(
            fn_index=0,  # Function endpoint
            inputs=[params["prompt"], duration]
        )
        
        # 3. Poll for progress
        while not job.done():
            status = await job.status()
            progress_callback(status.progress, f"Generating audio... {status.eta}s")
            await asyncio.sleep(1)
            
        # 4. Get results
        result = await job.result()
        saved_file = await self._save_audio(result, project_path)
        
        return FunctionResult(
            output_files=[saved_file],
            metadata={"duration": duration, "model": "musicgen"},
            preview_url=saved_file
        )
    
    def get_parameter_schema(self):
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Audio description"},
                "mood": {"type": "string", "enum": ["happy", "sad", "epic", "calm"]}
            },
            "required": ["prompt"]
        }
    
    def get_backend_type(self):
        return "gradio"
```

### Function Registration
```python
# Function Registry for easy node creation
FUNCTION_REGISTRY = {
    "create_image": {
        "class": CreateImageComfyUI,
        "display_name": "Create Image",
        "category": "generation",
        "icon": "image"
    },
    "create_audio": {
        "class": CreateAudioGradio,
        "display_name": "Create Audio", 
        "category": "generation",
        "icon": "music"
    },
    "style_transfer": {
        "class": StyleTransferComfyUI,
        "display_name": "Apply Style",
        "category": "effects",
        "icon": "palette"
    }
}

# Easy function addition
def register_function(function_id: str, function_class: type, metadata: dict):
    """Register a new function for use in the canvas"""
    FUNCTION_REGISTRY[function_id] = {
        "class": function_class,
        **metadata
    }
```

### Template Structure Example
```json
{
  "template_id": "create_image_standard",
  "version": "1.0",
  "function": "create_image",
  "quality": "standard",
  "parameter_mapping": {
    "prompt": {
      "source": "node.prompt",
      "target": "workflow.nodes.clip_text_encode.text",
      "type": "direct"
    },
    "style": {
      "source": "node.style", 
      "target": "workflow.nodes.lora_loader.lora_name",
      "type": "lookup",
      "lookup_table": {
        "anime": "anime_style_v2.safetensors",
        "realistic": "photorealistic_v3.safetensors",
        "artistic": "artistic_style_v1.safetensors"
      }
    },
    "reference_image": {
      "source": "node.reference_image",
      "target": "workflow.nodes.image_loader.image",
      "type": "file_upload",
      "preprocessing": "upload_to_comfyui"
    }
  },
  "quality_parameters": {
    "standard": {
      "sampler_steps": 20,
      "cfg_scale": 7.5,
      "width": 1024,
      "height": 1024
    }
  },
  "workflow_template": "comfyui_workflows/flux_standard.json",
  "api_endpoint": "http://comfyui:8188",
  "timeout": 180
}
```

### Parameter Translation System
The Function Runner implements sophisticated parameter translation:

1. **Direct Mapping**: Simple value pass-through (prompt → text)
2. **Lookup Translation**: Map user-friendly values to technical ones (style → LoRA file)
3. **File Handling**: Upload referenced files before workflow execution
4. **Computed Values**: Generate parameters based on quality settings
5. **Conditional Parameters**: Include/exclude based on user inputs

### Backend Client Implementations

#### ComfyUI Client Base
```python
class ComfyUIClient:
    """Base client for ComfyUI API interactions"""
    
    async def queue_prompt(self, workflow: dict) -> str:
        """Submit workflow and return prompt_id"""
        response = await self.post("/prompt", {"prompt": workflow})
        return response["prompt_id"]
    
    async def track_progress(self, prompt_id: str):
        """Stream progress updates via WebSocket"""
        async with self.ws_connect() as ws:
            await ws.send_json({"type": "subscribe", "prompt_id": prompt_id})
            async for msg in ws:
                if msg.type == "executing":
                    yield ProgressUpdate(
                        progress=msg.data["progress"],
                        message=self._translate_node_name(msg.data["node"])
                    )
    
    async def get_outputs(self, prompt_id: str) -> dict:
        """Retrieve generated outputs"""
        history = await self.get(f"/history/{prompt_id}")
        return self._extract_outputs(history)
```

#### Gradio Client Base
```python
class GradioClient:
    """Base client for Gradio API interactions"""
    
    async def submit(self, fn_index: int, inputs: list) -> Job:
        """Submit prediction request"""
        response = await self.post("/api/predict", {
            "fn_index": fn_index,
            "data": inputs
        })
        return Job(self, response["job_id"])
    
class Job:
    """Gradio job with polling support"""
    
    async def status(self) -> JobStatus:
        """Poll current status"""
        response = await self.client.get(f"/api/status/{self.job_id}")
        return JobStatus(
            progress=response.get("progress", 0),
            eta=response.get("eta"),
            done=response["status"] == "complete"
        )
    
    async def result(self) -> Any:
        """Get final result"""
        response = await self.client.get(f"/api/result/{self.job_id}")
        return response["data"]
```

### Creating New Functions - Developer Guide

To add a new node/function to the system:

1. **Create Function Class**
```python
# functions/my_new_function.py
class MyNewFunction(FunctionInterface):
    def __init__(self):
        # Choose backend
        self.client = ComfyUIClient("http://comfyui:8188")
        # or
        self.client = GradioClient("http://gradio:7860")
    
    async def execute(self, params, quality, project_path, progress_callback):
        # Your implementation
        pass
    
    def get_parameter_schema(self):
        # Define inputs
        pass
    
    def get_backend_type(self):
        return "comfyui"  # or "gradio"
```

2. **Create Templates** (for ComfyUI functions)
```
workspace/Library/Templates/my_function/
├── low_quality/workflow.json
├── standard_quality/workflow.json
└── high_quality/workflow.json
```

3. **Register Function**
```python
register_function(
    "my_function",
    MyNewFunction,
    {
        "display_name": "My Function",
        "category": "effects",
        "icon": "sparkles"
    }
)
```

4. **Frontend Integration**
The function automatically appears in the node palette with proper parameter controls based on the schema.

## Risk Mitigation

### Technical Risks
1. **External API Availability**
   - Mitigation: Health checks, circuit breakers, fallback endpoints
2. **Network Latency**
   - Mitigation: Connection pooling, request batching, local caching
3. **Template Compatibility**
   - Mitigation: Version management, validation, backwards compatibility

### Operational Risks
1. **Cost Management**
   - Mitigation: Usage quotas, quality-based pricing, monitoring
2. **Security Concerns**
   - Mitigation: API authentication, input sanitization, output validation
3. **Performance Bottlenecks**
   - Mitigation: Worker scaling, queue optimization, result caching

## Success Metrics

### Development Velocity
- New function integration: < 4 hours
- Template creation: < 1 hour
- Quality tier addition: < 2 hours

### System Performance
- Function overhead: < 5 seconds
- Worker utilization: > 80%
- Success rate: > 95%

### User Satisfaction
- Quality abstraction effectiveness: 100%
- Error self-resolution: > 90%
- Performance satisfaction: > 4.5/5

## Implementation Status

### Completed (15%)
- ✅ Task dispatcher with quality routing (STORY-013)
- ✅ Basic pipeline configuration
- ✅ WebSocket progress infrastructure
- ✅ Test coverage for dispatcher

### In Progress (0%)
- None currently active

### Remaining (85%)
- Worker service implementation
- Template management system
- API client development
- Quality configuration extension
- Integration testing
- Documentation

---

**Document Version**: 1.0  
**Created**: 2025-01-13  
**Last Updated**: 2025-01-13  
**Epic Owner**: Backend Team Lead  
**Technical Lead**: AI Integration Architect