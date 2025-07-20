"""
Storyboard/Pre-vis Integration Models
STORY-087 Implementation

Models for integrating storyboard and pre-visualization capabilities with the
professional script breakdown system.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.models.breakdown_models import SceneBreakdown, BreakdownElement
from app.models.generative_shotlist import ShotSpecification


class StoryboardFrameStatus(str, Enum):
    """Status of storyboard frames."""
    CONCEPT = "concept"
    SKETCH = "sketch"
    DRAFT = "draft"
    FINALIZED = "finalized"
    APPROVED = "approved"
    GENERATED = "generated"


class CameraMovement(str, Enum):
    """Types of camera movements."""
    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    TRACK = "track"
    DOLLY = "dolly"
    CRANE = "crane"
    ZOOM = "zoom"
    HANDHELD = "handheld"
    STEADICAM = "steadicam"
    DRONE = "drone"


class ShotComposition(str, Enum):
    """Standard shot compositions."""
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSEUP = "closeup"
    EXTREME_CLOSEUP = "extreme_closeup"
    TWO_SHOT = "two_shot"
    OVER_SHOULDER = "over_shoulder"
    POV = "pov"
    ESTABLISHING = "establishing"
    INSERT = "insert"


class StoryboardFrame(BaseModel):
    """Individual storyboard frame with pre-vis data."""
    
    frame_id: str = Field(..., description="Unique frame identifier")
    scene_id: str = Field(..., description="Parent scene ID")
    shot_number: int = Field(..., description="Shot number in sequence")
    frame_number: int = Field(..., description="Frame number within shot")
    
    # Visual description
    description: str = Field(..., description="Visual description of the frame")
    visual_notes: str = Field(default="", description="Director's visual notes")
    
    # Technical specs
    camera_angle: str = Field(default="", description="Camera angle description")
    camera_movement: CameraMovement = Field(default=CameraMovement.STATIC)
    composition: ShotComposition = Field(default=ShotComposition.MEDIUM)
    focal_length: float = Field(default=35.0, description="Camera focal length in mm")
    
    # Positioning
    position: Dict[str, float] = Field(default_factory=dict, description="Frame positioning data")
    
    # Status
    status: StoryboardFrameStatus = Field(default=StoryboardFrameStatus.CONCEPT)
    
    # Pre-vis generation
    previs_path: Optional[str] = Field(None, description="Path to pre-vis file")
    thumbnail_path: Optional[str] = Field(None, description="Thumbnail image path")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    # Generation metadata
    generation_params: Dict[str, Any] = Field(default_factory=dict, description="Generation parameters")
    model_version: str = Field(default="", description="AI model version used")


class StoryboardShot(BaseModel):
    """Complete storyboard shot with multiple frames."""
    
    shot_id: str = Field(..., description="Unique shot identifier")
    scene_id: str = Field(..., description="Parent scene ID")
    shot_number: int = Field(..., description="Shot number")
    
    # Shot specifications
    shot_type: str = Field(default="", description="Type of shot")
    duration: float = Field(default=3.0, description="Shot duration in seconds")
    
    # Technical specs
    camera_setup: Dict[str, Any] = Field(default_factory=dict, description="Camera setup details")
    lighting_setup: Dict[str, Any] = Field(default_factory=dict, description="Lighting setup")
    audio_notes: str = Field(default="", description="Audio requirements")
    
    # Storyboard frames
    frames: List[StoryboardFrame] = Field(default_factory=list)
    
    # Pre-vis data
    previs_sequence: Dict[str, Any] = Field(default_factory=dict, description="Pre-vis sequence data")
    
    # Linked elements
    linked_elements: List[str] = Field(default_factory=list, description="Linked breakdown elements")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_frame(self, frame: StoryboardFrame) -> None:
        """Add a frame to this shot."""
        self.frames.append(frame)
        self.frames.sort(key=lambda f: f.frame_number)
    
    def get_frame_count(self) -> int:
        """Get total number of frames in shot."""
        return len(self.frames)
    
    def get_duration_estimate(self) -> float:
        """Get estimated duration based on frames."""
        if not self.frames:
            return self.duration
        return max(1.0, len(self.frames) * 0.5)  # 0.5s per frame estimate


class StoryboardSequence(BaseModel):
    """Complete storyboard sequence for a scene."""
    
    sequence_id: str = Field(..., description="Unique sequence identifier")
    scene_id: str = Field(..., description="Parent scene ID")
    
    # Sequence metadata
    sequence_name: str = Field(default="", description="Sequence name")
    description: str = Field(default="", description="Sequence description")
    
    # Shots
    shots: List[StoryboardShot] = Field(default_factory=list)
    
    # Scene breakdown integration
    scene_breakdown: Optional[SceneBreakdown] = Field(None, description="Associated scene breakdown")
    
    # Pre-vis generation
    previs_sequence_path: Optional[str] = Field(None, description="Path to complete pre-vis sequence")
    
    # Technical specs
    total_duration: float = Field(default=0.0, description="Total sequence duration")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio")
    resolution: str = Field(default="1920x1080", description="Resolution")
    frame_rate: float = Field(default=24.0, description="Frame rate")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    def add_shot(self, shot: StoryboardShot) -> None:
        """Add a shot to this sequence."""
        self.shots.append(shot)
        self.shots.sort(key=lambda s: s.shot_number)
        self._recalculate_duration()
    
    def _recalculate_duration(self) -> None:
        """Recalculate total sequence duration."""
        self.total_duration = sum(shot.get_duration_estimate() for shot in self.shots)
    
    def get_shot_count(self) -> int:
        """Get total number of shots."""
        return len(self.shots)
    
    def get_frame_count(self) -> int:
        """Get total number of frames."""
        return sum(shot.get_frame_count() for shot in self.shots)


class PrevisGenerationRequest(BaseModel):
    """Request for generating pre-visualization."""
    
    sequence_id: str = Field(..., description="Sequence to generate pre-vis for")
    scene_id: str = Field(..., description="Scene ID")
    
    # Generation parameters
    style: str = Field(default="realistic", description="Visual style")
    quality: str = Field(default="standard", description="Generation quality")
    resolution: str = Field(default="1920x1080", description="Output resolution")
    frame_rate: float = Field(default=24.0, description="Frame rate")
    
    # Camera settings
    camera_preset: str = Field(default="standard", description="Camera preset")
    lighting_preset: str = Field(default="natural", description="Lighting preset")
    
    # Asset integration
    include_assets: bool = Field(default=True, description="Include linked assets")
    asset_overrides: Dict[str, Any] = Field(default_factory=dict, description="Asset override settings")
    
    # Processing options
    batch_size: int = Field(default=1, description="Processing batch size")
    priority: int = Field(default=5, description="Generation priority")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")


class PrevisGenerationResult(BaseModel):
    """Result of pre-vis generation."""
    
    result_id: str = Field(..., description="Result identifier")
    sequence_id: str = Field(..., description="Sequence ID")
    
    # Generation status
    status: str = Field(default="pending", description="Generation status")
    progress: float = Field(default=0.0, description="Generation progress")
    
    # Output files
    sequence_path: Optional[str] = Field(None, description="Path to generated sequence")
    frame_paths: List[str] = Field(default_factory=list, description="Individual frame paths")
    thumbnail_paths: List[str] = Field(default_factory=list, description="Thumbnail paths")
    
    # Technical details
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Generation metadata")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    
    def is_complete(self) -> bool:
        """Check if generation is complete."""
        return self.status in ["completed", "failed"]


class StoryboardTemplate(BaseModel):
    """Template for storyboard creation."""
    
    template_id: str = Field(..., description="Template identifier")
    template_name: str = Field(..., description="Template name")
    description: str = Field(default="", description="Template description")
    
    # Template configuration
    default_frames_per_shot: int = Field(default=3, description="Default frames per shot")
    default_shot_duration: float = Field(default=3.0, description="Default shot duration")
    
    # Camera presets
    camera_presets: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Camera presets")
    composition_templates: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Composition templates")
    
    # Style settings
    visual_style: str = Field(default="realistic", description="Default visual style")
    color_palette: List[str] = Field(default_factory=list, description="Default color palette")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def apply_template(self, sequence: StoryboardSequence) -> None:
        """Apply template settings to sequence."""
        for shot in sequence.shots:
            if not shot.camera_setup:
                shot.camera_setup.update(self.camera_presets.get("default", {}))
            
            # Set default duration if not specified
            if shot.duration == 3.0 and shot.get_frame_count() == 0:
                shot.duration = self.default_shot_duration