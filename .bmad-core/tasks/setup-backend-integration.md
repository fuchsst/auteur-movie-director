# Setup Backend Integration

## Task Overview
Establish robust connections to the generative AI backends (ComfyUI, Wan2GP, LiteLLM) with proper error handling, offline-first operation, and resource management.

## Objective
Create a reliable backend integration system that enables the film crew agents to access generative capabilities while maintaining system stability and user experience.

## Key Requirements
- [ ] Offline-first architecture with graceful degradation
- [ ] Robust error handling and retry mechanisms
- [ ] VRAM-aware task routing and resource management
- [ ] Async operations that don't block Blender UI
- [ ] Comprehensive connection monitoring and status reporting
- [ ] Self-contained deployment with bundled dependencies

## Backend Architecture

### 1. Backend Client Manager
```python
class BackendManager:
    """Central manager for all generative backend connections"""
    
    def __init__(self):
        self.comfyui_client = ComfyUIClient()
        self.wan2gp_client = Wan2GPClient()
        self.litellm_client = LiteLLMClient()
        self.vram_manager = VRAMManager()
        
    def initialize_backends(self):
        """Initialize all backend connections with health checks"""
        results = {}
        
        # Check each backend availability
        results['comfyui'] = self.comfyui_client.health_check()
        results['wan2gp'] = self.wan2gp_client.health_check()
        results['litellm'] = self.litellm_client.health_check()
        
        return results
    
    def select_optimal_backend(self, task_type, requirements):
        """Select best backend based on task requirements and availability"""
        if task_type == "video_generation":
            if requirements.get("character_lora") or requirements.get("style_lora"):
                return self.comfyui_client if self.comfyui_client.is_available() else None
            else:
                return self.wan2gp_client if self.wan2gp_client.is_available() else self.comfyui_client
        
        elif task_type == "text_generation":
            return self.litellm_client if self.litellm_client.is_available() else None
        
        return None
```

### 2. ComfyUI Integration
```python
class ComfyUIClient:
    """Client for ComfyUI workflow execution and management"""
    
    def __init__(self, base_url="http://localhost:8188"):
        self.base_url = base_url
        self.session = None
        self.workflow_templates = {}
        self.model_cache = {}
        
    def health_check(self):
        """Check if ComfyUI server is running and responsive"""
        try:
            response = requests.get(f"{self.base_url}/system_stats", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def load_workflow_template(self, template_name):
        """Load and cache workflow template"""
        template_path = f"workflows/comfyui/{template_name}.json"
        
        if template_name not in self.workflow_templates:
            with open(template_path, 'r') as f:
                self.workflow_templates[template_name] = json.load(f)
        
        return self.workflow_templates[template_name]
    
    async def execute_workflow(self, template_name, parameters, progress_callback=None):
        """Execute ComfyUI workflow with parameters"""
        try:
            # Load and customize workflow
            workflow = self.load_workflow_template(template_name)
            customized_workflow = self.inject_parameters(workflow, parameters)
            
            # Check VRAM requirements
            vram_required = self.calculate_vram_requirement(customized_workflow)
            if not self.vram_manager.check_availability(vram_required):
                raise VRAMInsufficientError(f"Requires {vram_required}GB VRAM")
            
            # Execute workflow
            response = await self.submit_workflow(customized_workflow)
            
            # Monitor progress
            result = await self.monitor_execution(response['prompt_id'], progress_callback)
            
            return result
            
        except Exception as e:
            self.handle_execution_error(e)
            raise
    
    def inject_parameters(self, workflow, parameters):
        """Inject dynamic parameters into workflow template"""
        workflow_copy = copy.deepcopy(workflow)
        
        # Replace parameter placeholders
        for node_id, node in workflow_copy.items():
            if "inputs" in node:
                for input_key, input_value in node["inputs"].items():
                    if isinstance(input_value, str) and input_value.startswith("{{"):
                        param_name = input_value.strip("{}")
                        if param_name in parameters:
                            node["inputs"][input_key] = parameters[param_name]
        
        return workflow_copy
```

### 3. Wan2GP Integration
```python
class Wan2GPClient:
    """Client for Wan2GP video generation"""
    
    def __init__(self):
        self.gradio_client = None
        self.config_templates = {}
        
    def initialize(self):
        """Initialize Gradio client connection"""
        try:
            from gradio_client import Client
            self.gradio_client = Client("http://localhost:7860")
            return True
        except Exception as e:
            print(f"Wan2GP initialization failed: {e}")
            return False
    
    async def generate_video(self, prompt, config_name="default", progress_callback=None):
        """Generate video using Wan2GP"""
        try:
            if not self.gradio_client:
                if not self.initialize():
                    raise ConnectionError("Wan2GP not available")
            
            # Load configuration
            config = self.load_config_template(config_name)
            
            # Execute generation
            result = await self.gradio_client.predict(
                prompt=prompt,
                **config,
                api_name="/generate_video"
            )
            
            return result
            
        except Exception as e:
            self.handle_generation_error(e)
            raise
```

### 4. LiteLLM Integration
```python
class LiteLLMClient:
    """Client for local LLM server via LiteLLM"""
    
    def __init__(self, base_url="http://localhost:4000"):
        self.base_url = base_url
        self.client = None
        
    def initialize(self):
        """Initialize LiteLLM client"""
        try:
            import litellm
            self.client = litellm
            # Test connection
            response = self.client.completion(
                model="local/llama",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    async def generate_text(self, prompt, max_tokens=2000, temperature=0.7):
        """Generate text using local LLM"""
        try:
            if not self.client:
                if not self.initialize():
                    raise ConnectionError("LiteLLM not available")
            
            response = await self.client.acompletion(
                model="local/llama",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.handle_text_generation_error(e)
            raise
```

## VRAM Management Integration

### 1. VRAM Budgeting System
```python
class VRAMManager:
    """Manage VRAM allocation and budgeting"""
    
    def __init__(self):
        self.vram_profiles = self.load_vram_profiles()
        self.current_allocation = {}
        
    def load_vram_profiles(self):
        """Load model VRAM requirement profiles"""
        with open("workflows/vram_profiles.json", 'r') as f:
            return json.load(f)
    
    def calculate_workflow_vram(self, workflow_name, parameters):
        """Calculate total VRAM requirement for workflow"""
        base_requirement = self.vram_profiles.get(workflow_name, {}).get("base", 8)
        
        # Add requirements for additional models
        additional = 0
        if parameters.get("character_lora"):
            additional += self.vram_profiles.get("character_lora", {}).get("vram", 2)
        if parameters.get("style_lora"):
            additional += self.vram_profiles.get("style_lora", {}).get("vram", 2)
        
        return base_requirement + additional
    
    def check_availability(self, required_vram):
        """Check if required VRAM is available"""
        available_vram = self.get_available_vram()
        return available_vram >= required_vram
    
    def reserve_vram(self, task_id, amount):
        """Reserve VRAM for specific task"""
        if self.check_availability(amount):
            self.current_allocation[task_id] = amount
            return True
        return False
    
    def release_vram(self, task_id):
        """Release VRAM after task completion"""
        if task_id in self.current_allocation:
            del self.current_allocation[task_id]
```

## Error Handling and Fallback Strategies

### 1. Connection Error Handling
```python
class BackendErrorHandler:
    """Handle backend connection and execution errors"""
    
    @staticmethod
    def handle_connection_error(backend_name, error):
        """Handle backend connection failures"""
        error_messages = {
            'comfyui': "ComfyUI server not responding. Please start ComfyUI and try again.",
            'wan2gp': "Wan2GP service unavailable. Check Gradio server status.",
            'litellm': "LiteLLM server not responding. Verify local LLM setup."
        }
        
        message = error_messages.get(backend_name, f"{backend_name} connection failed")
        return {
            'success': False,
            'error': 'connection_error',
            'message': message,
            'user_action': f"Start {backend_name} service and retry"
        }
    
    @staticmethod
    def handle_vram_error(required, available):
        """Handle VRAM insufficient errors"""
        return {
            'success': False,
            'error': 'vram_insufficient',
            'message': f"Insufficient VRAM: {required}GB required, {available}GB available",
            'user_action': "Reduce quality settings or free up VRAM"
        }
    
    @staticmethod
    def handle_generation_error(error):
        """Handle generation process errors"""
        return {
            'success': False,
            'error': 'generation_failed',
            'message': f"Generation failed: {str(error)}",
            'user_action': "Check model availability and try again"
        }
```

### 2. Offline-First Operation
```python
def check_online_access():
    """Check if online access is allowed by Blender"""
    return bpy.app.online_access

class OfflineFallbackManager:
    """Manage offline fallback strategies"""
    
    def __init__(self):
        self.local_models = self.scan_local_models()
        self.fallback_workflows = self.load_fallback_workflows()
    
    def get_fallback_workflow(self, original_workflow):
        """Get offline-compatible fallback workflow"""
        if original_workflow in self.fallback_workflows:
            return self.fallback_workflows[original_workflow]
        
        # Generate simplified workflow
        return self.create_simplified_workflow(original_workflow)
    
    def create_simplified_workflow(self, workflow_name):
        """Create simplified version of workflow for limited resources"""
        # Implementation for creating resource-efficient workflows
        pass
```

## Success Criteria
- [ ] All backends connect successfully when available
- [ ] Graceful degradation when backends are unavailable
- [ ] VRAM management prevents system crashes
- [ ] Async operations keep Blender UI responsive
- [ ] Error messages provide clear user guidance
- [ ] Offline-first operation respects bpy.app.online_access
- [ ] Resource monitoring works accurately

## Related Tasks
- `implement-vram-budgeting.md` - Detailed VRAM management
- `implement-crewai-agents.md` - Agent integration with backends
- `create-addon-structure.md` - Overall addon architecture

## Dependencies
- `backend-integration-validation` checklist
- `backend-client-template` template
- `error-recovery-patterns` utils