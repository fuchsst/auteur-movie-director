# User Story: Health Check Service

**Story ID:** STORY-010  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Backend Integration  
**Story Points:** 5  
**Priority:** High (P1)  

---

## Story Description

**As the** connection management system  
**I want** continuous health monitoring of all backend services  
**So that** I can detect issues early and maintain system reliability  

## Acceptance Criteria

### Functional Requirements
- [ ] Perform periodic health checks on all services
- [ ] Detect service availability changes within 30 seconds
- [ ] Check service-specific health endpoints
- [ ] Verify service capabilities and versions
- [ ] Track health check history
- [ ] Trigger reconnection on recovery
- [ ] Support custom health check intervals
- [ ] Aggregate health status across services

### Technical Requirements
- [ ] Async health check execution
- [ ] Non-blocking health checks
- [ ] Configurable check intervals per service
- [ ] Timeout handling for slow services
- [ ] Health state machine implementation
- [ ] Event-driven status changes
- [ ] Thread-safe status updates
- [ ] Minimal performance overhead

### Quality Requirements
- [ ] Health checks complete <2s per service
- [ ] False positive rate <1%
- [ ] Status accuracy >99%
- [ ] Memory usage <5MB for history
- [ ] No impact on normal operations
- [ ] Clear health state definitions
- [ ] Comprehensive logging
- [ ] Graceful degradation

## Implementation Notes

### Technical Approach

**Health Check Service Architecture:**
```python
from enum import Enum
from typing import Dict, List, Callable, Optional
import asyncio

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ServiceHealth:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.status = HealthStatus.UNKNOWN
        self.last_check_time = 0
        self.last_success_time = 0
        self.consecutive_failures = 0
        self.response_time = 0
        self.version = None
        self.capabilities = {}
        self.error_message = None
        
class HealthCheckService:
    def __init__(self):
        self.health_states: Dict[str, ServiceHealth] = {}
        self.check_intervals: Dict[str, float] = {}
        self.health_checkers: Dict[str, Callable] = {}
        self.status_callbacks: List[Callable] = []
        self._running = False
        self._tasks = {}
        
    async def start(self):
        """Start health monitoring for all services"""
        self._running = True
        
        for service in BACKEND_SERVICES:
            # Initialize health state
            self.health_states[service] = ServiceHealth(service)
            
            # Start health check task
            task = asyncio.create_task(
                self._health_check_loop(service)
            )
            self._tasks[service] = task
```

**Service-Specific Health Checkers:**
```python
async def check_comfyui_health(self, url: str) -> Dict:
    """Health check for ComfyUI WebSocket service"""
    try:
        start_time = time.time()
        
        # Test WebSocket connection
        async with websockets.connect(url, timeout=5) as ws:
            # Send system stats request
            await ws.send(json.dumps({
                "type": "system_stats"
            }))
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(response)
            
            return {
                'healthy': True,
                'response_time': time.time() - start_time,
                'version': data.get('version'),
                'capabilities': {
                    'models': data.get('models', []),
                    'vram_available': data.get('vram_free'),
                    'queue_size': data.get('queue_size', 0)
                }
            }
            
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'response_time': time.time() - start_time
        }

async def check_litellm_health(self, url: str) -> Dict:
    """Health check for LiteLLM HTTP service"""
    try:
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                data = await response.json()
                
                return {
                    'healthy': response.status == 200,
                    'response_time': time.time() - start_time,
                    'version': data.get('version'),
                    'capabilities': {
                        'models': data.get('models', []),
                        'rate_limit': data.get('rate_limit')
                    }
                }
                
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'response_time': time.time() - start_time
        }
```

**Health Check Loop:**
```python
async def _health_check_loop(self, service: str):
    """Continuous health check loop for a service"""
    interval = self.check_intervals.get(service, 30)
    checker = self.health_checkers.get(service)
    
    while self._running:
        try:
            # Perform health check
            result = await checker()
            
            # Update health state
            await self._update_health_state(service, result)
            
        except Exception as e:
            logger.error(f"Health check error for {service}: {e}")
            
            # Mark as unhealthy on check failure
            await self._update_health_state(service, {
                'healthy': False,
                'error': str(e)
            })
            
        # Wait for next check
        await asyncio.sleep(interval)
```

**Health State Management:**
```python
async def _update_health_state(self, service: str, result: Dict):
    """Update service health state based on check result"""
    health = self.health_states[service]
    previous_status = health.status
    
    # Update basic info
    health.last_check_time = time.time()
    health.response_time = result.get('response_time', 0)
    
    if result['healthy']:
        health.last_success_time = time.time()
        health.consecutive_failures = 0
        health.error_message = None
        health.version = result.get('version')
        health.capabilities = result.get('capabilities', {})
        
        # Determine health status
        if health.response_time < 1.0:
            health.status = HealthStatus.HEALTHY
        else:
            health.status = HealthStatus.DEGRADED
            
    else:
        health.consecutive_failures += 1
        health.error_message = result.get('error')
        
        # Determine severity
        if health.consecutive_failures >= 3:
            health.status = HealthStatus.UNHEALTHY
        else:
            health.status = HealthStatus.DEGRADED
            
    # Notify if status changed
    if health.status != previous_status:
        await self._notify_status_change(service, previous_status, health.status)
```

**Status Change Notifications:**
```python
async def _notify_status_change(self, 
                               service: str, 
                               old_status: HealthStatus,
                               new_status: HealthStatus):
    """Notify listeners of health status changes"""
    
    # Log status change
    logger.info(f"{service}: {old_status.value} -> {new_status.value}")
    
    # Call registered callbacks
    for callback in self.status_callbacks:
        try:
            await callback(service, old_status, new_status)
        except Exception as e:
            logger.error(f"Callback error: {e}")
            
    # Trigger UI update
    if hasattr(bpy.ops.movie_director, 'update_service_status'):
        bpy.ops.movie_director.update_service_status(
            service=service,
            status=new_status.value
        )
```

**Aggregated Health Status:**
```python
def get_system_health(self) -> HealthStatus:
    """Get overall system health status"""
    if not self.health_states:
        return HealthStatus.UNKNOWN
        
    statuses = [h.status for h in self.health_states.values()]
    
    # System is unhealthy if any critical service is unhealthy
    critical_services = ['comfyui', 'litellm']
    for service in critical_services:
        if self.health_states[service].status == HealthStatus.UNHEALTHY:
            return HealthStatus.UNHEALTHY
            
    # System is degraded if any service is degraded/unhealthy
    if any(s in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY] for s in statuses):
        return HealthStatus.DEGRADED
        
    # System is healthy only if all services are healthy
    if all(s == HealthStatus.HEALTHY for s in statuses):
        return HealthStatus.HEALTHY
        
    return HealthStatus.UNKNOWN
```

### Health Check Configuration
```python
HEALTH_CHECK_CONFIG = {
    'comfyui': {
        'interval': 30,
        'timeout': 5,
        'endpoint': '/system_stats'
    },
    'litellm': {
        'interval': 30,
        'timeout': 5,
        'endpoint': '/health'
    },
    'wan2gp': {
        'interval': 60,  # Less frequent for Gradio
        'timeout': 10,
        'endpoint': '/api/health'
    }
}
```

## Testing Strategy

### Unit Tests
```python
class TestHealthCheckService(unittest.TestCase):
    async def test_health_check_execution(self):
        # Mock backend responses
        # Verify health checks run
        
    async def test_status_transitions(self):
        # Test state machine
        # Verify correct transitions
        
    async def test_failure_detection(self):
        # Simulate failures
        # Verify detection time
```

### Integration Tests
- Test with real services
- Simulate service outages
- Verify recovery detection
- Test notification system

## Dependencies
- STORY-001: Service discovery provides endpoints
- STORY-009: Uses connection pool for checks
- Backend services must implement health endpoints

## Related Stories
- Provides data to STORY-005 (Status Panel)
- Feeds STORY-008 (Health Dashboard)
- Triggers STORY-011 (Auto Reconnection)

## Definition of Done
- [ ] Health checks running for all services
- [ ] Status changes detected <30s
- [ ] Health history tracked
- [ ] Notifications working
- [ ] Aggregated status accurate
- [ ] Performance overhead minimal
- [ ] Error handling comprehensive
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] Backend Engineer
- [ ] QA Engineer