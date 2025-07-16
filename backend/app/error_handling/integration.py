"""Integration module for error handling with function runner"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable

from .classifier import ErrorClassifier
from .recovery import RecoveryManager
from .circuit_breaker import CircuitBreakerManager, CircuitBreakerOpenError
from .compensation import CompensationManager, Operation
from .analytics import ErrorAnalytics
from .self_healing import SelfHealingSystem
from .context import ErrorContextManager
from .models import ErrorContext

logger = logging.getLogger(__name__)


class ErrorHandlingIntegration:
    """Integration layer for error handling in function runner"""
    
    def __init__(
        self,
        task_queue=None,
        resource_queue=None,
        dead_letter_queue=None,
        notification_service=None,
        alert_service=None,
        worker_manager=None,
        queue_manager=None,
        resource_monitor=None,
        storage_manager=None
    ):
        # Initialize components
        self.classifier = ErrorClassifier()
        self.circuit_breakers = CircuitBreakerManager()
        self.compensation = CompensationManager()
        self.analytics = ErrorAnalytics(alert_service)
        self.context_manager = ErrorContextManager()
        
        # Initialize recovery manager
        self.recovery = RecoveryManager(
            task_queue=task_queue,
            resource_queue=resource_queue,
            dead_letter_queue=dead_letter_queue,
            notification_service=notification_service,
            alert_service=alert_service
        )
        
        # Initialize self-healing
        self.self_healing = SelfHealingSystem(
            worker_manager=worker_manager,
            queue_manager=queue_manager,
            resource_monitor=resource_monitor,
            storage_manager=storage_manager
        )
        
        self._running = False
    
    async def start(self):
        """Start error handling systems"""
        if self._running:
            return
            
        self._running = True
        
        # Start self-healing
        await self.self_healing.start()
        
        # Start periodic cleanup
        asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Error handling integration started")
    
    async def stop(self):
        """Stop error handling systems"""
        self._running = False
        
        # Stop self-healing
        await self.self_healing.stop()
        
        logger.info("Error handling integration stopped")
    
    async def wrap_task_execution(
        self,
        task_id: str,
        template_id: str,
        operation_type: str,
        task_data: Dict[str, Any],
        execute_func: Callable
    ) -> Any:
        """Wrap task execution with error handling"""
        
        # Create error context
        context = self.context_manager.create_context(
            task_id=task_id,
            template_id=template_id,
            operation_type=operation_type,
            original_task=task_data
        )
        
        # Get circuit breaker for service
        service_name = task_data.get('service', 'default')
        breaker = self.circuit_breakers.get_breaker(service_name)
        
        try:
            # Execute with circuit breaker protection
            result = await breaker.call(execute_func, task_data)
            return result
            
        except CircuitBreakerOpenError as e:
            # Circuit is open, fail fast
            logger.error(f"Circuit breaker open for {service_name}: {e}")
            raise
            
        except Exception as e:
            # Handle error
            await self._handle_task_error(context, e)
            raise
    
    async def _handle_task_error(
        self,
        context: ErrorContext,
        error: Exception
    ):
        """Handle task execution error"""
        
        # Classify error
        classification = self.classifier.classify_error(error, {
            'task_id': context.task_id,
            'template_id': context.template_id,
            'operation': context.operation_type
        })
        
        # Record in analytics
        await self.analytics.record_error(classification)
        
        # Attempt recovery
        recovery_result = await self.recovery.handle_error(
            context,
            error,
            classification
        )
        
        # Record recovery attempt
        await self.analytics.record_recovery_attempt(
            classification.category,
            recovery_result.success
        )
        
        # If recovery failed, attempt compensation
        if not recovery_result.success:
            operation = Operation(
                operation_id=context.task_id,
                operation_type=context.operation_type,
                data=context.original_task
            )
            
            await self.compensation.compensate(operation, error)
    
    async def handle_worker_error(
        self,
        worker_id: str,
        error: Exception
    ):
        """Handle worker-level error"""
        
        # Classify error
        classification = self.classifier.classify_error(error, {
            'worker_id': worker_id
        })
        
        # Record in analytics
        await self.analytics.record_error(classification)
        
        # Worker errors often need self-healing
        if classification.category in ['resource', 'permanent']:
            # Trigger immediate diagnostic
            await self.self_healing.diagnose_and_heal()
    
    async def protect_external_call(
        self,
        service: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Protect external service call with circuit breaker"""
        breaker = self.circuit_breakers.get_breaker(service)
        
        try:
            return await breaker.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            # Circuit open, return cached or default response
            logger.warning(f"Circuit breaker open for {service}, using fallback")
            return kwargs.get('fallback', None)
    
    async def get_error_analysis(self) -> Dict[str, Any]:
        """Get comprehensive error analysis"""
        
        # Get analytics report
        report = await self.analytics.analyze_error_patterns()
        
        # Get circuit breaker status
        breaker_stats = self.circuit_breakers.get_all_stats()
        
        # Get recovery stats
        recovery_stats = self.recovery.get_recovery_stats()
        
        # Get compensation stats
        compensation_stats = self.compensation.get_compensation_stats()
        
        # Get self-healing stats
        healing_stats = self.self_healing.get_healing_stats()
        
        return {
            'error_analysis': report.model_dump(),
            'circuit_breakers': breaker_stats,
            'recovery': recovery_stats,
            'compensation': compensation_stats,
            'self_healing': healing_stats,
            'health_status': self.circuit_breakers.get_health_status()
        }
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old data"""
        while self._running:
            try:
                # Clean up old contexts
                self.context_manager.cleanup_old_contexts(hours=24)
                
                # Wait 1 hour
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")


# Decorator for error handling
def with_error_handling(
    operation_type: str,
    service: str = 'default'
):
    """Decorator to add error handling to async functions"""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Get error handler from context
            error_handler = getattr(self, '_error_handler', None)
            if not error_handler:
                # No error handler, execute normally
                return await func(self, *args, **kwargs)
            
            # Create task context
            task_id = kwargs.get('task_id', f"{operation_type}_{datetime.now().timestamp()}")
            template_id = kwargs.get('template_id', 'unknown')
            
            return await error_handler.wrap_task_execution(
                task_id=task_id,
                template_id=template_id,
                operation_type=operation_type,
                task_data=kwargs,
                execute_func=lambda data: func(self, *args, **kwargs)
            )
        
        return wrapper
    return decorator


# Context manager for error handling
class ErrorHandlingContext:
    """Context manager for error handling"""
    
    def __init__(
        self,
        error_handler: ErrorHandlingIntegration,
        task_id: str,
        template_id: str,
        operation_type: str,
        task_data: Dict[str, Any]
    ):
        self.error_handler = error_handler
        self.task_id = task_id
        self.template_id = template_id
        self.operation_type = operation_type
        self.task_data = task_data
        self.context = None
        self.operations = []
    
    async def __aenter__(self):
        """Enter context"""
        self.context = self.error_handler.context_manager.create_context(
            task_id=self.task_id,
            template_id=self.template_id,
            operation_type=self.operation_type,
            original_task=self.task_data
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        if exc_type is not None:
            # Error occurred, handle it
            await self.error_handler._handle_task_error(
                self.context,
                exc_val
            )
            
            # Compensate operations
            for operation in reversed(self.operations):
                await self.error_handler.compensation.compensate(
                    operation,
                    exc_val
                )
        
        return False  # Don't suppress exceptions
    
    def record_operation(
        self,
        operation_type: str,
        data: Dict[str, Any]
    ):
        """Record an operation for potential compensation"""
        operation = Operation(
            operation_id=f"{self.task_id}_{len(self.operations)}",
            operation_type=operation_type,
            data=data
        )
        self.operations.append(operation)