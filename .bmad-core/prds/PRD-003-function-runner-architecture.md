# Product Requirements Document: Function Runner Architecture

## Executive Summary

### Business Justification
The Function Runner Architecture serves as the strategic moat that enables the Generative Media Studio to stay perpetually current with AI innovation. By treating AI models as hot-swappable microservices, this architecture transforms the platform from a static tool into a living ecosystem:
- **Infinite Model Support**: Any AI model can be integrated without core changes
- **Zero User Complexity**: Complete abstraction of technical details
- **Continuous Innovation**: New models deployed within days of release
- **Fault-Proof Operations**: Isolated failures never impact user experience
- **Optimal Resource Usage**: Pay only for what you use

### Target User Benefits
- **Creators**: Always have access to cutting-edge AI capabilities
- **Platform Operators**: Add new models without engineering bottlenecks
- **Developers**: Clean, standardized integration patterns
- **Enterprise Users**: Predictable performance and compliance
- **Community**: Potential for user-contributed models

### Expected Impact
- Deploy new AI models in < 24 hours vs months
- Support unlimited concurrent model types
- Achieve 99.99% platform availability
- Reduce integration costs by 90%
- Enable community-driven model marketplace

## Problem Statement

### Current Limitations
1. **Dependency Conflicts**: Each AI model requires specific, often incompatible environments
2. **Monolithic Architecture**: Adding models requires core platform modifications
3. **Resource Inefficiency**: All models loaded whether used or not
4. **Update Complexity**: System-wide deployments for any model change
5. **Failure Cascades**: One model crash can bring down entire system

### Technical Challenges
- FLUX requires PyTorch 2.0, older models need PyTorch 1.13
- Different CUDA versions for different model architectures
- Memory leaks compound when switching between models
- Model weights consume 100GB+ of storage when pre-loaded
- Version updates break existing workflows

### Market Reality
- New breakthrough models released weekly
- Users expect immediate access to latest capabilities
- Competition measured in days, not quarters
- Model performance improves 2x annually
- Licensing and compliance requirements vary per model

## Solution Overview

### Microservices Architecture for AI
Implement containerized model execution where each AI capability runs as an independent, hot-swappable service:

**Core Innovation: The Function Runner Pattern**
```
User Request → Platform Routes → Container Executes → Results Return
     ↓              ↓                    ↓                 ↓
"Create Video"  Quality Check    Isolated Environment   Seamless
```

### Architecture Components

1. **Model Containers**: Docker images with pre-loaded models and dependencies
2. **Orchestration Layer**: Intelligent routing based on task and quality
3. **ComfyUI Interface**: Standardized API across all containers
4. **Lifecycle Manager**: Dynamic container start/stop/scaling
5. **Model Registry**: Capability catalog with resource requirements

### Strategic Benefits
- **Complete Isolation**: Dependencies never conflict
- **Hot Deployment**: Add/update models without downtime
- **Selective Loading**: Only active models consume resources
- **Graceful Degradation**: Automatic fallback on failures
- **Version Freedom**: Run multiple versions simultaneously

## User Stories & Acceptance Criteria

### Epic 1: Invisible Complexity
**As a** creative user  
**I want to** use AI capabilities without technical knowledge  
**So that** I can focus on creating

**Acceptance Criteria:**
- [ ] Node names describe function, not model ("Create Image" not "FLUX")
- [ ] Quality setting automatically selects optimal model
- [ ] Seamless fallback when preferred model unavailable
- [ ] Progress updates use creative language
- [ ] Zero exposure to technical errors
- [ ] Progress notifications show user-friendly messages ("Creating your image..." not "Loading FLUX model")
- [ ] Error messages abstracted to actionable guidance ("Try reducing quality" not "CUDA OOM")
- [ ] UI displays estimated time remaining based on quality selection

### Epic 2: Instant Model Adoption
**As a** platform operator  
**I want to** deploy new models rapidly  
**So that** we maintain competitive advantage

**Acceptance Criteria:**
- [ ] New model containerized in < 8 hours
- [ ] Zero changes to platform core required
- [ ] Automatic quality tier assignment
- [ ] A/B testing capability built-in
- [ ] Rollback without user impact

### Epic 3: Efficient Resource Management
**As a** system administrator  
**I want to** optimize infrastructure costs  
**So that** we scale sustainably

**Acceptance Criteria:**
- [ ] Containers start in < 10 seconds on-demand
- [ ] Automatic shutdown after 5 minutes idle
- [ ] GPU memory released immediately
- [ ] Shared model cache across containers
- [ ] Predictive pre-warming based on usage

### Epic 4: Bulletproof Reliability
**As a** user in production  
**I want to** never lose work due to failures  
**So that** I can meet deadlines

**Acceptance Criteria:**
- [ ] Container crashes isolated from platform
- [ ] Automatic restart within 30 seconds
- [ ] Job queue preserved during failures
- [ ] Alternative model selection transparent
- [ ] Health monitoring prevents issues

## Technical Requirements

### Container Infrastructure Setup
#### Prerequisites
- **Docker Engine**: Version 20.10+ with GPU support
- **NVIDIA Container Toolkit**: For GPU acceleration
  ```bash
  # Install NVIDIA Container Toolkit
  distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
  curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
  curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
  sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
  ```
- **Container Registry**: Local registry or cloud (ECR, Docker Hub)
- **Monitoring Stack**: Prometheus + Grafana for container metrics

#### Development Environment
```yaml
# docker-compose.comfyui.yml - Example model service
version: '3.8'
services:
  comfyui:
    image: studio/comfyui:latest
    container_name: gms_comfyui
    ports:
      - "8188:8188"
    volumes:
      - ./models:/models:ro        # Read-only model weights
      - comfyui_cache:/cache       # Shared cache
    environment:
      - MODEL_PATH=/models
      - CACHE_PATH=/cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - gms_network

volumes:
  comfyui_cache:
```

#### Makefile Commands for Model Management
```makefile
# Model-specific targets
up-with-flux:        # Start with FLUX image generation
	docker compose -f docker-compose.yml -f docker-compose.flux.yml up -d

up-with-video:       # Start with video generation models
	docker compose -f docker-compose.yml -f docker-compose.video.yml up -d

build-model:         # Build a specific model container
	@read -p "Model name: " model; \
	docker build -f models/$$model/Dockerfile -t studio/$$model:latest .

push-model:          # Push model to registry
	@read -p "Model name: " model; \
	docker push studio/$$model:latest

model-shell:         # Debug a model container
	@read -p "Model name: " model; \
	docker compose exec $$model /bin/bash
```

### Container Architecture
```
┌─────────────────────────────────────────────────────────┐
│                   Production Canvas (Frontend)           │
├─────────────────────────────────────────────────────────┤
│                    FastAPI Gateway                       │
├─────────────────────────────────────────────────────────┤
│                    Celery Task Queue                     │
├──────────┬──────────┬──────────┬──────────┬───────────┤
│  Image   │  Video   │  Audio   │  Style   │    ...    │
│Container │Container │Container │Container │           │
│          │          │          │          │           │
│ FLUX.dev │ Wan2GP   │ AudioLDM │ IP-Adapt │  Future   │
│ FLUX.sch │ CogVideo │ MusicGen │ ControlN │  Models   │
└──────────┴──────────┴──────────┴──────────┴───────────┘
```

### Container Specifications
```dockerfile
# Base template for all model containers
FROM nvidia/cuda:12.1-cudnn8-runtime-ubuntu22.04

# Model-specific dependencies
RUN pip install -r requirements.txt

# Pre-load model weights
COPY models/ /models/

# Standardized API server
COPY comfyui_server.py /app/
EXPOSE 8188

# Health check
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8188/health

CMD ["python", "/app/comfyui_server.py"]
```

### Model Registry Design
```yaml
models:
  create_image_low:
    function: "Create Image"
    quality: "low"
    container: "studio/flux-schnell:latest"
    resources:
      gpu_memory: 12GB
      priority: 100
    fallback: "create_image_standard"
    
  create_image_standard:
    function: "Create Image"  
    quality: "standard"
    container: "studio/flux-dev-fp8:latest"
    resources:
      gpu_memory: 16GB
      priority: 200
      
  create_image_high:
    function: "Create Image"
    quality: "high"
    container: "studio/flux-dev-fp16:latest"
    resources:
      gpu_memory: 24GB
      priority: 300
```

### Orchestration Flow
```python
class FunctionRunner:
    async def execute(self, function, quality, params):
        # 1. Resolve model from registry
        model = self.registry.get_model(function, quality)
        
        # 2. Check container status
        if not model.container.is_running():
            await model.container.start()
            
        # 3. Submit job via ComfyUI API
        job_id = await model.submit_job(params)
        
        # 4. Stream progress updates
        async for progress in model.track_progress(job_id):
            yield progress
            
        # 5. Return results
        return await model.get_results(job_id)
```

## Implementation Details

### UI Abstraction Layer
The Function Runner provides complete abstraction between technical implementation and user experience:

#### Progress Notification Format
```javascript
// Backend sends technical progress
{
  "event": "model_loading",
  "model": "flux-dev-fp16",
  "progress": 45,
  "stage": "loading_weights"
}

// UI translates to user-friendly message
{
  "message": "Preparing your creation...",
  "progress": 45,
  "timeRemaining": "30 seconds"
}
```

#### Error Message Translation
```javascript
const errorMap = {
  "CUDA_OUT_OF_MEMORY": {
    "message": "This quality setting requires more resources than available",
    "suggestion": "Try using 'Standard' quality instead",
    "action": "REDUCE_QUALITY"
  },
  "MODEL_TIMEOUT": {
    "message": "Taking longer than expected",
    "suggestion": "We're working on it - your creation will complete soon",
    "action": "WAIT"
  }
};
```

#### Quality Settings UI
- **Low Quality**: "Fast Preview" - 10-30 seconds
- **Standard Quality**: "Balanced" - 30-60 seconds  
- **High Quality**: "Maximum Detail" - 1-3 minutes

Each quality level automatically selects the appropriate container based on available resources.

#### Progress Area Integration
Progress notifications display in the collapsible Progress and Notification Area in the right panel:
- Real-time progress bars with percentage complete
- Estimated time remaining based on historical performance
- Queue position when resources are constrained
- Status messages in plain language
- Completed task notifications with preview thumbnails

### Container Lifecycle Management
- **Cold Start**: < 10 seconds with pre-loaded weights
- **Warm Pool**: Keep frequently used containers running
- **Auto-Scale**: Based on queue depth and response time
- **Graceful Shutdown**: Complete active jobs before stopping
- **Resource Limits**: Enforce GPU/CPU/Memory quotas

### VRAM Budgeting System
#### Resource-Aware Container Management
```python
class VRAMBudgetManager:
    def __init__(self, total_vram=24000):  # 24GB in MB
        self.total_vram = total_vram
        self.allocated = {}
        
    def can_start_container(self, model_id, required_vram):
        available = self.total_vram - sum(self.allocated.values())
        return available >= required_vram
        
    def allocate(self, model_id, vram):
        if self.can_start_container(model_id, vram):
            self.allocated[model_id] = vram
            return True
        return False
        
    def release(self, model_id):
        if model_id in self.allocated:
            del self.allocated[model_id]
```

#### Dynamic Model Swapping
```yaml
# Container swap configuration
swap_strategy:
  mode: "least_recently_used"
  grace_period: 300  # 5 minutes
  priorities:
    - high_quality_active_job
    - standard_quality_active_job
    - recently_used
    - preloaded
```

#### Development Resource Profiles
```makefile
# Resource-constrained development modes
dev-lowmem:          # Run with 8GB VRAM limit
	VRAM_LIMIT=8000 docker compose up -d

dev-mediummem:       # Run with 16GB VRAM limit
	VRAM_LIMIT=16000 docker compose up -d

dev-highmem:         # Run with 24GB+ VRAM
	VRAM_LIMIT=24000 docker compose up -d
```

### API Standardization
Every container implements the ComfyUI API:
```
POST   /prompt        - Submit generation job
GET    /history/{id}  - Check job status  
GET    /view          - Retrieve results
WS     /ws            - Real-time updates
GET    /health        - Container status
```

### Quality-Based Routing
```javascript
// User sees simple quality choice
const quality = "high"; // or "standard", "low"

// System maps to specific model
const modelMap = {
  "Create Image": {
    "low": "flux-schnell",      // 12GB VRAM
    "standard": "flux-dev-fp8",  // 16GB VRAM
    "high": "flux-dev-fp16"      // 24GB VRAM
  }
};
```

### Testing Infrastructure
#### Container Testing Framework
```python
# tests/test_function_runner.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_container():
    container = Mock()
    container.is_running.return_value = False
    container.start = Mock(return_value=True)
    return container

async def test_container_cold_start(function_runner, mock_container):
    # Test container starts when not running
    result = await function_runner.execute(
        function="Create Image",
        quality="standard",
        params={"prompt": "test"}
    )
    
    mock_container.start.assert_called_once()
    assert result.status == "completed"

async def test_vram_budget_enforcement(vram_manager):
    # Test VRAM allocation limits
    assert vram_manager.allocate("model1", 20000) == True
    assert vram_manager.allocate("model2", 10000) == False  # Exceeds budget
    
    vram_manager.release("model1")
    assert vram_manager.allocate("model2", 10000) == True
```

#### Integration Testing
```makefile
# Test commands
test-containers:     # Test all model containers
	./scripts/test-containers.sh

test-gpu:           # Test GPU allocation
	docker compose exec worker pytest tests/test_gpu.py

test-fallback:      # Test model fallback scenarios
	docker compose exec worker pytest tests/test_fallback.py
```

#### Load Testing
```yaml
# locust/locustfile.py configuration
class ModelLoadTest(HttpUser):
    @task
    def create_image_standard(self):
        self.client.post("/api/generate", json={
            "function": "Create Image",
            "quality": "standard",
            "params": {"prompt": "test image"}
        })
    
    @task
    def create_video_low(self):
        self.client.post("/api/generate", json={
            "function": "Create Video",
            "quality": "low",
            "params": {"prompt": "test video"}
        })
```

## Success Metrics

### Model Integration Velocity
- **Time to Deploy**: < 24 hours for new model
- **Success Rate**: 95% first-time deployment success
- **Reusability**: 80% configuration reuse
- **Documentation**: Automated from container metadata
- **Testing Coverage**: 100% automated validation

### System Performance
- **Availability**: 99.99% uptime SLA
- **Response Time**: < 200ms to start generation
- **Throughput**: 1000+ concurrent jobs
- **Resource Efficiency**: 85% GPU utilization
- **Cost per Generation**: Decrease 20% quarterly

### User Experience
- **Abstraction Success**: 0% users see model names
- **Fallback Transparency**: 100% seamless degradation
- **Error Clarity**: 95% self-resolved issues
- **Performance Satisfaction**: 4.5+ star rating
- **Feature Adoption**: New models used within 48 hours

## Risk Mitigation

### Technical Risks
1. **Container Overhead**: 5-10% performance penalty
   - *Mitigation*: GPU pass-through, optimized base images
2. **Network Bottlenecks**: Large file transfers
   - *Mitigation*: Shared memory volumes, caching layer
3. **Version Sprawl**: Too many container variants
   - *Mitigation*: Automated deprecation, usage analytics

### Operational Risks
1. **Monitoring Complexity**: Many moving parts
   - *Mitigation*: Unified observability platform
2. **Security Surface**: Each container is attack vector
   - *Mitigation*: Minimal base images, network isolation
3. **Cost Management**: Runaway GPU usage
   - *Mitigation*: Quotas, automatic scaling limits

## Development Roadmap

### Phase 1: Foundation (Week 1-2)
- Docker environment with GPU support
- Basic container management service
- ComfyUI API wrapper template
- Health check infrastructure

### Phase 2: Core Models (Week 3-4)
- Image generation containers (FLUX variants)
- Video generation containers (Wan2GP)
- Model registry implementation
- Quality-based routing

### Phase 3: Orchestration (Week 5-6)
- Celery integration for job management
- Container lifecycle automation
- Resource monitoring and limits
- Fallback logic implementation

### Phase 4: Production Hardening (Week 7-8)
- Performance optimization
- Security scanning and hardening
- Monitoring dashboard
- Documentation and examples

## Future Vision

### Community Ecosystem
- **Model Marketplace**: Users contribute containers
- **Revenue Sharing**: Incentivize quality models
- **Certification Program**: Ensure security/performance
- **Template Library**: Accelerate new integrations

### Technical Evolution
- **Kubernetes Migration**: Cloud-native orchestration
- **Edge Deployment**: Local model execution
- **Model Mesh**: Distributed model serving
- **Federated Learning**: Privacy-preserving training
- **Quantum Ready**: Future computational paradigms

---

**Document Version**: 2.0  
**Created**: 2025-01-02  
**Last Updated**: 2025-01-02  
**Status**: Final Draft  
**Owner**: Generative Media Studio Architecture Team