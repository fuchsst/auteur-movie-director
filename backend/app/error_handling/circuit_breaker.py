"""Circuit breaker implementation for fault tolerance"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Any, Type, Optional, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
        success_threshold: int = 2
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self._state = CircuitBreakerState.CLOSED
        self._lock = asyncio.Lock()
        
        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.circuit_opens = 0
    
    @property
    def state(self) -> CircuitBreakerState:
        """Get current state"""
        return self._state
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        async with self._lock:
            self.total_calls += 1
            
            if self._state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' entering half-open state")
                else:
                    next_attempt = self._next_attempt_time()
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open. "
                        f"Next attempt at {next_attempt}"
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
            self.total_successes += 1
            self.last_success_time = datetime.now()
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' closed after recovery")
            else:
                self.failure_count = 0
    
    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.total_failures += 1
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                # Failure in half-open state reopens the circuit
                self._state = CircuitBreakerState.OPEN
                self.circuit_opens += 1
                logger.warning(
                    f"Circuit breaker '{self.name}' reopened after failure in half-open state"
                )
            elif self.failure_count >= self.failure_threshold:
                self._state = CircuitBreakerState.OPEN
                self.circuit_opens += 1
                logger.warning(
                    f"Circuit breaker '{self.name}' opened after {self.failure_count} failures"
                )
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
            
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure > timedelta(seconds=self.recovery_timeout)
    
    def _next_attempt_time(self) -> datetime:
        """Calculate next attempt time"""
        if not self.last_failure_time:
            return datetime.now()
            
        return self.last_failure_time + timedelta(seconds=self.recovery_timeout)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self._state,
            'failure_count': self.failure_count,
            'total_calls': self.total_calls,
            'total_failures': self.total_failures,
            'total_successes': self.total_successes,
            'circuit_opens': self.circuit_opens,
            'success_rate': self.total_successes / self.total_calls if self.total_calls > 0 else 0,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None
        }
    
    async def reset(self):
        """Manually reset circuit breaker"""
        async with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerManager:
    """Manage circuit breakers for different services"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {
            'default': CircuitBreaker(
                name='default',
                failure_threshold=5,
                recovery_timeout=60
            ),
            'comfyui': CircuitBreaker(
                name='comfyui',
                failure_threshold=3,
                recovery_timeout=30,
                success_threshold=2
            ),
            'storage': CircuitBreaker(
                name='storage',
                failure_threshold=5,
                recovery_timeout=60,
                success_threshold=3
            ),
            'gpu_allocation': CircuitBreaker(
                name='gpu_allocation',
                failure_threshold=2,
                recovery_timeout=120,
                success_threshold=1
            ),
            'external_api': CircuitBreaker(
                name='external_api',
                failure_threshold=4,
                recovery_timeout=45,
                success_threshold=2
            )
        }
    
    def get_breaker(self, service: str) -> CircuitBreaker:
        """Get circuit breaker for service"""
        return self.breakers.get(service, self.breakers['default'])
    
    def add_breaker(
        self,
        service: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
        success_threshold: int = 2
    ) -> CircuitBreaker:
        """Add a new circuit breaker"""
        breaker = CircuitBreaker(
            name=service,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            success_threshold=success_threshold
        )
        self.breakers[service] = breaker
        return breaker
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {
            name: breaker.get_stats()
            for name, breaker in self.breakers.items()
        }
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            await breaker.reset()
    
    def get_open_breakers(self) -> List[str]:
        """Get list of open circuit breakers"""
        return [
            name for name, breaker in self.breakers.items()
            if breaker.state == CircuitBreakerState.OPEN
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        total_breakers = len(self.breakers)
        open_breakers = self.get_open_breakers()
        
        return {
            'healthy': len(open_breakers) == 0,
            'total_breakers': total_breakers,
            'open_breakers': open_breakers,
            'health_percentage': (total_breakers - len(open_breakers)) / total_breakers * 100
        }