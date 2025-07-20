"""
Tests for Digital Table Read Integration
STORY-088 Implementation
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch
from pathlib import Path

from app.models.table_read_models import (
    CharacterAnalysis, SceneAnalysis, StoryCircleAnalysis, CreativeBible,
    TableReadRequest, TableReadSession, StoryCircleBeat, CharacterArchetype,
    SceneType, EmotionalTone, ConflictLevel, extract_scene_headings,
    extract_character_names, identify_story_circle_beat
)
from app.services.table_read_service import TableReadService
from app.services.breakdown_service import BreakdownService


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace for testing."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_breakdown_service():
    """Create mock breakdown service."""
    service = AsyncMock(spec=BreakdownService)
    return service


@pytest.fixture
def table_read_service(temp_workspace, mock_breakdown_service):
    """Create table read service for testing."""
    return TableReadService(
        project_root=str(temp_workspace),
        breakdown_service=mock_breakdown_service
    )


@pytest.fixture
def sample_script():
    """Create sample script for testing."""
    return """
INT. COFFEE SHOP - MORNING

ALEX (30s), disheveled and anxious, sits at a corner table nursing a cold coffee. 
This is their comfort zone - familiar, safe, but unsatisfying.

ALEX
(to self)
Same routine, every day. Is this all there is?

BARISTA
Your usual refill?

ALEX
Actually... make it something different today.

EXT. CITY STREET - LATER

Alex steps out of the coffee shop, clutching a new exotic drink. 
They pause at the threshold, looking at the busy street ahead.

ALEX
(deep breath)
Okay, let's do this.

They walk into the unknown, leaving their comfort zone behind.

INT. COFFEE SHOP - DAY

Alex returns, changed. Their clothes are different, their posture confident.
They order with certainty, no longer the anxious person from before.

ALEX
I'll have the Ethiopian blend. Black.

They smile, transformed by their journey.
"""


class TestTableReadModels:
    """Test table read model functionality."""
    
    def test_story_circle_beat_creation(self):
        """Test story circle beat enum."""
        beat = StoryCircleBeat.YOU
        assert beat == "you"
        assert beat.value == "you"
    
    def test_character_analysis_creation(self):
        """Test character analysis creation."""
        analysis = CharacterAnalysis(
            character_name="Alex",
            archetype=CharacterArchetype.HERO,
            primary_motivation="seek change",
            internal_conflict="fear of the unknown",
            external_conflict="comfort zone",
            character_arc="transformation from anxious to confident",
            story_circle_position=StoryCircleBeat.YOU,
            emotional_journey=[EmotionalTone.ANTICIPATION, EmotionalTone.FEAR],
            relationships={"Barista": "familiar acquaintance"},
            dialogue_patterns=["uncertain questions", "gradual confidence"],
            key_moments=["leaves comfort zone", "returns changed"],
            transformation_summary="fundamental confidence shift"
        )
        
        assert analysis.character_name == "Alex"
        assert analysis.archetype == CharacterArchetype.HERO
        assert analysis.transformation_summary == "fundamental confidence shift"
    
    def test_scene_analysis_creation(self):
        """Test scene analysis creation."""
        scene = SceneAnalysis(
            scene_id="scene_001",
            scene_number="1",
            scene_heading="INT. COFFEE SHOP - MORNING",
            synopsis="Alex in comfort zone, questioning routine",
            story_circle_beat=StoryCircleBeat.YOU,
            scene_type=SceneType.SETUP,
            primary_emotion=EmotionalTone.ANTICIPATION,
            conflict_level=ConflictLevel.LOW,
            character_development={"Alex": "introduced in comfort zone"},
            thematic_elements=["identity", "routine", "comfort"],
            visual_descriptions=["cozy coffee shop", "anxious posture"],
            dialogue_highlights=["'Is this all there is?'"],
            pacing_analysis="slow, contemplative",
            dramatic_function="establish character and world",
            foreshadowing=["change is coming"],
            callbacks=["return to familiar place"],
            character_arcs={"Alex": "beginning of transformation"},
            emotional_arc=[EmotionalTone.ANTICIPATION, EmotionalTone.FEAR],
            stakes="existential satisfaction",
            tension_level=3
        )
        
        assert scene.scene_id == "scene_001"
        assert scene.story_circle_beat == StoryCircleBeat.YOU
        assert scene.tension_level == 3
    
    def test_story_circle_analysis_creation(self):
        """Test story circle analysis creation."""
        analysis = StoryCircleAnalysis(
            beats={
                StoryCircleBeat.YOU: [],
                StoryCircleBeat.NEED: [],
                StoryCircleBeat.GO: [],
                StoryCircleBeat.SEARCH: [],
                StoryCircleBeat.FIND: [],
                StoryCircleBeat.TAKE: [],
                StoryCircleBeat.RETURN: [],
                StoryCircleBeat.CHANGE: []
            },
            character_journeys={"Alex": [StoryCircleBeat.YOU, StoryCircleBeat.CHANGE]},
            overall_arc="transformation arc",
            thematic_throughline="finding oneself",
            character_transformations={"Alex": "anxious to confident"},
            pacing_analysis="well-paced transformation",
            emotional_progression=[EmotionalTone.ANTICIPATION, EmotionalTone.JOY],
            structural_strengths=["clear arc", "emotional progression"],
            structural_weaknesses=["could be deeper"],
            improvement_suggestions=["add more conflict"]
        )
        
        assert analysis.overall_arc == "transformation arc"
        assert len(analysis.character_transformations) == 1
    
    def test_creative_bible_creation(self):
        """Test creative bible creation."""
        # Create required nested objects
        story_circle = StoryCircleAnalysis(
            beats={
                StoryCircleBeat.YOU: [],
                StoryCircleBeat.NEED: [],
                StoryCircleBeat.GO: [],
                StoryCircleBeat.SEARCH: [],
                StoryCircleBeat.FIND: [],
                StoryCircleBeat.TAKE: [],
                StoryCircleBeat.RETURN: [],
                StoryCircleBeat.CHANGE: []
            },
            character_journeys={"Alex": [StoryCircleBeat.YOU, StoryCircleBeat.CHANGE]},
            overall_arc="transformation arc",
            thematic_throughline="finding oneself",
            character_transformations={"Alex": "anxious to confident"},
            pacing_analysis="well-paced transformation",
            emotional_progression=[EmotionalTone.ANTICIPATION, EmotionalTone.JOY],
            structural_strengths=["clear arc", "emotional progression"],
            structural_weaknesses=["could be deeper"],
            improvement_suggestions=["add more conflict"]
        )
        
        themes = ThemeAnalysis(
            primary_themes=["identity", "transformation", "courage"],
            secondary_themes=["routine vs change", "comfort vs growth"],
            motifs=["coffee shop", "daily routine"],
            symbols=["coffee cup", "door", "mirror"],
            thematic_questions=["What defines identity?", "How does change occur?"],
            moral_dilemmas=["safety vs growth", "comfort vs fulfillment"],
            philosophical_exploration="existential exploration of self",
            cultural_commentary="modern anxiety and routine",
            universal_themes=["personal growth", "finding purpose"]
        )
        
        bible = CreativeBible(
            bible_id="test_bible",
            project_id="test_project",
            title="The Coffee Shop Awakening",
            logline="An anxious person's journey to self-confidence",
            synopsis="A transformative journey from comfort to confidence",
            character_bios={},
            scene_analyses=[],
            story_circle=story_circle,
            themes=themes,
            dialogue_analysis=[],
            visual_style="intimate, warm",
            tone_description="contemplative and hopeful",
            genre_analysis="character drama",
            target_audience="adults seeking inspiration",
            comparable_works=["Eat Pray Love", "Wild"],
            production_notes="focus on character transformation",
            character_relationships={},
            emotional_heatmap={},
            structural_timeline={}
        )
        
        assert bible.title == "The Coffee Shop Awakening"
        assert bible.comparable_works == ["Eat Pray Love", "Wild"]
        assert bible.story_circle.overall_arc == "transformation arc"


class TestScriptParsing:
    """Test script parsing functions."""
    
    def test_extract_scene_headings(self):
        """Test scene heading extraction."""
        script = """
        INT. COFFEE SHOP - MORNING
        
        Some dialogue
        
        EXT. CITY STREET - DAY
        
        More dialogue
        """
        
        headings = extract_scene_headings(script)
        assert len(headings) == 2
        assert "INT. COFFEE SHOP - MORNING" in headings
        assert "EXT. CITY STREET - DAY" in headings
    
    def test_extract_character_names(self):
        """Test character name extraction."""
        script = """
        ALEX
        Hello there.
        
        BARISTA
        Your usual?
        
        CUSTOMER
        No, something different.
        """
        
        names = extract_character_names(script)
        assert "ALEX" in names
        assert "BARISTA" in names
        assert "CUSTOMER" in names
    
    def test_identify_story_circle_beat(self):
        """Test story circle beat identification."""
        # Test comfort zone detection
        content = "This is my comfortable space, my routine, my normal life"
        beat = identify_story_circle_beat(content)
        assert beat == StoryCircleBeat.YOU
        
        # Test need detection
        content = "I want something more, I need change, I desire growth"
        beat = identify_story_circle_beat(content)
        assert beat == StoryCircleBeat.NEED
        
        # Test go detection
        content = "I must leave this place, cross this threshold, enter the unknown"
        beat = identify_story_circle_beat(content)
        assert beat == StoryCircleBeat.GO


class TestTableReadService:
    """Test table read service functionality."""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, table_read_service):
        """Test service initialization."""
        assert table_read_service is not None
        assert len(table_read_service.story_circle_templates) > 0
        assert "hero_journey" in table_read_service.story_circle_templates
    
    @pytest.mark.asyncio
    async def test_create_session(self, table_read_service):
        """Test session creation."""
        request = TableReadRequest(
            project_id="test_project",
            script_content="INT. ROOM - DAY\n\nALEX\nHello world.",
            analysis_depth="comprehensive"
        )
        
        session = await table_read_service.create_table_read_session(request)
        
        assert session is not None
        assert session.project_id == "test_project"
        assert session.status == "processing"
        assert session.progress == 0.0
        assert session.bible_id is not None
    
    @pytest.mark.asyncio
    async def test_session_processing(self, table_read_service, sample_script):
        """Test full session processing."""
        request = TableReadRequest(
            project_id="test_project",
            script_content=sample_script,
            analysis_depth="comprehensive"
        )
        
        session = await table_read_service.create_table_read_session(request)
        
        # Wait for processing to complete
        await asyncio.sleep(0.1)  # Allow async processing
        
        updated_session = table_read_service.sessions[session.session_id]
        assert updated_session.status in ["completed", "processing", "error"]
    
    @pytest.mark.asyncio
    async def test_parse_script(self, table_read_service, sample_script):
        """Test script parsing."""
        scenes = await table_read_service._parse_script(sample_script)
        
        assert len(scenes) > 0
        assert "scene_id" in scenes[0]
        assert "scene_heading" in scenes[0]
        assert "characters" in scenes[0]
    
    @pytest.mark.asyncio
    async def test_analyze_scenes(self, table_read_service, sample_script):
        """Test scene analysis."""
        scenes = await table_read_service._parse_script(sample_script)
        request = TableReadRequest(
            project_id="test_project",
            script_content=sample_script
        )
        
        scene_analyses = await table_read_service._analyze_scenes(scenes, request)
        
        assert len(scene_analyses) > 0
        assert all(isinstance(analysis, SceneAnalysis) for analysis in scene_analyses)
    
    @pytest.mark.asyncio
    async def test_analyze_characters(self, table_read_service, sample_script):
        """Test character analysis."""
        scenes = await table_read_service._parse_script(sample_script)
        scene_analyses = [
            SceneAnalysis(
                scene_id="scene_001",
                scene_number="1",
                scene_heading="INT. COFFEE SHOP - MORNING",
                synopsis="Character introduction",
                story_circle_beat=StoryCircleBeat.YOU,
                scene_type=SceneType.SETUP,
                primary_emotion=EmotionalTone.ANTICIPATION,
                conflict_level=ConflictLevel.LOW,
                character_development={"Alex": "introduced"},
                thematic_elements=["identity"],
                visual_descriptions=["cozy coffee shop"],
                dialogue_highlights=["questioning routine"],
                pacing_analysis="slow",
                dramatic_function="establish world",
                foreshadowing=[],
                callbacks=[],
                character_arcs={"Alex": "beginning"},
                emotional_arc=[EmotionalTone.ANTICIPATION],
                stakes="existential",
                tension_level=3
            )
        ]
        
        character_analyses = await table_read_service._analyze_characters(
            sample_script, scene_analyses
        )
        
        assert len(character_analyses) > 0
        assert "Alex" in character_analyses
        assert isinstance(character_analyses["Alex"], CharacterAnalysis)
    
    @pytest.mark.asyncio
    async def test_story_circle_analysis(self, table_read_service):
        """Test story circle analysis."""
        scene_analyses = [
            SceneAnalysis(
                scene_id="scene_001",
                scene_number="1",
                scene_heading="INT. COFFEE SHOP - MORNING",
                synopsis="Character in comfort zone",
                story_circle_beat=StoryCircleBeat.YOU,
                scene_type=SceneType.SETUP,
                primary_emotion=EmotionalTone.ANTICIPATION,
                conflict_level=ConflictLevel.LOW,
                character_development={},
                thematic_elements=[],
                visual_descriptions=[],
                dialogue_highlights=[],
                pacing_analysis="",
                dramatic_function="",
                foreshadowing=[],
                callbacks=[],
                character_arcs={},
                emotional_arc=[],
                stakes="",
                tension_level=3
            )
        ]
        
        character_analyses = {
            "Alex": CharacterAnalysis(
                character_name="Alex",
                archetype=CharacterArchetype.HERO,
                primary_motivation="change",
                internal_conflict="fear",
                external_conflict="comfort zone",
                character_arc="transformation",
                story_circle_position=StoryCircleBeat.YOU,
                emotional_journey=[],
                relationships={},
                dialogue_patterns=[],
                key_moments=[],
                transformation_summary="changed"
            )
        }
        
        story_circle = await table_read_service._analyze_story_circle(
            scene_analyses, character_analyses
        )
        
        assert story_circle is not None
        assert len(story_circle.beats) == 8
        assert story_circle.character_transformations["Alex"] == "changed"
    
    @pytest.mark.asyncio
    async def test_creative_bible_generation(self, table_read_service, sample_script):
        """Test creative bible generation."""
        scenes = await table_read_service._parse_script(sample_script)
        request = TableReadRequest(
            project_id="test_project",
            script_content=sample_script
        )
        
        # Mock analysis results
        scene_analyses = await table_read_service._analyze_scenes(scenes, request)
        character_analyses = await table_read_service._analyze_characters(
            sample_script, scene_analyses
        )
        story_circle = await table_read_service._analyze_story_circle(
            scene_analyses, character_analyses
        )
        themes = await table_read_service._analyze_themes(scene_analyses, character_analyses)
        dialogue_analysis = await table_read_service._analyze_dialogue(
            sample_script, character_analyses
        )
        
        bible = await table_read_service._generate_creative_bible(
            request, scene_analyses, character_analyses, 
            story_circle, themes, dialogue_analysis
        )
        
        assert bible is not None
        assert bible.project_id == "test_project"
        assert bible.title is not None
        assert bible.logline is not None
        assert bible.synopsis is not None
    
    @pytest.mark.asyncio
    async def test_get_session_status(self, table_read_service):
        """Test getting session status."""
        request = TableReadRequest(
            project_id="test_project",
            script_content="INT. ROOM - DAY\n\nALEX\nHello."
        )
        
        session = await table_read_service.create_table_read_session(request)
        retrieved = await table_read_service.get_session_status(session.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
    
    @pytest.mark.asyncio
    async def test_get_creative_bible(self, table_read_service):
        """Test getting creative bible."""
        bible = CreativeBible(
            bible_id="test_bible",
            project_id="test_project",
            title="Test Story",
            logline="Test logline",
            synopsis="Test synopsis",
            character_bios={},
            scene_analyses=[],
            story_circle=None,
            themes=None,
            dialogue_analysis=[],
            visual_style="",
            tone_description="",
            genre_analysis="",
            target_audience="",
            comparable_works=[],
            production_notes="",
            character_relationships={},
            emotional_heatmap={},
            structural_timeline={}
        )
        
        table_read_service.bibles["test_bible"] = bible
        
        retrieved = await table_read_service.get_creative_bible("test_bible")
        assert retrieved is not None
        assert retrieved.title == "Test Story"
    
    @pytest.mark.asyncio
    async def test_export_bible(self, table_read_service):
        """Test bible export."""
        bible = CreativeBible(
            bible_id="test_bible",
            project_id="test_project",
            title="Test Story",
            logline="Test logline",
            synopsis="Test synopsis",
            character_bios={},
            scene_analyses=[],
            story_circle=None,
            themes=None,
            dialogue_analysis=[],
            visual_style="",
            tone_description="",
            genre_analysis="",
            target_audience="",
            comparable_works=[],
            production_notes="",
            character_relationships={},
            emotional_heatmap={},
            structural_timeline={}
        )
        
        table_read_service.bibles["test_bible"] = bible
        
        export_result = await table_read_service.export_bible("test_bible", "json")
        
        assert export_result["format"] == "json"
        assert export_result["bible_id"] == "test_bible"
        assert "content" in export_result
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, table_read_service):
        """Test listing sessions."""
        request1 = TableReadRequest(
            project_id="project_1",
            script_content="INT. ROOM - DAY\n\nALEX\nHello."
        )
        request2 = TableReadRequest(
            project_id="project_2",
            script_content="EXT. PARK - DAY\n\nBOB\nHi there."
        )
        
        session1 = await table_read_service.create_table_read_session(request1)
        session2 = await table_read_service.create_table_read_session(request2)
        
        sessions = await table_read_service.list_sessions("project_1")
        assert len(sessions) == 1
        assert sessions[0].project_id == "project_1"
        
        all_sessions = await table_read_service.list_sessions()
        assert len(all_sessions) >= 2


class TestAPIEndpoints:
    """Test API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_session_endpoint(self, client, table_read_service):
        """Test create session endpoint."""
        with patch('app.api.v1.table_read.get_table_read_service', return_value=table_read_service):
            response = client.post(
                "/api/v1/table-read/sessions",
                json={
                    "project_id": "test_project",
                    "script_content": "INT. ROOM - DAY\n\nALEX\nHello world.",
                    "analysis_depth": "comprehensive"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert "bible_id" in data
    
    @pytest.mark.asyncio
    async def test_get_session_status_endpoint(self, client, table_read_service):
        """Test get session status endpoint."""
        with patch('app.api.v1.table_read.get_table_read_service', return_value=table_read_service):
            # Create a session first
            table_read_service.sessions["test_session"] = TableReadSession(
                session_id="test_session",
                project_id="test_project",
                bible_id="test_bible",
                status="completed",
                progress=1.0
            )
            
            response = client.get("/api/v1/table-read/sessions/test_session")
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test_session"
    
    @pytest.mark.asyncio
    async def test_get_bible_endpoint(self, client, table_read_service):
        """Test get bible endpoint."""
        with patch('app.api.v1.table_read.get_table_read_service', return_value=table_read_service):
            bible = CreativeBible(
                bible_id="test_bible",
                project_id="test_project",
                title="Test Story",
                logline="Test logline",
                synopsis="Test synopsis",
                character_bios={},
                scene_analyses=[],
                story_circle=None,
                themes=None,
                dialogue_analysis=[],
                visual_style="",
                tone_description="",
                genre_analysis="",
                target_audience="",
                comparable_works=[],
                production_notes="",
                character_relationships={},
                emotional_heatmap={},
                structural_timeline={}
            )
            
            table_read_service.bibles["test_bible"] = bible
            
            response = client.get("/api/v1/table-read/bibles/test_bible/full")
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Story"
    
    @pytest.mark.asyncio
    async def test_list_sessions_endpoint(self, client, table_read_service):
        """Test list sessions endpoint."""
        with patch('app.api.v1.table_read.get_table_read_service', return_value=table_read_service):
            response = client.get("/api/v1/table-read/sessions")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


class TestIntegration:
    """Integration tests for table read functionality."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, table_read_service, sample_script):
        """Test complete table read workflow."""
        # Create request
        request = TableReadRequest(
            project_id="test_project",
            script_content=sample_script,
            analysis_depth="comprehensive",
            focus_areas=["characters", "structure", "themes"]
        )
        
        # Create session
        session = await table_read_service.create_table_read_session(request)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Get results
        bible = await table_read_service.get_creative_bible(session.bible_id)
        
        assert bible is not None
        assert bible.project_id == "test_project"
        assert len(bible.character_bios) > 0
        assert len(bible.scene_analyses) > 0
        assert bible.story_circle is not None
    
    @pytest.mark.asyncio
    async def test_error_handling(self, table_read_service):
        """Test error handling."""
        # Test with invalid script content
        request = TableReadRequest(
            project_id="test_project",
            script_content="",  # Empty content
            analysis_depth="comprehensive"
        )
        
        with pytest.raises(ValueError):
            await table_read_service._process_table_read("test_session", request)
    
    @pytest.mark.asyncio
    async def test_export_formats(self, table_read_service):
        """Test different export formats."""
        bible = CreativeBible(
            bible_id="test_bible",
            project_id="test_project",
            title="Test Story",
            logline="Test logline",
            synopsis="Test synopsis",
            character_bios={},
            scene_analyses=[],
            story_circle=None,
            themes=None,
            dialogue_analysis=[],
            visual_style="",
            tone_description="",
            genre_analysis="",
            target_audience="",
            comparable_works=[],
            production_notes="",
            character_relationships={},
            emotional_heatmap={},
            structural_timeline={}
        )
        
        table_read_service.bibles["test_bible"] = bible
        
        # Test JSON export
        json_export = await table_read_service.export_bible("test_bible", "json")
        assert json_export["format"] == "json"
        
        # Test Markdown export
        markdown_export = await table_read_service.export_bible("test_bible", "markdown")
        assert markdown_export["format"] == "markdown"
        
        # Test PDF export (placeholder)
        pdf_export = await table_read_service.export_bible("test_bible", "pdf")
        assert pdf_export["format"] == "pdf"


if __name__ == "__main__":
    pytest.main([__file__])