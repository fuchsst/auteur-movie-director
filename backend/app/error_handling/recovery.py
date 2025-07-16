"""Recovery strategy implementations"""

import asyncio
import random
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .models import (
    ErrorContext, ErrorClassification, RecoveryResult,
    RecoveryStrategy as RecoveryStrategyEnum
)
from .context import ErrorContextManager

logger = logging.getLogger(__name__)


class RecoveryStrategy(ABC):
    """Base recovery strategy"""
    
    @abstractmethod
    async def recover(
        self,
        context: ErrorContext,
        error: Exception,
        classification: ErrorClassification
    ) -> RecoveryResult:
        """Execute recovery strategy"""
        pass


class RetryWithBackoffStrategy(RecoveryStrategy):
    """Retry with exponential backoff"""
    
    def __init__(self, task_queue=None):
        self.base_delay = 1.0  # seconds
        self.max_delay = 60.0
        self.jitter_factor = 0.1
        self.task_queue = task_queue
    
    async def recover(
        self,
        context: ErrorContext,
        error: Exception,
        classification: ErrorClassification
    ) -> RecoveryResult:
        """Attempt recovery through retry"""
        
        max_retries = classification.metadata.get('max_retries', 3)
        attempt = context.retry_count + 1
        
        if attempt > max_retries:
            return RecoveryResult(
                success=False,
                action='max_retries_exceeded',
                reason=f'Exceeded maximum retries ({max_retries})'
            )
        
        # Calculate delay with exponential backoff
        delay = min(
            self.base_delay * (2 ** (attempt - 1)),
            self.max_delay
        )
        
        # Add jitter to prevent thundering herd
        jitter = delay * self.jitter_factor * (2 * random.random() - 1)
        delay = max(0, delay + jitter)
        
        logger.info(
            f"Retrying task {context.task_id} after {delay:.2f}s "
            f"(attempt {attempt}/{max_retries})"
        )
        
        # Schedule retry
        if self.task_queue:
            # Re-submit task with updated retry count
            retry_task = context.original_task.copy()
            retry_task['retry_count'] = attempt
            retry_task['previous_error'] = str(error)
            retry_task['retry_delay'] = delay
            
            # Schedule task after delay
            asyncio.create_task(self._delayed_submit(retry_task, delay))
        
        return RecoveryResult(
            success=True,
            action='retry_scheduled',
            metadata={
                'attempt': attempt,
                'delay': delay,
                'next_attempt_at': (datetime.now() + timedelta(seconds=delay)).isoformat()
            }
        )
    
    async def _delayed_submit(self, task: Dict[str, Any], delay: float):
        """Submit task after delay"""
        await asyncio.sleep(delay)
        if self.task_queue:
            await self.task_queue.submit(task)


class QueueAndWaitStrategy(RecoveryStrategy):
    """Queue task and wait for resources"""
    
    def __init__(self, resource_queue=None):
        self.resource_queue = resource_queue
        self.default_wait_time = 300  # 5 minutes
    
    async def recover(
        self,
        context: ErrorContext,
        error: Exception,
        classification: ErrorClassification
    ) -> RecoveryResult:
        """Queue task to wait for resources"""
        
        wait_time = classification.metadata.get('wait_time', self.default_wait_time)
        
        if self.resource_queue:
            # Add to resource waiting queue
            await self.resource_queue.add_waiting_task({
                'task': context.original_task,
                'reason': str(error),
                'wait_until': datetime.now() + timedelta(seconds=wait_time)
            })
        
        logger.info(
            f"Task {context.task_id} queued for resource availability "
            f"(wait time: {wait_time}s)"
        )
        
        return RecoveryResult(
            success=True,
            action='queued_for_resources',
            metadata={
                'wait_time': wait_time,
                'reason': str(error)
            }
        )


class FailFastStrategy(RecoveryStrategy):
    """Fail immediately without retry"""
    
    def __init__(self, notification_service=None):
        self.notification_service = notification_service
    
    async def recover(
        self,
        context: ErrorContext,
        error: Exception,
        classification: ErrorClassification
    ) -> RecoveryResult:
        """Fail fast and notify"""
        
        # Send notification if configured
        if classification.metadata.get('notify_user') and self.notification_service:
            await self.notification_service.notify_error(
                task_id=context.task_id,
                error=str(error),
                severity=classification.severity
            )
        
        logger.warning(
            f"Task {context.task_id} failed with validation error: {error}"
        )
        
        return RecoveryResult(
            success=False,
            action='failed_validation',
            reason=str(error),
            metadata={
                'notified': classification.metadata.get('notify_user', False)
            }
        )


class DeadLetterQueueStrategy(RecoveryStrategy):
    """Move to dead letter queue for manual intervention"""
    
    def __init__(self, dead_letter_queue=None, alert_service=None):
        self.dead_letter_queue = dead_letter_queue
        self.alert_service = alert_service
    
    async def recover(
        self,
        context: ErrorContext,
        error: Exception,
        classification: ErrorClassification
    ) -> RecoveryResult:
        """Move to dead letter queue"""
        
        # Add to dead letter queue
        if self.dead_letter_queue:
            await self.dead_letter_queue.add({
                'task': context.original_task,
                'error': str(error),
                'classification': classification.model_dump(),
                'context': context.model_dump(),
                'timestamp': datetime.now().isoformat()
            })
        
        # Alert admin if configured
        if classification.metadata.get('alert_admin') and self.alert_service:
            await self.alert_service.send_alert(
                level='critical',
                message=f"Task {context.task_id} moved to dead letter queue",
                details={
                    'error': str(error),
                    'task_type': context.template_id
                }
            )
        
        logger.error(
            f"Task {context.task_id} moved to dead letter queue: {error}"
        )
        
        return RecoveryResult(
            success=False,
            action='dead_letter_queue',
            reason='Permanent failure - manual intervention required',
            metadata={
                'alerted': classification.metadata.get('alert_admin', False)
            }
        )


class RecoveryManager:
    """Manage error recovery strategies"""
    
    def __init__(
        self,
        task_queue=None,
        resource_queue=None,
        dead_letter_queue=None,
        notification_service=None,
        alert_service=None
    ):
        self.strategies = {
            RecoveryStrategyEnum.RETRY_WITH_BACKOFF: RetryWithBackoffStrategy(task_queue),
            RecoveryStrategyEnum.QUEUE_AND_WAIT: QueueAndWaitStrategy(resource_queue),
            RecoveryStrategyEnum.FAIL_FAST: FailFastStrategy(notification_service),
            RecoveryStrategyEnum.DEAD_LETTER_QUEUE: DeadLetterQueueStrategy(
                dead_letter_queue, alert_service
            ),
            RecoveryStrategyEnum.RETRY_ONCE: RetryWithBackoffStrategy(task_queue)
        }
        
        self.context_manager = ErrorContextManager()
        self._recovery_metrics = {
            'total_attempts': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0
        }
    
    async def handle_error(
        self,
        context: ErrorContext,
        error: Exception,
        classification: ErrorClassification
    ) -> RecoveryResult:
        """Handle an error with appropriate recovery strategy"""
        
        # Log error
        await self._log_error(context, error, classification)
        
        # Add to error history
        self.context_manager.add_error_to_history(context.task_id, classification)
        
        # Check if we should attempt recovery
        if not self._should_attempt_recovery(context, classification):
            return RecoveryResult(
                success=False,
                action='abandoned',
                reason='Max recovery attempts exceeded or non-recoverable error'
            )
        
        # Get recovery strategy
        strategy = self.strategies.get(classification.strategy)
        if not strategy:
            strategy = self.strategies[RecoveryStrategyEnum.FAIL_FAST]
        
        # Execute recovery
        try:
            result = await strategy.recover(context, error, classification)
            
            # Record recovery attempt
            self.context_manager.add_recovery_attempt(context.task_id, result)
            
            # Update metrics
            self._recovery_metrics['total_attempts'] += 1
            if result.success:
                self._recovery_metrics['successful_recoveries'] += 1
            else:
                self._recovery_metrics['failed_recoveries'] += 1
            
            return result
            
        except Exception as recovery_error:
            logger.error(f"Recovery failed: {recovery_error}")
            self._recovery_metrics['failed_recoveries'] += 1
            
            return RecoveryResult(
                success=False,
                action='recovery_failed',
                error=str(recovery_error)
            )
    
    def _should_attempt_recovery(
        self,
        context: ErrorContext,
        classification: ErrorClassification
    ) -> bool:
        """Determine if recovery should be attempted"""
        
        # Check if error is recoverable
        if not classification.recoverable:
            return False
        
        # Check recovery history
        recent_errors = self.context_manager.get_recent_errors(
            context.task_id,
            minutes=5
        )
        
        if len(recent_errors) >= 5:
            logger.warning(
                f"Too many recovery attempts for task {context.task_id}"
            )
            return False
        
        return True
    
    async def _log_error(
        self,
        context: ErrorContext,
        error: Exception,
        classification: ErrorClassification
    ):
        """Log error details"""
        logger.error(
            f"Error in task {context.task_id}: {error}",
            extra={
                'task_id': context.task_id,
                'template_id': context.template_id,
                'error_category': classification.category,
                'error_type': classification.error_type,
                'recoverable': classification.recoverable,
                'strategy': classification.strategy
            }
        )
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        total = self._recovery_metrics['total_attempts']
        successful = self._recovery_metrics['successful_recoveries']
        
        return {
            'total_attempts': total,
            'successful_recoveries': successful,
            'failed_recoveries': self._recovery_metrics['failed_recoveries'],
            'success_rate': successful / total if total > 0 else 0
        }