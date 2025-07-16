"""Self-healing mechanisms for automatic system recovery"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime, timedelta
import psutil

from .models import SystemIssue, HealingResult, HealingRecord, ErrorSeverity

logger = logging.getLogger(__name__)


class SystemDiagnostics:
    """System health diagnostics"""
    
    def __init__(self):
        self.checks = {
            'worker_health': self._check_worker_health,
            'queue_depth': self._check_queue_depth,
            'resource_usage': self._check_resource_usage,
            'model_integrity': self._check_model_integrity,
            'storage_space': self._check_storage_space,
            'network_connectivity': self._check_network_connectivity,
            'service_availability': self._check_service_availability
        }
    
    async def run_diagnostics(self) -> List[SystemIssue]:
        """Run all diagnostic checks"""
        issues = []
        
        for check_name, check_func in self.checks.items():
            try:
                check_issues = await check_func()
                issues.extend(check_issues)
            except Exception as e:
                logger.error(f"Diagnostic check {check_name} failed: {e}")
                issues.append(SystemIssue(
                    type='diagnostic_failure',
                    severity=ErrorSeverity.MEDIUM,
                    target=check_name,
                    details={'error': str(e)}
                ))
        
        return issues
    
    async def _check_worker_health(self) -> List[SystemIssue]:
        """Check worker health status"""
        issues = []
        
        try:
            # Import here to avoid circular dependency
            from ..services.worker_manager import worker_manager
            
            if worker_manager:
                unhealthy_workers = await worker_manager.get_unhealthy_workers()
                
                for worker in unhealthy_workers:
                    issues.append(SystemIssue(
                        type='worker_unresponsive',
                        severity=ErrorSeverity.HIGH,
                        target=worker.id,
                        details={
                            'last_heartbeat': worker.last_heartbeat.isoformat() if worker.last_heartbeat else None,
                            'status': worker.status
                        }
                    ))
        except Exception as e:
            logger.error(f"Worker health check failed: {e}")
        
        return issues
    
    async def _check_queue_depth(self) -> List[SystemIssue]:
        """Check task queue depth"""
        issues = []
        
        try:
            # Import here to avoid circular dependency
            from ..services.task_queue import queue_manager
            
            if queue_manager:
                stats = await queue_manager.get_stats()
                
                # Check for queue backlog
                if stats.depth > stats.processing_rate * 300:  # 5 min backlog
                    issues.append(SystemIssue(
                        type='queue_backlog',
                        severity=ErrorSeverity.MEDIUM,
                        details={
                            'depth': stats.depth,
                            'rate': stats.processing_rate,
                            'estimated_wait': stats.depth / stats.processing_rate if stats.processing_rate > 0 else float('inf')
                        }
                    ))
                
                # Check for stalled queue
                if stats.processing_rate == 0 and stats.depth > 0:
                    issues.append(SystemIssue(
                        type='queue_stalled',
                        severity=ErrorSeverity.HIGH,
                        details={'depth': stats.depth}
                    ))
        except Exception as e:
            logger.error(f"Queue depth check failed: {e}")
        
        return issues
    
    async def _check_resource_usage(self) -> List[SystemIssue]:
        """Check system resource usage"""
        issues = []
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                issues.append(SystemIssue(
                    type='high_cpu_usage',
                    severity=ErrorSeverity.HIGH,
                    details={'cpu_percent': cpu_percent}
                ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                issues.append(SystemIssue(
                    type='resource_leak',
                    severity=ErrorSeverity.HIGH,
                    details={
                        'memory_percent': memory.percent,
                        'available_mb': memory.available / (1024 * 1024)
                    }
                ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 95:
                issues.append(SystemIssue(
                    type='low_disk_space',
                    severity=ErrorSeverity.CRITICAL,
                    details={
                        'disk_percent': disk.percent,
                        'free_gb': disk.free / (1024 * 1024 * 1024)
                    }
                ))
        except Exception as e:
            logger.error(f"Resource usage check failed: {e}")
        
        return issues
    
    async def _check_model_integrity(self) -> List[SystemIssue]:
        """Check AI model integrity"""
        issues = []
        
        # This would check model files, checksums, etc.
        # For now, just a placeholder
        return issues
    
    async def _check_storage_space(self) -> List[SystemIssue]:
        """Check storage space for outputs"""
        issues = []
        
        try:
            # Check workspace directory
            workspace_disk = psutil.disk_usage('./workspace')
            if workspace_disk.percent > 90:
                issues.append(SystemIssue(
                    type='workspace_full',
                    severity=ErrorSeverity.HIGH,
                    details={
                        'percent_used': workspace_disk.percent,
                        'free_gb': workspace_disk.free / (1024 * 1024 * 1024)
                    }
                ))
        except Exception as e:
            logger.error(f"Storage space check failed: {e}")
        
        return issues
    
    async def _check_network_connectivity(self) -> List[SystemIssue]:
        """Check network connectivity to external services"""
        issues = []
        
        # This would ping external services
        # For now, just a placeholder
        return issues
    
    async def _check_service_availability(self) -> List[SystemIssue]:
        """Check availability of dependent services"""
        issues = []
        
        # This would check Redis, database, etc.
        # For now, just a placeholder
        return issues


class SelfHealingSystem:
    """Automatic remediation for common issues"""
    
    def __init__(
        self,
        worker_manager=None,
        queue_manager=None,
        resource_monitor=None,
        storage_manager=None
    ):
        self.worker_manager = worker_manager
        self.queue_manager = queue_manager
        self.resource_monitor = resource_monitor
        self.storage_manager = storage_manager
        
        self.diagnostics = SystemDiagnostics()
        self.healing_actions = {
            'worker_unresponsive': self._heal_unresponsive_worker,
            'queue_backlog': self._heal_queue_backlog,
            'queue_stalled': self._heal_stalled_queue,
            'resource_leak': self._heal_resource_leak,
            'high_cpu_usage': self._heal_high_cpu,
            'low_disk_space': self._heal_low_disk_space,
            'workspace_full': self._heal_workspace_full,
            'model_corruption': self._heal_model_corruption
        }
        
        self.healing_history: List[HealingRecord] = []
        self._running = False
        self._healing_task = None
    
    async def start(self):
        """Start self-healing system"""
        if self._running:
            return
            
        self._running = True
        self._healing_task = asyncio.create_task(self._healing_loop())
        logger.info("Self-healing system started")
    
    async def stop(self):
        """Stop self-healing system"""
        self._running = False
        if self._healing_task:
            self._healing_task.cancel()
            try:
                await self._healing_task
            except asyncio.CancelledError:
                pass
        logger.info("Self-healing system stopped")
    
    async def _healing_loop(self):
        """Continuous diagnosis and healing loop"""
        while self._running:
            try:
                # Run diagnostics
                issues = await self.diagnostics.run_diagnostics()
                
                # Log issues
                if issues:
                    logger.info(f"Detected {len(issues)} system issues")
                
                # Attempt healing for each issue
                for issue in issues:
                    if not self._running:
                        break
                    await self._attempt_healing(issue)
                
                # Wait before next check
                await asyncio.sleep(60)  # Run every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Self-healing error: {e}")
                await asyncio.sleep(300)  # Back off on error
    
    async def diagnose_and_heal(self) -> List[HealingResult]:
        """Run single diagnostic and healing cycle"""
        issues = await self.diagnostics.run_diagnostics()
        results = []
        
        for issue in issues:
            result = await self._attempt_healing(issue)
            if result:
                results.append(result)
        
        return results
    
    async def _attempt_healing(self, issue: SystemIssue) -> Optional[HealingResult]:
        """Attempt to heal a system issue"""
        
        handler = self.healing_actions.get(issue.type)
        if not handler:
            logger.warning(
                f"No healing action for issue type: {issue.type}"
            )
            return None
        
        logger.info(
            f"Attempting to heal {issue.type} issue "
            f"(severity: {issue.severity})"
        )
        
        try:
            result = await handler(issue)
            
            # Record healing attempt
            record = HealingRecord(
                timestamp=datetime.now(),
                issue=issue,
                action=result.action,
                success=result.success,
                result=result
            )
            self.healing_history.append(record)
            
            if result.success:
                logger.info(
                    f"Successfully healed {issue.type}: {result.action}"
                )
            else:
                logger.warning(
                    f"Failed to heal {issue.type}: {result.reason}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Healing action failed: {e}")
            
            # Record failure
            record = HealingRecord(
                timestamp=datetime.now(),
                issue=issue,
                action="healing_failed",
                success=False
            )
            self.healing_history.append(record)
            
            return HealingResult(
                success=False,
                action="healing_exception",
                reason=str(e),
                issue_id=issue.issue_id
            )
    
    async def _heal_unresponsive_worker(
        self,
        issue: SystemIssue
    ) -> HealingResult:
        """Restart unresponsive worker"""
        if not self.worker_manager:
            return HealingResult(
                success=False,
                action="no_worker_manager",
                reason="Worker manager not available",
                issue_id=issue.issue_id
            )
        
        worker_id = issue.target
        
        # Try graceful restart first
        restarted = await self.worker_manager.restart_worker(
            worker_id,
            graceful=True
        )
        
        if not restarted:
            # Force restart
            restarted = await self.worker_manager.restart_worker(
                worker_id,
                graceful=False
            )
        
        return HealingResult(
            success=restarted,
            action=f"restarted_worker_{worker_id}",
            reason=None if restarted else "Failed to restart worker",
            issue_id=issue.issue_id
        )
    
    async def _heal_queue_backlog(
        self,
        issue: SystemIssue
    ) -> HealingResult:
        """Handle queue backlog"""
        if not self.worker_manager:
            return HealingResult(
                success=False,
                action="no_worker_manager",
                reason="Worker manager not available",
                issue_id=issue.issue_id
            )
        
        # Scale up workers
        current_workers = await self.worker_manager.get_worker_count()
        scaled = await self.worker_manager.scale_workers(
            current_workers + 2
        )
        
        return HealingResult(
            success=scaled,
            action=f"scaled_workers_to_{current_workers + 2}",
            reason=None if scaled else "Failed to scale workers",
            issue_id=issue.issue_id
        )
    
    async def _heal_stalled_queue(
        self,
        issue: SystemIssue
    ) -> HealingResult:
        """Handle stalled queue"""
        if not self.queue_manager:
            return HealingResult(
                success=False,
                action="no_queue_manager",
                reason="Queue manager not available",
                issue_id=issue.issue_id
            )
        
        # Restart queue processing
        restarted = await self.queue_manager.restart_processing()
        
        return HealingResult(
            success=restarted,
            action="restarted_queue_processing",
            reason=None if restarted else "Failed to restart queue",
            issue_id=issue.issue_id
        )
    
    async def _heal_resource_leak(
        self,
        issue: SystemIssue
    ) -> HealingResult:
        """Handle memory leak"""
        # Trigger garbage collection
        import gc
        gc.collect()
        
        # Clear caches if available
        if self.resource_monitor:
            await self.resource_monitor.clear_caches()
        
        return HealingResult(
            success=True,
            action="cleared_memory_and_caches",
            issue_id=issue.issue_id
        )
    
    async def _heal_high_cpu(
        self,
        issue: SystemIssue
    ) -> HealingResult:
        """Handle high CPU usage"""
        if not self.queue_manager:
            return HealingResult(
                success=False,
                action="no_queue_manager",
                reason="Queue manager not available",
                issue_id=issue.issue_id
            )
        
        # Throttle task processing
        throttled = await self.queue_manager.set_rate_limit(
            tasks_per_minute=30
        )
        
        return HealingResult(
            success=throttled,
            action="throttled_task_processing",
            reason=None if throttled else "Failed to throttle",
            issue_id=issue.issue_id
        )
    
    async def _heal_low_disk_space(
        self,
        issue: SystemIssue
    ) -> HealingResult:
        """Handle low disk space"""
        if not self.storage_manager:
            return HealingResult(
                success=False,
                action="no_storage_manager",
                reason="Storage manager not available",
                issue_id=issue.issue_id
            )
        
        # Clean up old files
        cleaned = await self.storage_manager.cleanup_old_files(
            days=7
        )
        
        return HealingResult(
            success=cleaned > 0,
            action=f"cleaned_{cleaned}_old_files",
            reason=None if cleaned > 0 else "No files to clean",
            issue_id=issue.issue_id
        )
    
    async def _heal_workspace_full(
        self,
        issue: SystemIssue
    ) -> HealingResult:
        """Handle full workspace"""
        if not self.storage_manager:
            return HealingResult(
                success=False,
                action="no_storage_manager",
                reason="Storage manager not available",
                issue_id=issue.issue_id
            )
        
        # Archive old projects
        archived = await self.storage_manager.archive_old_projects(
            days=30
        )
        
        return HealingResult(
            success=archived > 0,
            action=f"archived_{archived}_old_projects",
            reason=None if archived > 0 else "No projects to archive",
            issue_id=issue.issue_id
        )
    
    async def _heal_model_corruption(
        self,
        issue: SystemIssue
    ) -> HealingResult:
        """Handle model corruption"""
        # This would re-download or validate models
        # For now, just log the issue
        return HealingResult(
            success=False,
            action="model_validation_not_implemented",
            reason="Model healing not yet implemented",
            issue_id=issue.issue_id
        )
    
    def get_healing_stats(self) -> Dict[str, Any]:
        """Get self-healing statistics"""
        total_attempts = len(self.healing_history)
        successful = sum(1 for r in self.healing_history if r.success)
        
        # Group by issue type
        by_type = {}
        for record in self.healing_history:
            issue_type = record.issue.type
            if issue_type not in by_type:
                by_type[issue_type] = {'attempts': 0, 'successes': 0}
            by_type[issue_type]['attempts'] += 1
            if record.success:
                by_type[issue_type]['successes'] += 1
        
        return {
            'total_healing_attempts': total_attempts,
            'successful_healings': successful,
            'success_rate': successful / total_attempts if total_attempts > 0 else 0,
            'by_issue_type': by_type,
            'recent_healings': [
                {
                    'timestamp': r.timestamp.isoformat(),
                    'issue_type': r.issue.type,
                    'action': r.action,
                    'success': r.success
                }
                for r in self.healing_history[-10:]  # Last 10
            ]
        }