"""Error classification system"""

import re
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime

from .models import ErrorClassification, ErrorCategory, RecoveryStrategy, ErrorSeverity


class ErrorClassifier:
    """Classify errors and determine recovery strategies"""
    
    # Error categories with recovery strategies
    ERROR_CATEGORIES = {
        ErrorCategory.TRANSIENT: {
            'patterns': [
                r'connection reset',
                r'timeout',
                r'temporary failure',
                r'resource temporarily unavailable',
                r'connection refused',
                r'network unreachable',
                r'broken pipe',
                r'connection aborted'
            ],
            'strategy': RecoveryStrategy.RETRY_WITH_BACKOFF,
            'max_retries': 3,
            'severity': ErrorSeverity.LOW
        },
        ErrorCategory.RESOURCE: {
            'patterns': [
                r'out of memory',
                r'no space left',
                r'gpu memory',
                r'resource exhausted',
                r'cannot allocate memory',
                r'insufficient resources',
                r'quota exceeded',
                r'too many open files'
            ],
            'strategy': RecoveryStrategy.QUEUE_AND_WAIT,
            'wait_time': 300,
            'severity': ErrorSeverity.HIGH
        },
        ErrorCategory.VALIDATION: {
            'patterns': [
                r'invalid input',
                r'schema validation',
                r'type error',
                r'constraint violation',
                r'invalid parameter',
                r'validation failed',
                r'format error',
                r'missing required'
            ],
            'strategy': RecoveryStrategy.FAIL_FAST,
            'notify_user': True,
            'severity': ErrorSeverity.MEDIUM
        },
        ErrorCategory.PERMANENT: {
            'patterns': [
                r'model not found',
                r'permission denied',
                r'invalid configuration',
                r'unsupported operation',
                r'authentication failed',
                r'access denied',
                r'not implemented',
                r'feature disabled'
            ],
            'strategy': RecoveryStrategy.DEAD_LETTER_QUEUE,
            'alert_admin': True,
            'severity': ErrorSeverity.CRITICAL
        }
    }
    
    # Exception type mapping
    EXCEPTION_TYPE_MAPPING = {
        'ConnectionError': ErrorCategory.TRANSIENT,
        'TimeoutError': ErrorCategory.TRANSIENT,
        'MemoryError': ErrorCategory.RESOURCE,
        'ValueError': ErrorCategory.VALIDATION,
        'TypeError': ErrorCategory.VALIDATION,
        'PermissionError': ErrorCategory.PERMANENT,
        'NotImplementedError': ErrorCategory.PERMANENT
    }
    
    def classify_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorClassification:
        """Classify an error and determine recovery strategy"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # First check exception type mapping
        if error_type in self.EXCEPTION_TYPE_MAPPING:
            category = self.EXCEPTION_TYPE_MAPPING[error_type]
            config = self.ERROR_CATEGORIES[category]
            return self._create_classification(
                category, config, error_type, str(error), context
            )
        
        # Check against known patterns
        for category, config in self.ERROR_CATEGORIES.items():
            for pattern in config['patterns']:
                if re.search(pattern, error_str, re.IGNORECASE):
                    return self._create_classification(
                        category, config, error_type, str(error), context
                    )
        
        # Default classification for unknown errors
        return ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            strategy=RecoveryStrategy.RETRY_ONCE,
            error_type=error_type,
            message=str(error),
            recoverable=False,
            severity=ErrorSeverity.MEDIUM,
            metadata=self._extract_metadata(error, context)
        )
    
    def _create_classification(
        self,
        category: ErrorCategory,
        config: Dict[str, Any],
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorClassification:
        """Create error classification from category config"""
        return ErrorClassification(
            category=category,
            strategy=config['strategy'],
            error_type=error_type,
            message=message,
            recoverable=category in [ErrorCategory.TRANSIENT, ErrorCategory.RESOURCE],
            severity=config.get('severity', ErrorSeverity.MEDIUM),
            metadata=self._extract_metadata_with_config(config, context)
        )
    
    def _extract_metadata(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract useful metadata from error"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        # Add context if provided
        if context:
            metadata['context'] = context
        
        # Extract specific error attributes
        if hasattr(error, 'response'):
            metadata['response_code'] = getattr(error.response, 'status_code', None)
            metadata['response_body'] = getattr(error.response, 'text', None)
        
        if hasattr(error, 'errno'):
            metadata['errno'] = error.errno
            
        if hasattr(error, 'strerror'):
            metadata['strerror'] = error.strerror
            
        return metadata
    
    def _extract_metadata_with_config(
        self, 
        config: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract metadata with category config"""
        metadata = {
            'timestamp': datetime.now().isoformat()
        }
        
        # Add config-specific metadata
        if 'max_retries' in config:
            metadata['max_retries'] = config['max_retries']
        
        if 'wait_time' in config:
            metadata['wait_time'] = config['wait_time']
            
        if 'notify_user' in config:
            metadata['notify_user'] = config['notify_user']
            
        if 'alert_admin' in config:
            metadata['alert_admin'] = config['alert_admin']
        
        # Add context if provided
        if context:
            metadata['context'] = context
            
        return metadata
    
    def batch_classify(self, errors: List[Exception]) -> List[ErrorClassification]:
        """Classify multiple errors"""
        return [self.classify_error(error) for error in errors]
    
    def get_error_pattern_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics about error patterns"""
        stats = {}
        
        for category, config in self.ERROR_CATEGORIES.items():
            stats[category] = {
                'pattern_count': len(config['patterns']),
                'strategy': config['strategy'],
                'severity': config.get('severity', ErrorSeverity.MEDIUM)
            }
            
        return stats