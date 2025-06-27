# User Story: HTTP Client for LiteLLM

**Story ID:** STORY-004  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Backend Client  
**Story Points:** 3  
**Priority:** Critical (P0)  

---

## Story Description

**As a** screenwriter using AI for narrative development  
**I want** a reliable HTTP connection to LiteLLM  
**So that** I can leverage LLMs for script analysis and generation  

## Acceptance Criteria

### Functional Requirements
- [ ] Establishes HTTP connection to LiteLLM API
- [ ] Supports both streaming and non-streaming responses
- [ ] Handles authentication (API key if configured)
- [ ] Sends properly formatted completion requests
- [ ] Receives and parses JSON responses
- [ ] Supports conversation context management
- [ ] Implements request retry logic
- [ ] Handles rate limiting appropriately

### Technical Requirements
- [ ] Uses `aiohttp` for async HTTP operations
- [ ] Connection pooling for efficiency
- [ ] Request/response logging capability
- [ ] Timeout configuration per request type
- [ ] Proper header management
- [ ] JSON schema validation
- [ ] Error response parsing
- [ ] SSL/TLS support

### Quality Requirements
- [ ] Response time <500ms for simple requests
- [ ] Connection pool reuse >80%
- [ ] Zero dropped requests under normal load
- [ ] Graceful handling of server errors
- [ ] Unit tests for all API methods
- [ ] Mock server for testing
- [ ] Clear error messages
- [ ] Thread-safe operations

## Implementation Notes

### Technical Approach

**LiteLLM HTTP Client:**
```python
import aiohttp
import asyncio
from typing import Dict, Any, Optional, AsyncIterator

class LiteLLMHTTPClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "BlenderMovieDirector/1.0"
        }
        
    async def connect(self):
        """Initialize HTTP session with connection pooling"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300
        )
        
        timeout = aiohttp.ClientTimeout(
            total=300,  # 5 minutes for long completions
            connect=5,
            sock_read=60
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        
    async def complete(self, 
                      model: str,
                      messages: List[Dict[str, str]],
                      **kwargs) -> Dict[str, Any]:
        """Send completion request to LiteLLM"""
        endpoint = f"{self.base_url}/v1/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs  # temperature, max_tokens, etc.
        }
        
        async with self.session.post(endpoint, json=payload) as response:
            response.raise_for_status()
            return await response.json()
```

**Streaming Support:**
```python
async def complete_stream(self, 
                         model: str,
                         messages: List[Dict[str, str]],
                         **kwargs) -> AsyncIterator[str]:
    """Stream completion responses"""
    endpoint = f"{self.base_url}/v1/completions"
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        **kwargs
    }
    
    async with self.session.post(endpoint, json=payload) as response:
        response.raise_for_status()
        
        async for line in response.content:
            if line.startswith(b'data: '):
                data = line[6:].decode('utf-8').strip()
                if data and data != '[DONE]':
                    chunk = json.loads(data)
                    yield chunk['choices'][0]['delta'].get('content', '')
```

**Error Handling:**
```python
class LiteLLMErrorHandler:
    async def handle_request(self, request_func, *args, **kwargs):
        """Wrapper for HTTP requests with retry logic"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                return await request_func(*args, **kwargs)
            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # Rate limited
                    retry_after = int(e.headers.get('Retry-After', retry_delay))
                    await asyncio.sleep(retry_after)
                elif e.status >= 500:  # Server error
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    # Client error, don't retry
                    raise LiteLLMClientError(f"API error: {e.status} - {e.message}")
            except aiohttp.ClientError as e:
                # Network error, retry
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    raise LiteLLMConnectionError(f"Connection failed: {e}")
```

### Blender Integration
- Client instance per addon session
- Non-blocking API calls
- Progress indication for long requests
- Response caching for repeated queries

### LiteLLM API Specifics
- OpenAI-compatible endpoint structure
- Model routing handled by LiteLLM
- Support for multiple model providers
- Token usage tracking

### Request Types
1. **Script Analysis**: Parse and structure scripts
2. **Dialogue Generation**: Create character dialogue
3. **Scene Description**: Expand scene details
4. **Creative Suggestions**: Plot and character ideas

## Testing Strategy

### Unit Tests
```python
class TestLiteLLMClient(unittest.TestCase):
    async def test_connection_pooling(self):
        # Verify connection reuse
        # Check pool statistics
        
    async def test_streaming_response(self):
        # Mock streaming endpoint
        # Verify chunk processing
        
    async def test_error_handling(self):
        # Test various HTTP errors
        # Verify retry behavior
```

### Integration Tests
- Test with local LiteLLM instance
- Verify all supported models
- Test rate limiting behavior
- Long-running request tests

## Dependencies
- STORY-001: Service Discovery (to find LiteLLM endpoint)
- `aiohttp` for async HTTP
- JSON schema validation library

## Related Stories
- Used by STORY-009 (Connection Pool Manager)
- Monitored by STORY-010 (Health Check Service)
- Status shown in STORY-005 (Connection Status Panel)
- Used by Screenwriter agent in EPIC-006

## Definition of Done
- [ ] HTTP connection established
- [ ] API requests work correctly
- [ ] Streaming responses functional
- [ ] Error handling comprehensive
- [ ] Connection pooling verified
- [ ] Unit tests >90% coverage
- [ ] Integration tests pass
- [ ] API documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] Backend Engineer
- [ ] QA Engineer