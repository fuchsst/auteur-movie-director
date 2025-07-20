"""
Expanded Asset System Models
STORY-083 Implementation

Defines comprehensive asset types for film production breakdown elements
including props, wardrobe, vehicles, set dressing, SFX, and music.
"""

from typing import Dict, List, Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class AssetType(str, Enum):
    """Enumeration of all supported asset types in the expanded system."""
    CHARACTER = "character"
    STYLE = "style"
    LOCATION = "location"
    PROP = "prop"
    WARDROBE = "wardrobe"
    VEHICLE = "vehicle"
    SET_DRESSING = "set_dressing"
    SFX = "sfx"
    SOUND = "sound"
    MUSIC = "music"


class PropagationMode(str, Enum):
    """Propagation modes for asset inheritance rules."""
    INHERIT = "inherit"
    OVERRIDE = "override"
    MERGE = "merge"
    BLOCK = "block"


class AssetCategory(str, Enum):
    """Categories for organizing assets within each type."""
    # Prop categories
    WEAPON = "weapon"
    TOOL = "tool"
    FURNITURE = "furniture"
    ELECTRONIC = "electronic"
    ARTIFACT = "artifact"
    
    # Wardrobe categories
    OUTERWEAR = "outerwear"
    INNERWEAR = "innerwear"
    FOOTWEAR = "footwear"
    ACCESSORY = "accessory"
    UNIFORM = "uniform"
    
    # Vehicle categories
    LAND = "land"
    AIR = "air"
    SEA = "sea"
    FUTURISTIC = "futuristic"
    HISTORICAL = "historical"
    
    # Set dressing categories
    DECORATIVE = "decorative"
    FUNCTIONAL = "functional"
    ATMOSPHERIC = "atmospheric"
    PERIOD = "period"
    
    # SFX categories
    PRACTICAL = "practical"
    DIGITAL = "digital"
    ATMOSPHERE = "atmosphere"
    DESTRUCTION = "destruction"
    
    # Sound categories
    AMBIENT = "ambient"
    DIALOGUE = "dialogue"
    FOLEY = "foley"
    EFFECT = "effect"
    
    # Music categories
    SCORE = "score"
    SOURCE = "source"
    THEME = "theme"
    TRANSITION = "transition"


class AssetReference(BaseModel):
    """Reference to an asset with usage context."""
    asset_id: str = Field(..., description="Unique identifier of the referenced asset")
    usage_context: Dict[str, any] = Field(default_factory=dict, description="Context-specific usage data")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score for this reference")
    notes: Optional[str] = Field(None, description="Additional usage notes")


class BaseAsset(BaseModel):
    """Base asset model with common properties."""
    asset_id: str = Field(..., description="Unique identifier for the asset")
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable asset name")
    description: str = Field(..., max_length=500, description="Detailed description of the asset")
    asset_type: AssetType = Field(..., description="Type of asset")
    category: AssetCategory = Field(..., description="Category within asset type")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    metadata: Dict[str, any] = Field(default_factory=dict, description="Additional metadata")
    
    # Provenance and versioning
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="Creator identifier")
    version: int = Field(default=1, ge=1, description="Asset version number")
    
    # Usage tracking
    usage_count: int = Field(default=0, ge=0, description="Number of times used in project")
    referenced_in: List[str] = Field(default_factory=list, description="List of shot/sequence IDs")


class PropAsset(BaseAsset):
    """Prop asset with specific properties for objects used by characters."""
    asset_type: Literal[AssetType.PROP] = AssetType.PROP
    category: AssetCategory = Field(..., description="Prop category")
    
    # Physical properties
    dimensions: Optional[Dict[str, float]] = Field(None, description="Physical dimensions (l, w, h)")
    weight: Optional[float] = Field(None, ge=0, description="Weight in kg")
    material: Optional[str] = Field(None, description="Primary material")
    
    # Visual properties
    color: Optional[str] = Field(None, description="Primary color")
    texture: Optional[str] = Field(None, description="Surface texture")
    condition: str = Field(default="new", description="Condition: new, worn, damaged, antique")
    
    # Usage properties
    is_interactive: bool = Field(default=False, description="Can be interacted with by characters")
    is_weapon: bool = Field(default=False, description="Is this a weapon")
    era: Optional[str] = Field(None, description="Historical era or time period")
    
    # References
    reference_images: List[str] = Field(default_factory=list, description="Image URLs for reference")
    trigger_word: Optional[str] = Field(None, description="LoRA trigger word")


class WardrobeAsset(BaseAsset):
    """Wardrobe/clothing asset with detailed specifications."""
    asset_type: Literal[AssetType.WARDROBE] = AssetType.WARDROBE
    category: AssetCategory = Field(..., description="Wardrobe category")
    
    # Character association
    character_id: Optional[str] = Field(None, description="Associated character ID")
    character_name: Optional[str] = Field(None, description="Character wearing this")
    
    # Garment properties
    size: Optional[str] = Field(None, description="Size (XS, S, M, L, XL, etc.)")
    color: Optional[str] = Field(default=None, description="Primary color")
    pattern: Optional[str] = Field(None, description="Pattern or design")
    fabric: Optional[str] = Field(None, description="Fabric material")
    
    # Style properties
    era: Optional[str] = Field(None, description="Historical era or fashion period")
    style: str = Field(..., description="Style descriptor (casual, formal, etc.)")
    condition: str = Field(default="new", description="Garment condition")
    
    # References
    reference_images: List[str] = Field(default_factory=list, description="Reference images")
    trigger_word: Optional[str] = Field(None, description="LoRA trigger word")


class VehicleAsset(BaseAsset):
    """Vehicle asset for transportation elements."""
    asset_type: Literal[AssetType.VEHICLE] = AssetType.VEHICLE
    category: AssetCategory = Field(..., description="Vehicle category")
    
    # Vehicle properties
    make: Optional[str] = Field(None, description="Manufacturer or brand")
    model: Optional[str] = Field(None, description="Model name/number")
    year: Optional[int] = Field(None, ge=1800, le=2100, description="Manufacturing year")
    color: Optional[str] = Field(None, description="Vehicle color")
    condition: str = Field(default="good", description="Vehicle condition")
    
    # Technical properties
    fuel_type: Optional[str] = Field(None, description="Fuel type (gas, electric, etc.)")
    transmission: Optional[str] = Field(None, description="Transmission type")
    capacity: Optional[int] = Field(None, ge=1, description="Passenger capacity")
    
    # Usage properties
    is_drivable: bool = Field(default=True, description="Can be driven by characters")
    interior_visible: bool = Field(default=False, description="Interior is visible in shots")
    
    # References
    reference_images: List[str] = Field(default_factory=list, description="Reference images")
    trigger_word: Optional[str] = Field(None, description="LoRA trigger word")


class SetDressingAsset(BaseAsset):
    """Set dressing/environmental decoration assets."""
    asset_type: Literal[AssetType.SET_DRESSING] = AssetType.SET_DRESSING
    category: AssetCategory = Field(..., description="Set dressing category")
    
    # Environmental properties
    placement: str = Field(..., description="Where this is placed (wall, floor, table, etc.)")
    scale: Optional[Dict[str, float]] = Field(None, description="Scale relative to human (x, y, z)")
    
    # Visual properties
    color_scheme: List[str] = Field(default_factory=list, description="Color palette")
    style: str = Field(..., description="Style descriptor (modern, antique, etc.)")
    era: Optional[str] = Field(None, description="Historical era")
    
    # Interaction properties
    is_movable: bool = Field(default=True, description="Can be moved/repositioned")
    is_breakable: bool = Field(default=False, description="Can be broken/damaged")
    
    # References
    reference_images: List[str] = Field(default_factory=list, description="Reference images")
    trigger_word: Optional[str] = Field(None, description="LoRA trigger word")


class SFXAsset(BaseAsset):
    """Special effects asset for visual effects."""
    asset_type: Literal[AssetType.SFX] = AssetType.SFX
    category: AssetCategory = Field(..., description="SFX category")
    
    # Effect properties
    effect_type: str = Field(..., description="Type of effect (explosion, fire, etc.)")
    intensity: str = Field(..., description="Intensity level (subtle, moderate, extreme)")
    duration: Optional[float] = Field(None, ge=0, description="Duration in seconds")
    
    # Technical properties
    is_practical: bool = Field(default=False, description="Physical practical effect")
    is_digital: bool = Field(default=True, description="Digital VFX")
    complexity: str = Field(default="medium", description="Complexity level")
    
    # References
    reference_videos: List[str] = Field(default_factory=list, description="Video references")
    effect_layers: List[str] = Field(default_factory=list, description="Layer breakdown")


class SoundAsset(BaseAsset):
    """Sound effects and ambient audio assets."""
    asset_type: Literal[AssetType.SOUND] = AssetType.SOUND
    category: AssetCategory = Field(..., description="Sound category")
    
    # Audio properties
    duration: float = Field(..., ge=0, description="Duration in seconds")
    sample_rate: int = Field(default=44100, description="Audio sample rate")
    bit_depth: int = Field(default=16, description="Audio bit depth")
    channels: int = Field(default=2, description="Number of audio channels")
    
    # Sound properties
    loopable: bool = Field(default=False, description="Can be looped")
    volume: float = Field(default=1.0, ge=0, le=1, description="Default volume level")
    fade_in: float = Field(default=0.0, ge=0, description="Fade in duration")
    fade_out: float = Field(default=0.0, ge=0, description="Fade out duration")
    
    # References
    audio_file_url: Optional[str] = Field(None, description="Audio file URL")
    waveform_preview: Optional[str] = Field(None, description="Base64 encoded waveform")


class MusicAsset(BaseAsset):
    """Music and musical score assets."""
    asset_type: Literal[AssetType.MUSIC] = AssetType.MUSIC
    category: AssetCategory = Field(..., description="Music category")
    
    # Musical properties
    tempo: int = Field(..., ge=40, le=240, description="BPM tempo")
    key: Optional[str] = Field(None, description="Musical key")
    time_signature: str = Field(default="4/4", description="Time signature")
    mood: str = Field(..., description="Emotional mood description")
    
    # Technical properties
    duration: float = Field(..., ge=0, description="Duration in seconds")
    composer: Optional[str] = Field(None, description="Composer name")
    genre: Optional[str] = Field(None, description="Musical genre")
    
    # Usage properties
    is_loopable: bool = Field(default=False, description="Can be looped")
    has_stems: bool = Field(default=False, description="Has separate instrument tracks")
    
    # References
    audio_file_url: Optional[str] = Field(None, description="Audio file URL")
    sheet_music_url: Optional[str] = Field(None, description="Sheet music URL")


class AssetCollection(BaseModel):
    """Collection of assets grouped by type and category."""
    collection_id: str = Field(..., description="Unique identifier for the collection")
    name: str = Field(..., description="Collection name")
    description: str = Field(..., description="Collection description")
    
    # Organized assets
    props: List[PropAsset] = Field(default_factory=list)
    wardrobe: List[WardrobeAsset] = Field(default_factory=list)
    vehicles: List[VehicleAsset] = Field(default_factory=list)
    set_dressing: List[SetDressingAsset] = Field(default_factory=list)
    sfx: List[SFXAsset] = Field(default_factory=list)
    sounds: List[SoundAsset] = Field(default_factory=list)
    music: List[MusicAsset] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_all_assets(self) -> List[BaseAsset]:
        """Get all assets in this collection."""
        return [
            *self.props,
            *self.wardrobe,
            *self.vehicles,
            *self.set_dressing,
            *self.sfx,
            *self.sounds,
            *self.music
        ]
    
    def count_by_type(self) -> Dict[str, int]:
        """Get count of assets by type."""
        return {
            AssetType.PROP: len(self.props),
            AssetType.WARDROBE: len(self.wardrobe),
            AssetType.VEHICLE: len(self.vehicles),
            AssetType.SET_DRESSING: len(self.set_dressing),
            AssetType.SFX: len(self.sfx),
            AssetType.SOUND: len(self.sounds),
            AssetType.MUSIC: len(self.music)
        }


# Type mapping for dynamic asset creation
ASSET_TYPE_MAP = {
    AssetType.PROP: PropAsset,
    AssetType.WARDROBE: WardrobeAsset,
    AssetType.VEHICLE: VehicleAsset,
    AssetType.SET_DRESSING: SetDressingAsset,
    AssetType.SFX: SFXAsset,
    AssetType.SOUND: SoundAsset,
    AssetType.MUSIC: MusicAsset
}


def create_asset_from_dict(asset_data: dict) -> BaseAsset:
    """Factory function to create appropriate asset instance from dictionary."""
    asset_type = AssetType(asset_data.get('asset_type'))
    asset_class = ASSET_TYPE_MAP.get(asset_type, BaseAsset)
    return asset_class(**asset_data)