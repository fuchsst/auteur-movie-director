# User Story: ComfyUI Client Integration

**Story ID:** STORY-002  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Backend Client  
**Story Points:** 5  
**Priority:** Critical (P0)  

---

## Story Description

**As a** filmmaker using ComfyUI for image/video generation  
**I want** a reliable client connection to ComfyUI  
**So that** I can execute workflows and receive results seamlessly  

## Acceptance Criteria

### Functional Requirements
- [ ] Establishes connection to ComfyUI server using comfyui_api_client
- [ ] Loads and validates workflow JSON files
- [ ] Sets workflow parameters dynamically from Blender
- [ ] Executes workflows and retrieves results
- [ ] Handles both synchronous and asynchronous execution
- [ ] Supports workflow format conversion (workflow.json vs workflow_api.json)
- [ ] Manages generated image/video outputs
- [ ] Provides execution status to UI layer

### Technical Requirements
- [ ] Integrates `comfyui_api_client` library
- [ ] Implements wrapper class for Blender integration
- [ ] Thread-safe workflow execution
- [ ] Error handling for connection failures
- [ ] Workflow parameter validation
- [ ] Output file management
- [ ] Progress callback integration
- [ ] Proper cleanup on addon disable

### Quality Requirements
- [ ] Connection stable for extended sessions
- [ ] Workflow execution success rate >99%
- [ ] Clear error messages for failures
- [ ] No memory leaks during long sessions
- [ ] Unit tests cover main functionality
- [ ] Performance: workflow submission <100ms
- [ ] Generated files properly organized
- [ ] Thread-safe operations verified

## Implementation Notes

### Technical Approach

**ComfyUI Client Wrapper:**
```python
from comfyui_api_client import ComfyUIClient, ComfyUIClientAsync
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Callable

class BlenderComfyUIClient:
    def __init__(self, host: str = "localhost", port: int = 8188):
        self.host = host
        self.port = port
        self.url = f"{host}:{port}"
        self.client = None
        self.async_client = None
        self.workflows = {}
        self.output_dir = None
        
    def connect(self):
        """Initialize synchronous client connection"""
        try:
            # Test connection first
            import requests
            response = requests.get(f"http://{self.url}/system_stats", timeout=5)
            response.raise_for_status()
            
            # Connection successful
            self.client = ComfyUIClient(self.url)
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to ComfyUI: {e}")
            
    async def connect_async(self):
        """Initialize asynchronous client connection"""
        self.async_client = ComfyUIClientAsync(self.url)
        await self.async_client.connect()
        
    def load_workflow(self, workflow_path: Path, workflow_id: str = "default"):
        """Load and validate a workflow file"""
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_path}")
            
        # Create client with workflow
        self.workflows[workflow_id] = ComfyUIClient(self.url, str(workflow_path))
        self.workflows[workflow_id].connect()
        
        return workflow_id
```

**Workflow Execution:**
```python
def execute_workflow(self, 
                    workflow_id: str,
                    parameters: Dict[str, any],
                    output_nodes: List[str] = None,
                    progress_callback: Optional[Callable] = None):
    """Execute a workflow with given parameters"""
    
    if workflow_id not in self.workflows:
        raise ValueError(f"Workflow '{workflow_id}' not loaded")
        
    client = self.workflows[workflow_id]
    
    # Set parameters for workflow nodes
    for node_id, params in parameters.items():
        client.set_data(key=node_id, **params)
    
    # Execute and get results
    try:
        if progress_callback:
            # TODO: Implement progress tracking
            pass
            
        results = client.generate(node_names=output_nodes)
        
        # Process results
        output_files = []
        for node_name, outputs in results.items():
            if isinstance(outputs, list):
                for output in outputs:
                    if isinstance(output, (str, Path)):
                        output_files.append(output)
                        
        return {
            'status': 'success',
            'outputs': output_files,
            'node_results': results
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'outputs': []
        }
```

**Async Workflow Execution:**
```python
async def execute_workflow_async(self,
                               workflow_path: Path,
                               parameters: Dict[str, any],
                               output_nodes: List[str] = None):
    """Execute workflow asynchronously"""
    
    if not self.async_client:
        await self.connect_async()
        
    # Create async client for this workflow
    client = ComfyUIClientAsync(self.url, str(workflow_path))
    await client.connect()
    
    # Set parameters
    for node_id, params in parameters.items():
        await client.set_data(key=node_id, **params)
        
    # Execute asynchronously
    results = await client.generate(node_names=output_nodes)
    
    await client.close()
    
    return self._process_results(results)
```

**Blender Integration Helper:**
```python
class ComfyUIWorkflowManager:
    """Manages ComfyUI workflows for Blender addon"""
    
    def __init__(self, addon_prefs):
        self.prefs = addon_prefs
        self.client = BlenderComfyUIClient(
            host=self.prefs.comfyui_host,
            port=self.prefs.comfyui_port
        )
        self.workflow_cache = {}
        
    def get_workflow_for_task(self, task_type: str) -> str:
        """Get appropriate workflow for task type"""
        workflow_map = {
            'image_generation': 'workflows/sd_basic.json',
            'video_generation': 'workflows/ltx_video.json',
            'upscale': 'workflows/upscale_4x.json',
            'controlnet': 'workflows/controlnet_pose.json'
        }
        
        workflow_path = Path(workflow_map.get(task_type))
        
        if task_type not in self.workflow_cache:
            workflow_id = self.client.load_workflow(workflow_path, task_type)
            self.workflow_cache[task_type] = workflow_id
            
        return self.workflow_cache[task_type]
```

### Parameter Mapping
```python
def map_blender_to_comfyui_params(task_type: str, blender_props) -> Dict:
    """Map Blender properties to ComfyUI node parameters"""
    
    if task_type == 'image_generation':
        return {
            'KSampler': {
                'seed': blender_props.seed,
                'steps': blender_props.steps,
                'cfg': blender_props.cfg_scale,
                'denoise': blender_props.denoise_strength
            },
            'CLIPTextEncode': {
                'text': blender_props.prompt
            },
            'EmptyLatentImage': {
                'width': blender_props.width,
                'height': blender_props.height
            }
        }
    # Add more task type mappings...
```

### Error Handling
- Connection errors: Retry with backoff
- Workflow errors: Parse ComfyUI error messages
- File errors: Validate paths and permissions
- Parameter errors: Validate before submission

## Testing Strategy

### Unit Tests
```python
class TestComfyUIClient(unittest.TestCase):
    def test_connection(self):
        # Test connection to mock server
        
    def test_workflow_loading(self):
        # Test workflow file loading
        
    def test_parameter_setting(self):
        # Test parameter mapping
        
    def test_execution(self):
        # Test workflow execution
```

### Integration Tests
- Test with real ComfyUI instance
- Test various workflow types
- Test error scenarios
- Verify file outputs

## Dependencies
- STORY-001: Service Discovery (to find ComfyUI endpoint)
- `comfyui_api_client` Python package
- `requests` for HTTP communication
- `asyncio` for async operations

## Related Stories
- Used by STORY-009 (Connection Pool Manager)
- Monitored by STORY-010 (Health Check Service)
- Status shown in STORY-005 (Connection Status Panel)

## Definition of Done
- [ ] ComfyUI client integrated successfully
- [ ] Workflows load and execute correctly
- [ ] Parameter mapping works for all node types
- [ ] Error handling comprehensive
- [ ] Unit test coverage >90%
- [ ] Integration tests with real ComfyUI
- [ ] Documentation complete
- [ ] Performance targets met

---

**Sign-off:**
- [ ] Development Lead
- [ ] Backend Engineer
- [ ] QA Engineer