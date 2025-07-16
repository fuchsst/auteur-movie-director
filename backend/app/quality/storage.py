"""
Preset Storage and Retrieval

Handles persistence of custom quality presets.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .models import QualityPreset, QualityLevel
from .exceptions import PresetNotFoundError, PresetValidationError

logger = logging.getLogger(__name__)


class PresetStorage:
    """Store and retrieve custom presets"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./data/quality_presets")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        self._ensure_storage()
    
    def _ensure_storage(self):
        """Ensure storage directories exist"""
        (self.storage_path / "users").mkdir(exist_ok=True)
        (self.storage_path / "shared").mkdir(exist_ok=True)
        (self.storage_path / "exports").mkdir(exist_ok=True)
    
    async def save_preset(self, preset: QualityPreset, user_id: str) -> bool:
        """Save custom preset"""
        
        # Validate preset
        if not preset.is_custom:
            raise PresetValidationError("Cannot save built-in preset")
        
        if not preset.name:
            raise PresetValidationError("Preset must have a name")
        
        # Create user directory if needed
        user_dir = self.storage_path / "users" / user_id
        user_dir.mkdir(exist_ok=True)
        
        # Save preset file
        preset_file = user_dir / f"{preset.id}.json"
        
        try:
            preset_data = preset.to_dict()
            preset_data['user_id'] = user_id
            
            with open(preset_file, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            # Update cache
            cache_key = f"{user_id}:{preset.id}"
            self.cache[cache_key] = preset
            
            logger.info(f"Saved preset {preset.id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save preset {preset.id}: {e}")
            raise PresetValidationError(f"Failed to save preset: {e}")
    
    async def get_preset(self, preset_id: str, user_id: Optional[str] = None) -> Optional[QualityPreset]:
        """Get a specific preset"""
        
        # Check cache
        if user_id:
            cache_key = f"{user_id}:{preset_id}"
            if cache_key in self.cache:
                return self.cache[cache_key]
        
        # Search in user presets
        if user_id:
            preset_file = self.storage_path / "users" / user_id / f"{preset_id}.json"
            if preset_file.exists():
                return await self._load_preset_file(preset_file, user_id)
        
        # Search in shared presets
        shared_file = self.storage_path / "shared" / f"{preset_id}.json"
        if shared_file.exists():
            return await self._load_preset_file(shared_file)
        
        # Search all users (admin access)
        for user_dir in (self.storage_path / "users").iterdir():
            if user_dir.is_dir():
                preset_file = user_dir / f"{preset_id}.json"
                if preset_file.exists():
                    return await self._load_preset_file(preset_file, user_dir.name)
        
        return None
    
    async def get_user_presets(self, user_id: str) -> List[QualityPreset]:
        """Get all presets for a user"""
        
        presets = []
        user_dir = self.storage_path / "users" / user_id
        
        if not user_dir.exists():
            return presets
        
        # Load all preset files
        for preset_file in user_dir.glob("*.json"):
            try:
                preset = await self._load_preset_file(preset_file, user_id)
                if preset:
                    presets.append(preset)
            except Exception as e:
                logger.warning(f"Failed to load preset {preset_file}: {e}")
        
        # Sort by creation date (newest first)
        presets.sort(key=lambda p: p.created_at or datetime.min, reverse=True)
        
        return presets
    
    async def update_preset(self, preset: QualityPreset, user_id: str) -> bool:
        """Update an existing preset"""
        
        # Verify ownership
        existing = await self.get_preset(preset.id, user_id)
        if not existing:
            raise PresetNotFoundError(f"Preset {preset.id} not found")
        
        if existing.created_by != user_id:
            raise PresetValidationError("Cannot update preset created by another user")
        
        # Update timestamp
        preset.updated_at = datetime.now()
        
        # Save updated preset
        return await self.save_preset(preset, user_id)
    
    async def delete_preset(self, preset_id: str, user_id: str) -> bool:
        """Delete a preset"""
        
        preset_file = self.storage_path / "users" / user_id / f"{preset_id}.json"
        
        if not preset_file.exists():
            raise PresetNotFoundError(f"Preset {preset_id} not found")
        
        try:
            # Remove file
            preset_file.unlink()
            
            # Remove from cache
            cache_key = f"{user_id}:{preset_id}"
            self.cache.pop(cache_key, None)
            
            logger.info(f"Deleted preset {preset_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete preset {preset_id}: {e}")
            return False
    
    async def update_usage_stats(self, preset_id: str, usage_count: int) -> bool:
        """Update usage statistics for a preset"""
        
        # Find preset file
        preset_file = None
        for path in [self.storage_path / "shared", self.storage_path / "users"]:
            for file in path.rglob(f"{preset_id}.json"):
                preset_file = file
                break
        
        if not preset_file:
            return False
        
        try:
            # Load and update
            with open(preset_file, 'r') as f:
                data = json.load(f)
            
            data['usage_count'] = usage_count
            data['updated_at'] = datetime.now().isoformat()
            
            with open(preset_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update usage stats for {preset_id}: {e}")
            return False
    
    async def export_preset(self, preset_id: str, user_id: str) -> Optional[str]:
        """Export a preset for sharing"""
        
        preset = await self.get_preset(preset_id, user_id)
        if not preset:
            raise PresetNotFoundError(f"Preset {preset_id} not found")
        
        # Create export file
        export_file = self.storage_path / "exports" / f"{preset_id}_export.json"
        
        try:
            export_data = preset.to_dict()
            # Remove user-specific data
            export_data.pop('created_by', None)
            export_data.pop('usage_count', None)
            export_data['exported_at'] = datetime.now().isoformat()
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return str(export_file)
            
        except Exception as e:
            logger.error(f"Failed to export preset {preset_id}: {e}")
            return None
    
    async def import_preset(self, preset_data: Dict[str, Any], user_id: str) -> QualityPreset:
        """Import a preset from exported data"""
        
        try:
            # Convert level if needed
            if isinstance(preset_data.get('level'), int):
                preset_data['level'] = QualityLevel(preset_data['level'])
            
            # Create new preset with new ID
            preset_data['id'] = f"imported_{preset_data.get('id', 'unknown')}_{datetime.now().timestamp():.0f}"
            preset_data['is_custom'] = True
            preset_data['created_by'] = user_id
            preset_data['created_at'] = datetime.now()
            preset_data['updated_at'] = datetime.now()
            preset_data['usage_count'] = 0
            
            # Remove export metadata
            preset_data.pop('exported_at', None)
            
            # Create preset
            preset = QualityPreset.from_dict(preset_data)
            
            # Save it
            await self.save_preset(preset, user_id)
            
            return preset
            
        except Exception as e:
            logger.error(f"Failed to import preset: {e}")
            raise PresetValidationError(f"Failed to import preset: {e}")
    
    async def share_preset(self, preset_id: str, user_id: str) -> bool:
        """Share a preset with all users"""
        
        preset = await self.get_preset(preset_id, user_id)
        if not preset:
            raise PresetNotFoundError(f"Preset {preset_id} not found")
        
        if preset.created_by != user_id:
            raise PresetValidationError("Cannot share preset created by another user")
        
        # Copy to shared directory
        source_file = self.storage_path / "users" / user_id / f"{preset_id}.json"
        dest_file = self.storage_path / "shared" / f"{preset_id}.json"
        
        try:
            preset_data = preset.to_dict()
            preset_data['shared_by'] = user_id
            preset_data['shared_at'] = datetime.now().isoformat()
            
            with open(dest_file, 'w') as f:
                json.dump(preset_data, f, indent=2)
            
            logger.info(f"Shared preset {preset_id} from user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to share preset {preset_id}: {e}")
            return False
    
    async def get_shared_presets(self) -> List[QualityPreset]:
        """Get all shared presets"""
        
        presets = []
        shared_dir = self.storage_path / "shared"
        
        if not shared_dir.exists():
            return presets
        
        for preset_file in shared_dir.glob("*.json"):
            try:
                preset = await self._load_preset_file(preset_file)
                if preset:
                    presets.append(preset)
            except Exception as e:
                logger.warning(f"Failed to load shared preset {preset_file}: {e}")
        
        return presets
    
    async def _load_preset_file(self, preset_file: Path, user_id: Optional[str] = None) -> Optional[QualityPreset]:
        """Load preset from file"""
        
        try:
            with open(preset_file, 'r') as f:
                data = json.load(f)
            
            # Convert timestamps
            for field in ['created_at', 'updated_at']:
                if data.get(field):
                    data[field] = datetime.fromisoformat(data[field])
            
            # Convert level
            if isinstance(data.get('level'), int):
                data['level'] = QualityLevel(data['level'])
            
            preset = QualityPreset(**{k: v for k, v in data.items() if k != 'user_id'})
            
            # Cache it
            if user_id:
                cache_key = f"{user_id}:{preset.id}"
                self.cache[cache_key] = preset
            
            return preset
            
        except Exception as e:
            logger.error(f"Failed to load preset from {preset_file}: {e}")
            return None
    
    async def cleanup_old_presets(self, days: int = 90) -> int:
        """Clean up old unused presets"""
        
        count = 0
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for user_dir in (self.storage_path / "users").iterdir():
            if not user_dir.is_dir():
                continue
            
            for preset_file in user_dir.glob("*.json"):
                try:
                    # Check last modified time
                    if preset_file.stat().st_mtime < cutoff_date:
                        # Check usage
                        with open(preset_file, 'r') as f:
                            data = json.load(f)
                        
                        if data.get('usage_count', 0) == 0:
                            preset_file.unlink()
                            count += 1
                            logger.info(f"Cleaned up unused preset {preset_file.name}")
                
                except Exception as e:
                    logger.warning(f"Failed to check preset {preset_file}: {e}")
        
        return count