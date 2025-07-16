"""Compensation and rollback mechanisms"""

import asyncio
import logging
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
import os

from .models import CompensationResult

logger = logging.getLogger(__name__)


class Operation:
    """Represents an operation that may need compensation"""
    
    def __init__(
        self,
        operation_id: str,
        operation_type: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        self.operation_id = operation_id
        self.type = operation_type
        self.data = data
        self.timestamp = timestamp or datetime.now()


class CompensationManager:
    """Handle compensation logic for failed operations"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self.compensation_handlers: Dict[str, Callable] = {
            'file_upload': self._compensate_file_upload,
            'resource_allocation': self._compensate_resource_allocation,
            'task_submission': self._compensate_task_submission,
            'model_loading': self._compensate_model_loading,
            'output_generation': self._compensate_output_generation,
            'database_write': self._compensate_database_write,
            'queue_operation': self._compensate_queue_operation
        }
        self.compensation_history: List[CompensationResult] = []
        self._failed_compensations: List[Dict[str, Any]] = []
    
    async def compensate(
        self,
        operation: Operation,
        error: Exception
    ) -> CompensationResult:
        """Execute compensation logic for failed operation"""
        
        handler = self.compensation_handlers.get(operation.type)
        if not handler:
            logger.warning(
                f"No compensation handler for operation type: {operation.type}"
            )
            return CompensationResult(
                success=False,
                operation_type=operation.type,
                action_taken="no_handler",
                error="No compensation handler available"
            )
        
        try:
            result = await handler(operation, error)
            logger.info(
                f"Successfully compensated for failed {operation.type}: "
                f"{result.action_taken}"
            )
            
            self.compensation_history.append(result)
            return result
            
        except Exception as comp_error:
            logger.error(f"Compensation failed: {comp_error}")
            
            # Record compensation failure for manual intervention
            await self._record_compensation_failure(operation, error, comp_error)
            
            result = CompensationResult(
                success=False,
                operation_type=operation.type,
                action_taken="compensation_failed",
                error=str(comp_error)
            )
            
            self.compensation_history.append(result)
            return result
    
    async def _compensate_file_upload(
        self,
        operation: Operation,
        error: Exception
    ) -> CompensationResult:
        """Clean up partially uploaded files"""
        file_path = operation.data.get('file_path')
        
        if not file_path:
            return CompensationResult(
                success=True,
                operation_type=operation.type,
                action_taken="no_file_to_clean"
            )
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up partial upload: {file_path}")
                
                # Also clean up any temporary files
                temp_path = operation.data.get('temp_path')
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                
                return CompensationResult(
                    success=True,
                    operation_type=operation.type,
                    action_taken=f"removed_file: {file_path}"
                )
            else:
                return CompensationResult(
                    success=True,
                    operation_type=operation.type,
                    action_taken="file_not_found"
                )
                
        except Exception as e:
            return CompensationResult(
                success=False,
                operation_type=operation.type,
                action_taken="cleanup_failed",
                error=str(e)
            )
    
    async def _compensate_resource_allocation(
        self,
        operation: Operation,
        error: Exception
    ) -> CompensationResult:
        """Release allocated resources"""
        allocation_id = operation.data.get('allocation_id')
        resource_type = operation.data.get('resource_type', 'unknown')
        
        if not allocation_id:
            return CompensationResult(
                success=True,
                operation_type=operation.type,
                action_taken="no_allocation_to_release"
            )
        
        try:
            # Import here to avoid circular dependency
            from ..services.resource_manager import resource_manager
            
            if resource_manager:
                await resource_manager.release_allocation(allocation_id)
                logger.info(
                    f"Released {resource_type} allocation: {allocation_id}"
                )
            
            return CompensationResult(
                success=True,
                operation_type=operation.type,
                action_taken=f"released_{resource_type}: {allocation_id}"
            )
            
        except Exception as e:
            return CompensationResult(
                success=False,
                operation_type=operation.type,
                action_taken="release_failed",
                error=str(e)
            )
    
    async def _compensate_task_submission(
        self,
        operation: Operation,
        error: Exception
    ) -> CompensationResult:
        """Cancel submitted task"""
        task_id = operation.data.get('task_id')
        queue_name = operation.data.get('queue_name', 'default')
        
        if not task_id:
            return CompensationResult(
                success=True,
                operation_type=operation.type,
                action_taken="no_task_to_cancel"
            )
        
        try:
            # Import here to avoid circular dependency
            from ..services.task_queue import task_queue
            
            if task_queue:
                cancelled = await task_queue.cancel_task(task_id, queue_name)
                if cancelled:
                    logger.info(f"Cancelled task: {task_id}")
                    action = f"cancelled_task: {task_id}"
                else:
                    action = f"task_already_processed: {task_id}"
            else:
                action = "task_queue_not_available"
            
            return CompensationResult(
                success=True,
                operation_type=operation.type,
                action_taken=action
            )
            
        except Exception as e:
            return CompensationResult(
                success=False,
                operation_type=operation.type,
                action_taken="cancellation_failed",
                error=str(e)
            )
    
    async def _compensate_model_loading(
        self,
        operation: Operation,
        error: Exception
    ) -> CompensationResult:
        """Unload or clean up loaded models"""
        model_id = operation.data.get('model_id')
        gpu_id = operation.data.get('gpu_id')
        
        if not model_id:
            return CompensationResult(
                success=True,
                operation_type=operation.type,
                action_taken="no_model_to_unload"
            )
        
        try:
            # Import here to avoid circular dependency
            from ..services.model_manager import model_manager
            
            if model_manager:
                await model_manager.unload_model(model_id, gpu_id)
                logger.info(f"Unloaded model: {model_id}")
            
            return CompensationResult(
                success=True,
                operation_type=operation.type,
                action_taken=f"unloaded_model: {model_id}"
            )
            
        except Exception as e:
            return CompensationResult(
                success=False,
                operation_type=operation.type,
                action_taken="unload_failed",
                error=str(e)
            )
    
    async def _compensate_output_generation(
        self,
        operation: Operation,
        error: Exception
    ) -> CompensationResult:
        """Clean up partial outputs"""
        output_paths = operation.data.get('output_paths', [])
        
        if not output_paths:
            return CompensationResult(
                success=True,
                operation_type=operation.type,
                action_taken="no_outputs_to_clean"
            )
        
        cleaned = []
        failed = []
        
        for path in output_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    cleaned.append(path)
                    logger.info(f"Cleaned up partial output: {path}")
            except Exception as e:
                failed.append((path, str(e)))
        
        if failed:
            return CompensationResult(
                success=False,
                operation_type=operation.type,
                action_taken=f"partial_cleanup: cleaned={len(cleaned)}, failed={len(failed)}",
                error=f"Failed to clean some outputs: {failed}"
            )
        
        return CompensationResult(
            success=True,
            operation_type=operation.type,
            action_taken=f"cleaned_outputs: {len(cleaned)} files"
        )
    
    async def _compensate_database_write(
        self,
        operation: Operation,
        error: Exception
    ) -> CompensationResult:
        """Rollback database changes"""
        transaction_id = operation.data.get('transaction_id')
        table_name = operation.data.get('table_name')
        record_id = operation.data.get('record_id')
        
        if not transaction_id:
            return CompensationResult(
                success=True,
                operation_type=operation.type,
                action_taken="no_transaction_to_rollback"
            )
        
        # This would connect to actual database
        # For now, just log the action
        logger.info(
            f"Would rollback transaction {transaction_id} "
            f"for table {table_name}, record {record_id}"
        )
        
        return CompensationResult(
            success=True,
            operation_type=operation.type,
            action_taken=f"rollback_logged: {transaction_id}"
        )
    
    async def _compensate_queue_operation(
        self,
        operation: Operation,
        error: Exception
    ) -> CompensationResult:
        """Compensate queue operations"""
        queue_op = operation.data.get('queue_operation')
        queue_name = operation.data.get('queue_name')
        message_id = operation.data.get('message_id')
        
        if queue_op == 'publish' and message_id:
            # Would remove message from queue
            logger.info(
                f"Would remove message {message_id} from queue {queue_name}"
            )
            action = f"message_removal_logged: {message_id}"
        else:
            action = "no_queue_action_needed"
        
        return CompensationResult(
            success=True,
            operation_type=operation.type,
            action_taken=action
        )
    
    async def _record_compensation_failure(
        self,
        operation: Operation,
        original_error: Exception,
        compensation_error: Exception
    ):
        """Record compensation failure for manual intervention"""
        failure_record = {
            'timestamp': datetime.now().isoformat(),
            'operation': {
                'id': operation.operation_id,
                'type': operation.type,
                'data': operation.data
            },
            'original_error': str(original_error),
            'compensation_error': str(compensation_error)
        }
        
        self._failed_compensations.append(failure_record)
        
        # In production, this would persist to a database or file
        logger.error(
            f"Compensation failure recorded for manual intervention: "
            f"{failure_record}"
        )
    
    def get_compensation_stats(self) -> Dict[str, Any]:
        """Get compensation statistics"""
        total = len(self.compensation_history)
        successful = sum(1 for r in self.compensation_history if r.success)
        
        return {
            'total_compensations': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': successful / total if total > 0 else 0,
            'failed_compensations_pending': len(self._failed_compensations)
        }
    
    def get_failed_compensations(self) -> List[Dict[str, Any]]:
        """Get list of failed compensations requiring manual intervention"""
        return self._failed_compensations.copy()