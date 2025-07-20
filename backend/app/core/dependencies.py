from __future__ import annotations

"""
Application dependencies for dependency injection
"""

from typing import Optional
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.templates import TemplateRegistry
from app.resources import ResourceMapper, GPUResourceManager, ResourceMonitor
from app.config import settings
from app.services.websocket import WebSocketManager
from app.error_handling import ErrorHandlingIntegration
from redis import asyncio as aioredis


# Global instances
_template_registry: Optional[TemplateRegistry] = None
_resource_mapper: Optional[ResourceMapper] = None
_gpu_manager: Optional[GPUResourceManager] = None
_resource_monitor: Optional[ResourceMonitor] = None
_progress_tracker: Optional[None] = None  # Will be imported when needed
_ws_manager: Optional[WebSocketManager] = None
_redis_client: Optional[aioredis.Redis] = None
_error_handler: Optional[ErrorHandlingIntegration] = None


def get_template_registry() -> TemplateRegistry:
    """
    Get or create the global template registry instance.
    
    Returns:
        TemplateRegistry: The global template registry
    """
    global _template_registry
    
    if _template_registry is None:
        # Get template directories from settings
        template_dirs = [Path(d) for d in settings.TEMPLATE_DIRECTORIES]
        
        # Create registry
        _template_registry = TemplateRegistry(template_dirs)
        
        # Note: In production, this should be initialized during app startup
        # For now, we'll do lazy initialization
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if not loop.is_running():
            loop.run_until_complete(_template_registry.initialize())
    
    return _template_registry


def get_resource_mapper() -> ResourceMapper:
    """
    Get or create the global resource mapper instance.
    
    Returns:
        ResourceMapper: The global resource mapper
    """
    global _resource_mapper
    
    if _resource_mapper is None:
        _resource_mapper = ResourceMapper()
        
        # Initialize in background
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop.run_until_complete(_resource_mapper.start())
        except RuntimeError:
            pass
    
    return _resource_mapper


def get_gpu_manager() -> GPUResourceManager:
    """
    Get or create the global GPU manager instance.
    
    Returns:
        GPUResourceManager: The global GPU manager
    """
    global _gpu_manager
    
    if _gpu_manager is None:
        _gpu_manager = GPUResourceManager()
        
        # Initialize in background
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop.run_until_complete(_gpu_manager.start())
        except RuntimeError:
            pass
    
    return _gpu_manager


def get_resource_monitor() -> ResourceMonitor:
    """
    Get or create the global resource monitor instance.
    
    Returns:
        ResourceMonitor: The global resource monitor
    """
    global _resource_monitor
    
    if _resource_monitor is None:
        resource_mapper = get_resource_mapper()
        _resource_monitor = ResourceMonitor(resource_mapper)
        
        # Initialize in background
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                loop.run_until_complete(_resource_monitor.start())
        except RuntimeError:
            pass
    
    return _resource_monitor


async def get_redis_client() -> aioredis.Redis:
    """
    Get or create Redis client instance.
    
    Returns:
        aioredis.Redis: Redis client
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    return _redis_client


def get_ws_manager() -> WebSocketManager:
    """
    Get or create WebSocket manager instance.
    
    Returns:
        WebSocketManager: WebSocket manager
    """
    global _ws_manager
    
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    
    return _ws_manager


async def get_progress_tracker() -> ProgressTracker:
    """
    Get or create progress tracker instance.
    
    Returns:
        ProgressTracker: Progress tracker
    """
    global _progress_tracker
    
    if _progress_tracker is None:
        redis_client = await get_redis_client()
        ws_manager = get_ws_manager()
        _progress_tracker = ProgressTracker(
            redis_client, 
            ws_manager,
            preview_dir=str(settings.PREVIEW_DIR)
        )
    
    return _progress_tracker


async def get_error_handler() -> ErrorHandlingIntegration:
    """
    Get or create error handling integration instance.
    
    Returns:
        ErrorHandlingIntegration: Error handler
    """
    global _error_handler
    
    if _error_handler is None:
        # Get dependencies
        redis_client = await get_redis_client()
        ws_manager = get_ws_manager()
        
        # Create error handler with all dependencies
        _error_handler = ErrorHandlingIntegration(
            # task_queue=task_queue,  # Will be injected when available
            # resource_queue=resource_queue,  # Will be injected when available
            # dead_letter_queue=dead_letter_queue,  # Will be injected when available
            # notification_service=notification_service,  # Will be injected when available
            # alert_service=alert_service,  # Will be injected when available
            # worker_manager=worker_manager,  # Will be injected when available
            # queue_manager=queue_manager,  # Will be injected when available
            resource_monitor=get_resource_monitor(),
            # storage_manager=storage_manager  # Will be injected when available
        )
        
        # Start error handling systems
        await _error_handler.start()
    
    return _error_handler


# Security scheme for authentication
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Get the current authenticated user.
    
    This is a placeholder implementation. In production, this would:
    - Validate the JWT token
    - Extract user information from the token
    - Check user permissions
    
    For now, returns a mock user ID.
    """
    # In development, return a mock user
    if not credentials:
        return "dev_user"
    
    # In production, validate token and extract user
    # Example:
    # try:
    #     payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
    #     user_id = payload.get("sub")
    #     if not user_id:
    #         raise HTTPException(status_code=401, detail="Invalid token")
    #     return user_id
    # except jwt.ExpiredSignatureError:
    #     raise HTTPException(status_code=401, detail="Token expired")
    # except jwt.JWTError:
    #     raise HTTPException(status_code=401, detail="Invalid token")
    
    return "authenticated_user"