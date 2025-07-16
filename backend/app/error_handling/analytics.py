"""Error analytics and monitoring"""

import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from .models import (
    ErrorAnalysisReport, ErrorAnomaly, ErrorSeverity,
    ErrorClassification, ErrorCategory
)

logger = logging.getLogger(__name__)


class ErrorMetrics:
    """Container for error metrics"""
    
    def __init__(self, window_size: int = 1000):
        self.error_counts = defaultdict(int)
        self.error_trends = deque(maxlen=window_size)
        self.recovery_attempts = defaultdict(int)
        self.recovery_successes = defaultdict(int)
        self.last_errors: Dict[str, datetime] = {}
        self.error_durations: Dict[str, List[float]] = defaultdict(list)


class ErrorAnalytics:
    """Track and analyze error patterns"""
    
    def __init__(self, alert_service=None):
        self.metrics = ErrorMetrics()
        self.alert_service = alert_service
        self.alert_thresholds = {
            'error_rate': 0.1,  # 10% error rate
            'specific_error_count': 10,  # 10 occurrences of same error
            'recovery_failure_rate': 0.2,  # 20% recovery failure
            'error_spike': 2.0,  # 2x normal rate
            'critical_errors': 3  # 3 critical errors in window
        }
        self._baseline_error_rate = 0.05  # 5% baseline
        self._analysis_window_minutes = 5
    
    async def record_error(self, classification: ErrorClassification):
        """Record an error occurrence"""
        # Update counts
        self.metrics.error_counts[classification.category] += 1
        self.metrics.error_counts[classification.error_type] += 1
        
        # Add to trends
        self.metrics.error_trends.append(classification)
        
        # Update last seen
        self.metrics.last_errors[classification.error_type] = datetime.now()
        
        # Check for anomalies
        await self._check_anomalies(classification)
    
    async def record_recovery_attempt(
        self,
        error_category: str,
        success: bool
    ):
        """Record recovery attempt result"""
        self.metrics.recovery_attempts[error_category] += 1
        if success:
            self.metrics.recovery_successes[error_category] += 1
    
    async def analyze_error_patterns(
        self,
        window_minutes: Optional[int] = None
    ) -> ErrorAnalysisReport:
        """Analyze recent error patterns"""
        
        window_minutes = window_minutes or self._analysis_window_minutes
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        
        # Get recent errors
        recent_errors = [
            e for e in self.metrics.error_trends
            if e.timestamp > cutoff_time
        ]
        
        # Calculate metrics
        total_errors = len(recent_errors)
        total_requests = max(len(self.metrics.error_trends), 1)
        error_rate = total_errors / total_requests
        
        # Count by category
        error_frequency = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for error in recent_errors:
            error_frequency[error.category] += 1
            severity_counts[error.severity] += 1
        
        # Check for anomalies
        anomalies = await self._detect_anomalies(
            error_rate,
            error_frequency,
            severity_counts,
            recent_errors
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            anomalies,
            error_frequency,
            error_rate
        )
        
        return ErrorAnalysisReport(
            total_errors=total_errors,
            error_rate=error_rate,
            error_distribution=dict(error_frequency),
            anomalies=anomalies,
            recommendations=recommendations,
            analysis_window_minutes=window_minutes
        )
    
    async def _detect_anomalies(
        self,
        error_rate: float,
        error_frequency: Dict[str, int],
        severity_counts: Dict[str, int],
        recent_errors: List[ErrorClassification]
    ) -> List[ErrorAnomaly]:
        """Detect anomalies in error patterns"""
        anomalies = []
        
        # High error rate
        if error_rate > self.alert_thresholds['error_rate']:
            anomalies.append(ErrorAnomaly(
                type='high_error_rate',
                severity=ErrorSeverity.CRITICAL,
                value=error_rate,
                threshold=self.alert_thresholds['error_rate']
            ))
        
        # Frequent specific errors
        for error_type, count in error_frequency.items():
            if count > self.alert_thresholds['specific_error_count']:
                anomalies.append(ErrorAnomaly(
                    type='frequent_error',
                    severity=ErrorSeverity.HIGH,
                    error_type=error_type,
                    count=count
                ))
        
        # Error spike detection
        if self._is_error_spike(error_rate):
            anomalies.append(ErrorAnomaly(
                type='error_spike',
                severity=ErrorSeverity.HIGH,
                value=error_rate / self._baseline_error_rate,
                threshold=self.alert_thresholds['error_spike']
            ))
        
        # Critical error threshold
        critical_count = severity_counts.get(ErrorSeverity.CRITICAL, 0)
        if critical_count >= self.alert_thresholds['critical_errors']:
            anomalies.append(ErrorAnomaly(
                type='critical_error_threshold',
                severity=ErrorSeverity.CRITICAL,
                count=critical_count,
                threshold=self.alert_thresholds['critical_errors']
            ))
        
        # Recovery failure rate
        recovery_failure_rate = self._calculate_recovery_failure_rate()
        if recovery_failure_rate > self.alert_thresholds['recovery_failure_rate']:
            anomalies.append(ErrorAnomaly(
                type='high_recovery_failure',
                severity=ErrorSeverity.HIGH,
                value=recovery_failure_rate,
                threshold=self.alert_thresholds['recovery_failure_rate']
            ))
        
        # Send alerts for critical anomalies
        if anomalies and self.alert_service:
            await self._send_anomaly_alerts(anomalies)
        
        return anomalies
    
    def _is_error_spike(self, current_rate: float) -> bool:
        """Detect if current error rate is a spike"""
        spike_threshold = self._baseline_error_rate * self.alert_thresholds['error_spike']
        return current_rate > spike_threshold
    
    def _calculate_recovery_failure_rate(self) -> float:
        """Calculate overall recovery failure rate"""
        total_attempts = sum(self.metrics.recovery_attempts.values())
        total_successes = sum(self.metrics.recovery_successes.values())
        
        if total_attempts == 0:
            return 0.0
            
        failure_rate = 1 - (total_successes / total_attempts)
        return failure_rate
    
    def _generate_recommendations(
        self,
        anomalies: List[ErrorAnomaly],
        error_frequency: Dict[str, int],
        error_rate: float
    ) -> List[str]:
        """Generate recommendations based on error analysis"""
        recommendations = []
        
        for anomaly in anomalies:
            if anomaly.type == 'high_error_rate':
                recommendations.append(
                    "Consider scaling up workers or investigating system load. "
                    f"Current error rate: {anomaly.value:.2%}"
                )
            
            elif anomaly.type == 'frequent_error' and anomaly.error_type == ErrorCategory.RESOURCE:
                recommendations.append(
                    "Resource errors detected - check GPU/memory availability. "
                    "Consider implementing resource pooling or queuing."
                )
            
            elif anomaly.type == 'frequent_error' and anomaly.error_type == ErrorCategory.TRANSIENT:
                recommendations.append(
                    "High number of transient errors - check network stability "
                    "and external service health."
                )
            
            elif anomaly.type == 'error_spike':
                recommendations.append(
                    f"Error spike detected ({anomaly.value:.1f}x normal). "
                    "Investigate recent changes or external factors."
                )
            
            elif anomaly.type == 'critical_error_threshold':
                recommendations.append(
                    f"Multiple critical errors detected ({anomaly.count}). "
                    "Immediate investigation required."
                )
            
            elif anomaly.type == 'high_recovery_failure':
                recommendations.append(
                    f"Recovery mechanisms failing ({anomaly.value:.2%} failure rate). "
                    "Review recovery strategies and thresholds."
                )
        
        # Add general recommendations based on patterns
        if error_frequency.get(ErrorCategory.VALIDATION, 0) > 5:
            recommendations.append(
                "Multiple validation errors - review input validation "
                "and provide better user feedback."
            )
        
        if error_rate > 0.05 and not any(a.type == 'high_error_rate' for a in anomalies):
            recommendations.append(
                "Elevated error rate detected. Monitor closely for trends."
            )
        
        return recommendations
    
    async def _check_anomalies(self, classification: ErrorClassification):
        """Real-time anomaly checking for immediate alerts"""
        # Check for critical errors
        if classification.severity == ErrorSeverity.CRITICAL:
            recent_critical = sum(
                1 for e in list(self.metrics.error_trends)[-20:]
                if e.severity == ErrorSeverity.CRITICAL
            )
            
            if recent_critical >= self.alert_thresholds['critical_errors']:
                if self.alert_service:
                    await self.alert_service.send_alert(
                        level='critical',
                        message=f"Critical error threshold exceeded: {recent_critical} errors",
                        details={
                            'error_type': classification.error_type,
                            'category': classification.category,
                            'message': classification.message
                        }
                    )
    
    async def _send_anomaly_alerts(self, anomalies: List[ErrorAnomaly]):
        """Send alerts for detected anomalies"""
        critical_anomalies = [
            a for a in anomalies
            if a.severity == ErrorSeverity.CRITICAL
        ]
        
        if critical_anomalies and self.alert_service:
            await self.alert_service.send_alert(
                level='critical',
                message=f"Critical anomalies detected: {len(critical_anomalies)}",
                details={
                    'anomalies': [
                        {
                            'type': a.type,
                            'value': a.value,
                            'threshold': a.threshold,
                            'error_type': a.error_type
                        }
                        for a in critical_anomalies
                    ]
                }
            )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics"""
        total_errors = sum(self.metrics.error_counts.values())
        
        # Calculate category distribution
        category_dist = {}
        for category in ErrorCategory:
            count = self.metrics.error_counts.get(category, 0)
            category_dist[category] = {
                'count': count,
                'percentage': count / total_errors if total_errors > 0 else 0
            }
        
        # Calculate recovery stats
        recovery_stats = {}
        for category, attempts in self.metrics.recovery_attempts.items():
            successes = self.metrics.recovery_successes.get(category, 0)
            recovery_stats[category] = {
                'attempts': attempts,
                'successes': successes,
                'success_rate': successes / attempts if attempts > 0 else 0
            }
        
        return {
            'total_errors': total_errors,
            'category_distribution': category_dist,
            'recovery_stats': recovery_stats,
            'recent_error_rate': self._calculate_recent_error_rate(),
            'top_errors': self._get_top_errors(5)
        }
    
    def _calculate_recent_error_rate(self, minutes: int = 5) -> float:
        """Calculate error rate for recent time window"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_errors = sum(
            1 for e in self.metrics.error_trends
            if e.timestamp > cutoff_time
        )
        
        # Assume ~100 requests per minute as baseline
        expected_requests = minutes * 100
        return recent_errors / expected_requests
    
    def _get_top_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most frequent error types"""
        error_types = defaultdict(int)
        
        for error in self.metrics.error_trends:
            error_types[error.error_type] += 1
        
        sorted_errors = sorted(
            error_types.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {'error_type': error_type, 'count': count}
            for error_type, count in sorted_errors[:limit]
        ]