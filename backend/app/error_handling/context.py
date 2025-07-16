"""Error context management"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .models import ErrorContext, ErrorHistory, ErrorClassification, RecoveryResult


class ErrorContextManager:
    """Manage error contexts for tasks"""
    
    def __init__(self):
        self._contexts: Dict[str, ErrorContext] = {}
        self._histories: Dict[str, ErrorHistory] = {}
    
    def create_context(
        self,
        task_id: str,
        template_id: str,
        operation_type: str,
        original_task: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """Create error context for a task"""
        context = ErrorContext(
            task_id=task_id,
            template_id=template_id,
            operation_type=operation_type,
            original_task=original_task,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        self._contexts[task_id] = context
        
        # Initialize history if not exists
        if task_id not in self._histories:
            self._histories[task_id] = ErrorHistory(task_id=task_id)
            
        return context
    
    def get_context(self, task_id: str) -> Optional[ErrorContext]:
        """Get error context for a task"""
        return self._contexts.get(task_id)
    
    def update_context(
        self, 
        task_id: str, 
        retry_count: Optional[int] = None,
        metadata_update: Optional[Dict[str, Any]] = None
    ) -> Optional[ErrorContext]:
        """Update error context"""
        context = self._contexts.get(task_id)
        if not context:
            return None
            
        if retry_count is not None:
            context.retry_count = retry_count
            
        if metadata_update:
            context.metadata.update(metadata_update)
            
        return context
    
    def add_error_to_history(
        self, 
        task_id: str, 
        classification: ErrorClassification
    ):
        """Add error to task history"""
        history = self._histories.get(task_id)
        if not history:
            history = ErrorHistory(task_id=task_id)
            self._histories[task_id] = history
            
        history.errors.append(classification)
        history.last_error_time = datetime.now()
    
    def add_recovery_attempt(
        self,
        task_id: str,
        result: RecoveryResult
    ):
        """Add recovery attempt to history"""
        history = self._histories.get(task_id)
        if not history:
            history = ErrorHistory(task_id=task_id)
            self._histories[task_id] = history
            
        history.recovery_attempts.append(result)
        if result.action == 'retry_scheduled':
            history.total_retries += 1
    
    def get_history(self, task_id: str) -> Optional[ErrorHistory]:
        """Get error history for a task"""
        return self._histories.get(task_id)
    
    def get_recent_errors(
        self, 
        task_id: str, 
        minutes: int = 5
    ) -> List[ErrorClassification]:
        """Get recent errors for a task"""
        history = self._histories.get(task_id)
        if not history:
            return []
            
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        return [
            error for error in history.errors
            if error.timestamp.timestamp() > cutoff_time
        ]
    
    def cleanup_old_contexts(self, hours: int = 24):
        """Clean up old contexts"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        # Clean up contexts
        old_contexts = [
            task_id for task_id, context in self._contexts.items()
            if context.start_time.timestamp() < cutoff_time
        ]
        
        for task_id in old_contexts:
            del self._contexts[task_id]
            
        # Clean up histories
        old_histories = [
            task_id for task_id, history in self._histories.items()
            if history.last_error_time and 
            history.last_error_time.timestamp() < cutoff_time
        ]
        
        for task_id in old_histories:
            del self._histories[task_id]