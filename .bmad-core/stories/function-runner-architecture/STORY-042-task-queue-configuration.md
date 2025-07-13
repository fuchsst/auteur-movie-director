# Story: Task Queue Configuration

**Story ID**: STORY-042  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Infrastructure  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: ✅ Completed  

## Story Description
As a platform engineer, I want a sophisticated task queue configuration system that intelligently routes generation tasks to appropriate workers based on resource requirements and priorities, so that GPU-intensive tasks go to GPU workers while lightweight tasks utilize CPU workers efficiently.

## Acceptance Criteria

### Functional Requirements
- [ ] Multiple named queues for different task types (gpu, cpu, io, priority)
- [ ] Automatic task routing based on function type and resource requirements
- [ ] Priority queuing with configurable priority levels (1-10)
- [ ] Dead letter queue for failed tasks with retry policies
- [ ] Queue depth monitoring and alerting thresholds
- [ ] Task deduplication to prevent duplicate processing
- [ ] Queue pause/resume functionality for maintenance
- [ ] Batch task submission with atomic guarantees

### Technical Requirements
- [ ] Implement Celery queue configuration with Redis backend
- [ ] Create task router with intelligent routing logic
- [ ] Configure queue-specific worker pools and concurrency
- [ ] Implement task serialization with MessagePack for efficiency
- [ ] Add queue monitoring with Flower dashboard integration
- [ ] Create dead letter queue with exponential backoff retry
- [ ] Implement task result storage with configurable TTL
- [ ] Add queue metrics collection for performance analysis

### Quality Requirements
- [ ] Task routing latency < 10ms for 95th percentile
- [ ] Queue throughput > 1000 tasks/second per queue
- [ ] Task deduplication accuracy 100%
- [ ] Priority task scheduling within 100ms
- [ ] Queue monitoring update frequency < 1 second
- [ ] Zero message loss during Redis failover
- [ ] Support for tasks up to 10MB in size

## Implementation Notes

### Queue Configuration
```python
# queues.py
from kombu import Queue, Exchange
from celery import Celery

# Define exchanges
default_exchange = Exchange('auteur', type='direct')
priority_exchange = Exchange('auteur.priority', type='direct')
dlq_exchange = Exchange('auteur.dlq', type='direct')

# Queue definitions
QUEUES = [
    # GPU-intensive tasks
    Queue('gpu.generation', exchange=default_exchange, 
          routing_key='gpu.generation', priority=10,
          queue_arguments={'x-max-priority': 10}),
    
    Queue('gpu.processing', exchange=default_exchange,
          routing_key='gpu.processing', priority=8),
    
    # CPU tasks
    Queue('cpu.analysis', exchange=default_exchange,
          routing_key='cpu.analysis', priority=5),
    
    Queue('cpu.thumbnail', exchange=default_exchange,
          routing_key='cpu.thumbnail', priority=3),
    
    # IO tasks
    Queue('io.storage', exchange=default_exchange,
          routing_key='io.storage', priority=1),
    
    # Priority queue for urgent tasks
    Queue('priority', exchange=priority_exchange,
          routing_key='priority', priority=10,
          queue_arguments={'x-max-priority': 10}),
    
    # Dead letter queue
    Queue('dlq', exchange=dlq_exchange,
          routing_key='dlq', priority=1,
          queue_arguments={
              'x-message-ttl': 86400000,  # 24 hours
              'x-max-length': 10000
          })
]

# Celery configuration
app = Celery('auteur')
app.conf.update(
    task_queues=QUEUES,
    task_default_queue='cpu.analysis',
    task_default_exchange='auteur',
    task_default_routing_key='cpu.analysis',
    
    # Result backend settings
    result_backend='redis://redis:6379/1',
    result_expires=3600,  # 1 hour
    result_compression='gzip',
    
    # Serialization
    task_serializer='msgpack',
    result_serializer='msgpack',
    accept_content=['msgpack', 'json'],
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_send_sent_event=True,
    
    # Rate limiting
    task_annotations={
        'auteur.tasks.generate.*': {'rate_limit': '10/m'},
        'auteur.tasks.thumbnail.*': {'rate_limit': '100/m'}
    }
)
```

### Task Router Implementation
```python
class TaskRouter:
    """Intelligent task routing based on resource requirements"""
    
    # Task to queue mapping
    ROUTE_MAP = {
        # GPU tasks
        'generate_image': 'gpu.generation',
        'generate_video': 'gpu.generation',
        'apply_style_transfer': 'gpu.processing',
        'run_upscaling': 'gpu.processing',
        
        # CPU tasks
        'analyze_scene': 'cpu.analysis',
        'extract_metadata': 'cpu.analysis',
        'generate_thumbnail': 'cpu.thumbnail',
        'create_preview': 'cpu.thumbnail',
        
        # IO tasks
        'save_to_storage': 'io.storage',
        'upload_to_cloud': 'io.storage',
        'cleanup_temp_files': 'io.storage'
    }
    
    def route_task(self, name: str, args: list, kwargs: dict, 
                   options: dict, task=None, **kw) -> dict:
        """Route task to appropriate queue"""
        
        # Check for explicit priority flag
        if kwargs.get('priority_task'):
            return {'queue': 'priority', 'routing_key': 'priority'}
        
        # Check resource requirements
        if hasattr(task, 'resource_requirements'):
            reqs = task.resource_requirements
            if reqs.get('gpu'):
                queue = 'gpu.generation' if reqs.get('vram_gb', 0) > 8 else 'gpu.processing'
                return {'queue': queue, 'routing_key': queue}
        
        # Use route map
        task_name = name.split('.')[-1]
        queue = self.ROUTE_MAP.get(task_name, 'cpu.analysis')
        
        return {
            'queue': queue,
            'routing_key': queue,
            'priority': self.calculate_priority(task, kwargs)
        }
    
    def calculate_priority(self, task, kwargs: dict) -> int:
        """Calculate task priority based on various factors"""
        base_priority = kwargs.get('priority', 5)
        
        # Boost priority for user-initiated tasks
        if kwargs.get('user_initiated'):
            base_priority = min(base_priority + 2, 10)
        
        # Lower priority for batch operations
        if kwargs.get('batch_size', 1) > 10:
            base_priority = max(base_priority - 1, 1)
        
        return base_priority
```

### Queue Monitoring
```python
class QueueMonitor:
    """Monitor queue health and performance"""
    
    def __init__(self, app: Celery, redis_client: Redis):
        self.app = app
        self.redis = redis_client
        self.metrics = {}
    
    async def collect_metrics(self):
        """Collect queue metrics every second"""
        while True:
            for queue in QUEUES:
                queue_name = queue.name
                
                # Get queue depth
                depth = self.redis.llen(f"celery:{queue_name}")
                
                # Get processing rate
                rate = await self.calculate_processing_rate(queue_name)
                
                # Get error rate
                error_rate = await self.calculate_error_rate(queue_name)
                
                self.metrics[queue_name] = {
                    'depth': depth,
                    'processing_rate': rate,
                    'error_rate': error_rate,
                    'timestamp': datetime.now()
                }
                
                # Check thresholds
                await self.check_thresholds(queue_name, depth, error_rate)
            
            # Publish metrics
            await self.publish_metrics()
            await asyncio.sleep(1)
    
    async def check_thresholds(self, queue: str, depth: int, error_rate: float):
        """Alert if thresholds exceeded"""
        if depth > self.get_threshold(queue, 'max_depth'):
            await self.alert(f"Queue {queue} depth {depth} exceeds threshold")
        
        if error_rate > self.get_threshold(queue, 'max_error_rate'):
            await self.alert(f"Queue {queue} error rate {error_rate}% exceeds threshold")
```

### Dead Letter Queue Handler
```python
class DeadLetterQueueHandler:
    """Handle failed tasks with retry logic"""
    
    def __init__(self, app: Celery):
        self.app = app
        self.retry_policies = {
            'default': ExponentialBackoff(base=60, factor=2, max_delay=3600),
            'critical': ExponentialBackoff(base=30, factor=1.5, max_delay=1800),
            'batch': LinearBackoff(delay=300, max_retries=3)
        }
    
    @app.task(bind=True, queue='dlq')
    def process_dead_letter(self, task_data: dict):
        """Process tasks from dead letter queue"""
        original_task = task_data['task']
        error_info = task_data['error']
        retry_count = task_data.get('retry_count', 0)
        
        # Determine retry policy
        policy_name = self.get_retry_policy(original_task)
        policy = self.retry_policies[policy_name]
        
        # Check if should retry
        if retry_count < policy.max_retries:
            delay = policy.get_delay(retry_count)
            
            # Re-queue with delay
            self.app.send_task(
                original_task['name'],
                args=original_task['args'],
                kwargs=original_task['kwargs'],
                countdown=delay,
                queue=original_task.get('queue', 'cpu.analysis')
            )
            
            logger.info(f"Retrying task {original_task['id']} after {delay}s")
        else:
            # Max retries exceeded, move to permanent failure storage
            await self.store_permanent_failure(task_data)
            logger.error(f"Task {original_task['id']} permanently failed")
```

## Dependencies
- **STORY-041**: Worker Pool Management - workers consume from these queues
- **STORY-043**: Worker Health Monitoring - monitors queue processing health
- Redis for queue backend and metrics storage
- Celery for distributed task queue
- Flower for queue visualization
- MessagePack for efficient serialization

## Testing Criteria
- [ ] Unit tests for task router logic with various task types
- [ ] Integration tests for queue creation and configuration
- [ ] Load tests verifying 1000+ tasks/second throughput
- [ ] Priority queue tests ensuring correct task ordering
- [ ] Dead letter queue tests with retry scenarios
- [ ] Monitoring tests for metric collection accuracy
- [ ] Chaos tests for Redis failover scenarios
- [ ] End-to-end tests for complete task lifecycle

## Definition of Done
- [ ] All queues configured with appropriate settings
- [ ] Task router correctly routes all task types
- [ ] Priority queuing working with 10 priority levels
- [ ] Dead letter queue processes failures with retry
- [ ] Queue monitoring collects metrics every second
- [ ] Flower dashboard shows all queue statistics
- [ ] Task deduplication prevents duplicate processing
- [ ] Performance meets throughput requirements
- [ ] Documentation includes queue configuration guide
- [ ] Code review passed with test coverage > 85%

## Story Links
- **Depends On**: STORY-041 (Worker Pool Management)
- **Blocks**: STORY-047 (API Client Layer)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/foundation/task_queue_design.md