"""
Project schema definitions following the BMAD structure as API contract.
Any deviation from these schemas is a breaking change.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator


class AssetType(str, Enum):
    """Asset types aligned with generative pipeline"""

    CHARACTERS = "Characters"
    STYLES = "Styles"
    LOCATIONS = "Locations"
    MUSIC = "Music"
    SCRIPTS = "Scripts"


class CreativeDocType(str, Enum):
    """Creative documents that guide the pipeline"""

    TREATMENTS = "Treatments"
    SCRIPTS = "Scripts"
    SHOT_LISTS = "Shot_Lists"
    CANVAS = "Canvas"


class QualityLevel(str, Enum):
    """Quality levels for generation pipeline"""

    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"


class NarrativeStructure(str, Enum):
    """Supported narrative structures"""

    THREE_ACT = "three-act"
    HERO_JOURNEY = "hero-journey"
    BEAT_SHEET = "beat-sheet"
    STORY_CIRCLE = "story-circle"


class LoRATrainingStatus(str, Enum):
    """Character LoRA training status"""

    UNTRAINED = "untrained"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


class AssetReference(BaseModel):
    """Base asset reference model"""

    id: str = Field(description="Asset UUID")
    name: str = Field(description="Human-readable name")
    type: str = Field(description="Asset type")
    path: str = Field(description="Relative path from project root")
    metadata: dict[str, Any] | None = Field(default=None)


class CharacterAsset(AssetReference):
    """Character asset with LoRA support"""

    assetId: str = Field(description="Character UUID")
    assetType: str = Field(default="Character")
    description: str = Field(description="Character appearance/personality")
    triggerWord: str | None = Field(default=None, description="LoRA activation token")
    baseFaceImagePath: str | None = Field(default=None, description="Canonical face image")
    loraModelPath: str | None = Field(default=None, description="Trained LoRA file")
    loraTrainingStatus: LoRATrainingStatus = Field(
        default=LoRATrainingStatus.UNTRAINED, description="LoRA training status"
    )
    variations: dict[str, str] = Field(
        default_factory=dict, description="variation_type -> image_path mapping"
    )
    usage: list[str] = Field(default_factory=list, description="Shot IDs where character is used")


class SceneInfo(BaseModel):
    """Scene information"""

    id: str
    name: str
    order: int
    shotIds: list[str] = Field(default_factory=list)


class ChapterInfo(BaseModel):
    """Chapter information"""

    id: str
    name: str
    order: int
    scenes: list[str] = Field(description="Scene IDs")


class EmotionalBeat(BaseModel):
    """Emotional beat for narrative pacing"""

    beat: str = Field(description="Beat name (e.g., 'Catalyst', 'All Is Lost')")
    sceneId: str
    keywords: list[str] = Field(description="Mood keywords for prompting")


class NarrativeConfig(BaseModel):
    """Narrative structure configuration"""

    structure: NarrativeStructure
    chapters: list[ChapterInfo]
    emotionalBeats: list[EmotionalBeat] | None = None


class ProjectSettings(BaseModel):
    """Project-wide settings"""

    fps: int = Field(default=24, description="Frames per second")
    resolution: tuple[int, int] = Field(default=(1920, 1080))
    aspectRatio: str = Field(default="16:9")
    defaultQuality: QualityLevel = Field(default=QualityLevel.STANDARD)
    outputFormat: str = Field(default="mp4")


class CanvasViewport(BaseModel):
    """Canvas viewport state"""

    x: float
    y: float
    zoom: float


class CanvasState(BaseModel):
    """Canvas node graph state"""

    nodes: list[Any] = Field(default_factory=list)
    edges: list[Any] = Field(default_factory=list)
    viewport: CanvasViewport


class GitConfig(BaseModel):
    """Git repository configuration"""

    initialized: bool = Field(default=False)
    lfs_enabled: bool = Field(default=False)
    remote: str | None = None


class ProjectMetadata(BaseModel):
    """Project metadata"""

    director: str | None = None
    genre: str | None = None
    style: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    gitCommit: str | None = None
    lastExport: datetime | None = None
    totalFrames: int | None = None
    activeTakes: dict[str, str] = Field(
        default_factory=dict, description="nodeId -> takeId mapping"
    )


class ProjectManifest(BaseModel):
    """
    Project manifest schema - single source of truth.
    This is the API contract for project structure.
    """

    id: str = Field(description="Project UUID")
    name: str = Field(description="Human-readable project name")
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = Field(default="1.0.0", description="Schema version")
    quality: QualityLevel = Field(default=QualityLevel.STANDARD)
    takes_system_enabled: bool = Field(default=True)

    narrative: NarrativeConfig

    assets: dict[str, list[Any]] = Field(
        default_factory=lambda: {"characters": [], "styles": [], "locations": [], "music": []}
    )

    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    canvas: CanvasState | None = None
    metadata: ProjectMetadata = Field(default_factory=ProjectMetadata)
    git: GitConfig = Field(default_factory=GitConfig)

    @validator("modified", pre=True, always=True)
    def update_modified(cls, v):
        return datetime.now(timezone.utc)


class ProjectCreate(BaseModel):
    """Project creation request"""

    name: str = Field(min_length=1, max_length=255)
    narrative_structure: NarrativeStructure = Field(default=NarrativeStructure.THREE_ACT)
    quality: QualityLevel = Field(default=QualityLevel.STANDARD)
    director: str | None = None
    description: str | None = None


class ProjectUpdate(BaseModel):
    """Project update request"""

    name: str | None = Field(min_length=1, max_length=255)
    quality: QualityLevel | None = None
    description: str | None = None
    tags: list[str] | None = None


class ProjectStructureValidation(BaseModel):
    """Project structure validation result"""

    valid: bool
    missing_directories: list[str] = Field(default_factory=list)
    unexpected_directories: list[str] = Field(default_factory=list)
    git_initialized: bool
    git_lfs_enabled: bool
    project_json_valid: bool
    errors: list[str] = Field(default_factory=list)
