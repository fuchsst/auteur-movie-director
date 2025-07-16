"""Error handling data models"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    """Error categories"""
    TRANSIENT = "transient"
    RESOURCE = "resource"
    VALIDATION = "validation"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    """Recovery strategies"""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    QUEUE_AND_WAIT = "queue_and_wait"
    FAIL_FAST = "fail_fast"
    DEAD_LETTER_QUEUE = "dead_letter_queue"
    CIRCUIT_BREAKER = "circuit_breaker"
    COMPENSATION = "compensation"
    RETRY_ONCE = "retry_once"


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorClassification(BaseModel):
    """Error classification result"""
    category: ErrorCategory
    strategy: RecoveryStrategy
    error_type: str
    message: str
    recoverable: bool
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class RecoveryResult(BaseModel):
    """Recovery attempt result"""
    success: bool
    action: str
    reason: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    

class ErrorContext(BaseModel):
    """Context for error handling"""
    task_id: str
    template_id: str
    operation_type: str
    retry_count: int = 0
    original_task: Dict[str, Any]
    start_time: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorHistory(BaseModel):
    """Error history for a task"""
    task_id: str
    errors: List[ErrorClassification] = Field(default_factory=list)
    recovery_attempts: List[RecoveryResult] = Field(default_factory=list)
    total_retries: int = 0
    last_error_time: Optional[datetime] = None
    

class SystemIssue(BaseModel):
    """System health issue"""
    issue_id: str = Field(default_factory=lambda: f"issue_{datetime.now().timestamp()}")
    type: str
    severity: ErrorSeverity
    target: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=datetime.now)
    

class HealingResult(BaseModel):
    """Self-healing action result"""
    success: bool
    action: str
    reason: Optional[str] = None
    issue_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    

class HealingRecord(BaseModel):
    """Record of healing action"""
    timestamp: datetime
    issue: SystemIssue
    action: str
    success: bool
    result: Optional[HealingResult] = None
    

class ErrorAnomaly(BaseModel):
    """Error pattern anomaly"""
    type: str
    severity: ErrorSeverity
    value: Optional[float] = None
    threshold: Optional[float] = None
    error_type: Optional[str] = None
    count: Optional[int] = None
    detected_at: datetime = Field(default_factory=datetime.now)
    

class ErrorAnalysisReport(BaseModel):
    """Error analysis report"""
    total_errors: int
    error_rate: float
    error_distribution: Dict[str, int]
    anomalies: List[ErrorAnomaly]
    recommendations: List[str]
    analysis_window_minutes: int = 5
    timestamp: datetime = Field(default_factory=datetime.now)


class CompensationResult(BaseModel):
    """Compensation action result"""
    success: bool
    operation_type: str
    action_taken: str
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)