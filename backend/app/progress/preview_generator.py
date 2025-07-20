"""Preview generation during task execution"""

import asyncio
import hashlib
from typing import Optional, Dict, Any, Set
from datetime import datetime
import aiofiles
import os
from pathlib import Path

from app.config import settings


class PreviewGenerator:
    """Generate preview images during task execution"""
    
    def __init__(self, preview_dir: Optional[str] = None):
        self.preview_dir = Path(preview_dir or settings.PREVIEW_DIR)
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        self.preview_cache: Dict[str, str] = {}
        self.generation_locks: Dict[str, asyncio.Lock] = {}
        self.preview_intervals = [0.25, 0.5, 0.75]  # Generate at these progress points
    
    async def generate_preview(
        self, 
        task_id: str, 
        task_data: Dict[str, Any],
        stage_progress: float,
        stage_name: str
    ) -> Optional[str]:
        """Generate preview image for current progress"""
        
        # Check if preview generation is appropriate
        if not self._should_generate_preview(task_data, stage_progress, stage_name):
            return None
        
        # Create cache key
        cache_key = self._get_cache_key(task_id, stage_progress)
        
        # Check cache
        if cache_key in self.preview_cache:
            return self.preview_cache[cache_key]
        
        # Get or create lock for this task
        if task_id not in self.generation_locks:
            self.generation_locks[task_id] = asyncio.Lock()
        
        # Ensure only one preview generation per task at a time
        async with self.generation_locks[task_id]:
            # Double-check cache after acquiring lock
            if cache_key in self.preview_cache:
                return self.preview_cache[cache_key]
            
            try:
                # Generate preview based on task type
                preview_data = await self._generate_preview_data(
                    task_data, 
                    stage_progress,
                    stage_name
                )
                
                if preview_data:
                    # Store preview
                    preview_url = await self._store_preview(
                        task_id, 
                        preview_data,
                        stage_progress
                    )
                    self.preview_cache[cache_key] = preview_url
                    return preview_url
                    
            except Exception as e:
                # Log error but don't fail the main task
                print(f"Preview generation error: {e}")
                
        return None
    
    def _should_generate_preview(
        self, 
        task_data: Dict[str, Any], 
        progress: float,
        stage_name: str
    ) -> bool:
        """Determine if preview should be generated"""
        # Only generate during main execution stages
        if stage_name not in ['generation', 'frame_generation', 'synthesis', 'execution']:
            return False
        
        # Check if task type supports previews
        task_type = task_data.get('type', '')
        if task_type not in ['image_generation', 'video_generation', 'audio_generation']:
            return False
        
        # Check if we're at a preview interval
        tolerance = 0.02
        for interval in self.preview_intervals:
            if abs(progress - interval) < tolerance:
                return True
        
        return False
    
    async def _generate_preview_data(
        self, 
        task_data: Dict[str, Any],
        progress: float,
        stage_name: str
    ) -> Optional[bytes]:
        """Generate preview data based on task type"""
        task_type = task_data.get('type', '')
        
        if task_type == 'image_generation':
            return await self._generate_image_preview(task_data, progress)
        elif task_type == 'video_generation':
            return await self._generate_video_preview(task_data, progress)
        elif task_type == 'audio_generation':
            return await self._generate_audio_preview(task_data, progress)
        
        return None
    
    async def _generate_image_preview(
        self, 
        task_data: Dict[str, Any],
        progress: float
    ) -> Optional[bytes]:
        """Generate preview for image generation tasks"""
        # Get intermediate output path from task data
        intermediate_path = task_data.get('intermediate_output')
        if not intermediate_path or not os.path.exists(intermediate_path):
            return None
        
        # Read and potentially resize image
        try:
            async with aiofiles.open(intermediate_path, 'rb') as f:
                image_data = await f.read()
            
            # TODO: Resize image if too large
            # For now, just return the raw data
            return image_data
            
        except Exception:
            return None
    
    async def _generate_video_preview(
        self, 
        task_data: Dict[str, Any],
        progress: float
    ) -> Optional[bytes]:
        """Generate preview frame for video generation tasks"""
        # Get frame at current progress
        frames_dir = task_data.get('frames_dir')
        if not frames_dir or not os.path.exists(frames_dir):
            return None
        
        # Calculate which frame to use
        total_frames = task_data.get('total_frames', 30)
        frame_index = int(total_frames * progress)
        frame_path = os.path.join(frames_dir, f"frame_{frame_index:04d}.png")
        
        if not os.path.exists(frame_path):
            return None
        
        try:
            async with aiofiles.open(frame_path, 'rb') as f:
                return await f.read()
        except Exception:
            return None
    
    async def _generate_audio_preview(
        self, 
        task_data: Dict[str, Any],
        progress: float
    ) -> Optional[bytes]:
        """Generate waveform preview for audio generation tasks"""
        # TODO: Implement waveform generation
        # For now, return None
        return None
    
    async def _store_preview(
        self, 
        task_id: str, 
        preview_data: bytes,
        progress: float
    ) -> str:
        """Store preview data and return URL"""
        # Generate filename
        timestamp = int(datetime.now().timestamp())
        progress_int = int(progress * 100)
        filename = f"{task_id}_{progress_int}_{timestamp}.png"
        
        # Store file
        file_path = self.preview_dir / filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(preview_data)
        
        # Return URL
        return f"/api/v1/previews/{filename}"
    
    def _get_cache_key(self, task_id: str, progress: float) -> str:
        """Generate cache key for preview"""
        progress_int = int(progress * 100 / 5) * 5  # Round to nearest 5%
        return f"{task_id}:{progress_int}"
    
    async def cleanup_task_previews(self, task_id: str):
        """Clean up previews for a completed task"""
        # Remove from cache
        keys_to_remove = [
            key for key in self.preview_cache.keys() 
            if key.startswith(f"{task_id}:")
        ]
        for key in keys_to_remove:
            del self.preview_cache[key]
        
        # Remove lock
        if task_id in self.generation_locks:
            del self.generation_locks[task_id]
        
        # Optionally delete files (keep for history)
        # This could be done by a cleanup job later