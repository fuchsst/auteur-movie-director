"""
Asset Registry Service
STORY-083 Implementation

Manages registration, storage, and retrieval of all asset types
with support for the expanded asset system.
"""

import uuid
import json
from typing import Dict, List, Optional, Type, Union
from pathlib import Path
from datetime import datetime

from app.models.asset_types import (
    AssetType, AssetCategory, BaseAsset, PropAsset, WardrobeAsset, 
    VehicleAsset, SetDressingAsset, SFXAsset, SoundAsset, MusicAsset,
    AssetCollection, create_asset_from_dict, ASSET_TYPE_MAP
)


class AssetRegistry:
    """Central registry for all production assets with search and management capabilities."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.assets_dir = self.project_root / "01_Assets"
        self.generative_assets_dir = self.assets_dir / "Generative_Assets"
        
        # Ensure directory structure exists
        self._ensure_directories()
        
        # In-memory cache for performance
        self._asset_cache: Dict[str, BaseAsset] = {}
        self._type_index: Dict[AssetType, List[str]] = {t: [] for t in AssetType}
        self._category_index: Dict[str, List[str]] = {}
    
    def _ensure_directories(self):
        """Create necessary directory structure for asset storage."""
        directories = [
            self.generative_assets_dir / "Props",
            self.generative_assets_dir / "Wardrobe",
            self.generative_assets_dir / "Vehicles",
            self.generative_assets_dir / "Set_Dressing",
            self.generative_assets_dir / "SFX",
            self.generative_assets_dir / "Sounds",
            self.generative_assets_dir / "Music"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def register_asset(self, asset: BaseAsset) -> str:
        """Register a new asset in the registry."""
        # Generate unique ID if not provided
        if not asset.asset_id:
            asset.asset_id = str(uuid.uuid4())
        
        # Update timestamps
        asset.updated_at = datetime.now()
        
        # Store in cache
        self._asset_cache[asset.asset_id] = asset
        
        # Update indices
        self._type_index[asset.asset_type].append(asset.asset_id)
        
        category_key = f"{asset.asset_type.value}_{asset.category.value}"
        if category_key not in self._category_index:
            self._category_index[category_key] = []
        self._category_index[category_key].append(asset.asset_id)
        
        # Persist to disk
        await self._persist_asset(asset)
        
        return asset.asset_id
    
    async def _persist_asset(self, asset: BaseAsset) -> None:
        """Persist asset to filesystem."""
        asset_dir = self._get_asset_directory(asset)
        asset_file = asset_dir / f"{asset.asset_id}.json"
        
        # Ensure directory exists
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        # Write asset data
        with open(asset_file, 'w') as f:
            json.dump(asset.model_dump(), f, indent=2, default=str)
    
    def _get_asset_directory(self, asset: BaseAsset) -> Path:
        """Get the directory path for storing an asset."""
        type_map = {
            AssetType.PROP: "Props",
            AssetType.WARDROBE: "Wardrobe", 
            AssetType.VEHICLE: "Vehicles",
            AssetType.SET_DRESSING: "Set_Dressing",
            AssetType.SFX: "SFX",
            AssetType.SOUND: "Sounds",
            AssetType.MUSIC: "Music"
        }
        
        subdir = type_map.get(asset.asset_type, "Other")
        return self.generative_assets_dir / subdir
    
    async def get_asset(self, asset_id: str) -> Optional[BaseAsset]:
        """Retrieve an asset by ID."""
        # Check cache first
        if asset_id in self._asset_cache:
            return self._asset_cache[asset_id]
        
        # Load from disk
        asset = await self._load_asset(asset_id)
        if asset:
            self._asset_cache[asset_id] = asset
        
        return asset
    
    async def _load_asset(self, asset_id: str) -> Optional[BaseAsset]:
        """Load asset from filesystem."""
        # Search all asset directories
        for asset_type_dir in self.generative_assets_dir.iterdir():
            if asset_type_dir.is_dir():
                asset_file = asset_type_dir / f"{asset_id}.json"
                if asset_file.exists():
                    with open(asset_file, 'r') as f:
                        data = json.load(f)
                    return create_asset_from_dict(data)
        
        return None
    
    async def update_asset(self, asset_id: str, updates: Dict) -> bool:
        """Update an existing asset."""
        asset = await self.get_asset(asset_id)
        if not asset:
            return False
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(asset, key):
                setattr(asset, key, value)
        
        asset.version += 1
        asset.updated_at = datetime.now()
        
        # Persist changes
        await self._persist_asset(asset)
        
        # Update cache
        self._asset_cache[asset_id] = asset
        
        return True
    
    async def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset from the registry."""
        asset = await self.get_asset(asset_id)
        if not asset:
            return False
        
        # Remove from indices
        if asset_id in self._type_index[asset.asset_type]:
            self._type_index[asset.asset_type].remove(asset_id)
        
        category_key = f"{asset.asset_type.value}_{asset.category.value}"
        if category_key in self._category_index and asset_id in self._category_index[category_key]:
            self._category_index[category_key].remove(asset_id)
        
        # Remove from cache
        if asset_id in self._asset_cache:
            del self._asset_cache[asset_id]
        
        # Remove from filesystem
        asset_dir = self._get_asset_directory(asset)
        asset_file = asset_dir / f"{asset_id}.json"
        if asset_file.exists():
            asset_file.unlink()
        
        return True
    
    async def search_assets(
        self,
        query: str = "",
        asset_type: Optional[AssetType] = None,
        category: Optional[AssetCategory] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseAsset]:
        """Search assets with filtering and pagination."""
        results = []
        
        # Start with type filter if specified
        candidate_ids = []
        if asset_type:
            candidate_ids = self._type_index[asset_type]
        else:
            # Get all asset IDs
            candidate_ids = list(self._asset_cache.keys())
        
        # Filter by category
        if category:
            category_key = f"{asset_type.value}_{category.value}" if asset_type else f"*_{category.value}"
            category_assets = []
            for key, ids in self._category_index.items():
                if category_key in key or key.endswith(f"_{category.value}"):
                    category_assets.extend(ids)
            candidate_ids = list(set(candidate_ids) & set(category_assets))
        
        # Load and filter candidates
        for asset_id in candidate_ids[offset:offset+limit]:
            asset = await self.get_asset(asset_id)
            if not asset:
                continue
            
            # Text search
            if query:
                searchable_text = f"{asset.name} {asset.description} {' '.join(asset.tags)}".lower()
                if query.lower() not in searchable_text:
                    continue
            
            # Tag filtering
            if tags:
                if not any(tag.lower() in [t.lower() for t in asset.tags] for tag in tags):
                    continue
            
            results.append(asset)
        
        return results
    
    async def get_assets_by_type(self, asset_type: AssetType) -> List[BaseAsset]:
        """Get all assets of a specific type."""
        asset_ids = self._type_index[asset_type]
        assets = []
        
        for asset_id in asset_ids:
            asset = await self.get_asset(asset_id)
            if asset:
                assets.append(asset)
        
        return assets
    
    async def get_collection(self, collection_id: str) -> Optional[AssetCollection]:
        """Get a complete asset collection."""
        collection_file = self.assets_dir / f"collections/{collection_id}.json"
        
        if not collection_file.exists():
            return None
        
        with open(collection_file, 'r') as f:
            data = json.load(f)
        
        # Reconstruct assets
        props = [PropAsset(**p) for p in data.get('props', [])]
        wardrobe = [WardrobeAsset(**w) for w in data.get('wardrobe', [])]
        vehicles = [VehicleAsset(**v) for v in data.get('vehicles', [])]
        set_dressing = [SetDressingAsset(**s) for s in data.get('set_dressing', [])]
        sfx = [SFXAsset(**s) for s in data.get('sfx', [])]
        sounds = [SoundAsset(**s) for s in data.get('sounds', [])]
        music = [MusicAsset(**m) for m in data.get('music', [])]
        
        return AssetCollection(
            collection_id=collection_id,
            name=data['name'],
            description=data['description'],
            props=props,
            wardrobe=wardrobe,
            vehicles=vehicles,
            set_dressing=set_dressing,
            sfx=sfx,
            sounds=sounds,
            music=music,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
    
    async def save_collection(self, collection: AssetCollection) -> str:
        """Save an asset collection."""
        collection_dir = self.assets_dir / "collections"
        collection_dir.mkdir(parents=True, exist_ok=True)
        
        collection_file = collection_dir / f"{collection.collection_id}.json"
        
        # Prepare data for JSON serialization
        data = collection.model_dump()
        data['created_at'] = collection.created_at.isoformat()
        data['updated_at'] = collection.updated_at.isoformat()
        
        with open(collection_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return collection.collection_id
    
    async def get_usage_statistics(self) -> Dict:
        """Get usage statistics for all assets."""
        stats = {
            'total_assets': len(self._asset_cache),
            'by_type': {},
            'by_category': {},
            'most_used': [],
            'unused': []
        }
        
        # Count by type
        for asset_type in AssetType:
            stats['by_type'][asset_type.value] = len(self._type_index[asset_type])
        
        # Count by category
        for category_key, asset_ids in self._category_index.items():
            stats['by_category'][category_key] = len(asset_ids)
        
        # Most used assets
        assets = [await self.get_asset(aid) for aid in self._asset_cache.keys()]
        assets = [a for a in assets if a]
        
        stats['most_used'] = sorted(
            assets,
            key=lambda x: x.usage_count,
            reverse=True
        )[:10]
        
        stats['unused'] = [a for a in assets if a.usage_count == 0]
        
        return stats
    
    async def reload(self) -> None:
        """Reload all assets from disk."""
        self._asset_cache.clear()
        self._type_index = {t: [] for t in AssetType}
        self._category_index.clear()
        
        # Scan all asset directories
        for asset_type_dir in self.generative_assets_dir.iterdir():
            if asset_type_dir.is_dir():
                for asset_file in asset_type_dir.glob("*.json"):
                    try:
                        with open(asset_file, 'r') as f:
                            data = json.load(f)
                        asset = create_asset_from_dict(data)
                        
                        self._asset_cache[asset.asset_id] = asset
                        self._type_index[asset.asset_type].append(asset.asset_id)
                        
                        category_key = f"{asset.asset_type.value}_{asset.category.value}"
                        if category_key not in self._category_index:
                            self._category_index[category_key] = []
                        self._category_index[category_key].append(asset.asset_id)
                        
                    except Exception as e:
                        print(f"Error loading asset {asset_file}: {e}")


class AssetRegistryAPI:
    """API wrapper for the asset registry service."""
    
    def __init__(self, project_root: str):
        self.registry = AssetRegistry(Path(project_root))
    
    async def create_asset(self, asset_data: dict) -> dict:
        """Create a new asset via API."""
        asset_type = AssetType(asset_data['asset_type'])
        asset_class = ASSET_TYPE_MAP[asset_type]
        
        # Ensure asset_id is generated if not provided
        if 'asset_id' not in asset_data:
            import uuid
            asset_data['asset_id'] = str(uuid.uuid4())
            
        asset = asset_class(**asset_data)
        
        asset_id = await self.registry.register_asset(asset)
        return {"asset_id": asset_id, "status": "created"}
    
    async def get_asset(self, asset_id: str) -> dict:
        """Get asset details via API."""
        asset = await self.registry.get_asset(asset_id)
        return asset.model_dump() if asset else None
    
    async def update_asset(self, asset_id: str, updates: dict) -> dict:
        """Update asset via API."""
        success = await self.registry.update_asset(asset_id, updates)
        return {"success": success}
    
    async def search_assets(self, query: str = "", category=None, tags=None, limit=100, offset=0) -> dict:
        """Search assets via API."""
        results = await self.registry.search_assets(
            query=query, 
            asset_type=category, 
            tags=tags, 
            limit=limit, 
            offset=offset
        )
        return {"assets": [asset.model_dump() for asset in results]}

    async def get_collection(self, collection_id: str) -> dict:
        """Get asset collection via API."""
        collection = await self.registry.get_collection(collection_id)
        return collection.model_dump() if collection else None