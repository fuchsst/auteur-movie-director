"""
Dead Letter Queue Handler

Manages failed task processing with intelligent retry policies,
exponential backoff, and permanent failure handling.
"""

import logging
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from celery import Celery
from redis import Redis

logger = logging.getLogger(__name__)


class RetryPolicy(Enum):
    """Retry policy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"
    FIXED = "fixed"


@dataclass
class BackoffConfig:
    """Retry backoff configuration"""
    policy: RetryPolicy
    base_delay: int  # Base delay in seconds
    max_delay: int   # Maximum delay in seconds
    max_retries: int # Maximum retry attempts
    factor: float = 2.0  # Multiplier for exponential backoff
    jitter: bool = True  # Add random jitter to prevent thundering herd


class BackoffStrategy:
    """Calculate retry delays based on different strategies"""
    
    @staticmethod
    def exponential(attempt: int, config: BackoffConfig) -> int:
        """Exponential backoff with optional jitter"""
        delay = config.base_delay * (config.factor ** attempt)
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            import random
            jitter_factor = random.uniform(0.5, 1.5)
            delay = int(delay * jitter_factor)
        
        return delay
    
    @staticmethod
    def linear(attempt: int, config: BackoffConfig) -> int:
        """Linear backoff"""
        delay = config.base_delay + (config.base_delay * attempt)
        return min(delay, config.max_delay)
    
    @staticmethod
    def fibonacci(attempt: int, config: BackoffConfig) -> int:
        """Fibonacci backoff"""
        def fib(n):
            if n <= 1:
                return n
            return fib(n-1) + fib(n-2)
        
        delay = config.base_delay * fib(attempt + 1)
        return min(delay, config.max_delay)
    
    @staticmethod
    def fixed(attempt: int, config: BackoffConfig) -> int:
        """Fixed delay"""
        return config.base_delay


class DeadLetterQueueHandler:
    """Handle failed tasks with sophisticated retry logic"""
    
    # Default retry policies for different task types
    DEFAULT_RETRY_POLICIES = {
        'gpu.generation': BackoffConfig(
            policy=RetryPolicy.EXPONENTIAL,
            base_delay=120,    # 2 minutes
            max_delay=3600,    # 1 hour
            max_retries=5,
            factor=2.0
        ),
        'gpu.processing': BackoffConfig(
            policy=RetryPolicy.EXPONENTIAL,
            base_delay=60,     # 1 minute
            max_delay=1800,    # 30 minutes
            max_retries=4,
            factor=1.8
        ),
        'cpu.analysis': BackoffConfig(
            policy=RetryPolicy.LINEAR,
            base_delay=30,     # 30 seconds
            max_delay=900,     # 15 minutes
            max_retries=6,
            factor=1.0
        ),
        'cpu.thumbnail': BackoffConfig(
            policy=RetryPolicy.FIXED,
            base_delay=15,     # 15 seconds
            max_delay=300,     # 5 minutes
            max_retries=3,
            factor=1.0
        ),
        'io.storage': BackoffConfig(
            policy=RetryPolicy.FIBONACCI,
            base_delay=10,     # 10 seconds
            max_delay=600,     # 10 minutes
            max_retries=8,
            factor=1.0
        ),
        'priority': BackoffConfig(
            policy=RetryPolicy.EXPONENTIAL,
            base_delay=30,     # 30 seconds
            max_delay=600,     # 10 minutes
            max_retries=3,
            factor=1.5
        ),
        'default': BackoffConfig(
            policy=RetryPolicy.EXPONENTIAL,
            base_delay=60,     # 1 minute
            max_delay=1800,    # 30 minutes
            max_retries=5,
            factor=2.0
        )
    }
    
    # Error types that should not be retried
    NON_RETRYABLE_ERRORS = {
        'ValueError',
        'TypeError', 
        'KeyError',
        'AttributeError',
        'ImportError',
        'SyntaxError',
        'InvalidInputError',
        'AuthenticationError',
        'PermissionError'
    }
    
    def __init__(self, app: Celery, redis_client: Redis):
        self.app = app
        self.redis = redis_client
        self.strategies = {
            RetryPolicy.EXPONENTIAL: BackoffStrategy.exponential,
            RetryPolicy.LINEAR: BackoffStrategy.linear,
            RetryPolicy.FIBONACCI: BackoffStrategy.fibonacci,
            RetryPolicy.FIXED: BackoffStrategy.fixed
        }
    
    def handle_task_failure(self, task_id: str, task_name: str, args: list, 
                           kwargs: dict, exception: Exception, traceback: str,
                           queue: str = None) -> bool:
        """Handle failed task and decide on retry strategy"""
        
        # Create failure record
        failure_data = {
            'task_id': task_id,
            'task_name': task_name,
            'args': args,
            'kwargs': kwargs,
            'queue': queue or 'unknown',
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'traceback': traceback,
            'failed_at': datetime.now().isoformat(),
            'retry_count': kwargs.get('retry_count', 0)
        }
        
        # Check if error type is retryable
        if self._is_non_retryable_error(exception):
            logger.error(f"Task {task_id} failed with non-retryable error: {exception}")
            self._store_permanent_failure(failure_data)
            return False
        
        # Get retry policy for the queue
        retry_config = self._get_retry_policy(queue, task_name)
        
        # Check if max retries exceeded
        retry_count = failure_data['retry_count']
        if retry_count >= retry_config.max_retries:
            logger.error(f"Task {task_id} exceeded max retries ({retry_config.max_retries})")
            self._store_permanent_failure(failure_data)
            return False
        
        # Calculate retry delay
        delay = self._calculate_delay(retry_count, retry_config)
        
        # Schedule retry
        return self._schedule_retry(failure_data, delay, retry_config)
    
    def _is_non_retryable_error(self, exception: Exception) -> bool:
        """Check if error type should not be retried"""
        return type(exception).__name__ in self.NON_RETRYABLE_ERRORS
    
    def _get_retry_policy(self, queue: str, task_name: str) -> BackoffConfig:
        """Get retry policy for task based on queue and task type"""
        
        # First try queue-specific policy
        if queue and queue in self.DEFAULT_RETRY_POLICIES:
            return self.DEFAULT_RETRY_POLICIES[queue]
        
        # Try task name pattern matching
        task_name_lower = task_name.lower()
        if 'generate' in task_name_lower or 'create' in task_name_lower:
            return self.DEFAULT_RETRY_POLICIES['gpu.generation']
        elif 'process' in task_name_lower or 'analyze' in task_name_lower:
            return self.DEFAULT_RETRY_POLICIES['cpu.analysis']
        elif 'thumbnail' in task_name_lower or 'preview' in task_name_lower:
            return self.DEFAULT_RETRY_POLICIES['cpu.thumbnail']
        elif 'save' in task_name_lower or 'upload' in task_name_lower:
            return self.DEFAULT_RETRY_POLICIES['io.storage']
        
        # Default policy
        return self.DEFAULT_RETRY_POLICIES['default']
    
    def _calculate_delay(self, retry_count: int, config: BackoffConfig) -> int:
        """Calculate retry delay based on policy"""
        strategy = self.strategies[config.policy]
        return strategy(retry_count, config)
    
    def _schedule_retry(self, failure_data: dict, delay: int, config: BackoffConfig) -> bool:
        """Schedule task retry with delay"""
        try:
            # Increment retry count
            retry_kwargs = failure_data['kwargs'].copy()
            retry_kwargs['retry_count'] = failure_data['retry_count'] + 1
            retry_kwargs['original_task_id'] = failure_data['task_id']
            retry_kwargs['retry_delay'] = delay
            
            # Generate new task ID for retry
            import uuid
            new_task_id = str(uuid.uuid4())
            
            # Store retry metadata
            retry_metadata = {
                'original_task_id': failure_data['task_id'],
                'retry_count': retry_kwargs['retry_count'],
                'scheduled_at': datetime.now().isoformat(),
                'retry_delay': delay,
                'retry_policy': config.policy.value,
                'next_attempt_at': (datetime.now() + timedelta(seconds=delay)).isoformat()
            }
            
            self.redis.setex(
                f"retry_metadata:{new_task_id}",
                delay + 3600,  # Keep metadata for 1 hour after retry
                json.dumps(retry_metadata)
            )
            
            # Schedule the retry
            self.app.send_task(
                failure_data['task_name'],
                args=failure_data['args'],
                kwargs=retry_kwargs,
                countdown=delay,
                queue=failure_data['queue'],
                task_id=new_task_id
            )
            
            logger.info(
                f"Scheduled retry for task {failure_data['task_id']} -> {new_task_id} "
                f"after {delay}s (attempt {retry_kwargs['retry_count']}/{config.max_retries})"
            )
            
            # Store in DLQ for tracking
            self._store_in_dlq(failure_data, retry_metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule retry for task {failure_data['task_id']}: {e}")
            self._store_permanent_failure(failure_data)
            return False
    
    def _store_in_dlq(self, failure_data: dict, retry_metadata: dict):
        """Store failed task in dead letter queue for tracking"""
        dlq_entry = {
            **failure_data,
            'retry_metadata': retry_metadata,
            'dlq_stored_at': datetime.now().isoformat()
        }
        
        # Store in Redis list with TTL
        key = f"dlq:entries:{datetime.now().strftime('%Y-%m-%d')}"
        self.redis.lpush(key, json.dumps(dlq_entry))
        self.redis.expire(key, 86400 * 7)  # Keep for 7 days
        
        # Update DLQ metrics
        self._update_dlq_metrics(failure_data['queue'], failure_data['exception_type'])
    
    def _store_permanent_failure(self, failure_data: dict):
        """Store permanently failed task"""
        permanent_failure = {
            **failure_data,
            'permanently_failed_at': datetime.now().isoformat(),
            'reason': 'max_retries_exceeded' if failure_data['retry_count'] > 0 else 'non_retryable_error'
        }
        
        # Store in Redis with longer TTL
        key = f"permanent_failures:{datetime.now().strftime('%Y-%m')}"
        self.redis.lpush(key, json.dumps(permanent_failure))
        self.redis.expire(key, 86400 * 30)  # Keep for 30 days
        
        # Update failure metrics
        self._update_failure_metrics(failure_data['queue'], failure_data['exception_type'])
        
        logger.error(f"Task {failure_data['task_id']} permanently failed: {permanent_failure['reason']}")
    
    def _update_dlq_metrics(self, queue: str, exception_type: str):
        """Update DLQ metrics"""
        date_key = datetime.now().strftime('%Y-%m-%d')
        
        # Increment counters
        self.redis.hincrby(f"dlq_metrics:queue:{date_key}", queue, 1)
        self.redis.hincrby(f"dlq_metrics:error:{date_key}", exception_type, 1)
        self.redis.incr(f"dlq_metrics:total:{date_key}")
        
        # Set expiration
        self.redis.expire(f"dlq_metrics:queue:{date_key}", 86400 * 30)
        self.redis.expire(f"dlq_metrics:error:{date_key}", 86400 * 30)
        self.redis.expire(f"dlq_metrics:total:{date_key}", 86400 * 30)
    
    def _update_failure_metrics(self, queue: str, exception_type: str):
        """Update permanent failure metrics"""
        date_key = datetime.now().strftime('%Y-%m-%d')
        
        # Increment counters
        self.redis.hincrby(f"failure_metrics:queue:{date_key}", queue, 1)
        self.redis.hincrby(f"failure_metrics:error:{date_key}", exception_type, 1)
        self.redis.incr(f"failure_metrics:total:{date_key}")
        
        # Set expiration
        self.redis.expire(f"failure_metrics:queue:{date_key}", 86400 * 30)
        self.redis.expire(f"failure_metrics:error:{date_key}", 86400 * 30)
        self.redis.expire(f"failure_metrics:total:{date_key}", 86400 * 30)
    
    def get_dlq_stats(self, date: str = None) -> Dict[str, Any]:
        """Get dead letter queue statistics"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            queue_stats = self.redis.hgetall(f"dlq_metrics:queue:{date}")
            error_stats = self.redis.hgetall(f"dlq_metrics:error:{date}")
            total_dlq = self.redis.get(f"dlq_metrics:total:{date}")
            total_failures = self.redis.get(f"failure_metrics:total:{date}")
            
            return {
                'date': date,
                'dlq_by_queue': {k.decode(): int(v) for k, v in queue_stats.items()},
                'dlq_by_error': {k.decode(): int(v) for k, v in error_stats.items()},
                'total_dlq_entries': int(total_dlq) if total_dlq else 0,
                'total_permanent_failures': int(total_failures) if total_failures else 0
            }
        except Exception as e:
            logger.error(f"Error getting DLQ stats: {e}")
            return {'date': date, 'error': str(e)}
    
    def get_recent_failures(self, hours: int = 24) -> list:
        """Get recent failures from DLQ"""
        try:
            failures = []
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=hours)
            
            # Check each day in range
            current_date = start_date
            while current_date <= end_date:
                date_key = current_date.strftime('%Y-%m-%d')
                dlq_key = f"dlq:entries:{date_key}"
                
                entries = self.redis.lrange(dlq_key, 0, -1)
                for entry in entries:
                    try:
                        failure_data = json.loads(entry)
                        # Parse timestamp and filter by hour range
                        failed_at = datetime.fromisoformat(failure_data['failed_at'])
                        if start_date <= failed_at <= end_date:
                            failures.append(failure_data)
                    except Exception as e:
                        logger.warning(f"Could not parse DLQ entry: {e}")
                
                current_date += timedelta(days=1)
            
            # Sort by failure time (most recent first)
            failures.sort(key=lambda x: x['failed_at'], reverse=True)
            return failures
            
        except Exception as e:
            logger.error(f"Error getting recent failures: {e}")
            return []
    
    def retry_failed_task(self, task_id: str, force: bool = False) -> bool:
        """Manually retry a failed task"""
        try:
            # Find task in DLQ or permanent failures
            task_data = self._find_failed_task(task_id)
            if not task_data:
                logger.error(f"Failed task {task_id} not found")
                return False
            
            # Check if forcing retry or if within retry limits
            retry_config = self._get_retry_policy(task_data['queue'], task_data['task_name'])
            if not force and task_data['retry_count'] >= retry_config.max_retries:
                logger.error(f"Task {task_id} already exceeded max retries. Use force=True to override.")
                return False
            
            # Generate new task ID and schedule immediate retry
            import uuid
            new_task_id = str(uuid.uuid4())
            
            retry_kwargs = task_data['kwargs'].copy()
            retry_kwargs['retry_count'] = task_data['retry_count'] + 1
            retry_kwargs['original_task_id'] = task_id
            retry_kwargs['manual_retry'] = True
            
            self.app.send_task(
                task_data['task_name'],
                args=task_data['args'],
                kwargs=retry_kwargs,
                queue=task_data['queue'],
                task_id=new_task_id
            )
            
            logger.info(f"Manually retried task {task_id} -> {new_task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error manually retrying task {task_id}: {e}")
            return False
    
    def _find_failed_task(self, task_id: str) -> Optional[dict]:
        """Find failed task in DLQ or permanent failures"""
        # Search in recent DLQ entries
        for hours in [24, 168, 720]:  # 1 day, 1 week, 1 month
            failures = self.get_recent_failures(hours)
            for failure in failures:
                if failure['task_id'] == task_id:
                    return failure
        
        return None


# Global instance
dlq_handler = None


def get_dlq_handler(app: Celery, redis_client: Redis) -> DeadLetterQueueHandler:
    """Get or create DLQ handler instance"""
    global dlq_handler
    if dlq_handler is None:
        dlq_handler = DeadLetterQueueHandler(app, redis_client)
    return dlq_handler