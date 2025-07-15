"""
Application dependencies for dependency injection
"""

from typing import Optional
from pathlib import Path

from app.templates import TemplateRegistry
from app.resources import ResourceMapper, GPUResourceManager, ResourceMonitor
from app.config import settings


# Global instances
_template_registry: Optional[TemplateRegistry] = None
_resource_mapper: Optional[ResourceMapper] = None
_gpu_manager: Optional[GPUResourceManager] = None
_resource_monitor: Optional[ResourceMonitor] = None


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