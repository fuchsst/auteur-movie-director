"""
Breakdown View Models
STORY-086 Implementation

Models for the professional script breakdown interface that mirrors traditional
production workflows and integrates with the generative platform.
"""

from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.models.asset_types import AssetType, BaseAsset


class BreakdownElementStatus(str, Enum):
    """Status of breakdown elements."""
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    LINKED = "linked"
    CREATED = "created"
    IGNORED = "ignored"


class ElementCategory(str, Enum):
    """Categories of production elements."""
    CAST = "cast"
    PROPS = "props"
    WARDROBE = "wardrobe"
    VEHICLES = "vehicles"
    SET_DRESSING = "set_dressing"
    SFX = "sfx"
    SOUNDS = "sounds"
    MUSIC = "music"
    LOCATIONS = "locations"
    SPECIAL_EFFECTS = "special_effects"


class BreakdownElement(BaseModel):
    """A production element detected in script."""
    
    element_id: str = Field(..., description="Unique element identifier")
    element_type: ElementCategory = Field(..., description="Type of element")
    name: str = Field(..., description="Element name/description")
    description: str = Field(..., description="Detailed description")
    
    # Script context
    scene_id: str = Field(..., description="Parent scene ID")
    script_position: Dict[str, int] = Field(default_factory=dict, description="Position in script")
    context_text: str = Field(default="", description="Surrounding text context")
    
    # Asset linking
    asset_id: Optional[str] = Field(None, description="Linked asset ID")
    asset_type: Optional[AssetType] = Field(None, description="Asset type")
    
    # Status and workflow
    status: BreakdownElementStatus = Field(default=BreakdownElementStatus.DETECTED)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Detection confidence")
    
    # Production details
    quantity: int = Field(default=1, ge=1, description="Quantity needed")
    notes: str = Field(default="", description="Production notes")
    special_instructions: str = Field(default="", description="Special instructions")
    
    # Budget and scheduling
    estimated_cost: float = Field(default=0.0, description="Estimated cost")
    estimated_time: float = Field(default=0.0, description="Estimated setup time")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")


class SceneBreakdown(BaseModel):
    """Complete breakdown for a single scene."""
    
    scene_id: str = Field(..., description="Scene identifier")
    scene_number: str = Field(..., description="Scene number (e.g., '1', '2A')")
    scene_heading: str = Field(..., description="Scene heading")
    synopsis: str = Field(..., description="Scene synopsis")
    
    # Location details
    location: str = Field(..., description="Primary location")
    time_of_day: str = Field(..., description="Time of day")
    interior_exterior: str = Field(..., description="INT/EXT")
    
    # Script timing
    estimated_pages: float = Field(default=0.0, description="Estimated script pages")
    estimated_duration: float = Field(default=0.0, description="Estimated duration in seconds")
    
    # Production elements
    elements: Dict[ElementCategory, List[BreakdownElement]] = Field(default_factory=dict)
    
    # Characters
    characters: List[str] = Field(default_factory=list, description="Characters in scene")
    day_night: str = Field(default="DAY", description="Day or night scene")
    
    # Production notes
    continuity_notes: str = Field(default="", description="Continuity notes")
    special_notes: str = Field(default="", description="Special production notes")
    
    # Status
    breakdown_complete: bool = Field(default=False)
    validated: bool = Field(default=False)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def get_total_elements(self) -> int:
        """Get total number of elements across all categories."""
        return sum(len(elements) for elements in self.elements.values())
    
    def get_total_cost(self) -> float:
        """Get total estimated cost for all elements."""
        return sum(
            element.estimated_cost 
            for elements in self.elements.values() 
            for element in elements
        )
    
    def get_elements_by_status(self, status: BreakdownElementStatus) -> List[BreakdownElement]:
        """Get elements filtered by status."""
        elements = []
        for category_elements in self.elements.values():
            elements.extend([e for e in category_elements if e.status == status])
        return elements


class ScriptBreakdown(BaseModel):
    """Complete script breakdown for a project."""
    
    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name")
    
    # Script info
    script_title: str = Field(..., description="Script title")
    script_author: str = Field(..., description="Script author")
    total_scenes: int = Field(..., description="Total number of scenes")
    total_pages: float = Field(..., description="Total script pages")
    
    # Scene breakdowns
    scenes: Dict[str, SceneBreakdown] = Field(default_factory=dict)
    scene_order: List[str] = Field(default_factory=list)
    
    # Global elements
    all_characters: List[str] = Field(default_factory=list)
    all_locations: List[str] = Field(default_factory=list)
    
    # Statistics
    total_elements: int = Field(default=0)
    total_estimated_cost: float = Field(default=0.0)
    total_estimated_duration: float = Field(default=0.0)
    
    # Element counts by category
    element_counts: Dict[ElementCategory, int] = Field(default_factory=dict)
    
    # Validation
    is_valid: bool = Field(default=True)
    validation_errors: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    def calculate_totals(self) -> None:
        """Calculate total statistics."""
        self.total_elements = sum(scene.get_total_elements() for scene in self.scenes.values())
        self.total_estimated_cost = sum(scene.get_total_cost() for scene in self.scenes.values())
        self.total_estimated_duration = sum(scene.estimated_duration for scene in self.scenes.values())
        
        # Calculate element counts by category
        category_counts = {category: 0 for category in ElementCategory}
        for scene in self.scenes.values():
            for category, elements in scene.elements.items():
                category_counts[category] += len(elements)
        
        self.element_counts = category_counts
    
    def get_scene_by_number(self, scene_number: str) -> Optional[SceneBreakdown]:
        """Get scene by scene number."""
        for scene in self.scenes.values():
            if scene.scene_number == scene_number:
                return scene
        return None
    
    def validate_breakdown(self) -> bool:
        """Validate the complete breakdown."""
        errors = []
        
        # Check for duplicate scene numbers
        scene_numbers = [scene.scene_number for scene in self.scenes.values()]
        if len(scene_numbers) != len(set(scene_numbers)):
            errors.append("Duplicate scene numbers found")
        
        # Check for missing required fields
        for scene in self.scenes.values():
            if not scene.scene_heading:
                errors.append(f"Missing scene heading for scene {scene.scene_id}")
            if not scene.location:
                errors.append(f"Missing location for scene {scene.scene_id}")
        
        self.validation_errors = errors
        self.is_valid = len(errors) == 0
        return self.is_valid


class BreakdownTemplate(BaseModel):
    """Template for creating breakdowns from scripts."""
    
    template_id: str = Field(..., description="Template identifier")
    template_name: str = Field(..., description="Template name")
    template_description: str = Field(..., description="Template description")
    
    # Template configuration
    element_categories: List[ElementCategory] = Field(default_factory=list)
    detection_rules: Dict[str, Any] = Field(default_factory=dict)
    default_values: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation rules
    required_fields: List[str] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")
    
    def apply_template(self, script_data: Dict[str, Any]) -> ScriptBreakdown:
        """Apply template to script data."""
        return ScriptBreakdown(
            project_id=script_data.get("project_id", "unknown"),
            project_name=script_data.get("project_name", "Untitled Project"),
            script_title=script_data.get("title", "Untitled Script"),
            script_author=script_data.get("author", "Unknown"),
            total_scenes=script_data.get("total_scenes", 0),
            total_pages=script_data.get("total_pages", 0.0)
        )


class BreakdownExportFormat(str, Enum):
    """Export formats for breakdown data."""
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    FDX = "fdx"


class BreakdownExportRequest(BaseModel):
    """Request for exporting breakdown data."""
    
    project_id: str = Field(..., description="Project identifier")
    export_format: BreakdownExportFormat = Field(..., description="Export format")
    include_scenes: List[str] = Field(default_factory=list, description="Specific scenes to include")
    export_options: Dict[str, Any] = Field(default_factory=dict, description="Export options")
    
    # Filtering
    filter_categories: List[ElementCategory] = Field(default_factory=list)
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    include_notes: bool = Field(default=True)
    include_costs: bool = Field(default=True)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None, description="Creator identifier")