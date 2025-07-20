"""
Progress tracker dependencies to avoid circular imports
"""

from typing import Optional
from app.progress.tracker import ProgressTracker
from app.core.dependencies import get_redis_client, get_ws_manager

# Global instance
_progress_tracker: Optional[ProgressTracker] = None


async def get_progress_tracker() -> ProgressTracker:
    """
    Get or create progress tracker instance.
    
    Returns:
        ProgressTracker: Progress tracker instance
    """
    global _progress_tracker
    
    if _progress_tracker is None:
        redis_client = await get_redis_client()
        ws_manager = get_ws_manager()
        from app.config import settings
        
        _progress_tracker = ProgressTracker(
            redis_client, 
            ws_manager,
            preview_dir=str(settings.PREVIEW_DIR)
        )
    
    return _progress_tracker