"""
Scene Breakdown Visualization Schemas
====================================

Pydantic models for scene-by-scene breakdown visualization system.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SceneBeatType(str, Enum):
    """Types of story beats that can occur in scenes."""
    OPENING = "opening"
    INCITING_INCIDENT = "inciting_incident"
    FIRST_ACT_TURN = "first_act_turn"
    MIDPOINT = "midpoint"
    SECOND_ACT_TURN = "second_act_turn"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    SETUP = "setup"
    CONFRONTATION = "confrontation"
    REVERSAL = "reversal"
    REVELATION = "revelation"


class SceneStatus(str, Enum):
    """Status of scene breakdown completion."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    REVIEW = "review"
    APPROVED = "approved"


class SceneType(str, Enum):
    """Types of scenes based on function."""
    ACTION = "action"
    DIALOGUE = "dialogue"
    TRANSITION = "transition"
    MONTAGE = "montage"
    FLASHBACK = "flashback"
    DREAM = "dream"
    INTROSPECTION = "introspection"


class SceneAsset(BaseModel):
    """Asset assigned to a scene."""
    asset_id: str = Field(..., description="Unique asset identifier")
    asset_type: str = Field(..., description="Type of asset (character, prop, location, etc.)")
    asset_name: str = Field(..., description="Human-readable asset name")
    thumbnail_url: Optional[str] = Field(None, description="URL to asset thumbnail")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Asset-specific properties")
    quantity: int = Field(default=1, description="Quantity of this asset needed")


class SceneCharacter(BaseModel):
    """Character present in a scene."""
    character_id: str = Field(..., description="Unique character identifier")
    character_name: str = Field(..., description="Character name")
    role_in_scene: str = Field(..., description="Character's role/purpose in this scene")
    dialogue_lines: int = Field(default=0, description="Number of dialogue lines")
    screen_time: float = Field(default=0.0, description="Estimated screen time in minutes")
    emotions: List[str] = Field(default_factory=list, description="Character emotions in this scene")
    objectives: List[str] = Field(default_factory=list, description="Character objectives in this scene")


class StoryBeat(BaseModel):
    """Story beat within a scene."""
    beat_id: str = Field(..., description="Unique beat identifier")
    beat_type: SceneBeatType = Field(..., description="Type of story beat")
    description: str = Field(..., description="Beat description")
    timestamp: Optional[float] = Field(None, description="Timestamp in scene (minutes)")
    duration: Optional[float] = Field(None, description="Beat duration (minutes)")
    importance: int = Field(default=1, ge=1, le=5, description="Beat importance 1-5")
    connects_to: List[str] = Field(default_factory=list, description="Connected beats in other scenes")


class SceneBreakdown(BaseModel):
    """Complete scene breakdown for visualization."""
    scene_id: str = Field(..., description="Unique scene identifier")
    project_id: str = Field(..., description="Parent project identifier")
    act_number: int = Field(..., ge=1, le=3, description="Act number (1-3)")
    chapter_number: Optional[int] = Field(None, description="Chapter number within act")
    scene_number: int = Field(..., description="Scene number within chapter/act")
    
    # Core scene information
    title: str = Field(..., description="Scene title")
    description: str = Field(..., description="Scene description/synopsis")
    scene_type: SceneType = Field(..., description="Type of scene")
    location: str = Field(..., description="Primary location")
    time_of_day: str = Field(..., description="Time of day")
    duration_minutes: float = Field(..., description="Estimated scene duration")
    
    # Visual breakdown
    slug_line: str = Field(..., description="Standard screenplay slug line")
    synopsis: str = Field(..., description="Brief scene synopsis")
    script_notes: str = Field(default="", description="Director/screenwriter notes")
    
    # Status tracking
    status: SceneStatus = Field(default=SceneStatus.DRAFT)
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Relationships
    characters: List[SceneCharacter] = Field(default_factory=list)
    assets: List[SceneAsset] = Field(default_factory=list)
    story_beats: List[StoryBeat] = Field(default_factory=list)
    
    # Story analysis
    story_circle_position: Optional[int] = Field(None, ge=1, le=8, description="Dan Harmon's story circle position")
    conflict_level: int = Field(default=1, ge=1, le=5, description="Scene conflict intensity")
    stakes_level: int = Field(default=1, ge=1, le=5, description="Scene stakes level")
    
    # Visual and technical
    color_palette: List[str] = Field(default_factory=list, description="Scene color palette")
    mood_tags: List[str] = Field(default_factory=list, description="Mood descriptors")
    camera_angles: List[str] = Field(default_factory=list, description="Key camera angles")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)
    
    # Canvas positioning for visualization
    canvas_position: Optional[Dict[str, float]] = Field(None, description="x,y coordinates for canvas")
    connections: List[str] = Field(default_factory=list, description="Connected scene IDs")


class SceneReorderRequest(BaseModel):
    """Request to reorder scenes."""
    scene_id: str = Field(..., description="Scene to move")
    new_position: int = Field(..., description="New position index")
    target_act: Optional[int] = Field(None, description="Target act if moving between acts")
    target_chapter: Optional[int] = Field(None, description="Target chapter if moving")


class SceneBulkUpdate(BaseModel):
    """Bulk update request for multiple scenes."""
    scene_ids: List[str] = Field(..., description="Scenes to update")
    updates: Dict[str, Any] = Field(..., description="Fields to update")


class SceneAnalysis(BaseModel):
    """Analysis results for a scene."""
    scene_id: str = Field(..., description="Scene identifier")
    pacing_score: float = Field(..., ge=0.0, le=100.0, description="Scene pacing score")
    character_balance: Dict[str, float] = Field(..., description="Character screen time distribution")
    story_progression: float = Field(..., ge=0.0, le=100.0, description="Story progression score")
    missing_elements: List[str] = Field(default_factory=list, description="Missing required elements")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class SceneSummary(BaseModel):
    """Summary information for scene grid view."""
    scene_id: str
    title: str
    scene_number: int
    act_number: int
    chapter_number: Optional[int]
    duration_minutes: float
    status: SceneStatus
    completion_percentage: float
    character_count: int
    asset_count: int
    story_beat_count: int
    thumbnail_url: Optional[str]
    color_indicator: str