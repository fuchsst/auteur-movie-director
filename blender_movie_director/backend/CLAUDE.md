# Backend Integration Layer

## Overview

The backend layer implements the service connectivity architecture defined in [PRD-001](/.bmad-core/prds/PRD-001-backend-integration-service-layer.md). It provides unified API integration with local generative services through consistent Python interfaces, enabling intelligent task routing and robust error handling.

## Architecture

As per PRD-001, the backend layer consists of:

### 4 Backend Services
- **ComfyUI** (`comfyui/`) - Complex image/video workflows with advanced compositing
- **Wan2GP** (`wan2gp/`) - Fast video generation with multiple model support  
- **RVC** - Voice cloning and audio processing (integration pending)
- **AudioLDM** - Sound effects and ambient audio generation (integration pending)

### LLM Integration Layer
- **LiteLLM** (`litellm/`) - Python library for unified LLM access (not a backend service)
- Supports multiple providers: OpenAI, Anthropic, Azure, local models
- Used by the Screenwriter agent for narrative development

## Core Components

### Service Discovery (`service_discovery.py`)
Implements automatic discovery of backend services as specified in PRD-001:
- Scans default and custom ports
- Validates service availability via health endpoints
- Completes discovery within 5-second target
- Supports parallel discovery of all services

### Client Integration Pattern
```python
# Using existing Python clients as per PRD-001
from comfyui_api_client import ComfyUIClient
from gradio_client import Client as GradioClient
import litellm

# Backend service clients
comfyui = ComfyUIClient("http://localhost:8188")
wan2gp = GradioClient("http://localhost:7860")

# LLM integration (not a backend service)
response = litellm.completion(model="gpt-3.5-turbo", messages=[...])
```

## Task Routing Logic

### Intelligent Backend Selection
As defined in PRD-001, the Producer agent routes tasks based on:
- Task complexity and requirements
- Available hardware resources (VRAM)
- Service capabilities
- Performance requirements

```python
def select_optimal_backend(task_type, complexity, available_resources):
    """Route tasks to most appropriate backend"""
    
    if task_type == "quick_preview":
        return wan2gp_client  # Fast generation
    elif task_type == "character_consistency":
        return comfyui_client  # Advanced workflows
    elif task_type == "voice_generation":
        return rvc_client  # Voice cloning
    elif task_type == "sound_effects":
        return audioldm_client  # Audio generation
```

## Connection Management

### Health Check Service
Per PRD-001 requirements:
- Monitors all 4 backend services
- Separate API key validation for LLM integration
- Updates status every 30 seconds
- Provides metrics for the Health Dashboard

### Connection Pool Manager
- Maintains persistent connections to backends
- Thread-safe pool operations
- Automatic reconnection with exponential backoff
- Resource cleanup on shutdown

## Error Handling & Resilience

### Robust Connection Management
```python
class ResilientBackendClient:
    """Implements resilience patterns from PRD-001"""
    
    async def execute_with_retry(self, operation, max_retries=3):
        for attempt in range(max_retries):
            try:
                return await operation()
            except ConnectionError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
```

### Resource Monitoring
- VRAM usage tracking
- Queue depth monitoring
- Response time metrics
- Success rate calculation

## Integration with Agent System

The backend layer serves the film crew agents:
- **Screenwriter** → LiteLLM for text generation
- **Cinematographer** → ComfyUI/Wan2GP for video generation
- **Sound Designer** → RVC/AudioLDM for audio
- **Casting Director** → ComfyUI for character consistency

## Development Patterns

### Async Operations
All backend operations are asynchronous to maintain UI responsiveness:
```python
async def generate_content(prompt, backend):
    """Non-blocking generation"""
    result = await backend.generate_async(prompt)
    
    # Update UI on main thread
    bpy.app.timers.register(
        lambda: update_ui_with_result(result)
    )
```

### Configuration Management
- Service URLs in addon preferences
- Custom ports via .env file
- Model selection based on hardware
- Template paths for workflows

## Testing

Run backend integration tests:
```bash
pytest tests/test_service_discovery.py -v
./scripts/run-script.sh tests/manual_test_discovery.py
```

## Reference
- [PRD-001: Backend Integration Service Layer](/.bmad-core/prds/PRD-001-backend-integration-service-layer.md)
- [STORY-001: Service Discovery](/.bmad-core/stories/EPIC-001-backend-service-connectivity/STORY-001-service-discovery-infrastructure.md)
- [ComfyUI API Guide](/.bmad-core/data/comfyui-api-guide.md)