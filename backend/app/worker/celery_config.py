"""
Celery Configuration for Function Runner Workers

Configures Celery with sophisticated queue routing, dead letter queues,
custom autoscaler, and optimized settings for function runner tasks.
"""

import os
import logging
from typing import Dict, Any

from celery import Celery
from celery.signals import task_failure, task_success, task_prerun, task_postrun
from kombu import Queue

from app.config import settings
from app.worker.queues import create_queues, task_router
from app.worker.dead_letter_queue import get_dlq_handler
from app.worker.queue_monitor import get_queue_monitor
from app.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery('auteur_function_runner')

# Redis client for additional functionality
redis_client = get_redis_client()

# Broker configuration
BROKER_URL = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
RESULT_BACKEND = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/1')

# Advanced worker configuration
WORKER_CONFIG = {
    # Connection settings
    'broker_url': BROKER_URL,
    'result_backend': RESULT_BACKEND,
    'broker_connection_retry_on_startup': True,
    'broker_connection_retry': True,
    
    # Serialization - use msgpack for efficiency
    'task_serializer': 'msgpack',
    'result_serializer': 'msgpack',
    'accept_content': ['msgpack', 'json'],
    'timezone': 'UTC',
    'enable_utc': True,
    
    # Result settings
    'result_expires': 3600,  # Results expire after 1 hour
    'result_compression': 'gzip',
    'result_cache_max': 10000,
    'task_ignore_result': False,
    'task_store_eager_result': True,
    
    # Task execution settings
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'task_track_started': True,
    'task_send_sent_event': True,
    'task_publish_retry': True,
    'task_publish_retry_policy': {
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    },
    
    # Worker settings
    'worker_prefetch_multiplier': 1,  # Prevent worker overload
    'worker_max_tasks_per_child': 100,  # Restart workers to prevent memory leaks
    'worker_disable_rate_limits': False,
    'worker_send_task_events': True,
    'worker_log_format': '[%(asctime)s: %(levelname)s/%(processName)s/%(name)s] %(message)s',
    'worker_task_log_format': '[%(asctime)s: %(levelname)s/%(processName)s/%(name)s][%(task_name)s(%(task_id)s)] %(message)s',
    
    # Auto-scaling settings
    'worker_autoscaler': 'app.worker.autoscaler:FunctionRunnerAutoscaler',
    'worker_autoscale_max': getattr(settings, 'MAX_WORKERS', 10),
    'worker_autoscale_min': getattr(settings, 'MIN_WORKERS', 1),
    
    # Queue configuration from our advanced queue system
    'task_queues': create_queues(),
    
    # Task routing using our intelligent router
    'task_routes': task_router.route_task,
    
    # Default settings
    'task_default_queue': 'cpu.analysis',
    'task_default_exchange': 'auteur',
    'task_default_exchange_type': 'direct',
    'task_default_routing_key': 'cpu.analysis',
    
    # Rate limiting for different task types
    'task_annotations': {
        'app.worker.tasks.generate.*': {
            'rate_limit': '10/m',  # 10 per minute for generation tasks
            'soft_time_limit': 300,  # 5 minutes soft limit
            'time_limit': 600,       # 10 minutes hard limit
        },
        'app.worker.tasks.process.*': {
            'rate_limit': '50/m',   # 50 per minute for processing
            'soft_time_limit': 120,  # 2 minutes soft limit
            'time_limit': 300,       # 5 minutes hard limit
        },
        'app.worker.tasks.thumbnail.*': {
            'rate_limit': '100/m',  # 100 per minute for thumbnails
            'soft_time_limit': 30,   # 30 seconds soft limit
            'time_limit': 60,        # 1 minute hard limit
        },
        'app.worker.tasks.io.*': {
            'rate_limit': '200/m',  # 200 per minute for I/O
            'soft_time_limit': 60,   # 1 minute soft limit
            'time_limit': 120,       # 2 minutes hard limit
        },
    },
    
    # Memory and resource management
    'worker_max_memory_per_child': 500000,  # 500MB per worker
    
    # Beat schedule (if using periodic tasks)
    'beat_schedule': {
        'cleanup-expired-results': {
            'task': 'app.worker.tasks.cleanup_expired_results',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'io.storage'}
        },
        'monitor-queue-health': {
            'task': 'app.worker.tasks.monitor_queue_health',
            'schedule': 60.0,    # Every minute
            'options': {'queue': 'cpu.analysis'}
        },
    }
}

# Apply configuration
app.conf.update(WORKER_CONFIG)

# Initialize additional components
dlq_handler = get_dlq_handler(app, redis_client)
queue_monitor = get_queue_monitor(app, redis_client)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handle task prerun for monitoring"""
    try:
        # Determine queue from task routing
        queue_name = getattr(task.request, 'delivery_info', {}).get('routing_key', 'unknown')
        if queue_name and hasattr(queue_monitor, 'record_task_started'):
            queue_monitor.record_task_started(queue_name, task_id)
        
        logger.info(f"Task {task_id} ({task.name}) starting on queue {queue_name}")
    except Exception as e:
        logger.warning(f"Error in task prerun handler: {e}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, 
                        kwargs=None, retval=None, state=None, **kwds):
    """Handle task postrun for monitoring"""
    try:
        # Determine queue and processing time
        queue_name = getattr(task.request, 'delivery_info', {}).get('routing_key', 'unknown')
        
        # Calculate processing time if available
        processing_time = 0.0
        if hasattr(task.request, 'time_start'):
            from datetime import datetime
            start_time = task.request.time_start
            processing_time = (datetime.now() - start_time).total_seconds()
        
        if queue_name and hasattr(queue_monitor, 'record_task_completed'):
            queue_monitor.record_task_completed(queue_name, task_id, processing_time)
        
        logger.info(f"Task {task_id} completed in {processing_time:.2f}s")
    except Exception as e:
        logger.warning(f"Error in task postrun handler: {e}")


@task_success.connect
def task_success_handler(sender=None, result=None, **kwds):
    """Handle successful task completion"""
    try:
        task_id = kwds.get('task_id')
        logger.debug(f"Task {task_id} succeeded")
    except Exception as e:
        logger.warning(f"Error in task success handler: {e}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, 
                        traceback=None, einfo=None, **kwds):
    """Handle task failures and route to DLQ"""
    try:
        # Get task information
        task_name = sender.name if sender else 'unknown'
        task_args = getattr(sender, 'request', {}).get('args', [])
        task_kwargs = getattr(sender, 'request', {}).get('kwargs', {})
        queue_name = getattr(sender, 'request', {}).get('delivery_info', {}).get('routing_key')
        
        # Record failure for monitoring
        if queue_name and hasattr(queue_monitor, 'record_task_failed'):
            queue_monitor.record_task_failed(queue_name, task_id, type(exception).__name__)
        
        # Handle retry logic through DLQ
        if dlq_handler:
            dlq_handler.handle_task_failure(
                task_id=task_id,
                task_name=task_name,
                args=task_args,
                kwargs=task_kwargs,
                exception=exception,
                traceback=str(traceback) if traceback else str(einfo),
                queue=queue_name
            )
        
        logger.error(f"Task {task_id} failed: {exception}")
        
    except Exception as e:
        logger.error(f"Error in task failure handler: {e}")


# Custom Celery app startup
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    logger.info("Celery configured with advanced queue system")


class WorkerTypeConfig:
    """Configuration for different worker types"""
    
    @staticmethod
    def get_gpu_worker_config() -> Dict[str, Any]:
        """Configuration for GPU workers"""
        return {
            'queues': ['gpu', 'priority'],
            'concurrency': 1,  # GPU workers handle one task at a time
            'prefetch_multiplier': 1,
            'max_tasks_per_child': 50,  # GPU workers restart more frequently
            'environment': {
                'CUDA_VISIBLE_DEVICES': '0',
                'WORKER_TYPE': 'gpu',
                'GPU_MEMORY_FRACTION': '0.95'
            }
        }
    
    @staticmethod
    def get_cpu_worker_config() -> Dict[str, Any]:
        """Configuration for CPU workers"""
        return {
            'queues': ['cpu', 'default'],
            'concurrency': 4,  # CPU workers can handle multiple tasks
            'prefetch_multiplier': 2,
            'max_tasks_per_child': 100,
            'environment': {
                'WORKER_TYPE': 'cpu',
                'OMP_NUM_THREADS': '2'
            }
        }
    
    @staticmethod
    def get_io_worker_config() -> Dict[str, Any]:
        """Configuration for I/O workers"""
        return {
            'queues': ['io'],
            'concurrency': 8,  # I/O workers can handle many concurrent operations
            'prefetch_multiplier': 4,
            'max_tasks_per_child': 200,
            'environment': {
                'WORKER_TYPE': 'io'
            }
        }
    
    @staticmethod
    def get_general_worker_config() -> Dict[str, Any]:
        """Configuration for general workers"""
        return {
            'queues': ['default'],
            'concurrency': 2,
            'prefetch_multiplier': 1,
            'max_tasks_per_child': 100,
            'environment': {
                'WORKER_TYPE': 'general'
            }
        }


def create_worker_command(worker_type: str = 'general') -> str:
    """Create Celery worker command for specific worker type"""
    
    config_map = {
        'gpu': WorkerTypeConfig.get_gpu_worker_config(),
        'cpu': WorkerTypeConfig.get_cpu_worker_config(),
        'io': WorkerTypeConfig.get_io_worker_config(),
        'general': WorkerTypeConfig.get_general_worker_config()
    }
    
    config = config_map.get(worker_type, WorkerTypeConfig.get_general_worker_config())
    
    # Build command
    cmd_parts = [
        'celery',
        '-A', 'app.worker.celery_config',
        'worker',
        '--hostname', f'{worker_type}@%h',
        '--queues', ','.join(config['queues']),
        '--concurrency', str(config['concurrency']),
        '--prefetch-multiplier', str(config['prefetch_multiplier']),
        '--max-tasks-per-child', str(config['max_tasks_per_child']),
        '--loglevel', 'info'
    ]
    
    return ' '.join(cmd_parts)


def get_monitoring_config() -> Dict[str, Any]:
    """Get configuration for Celery monitoring"""
    return {
        'flower_config': {
            'broker': BROKER_URL,
            'port': 5555,
            'address': '0.0.0.0',
            'url_prefix': '/flower',
            'basic_auth': None,  # Set in production
            'persistent': True,
            'db': '/tmp/flower.db',
            'max_tasks': 10000,
        },
        'monitoring_queues': ['default', 'gpu', 'cpu', 'io', 'priority'],
        'metrics_retention': 7 * 24 * 3600,  # 7 days
    }


# Task discovery
app.autodiscover_tasks(['app.worker.tasks'])

# Health check task
@app.task(name='worker.health_check')
def health_check():
    """Simple health check task"""
    import psutil
    from datetime import datetime
    
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'worker_id': os.getenv('WORKER_ID', 'unknown'),
        'worker_type': os.getenv('WORKER_TYPE', 'unknown'),
        'system': {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
        }
    }


# Worker startup hook
@app.task(bind=True, name='worker.startup')
def worker_startup(self):
    """Task executed when worker starts"""
    import logging
    
    logger = logging.getLogger(__name__)
    worker_id = os.getenv('WORKER_ID', self.request.hostname)
    worker_type = os.getenv('WORKER_TYPE', 'unknown')
    
    logger.info(f"Worker {worker_id} of type {worker_type} started")
    
    return {
        'worker_id': worker_id,
        'worker_type': worker_type,
        'started_at': self.request.called_directly or 'unknown'
    }


# Worker shutdown hook
@app.task(bind=True, name='worker.shutdown')
def worker_shutdown(self):
    """Task executed when worker shuts down"""
    import logging
    
    logger = logging.getLogger(__name__)
    worker_id = os.getenv('WORKER_ID', self.request.hostname)
    
    logger.info(f"Worker {worker_id} shutting down")
    
    return {
        'worker_id': worker_id,
        'shutdown_at': self.request.called_directly or 'unknown'
    }