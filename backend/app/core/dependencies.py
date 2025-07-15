"""
Application dependencies for dependency injection
"""

from typing import Optional
from pathlib import Path

from app.templates import TemplateRegistry
from app.config import settings


# Global template registry instance
_template_registry: Optional[TemplateRegistry] = None


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