"""
Comprehensive tests for STORY-083: Expanded Asset System
Tests all asset types, registry functionality, and API endpoints.
"""

import pytest
import asyncio
import uuid
from pathlib import Path
from datetime import datetime

from app.models.asset_types import (
    AssetType, AssetCategory, PropAsset, WardrobeAsset, VehicleAsset,
    SetDressingAsset, SFXAsset, SoundAsset, MusicAsset, AssetCollection,
    create_asset_from_dict
)
from app.services.asset_registry import AssetRegistry, AssetRegistryAPI


class TestAssetModels:
    """Test all asset model types"""
    
    def test_prop_asset_creation(self):
        """Test creating a prop asset"""
        prop = PropAsset(
            asset_id="test-prop-001",
            name="Ancient Sword",
            description="A weathered bronze sword",
            category=AssetCategory.WEAPON,
            material="bronze",
            is_weapon=True,
            tags=["ancient", "weapon"]
        )
        
        assert prop.asset_type == AssetType.PROP
        assert prop.name == "Ancient Sword"
        assert prop.material == "bronze"
        assert prop.is_weapon is True
        assert prop.asset_id == "test-prop-001"
    
    def test_wardrobe_asset_creation(self):
        """Test creating a wardrobe asset"""
        wardrobe = WardrobeAsset(
            asset_id="test-wardrobe-001",
            name="Medieval Tunic",
            description="A simple medieval tunic",
            category=AssetCategory.OUTERWEAR,
            character_name="Sir Knight",
            color="brown",
            style="medieval",
            tags=["medieval", "clothing"]
        )
        
        assert wardrobe.asset_type == AssetType.WARDROBE
        assert wardrobe.character_name == "Sir Knight"
        assert wardrobe.color == "brown"
        assert wardrobe.style == "medieval"
    
    def test_vehicle_asset_creation(self):
        """Test creating a vehicle asset"""
        vehicle = VehicleAsset(
            asset_id="test-vehicle-001",
            name="1967 Mustang",
            description="Classic American muscle car",
            category=AssetCategory.LAND,
            make="Ford",
            model="Mustang",
            year=1967,
            color="red",
            tags=["classic", "muscle", "car"]
        )
        
        assert vehicle.asset_type == AssetType.VEHICLE
        assert vehicle.make == "Ford"
        assert vehicle.model == "Mustang"
        assert vehicle.year == 1967
    
    def test_set_dressing_asset_creation(self):
        """Test creating set dressing asset"""
        dressing = SetDressingAsset(
            asset_id="test-dressing-001",
            name="Medieval Tapestry",
            description="Large wall tapestry",
            category=AssetCategory.DECORATIVE,
            placement="wall",
            style="medieval",
            tags=["decoration", "medieval"]
        )
        
        assert dressing.asset_type == AssetType.SET_DRESSING
        assert dressing.placement == "wall"
        assert dressing.style == "medieval"
    
    def test_sfx_asset_creation(self):
        """Test creating SFX asset"""
        sfx = SFXAsset(
            asset_id="test-sfx-001",
            name="Explosion",
            description="Large explosion effect",
            category=AssetCategory.DIGITAL,
            effect_type="explosion",
            intensity="extreme",
            duration=3.5,
            tags=["explosion", "destruction"]
        )
        
        assert sfx.asset_type == AssetType.SFX
        assert sfx.effect_type == "explosion"
        assert sfx.intensity == "extreme"
        assert sfx.duration == 3.5
    
    def test_sound_asset_creation(self):
        """Test creating sound asset"""
        sound = SoundAsset(
            asset_id="test-sound-001",
            name="Ambient Forest",
            description="Peaceful forest ambient sounds",
            category=AssetCategory.AMBIENT,
            duration=300.0,
            loopable=True,
            tags=["ambient", "nature"]
        )
        
        assert sound.asset_type == AssetType.SOUND
        assert sound.duration == 300.0
        assert sound.loopable is True
    
    def test_music_asset_creation(self):
        """Test creating music asset"""
        music = MusicAsset(
            asset_id="test-music-001",
            name="Epic Battle Theme",
            description="Orchestral battle music",
            category=AssetCategory.SCORE,
            tempo=120,
            key="C minor",
            mood="epic",
            duration=180.0,
            tags=["epic", "battle", "orchestral"]
        )
        
        assert music.asset_type == AssetType.MUSIC
        assert music.tempo == 120
        assert music.key == "C minor"
        assert music.mood == "epic"
    
    def test_asset_factory_function(self):
        """Test the asset factory function"""
        prop_data = {
            "asset_id": "factory-test-001",
            "name": "Factory Prop",
            "description": "Created via factory",
            "asset_type": "prop",
            "category": "weapon",
            "material": "steel"
        }
        
        asset = create_asset_from_dict(prop_data)
        assert isinstance(asset, PropAsset)
        assert asset.name == "Factory Prop"


class TestAssetRegistry:
    """Test the asset registry functionality"""
    
    @pytest.fixture
    def registry(self, tmp_path):
        """Create a test registry"""
        return AssetRegistry(tmp_path)
    
    @pytest.mark.asyncio
    async def test_register_asset(self, registry):
        """Test registering an asset"""
        prop = PropAsset(
            asset_id="test-prop-001",
            name="Test Prop",
            description="Test description",
            category=AssetCategory.TOOL
        )
        
        asset_id = await registry.register_asset(prop)
        assert asset_id == "test-prop-001"
        
        # Verify asset was stored
        retrieved = await registry.get_asset(asset_id)
        assert retrieved is not None
        assert retrieved.name == "Test Prop"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_asset(self, registry):
        """Test getting non-existent asset"""
        asset = await registry.get_asset("nonexistent")
        assert asset is None
    
    @pytest.mark.asyncio
    async def test_update_asset(self, registry):
        """Test updating an asset"""
        prop = PropAsset(
            asset_id="update-test-001",
            name="Original Name",
            description="Original description",
            category=AssetCategory.TOOL
        )
        
        await registry.register_asset(prop)
        
        # Update the asset
        updates = {"name": "Updated Name", "description": "Updated description"}
        success = await registry.update_asset("update-test-001", updates)
        assert success is True
        
        # Verify update
        updated = await registry.get_asset("update-test-001")
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.version == 2
    
    @pytest.mark.asyncio
    async def test_delete_asset(self, registry):
        """Test deleting an asset"""
        prop = PropAsset(
            asset_id="delete-test-001",
            name="To Delete",
            description="Will be deleted",
            category=AssetCategory.TOOL
        )
        
        await registry.register_asset(prop)
        
        # Delete the asset
        success = await registry.delete_asset("delete-test-001")
        assert success is True
        
        # Verify deletion
        deleted = await registry.get_asset("delete-test-001")
        assert deleted is None
    
    @pytest.mark.asyncio
    async def test_search_assets(self, registry):
        """Test searching assets"""
        # Register multiple assets
        assets = [
            PropAsset(
                asset_id="search-test-001",
                name="Magic Sword",
                description="A magical sword",
                category=AssetCategory.WEAPON,
                tags=["magic", "weapon"]
            ),
            WardrobeAsset(
                asset_id="search-test-002",
                name="Magic Robe",
                description="A magical robe",
                category=AssetCategory.OUTERWEAR,
                style="magical",
                tags=["magic", "clothing"]
            ),
            VehicleAsset(
                asset_id="search-test-003",
                name="Magic Carpet",
                description="A flying carpet",
                category=AssetCategory.AIR,
                tags=["magic", "transport"]
            )
        ]
        
        for asset in assets:
            await registry.register_asset(asset)
        
        # Test search by query
        results = await registry.search_assets(query="magic")
        assert len(results) == 3
        
        # Test search by type
        results = await registry.search_assets(asset_type=AssetType.PROP)
        assert len(results) == 1
        assert results[0].asset_type == AssetType.PROP
        
        # Test search by tags
        results = await registry.search_assets(tags=["weapon"])
        assert len(results) == 1
        assert results[0].name == "Magic Sword"
    
    @pytest.mark.asyncio
    async def test_pagination(self, registry):
        """Test pagination functionality"""
        # Register 10 assets
        for i in range(10):
            prop = PropAsset(
                asset_id=f"page-test-{i:03d}",
                name=f"Prop {i}",
                description=f"Test prop {i}",
                category=AssetCategory.TOOL
            )
            await registry.register_asset(prop)
        
        # Test pagination
        results = await registry.search_assets(limit=5, offset=0)
        assert len(results) == 5
        
        results = await registry.search_assets(limit=5, offset=5)
        assert len(results) == 5
        
        results = await registry.search_assets(limit=3, offset=8)
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_asset_collections(self, registry):
        """Test asset collections"""
        # Create test assets
        prop = PropAsset(
            asset_id="collection-prop-001",
            name="Collection Prop",
            description="Part of collection",
            category=AssetCategory.TOOL
        )
        
        wardrobe = WardrobeAsset(
            asset_id="collection-wardrobe-001",
            name="Collection Wardrobe",
            description="Part of collection",
            category=AssetCategory.OUTERWEAR,
            style="casual"
        )
        
        await registry.register_asset(prop)
        await registry.register_asset(wardrobe)
        
        # Create collection
        collection = AssetCollection(
            collection_id="test-collection-001",
            name="Test Collection",
            description="A test collection",
            props=[prop],
            wardrobe=[wardrobe]
        )
        
        collection_id = await registry.save_collection(collection)
        assert collection_id == "test-collection-001"
        
        # Retrieve collection
        retrieved = await registry.get_collection(collection_id)
        assert retrieved is not None
        assert retrieved.name == "Test Collection"
        assert len(retrieved.props) == 1
        assert len(retrieved.wardrobe) == 1
    
    @pytest.mark.asyncio
    async def test_usage_statistics(self, registry):
        """Test usage statistics"""
        # Register some assets
        assets = [
            PropAsset(
                asset_id="stats-test-001",
                name="Stats Prop 1",
                description="Test prop 1",
                category=AssetCategory.TOOL
            ),
            PropAsset(
                asset_id="stats-test-002",
                name="Stats Prop 2",
                description="Test prop 2",
                category=AssetCategory.WEAPON
            ),
            WardrobeAsset(
                asset_id="stats-test-003",
                name="Stats Wardrobe",
                description="Test wardrobe",
                category=AssetCategory.OUTERWEAR,
                style="formal"
            )
        ]
        
        for asset in assets:
            await registry.register_asset(asset)
        
        # Get statistics
        stats = await registry.get_usage_statistics()
        
        assert stats["total_assets"] == 3
        assert stats["by_type"]["prop"] == 2
        assert stats["by_type"]["wardrobe"] == 1
        assert "prop_tool" in stats["by_category"]
        assert "prop_weapon" in stats["by_category"]
        assert "wardrobe_outerwear" in stats["by_category"]


class TestAssetRegistryAPI:
    """Test the API wrapper for asset registry"""
    
    @pytest.fixture
    def api_service(self, tmp_path):
        """Create a test API service"""
        return AssetRegistryAPI(str(tmp_path))
    
    @pytest.mark.asyncio
    async def test_api_create_asset(self, api_service):
        """Test API asset creation"""
        asset_data = {
            "asset_type": AssetType.PROP,
            "category": AssetCategory.TOOL,
            "name": "API Test Prop",
            "description": "Created via API",
            "tags": ["api", "test"]
        }
        
        result = await api_service.create_asset(asset_data)
        assert "asset_id" in result
        assert result["asset_id"] is not None
    
    @pytest.mark.asyncio
    async def test_api_get_asset(self, api_service):
        """Test API asset retrieval"""
        # Create asset first
        asset_data = {
            "asset_type": AssetType.PROP,
            "category": AssetCategory.TOOL,
            "name": "API Get Test",
            "description": "Test asset for API get"
        }
        
        create_result = await api_service.create_asset(asset_data)
        asset_id = create_result["asset_id"]
        
        # Get via API
        asset = await api_service.get_asset(asset_id)
        assert asset is not None
        assert asset["name"] == "API Get Test"
    
    @pytest.mark.asyncio
    async def test_api_search_assets(self, api_service):
        """Test API asset search"""
        # Create test assets
        for i in range(3):
            asset_data = {
                "asset_type": AssetType.PROP,
                "category": AssetCategory.TOOL,
                "name": f"API Search Test {i}",
                "description": f"Search test {i}",
                "tags": ["api", "search", f"test-{i}"]
            }
            await api_service.create_asset(asset_data)
        
        # Search via API
        results = await api_service.search_assets(query="Search")
        assert "assets" in results
        assert len(results["assets"]) >= 3
    
    @pytest.mark.asyncio
    async def test_api_update_asset(self, api_service):
        """Test API asset update"""
        # Create asset
        asset_data = {
            "asset_type": AssetType.PROP,
            "category": AssetCategory.TOOL,
            "name": "API Update Original",
            "description": "Original description"
        }
        
        create_result = await api_service.create_asset(asset_data)
        asset_id = create_result["asset_id"]
        
        # Update via API
        updates = {"name": "API Update New", "description": "Updated description"}
        result = await api_service.update_asset(asset_id, updates)
        assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])