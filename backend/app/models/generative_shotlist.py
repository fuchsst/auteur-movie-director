"""
Structured GenerativeShotList Schema
STORY-084 Implementation

Defines the JSON schema for structured shot lists that integrate with the expanded asset system
and provide a comprehensive foundation for generative filmmaking workflows.
"""

from typing import Dict, List, Optional, Union, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models.asset_types import AssetReference, AssetType


class ShotType(str, Enum):
    """Enumeration of standard shot types used in filmmaking."""
    ESTABLISHING = "establishing"
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSEUP = "closeup"
    EXTREME_CLOSEUP = "extreme_closeup"
    OVER_SHOULDER = "over_shoulder"
    TWO_SHOT = "two_shot"
    POV = "pov"
    INSERT = "insert"
    CUTAWAY = "cutaway"
    MASTER = "master"
    COVERAGE = "coverage"


class CameraMovement(str, Enum):
    """Enumeration of camera movement types."""
    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    DOLLY = "dolly"
    TRUCK = "truck"
    PEDESTAL = "pedestal"
    ZOOM = "zoom"
    RACK_FOCUS = "rack_focus"
    HANDHELD = "handheld"
    STABILIZED = "stabilized"
    CRANE = "crane"
    DRONE = "drone"
    GIMBAL = "gimbal"


class ShotAngle(str, Enum):
    """Enumeration of camera angles."""
    EYE_LEVEL = "eye_level"
    HIGH_ANGLE = "high_angle"
    LOW_ANGLE = "low_angle"
    BIRDSEYE = "birdseye"
    DUTCH = "dutch"
    PROFILE = "profile"
    BACK = "back"
    FRONT = "front"


class ShotDuration(str, Enum):
    """Standard shot duration categories."""
    SUBLIMINAL = "subliminal"  # < 1 second
    QUICK = "quick"  # 1-3 seconds
    STANDARD = "standard"  # 3-10 seconds
    LONG = "long"  # 10-30 seconds
    EXTENDED = "extended"  # 30+ seconds


class LightingSetup(str, Enum):
    """Standard lighting setups."""
    NATURAL = "natural"
    KEY_LIGHT = "key_light"
    THREE_POINT = "three_point"
    FOUR_POINT = "four_point"
    RIM_LIGHT = "rim_light"
    BACKLIGHT = "backlight"
    SIDELIGHT = "sidelight"
    TOP_LIGHT = "top_light"
    UNDERLIGHT = "underlight"
    PRACTICAL = "practical"
    NEGATIVE_FILL = "negative_fill"


class ColorGradeStyle(str, Enum):
    """Color grading styles."""
    NATURAL = "natural"
    WARM = "warm"
    COOL = "cool"
    HIGH_CONTRAST = "high_contrast"
    LOW_CONTRAST = "low_contrast"
    DESATURATED = "desaturated"
    VIBRANT = "vibrant"
    TEAL_ORANGE = "teal_orange"
    MONOCHROME = "monochrome"
    VINTAGE = "vintage"
    CYBERPUNK = "cyberpunk"
    NOIR = "noir"


class AudioDesign(str, Enum):
    """Audio design approaches."""
    NATURALISTIC = "naturalistic"
    STYLIZED = "stylized"
    EXPRESSIONISTIC = "expressionistic"
    MINIMAL = "minimal"
    LAYERED = "layered"
    ATMOSPHERIC = "atmospheric"
    TENSION_BUILDING = "tension_building"
    EMOTIONAL = "emotional"
    ACTION_DRIVEN = "action_driven"
    DIALOGUE_FOCUSED = "dialogue_focused"


class GenerativePrompt(BaseModel):
    """A structured prompt for AI generation systems."""
    prompt_text: str = Field(..., description="The actual prompt text")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt to avoid")
    style_references: List[str] = Field(default_factory=list, description="Style reference URLs or descriptions")
    camera_settings: Dict[str, Any] = Field(default_factory=dict, description="Camera-specific settings")
    lighting_notes: Optional[str] = Field(None, description="Specific lighting instructions")
    composition_guidelines: Optional[str] = Field(None, description="Composition and framing notes")


class ShotRequirements(BaseModel):
    """Technical and creative requirements for a shot."""
    
    # Technical requirements
    resolution: str = Field(default="1920x1080", description="Target resolution")
    aspect_ratio: str = Field(default="16:9", description="Aspect ratio")
    frame_rate: int = Field(default=24, description="Frame rate")
    codec: str = Field(default="h264", description="Video codec")
    quality_preset: str = Field(default="high", description="Quality preset")
    
    # Creative requirements
    mood: str = Field(..., description="Emotional mood of the shot")
    tone: str = Field(..., description="Overall tone and atmosphere")
    visual_style: str = Field(..., description="Visual style description")
    
    # Technical constraints
    max_file_size: Optional[int] = Field(None, description="Maximum file size in bytes")
    max_duration: Optional[float] = Field(None, description="Maximum duration in seconds")
    render_priority: int = Field(default=5, ge=1, le=10, description="Render priority (1-10)")


class ShotAssets(BaseModel):
    """Assets associated with a shot."""
    
    # Primary assets
    characters: List[AssetReference] = Field(default_factory=list, description="Character assets")
    props: List[AssetReference] = Field(default_factory=list, description="Prop assets")
    wardrobe: List[AssetReference] = Field(default_factory=list, description="Wardrobe assets")
    vehicles: List[AssetReference] = Field(default_factory=list, description="Vehicle assets")
    set_dressing: List[AssetReference] = Field(default_factory=list, description="Set dressing assets")
    
    # Environmental assets
    locations: List[AssetReference] = Field(default_factory=list, description="Location assets")
    sfx: List[AssetReference] = Field(default_factory=list, description="SFX assets")
    sounds: List[AssetReference] = Field(default_factory=list, description="Sound assets")
    music: List[AssetReference] = Field(default_factory=list, description="Music assets")
    
    # Style and effects
    styles: List[AssetReference] = Field(default_factory=list, description="Visual style assets")
    lighting: List[AssetReference] = Field(default_factory=list, description="Lighting setup assets")


class ShotTiming(BaseModel):
    """Timing information for a shot."""
    
    estimated_duration: float = Field(..., ge=0.1, description="Estimated duration in seconds")
    target_duration: Optional[float] = Field(None, ge=0.1, description="Target duration")
    min_duration: Optional[float] = Field(None, ge=0.1, description="Minimum acceptable duration")
    max_duration: Optional[float] = Field(None, ge=0.1, description="Maximum acceptable duration")
    
    # Timing relationships
    follows_shot: Optional[str] = Field(None, description="ID of preceding shot")
    precedes_shot: Optional[str] = Field(None, description="ID of following shot")
    can_be_parallel: bool = Field(default=False, description="Can be generated in parallel")


class ShotComposition(BaseModel):
    """Composition details for a shot."""
    
    # Framing
    shot_type: ShotType = Field(..., description="Primary shot type")
    shot_angle: ShotAngle = Field(..., description="Camera angle")
    camera_movement: CameraMovement = Field(..., description="Camera movement type")
    
    # Composition rules
    rule_of_thirds: bool = Field(default=True, description="Use rule of thirds")
    headroom: str = Field(default="standard", description="Headroom amount")
    lead_room: str = Field(default="standard", description="Lead room amount")
    
    # Focus and depth
    depth_of_field: str = Field(default="standard", description="Depth of field")
    focal_length: Optional[float] = Field(None, description="Focal length in mm")
    focus_distance: Optional[float] = Field(None, description="Focus distance")
    
    # Movement details
    movement_speed: str = Field(default="normal", description="Movement speed")
    movement_direction: Optional[str] = Field(None, description="Movement direction")
    movement_duration: Optional[float] = Field(None, description="Movement duration")


class ShotLighting(BaseModel):
    """Lighting design for a shot."""
    
    # Primary setup
    lighting_setup: LightingSetup = Field(..., description="Primary lighting setup")
    key_light_intensity: float = Field(default=1.0, ge=0.0, le=2.0, description="Key light intensity")
    fill_light_ratio: float = Field(default=0.5, ge=0.0, le=2.0, description="Fill light ratio")
    back_light_intensity: float = Field(default=0.3, ge=0.0, le=2.0, description="Back light intensity")
    
    # Color and mood
    color_temperature: int = Field(default=5600, description="Color temperature in Kelvin")
    color_grade_style: ColorGradeStyle = Field(..., description="Color grading style")
    contrast_level: str = Field(default="standard", description="Contrast level")
    
    # Special effects
    practical_lights: List[str] = Field(default_factory=list, description="Practical light sources")
    special_effects: List[str] = Field(default_factory=list, description="Special lighting effects")


class ShotAudio(BaseModel):
    """Audio design for a shot."""
    
    # Design approach
    audio_design: AudioDesign = Field(..., description="Audio design approach")
    primary_source: str = Field(..., description="Primary audio source")
    
    # Elements
    dialogue: bool = Field(default=False, description="Contains dialogue")
    music: bool = Field(default=False, description="Contains music")
    ambient: bool = Field(default=True, description="Contains ambient sound")
    foley: bool = Field(default=False, description="Contains foley effects")
    sfx: bool = Field(default=False, description="Contains sound effects")
    
    # Technical
    audio_channels: int = Field(default=2, description="Number of audio channels")
    sample_rate: int = Field(default=44100, description="Audio sample rate")
    bit_depth: int = Field(default=16, description="Audio bit depth")


class ShotSpecification(BaseModel):
    """Simplified shot specification for storyboard integration."""
    
    shot_id: str = Field(..., description="Unique identifier for the shot")
    shot_type: ShotType = Field(..., description="Type of shot")
    camera_angle: ShotAngle = Field(..., description="Camera angle")
    camera_movement: CameraMovement = Field(..., description="Camera movement")
    duration: float = Field(..., description="Shot duration in seconds")
    description: str = Field(..., description="Shot description")
    key_characters: List[str] = Field(default_factory=list, description="Key characters in shot")
    key_props: List[str] = Field(default_factory=list, description="Key props in shot")
    location: Optional[str] = Field(None, description="Location identifier")
    mood: str = Field(..., description="Emotional mood")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        use_enum_values = True


class GenerativeShot(BaseModel):
    """A single shot with comprehensive generative specifications."""
    
    # Core identification
    shot_id: str = Field(..., description="Unique identifier for the shot")
    sequence_id: Optional[str] = Field(None, description="Parent sequence ID")
    scene_id: Optional[str] = Field(None, description="Parent scene ID")
    
    # Shot details
    shot_number: str = Field(..., description="Shot number (e.g., '1A', '42B')")
    shot_type: ShotType = Field(..., description="Type of shot")
    shot_description: str = Field(..., description="Detailed description of the shot")
    shot_synopsis: str = Field(..., description="Brief narrative synopsis")
    
    # Technical specifications
    composition: ShotComposition = Field(..., description="Composition details")
    lighting: ShotLighting = Field(..., description="Lighting design")
    audio: ShotAudio = Field(..., description="Audio design")
    requirements: ShotRequirements = Field(..., description="Technical requirements")
    
    # Assets and resources
    assets: ShotAssets = Field(default_factory=ShotAssets, description="Associated assets")
    
    # Generative AI
    generative_prompt: GenerativePrompt = Field(..., description="AI generation prompt")
    
    # Timing
    timing: ShotTiming = Field(..., description="Timing information")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")
    version: int = Field(default=1, ge=1, description="Shot version")
    
    # Status and workflow
    status: str = Field(default="draft", description="Current status")
    approval_notes: Optional[str] = Field(None, description="Review notes")
    render_priority: int = Field(default=5, ge=1, le=10, description="Render priority")
    
    # Quality and validation
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality assessment")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")


class SequenceStructure(BaseModel):
    """Structure for organizing shots into sequences."""
    
    sequence_id: str = Field(..., description="Unique sequence identifier")
    sequence_name: str = Field(..., description="Human-readable sequence name")
    sequence_description: str = Field(..., description="Sequence description")
    
    # Narrative context
    act: Optional[str] = Field(None, description="Act number or identifier")
    chapter: Optional[str] = Field(None, description="Chapter identifier")
    scene: Optional[str] = Field(None, description="Scene identifier")
    
    # Shot organization
    shots: List[GenerativeShot] = Field(default_factory=list, description="Shots in sequence")
    shot_order: List[str] = Field(default_factory=list, description="Ordered list of shot IDs")
    
    # Technical specs
    total_duration: float = Field(default=0.0, description="Total sequence duration")
    
    def calculate_total_duration(self) -> None:
        """Calculate total duration from shots."""
        self.total_duration = sum(shot.timing.estimated_duration for shot in self.shots)
    complexity_level: str = Field(default="medium", description="Overall complexity")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class GenerativeShotList(BaseModel):
    """Complete structured shot list for generative filmmaking."""
    
    # Project identification
    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name")
    project_version: str = Field(default="1.0.0", description="Project version")
    
    # Story structure
    story_structure: Dict[str, Any] = Field(default_factory=dict, description="Story structure metadata")
    
    # Shot organization
    sequences: List[SequenceStructure] = Field(default_factory=list, description="Shot sequences")
    standalone_shots: List[GenerativeShot] = Field(default_factory=list, description="Standalone shots")
    
    # Asset references
    asset_registry: Dict[str, AssetReference] = Field(default_factory=dict, description="Referenced assets")
    
    # Technical specifications
    aspect_ratio: str = Field(default="16:9", description="Project aspect ratio")
    resolution: str = Field(default="1920x1080", description="Project resolution")
    frame_rate: int = Field(default=24, description="Project frame rate")
    color_space: str = Field(default="Rec.709", description="Color space")
    
    # Generation settings
    quality_preset: str = Field(default="standard", description="Quality preset")
    render_engine: str = Field(default="comfyui", description="Render engine")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    # Statistics
    total_shots: int = Field(default=0, description="Total number of shots")
    total_duration: float = Field(default=0.0, description="Total duration in seconds")
    total_sequences: int = Field(default=0, description="Total number of sequences")
    
    # Validation
    is_valid: bool = Field(default=True, description="Overall validation status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    
    def calculate_totals(self) -> None:
        """Calculate total statistics."""
        self.total_shots = len(self.standalone_shots) + sum(len(seq.shots) for seq in self.sequences)
        self.total_duration = sum(
            shot.timing.estimated_duration 
            for seq in self.sequences 
            for shot in seq.shots
        ) + sum(
            shot.timing.estimated_duration 
            for shot in self.standalone_shots
        )
        self.total_sequences = len(self.sequences)
    
    def validate_shot_list(self) -> bool:
        """Validate the complete shot list."""
        errors = []
        
        # Check for duplicate shot IDs
        shot_ids = []
        for seq in self.sequences:
            shot_ids.extend([shot.shot_id for shot in seq.shots])
        shot_ids.extend([shot.shot_id for shot in self.standalone_shots])
        
        if len(shot_ids) != len(set(shot_ids)):
            errors.append("Duplicate shot IDs found")
        
        # Check timing consistency
        for seq in self.sequences:
            for shot in seq.shots:
                if shot.timing.estimated_duration <= 0:
                    errors.append(f"Invalid duration for shot {shot.shot_id}")
        
        self.validation_errors = errors
        self.is_valid = len(errors) == 0
        return self.is_valid
    
    def get_shot_by_id(self, shot_id: str) -> Optional[GenerativeShot]:
        """Get a shot by its ID."""
        for seq in self.sequences:
            for shot in seq.shots:
                if shot.shot_id == shot_id:
                    return shot
        
        for shot in self.standalone_shots:
            if shot.shot_id == shot_id:
                return shot
        
        return None
    
    def get_sequence_by_id(self, sequence_id: str) -> Optional[SequenceStructure]:
        """Get a sequence by its ID."""
        for seq in self.sequences:
            if seq.sequence_id == sequence_id:
                return seq
        return None
    
    def export_to_json(self) -> str:
        """Export shot list to JSON format."""
        return self.model_dump_json(indent=2, exclude_none=True)
    
    def export_to_csv(self) -> str:
        """Export shot list to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "shot_id", "sequence_id", "shot_number", "shot_type", 
            "description", "duration", "status", "priority"
        ])
        
        # Write shots
        for seq in self.sequences:
            for shot in seq.shots:
                writer.writerow([
                    shot.shot_id,
                    seq.sequence_id,
                    shot.shot_number,
                    shot.shot_type.value,
                    shot.shot_description,
                    shot.timing.estimated_duration,
                    shot.status,
                    shot.render_priority
                ])
        
        for shot in self.standalone_shots:
            writer.writerow([
                shot.shot_id,
                "",
                shot.shot_number,
                shot.shot_type.value,
                shot.shot_description,
                shot.timing.estimated_duration,
                shot.status,
                shot.render_priority
            ])
        
        return output.getvalue()


class ShotListTemplate(BaseModel):
    """Template for creating shot lists from story structures."""
    
    template_id: str = Field(..., description="Template identifier")
    template_name: str = Field(..., description="Template name")
    template_description: str = Field(..., description="Template description")
    
    # Story structure mapping
    story_structure_type: str = Field(..., description="Type of story structure")
    act_breakdown: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="Act-based shot breakdown")
    
    # Default settings
    default_settings: Dict[str, Any] = Field(default_factory=dict, description="Default shot settings")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    def apply_template(self, story_data: Dict[str, any]) -> GenerativeShotList:
        """Apply template to story data to generate shot list."""
        shot_list = GenerativeShotList(
            project_id=story_data.get("project_id", "unknown"),
            project_name=story_data.get("title", "Untitled Project"),
            story_structure=story_data
        )
        
        # Generate shots based on template and story structure
        # This would be implemented based on specific templates
        # For now, return empty structure
        return shot_list


# Factory functions for creating shot lists
def create_shot_list_from_structure(
    project_id: str,
    project_name: str,
    story_structure: Dict[str, any]
) -> GenerativeShotList:
    """Create a shot list from story structure data."""
    return GenerativeShotList(
        project_id=project_id,
        project_name=project_name,
        story_structure=story_structure
    )


def create_shot_list_from_script(
    project_id: str,
    script_data: Dict[str, any]
) -> GenerativeShotList:
    """Create a shot list from parsed script data."""
    shot_list = GenerativeShotList(
        project_id=project_id,
        project_name=script_data.get("title", "Untitled Script"),
        story_structure=script_data
    )
    
    # Parse script scenes into shots
    # This would be implemented based on script parsing
    return shot_list


def validate_shot_list_json(shot_list_json: str) -> bool:
    """Validate a shot list JSON string."""
    try:
        shot_list = GenerativeShotList.model_validate_json(shot_list_json)
        return shot_list.validate_shot_list()
    except Exception:
        return False