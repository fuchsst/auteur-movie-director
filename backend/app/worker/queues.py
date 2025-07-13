"""
Task Queue Configuration System

Provides intelligent queue routing, priority handling, and dead letter queue management
for distributed task processing with resource-aware routing.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from kombu import Queue, Exchange
from celery import Celery
from redis import Redis

logger = logging.getLogger(__name__)


# Exchange definitions
DEFAULT_EXCHANGE = Exchange('auteur', type='direct')
PRIORITY_EXCHANGE = Exchange('auteur.priority', type='direct')
DLQ_EXCHANGE = Exchange('auteur.dlq', type='direct')


# Queue configurations with resource requirements and priorities
QUEUE_CONFIGS = {
    'gpu.generation': {
        'exchange': DEFAULT_EXCHANGE,
        'routing_key': 'gpu.generation',
        'priority': 10,
        'arguments': {'x-max-priority': 10},
        'description': 'High-priority GPU generation tasks (image/video)',
        'resource_type': 'gpu',
        'max_size': 100
    },
    'gpu.processing': {
        'exchange': DEFAULT_EXCHANGE,
        'routing_key': 'gpu.processing',
        'priority': 8,
        'arguments': {'x-max-priority': 10},
        'description': 'GPU processing tasks (upscaling, style transfer)',
        'resource_type': 'gpu',
        'max_size': 200
    },
    'cpu.analysis': {
        'exchange': DEFAULT_EXCHANGE,
        'routing_key': 'cpu.analysis',
        'priority': 5,
        'arguments': {'x-max-priority': 10},
        'description': 'CPU-intensive analysis tasks',
        'resource_type': 'cpu',
        'max_size': 500
    },
    'cpu.thumbnail': {
        'exchange': DEFAULT_EXCHANGE,
        'routing_key': 'cpu.thumbnail',
        'priority': 3,
        'arguments': {'x-max-priority': 10},
        'description': 'Thumbnail and preview generation',
        'resource_type': 'cpu',
        'max_size': 1000
    },
    'io.storage': {
        'exchange': DEFAULT_EXCHANGE,
        'routing_key': 'io.storage',
        'priority': 1,
        'arguments': {'x-max-priority': 10},
        'description': 'File I/O and storage operations',
        'resource_type': 'io',
        'max_size': 2000
    },
    'priority': {
        'exchange': PRIORITY_EXCHANGE,
        'routing_key': 'priority',
        'priority': 10,
        'arguments': {'x-max-priority': 10},
        'description': 'Urgent priority tasks bypassing normal routing',
        'resource_type': 'any',
        'max_size': 50
    },
    'dlq': {
        'exchange': DLQ_EXCHANGE,
        'routing_key': 'dlq',
        'priority': 1,
        'arguments': {
            'x-message-ttl': 86400000,  # 24 hours
            'x-max-length': 10000
        },
        'description': 'Dead letter queue for failed tasks',
        'resource_type': 'any',
        'max_size': 10000
    }
}


def create_queues() -> List[Queue]:
    """Create Celery queues from configuration"""
    queues = []
    
    for queue_name, config in QUEUE_CONFIGS.items():
        queue = Queue(
            queue_name,
            exchange=config['exchange'],
            routing_key=config['routing_key'],
            priority=config['priority'],
            queue_arguments=config.get('arguments', {})
        )
        queues.append(queue)
        logger.info(f"Created queue '{queue_name}': {config['description']}")
    
    return queues


class TaskRouter:
    """Intelligent task routing based on resource requirements and task characteristics"""
    
    # Task name patterns to queue mapping
    ROUTE_MAP = {
        # GPU generation tasks - high priority, GPU required
        'generate_image': 'gpu.generation',
        'generate_video': 'gpu.generation',
        'generate_animation': 'gpu.generation',
        'create_comfyui_workflow': 'gpu.generation',
        
        # GPU processing tasks - medium priority, GPU preferred
        'apply_style_transfer': 'gpu.processing',
        'run_upscaling': 'gpu.processing',
        'enhance_image': 'gpu.processing',
        'apply_effects': 'gpu.processing',
        
        # CPU analysis tasks - medium priority, CPU intensive
        'analyze_scene': 'cpu.analysis',
        'extract_metadata': 'cpu.analysis',
        'process_audio': 'cpu.analysis',
        'validate_assets': 'cpu.analysis',
        'convert_format': 'cpu.analysis',
        
        # CPU thumbnail tasks - low priority, quick processing
        'generate_thumbnail': 'cpu.thumbnail',
        'create_preview': 'cpu.thumbnail',
        'resize_image': 'cpu.thumbnail',
        'create_gif': 'cpu.thumbnail',
        
        # IO storage tasks - lowest priority, I/O bound
        'save_to_storage': 'io.storage',
        'upload_to_cloud': 'io.storage',
        'download_assets': 'io.storage',
        'cleanup_temp_files': 'io.storage',
        'backup_project': 'io.storage'
    }
    
    # Task priority modifiers
    PRIORITY_MODIFIERS = {
        'user_initiated': +3,      # User-triggered tasks get higher priority
        'real_time': +5,           # Real-time preview tasks
        'batch_operation': -2,     # Batch operations get lower priority
        'background': -3,          # Background maintenance tasks
        'retry': -1                # Retry attempts get slightly lower priority
    }
    
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client
        self.route_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def route_task(self, name: str, args: list, kwargs: dict, 
                   options: dict, task=None, **kw) -> dict:
        """Route task to appropriate queue based on various factors"""
        
        # Check cache first
        cache_key = self._get_cache_key(name, kwargs)
        if cache_key in self.route_cache:
            cached_route = self.route_cache[cache_key]
            if datetime.now() - cached_route['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cached_route['route']
        
        # Check for explicit priority override
        if kwargs.get('priority_task') or options.get('priority_task'):
            route = {'queue': 'priority', 'routing_key': 'priority', 'priority': 10}
            self._cache_route(cache_key, route)
            return route
        
        # Check resource requirements from task metadata
        if hasattr(task, 'resource_requirements'):
            queue = self._route_by_resources(task.resource_requirements)
            if queue:
                route = self._create_route(queue, kwargs, task)
                self._cache_route(cache_key, route)
                return route
        
        # Check resource requirements from kwargs
        if 'resource_requirements' in kwargs:
            queue = self._route_by_resources(kwargs['resource_requirements'])
            if queue:
                route = self._create_route(queue, kwargs, task)
                self._cache_route(cache_key, route)
                return route
        
        # Use task name pattern matching
        task_name = name.split('.')[-1]  # Get last part of dotted name
        queue = self.ROUTE_MAP.get(task_name)
        
        # Fallback to analyzing task name for keywords
        if not queue:
            queue = self._analyze_task_name(task_name)
        
        # Final fallback
        if not queue:
            queue = 'cpu.analysis'
        
        route = self._create_route(queue, kwargs, task)
        self._cache_route(cache_key, route)
        return route
    
    def _route_by_resources(self, requirements: dict) -> Optional[str]:
        """Route based on explicit resource requirements"""
        if requirements.get('gpu'):
            vram_required = requirements.get('vram_gb', 0)
            if vram_required > 8:
                return 'gpu.generation'
            else:
                return 'gpu.processing'
        elif requirements.get('cpu_intensive'):
            return 'cpu.analysis'
        elif requirements.get('io_intensive'):
            return 'io.storage'
        
        return None
    
    def _analyze_task_name(self, task_name: str) -> str:
        """Analyze task name for routing hints"""
        name_lower = task_name.lower()
        
        # GPU keywords
        gpu_keywords = ['generate', 'create', 'upscale', 'enhance', 'style', 'ai', 'model']
        if any(keyword in name_lower for keyword in gpu_keywords):
            return 'gpu.processing'
        
        # CPU analysis keywords
        cpu_keywords = ['analyze', 'process', 'convert', 'validate', 'extract']
        if any(keyword in name_lower for keyword in cpu_keywords):
            return 'cpu.analysis'
        
        # Thumbnail keywords
        thumb_keywords = ['thumbnail', 'preview', 'resize', 'small']
        if any(keyword in name_lower for keyword in thumb_keywords):
            return 'cpu.thumbnail'
        
        # IO keywords
        io_keywords = ['save', 'upload', 'download', 'store', 'backup', 'cleanup']
        if any(keyword in name_lower for keyword in io_keywords):
            return 'io.storage'
        
        return 'cpu.analysis'  # Default fallback
    
    def _create_route(self, queue: str, kwargs: dict, task=None) -> dict:
        """Create route dictionary with calculated priority"""
        priority = self._calculate_priority(queue, kwargs, task)
        
        return {
            'queue': queue,
            'routing_key': queue,
            'priority': priority
        }
    
    def _calculate_priority(self, queue: str, kwargs: dict, task=None) -> int:
        """Calculate task priority based on various factors"""
        # Get base priority from queue configuration
        base_priority = QUEUE_CONFIGS.get(queue, {}).get('priority', 5)
        
        # Apply modifiers based on task characteristics
        priority = base_priority
        
        for modifier_key, modifier_value in self.PRIORITY_MODIFIERS.items():
            if kwargs.get(modifier_key) or (task and getattr(task, modifier_key, False)):
                priority = max(1, min(10, priority + modifier_value))
        
        # Check explicit priority override
        if 'priority' in kwargs:
            explicit_priority = kwargs['priority']
            if 1 <= explicit_priority <= 10:
                priority = explicit_priority
        
        # Apply batch size penalty for large batches
        batch_size = kwargs.get('batch_size', 1)
        if batch_size > 10:
            penalty = min(2, batch_size // 20)  # -1 for every 20 items
            priority = max(1, priority - penalty)
        
        return priority
    
    def _get_cache_key(self, name: str, kwargs: dict) -> str:
        """Generate cache key for route"""
        relevant_keys = ['priority_task', 'resource_requirements', 'user_initiated', 'batch_operation']
        key_parts = [name]
        
        for key in relevant_keys:
            if key in kwargs:
                key_parts.append(f"{key}:{kwargs[key]}")
        
        return "|".join(key_parts)
    
    def _cache_route(self, cache_key: str, route: dict):
        """Cache route decision"""
        self.route_cache[cache_key] = {
            'route': route,
            'timestamp': datetime.now()
        }
        
        # Clean old entries periodically
        if len(self.route_cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove old cache entries"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, value in self.route_cache.items():
            if current_time - value['timestamp'] > timedelta(seconds=self.cache_ttl):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.route_cache[key]
    
    def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """Get information about a specific queue"""
        config = QUEUE_CONFIGS.get(queue_name)
        if not config:
            return {}
        
        return {
            'name': queue_name,
            'description': config['description'],
            'resource_type': config['resource_type'],
            'priority': config['priority'],
            'max_size': config['max_size'],
            'exchange': config['exchange'].name,
            'routing_key': config['routing_key']
        }
    
    def get_all_queues_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all configured queues"""
        return {name: self.get_queue_info(name) for name in QUEUE_CONFIGS.keys()}


class TaskDeduplicator:
    """Prevent duplicate task processing"""
    
    def __init__(self, redis_client: Redis, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl  # Time to live for deduplication keys
    
    def generate_task_hash(self, task_name: str, args: tuple, kwargs: dict) -> str:
        """Generate unique hash for task deduplication"""
        import hashlib
        import json
        
        # Create deterministic representation
        task_data = {
            'name': task_name,
            'args': args,
            'kwargs': {k: v for k, v in kwargs.items() if k not in ['task_id', 'timestamp']}
        }
        
        # Sort keys for consistency
        task_str = json.dumps(task_data, sort_keys=True, default=str)
        return hashlib.sha256(task_str.encode()).hexdigest()
    
    def is_duplicate(self, task_hash: str) -> bool:
        """Check if task is already being processed"""
        key = f"task_dedupe:{task_hash}"
        return self.redis.exists(key)
    
    def mark_processing(self, task_hash: str) -> bool:
        """Mark task as being processed"""
        key = f"task_dedupe:{task_hash}"
        return self.redis.setex(key, self.ttl, "processing")
    
    def mark_completed(self, task_hash: str):
        """Mark task as completed (remove from processing)"""
        key = f"task_dedupe:{task_hash}"
        self.redis.delete(key)


class QueueHealthChecker:
    """Monitor queue health and detect issues"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.thresholds = {
            'gpu.generation': {'max_depth': 50, 'max_age': 300},     # 5 minutes
            'gpu.processing': {'max_depth': 100, 'max_age': 600},    # 10 minutes
            'cpu.analysis': {'max_depth': 200, 'max_age': 1800},     # 30 minutes
            'cpu.thumbnail': {'max_depth': 500, 'max_age': 3600},    # 1 hour
            'io.storage': {'max_depth': 1000, 'max_age': 7200},      # 2 hours
            'priority': {'max_depth': 10, 'max_age': 60}             # 1 minute
        }
    
    def check_queue_health(self, queue_name: str) -> Dict[str, Any]:
        """Check health of specific queue"""
        try:
            # Get queue depth
            depth = self.redis.llen(f"celery:{queue_name}")
            
            # Get oldest task age
            oldest_age = self._get_oldest_task_age(queue_name)
            
            # Check thresholds
            thresholds = self.thresholds.get(queue_name, {'max_depth': 1000, 'max_age': 3600})
            
            health_status = {
                'queue_name': queue_name,
                'depth': depth,
                'oldest_task_age': oldest_age,
                'healthy': True,
                'issues': []
            }
            
            if depth > thresholds['max_depth']:
                health_status['healthy'] = False
                health_status['issues'].append(f"Queue depth {depth} exceeds threshold {thresholds['max_depth']}")
            
            if oldest_age > thresholds['max_age']:
                health_status['healthy'] = False
                health_status['issues'].append(f"Oldest task age {oldest_age}s exceeds threshold {thresholds['max_age']}s")
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking health for queue {queue_name}: {e}")
            return {
                'queue_name': queue_name,
                'healthy': False,
                'issues': [f"Health check failed: {str(e)}"]
            }
    
    def _get_oldest_task_age(self, queue_name: str) -> int:
        """Get age of oldest task in queue"""
        try:
            # Get first task from queue without removing it
            task_data = self.redis.lindex(f"celery:{queue_name}", 0)
            if not task_data:
                return 0
            
            import json
            task = json.loads(task_data)
            
            # Extract timestamp if available
            if 'eta' in task:
                from dateutil.parser import parse
                eta = parse(task['eta'])
                age = (datetime.now() - eta).total_seconds()
                return max(0, int(age))
            
            return 0
            
        except Exception as e:
            logger.warning(f"Could not get oldest task age for {queue_name}: {e}")
            return 0
    
    def check_all_queues_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all queues"""
        health_report = {}
        
        for queue_name in QUEUE_CONFIGS.keys():
            if queue_name != 'dlq':  # Skip DLQ for regular health checks
                health_report[queue_name] = self.check_queue_health(queue_name)
        
        return health_report


# Global instances
task_router = TaskRouter()