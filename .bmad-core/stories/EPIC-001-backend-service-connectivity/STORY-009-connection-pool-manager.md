# User Story: Connection Pool Manager

**Story ID:** STORY-009  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Backend Integration  
**Story Points:** 8  
**Priority:** Critical (P0)  

---

## Story Description

**As the** backend integration system  
**I want** a centralized connection pool manager  
**So that** all connections are efficiently managed and resource usage is optimized  

## Acceptance Criteria

### Functional Requirements
- [ ] Manage connections for all 5 backend services
- [ ] Implement connection pooling for HTTP services
- [ ] Maintain WebSocket connections efficiently
- [ ] Handle connection lifecycle (create, reuse, destroy)
- [ ] Support concurrent request handling
- [ ] Implement connection limits per service
- [ ] Provide connection statistics
- [ ] Clean up stale connections

### Technical Requirements
- [ ] Thread-safe connection management
- [ ] Async/await pattern throughout
- [ ] Connection health checking
- [ ] Resource leak prevention
- [ ] Configurable pool sizes
- [ ] Connection timeout handling
- [ ] Graceful shutdown procedures
- [ ] Memory-efficient connection storage

### Quality Requirements
- [ ] Zero connection leaks over 24h operation
- [ ] Connection reuse rate >80%
- [ ] Pool operations <10ms overhead
- [ ] Supports 100+ concurrent requests
- [ ] Thread safety verified
- [ ] Clear connection state tracking
- [ ] Comprehensive error handling
- [ ] Performance metrics available

## Implementation Notes

### Technical Approach

**Connection Pool Manager Architecture:**
```python
from typing import Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass

@dataclass
class ConnectionConfig:
    max_connections: int = 10
    min_connections: int = 2
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0
    health_check_interval: float = 60.0

class ConnectionPoolManager:
    def __init__(self):
        self.pools: Dict[str, ConnectionPool] = {}
        self.configs: Dict[str, ConnectionConfig] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks = []
        
    async def initialize(self):
        """Initialize all connection pools"""
        self._running = True
        
        # Create pools for each service
        for service in BACKEND_SERVICES:
            config = ConnectionConfig()
            pool = await self._create_pool(service, config)
            self.pools[service] = pool
            self.configs[service] = config
            
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
    async def get_connection(self, service: str):
        """Get a connection from the pool"""
        pool = self.pools.get(service)
        if not pool:
            raise ValueError(f"Unknown service: {service}")
            
        return await pool.acquire()
```

**Service-Specific Connection Pools:**
```python
class WebSocketPool(ConnectionPool):
    """Pool for WebSocket connections (ComfyUI)"""
    
    async def create_connection(self):
        """Create new WebSocket connection"""
        ws = await websockets.connect(
            self.url,
            ping_interval=30,
            ping_timeout=10
        )
        return WebSocketConnection(ws)
        
    async def validate_connection(self, conn):
        """Check if WebSocket is still alive"""
        try:
            await conn.ws.ping()
            return True
        except:
            return False

class HTTPPool(ConnectionPool):
    """Pool for HTTP connections (LiteLLM, RVC, etc)"""
    
    def __init__(self, service_name: str, base_url: str):
        super().__init__(service_name)
        self.session = None
        self.base_url = base_url
        
    async def initialize(self):
        """Create aiohttp session with connection pool"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections,
            ttl_dns_cache=300
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=60)
        )
        
    async def request(self, method: str, path: str, **kwargs):
        """Make HTTP request using pooled connection"""
        url = f"{self.base_url}{path}"
        async with self.session.request(method, url, **kwargs) as response:
            return await response.json()
```

**Connection Lifecycle Management:**
```python
class ConnectionPool:
    def __init__(self, service_name: str, config: ConnectionConfig):
        self.service_name = service_name
        self.config = config
        self.available = asyncio.Queue(maxsize=config.max_connections)
        self.in_use = set()
        self.total_created = 0
        self.stats = ConnectionStats()
        
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        start_time = time.time()
        conn = None
        
        try:
            # Try to get existing connection
            try:
                conn = await asyncio.wait_for(
                    self.available.get(),
                    timeout=0.1
                )
                
                # Validate connection
                if not await self.validate_connection(conn):
                    await self.destroy_connection(conn)
                    conn = None
                    
            except asyncio.TimeoutError:
                conn = None
                
            # Create new connection if needed
            if conn is None and self.can_create_new():
                conn = await self.create_connection()
                self.total_created += 1
                
            if conn is None:
                # Wait for available connection
                conn = await asyncio.wait_for(
                    self.available.get(),
                    timeout=self.config.connection_timeout
                )
                
            # Track connection usage
            self.in_use.add(conn)
            self.stats.record_acquisition(time.time() - start_time)
            
            yield conn
            
        finally:
            # Return connection to pool
            if conn:
                self.in_use.discard(conn)
                if self._running and await self.validate_connection(conn):
                    await self.available.put(conn)
                else:
                    await self.destroy_connection(conn)
```

**Health Checking and Cleanup:**
```python
async def _health_check_loop(self):
    """Periodic health checks for all pools"""
    while self._running:
        for service, pool in self.pools.items():
            try:
                await pool.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {service}: {e}")
                
        await asyncio.sleep(30)  # Check every 30 seconds
        
async def _cleanup_loop(self):
    """Clean up idle connections"""
    while self._running:
        for service, pool in self.pools.items():
            try:
                await pool.cleanup_idle_connections()
            except Exception as e:
                logger.error(f"Cleanup failed for {service}: {e}")
                
        await asyncio.sleep(60)  # Cleanup every minute
```

**Connection Statistics:**
```python
class ConnectionStats:
    def __init__(self):
        self.total_acquisitions = 0
        self.total_creations = 0
        self.total_errors = 0
        self.acquisition_times = deque(maxlen=1000)
        self.reuse_count = 0
        
    def record_acquisition(self, duration: float):
        self.total_acquisitions += 1
        self.acquisition_times.append(duration)
        
    def get_metrics(self):
        return {
            'total_acquisitions': self.total_acquisitions,
            'total_creations': self.total_creations,
            'reuse_rate': self.calculate_reuse_rate(),
            'avg_acquisition_time': self.calculate_avg_acquisition_time(),
            'error_rate': self.calculate_error_rate()
        }
```

### Blender Integration
- Pool manager singleton instance
- Initialized on addon enable
- Graceful shutdown on disable
- Stats exposed to health dashboard

### Service-Specific Configurations
```python
SERVICE_POOL_CONFIGS = {
    'comfyui': ConnectionConfig(
        max_connections=5,  # WebSocket connections
        min_connections=1,
        health_check_interval=30
    ),
    'litellm': ConnectionConfig(
        max_connections=20,  # HTTP connections
        min_connections=5,
        idle_timeout=600
    ),
    'wan2gp': ConnectionConfig(
        max_connections=10,
        min_connections=2,
        connection_timeout=60  # Longer for Gradio
    )
}
```

## Testing Strategy

### Unit Tests
```python
class TestConnectionPool(unittest.TestCase):
    async def test_connection_acquisition(self):
        # Test getting connections
        # Verify pool behavior
        
    async def test_connection_reuse(self):
        # Return and reacquire
        # Verify same connection
        
    async def test_pool_limits(self):
        # Exhaust pool
        # Verify waiting behavior
        
    async def test_health_checks(self):
        # Simulate unhealthy connections
        # Verify removal
```

### Integration Tests
- Test with real backend services
- Simulate connection failures
- Load testing with concurrent requests
- Memory leak detection

## Dependencies
- STORY-001: Service discovery provides endpoints
- STORY-002-004: Individual client implementations
- asyncio for async operations

## Related Stories
- Used by all backend operations
- Monitored by STORY-010 (Health Check)
- Stats shown in STORY-008 (Health Dashboard)

## Definition of Done
- [ ] Pool manager handles all services
- [ ] Connection reuse working efficiently
- [ ] Health checks remove bad connections
- [ ] No resource leaks
- [ ] Thread-safe operations verified
- [ ] Statistics tracking accurate
- [ ] Performance targets met
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] Backend Architect
- [ ] QA Engineer