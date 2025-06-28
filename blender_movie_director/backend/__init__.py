"""Backend Integration Layer for Blender Movie Director.

This module provides unified API integration with local generative services.
"""

from . import service_discovery


def register():
    """Register backend components."""
    # Service discovery is core functionality but doesn't need explicit registration
    # as it's used by other components
    pass


def unregister():
    """Unregister backend components."""
    pass
