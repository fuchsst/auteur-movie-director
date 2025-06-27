# User Story: Connection Test Suite

**Story ID:** STORY-015  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Testing & Quality  
**Story Points:** 5  
**Priority:** High (P1)  

---

## Story Description

**As a** developer working on backend connectivity  
**I want** comprehensive unit tests for all connection components  
**So that** I can ensure reliability and catch regressions early  

## Acceptance Criteria

### Functional Requirements
- [ ] Unit tests for service discovery logic
- [ ] Tests for each backend client type (WebSocket, HTTP, Gradio)
- [ ] Connection pool manager tests
- [ ] Health check service tests
- [ ] Reconnection logic tests
- [ ] Configuration loading tests
- [ ] Error handling tests
- [ ] Mock implementations for all backends

### Technical Requirements
- [ ] pytest test framework setup
- [ ] Mock backend servers
- [ ] Async test support
- [ ] Test coverage >90%
- [ ] Performance benchmarks
- [ ] Memory leak detection
- [ ] Thread safety tests
- [ ] CI/CD integration ready

### Quality Requirements
- [ ] Tests run in <30 seconds
- [ ] Zero flaky tests
- [ ] Clear test naming
- [ ] Comprehensive assertions
- [ ] Isolated test cases
- [ ] Reproducible results
- [ ] Good error messages
- [ ] Documentation for test setup

## Implementation Notes

### Technical Approach

**Test Framework Setup:**
```python
# tests/conftest.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import bpy

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_blender_context():
    """Mock Blender context for tests"""
    context = Mock()
    context.scene = Mock()
    context.scene.movie_director_props = Mock()
    return context

@pytest.fixture
async def mock_websocket_server():
    """Mock WebSocket server for ComfyUI tests"""
    from websockets.server import serve
    
    async def handler(websocket, path):
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'system_stats':
                await websocket.send(json.dumps({
                    'type': 'stats',
                    'version': '1.0.0',
                    'vram_free': 8192,
                    'models': ['sd-1.5', 'sdxl']
                }))
    
    server = await serve(handler, 'localhost', 8188)
    yield server
    server.close()
    await server.wait_closed()
```

**Service Discovery Tests:**
```python
# tests/test_service_discovery.py
import pytest
from movie_director.connectivity import ServiceDiscoveryManager

class TestServiceDiscovery:
    @pytest.mark.asyncio
    async def test_discover_all_services_success(self, mock_services):
        """Test successful discovery of all services"""
        discovery = ServiceDiscoveryManager()
        
        # Mock service responses
        mock_services.setup_all_healthy()
        
        # Run discovery
        results = await discovery.discover_all_services()
        
        # Verify all services found
        assert len(results) == 5
        assert all(r['discovered'] for r in results.values())
        assert results['comfyui']['endpoint'] == 'ws://localhost:8188'
        
    @pytest.mark.asyncio
    async def test_discover_with_custom_ports(self):
        """Test discovery with non-default ports"""
        discovery = ServiceDiscoveryManager()
        discovery.services['comfyui']['custom_ports'] = [8189, 8190]
        
        # Mock service on custom port
        with mock_service_on_port(8189):
            results = await discovery.discover_all_services()
            
        assert results['comfyui']['endpoint'] == 'ws://localhost:8189'
        
    @pytest.mark.asyncio
    async def test_discovery_timeout(self):
        """Test timeout handling during discovery"""
        discovery = ServiceDiscoveryManager()
        discovery.timeout = 0.1  # Very short timeout
        
        # No services running
        results = await discovery.discover_all_services()
        
        # Verify timeout handled gracefully
        assert all(not r['discovered'] for r in results.values())
        assert all(r['error'] == 'timeout' for r in results.values())
        
    def test_discovery_parallel_execution(self):
        """Verify services discovered in parallel"""
        import time
        
        discovery = ServiceDiscoveryManager()
        
        # Mock slow service checks
        async def slow_check(service):
            await asyncio.sleep(1)
            return {'discovered': True}
            
        discovery.discover_service = slow_check
        
        # Time parallel discovery
        start = time.time()
        asyncio.run(discovery.discover_all_services())
        duration = time.time() - start
        
        # Should complete in ~1 second, not 5
        assert duration < 2.0
```

**WebSocket Client Tests:**
```python
# tests/test_websocket_client.py
class TestComfyUIWebSocketClient:
    @pytest.mark.asyncio
    async def test_connection_establishment(self, mock_websocket_server):
        """Test WebSocket connection to ComfyUI"""
        client = ComfyUIWebSocketClient()
        
        await client.connect()
        
        assert client.state == ConnectionState.CONNECTED
        assert client.websocket is not None
        
    @pytest.mark.asyncio
    async def test_message_sending(self, mock_websocket_server):
        """Test sending workflow to ComfyUI"""
        client = ComfyUIWebSocketClient()
        await client.connect()
        
        # Send workflow
        workflow = {'prompt': 'test workflow'}
        response = await client.send_workflow(workflow)
        
        assert response['status'] == 'queued'
        assert 'job_id' in response
        
    @pytest.mark.asyncio
    async def test_reconnection_on_disconnect(self):
        """Test automatic reconnection logic"""
        client = ComfyUIWebSocketClient()
        
        # Connect to mock server
        with mock_websocket_server() as server:
            await client.connect()
            assert client.state == ConnectionState.CONNECTED
            
            # Simulate disconnect
            server.close()
            await asyncio.sleep(0.1)
            
            # Verify reconnection attempted
            assert client.state == ConnectionState.RECONNECTING
            
    @pytest.mark.asyncio  
    async def test_message_queue_during_disconnect(self):
        """Test message queuing while disconnected"""
        client = ComfyUIWebSocketClient()
        
        # Queue messages while disconnected
        await client.send_workflow({'prompt': 'test1'})
        await client.send_workflow({'prompt': 'test2'})
        
        assert client.message_queue.qsize() == 2
        
        # Connect and verify queue drains
        with mock_websocket_server():
            await client.connect()
            await asyncio.sleep(0.1)
            
        assert client.message_queue.empty()
```

**Connection Pool Tests:**
```python
# tests/test_connection_pool.py
class TestConnectionPoolManager:
    @pytest.mark.asyncio
    async def test_connection_pooling(self):
        """Test connection reuse from pool"""
        pool_manager = ConnectionPoolManager()
        await pool_manager.initialize()
        
        # Get connection twice
        conn1 = await pool_manager.get_connection('litellm')
        await pool_manager.release_connection('litellm', conn1)
        
        conn2 = await pool_manager.get_connection('litellm')
        
        # Should reuse same connection
        assert conn1 is conn2
        
    @pytest.mark.asyncio
    async def test_pool_size_limits(self):
        """Test pool respects size limits"""
        pool_manager = ConnectionPoolManager()
        pool_manager.configs['litellm'].max_connections = 2
        await pool_manager.initialize()
        
        # Acquire max connections
        conns = []
        for _ in range(2):
            conn = await pool_manager.get_connection('litellm')
            conns.append(conn)
            
        # Third should wait or fail
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                pool_manager.get_connection('litellm'),
                timeout=0.1
            )
            
    def test_thread_safety(self):
        """Test concurrent access to pool"""
        import threading
        
        pool_manager = ConnectionPoolManager()
        asyncio.run(pool_manager.initialize())
        
        errors = []
        
        def worker():
            try:
                for _ in range(10):
                    conn = asyncio.run(pool_manager.get_connection('litellm'))
                    asyncio.run(pool_manager.release_connection('litellm', conn))
            except Exception as e:
                errors.append(e)
                
        # Run concurrent workers
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        assert len(errors) == 0
```

**Health Check Tests:**
```python
# tests/test_health_check.py
class TestHealthCheckService:
    @pytest.mark.asyncio
    async def test_health_check_execution(self):
        """Test health checks run for all services"""
        health_service = HealthCheckService()
        
        # Mock health check functions
        health_service.health_checkers = {
            'comfyui': AsyncMock(return_value={'healthy': True}),
            'litellm': AsyncMock(return_value={'healthy': True})
        }
        
        await health_service.start()
        await asyncio.sleep(0.1)
        
        # Verify checks called
        assert all(checker.called for checker in health_service.health_checkers.values())
        
    @pytest.mark.asyncio
    async def test_status_transitions(self):
        """Test health status state machine"""
        health_service = HealthCheckService()
        
        # Simulate failures
        results = [
            {'healthy': True},   # -> HEALTHY
            {'healthy': False},  # -> DEGRADED
            {'healthy': False},  # -> DEGRADED
            {'healthy': False},  # -> UNHEALTHY (3rd failure)
            {'healthy': True},   # -> HEALTHY
        ]
        
        states = []
        for result in results:
            await health_service._update_health_state('test_service', result)
            states.append(health_service.health_states['test_service'].status)
            
        assert states == [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
            HealthStatus.HEALTHY
        ]
```

**Mock Backend Implementations:**
```python
# tests/mocks/mock_backends.py
class MockComfyUI:
    """Mock ComfyUI server for testing"""
    
    def __init__(self, port=8188):
        self.port = port
        self.workflows = {}
        self.responses = {}
        
    async def start(self):
        """Start mock WebSocket server"""
        async def handler(websocket, path):
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        self.server = await websockets.serve(handler, 'localhost', self.port)
        
    async def handle_message(self, websocket, message):
        """Process incoming messages"""
        data = json.loads(message)
        
        if data['type'] == 'execute':
            job_id = str(uuid.uuid4())
            self.workflows[job_id] = data['workflow']
            
            await websocket.send(json.dumps({
                'type': 'execution_start',
                'job_id': job_id
            }))
            
class MockLiteLLM:
    """Mock LiteLLM HTTP server"""
    
    def __init__(self, port=8000):
        self.app = web.Application()
        self.app.router.add_post('/v1/completions', self.handle_completion)
        self.app.router.add_get('/health', self.handle_health)
        
    async def handle_completion(self, request):
        """Mock completion endpoint"""
        data = await request.json()
        
        return web.json_response({
            'id': 'mock-completion',
            'choices': [{
                'text': 'Mock response',
                'finish_reason': 'stop'
            }]
        })
```

**Performance Tests:**
```python
# tests/test_performance.py
class TestPerformance:
    @pytest.mark.benchmark
    def test_service_discovery_performance(self, benchmark):
        """Benchmark service discovery"""
        discovery = ServiceDiscoveryManager()
        
        result = benchmark(
            lambda: asyncio.run(discovery.discover_all_services())
        )
        
        # Should complete quickly
        assert benchmark.stats['mean'] < 5.0  # seconds
        
    @pytest.mark.benchmark
    def test_connection_pool_performance(self, benchmark):
        """Benchmark connection acquisition"""
        pool = ConnectionPool('test', ConnectionConfig())
        asyncio.run(pool.initialize())
        
        def acquire_release():
            conn = asyncio.run(pool.acquire())
            asyncio.run(pool.release(conn))
            
        benchmark(acquire_release)
        
        # Should be very fast
        assert benchmark.stats['mean'] < 0.001  # 1ms
```

### Test Organization
```
tests/
├── unit/
│   ├── test_service_discovery.py
│   ├── test_websocket_client.py
│   ├── test_http_client.py
│   ├── test_gradio_client.py
│   ├── test_connection_pool.py
│   ├── test_health_check.py
│   ├── test_reconnection.py
│   └── test_configuration.py
├── integration/
│   ├── test_full_connection_flow.py
│   └── test_multi_backend.py
├── mocks/
│   ├── mock_backends.py
│   └── mock_services.py
├── fixtures/
│   └── test_configs.yaml
└── conftest.py
```

## Testing Strategy

### Unit Test Coverage
- Service discovery: 95%
- Client implementations: 90%
- Connection pool: 95%
- Health checks: 90%
- Configuration: 85%

### Test Execution
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=movie_director.connectivity tests/

# Run specific test file
pytest tests/unit/test_service_discovery.py

# Run async tests
pytest -m asyncio tests/
```

## Dependencies
- pytest and pytest-asyncio
- pytest-cov for coverage
- pytest-benchmark for performance
- Mock libraries
- Test fixtures

## Related Stories
- Tests all stories in EPIC-001
- Provides confidence for deployment
- Enables refactoring

## Definition of Done
- [ ] All components have unit tests
- [ ] Test coverage >90%
- [ ] Mock backends implemented
- [ ] Async tests working
- [ ] Performance tests included
- [ ] No flaky tests
- [ ] CI/CD ready
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] QA Lead
- [ ] Backend Engineer