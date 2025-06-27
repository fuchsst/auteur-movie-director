# User Story: Service Registry

**Story ID:** STORY-012  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Backend Integration  
**Story Points:** 5  
**Priority:** High (P1)  

---

## Story Description

**As the** backend integration system  
**I want** a centralized registry of backend service capabilities and LLM models  
**So that** the system can intelligently route requests and manage features  

## Acceptance Criteria

### Functional Requirements
- [ ] Register all backend services with their capabilities
- [ ] Track available LLM models and providers separately
- [ ] Track service versions and supported features
- [ ] Provide capability queries for routing decisions
- [ ] Update registry based on health check discoveries
- [ ] Support dynamic capability changes
- [ ] Export registry for debugging
- [ ] Validate capability compatibility
- [ ] Provide service metadata access
- [ ] Separate LLM capabilities from backend services

### Technical Requirements
- [ ] Thread-safe registry operations
- [ ] Versioned capability schema
- [ ] JSON serialization support
- [ ] In-memory caching with persistence
- [ ] Event system for registry changes
- [ ] Capability comparison logic
- [ ] Service dependency tracking
- [ ] Migration support for schema changes

### Quality Requirements
- [ ] Registry queries <1ms
- [ ] Updates propagate immediately
- [ ] Zero registry corruption
- [ ] Clear capability definitions
- [ ] Comprehensive service metadata
- [ ] Version compatibility checking
- [ ] Efficient memory usage
- [ ] Type-safe interfaces

## Implementation Notes

### Technical Approach

**Service Registry Architecture:**
```python
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class ServiceCapability:
    """Individual capability of a service"""
    name: str
    version: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class ServiceMetadata:
    """Metadata about a backend service"""
    name: str
    version: str
    api_version: str
    capabilities: List[ServiceCapability] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    status: str = "unknown"
    
class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, ServiceMetadata] = {}
        self._capability_index: Dict[str, Set[str]] = {}
        self._listeners: List[Callable] = []
        self._lock = threading.RLock()
        
    def register_service(self, service_name: str, metadata: ServiceMetadata):
        """Register or update a service in the registry"""
        with self._lock:
            # Store previous state for comparison
            previous = self._services.get(service_name)
            
            # Update registry
            self._services[service_name] = metadata
            
            # Update capability index
            self._update_capability_index(service_name, metadata)
            
            # Notify listeners if changed
            if previous != metadata:
                self._notify_change(service_name, previous, metadata)
```

**LLM Registry:**
```python
@dataclass
class LLMModel:
    """Information about an available LLM model"""
    model_id: str
    provider: str
    capabilities: List[str] = field(default_factory=list)
    context_length: int = 4096
    cost_per_1k_tokens: Dict[str, float] = field(default_factory=dict)
    
class LLMRegistry:
    """Separate registry for LLM models"""
    def __init__(self):
        self._models: Dict[str, LLMModel] = {}
        self._providers: Set[str] = set()
        self._lock = threading.RLock()
        
    def register_model(self, model: LLMModel):
        """Register an available LLM model"""
        with self._lock:
            self._models[model.model_id] = model
            self._providers.add(model.provider)
            
    def update_from_litellm(self):
        """Update registry from LiteLLM's available models"""
        import litellm
        
        # Get available models
        available_models = litellm.get_valid_models()
        
        for model_id in available_models:
            provider = self._get_provider_from_model_id(model_id)
            
            model = LLMModel(
                model_id=model_id,
                provider=provider,
                capabilities=["text_generation", "chat"],
                context_length=self._get_context_length(model_id)
            )
            
            self.register_model(model)
```

**Capability Definitions:**
```python
# Standard capability definitions for backend services
BACKEND_CAPABILITY_DEFINITIONS = {
    "image_generation": {
        "version": "1.0",
        "parameters": {
            "width": {"type": "int", "min": 64, "max": 2048},
            "height": {"type": "int", "min": 64, "max": 2048},
            "steps": {"type": "int", "min": 1, "max": 150},
            "models": {"type": "list", "items": "string"}
        }
    },
    "video_generation": {
        "version": "1.0",
        "parameters": {
            "width": {"type": "int", "min": 64, "max": 1920},
            "height": {"type": "int", "min": 64, "max": 1080},
            "frames": {"type": "int", "min": 1, "max": 300},
            "fps": {"type": "int", "min": 1, "max": 60},
            "models": {"type": "list", "items": "string"}
        }
    },
    "audio_generation": {
        "version": "1.0",
        "parameters": {
            "duration": {"type": "float", "min": 0.1, "max": 300.0},
            "sample_rate": {"type": "int", "choices": [16000, 22050, 44100, 48000]},
            "models": {"type": "list", "items": "string"}
        }
    }
}

# LLM capabilities are separate
LLM_CAPABILITY_DEFINITIONS = {
    "text_generation": {
        "version": "1.0",
        "parameters": {
            "max_tokens": {"type": "int", "min": 1, "max": 100000},
            "temperature": {"type": "float", "min": 0.0, "max": 2.0},
            "top_p": {"type": "float", "min": 0.0, "max": 1.0}
        }
    },
    "chat": {
        "version": "1.0",
        "parameters": {
            "system_prompt": {"type": "string"},
            "history_length": {"type": "int", "min": 0, "max": 100}
        }
    }
}
```

**Service Discovery Integration:**
```python
class ServiceDiscoveryIntegration:
    """Integrate registry with service discovery"""
    
    async def update_from_health_check(self, 
                                     service: str, 
                                     health_data: Dict):
        """Update registry from health check data"""
        
        # Extract capabilities from health response
        capabilities = self._extract_capabilities(health_data)
        
        # Create/update metadata
        metadata = ServiceMetadata(
            name=service,
            version=health_data.get('version', 'unknown'),
            api_version=health_data.get('api_version', '1.0'),
            capabilities=capabilities,
            models=health_data.get('models', []),
            resource_limits=health_data.get('limits', {}),
            status='healthy'
        )
        
        # Update registry
        registry.register_service(service, metadata)
        
    def _extract_capabilities(self, health_data: Dict) -> List[ServiceCapability]:
        """Extract capability information from health data"""
        capabilities = []
        
        # Map service features to standard capabilities
        if 'features' in health_data:
            for feature in health_data['features']:
                if cap := self._map_to_capability(feature):
                    capabilities.append(cap)
                    
        return capabilities
```

**Capability Queries:**
```python
class CapabilityQuery:
    """Query service capabilities"""
    
    def __init__(self, service_registry: ServiceRegistry, llm_registry: LLMRegistry):
        self.service_registry = service_registry
        self.llm_registry = llm_registry
        self._lock = threading.RLock()
    
    def find_services_with_capability(self, 
                                    capability: str,
                                    min_version: Optional[str] = None) -> List[str]:
        """Find all backend services supporting a capability"""
        services = []
        
        with self._lock:
            # Use capability index for fast lookup
            candidates = self.service_registry._capability_index.get(capability, set())
            
            for service_name in candidates:
                metadata = self.service_registry._services[service_name]
                
                # Check version requirement
                if min_version:
                    cap = self._get_capability(metadata, capability)
                    if cap and self._version_compatible(cap.version, min_version):
                        services.append(service_name)
                else:
                    services.append(service_name)
                    
        return services
    
    def find_llm_models_with_capability(self, capability: str) -> List[str]:
        """Find all LLM models supporting a capability"""
        models = []
        
        with self._lock:
            for model_id, model in self.llm_registry._models.items():
                if capability in model.capabilities:
                    models.append(model_id)
                    
        return models
        
    def get_service_models(self, service: str, capability: str) -> List[str]:
        """Get available models for a backend service capability"""
        with self._lock:
            metadata = self.service_registry._services.get(service)
            if not metadata:
                return []
                
            # Get models filtered by capability
            if capability == "image_generation":
                return [m for m in metadata.models if m.startswith("sd-") or m.startswith("flux-")]
            elif capability == "video_generation":
                return [m for m in metadata.models if m.startswith("ltx-") or m.startswith("cog-")]
            # ... etc
            
            return metadata.models
```

**Registry Persistence:**
```python
class RegistryPersistence:
    """Persist registries to disk"""
    
    def __init__(self, service_registry: ServiceRegistry, llm_registry: LLMRegistry):
        self.service_registry = service_registry
        self.llm_registry = llm_registry
        self._lock = threading.RLock()
    
    def save_registries(self, filepath: Path):
        """Save both registries to JSON file"""
        data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "llm_models": {}
        }
        
        with self._lock:
            # Save backend services
            for name, metadata in self.service_registry._services.items():
                data["services"][name] = self._metadata_to_dict(metadata)
            
            # Save LLM models
            for model_id, model in self.llm_registry._models.items():
                data["llm_models"][model_id] = self._model_to_dict(model)
                
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_registries(self, filepath: Path):
        """Load both registries from JSON file"""
        if not filepath.exists():
            return
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Validate version
        if data.get("version") != "1.0":
            raise ValueError(f"Unsupported registry version: {data.get('version')}")
            
        # Load backend services
        for name, service_data in data.get("services", {}).items():
            metadata = self._dict_to_metadata(service_data)
            self.service_registry.register_service(name, metadata)
            
        # Load LLM models
        for model_id, model_data in data.get("llm_models", {}).items():
            model = self._dict_to_model(model_data)
            self.llm_registry.register_model(model)
```

**Blender Property Integration:**
```python
class ServiceRegistryProperties(PropertyGroup):
    """Blender properties for service registry"""
    
    def get_service_capabilities(self, context):
        """Get capabilities for enum property"""
        items = []
        
        registry = get_service_registry()
        for service_name, metadata in registry.get_all_services().items():
            for cap in metadata.capabilities:
                item = (
                    f"{service_name}:{cap.name}",
                    f"{service_name} - {cap.name}",
                    f"Version {cap.version}"
                )
                items.append(item)
                
        return items or [("NONE", "No Capabilities", "")]
        
    selected_capability: EnumProperty(
        name="Service Capability",
        items=get_service_capabilities,
        description="Select a service capability"
    )
```

**Registry Events:**
```python
class RegistryEventHandler:
    """Handle registry change events"""
    
    def on_service_registered(self, service: str, metadata: ServiceMetadata):
        """Called when service is registered"""
        logger.info(f"Service registered: {service} v{metadata.version}")
        
        # Update UI if needed
        for area in bpy.context.screen.areas:
            if area.type in ['VIEW_3D', 'PROPERTIES']:
                area.tag_redraw()
                
    def on_capability_added(self, service: str, capability: ServiceCapability):
        """Called when new capability discovered"""
        logger.info(f"New capability for {service}: {capability.name}")
        
        # Notify agents of new capability
        if agent_system := get_agent_system():
            agent_system.notify_capability_change(service, capability)
```

### Service-Specific Registrations
```python
# ComfyUI capabilities
COMFYUI_CAPABILITIES = [
    ServiceCapability(
        name="image_generation",
        version="1.0",
        parameters={"checkpoints": True, "loras": True, "controlnet": True}
    ),
    ServiceCapability(
        name="video_generation",
        version="1.0",
        parameters={"models": ["ltx-video", "cogvideo"]}
    )
]

# Wan2GP capabilities
WAN2GP_CAPABILITIES = [
    ServiceCapability(
        name="video_generation",
        version="1.0",
        parameters={"models": ["causvid", "hunyuan-video"]}
    )
]

# RVC capabilities
RVC_CAPABILITIES = [
    ServiceCapability(
        name="voice_cloning",
        version="1.0",
        parameters={"models": ["rvc-v2"], "audio_formats": ["wav", "mp3"]}
    )
]

# AudioLDM capabilities  
AUDIOLDM_CAPABILITIES = [
    ServiceCapability(
        name="audio_generation",
        version="1.0",
        parameters={"models": ["audioldm-l", "audioldm-s-full"]}
    )
]
```

## Testing Strategy

### Unit Tests
```python
class TestServiceRegistry(unittest.TestCase):
    def test_service_registration(self):
        # Register services
        # Verify storage
        
    def test_capability_queries(self):
        # Query capabilities
        # Verify results
        
    def test_thread_safety(self):
        # Concurrent operations
        # Verify consistency
```

### Integration Tests
- Test with live service discovery
- Verify capability detection
- Test persistence/loading
- Event system validation

## Dependencies
- STORY-010: Health checks provide capability data for backends and LLM availability
- STORY-001: Service discovery initiates registration (backends only)
- STORY-004: LLM Integration Layer provides model availability
- Used by EPIC-007 (Intelligent Routing)

## Related Stories
- Provides data for agent routing decisions
- Used by workflow selection logic
- Supports capability-based UI

## Definition of Done
- [ ] Registry stores all service metadata
- [ ] Capability queries working
- [ ] Health check integration complete
- [ ] Persistence functional
- [ ] Thread-safe operations verified
- [ ] Event system working
- [ ] Documentation complete
- [ ] Performance targets met

---

**Sign-off:**
- [ ] Development Lead
- [ ] Backend Architect
- [ ] QA Engineer