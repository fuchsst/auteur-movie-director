"""
Digital Table Read Models
STORY-088 Implementation

Models for AI-powered script analysis and creative bible generation using Dan Harmon's Story Circle.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, ConfigDict, field_validator
from datetime import datetime
import re


class StoryCircleBeat(str, Enum):
    """Dan Harmon's Story Circle beats."""
    YOU = "you"  # Character in zone of comfort
    NEED = "need"  # Character wants something
    GO = "go"  # Character enters unfamiliar situation
    SEARCH = "search"  # Character adapts to new situation
    FIND = "find"  # Character finds what they wanted
    TAKE = "take"  # Character pays a heavy price
    RETURN = "return"  # Character returns to familiar situation
    CHANGE = "change"  # Character fundamentally changed


class CharacterArchetype(str, Enum):
    """Common character archetypes for analysis."""
    HERO = "hero"
    MENTOR = "mentor"
    ALLY = "ally"
    SHADOW = "shadow"
    THRESHOLD_GUARDIAN = "threshold_guardian"
    TRICKSTER = "trickster"
    HERALD = "herald"
    SHAPESHIFTER = "shapeshifter"


class SceneType(str, Enum):
    """Types of scenes for analysis."""
    SETUP = "setup"
    CONFRONTATION = "confrontation"
    RESOLUTION = "resolution"
    CHARACTER = "character"
    EXPOSITION = "exposition"
    TRANSITION = "transition"
    CLIMAX = "climax"
    DENOUEMENT = "denouement"


class EmotionalTone(str, Enum):
    """Emotional tones for scene analysis."""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    LOVE = "love"
    HOPE = "hope"
    DESPAIR = "despair"
    CURIOSITY = "curiosity"


class ConflictLevel(str, Enum):
    """Levels of conflict in scenes."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class CharacterAnalysis(BaseModel):
    """Analysis of a character's role and arc."""
    character_name: str
    archetype: CharacterArchetype
    primary_motivation: str
    internal_conflict: str
    external_conflict: str
    character_arc: str
    story_circle_position: StoryCircleBeat
    emotional_journey: List[EmotionalTone]
    relationships: Dict[str, str]
    dialogue_patterns: List[str]
    key_moments: List[str]
    transformation_summary: str
    
    model_config = ConfigDict(use_enum_values=True)


class SceneAnalysis(BaseModel):
    """Detailed analysis of a single scene."""
    scene_id: str
    scene_number: str
    scene_heading: str
    synopsis: str
    story_circle_beat: StoryCircleBeat
    scene_type: SceneType
    primary_emotion: EmotionalTone
    conflict_level: ConflictLevel
    character_development: Dict[str, str]
    thematic_elements: List[str]
    visual_descriptions: List[str]
    dialogue_highlights: List[str]
    pacing_analysis: str
    dramatic_function: str
    foreshadowing: List[str]
    callbacks: List[str]
    character_arcs: Dict[str, str]
    emotional_arc: List[EmotionalTone]
    stakes: str
    tension_level: int = Field(ge=1, le=10)
    
    model_config = ConfigDict(use_enum_values=True)


class StoryCircleAnalysis(BaseModel):
    """Complete Story Circle analysis for the script."""
    beats: Dict[StoryCircleBeat, List[SceneAnalysis]]
    character_journeys: Dict[str, List[StoryCircleBeat]]
    overall_arc: str
    thematic_throughline: str
    character_transformations: Dict[str, str]
    pacing_analysis: str
    emotional_progression: List[EmotionalTone]
    structural_strengths: List[str]
    structural_weaknesses: List[str]
    improvement_suggestions: List[str]
    
    model_config = ConfigDict(use_enum_values=True)


class TableReadRequest(BaseModel):
    """Request for digital table read analysis."""
    project_id: str
    script_content: str
    scene_breakdown: Optional[Dict[str, Any]] = None
    analysis_depth: str = Field(default="comprehensive", pattern=r"^(basic|comprehensive|deep)$")
    focus_areas: List[str] = Field(default_factory=lambda: ["characters", "structure", "themes"])
    character_voices: Optional[Dict[str, Dict[str, Any]]] = None
    include_audio: bool = False
    generate_bible: bool = True
    
    @field_validator('script_content')
    def validate_script_content(cls, v):
        if not v or len(v.strip()) < 100:
            raise ValueError("Script content must be at least 100 characters")
        return v.strip()


class DialogueAnalysis(BaseModel):
    """Analysis of dialogue patterns and character voices."""
    character_id: str
    character_name: str
    speech_patterns: List[str]
    vocabulary_level: str
    sentence_structure: str
    emotional_indicators: List[str]
    subtext_analysis: str
    voice_consistency: float = Field(ge=0.0, le=1.0)
    unique_phrases: List[str]
    dialogue_functions: List[str]
    relationship_indicators: Dict[str, str]


class ThemeAnalysis(BaseModel):
    """Analysis of themes and motifs."""
    primary_themes: List[str]
    secondary_themes: List[str]
    motifs: List[str]
    symbols: List[str]
    thematic_questions: List[str]
    moral_dilemmas: List[str]
    philosophical_exploration: str
    cultural_commentary: str
    universal_themes: List[str]


class CreativeBible(BaseModel):
    """Comprehensive creative bible generated from script analysis."""
    bible_id: str
    project_id: str
    title: str
    logline: str
    synopsis: str
    character_bios: Dict[str, CharacterAnalysis]
    scene_analyses: List[SceneAnalysis]
    story_circle: StoryCircleAnalysis
    themes: ThemeAnalysis
    dialogue_analysis: List[DialogueAnalysis]
    visual_style: str
    tone_description: str
    genre_analysis: str
    target_audience: str
    comparable_works: List[str]
    production_notes: str
    character_relationships: Dict[str, List[str]]
    emotional_heatmap: Dict[str, List[EmotionalTone]]
    structural_timeline: Dict[str, str]
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(use_enum_values=True)


class TableReadSession(BaseModel):
    """Active table read session with real-time analysis."""
    session_id: str
    project_id: str
    bible_id: str
    status: str = Field(default="processing")
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    current_analysis: Optional[str] = None
    results: Optional[CreativeBible] = None
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(use_enum_values=True)


class AudioGenerationRequest(BaseModel):
    """Request for generating audio table read."""
    session_id: str
    character_voices: Dict[str, Dict[str, Any]]
    background_music: Optional[str] = None
    sound_effects: Optional[List[str]] = None
    pacing: str = Field(default="natural", pattern=r"^(slow|natural|fast)$")
    emotion_intensity: float = Field(default=0.7, ge=0.0, le=1.0)
    
    model_config = ConfigDict(use_enum_values=True)


class AudioGenerationResult(BaseModel):
    """Result of audio table read generation."""
    result_id: str
    session_id: str
    audio_files: List[str]
    total_duration: float
    character_voices_used: Dict[str, str]
    metadata: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TableReadExportRequest(BaseModel):
    """Request to export table read results."""
    session_id: str
    format: str = Field(default="pdf", pattern=r"^(pdf|json|markdown|docx)$")
    include_audio: bool = False
    sections: List[str] = Field(default_factory=lambda: ["all"])
    
    model_config = ConfigDict(use_enum_values=True)


class TableReadExportResult(BaseModel):
    """Result of table read export."""
    export_id: str
    session_id: str
    format: str
    file_path: str
    file_size: int
    sections_included: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Helper functions for script parsing and analysis
def extract_scene_headings(script_content: str) -> List[str]:
    """Extract scene headings from script."""
    pattern = r'^\s*(INT\.|EXT\.|INT/EXT\.|EXT/INT\.)\s+.*?\s*-\s*.*?$'
    return re.findall(pattern, script_content, re.MULTILINE | re.IGNORECASE)


def extract_character_names(script_content: str) -> List[str]:
    """Extract character names from script."""
    pattern = r'^\s*([A-Z][A-Z\s]+)\s*$'
    lines = script_content.split('\n')
    characters = []
    for line in lines:
        match = re.match(pattern, line.strip())
        if match and len(match.group(1)) > 2:
            characters.append(match.group(1).strip())
    return list(set(characters))


def identify_story_circle_beat(scene_content: str) -> Optional[StoryCircleBeat]:
    """Identify which story circle beat a scene represents."""
    content_lower = scene_content.lower()
    
    # Keywords for each beat
    beat_keywords = {
        StoryCircleBeat.YOU: ["comfort", "home", "normal", "routine", "familiar"],
        StoryCircleBeat.NEED: ["want", "desire", "need", "wish", "crave", "yearn"],
        StoryCircleBeat.GO: ["leave", "enter", "cross", "step", "venture", "journey"],
        StoryCircleBeat.SEARCH: ["find", "look", "seek", "explore", "investigate", "adapt"],
        StoryCircleBeat.FIND: ["discover", "obtain", "achieve", "get", "acquire", "success"],
        StoryCircleBeat.TAKE: ["pay", "price", "cost", "sacrifice", "lose", "consequence"],
        StoryCircleBeat.RETURN: ["back", "return", "home", "familiar", "circle", "complete"],
        StoryCircleBeat.CHANGE: ["transform", "change", "grow", "different", "new", "evolve"]
    }
    
    for beat, keywords in beat_keywords.items():
        for keyword in keywords:
            if keyword in content_lower:
                return beat
    
    return None