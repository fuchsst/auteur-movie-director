"""
Celery Configuration for Function Runner Workers

Configures Celery for distributed task processing with multiple worker types,
auto-scaling, and queue routing.
"""

import os
from typing import Dict, Any

from celery import Celery
from kombu import Queue

from app.config import settings

# Initialize Celery app
app = Celery('auteur_function_runner')

# Broker configuration
BROKER_URL = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
RESULT_BACKEND = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')

# Worker configuration
WORKER_CONFIG = {
    # Connection settings
    'broker_url': BROKER_URL,
    'result_backend': RESULT_BACKEND,
    'broker_connection_retry_on_startup': True,
    'broker_connection_retry': True,
    
    # Task serialization
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'timezone': 'UTC',
    'enable_utc': True,
    
    # Worker settings
    'worker_prefetch_multiplier': 1,  # Prefetch one task at a time
    'worker_max_tasks_per_child': 100,  # Restart worker after 100 tasks
    'worker_disable_rate_limits': True,
    'worker_send_task_events': True,
    'task_send_sent_event': True,
    
    # Auto-scaling settings
    'worker_autoscaler': 'app.worker.autoscaler:FunctionRunnerAutoscaler',
    'worker_autoscale_max': getattr(settings, 'MAX_WORKERS', 10),
    'worker_autoscale_min': getattr(settings, 'MIN_WORKERS', 1),
    
    # Task routing configuration
    'task_routes': {
        'app.worker.tasks.generate_image': {'queue': 'gpu'},
        'app.worker.tasks.generate_video': {'queue': 'gpu'},
        'app.worker.tasks.generate_audio': {'queue': 'gpu'},
        'app.worker.tasks.process_file': {'queue': 'cpu'},
        'app.worker.tasks.resize_image': {'queue': 'cpu'},
        'app.worker.tasks.convert_format': {'queue': 'cpu'},
        'app.worker.tasks.upload_file': {'queue': 'io'},
        'app.worker.tasks.download_file': {'queue': 'io'},
        'app.worker.tasks.health_check': {'queue': 'default'},
    },
    
    # Queue configuration
    'task_queues': [
        Queue('default', routing_key='default', priority=5),
        Queue('gpu', routing_key='gpu', priority=10),
        Queue('cpu', routing_key='cpu', priority=7),
        Queue('io', routing_key='io', priority=3),
        Queue('priority', routing_key='priority', priority=15),
    ],
    
    # Default queue
    'task_default_queue': 'default',
    'task_default_exchange': 'default',
    'task_default_routing_key': 'default',
    
    # Result settings
    'result_expires': 3600,  # Results expire after 1 hour
    'task_ignore_result': False,
    'task_store_eager_result': True,
    
    # Error handling
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'task_track_started': True,
    
    # Monitoring
    'worker_log_format': '[%(asctime)s: %(levelname)s/%(processName)s/%(name)s] %(message)s',
    'worker_task_log_format': '[%(asctime)s: %(levelname)s/%(processName)s/%(name)s][%(task_name)s(%(task_id)s)] %(message)s',
}

# Apply configuration
app.conf.update(WORKER_CONFIG)


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