"""
Resource management exceptions
"""


class ResourceAllocationError(Exception):
    """Base exception for resource allocation errors"""
    pass


class InsufficientResourcesError(ResourceAllocationError):
    """Raised when requested resources exceed available capacity"""
    pass


class ResourceConflictError(ResourceAllocationError):
    """Raised when resource allocation conflicts with existing allocations"""
    pass