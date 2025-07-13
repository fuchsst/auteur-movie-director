# Story: Error Handling and Recovery

**Story ID**: STORY-049  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Feature  
**Points**: 7 (Large)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description
As a system administrator, I want comprehensive error handling and automatic recovery mechanisms for the function runner system, so that transient failures are automatically resolved, permanent failures are properly logged and reported, and the system maintains high availability even under adverse conditions.

## Acceptance Criteria

### Functional Requirements
- [ ] Automatic retry for transient failures with exponential backoff
- [ ] Dead letter queue for permanent failures
- [ ] Circuit breaker pattern for failing services
- [ ] Graceful degradation when resources unavailable
- [ ] Error categorization (transient, permanent, resource, validation)
- [ ] Automatic rollback for partial failures
- [ ] Error notification system with severity levels
- [ ] Self-healing mechanisms for common issues

### Technical Requirements
- [ ] Implement error classification system
- [ ] Create retry policies per error type
- [ ] Build circuit breaker for external services
- [ ] Implement compensation logic for rollbacks
- [ ] Add error tracking and analytics
- [ ] Create error recovery strategies
- [ ] Implement health check recovery
- [ ] Add chaos engineering support

### Quality Requirements
- [ ] Error detection within 5 seconds
- [ ] Automatic recovery success rate > 80%
- [ ] Zero data loss during failures
- [ ] Error classification accuracy > 95%
- [ ] Circuit breaker response time < 100ms
- [ ] Support for 50+ concurrent error scenarios
- [ ] Recovery action logging 100% complete

## Implementation Notes

### Error Classification System
```python
class ErrorClassifier:
    """Classify errors and determine recovery strategies"""
    
    # Error categories with recovery strategies
    ERROR_CATEGORIES = {
        'transient': {
            'patterns': [
                r'connection reset',
                r'timeout',
                r'temporary failure',
                r'resource temporarily unavailable'
            ],
            'strategy': 'retry_with_backoff',
            'max_retries': 3
        },
        'resource': {
            'patterns': [
                r'out of memory',
                r'no space left',
                r'gpu memory',
                r'resource exhausted'
            ],
            'strategy': 'queue_and_wait',
            'wait_time': 300
        },
        'validation': {
            'patterns': [
                r'invalid input',
                r'schema validation',
                r'type error',
                r'constraint violation'
            ],
            'strategy': 'fail_fast',
            'notify_user': True
        },
        'permanent': {
            'patterns': [
                r'model not found',
                r'permission denied',
                r'invalid configuration',
                r'unsupported operation'
            ],
            'strategy': 'dead_letter_queue',
            'alert_admin': True
        }
    }
    
    def classify_error(self, error: Exception) -> ErrorClassification:
        """Classify an error and determine recovery strategy"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Check against known patterns
        for category, config in self.ERROR_CATEGORIES.items():
            for pattern in config['patterns']:
                if re.search(pattern, error_str, re.IGNORECASE):
                    return ErrorClassification(
                        category=category,
                        strategy=config['strategy'],
                        error_type=error_type,
                        message=str(error),
                        recoverable=category in ['transient', 'resource'],
                        metadata=self._extract_metadata(error)
                    )
        
        # Default classification
        return ErrorClassification(
            category='unknown',
            strategy='retry_once',
            error_type=error_type,
            message=str(error),
            recoverable=False
        )
    
    def _extract_metadata(self, error: Exception) -> Dict[str, Any]:
        """Extract useful metadata from error"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        # Extract specific error attributes
        if hasattr(error, 'response'):
            metadata['response_code'] = getattr(error.response, 'status_code', None)
            metadata['response_body'] = getattr(error.response, 'text', None)
        
        return metadata
```

### Recovery Strategy Implementation
```python
class RecoveryManager:
    """Manage error recovery strategies"""
    
    def __init__(self):
        self.strategies = {
            'retry_with_backoff': RetryWithBackoffStrategy(),
            'queue_and_wait': QueueAndWaitStrategy(),
            'fail_fast': FailFastStrategy(),
            'dead_letter_queue': DeadLetterQueueStrategy(),
            'circuit_breaker': CircuitBreakerStrategy(),
            'compensation': CompensationStrategy()
        }
        self.recovery_history = RecoveryHistory()
    
    async def handle_error(self, 
                          context: ErrorContext,
                          error: Exception) -> RecoveryResult:
        """Handle an error with appropriate recovery strategy"""
        
        # Classify the error
        classification = ErrorClassifier().classify_error(error)
        
        # Log error
        await self._log_error(context, error, classification)
        
        # Check if we should attempt recovery
        if not self._should_attempt_recovery(context, classification):
            return RecoveryResult(
                success=False,
                action='abandoned',
                reason='Max recovery attempts exceeded'
            )
        
        # Get recovery strategy
        strategy = self.strategies.get(classification.strategy)
        if not strategy:
            strategy = self.strategies['fail_fast']
        
        # Execute recovery
        try:
            result = await strategy.recover(context, error, classification)
            
            # Record recovery attempt
            await self.recovery_history.record(
                context, classification, result
            )
            
            return result
            
        except Exception as recovery_error:
            logger.error(f"Recovery failed: {recovery_error}")
            return RecoveryResult(
                success=False,
                action='recovery_failed',
                error=recovery_error
            )
    
    def _should_attempt_recovery(self, 
                               context: ErrorContext,
                               classification: ErrorClassification) -> bool:
        """Determine if recovery should be attempted"""
        
        # Check if error is recoverable
        if not classification.recoverable:
            return False
        
        # Check recovery history
        recent_attempts = self.recovery_history.get_recent_attempts(
            context.task_id, 
            window_minutes=5
        )
        
        if len(recent_attempts) >= 5:
            logger.warning(f"Too many recovery attempts for task {context.task_id}")
            return False
        
        return True
```

### Retry Strategy
```python
class RetryWithBackoffStrategy(RecoveryStrategy):
    """Retry with exponential backoff"""
    
    def __init__(self):
        self.base_delay = 1.0  # seconds
        self.max_delay = 60.0
        self.jitter_factor = 0.1
    
    async def recover(self, 
                     context: ErrorContext,
                     error: Exception,
                     classification: ErrorClassification) -> RecoveryResult:
        """Attempt recovery through retry"""
        
        max_retries = classification.metadata.get('max_retries', 3)
        attempt = context.retry_count + 1
        
        if attempt > max_retries:
            return RecoveryResult(
                success=False,
                action='max_retries_exceeded'
            )
        
        # Calculate delay with exponential backoff
        delay = min(
            self.base_delay * (2 ** (attempt - 1)),
            self.max_delay
        )
        
        # Add jitter to prevent thundering herd
        jitter = delay * self.jitter_factor * (2 * random.random() - 1)
        delay += jitter
        
        logger.info(f"Retrying task {context.task_id} after {delay:.2f}s (attempt {attempt}/{max_retries})")
        
        # Schedule retry
        await asyncio.sleep(delay)
        
        # Re-submit task
        retry_task = context.original_task.copy()
        retry_task['retry_count'] = attempt
        retry_task['previous_error'] = str(error)
        
        await task_queue.submit(retry_task)
        
        return RecoveryResult(
            success=True,
            action='retry_scheduled',
            metadata={
                'attempt': attempt,
                'delay': delay,
                'next_attempt_at': datetime.now() + timedelta(seconds=delay)
            }
        )
```

### Circuit Breaker Pattern
```python
class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self._state = 'closed'  # closed, open, half_open
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> str:
        return self._state
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        async with self._lock:
            if self._state == 'open':
                if self._should_attempt_reset():
                    self._state = 'half_open'
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is open. Next attempt at {self._next_attempt_time()}"
                    )
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
            
        except self.expected_exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.failure_count = 0
            self._state = 'closed'
    
    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self._state = 'open'
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )

class CircuitBreakerManager:
    """Manage circuit breakers for different services"""
    
    def __init__(self):
        self.breakers = {
            'comfyui': CircuitBreaker(failure_threshold=3, recovery_timeout=30),
            'storage': CircuitBreaker(failure_threshold=5, recovery_timeout=60),
            'gpu_allocation': CircuitBreaker(failure_threshold=2, recovery_timeout=120)
        }
    
    def get_breaker(self, service: str) -> CircuitBreaker:
        """Get circuit breaker for service"""
        return self.breakers.get(service, self.breakers['default'])
```

### Compensation and Rollback
```python
class CompensationManager:
    """Handle compensation logic for failed operations"""
    
    def __init__(self):
        self.compensation_handlers = {
            'file_upload': self._compensate_file_upload,
            'resource_allocation': self._compensate_resource_allocation,
            'task_submission': self._compensate_task_submission
        }
    
    async def compensate(self, operation: Operation, error: Exception):
        """Execute compensation logic for failed operation"""
        
        handler = self.compensation_handlers.get(operation.type)
        if not handler:
            logger.warning(f"No compensation handler for operation type: {operation.type}")
            return
        
        try:
            await handler(operation, error)
            logger.info(f"Successfully compensated for failed {operation.type}")
        except Exception as comp_error:
            logger.error(f"Compensation failed: {comp_error}")
            # Record compensation failure for manual intervention
            await self._record_compensation_failure(operation, error, comp_error)
    
    async def _compensate_file_upload(self, operation: Operation, error: Exception):
        """Clean up partially uploaded files"""
        file_path = operation.data.get('file_path')
        if file_path and await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
            logger.info(f"Cleaned up partial upload: {file_path}")
    
    async def _compensate_resource_allocation(self, operation: Operation, error: Exception):
        """Release allocated resources"""
        allocation_id = operation.data.get('allocation_id')
        if allocation_id:
            await resource_manager.release_allocation(allocation_id)
            logger.info(f"Released resource allocation: {allocation_id}")
```

### Error Analytics and Monitoring
```python
class ErrorAnalytics:
    """Track and analyze error patterns"""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.error_trends = deque(maxlen=1000)
        self.alert_thresholds = {
            'error_rate': 0.1,  # 10% error rate
            'specific_error_count': 10,  # 10 occurrences of same error
            'recovery_failure_rate': 0.2  # 20% recovery failure
        }
    
    async def analyze_error_patterns(self) -> ErrorAnalysisReport:
        """Analyze recent error patterns"""
        
        # Calculate error rates
        recent_errors = [e for e in self.error_trends 
                        if e.timestamp > datetime.now() - timedelta(minutes=5)]
        
        error_rate = len(recent_errors) / max(len(self.error_trends), 1)
        
        # Find most common errors
        error_frequency = defaultdict(int)
        for error in recent_errors:
            error_frequency[error.category] += 1
        
        # Check for anomalies
        anomalies = []
        
        if error_rate > self.alert_thresholds['error_rate']:
            anomalies.append(ErrorAnomaly(
                type='high_error_rate',
                severity='critical',
                value=error_rate,
                threshold=self.alert_thresholds['error_rate']
            ))
        
        for error_type, count in error_frequency.items():
            if count > self.alert_thresholds['specific_error_count']:
                anomalies.append(ErrorAnomaly(
                    type='frequent_error',
                    severity='warning',
                    error_type=error_type,
                    count=count
                ))
        
        return ErrorAnalysisReport(
            total_errors=len(recent_errors),
            error_rate=error_rate,
            error_distribution=dict(error_frequency),
            anomalies=anomalies,
            recommendations=self._generate_recommendations(anomalies)
        )
    
    def _generate_recommendations(self, anomalies: List[ErrorAnomaly]) -> List[str]:
        """Generate recommendations based on error analysis"""
        recommendations = []
        
        for anomaly in anomalies:
            if anomaly.type == 'high_error_rate':
                recommendations.append(
                    "Consider scaling up workers or investigating system load"
                )
            elif anomaly.type == 'frequent_error' and anomaly.error_type == 'resource':
                recommendations.append(
                    "Resource errors detected - check GPU/memory availability"
                )
        
        return recommendations
```

### Self-Healing Mechanisms
```python
class SelfHealingSystem:
    """Automatic remediation for common issues"""
    
    def __init__(self):
        self.healing_actions = {
            'worker_unresponsive': self._heal_unresponsive_worker,
            'queue_backlog': self._heal_queue_backlog,
            'resource_leak': self._heal_resource_leak,
            'model_corruption': self._heal_model_corruption
        }
        self.healing_history = []
    
    async def diagnose_and_heal(self):
        """Continuous diagnosis and healing loop"""
        while True:
            try:
                # Run diagnostics
                issues = await self._run_diagnostics()
                
                # Attempt healing for each issue
                for issue in issues:
                    await self._attempt_healing(issue)
                
                await asyncio.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error(f"Self-healing error: {e}")
                await asyncio.sleep(300)  # Back off on error
    
    async def _run_diagnostics(self) -> List[SystemIssue]:
        """Diagnose system health issues"""
        issues = []
        
        # Check worker health
        unhealthy_workers = await worker_manager.get_unhealthy_workers()
        for worker in unhealthy_workers:
            issues.append(SystemIssue(
                type='worker_unresponsive',
                severity='high',
                target=worker.id,
                details={'last_heartbeat': worker.last_heartbeat}
            ))
        
        # Check queue depth
        queue_stats = await queue_manager.get_stats()
        if queue_stats.depth > queue_stats.processing_rate * 300:  # 5 min backlog
            issues.append(SystemIssue(
                type='queue_backlog',
                severity='medium',
                details={'depth': queue_stats.depth, 'rate': queue_stats.processing_rate}
            ))
        
        # Check resource usage
        resource_stats = await resource_monitor.get_stats()
        if resource_stats.memory_usage > 0.9:  # 90% memory
            issues.append(SystemIssue(
                type='resource_leak',
                severity='high',
                details={'memory_usage': resource_stats.memory_usage}
            ))
        
        return issues
    
    async def _attempt_healing(self, issue: SystemIssue):
        """Attempt to heal a system issue"""
        
        handler = self.healing_actions.get(issue.type)
        if not handler:
            logger.warning(f"No healing action for issue type: {issue.type}")
            return
        
        logger.info(f"Attempting to heal {issue.type} issue")
        
        try:
            result = await handler(issue)
            
            self.healing_history.append(HealingRecord(
                timestamp=datetime.now(),
                issue=issue,
                action=result.action,
                success=result.success
            ))
            
            if result.success:
                logger.info(f"Successfully healed {issue.type}: {result.action}")
            else:
                logger.warning(f"Failed to heal {issue.type}: {result.reason}")
                
        except Exception as e:
            logger.error(f"Healing action failed: {e}")
    
    async def _heal_unresponsive_worker(self, issue: SystemIssue) -> HealingResult:
        """Restart unresponsive worker"""
        worker_id = issue.target
        
        # Try graceful restart first
        restarted = await worker_manager.restart_worker(worker_id, graceful=True)
        
        if not restarted:
            # Force restart
            restarted = await worker_manager.restart_worker(worker_id, graceful=False)
        
        return HealingResult(
            success=restarted,
            action=f"Restarted worker {worker_id}",
            reason=None if restarted else "Failed to restart worker"
        )
```

## Dependencies
- **STORY-041**: Worker Pool Management - for worker recovery
- **STORY-042**: Task Queue Configuration - for retry queuing
- **STORY-043**: Worker Health Monitoring - for health-based recovery
- **STORY-048**: Progress Tracking System - for error reporting

## Testing Criteria
- [ ] Unit tests for error classification
- [ ] Integration tests for recovery strategies
- [ ] Circuit breaker behavior tests
- [ ] Compensation logic tests
- [ ] Chaos engineering tests
- [ ] Recovery success rate measurement
- [ ] Error analytics accuracy tests
- [ ] Self-healing effectiveness tests

## Definition of Done
- [ ] Error classification system implemented
- [ ] All recovery strategies working
- [ ] Circuit breakers protecting services
- [ ] Compensation logic for all operations
- [ ] Error analytics dashboard
- [ ] Self-healing mechanisms active
- [ ] Alert system integrated
- [ ] Chaos testing framework
- [ ] Documentation includes troubleshooting guide
- [ ] Code review passed with test coverage > 85%

## Story Links
- **Depends On**: STORY-041, STORY-042, STORY-043
- **Blocks**: STORY-051 (Integration & Testing)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/reliability/error_handling.md