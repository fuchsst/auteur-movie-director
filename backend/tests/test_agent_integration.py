"""
Comprehensive tests for STORY-085: Agent Integration Bridge
Tests agent task creation, recommendation systems, and workflow integration.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

from app.services.agent_integration import (
    AgentIntegrationBridge, AgentRole, TaskType, 
    AgentTask, AgentRecommendation
)
from app.services.asset_registry import AssetRegistry
from app.models.generative_shotlist import (
    GenerativeShotList, GenerativeShot, ShotType, ShotRequirements,
    ShotComposition, ShotLighting, ShotAudio, ShotTiming
)
from app.models.asset_types import AssetType, PropAsset, WardrobeAsset, AssetReference


class TestAgentIntegrationBridge:
    """Test the Agent Integration Bridge functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def asset_registry(self, temp_dir):
        """Create test asset registry."""
        return AssetRegistry(temp_dir)
    
    @pytest.fixture
    def bridge(self, temp_dir, asset_registry):
        """Create test agent integration bridge."""
        return AgentIntegrationBridge(str(temp_dir), asset_registry)
    
    @pytest.fixture
    def sample_shot_list(self):
        """Create a sample shot list for testing."""
        shot = GenerativeShot(
            shot_id="test-shot-001",
            shot_number="1A",
            shot_type=ShotType.CLOSEUP,
            shot_description="Close-up of protagonist showing determination",
            shot_synopsis="Character resolves to take action",
            composition=ShotComposition(
                shot_type=ShotType.CLOSEUP,
                shot_angle="eye_level",
                camera_movement="static"
            ),
            lighting=ShotLighting(
                lighting_setup="three_point",
                color_grade_style="warm"
            ),
            audio=ShotAudio(
                audio_design="emotional",
                primary_source="dialogue"
            ),
            requirements=ShotRequirements(
                mood="determined",
                tone="intense",
                visual_style="cinematic close-up"
            ),
            generative_prompt={"prompt_text": "Close-up of determined character"},
            timing=ShotTiming(estimated_duration=3.5)
        )
        
        return GenerativeShotList(
            project_id="test-project",
            project_name="Test Project",
            story_structure={"type": "three_act"}
        )
    
    def test_agent_role_enumeration(self):
        """Test agent role enumeration."""
        assert AgentRole.DRAMATURG.value == "dramaturg"
        assert AgentRole.PROP_MASTER.value == "prop_master"
        assert AgentRole.COSTUME_DESIGNER.value == "costume_designer"
        assert len(AgentRole) == 8
    
    def test_task_type_enumeration(self):
        """Test task type enumeration."""
        assert TaskType.ASSET_GENERATION.value == "asset_generation"
        assert TaskType.SCENE_ANALYSIS.value == "scene_analysis"
        assert len(TaskType) == 8
    
    @pytest.mark.asyncio
    async def test_create_task_from_shot(self, bridge, sample_shot_list):
        """Test creating agent task from shot."""
        shot = sample_shot_list.sequences[0].shots[0] if sample_shot_list.sequences else None
        if not shot:
            # Add a shot to the sample
            shot = GenerativeShot(
                shot_id="test-shot-001",
                shot_number="1A",
                shot_type=ShotType.CLOSEUP,
                shot_description="Test shot",
                shot_synopsis="Test synopsis",
                composition=ShotComposition(
                    shot_type=ShotType.CLOSEUP,
                    shot_angle="eye_level",
                    camera_movement="static"
                ),
                lighting=ShotLighting(
                    lighting_setup="three_point",
                    color_grade_style="natural"
                ),
                audio=ShotAudio(
                    audio_design="naturalistic",
                    primary_source="dialogue"
                ),
                requirements=ShotRequirements(
                    mood="neutral",
                    tone="conversational",
                    visual_style="standard"
                ),
                generative_prompt={"prompt_text": "Test shot"},
                timing=ShotTiming(estimated_duration=4.0)
            )
        
        task_id = await bridge.create_task_from_shot(
            shot=shot,
            agent_role=AgentRole.DRAMATURG
        )
        
        assert task_id is not None
        assert task_id.startswith("dramaturg_test-shot-001")
        assert task_id in bridge.active_tasks
        
        task = bridge.active_tasks[task_id]
        assert task.agent_role == AgentRole.DRAMATURG
        assert task.task_type == TaskType.SCENE_ANALYSIS
        assert task.context["shot_id"] == "test-shot-001"
        assert task.context["mood"] == "neutral"
    
    @pytest.mark.asyncio
    async def test_create_task_from_assets(self, bridge):
        """Test creating agent task from asset references."""
        assets = [
            AssetReference(asset_id="prop-001", asset_type=AssetType.PROP),
            AssetReference(asset_id="wardrobe-001", asset_type=AssetType.WARDROBE)
        ]
        
        task_id = await bridge.create_task_from_assets(
            assets=assets,
            agent_role=AgentRole.PROP_MASTER,
            task_type=TaskType.PROP_RECOMMENDATION,
            context={"scene": "warehouse", "tone": "dramatic"}
        )
        
        assert task_id is not None
        assert task_id.startswith("prop_master_prop_recommendation")
        assert task_id in bridge.active_tasks
        
        task = bridge.active_tasks[task_id]
        assert task.agent_role == AgentRole.PROP_MASTER
        assert task.task_type == TaskType.PROP_RECOMMENDATION
        assert len(task.assets) == 2
        assert task.context["scene"] == "warehouse"
    
    @pytest.mark.asyncio
    async def test_agent_specializations(self, bridge):
        """Test agent role specializations."""
        specializations = bridge.agent_specializations
        
        assert AgentRole.DRAMATURG in specializations
        assert TaskType.SCENE_ANALYSIS in specializations[AgentRole.DRAMATURG]
        assert TaskType.SHOT_PLANNING in specializations[AgentRole.DRAMATURG]
        
        assert AgentRole.PROP_MASTER in specializations
        assert TaskType.ASSET_GENERATION in specializations[AgentRole.PROP_MASTER]
        assert TaskType.PROP_RECOMMENDATION in specializations[AgentRole.PROP_MASTER]
    
    @pytest.mark.asyncio
    async def test_process_agent_recommendation(self, bridge, asset_registry):
        """Test processing agent recommendations."""
        recommendation = AgentRecommendation(
            recommendation_id="rec-001",
            agent_role=AgentRole.PROP_MASTER,
            task_id="task-001",
            asset_type=AssetType.PROP,
            recommendation_data={
                "name": "Ancient Sword",
                "description": "Weathered bronze sword for dramatic scene",
                "category": "weapon",
                "material": "bronze"
            },
            confidence_score=0.85,
            reasoning="Historical accuracy and dramatic impact",
            metadata={"scene": ["battle"], "character": ["warrior"]}
        )
        
        result = await bridge.process_agent_recommendation(recommendation)
        
        assert result["status"] == "created"
        assert "asset_id" in result
        assert result["recommendation_id"] == "rec-001"
        assert result["confidence_score"] == 0.85
        
        # Verify recommendation was stored
        assert len(bridge.recommendations) == 1
        assert bridge.recommendations[0] == recommendation
    
    @pytest.mark.asyncio
    async def test_process_low_confidence_recommendation(self, bridge):
        """Test processing low confidence recommendations."""
        recommendation = AgentRecommendation(
            recommendation_id="rec-low",
            agent_role=AgentRole.COSTUME_DESIGNER,
            task_id="task-002",
            asset_type=AssetType.WARDROBE,
            recommendation_data={
                "name": "Medieval Tunic",
                "description": "Simple tunic for period scene",
                "category": "outerwear"
            },
            confidence_score=0.5,  # Below threshold
            reasoning="Uncertain about period accuracy",
            metadata={"period": "uncertain"}
        )
        
        result = await bridge.process_agent_recommendation(recommendation)
        
        assert result["status"] == "review_needed"
        assert result["confidence_score"] == 0.5
    
    @pytest.mark.asyncio
    async def test_generate_shot_recommendations(self, bridge):
        """Test generating shot recommendations."""
        # Create a proper shot list
        shot = GenerativeShot(
            shot_id="rec-test-001",
            shot_number="1A",
            shot_type=ShotType.CLOSEUP,
            shot_description="Close-up of character in emotional moment",
            shot_synopsis="Character realization scene",
            composition=ShotComposition(
                shot_type=ShotType.CLOSEUP,
                shot_angle="eye_level",
                camera_movement="static"
            ),
            lighting=ShotLighting(
                lighting_setup="three_point",
                color_grade_style="warm"
            ),
            audio=ShotAudio(
                audio_design="emotional",
                primary_source="dialogue"
            ),
            requirements=ShotRequirements(
                mood="emotional",
                tone="intimate",
                visual_style="cinematic close-up"
            ),
            generative_prompt={"prompt_text": "Emotional close-up shot"},
            timing=ShotTiming(estimated_duration=3.0)
        )
        
        sequence = type('SequenceStructure', (), {
            'sequence_id': 'seq-001',
            'sequence_name': 'Test Sequence',
            'shots': [shot],
            'calculate_total_duration': lambda: None
        })()
        
        shot_list = GenerativeShotList(
            project_id="rec-test",
            project_name="Recommendation Test",
            story_structure={"type": "test"}
        )
        shot_list.sequences = [sequence]
        
        recommendations = await bridge.generate_shot_recommendations(
            shot_list,
            agent_roles=[AgentRole.DRAMATURG, AgentRole.SHOT_DESIGNER]
        )
        
        assert "dramaturg" in recommendations
        assert "shot_designer" in recommendations
        assert len(recommendations["dramaturg"]) >= 1
        assert len(recommendations["shot_designer"]) >= 1
        
        # Verify recommendation structure
        dramaturg_rec = recommendations["dramaturg"][0]
        assert dramaturg_rec.agent_role == AgentRole.DRAMATURG
        assert dramaturg_rec.confidence_score > 0.0
        assert "scene_notes" in dramaturg_rec.recommendation_data
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, bridge):
        """Test retrieving task status."""
        shot = GenerativeShot(
            shot_id="status-test-001",
            shot_number="1",
            shot_type=ShotType.MEDIUM,
            shot_description="Test shot for status",
            shot_synopsis="Test",
            composition=ShotComposition(
                shot_type=ShotType.MEDIUM,
                shot_angle="eye_level",
                camera_movement="static"
            ),
            lighting=ShotLighting(
                lighting_setup="three_point",
                color_grade_style="natural"
            ),
            audio=ShotAudio(
                audio_design="naturalistic",
                primary_source="dialogue"
            ),
            requirements=ShotRequirements(
                mood="test",
                tone="test",
                visual_style="test"
            ),
            generative_prompt={"prompt_text": "Test"},
            timing=ShotTiming(estimated_duration=4.0)
        )
        
        task_id = await bridge.create_task_from_shot(
            shot=shot,
            agent_role=AgentRole.VFX_SUPERVISOR
        )
        
        retrieved_task = await bridge.get_task_status(task_id)
        assert retrieved_task is not None
        assert retrieved_task.task_id == task_id
        assert retrieved_task.agent_role == AgentRole.VFX_SUPERVISOR
    
    @pytest.mark.asyncio
    async def test_get_recommendations_by_role(self, bridge):
        """Test filtering recommendations by agent role."""
        rec1 = AgentRecommendation(
            recommendation_id="rec-001",
            agent_role=AgentRole.PROP_MASTER,
            task_id="task-001",
            asset_type=AssetType.PROP,
            recommendation_data={"name": "Sword"},
            confidence_score=0.8,
            reasoning="test",
            metadata={}
        )
        
        rec2 = AgentRecommendation(
            recommendation_id="rec-002",
            agent_role=AgentRole.COSTUME_DESIGNER,
            task_id="task-002",
            asset_type=AssetType.WARDROBE,
            recommendation_data={"name": "Cloak"},
            confidence_score=0.9,
            reasoning="test",
            metadata={}
        )
        
        bridge.recommendations.extend([rec1, rec2])
        
        prop_recs = await bridge.get_recommendations_by_role(AgentRole.PROP_MASTER)
        assert len(prop_recs) == 1
        assert prop_recs[0].agent_role == AgentRole.PROP_MASTER
        
        costume_recs = await bridge.get_recommendations_by_role(AgentRole.COSTUME_DESIGNER)
        assert len(costume_recs) == 1
        assert costume_recs[0].agent_role == AgentRole.COSTUME_DESIGNER
    
    @pytest.mark.asyncio
    async def test_export_agent_workflow(self, bridge):
        """Test exporting agent workflow data."""
        shot = GenerativeShot(
            shot_id="export-test-001",
            shot_number="1",
            shot_type=ShotType.WIDE,
            shot_description="Export test shot",
            shot_synopsis="Test",
            composition=ShotComposition(
                shot_type=ShotType.WIDE,
                shot_angle="high_angle",
                camera_movement="static"
            ),
            lighting=ShotLighting(
                lighting_setup="natural",
                color_grade_style="natural"
            ),
            audio=ShotAudio(
                audio_design="atmospheric",
                primary_source="ambient"
            ),
            requirements=ShotRequirements(
                mood="expansive",
                tone="establishing",
                visual_style="wide establishing"
            ),
            generative_prompt={"prompt_text": "Test wide shot"},
            timing=ShotTiming(estimated_duration=8.0)
        )
        
        task_id = await bridge.create_task_from_shot(
            shot=shot,
            agent_role=AgentRole.LOCATION_SCOUT
        )
        
        workflow = await bridge.export_agent_workflow([task_id])
        
        assert "export_timestamp" in workflow
        assert workflow["total_tasks"] == 1
        assert len(workflow["tasks"]) == 1
        assert workflow["tasks"][0]["task_id"] == task_id
        assert workflow["tasks"][0]["agent_role"] == "location_scout"
        assert workflow["tasks"][0]["status"] == "pending"
    
    def test_agent_task_creation(self):
        """Test AgentTask dataclass creation."""
        task = AgentTask(
            task_id="test-task-001",
            agent_role=AgentRole.MUSIC_DIRECTOR,
            task_type=TaskType.STYLE_CONSULTATION,
            context={"scene": "battle", "mood": "epic"},
            assets=[],
            requirements={"tempo": 120, "key": "C minor"},
            priority=8
        )
        
        assert task.task_id == "test-task-001"
        assert task.agent_role == AgentRole.MUSIC_DIRECTOR
        assert task.priority == 8
        assert task.status == "pending"
        assert task.created_at is not None
    
    def test_agent_recommendation_creation(self):
        """Test AgentRecommendation dataclass creation."""
        recommendation = AgentRecommendation(
            recommendation_id="rec-test-001",
            agent_role=AgentRole.SOUND_DESIGNER,
            task_id="task-test-001",
            asset_type=AssetType.SOUND,
            recommendation_data={
                "name": "Ambient Forest",
                "duration": 300.0,
                "loopable": True
            },
            confidence_score=0.92,
            reasoning="Perfect match for forest scene atmosphere",
            metadata={"scene_type": "forest", "time_of_day": "day"}
        )
        
        assert recommendation.recommendation_id == "rec-test-001"
        assert recommendation.agent_role == AgentRole.SOUND_DESIGNER
        assert recommendation.confidence_score == 0.92
        assert recommendation.asset_type == AssetType.SOUND


if __name__ == "__main__":
    pytest.main([__file__, "-v"])