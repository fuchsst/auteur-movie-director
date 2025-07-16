"""Tests for error handling and recovery system"""

import pytest
import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.error_handling import (
    ErrorClassifier, ErrorClassification, ErrorCategory,
    RecoveryManager, RecoveryResult,
    CircuitBreaker, CircuitBreakerManager, CircuitBreakerOpenError,
    CompensationManager, Operation,
    ErrorAnalytics, ErrorAnalysisReport,
    SelfHealingSystem, SystemIssue,
    ErrorHandlingIntegration
)
from app.error_handling.models import ErrorSeverity, HealingResult, RecoveryStrategy


class TestErrorClassifier:
    """Test error classification"""
    
    def test_transient_error_classification(self):
        """Test classification of transient errors"""
        classifier = ErrorClassifier()
        
        # Connection error
        error = ConnectionError("Connection reset by peer")
        classification = classifier.classify_error(error)
        
        assert classification.category == ErrorCategory.TRANSIENT
        assert classification.strategy == RecoveryStrategy.RETRY_WITH_BACKOFF
        assert classification.recoverable is True
        assert classification.severity == ErrorSeverity.LOW
    
    def test_resource_error_classification(self):
        """Test classification of resource errors"""
        classifier = ErrorClassifier()
        
        # Memory error
        error = MemoryError("Out of memory")
        classification = classifier.classify_error(error)
        
        assert classification.category == ErrorCategory.RESOURCE
        assert classification.strategy == RecoveryStrategy.QUEUE_AND_WAIT
        assert classification.recoverable is True
        assert classification.severity == ErrorSeverity.HIGH
    
    def test_validation_error_classification(self):
        """Test classification of validation errors"""
        classifier = ErrorClassifier()
        
        # Validation error
        error = ValueError("Invalid input: schema validation failed")
        classification = classifier.classify_error(error)
        
        assert classification.category == ErrorCategory.VALIDATION
        assert classification.strategy == RecoveryStrategy.FAIL_FAST
        assert classification.recoverable is False
        assert classification.severity == ErrorSeverity.MEDIUM
    
    def test_permanent_error_classification(self):
        """Test classification of permanent errors"""
        classifier = ErrorClassifier()
        
        # Permission error
        error = PermissionError("Permission denied")
        classification = classifier.classify_error(error)
        
        assert classification.category == ErrorCategory.PERMANENT
        assert classification.strategy == RecoveryStrategy.DEAD_LETTER_QUEUE
        assert classification.recoverable is False
        assert classification.severity == ErrorSeverity.CRITICAL
    
    def test_unknown_error_classification(self):
        """Test classification of unknown errors"""
        classifier = ErrorClassifier()
        
        # Unknown error
        error = Exception("Some random error")
        classification = classifier.classify_error(error)
        
        assert classification.category == ErrorCategory.UNKNOWN
        assert classification.strategy == RecoveryStrategy.RETRY_ONCE
        assert classification.recoverable is False


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=60
        )
        
        # Successful calls should work
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == "closed"
    
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=60
        )
        
        # Failing function
        async def fail_func():
            raise Exception("Test failure")
        
        # Make failures up to threshold
        for i in range(3):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        # Circuit should be open
        assert breaker.state == "open"
        
        # Next call should fail immediately
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(fail_func)
    
    async def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker half-open state"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=1,  # 1 second
            success_threshold=2
        )
        
        # Open the circuit
        async def fail_func():
            raise Exception("Test failure")
        
        for i in range(2):
            with pytest.raises(Exception):
                await breaker.call(fail_func)
        
        assert breaker.state == "open"
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Success should move to half-open
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success"
        
        # Need one more success to close
        result = await breaker.call(success_func)
        assert breaker.state == "closed"


class TestRecoveryManager:
    """Test recovery management"""
    
    @pytest.fixture
    def mock_task_queue(self):
        """Mock task queue"""
        queue = AsyncMock()
        queue.submit = AsyncMock()
        return queue
    
    async def test_retry_with_backoff_strategy(self, mock_task_queue):
        """Test retry with backoff recovery"""
        from app.error_handling.recovery import RetryWithBackoffStrategy
        from app.error_handling.models import ErrorContext
        
        strategy = RetryWithBackoffStrategy(mock_task_queue)
        
        context = ErrorContext(
            task_id="test-123",
            template_id="test-template",
            operation_type="test",
            retry_count=0,
            original_task={"task": "data"},
            start_time=datetime.now()
        )
        
        error = Exception("Transient error")
        classification = ErrorClassification(
            category=ErrorCategory.TRANSIENT,
            strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            error_type="Exception",
            message=str(error),
            recoverable=True,
            metadata={"max_retries": 3}
        )
        
        result = await strategy.recover(context, error, classification)
        
        assert result.success is True
        assert result.action == "retry_scheduled"
        assert result.metadata["attempt"] == 1
        assert result.metadata["delay"] > 0
    
    async def test_max_retries_exceeded(self, mock_task_queue):
        """Test max retries exceeded"""
        from app.error_handling.recovery import RetryWithBackoffStrategy
        from app.error_handling.models import ErrorContext
        
        strategy = RetryWithBackoffStrategy(mock_task_queue)
        
        context = ErrorContext(
            task_id="test-456",
            template_id="test-template",
            operation_type="test",
            retry_count=3,  # Already at max
            original_task={"task": "data"},
            start_time=datetime.now()
        )
        
        error = Exception("Persistent error")
        classification = ErrorClassification(
            category=ErrorCategory.TRANSIENT,
            strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
            error_type="Exception",
            message=str(error),
            recoverable=True,
            metadata={"max_retries": 3}
        )
        
        result = await strategy.recover(context, error, classification)
        
        assert result.success is False
        assert result.action == "max_retries_exceeded"


class TestCompensationManager:
    """Test compensation mechanisms"""
    
    async def test_file_upload_compensation(self, tmp_path):
        """Test file upload compensation"""
        manager = CompensationManager()
        
        # Create a temporary file
        test_file = tmp_path / "test_upload.txt"
        test_file.write_text("test content")
        
        operation = Operation(
            operation_id="op-123",
            operation_type="file_upload",
            data={"file_path": str(test_file)}
        )
        
        error = Exception("Upload failed")
        result = await manager.compensate(operation, error)
        
        assert result.success is True
        assert "removed_file" in result.action_taken
        assert not test_file.exists()
    
    async def test_compensation_failure_recording(self):
        """Test recording of compensation failures"""
        manager = CompensationManager()
        
        # Operation that will fail compensation
        operation = Operation(
            operation_id="op-456",
            operation_type="unknown_type",
            data={}
        )
        
        error = Exception("Original error")
        result = await manager.compensate(operation, error)
        
        assert result.success is False
        assert result.action_taken == "no_handler"


class TestErrorAnalytics:
    """Test error analytics"""
    
    async def test_error_recording(self):
        """Test error recording and analysis"""
        analytics = ErrorAnalytics()
        
        # Record some errors
        for i in range(5):
            classification = ErrorClassification(
                category=ErrorCategory.TRANSIENT,
                strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                error_type="ConnectionError",
                message="Connection failed",
                recoverable=True
            )
            await analytics.record_error(classification)
        
        # Get analysis
        report = await analytics.analyze_error_patterns(window_minutes=5)
        
        assert report.total_errors == 5
        assert ErrorCategory.TRANSIENT in report.error_distribution
        assert report.error_distribution[ErrorCategory.TRANSIENT] == 5
    
    async def test_anomaly_detection(self):
        """Test anomaly detection"""
        analytics = ErrorAnalytics()
        analytics.alert_thresholds['specific_error_count'] = 3
        
        # Record many errors of same type
        for i in range(5):
            classification = ErrorClassification(
                category=ErrorCategory.RESOURCE,
                strategy=RecoveryStrategy.QUEUE_AND_WAIT,
                error_type="MemoryError",
                message="Out of memory",
                recoverable=True,
                severity=ErrorSeverity.HIGH
            )
            await analytics.record_error(classification)
        
        # Analyze
        report = await analytics.analyze_error_patterns()
        
        # Should detect anomaly
        assert len(report.anomalies) > 0
        anomaly = report.anomalies[0]
        assert anomaly.type == "frequent_error"
        assert anomaly.error_type == ErrorCategory.RESOURCE


class TestSelfHealing:
    """Test self-healing system"""
    
    @pytest.fixture
    def mock_worker_manager(self):
        """Mock worker manager"""
        manager = AsyncMock()
        manager.get_unhealthy_workers = AsyncMock(return_value=[])
        manager.restart_worker = AsyncMock(return_value=True)
        manager.get_worker_count = AsyncMock(return_value=4)
        manager.scale_workers = AsyncMock(return_value=True)
        return manager
    
    async def test_worker_healing(self, mock_worker_manager):
        """Test worker healing"""
        healing = SelfHealingSystem(worker_manager=mock_worker_manager)
        
        # Create worker issue
        issue = SystemIssue(
            type="worker_unresponsive",
            severity=ErrorSeverity.HIGH,
            target="worker-123"
        )
        
        result = await healing._heal_unresponsive_worker(issue)
        
        assert result.success is True
        assert "restarted_worker" in result.action
        mock_worker_manager.restart_worker.assert_called()
    
    async def test_healing_stats(self, mock_worker_manager):
        """Test healing statistics"""
        healing = SelfHealingSystem(worker_manager=mock_worker_manager)
        
        # Perform some healing
        issue = SystemIssue(
            type="worker_unresponsive",
            severity=ErrorSeverity.HIGH,
            target="worker-456"
        )
        
        await healing._attempt_healing(issue)
        
        # Get stats
        stats = healing.get_healing_stats()
        
        assert stats['total_healing_attempts'] == 1
        assert stats['successful_healings'] == 1
        assert stats['success_rate'] == 1.0


class TestErrorHandlingIntegration:
    """Test integrated error handling"""
    
    @pytest.fixture
    def error_handler(self):
        """Create error handler"""
        return ErrorHandlingIntegration()
    
    async def test_task_execution_wrapper(self, error_handler):
        """Test task execution wrapper"""
        # Successful execution
        async def success_task(data):
            return {"result": "success"}
        
        result = await error_handler.wrap_task_execution(
            task_id="test-123",
            template_id="test-template",
            operation_type="test",
            task_data={"input": "data"},
            execute_func=success_task
        )
        
        assert result["result"] == "success"
    
    async def test_task_execution_with_error(self, error_handler):
        """Test task execution with error handling"""
        # Failing execution
        async def fail_task(data):
            raise ConnectionError("Network error")
        
        with pytest.raises(ConnectionError):
            await error_handler.wrap_task_execution(
                task_id="test-456",
                template_id="test-template",
                operation_type="test",
                task_data={"input": "data"},
                execute_func=fail_task
            )
        
        # Should have recorded error
        history = error_handler.context_manager.get_history("test-456")
        assert history is not None
        assert len(history.errors) == 1
    
    async def test_error_analysis_integration(self, error_handler):
        """Test comprehensive error analysis"""
        # Generate some errors
        for i in range(3):
            try:
                async def fail_task(data):
                    raise ValueError("Test error")
                
                await error_handler.wrap_task_execution(
                    task_id=f"test-{i}",
                    template_id="test-template",
                    operation_type="test",
                    task_data={},
                    execute_func=fail_task
                )
            except ValueError:
                pass
        
        # Get analysis
        analysis = await error_handler.get_error_analysis()
        
        assert 'error_analysis' in analysis
        assert 'circuit_breakers' in analysis
        assert 'recovery' in analysis
        assert 'compensation' in analysis
        assert 'self_healing' in analysis