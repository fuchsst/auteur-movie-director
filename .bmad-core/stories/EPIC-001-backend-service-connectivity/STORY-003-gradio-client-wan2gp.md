# User Story: Gradio Client for Wan2GP

**Story ID:** STORY-003  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Backend Client  
**Story Points:** 5  
**Priority:** Critical (P0)  

---

## Story Description

**As a** content creator using Wan2GP for video generation  
**I want** a reliable Gradio client connection to Wan2GP  
**So that** I can generate videos with specialized models like CausVid  

## Acceptance Criteria

### Functional Requirements
- [ ] Establishes connection to Wan2GP Gradio interface
- [ ] Authenticates if required (API key support)
- [ ] Submits generation requests with proper parameters
- [ ] Handles file uploads for image/video inputs
- [ ] Receives generated outputs and downloads
- [ ] Tracks job progress and status
- [ ] Supports queue position updates
- [ ] Handles API rate limiting gracefully

### Technical Requirements
- [ ] Uses `gradio_client` Python library
- [ ] Implements async job submission
- [ ] File upload/download management
- [ ] Automatic retry on transient failures
- [ ] Connection pooling for efficiency
- [ ] Response caching where appropriate
- [ ] Timeout handling for long operations
- [ ] Proper resource cleanup

### Quality Requirements
- [ ] Connection reliability >99%
- [ ] File transfer integrity verified
- [ ] Clear progress reporting to user
- [ ] Graceful degradation on errors
- [ ] Unit tests for all client methods
- [ ] Integration tests with mock Gradio
- [ ] Performance: <1s connection time
- [ ] Memory efficient file handling

## Implementation Notes

### Technical Approach

**Wan2GP Gradio Client:**
```python
from gradio_client import Client
import asyncio
from pathlib import Path

class Wan2GPGradioClient:
    def __init__(self, url="http://localhost:7860"):
        self.url = url
        self.client = None
        self.connected = False
        self.job_queue = {}
        
    async def connect(self):
        """Initialize Gradio client connection"""
        try:
            self.client = Client(self.url)
            self.connected = True
            # Discover available functions
            self.api_info = self.client.view_api()
            return True
        except Exception as e:
            self.connected = False
            raise ConnectionError(f"Failed to connect to Wan2GP: {e}")
            
    async def generate_video(self, 
                           prompt: str,
                           model: str = "causvid",
                           **kwargs):
        """Submit video generation request"""
        if not self.connected:
            await self.connect()
            
        # Map parameters to Gradio interface
        job = self.client.submit(
            prompt,
            model,
            kwargs.get('num_frames', 32),
            kwargs.get('resolution', '512x512'),
            fn_index=0  # Assuming first function is generate
        )
        
        # Track job
        job_id = str(job)
        self.job_queue[job_id] = job
        
        return job_id
```

**Job Management:**
```python
class Wan2GPJobManager:
    async def wait_for_completion(self, job_id: str):
        """Wait for job completion with progress updates"""
        job = self.job_queue.get(job_id)
        if not job:
            raise ValueError(f"Unknown job: {job_id}")
            
        while not job.done():
            # Get progress if available
            progress = getattr(job, 'progress', None)
            if progress:
                await self._update_progress(job_id, progress)
            await asyncio.sleep(1)
            
        # Get result
        result = job.result()
        return self._process_result(result)
```

**File Handling:**
```python
class Wan2GPFileHandler:
    def prepare_input_file(self, file_path: Path):
        """Prepare file for upload to Gradio"""
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
            
        # Validate file type and size
        self._validate_file(file_path)
        
        # Return file handle for Gradio
        return open(file_path, 'rb')
        
    async def download_output(self, output_url: str, 
                            destination: Path):
        """Download generated content from Gradio"""
        # Handle both file paths and URLs
        if output_url.startswith('http'):
            await self._download_from_url(output_url, destination)
        else:
            # Local file path from Gradio
            shutil.copy(output_url, destination)
```

### Blender Integration
- Client runs in separate thread
- Progress updates via callbacks
- File management integrated with asset system
- Status shown in connection panel

### Wan2GP Specifics
- Supports multiple model types (CausVid, etc.)
- Handles model-specific parameters
- Queue position tracking
- GPU allocation awareness

### Error Handling
- Connection failures: Retry with backoff
- Queue timeouts: Notify user
- File transfer errors: Verify and retry
- Model errors: Parse and display

## Testing Strategy

### Unit Tests
```python
class TestWan2GPClient(unittest.TestCase):
    def test_connection_establishment(self):
        # Mock Gradio server
        # Verify connection success
        
    def test_job_submission(self):
        # Submit test job
        # Verify job tracking
        
    def test_file_handling(self):
        # Test upload/download
        # Verify integrity
```

### Integration Tests
- Test with Wan2GP test instance
- Verify all model types
- Test queue behavior
- Long-running job tests

## Dependencies
- STORY-001: Service Discovery (to find Wan2GP endpoint)
- `gradio_client` Python package
- File system access for uploads/downloads

## Related Stories
- Used by STORY-009 (Connection Pool Manager)
- Monitored by STORY-010 (Health Check Service)
- Status shown in STORY-005 (Connection Status Panel)

## Definition of Done
- [ ] Gradio connection established
- [ ] Job submission works correctly
- [ ] Progress tracking functional
- [ ] File upload/download verified
- [ ] Error handling comprehensive
- [ ] Unit tests >90% coverage
- [ ] Integration tests pass
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] Backend Engineer
- [ ] QA Engineer