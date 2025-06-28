"""Wan2GP Client Integration for Blender Movie Director.

This module provides a lean interface to the Wan2GP client for video generation.
The main implementation is in client.py - this just provides convenient access.
"""

from typing import Optional

from .client import Wan2GPClient
from .enums import Wan2GPModel, RECOMMENDED_SETTINGS
from .schemas import GenerationSettings, GenerationResult, ServerStatus

# Singleton instance
_client_instance = None


def get_client(server_address: str = "http://localhost:7860") -> Wan2GPClient:
    """Get the singleton Wan2GP client instance."""
    global _client_instance
    if _client_instance is None or _client_instance.server_address != server_address:
        _client_instance = Wan2GPClient(server_address)
    return _client_instance


# Convenience functions for common workflows
def quick_video(prompt: str, **kwargs) -> Optional[str]:
    """Generate a quick preview video."""
    client = get_client()
    result = client.generate_quick(prompt, **kwargs)
    return result.video_path if result.success else None


def quality_video(prompt: str, **kwargs) -> Optional[str]:
    """Generate a high-quality video."""
    client = get_client()
    result = client.generate_high_quality(prompt, **kwargs)
    return result.video_path if result.success else None


def controlled_video(prompt: str, control_video_path: str, **kwargs) -> Optional[str]:
    """Generate video with ControlNet guidance."""
    client = get_client()
    result = client.generate_with_control(prompt, control_video_path, **kwargs)
    return result.video_path if result.success else None


# Export the main classes for direct use
__all__ = [
    'Wan2GPClient',
    'GenerationSettings', 
    'GenerationResult',
    'ServerStatus',
    'Wan2GPModel',
    'get_client',
    'quick_video',
    'quality_video', 
    'controlled_video',
]
