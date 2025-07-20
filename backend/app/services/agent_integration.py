"""
Agent Integration Bridge
STORY-085 Implementation

Provides the integration layer between the expanded asset system and the agentic crew system
for AI-driven content generation workflows.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.models.asset_types import BaseAsset, AssetType, AssetReference
from app.models.generative_shotlist import GenerativeShotList, GenerativeShot, ShotRequirements
from app.services.asset_registry import AssetRegistry
# from app.models.quality_presets import QualityPreset  # Import if needed later


class AgentRole(str, Enum):
    """Enumeration of agent roles in the creative crew system."""
    DRAMATURG = "dramaturg"
    PROP_MASTER = "prop_master"
    COSTUME_DESIGNER = "costume_designer"
    VFX_SUPERVISOR = "vfx_supervisor"
    SHOT_DESIGNER = "shot_designer"
    LOCATION_SCOUT = "location_scout"
    MUSIC_DIRECTOR = "music_director"
    SOUND_DESIGNER = "sound_designer"


class TaskType(str, Enum):
    """Types of tasks agents can perform."""
    ASSET_GENERATION = "asset_generation"
    SCENE_ANALYSIS = "scene_analysis"
    SHOT_PLANNING = "shot_planning"
    STYLE_CONSULTATION = "style_consultation"
    QUALITY_ASSESSMENT = "quality_assessment"
    PROP_RECOMMENDATION = "prop_recommendation"
    WARDROBE_STYLING = "wardrobe_styling"
    LOCATION_MATCHING = "location_matching"


@dataclass
class AgentTask:
    """Represents a task assigned to an agent."""
    task_id: str
    agent_role: AgentRole
    task_type: TaskType
    context: Dict[str, Any]
    assets: List[AssetReference]
    requirements: Dict[str, Any]
    priority: int = 5
    status: str = "pending"
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AgentRecommendation:
    """Represents a recommendation from an agent."""
    recommendation_id: str
    agent_role: AgentRole
    task_id: str
    asset_type: AssetType
    recommendation_data: Dict[str, Any]
    confidence_score: float
    reasoning: str
    metadata: Dict[str, Any]


class AgentIntegrationBridge:
    """Central bridge between asset system and agentic crew."""
    
    def __init__(self, project_root: str, asset_registry: AssetRegistry):
        self.project_root = project_root
        self.asset_registry = asset_registry
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, AgentTask] = {}
        self.recommendations: List[AgentRecommendation] = []
        
        # Agent specialization mapping
        self.agent_specializations = {
            AgentRole.DRAMATURG: {
                TaskType.SCENE_ANALYSIS,
                TaskType.SHOT_PLANNING,
                TaskType.QUALITY_ASSESSMENT
            },
            AgentRole.PROP_MASTER: {
                TaskType.ASSET_GENERATION,
                TaskType.PROP_RECOMMENDATION,
                TaskType.QUALITY_ASSESSMENT
            },
            AgentRole.COSTUME_DESIGNER: {
                TaskType.ASSET_GENERATION,
                TaskType.WARDROBE_STYLING,
                TaskType.STYLE_CONSULTATION
            },
            AgentRole.VFX_SUPERVISOR: {
                TaskType.ASSET_GENERATION,
                TaskType.QUALITY_ASSESSMENT,
                TaskType.STYLE_CONSULTATION
            },
            AgentRole.SHOT_DESIGNER: {
                TaskType.SHOT_PLANNING,
                TaskType.SCENE_ANALYSIS,
                TaskType.QUALITY_ASSESSMENT
            },
            AgentRole.LOCATION_SCOUT: {
                TaskType.LOCATION_MATCHING,
                TaskType.SCENE_ANALYSIS
            },
            AgentRole.MUSIC_DIRECTOR: {
                TaskType.ASSET_GENERATION,
                TaskType.STYLE_CONSULTATION
            },
            AgentRole.SOUND_DESIGNER: {
                TaskType.ASSET_GENERATION,
                TaskType.STYLE_CONSULTATION
            }
        }
    
    async def create_task_from_shot(
        self, 
        shot: GenerativeShot, 
        agent_role: AgentRole,
        context: Dict[str, Any] = None
    ) -> str:
        """Create an agent task from a generative shot."""
        task_id = f"{agent_role.value}_{shot.shot_id}_{datetime.now().timestamp()}"
        
        # Determine task type based on agent role and shot requirements
        task_type = self._determine_task_type(agent_role, shot)
        
        # Extract relevant context
        context = context or {}
        context.update({
            "shot_id": shot.shot_id,
            "scene_description": shot.shot_description,
            "mood": shot.requirements.mood,
            "tone": shot.requirements.tone,
            "visual_style": shot.requirements.visual_style,
            "duration": shot.timing.estimated_duration,
            "resolution": shot.requirements.resolution,
            "aspect_ratio": shot.requirements.aspect_ratio
        })
        
        # Collect relevant assets
        assets = self._collect_relevant_assets(shot)
        
        task = AgentTask(
            task_id=task_id,
            agent_role=agent_role,
            task_type=task_type,
            context=context,
            assets=assets,
            requirements={
                "quality_preset": shot.requirements.quality_preset,
                "style_preferences": shot.requirements.visual_style,
                "technical_specs": {
                    "resolution": shot.requirements.resolution,
                    "aspect_ratio": shot.requirements.aspect_ratio,
                    "frame_rate": shot.requirements.frame_rate
                }
            },
            priority=shot.render_priority
        )
        
        self.active_tasks[task_id] = task
        return task_id
    
    async def create_task_from_assets(
        self,
        assets: List[AssetReference],
        agent_role: AgentRole,
        task_type: TaskType,
        context: Dict[str, Any] = None
    ) -> str:
        """Create an agent task from asset references."""
        task_id = f"{agent_role.value}_{task_type.value}_{datetime.now().timestamp()}"
        
        task = AgentTask(
            task_id=task_id,
            agent_role=agent_role,
            task_type=task_type,
            context=context or {},
            assets=assets,
            requirements={},
            priority=5
        )
        
        self.active_tasks[task_id] = task
        return task_id
    
    def _determine_task_type(self, agent_role: AgentRole, shot: GenerativeShot) -> TaskType:
        """Determine the appropriate task type based on agent role and shot requirements."""
        role_mapping = {
            AgentRole.DRAMATURG: TaskType.SCENE_ANALYSIS,
            AgentRole.PROP_MASTER: TaskType.PROP_RECOMMENDATION,
            AgentRole.COSTUME_DESIGNER: TaskType.WARDROBE_STYLING,
            AgentRole.VFX_SUPERVISOR: TaskType.STYLE_CONSULTATION,
            AgentRole.SHOT_DESIGNER: TaskType.SHOT_PLANNING,
            AgentRole.LOCATION_SCOUT: TaskType.LOCATION_MATCHING,
            AgentRole.MUSIC_DIRECTOR: TaskType.STYLE_CONSULTATION,
            AgentRole.SOUND_DESIGNER: TaskType.STYLE_CONSULTATION
        }
        return role_mapping.get(agent_role, TaskType.ASSET_GENERATION)
    
    def _collect_relevant_assets(self, shot: GenerativeShot) -> List[AssetReference]:
        """Collect all relevant asset references for a shot."""
        assets = []
        
        # Add character assets
        for character in shot.assets.characters:
            assets.append(character)
        
        # Add prop assets
        for prop in shot.assets.props:
            assets.append(prop)
        
        # Add wardrobe assets
        for wardrobe in shot.assets.wardrobe:
            assets.append(wardrobe)
        
        # Add location assets
        for location in shot.assets.locations:
            assets.append(location)
        
        # Add style assets
        for style in shot.assets.styles:
            assets.append(style)
        
        return assets
    
    async def process_agent_recommendation(
        self, 
        recommendation: AgentRecommendation
    ) -> Dict[str, Any]:
        """Process and potentially act on an agent recommendation."""
        
        # Store recommendation
        self.recommendations.append(recommendation)
        
        # Create asset if recommendation meets criteria
        if recommendation.confidence_score >= 0.7:
            asset_data = self._create_asset_from_recommendation(recommendation)
            
            # Register the new asset
            asset = await self.asset_registry.register_asset(asset_data)
            
            return {
                "status": "created",
                "asset_id": asset,
                "recommendation_id": recommendation.recommendation_id,
                "confidence_score": recommendation.confidence_score
            }
        
        return {
            "status": "review_needed",
            "recommendation_id": recommendation.recommendation_id,
            "confidence_score": recommendation.confidence_score
        }
    
    def _create_asset_from_recommendation(self, rec: AgentRecommendation) -> BaseAsset:
        """Create an asset instance from an agent recommendation."""
        from app.models.asset_types import create_asset_from_dict
        import uuid
        
        asset_data = {
            "asset_id": str(uuid.uuid4()),
            "asset_type": rec.asset_type.value,
            **rec.recommendation_data,
            "created_by": f"agent_{rec.agent_role.value}",
            "tags": ["agent_recommended", rec.agent_role.value]
        }
        
        return create_asset_from_dict(asset_data)
    
    async def generate_shot_recommendations(
        self,
        shot_list: GenerativeShotList,
        agent_roles: List[AgentRole] = None
    ) -> Dict[str, List[AgentRecommendation]]:
        """Generate comprehensive recommendations for a shot list."""
        
        if agent_roles is None:
            agent_roles = list(AgentRole)
        
        recommendations = {role.value: [] for role in agent_roles}
        
        for sequence in shot_list.sequences:
            for shot in sequence.shots:
                for role in agent_roles:
                    rec = await self._generate_shot_recommendation(shot, role)
                    if rec:
                        recommendations[role.value].append(rec)
        
        return recommendations
    
    async def _generate_shot_recommendation(
        self, 
        shot: GenerativeShot, 
        agent_role: AgentRole
    ) -> Optional[AgentRecommendation]:
        """Generate a specific recommendation for a shot from an agent."""
        
        recommendation_data = {}
        confidence_score = 0.0
        reasoning = ""
        
        if agent_role == AgentRole.DRAMATURG:
            recommendation_data = await self._dramaturg_analysis(shot)
            confidence_score = 0.85
            reasoning = "Scene analysis based on narrative structure"
            
        elif agent_role == AgentRole.PROP_MASTER:
            recommendation_data = await self._prop_recommendations(shot)
            confidence_score = 0.75
            reasoning = "Props needed for scene authenticity"
            
        elif agent_role == AgentRole.COSTUME_DESIGNER:
            recommendation_data = await self._wardrobe_recommendations(shot)
            confidence_score = 0.80
            reasoning = "Costume recommendations based on character and scene"
            
        elif agent_role == AgentRole.VFX_SUPERVISOR:
            recommendation_data = await self._vfx_recommendations(shot)
            confidence_score = 0.70
            reasoning = "Visual effects requirements analysis"
            
        elif agent_role == AgentRole.SHOT_DESIGNER:
            recommendation_data = await self._shot_design_recommendations(shot)
            confidence_score = 0.90
            reasoning = "Shot composition and technical recommendations"
        
        if recommendation_data:
            return AgentRecommendation(
                recommendation_id=f"{agent_role.value}_{shot.shot_id}_{datetime.now().timestamp()}",
                agent_role=agent_role,
                task_id="",  # Will be populated when task is created
                asset_type=self._get_recommendation_asset_type(agent_role),
                recommendation_data=recommendation_data,
                confidence_score=confidence_score,
                reasoning=reasoning,
                metadata={
                    "shot_id": shot.shot_id,
                    "scene_context": shot.shot_description,
                    "generation_time": datetime.now().isoformat()
                }
            )
        
        return None
    
    async def _dramaturg_analysis(self, shot: GenerativeShot) -> Dict[str, Any]:
        """Generate dramaturgical analysis and recommendations."""
        return {
            "scene_notes": f"Scene: {shot.shot_description}",
            "character_development": f"Character arc support needed for mood: {shot.requirements.mood}",
            "emotional_beats": shot.requirements.mood,
            "narrative_purpose": shot.shot_synopsis
        }
    
    async def _prop_recommendations(self, shot: GenerativeShot) -> Dict[str, Any]:
        """Generate prop recommendations based on scene context."""
        return {
            "recommended_props": [
                {
                    "name": f"Scene-specific prop for {shot.shot_description[:30]}...",
                    "category": "scene_specific",
                    "context": shot.shot_description
                }
            ],
            "prop_style": shot.requirements.visual_style
        }
    
    async def _wardrobe_recommendations(self, shot: GenerativeShot) -> Dict[str, Any]:
        """Generate wardrobe recommendations based on scene context."""
        return {
            "wardrobe_style": shot.requirements.visual_style,
            "color_palette": self._extract_color_palette(shot.lighting.color_grade_style),
            "character_wardrobe": {
                "style": shot.requirements.visual_style,
                "mood": shot.requirements.mood
            }
        }
    
    async def _vfx_recommendations(self, shot: GenerativeShot) -> Dict[str, Any]:
        """Generate VFX recommendations based on scene requirements."""
        return {
            "vfx_needs": f"Visual effects for {shot.requirements.visual_style}",
            "technical_specs": {
                "resolution": shot.requirements.resolution,
                "quality": shot.requirements.quality_preset
            },
            "style_guide": shot.requirements.visual_style
        }
    
    async def _shot_design_recommendations(self, shot: GenerativeShot) -> Dict[str, Any]:
        """Generate shot design and technical recommendations."""
        return {
            "shot_notes": f"Technical shot design for {shot.shot_description}",
            "composition_notes": shot.composition.model_dump(),
            "lighting_setup": shot.lighting.model_dump(),
            "camera_specs": {
                "angle": shot.composition.shot_angle,
                "movement": shot.composition.camera_movement,
                "type": shot.composition.shot_type
            }
        }
    
    def _extract_color_palette(self, color_grade: str) -> List[str]:
        """Extract color palette suggestions from color grade style."""
        palette_map = {
            "warm": ["#ff6b35", "#f7931e", "#ffd23f"],
            "cool": ["#3b82f6", "#06b6d4", "#8b5cf6"],
            "natural": ["#22c55e", "#84cc16", "#a3a3a3"],
            "high_contrast": ["#000000", "#ffffff", "#ef4444"]
        }
        return palette_map.get(color_grade, ["#808080"])
    
    def _get_recommendation_asset_type(self, agent_role: AgentRole) -> AssetType:
        """Determine the asset type for agent recommendations."""
        type_mapping = {
            AgentRole.PROP_MASTER: AssetType.PROP,
            AgentRole.COSTUME_DESIGNER: AssetType.WARDROBE,
            AgentRole.VFX_SUPERVISOR: AssetType.SFX,
            AgentRole.LOCATION_SCOUT: AssetType.LOCATION,
            AgentRole.MUSIC_DIRECTOR: AssetType.MUSIC,
            AgentRole.SOUND_DESIGNER: AssetType.SOUND
        }
        return type_mapping.get(agent_role, AssetType.PROP)
    
    async def get_task_status(self, task_id: str) -> Optional[AgentTask]:
        """Get the status of a specific task."""
        return self.active_tasks.get(task_id) or self.completed_tasks.get(task_id)
    
    async def get_active_tasks(self) -> List[AgentTask]:
        """Get all active tasks."""
        return list(self.active_tasks.values())
    
    async def get_recommendations_by_role(
        self, 
        agent_role: AgentRole
    ) -> List[AgentRecommendation]:
        """Get all recommendations from a specific agent role."""
        return [rec for rec in self.recommendations if rec.agent_role == agent_role]
    
    async def export_agent_workflow(self, task_ids: List[str] = None) -> Dict[str, Any]:
        """Export the complete agent workflow for documentation or replay."""
        target_tasks = []
        
        if task_ids:
            target_tasks = [
                task for task_id, task in self.active_tasks.items()
                if task_id in task_ids
            ] + [
                task for task_id, task in self.completed_tasks.items()
                if task_id in task_ids
            ]
        else:
            target_tasks = list(self.active_tasks.values()) + list(self.completed_tasks.values())
        
        return {
            "export_timestamp": datetime.now().isoformat(),
            "total_tasks": len(target_tasks),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "agent_role": task.agent_role.value,
                    "task_type": task.task_type.value,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "result": task.result,
                    "assets_count": len(task.assets)
                }
                for task in target_tasks
            ],
            "recommendations": [
                {
                    "recommendation_id": rec.recommendation_id,
                    "agent_role": rec.agent_role.value,
                    "confidence_score": rec.confidence_score,
                    "reasoning": rec.reasoning,
                    "asset_type": rec.asset_type.value
                }
                for rec in self.recommendations
            ]
        }