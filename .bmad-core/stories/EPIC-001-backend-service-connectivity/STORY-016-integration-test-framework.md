# User Story: Integration Test Framework

**Story ID:** STORY-016  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Testing & Quality  
**Story Points:** 8  
**Priority:** High (P1)  

---

## Story Description

**As a** QA engineer validating the complete system  
**I want** integration tests that verify end-to-end connectivity flows  
**So that** I can ensure all components work together correctly  

## Acceptance Criteria

### Functional Requirements
- [ ] End-to-end connection establishment tests
- [ ] Multi-backend coordination tests
- [ ] Failure recovery scenario tests
- [ ] Configuration change tests
- [ ] UI interaction tests
- [ ] Performance under load tests
- [ ] Network disruption tests
- [ ] Test environment setup automation

### Technical Requirements
- [ ] Docker-based test backends
- [ ] Network simulation tools
- [ ] Blender addon test harness
- [ ] Test data generators
- [ ] Result reporting system
- [ ] Parallel test execution
- [ ] Test environment cleanup
- [ ] CI/CD pipeline integration

### Quality Requirements
- [ ] Tests complete in <10 minutes
- [ ] Reproducible test results
- [ ] Clear failure diagnostics
- [ ] Minimal test flakiness
- [ ] Resource usage monitoring
- [ ] Test isolation guaranteed
- [ ] Comprehensive logging
- [ ] Easy local development

## Implementation Notes

### Technical Approach

**Test Environment Setup:**
```python
# tests/integration/docker-compose.yml
version: '3.8'
services:
  comfyui:
    image: comfyui/comfyui:latest
    ports:
      - "8188:8188"
    volumes:
      - ./test-models:/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8188/system_stats"]
      interval: 5s
      retries: 5
      
  litellm:
    image: ghcr.io/berriai/litellm:latest
    ports:
      - "8000:8000"
    environment:
      - LITELLM_MODE=mock
      - MOCK_RESPONSE=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      
  wan2gp:
    build:
      context: ./mock-wan2gp
    ports:
      - "7860:7860"
      
  test-network:
    image: networkstatic/iperf3
    networks:
      - test-net
```

**Integration Test Base Class:**
```python
# tests/integration/base.py
import pytest
import docker
import asyncio
from pathlib import Path

class IntegrationTestBase:
    """Base class for integration tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.docker_client = docker.from_env()
        cls.compose_file = Path(__file__).parent / 'docker-compose.yml'
        
        # Start test backends
        cls.start_test_backends()
        
        # Wait for services to be ready
        cls.wait_for_backends()
        
        # Initialize Blender addon
        cls.setup_blender_addon()
        
    @classmethod
    def start_test_backends(cls):
        """Start Docker containers for test backends"""
        import subprocess
        
        subprocess.run([
            'docker-compose',
            '-f', str(cls.compose_file),
            'up', '-d'
        ], check=True)
        
    @classmethod
    def wait_for_backends(cls, timeout=60):
        """Wait for all backends to be healthy"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if cls.all_backends_healthy():
                return
            time.sleep(1)
            
        raise TimeoutError("Backends failed to start")
        
    @classmethod
    def all_backends_healthy(cls):
        """Check if all backend containers are healthy"""
        containers = cls.docker_client.containers.list()
        
        for container in containers:
            if container.name.startswith('integration_'):
                health = container.attrs['State']['Health']['Status']
                if health != 'healthy':
                    return False
                    
        return True
```

**End-to-End Connection Tests:**
```python
# tests/integration/test_e2e_connection.py
class TestEndToEndConnection(IntegrationTestBase):
    
    @pytest.mark.integration
    async def test_full_connection_flow(self):
        """Test complete connection establishment flow"""
        # 1. Service Discovery
        discovery = ServiceDiscoveryManager()
        results = await discovery.discover_all_services()
        
        assert all(r['discovered'] for r in results.values())
        
        # 2. Connection Pool Initialization
        pool_manager = ConnectionPoolManager()
        await pool_manager.initialize()
        
        # 3. Health Checks
        health_service = HealthCheckService()
        await health_service.start()
        await asyncio.sleep(2)  # Let health checks run
        
        # 4. Verify all services healthy
        system_health = health_service.get_system_health()
        assert system_health == HealthStatus.HEALTHY
        
        # 5. Test actual operations
        # ComfyUI workflow
        comfyui_conn = await pool_manager.get_connection('comfyui')
        workflow_result = await comfyui_conn.send_workflow({
            'prompt': 'test workflow'
        })
        assert workflow_result['status'] == 'queued'
        
        # LiteLLM completion
        litellm_conn = await pool_manager.get_connection('litellm')
        completion = await litellm_conn.complete(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': 'Hello'}]
        )
        assert 'choices' in completion
        
    @pytest.mark.integration
    async def test_ui_to_backend_flow(self):
        """Test UI interaction triggering backend operations"""
        # Set up Blender context
        context = setup_test_blender_context()
        
        # Simulate UI action - refresh connections
        bpy.ops.movie_director.refresh_connections()
        
        # Wait for discovery
        await asyncio.sleep(3)
        
        # Check UI properties updated
        props = context.scene.movie_director_props
        assert props.comfyui_connection.status == 'connected'
        assert props.litellm_connection.status == 'connected'
        
        # Simulate configuration change
        props.comfyui_connection.url = 'ws://localhost:8189'
        
        # Trigger reconnection
        bpy.ops.movie_director.manual_reconnect(service='comfyui')
        
        # Verify reconnection attempted
        await asyncio.sleep(2)
        # Should fail (wrong port)
        assert props.comfyui_connection.status == 'error'
```

**Multi-Backend Coordination Tests:**
```python
# tests/integration/test_multi_backend.py
class TestMultiBackendCoordination(IntegrationTestBase):
    
    @pytest.mark.integration
    async def test_parallel_backend_operations(self):
        """Test multiple backends working in parallel"""
        pool_manager = ConnectionPoolManager()
        await pool_manager.initialize()
        
        # Launch parallel operations
        tasks = [
            self.generate_image_comfyui(pool_manager),
            self.generate_text_litellm(pool_manager),
            self.generate_video_wan2gp(pool_manager)
        ]
        
        # All should complete successfully
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        assert all(not isinstance(r, Exception) for r in results)
        assert results[0]['type'] == 'image'
        assert results[1]['type'] == 'text'
        assert results[2]['type'] == 'video'
        
    async def generate_image_comfyui(self, pool_manager):
        """Generate image via ComfyUI"""
        conn = await pool_manager.get_connection('comfyui')
        
        workflow = {
            'prompt': 'A beautiful landscape',
            'model': 'sd-1.5',
            'steps': 20
        }
        
        result = await conn.send_workflow(workflow)
        
        # Wait for completion
        while True:
            status = await conn.get_job_status(result['job_id'])
            if status['completed']:
                break
            await asyncio.sleep(0.5)
            
        return {'type': 'image', 'result': status['output']}
```

**Failure Recovery Tests:**
```python
# tests/integration/test_failure_recovery.py
class TestFailureRecovery(IntegrationTestBase):
    
    @pytest.mark.integration
    async def test_backend_crash_recovery(self):
        """Test recovery when backend crashes"""
        # Establish connections
        pool_manager = ConnectionPoolManager()
        await pool_manager.initialize()
        
        # Verify connected
        conn = await pool_manager.get_connection('comfyui')
        assert conn is not None
        
        # Kill ComfyUI container
        container = self.get_container('comfyui')
        container.stop()
        
        # Wait for detection
        await asyncio.sleep(35)  # Health check interval
        
        # Verify disconnected state
        health_service = get_health_service()
        assert health_service.health_states['comfyui'].status == HealthStatus.UNHEALTHY
        
        # Restart container
        container.start()
        
        # Wait for recovery
        await asyncio.sleep(10)
        
        # Verify reconnected
        assert health_service.health_states['comfyui'].status == HealthStatus.HEALTHY
        
        # Verify operations resume
        conn = await pool_manager.get_connection('comfyui')
        result = await conn.send_workflow({'prompt': 'test'})
        assert result['status'] == 'queued'
        
    @pytest.mark.integration
    async def test_network_disruption(self):
        """Test handling of network issues"""
        # Use network simulation
        network_sim = NetworkSimulator()
        
        # Add latency
        network_sim.add_latency('comfyui', 500)  # 500ms
        
        # Operations should still work but slower
        start = time.time()
        conn = await pool_manager.get_connection('comfyui')
        result = await conn.send_workflow({'prompt': 'test'})
        duration = time.time() - start
        
        assert duration > 0.5  # Latency applied
        assert result is not None
        
        # Add packet loss
        network_sim.add_packet_loss('comfyui', 50)  # 50% loss
        
        # Should trigger retries
        with pytest.raises(ConnectionError):
            await conn.send_workflow({'prompt': 'test'})
```

**Performance and Load Tests:**
```python
# tests/integration/test_performance.py
class TestPerformanceUnderLoad(IntegrationTestBase):
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_user_load(self):
        """Test system under concurrent user load"""
        pool_manager = ConnectionPoolManager()
        await pool_manager.initialize()
        
        # Simulate 50 concurrent users
        async def user_workflow(user_id):
            """Simulate single user workflow"""
            # Discovery
            discovery = ServiceDiscoveryManager()
            await discovery.discover_all_services()
            
            # Generate content
            conn = await pool_manager.get_connection('litellm')
            result = await conn.complete(
                model='gpt-3.5-turbo',
                messages=[{'role': 'user', 'content': f'User {user_id} request'}]
            )
            
            return result
            
        # Run concurrent users
        tasks = [user_workflow(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check success rate
        successes = sum(1 for r in results if not isinstance(r, Exception))
        success_rate = successes / len(results)
        
        assert success_rate > 0.95  # 95% success rate
        
        # Check resource usage
        stats = pool_manager.get_statistics()
        assert stats['connection_reuse_rate'] > 0.8
        assert stats['avg_acquisition_time'] < 0.1  # 100ms
```

**Test Utilities:**
```python
# tests/integration/utils.py
class NetworkSimulator:
    """Simulate network conditions"""
    
    def add_latency(self, service: str, latency_ms: int):
        """Add network latency to service"""
        subprocess.run([
            'docker', 'exec', f'integration_{service}_1',
            'tc', 'qdisc', 'add', 'dev', 'eth0',
            'root', 'netem', 'delay', f'{latency_ms}ms'
        ])
        
    def add_packet_loss(self, service: str, loss_percent: int):
        """Add packet loss to service"""
        subprocess.run([
            'docker', 'exec', f'integration_{service}_1',
            'tc', 'qdisc', 'add', 'dev', 'eth0',
            'root', 'netem', 'loss', f'{loss_percent}%'
        ])
        
class TestDataGenerator:
    """Generate test data for backends"""
    
    def generate_test_workflow(self, complexity='medium'):
        """Generate ComfyUI workflow for testing"""
        workflows = {
            'simple': {
                'nodes': 5,
                'model': 'sd-1.5',
                'steps': 20
            },
            'medium': {
                'nodes': 15,
                'model': 'sdxl',
                'steps': 30
            },
            'complex': {
                'nodes': 50,
                'model': 'sdxl',
                'steps': 50,
                'controlnet': True
            }
        }
        
        return workflows[complexity]
```

**CI/CD Integration:**
```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  pull_request:
    paths:
      - 'movie_director/connectivity/**'
      - 'tests/integration/**'

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
        
    - name: Start test backends
      run: |
        docker-compose -f tests/integration/docker-compose.yml up -d
        
    - name: Wait for backends
      run: |
        python tests/integration/wait_for_backends.py
        
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v --tb=short
        
    - name: Collect logs on failure
      if: failure()
      run: |
        docker-compose -f tests/integration/docker-compose.yml logs
        
    - name: Cleanup
      if: always()
      run: |
        docker-compose -f tests/integration/docker-compose.yml down -v
```

## Testing Strategy

### Test Scenarios
1. **Happy Path**: All services available and healthy
2. **Partial Failure**: Some services unavailable
3. **Recovery**: Services recover after failure
4. **Load**: System under concurrent load
5. **Network Issues**: Latency and packet loss
6. **Configuration Changes**: Dynamic reconfiguration

### Test Execution
```bash
# Run all integration tests
pytest tests/integration/ -m integration

# Run specific test
pytest tests/integration/test_e2e_connection.py

# Run with specific backend versions
COMFYUI_VERSION=latest pytest tests/integration/

# Run performance tests
pytest tests/integration/ -m slow
```

## Dependencies
- Docker and docker-compose
- Test backend images
- Network simulation tools
- pytest integration plugins
- Blender test harness

## Related Stories
- Integrates all EPIC-001 components
- Validates complete system
- Enables confident deployment

## Definition of Done
- [ ] Docker test environment working
- [ ] E2E tests covering main flows
- [ ] Failure recovery tests passing
- [ ] Performance tests established
- [ ] CI/CD pipeline integrated
- [ ] Test documentation complete
- [ ] Resource cleanup verified
- [ ] Results reporting system ready

---

**Sign-off:**
- [ ] QA Lead
- [ ] DevOps Engineer
- [ ] Development Lead