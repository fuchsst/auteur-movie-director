"""
Comprehensive tests for STORY-084: Structured GenerativeShotList Schema
Tests shot list creation, validation, and export functionality.
"""

import pytest
import json
import uuid
from datetime import datetime

from app.models.generative_shotlist import (
    GenerativeShotList, GenerativeShot, SequenceStructure, ShotType, 
    ShotRequirements, ShotComposition, ShotTiming, ShotAssets, 
    ShotLighting, ShotAudio, CameraMovement, ShotAngle, ColorGradeStyle,
    create_shot_list_from_structure, validate_shot_list_json
)


class TestGenerativeShotModels:
    """Test individual shot model components"""
    
    def test_shot_composition_creation(self):
        """Test creating shot composition"""
        composition = ShotComposition(
            shot_type=ShotType.CLOSEUP,
            shot_angle=ShotAngle.EYE_LEVEL,
            camera_movement=CameraMovement.STATIC
        )
        
        assert composition.shot_type == ShotType.CLOSEUP
        assert composition.shot_angle == ShotAngle.EYE_LEVEL
        assert composition.camera_movement == CameraMovement.STATIC
    
    def test_shot_timing_creation(self):
        """Test creating shot timing"""
        timing = ShotTiming(
            estimated_duration=5.5,
            target_duration=5.0,
            min_duration=4.0,
            max_duration=7.0
        )
        
        assert timing.estimated_duration == 5.5
        assert timing.target_duration == 5.0
        assert timing.can_be_parallel is False
    
    def test_shot_lighting_creation(self):
        """Test creating shot lighting"""
        lighting = ShotLighting(
            lighting_setup="three_point",
            color_grade_style=ColorGradeStyle.NATURAL,
            key_light_intensity=1.2,
            color_temperature=3200
        )
        
        assert lighting.lighting_setup == "three_point"
        assert lighting.color_grade_style == ColorGradeStyle.NATURAL
        assert lighting.key_light_intensity == 1.2
    
    def test_shot_audio_creation(self):
        """Test creating shot audio"""
        audio = ShotAudio(
            audio_design="naturalistic",
            primary_source="on_set_recording",
            dialogue=True,
            music=False,
            ambient=True
        )
        
        assert audio.audio_design == "naturalistic"
        assert audio.primary_source == "on_set_recording"
        assert audio.dialogue is True
        assert audio.music is False
    
    def test_generative_shot_creation(self):
        """Test creating a complete generative shot"""
        shot = GenerativeShot(
            shot_id="shot-001",
            shot_number="1A",
            shot_type=ShotType.CLOSEUP,
            shot_description="Close-up of protagonist's face showing determination",
            shot_synopsis="Protagonist resolves to take action",
            composition=ShotComposition(
                shot_type=ShotType.CLOSEUP,
                shot_angle=ShotAngle.EYE_LEVEL,
                camera_movement=CameraMovement.STATIC
            ),
            lighting=ShotLighting(
                lighting_setup="three_point",
                color_grade_style=ColorGradeStyle.WARM,
                key_light_intensity=1.0
            ),
            audio=ShotAudio(
                audio_design="emotional",
                primary_source="dialogue",
                dialogue=True,
                ambient=True
            ),
            requirements=ShotRequirements(
                mood="determined",
                tone="intense",
                visual_style="cinematic close-up"
            ),
            generative_prompt={"prompt_text": "Close-up of determined character, warm lighting, cinematic quality"},
            timing=ShotTiming(estimated_duration=3.5)
        )
        
        assert shot.shot_id == "shot-001"
        assert shot.shot_number == "1A"
        assert shot.composition.shot_type == ShotType.CLOSEUP
        assert shot.timing.estimated_duration == 3.5


class TestSequenceStructure:
    """Test sequence organization"""
    
    def test_sequence_creation(self):
        """Test creating a sequence"""
        sequence = SequenceStructure(
            sequence_id="seq-001",
            sequence_name="Opening Sequence",
            sequence_description="Establishing the world and protagonist"
        )
        
        assert sequence.sequence_id == "seq-001"
        assert sequence.sequence_name == "Opening Sequence"
        assert len(sequence.shots) == 0
    
    def test_sequence_with_shots(self):
        """Test sequence with shots"""
        shot = GenerativeShot(
            shot_id="shot-001",
            shot_number="1",
            shot_type=ShotType.ESTABLISHING,
            shot_description="Wide establishing shot of the city",
            shot_synopsis="Set the scene",
            composition=ShotComposition(
                shot_type=ShotType.ESTABLISHING,
                shot_angle=ShotAngle.BIRDSEYE,
                camera_movement=CameraMovement.DRONE
            ),
            lighting=ShotLighting(
                lighting_setup="natural",
                color_grade_style=ColorGradeStyle.NATURAL
            ),
            audio=ShotAudio(
                audio_design="atmospheric",
                primary_source="ambient"
            ),
            requirements=ShotRequirements(
                mood="expansive",
                tone="establishing",
                visual_style="cinematic wide shot"
            ),
            generative_prompt={"prompt_text": "Wide aerial city establishing shot"},
            timing=ShotTiming(estimated_duration=8.0)
        )
        
        sequence = SequenceStructure(
            sequence_id="seq-001",
            sequence_name="Opening",
            sequence_description="Opening sequence",
            shots=[shot],
            shot_order=["shot-001"]
        )
        sequence.calculate_total_duration()
        
        assert len(sequence.shots) == 1
        assert sequence.shot_order == ["shot-001"]
        assert sequence.total_duration == 8.0


class TestGenerativeShotList:
    """Test complete shot list functionality"""
    
    @pytest.fixture
    def sample_shot_list(self):
        """Create a sample shot list for testing"""
        return GenerativeShotList(
            project_id="proj-001",
            project_name="Test Project",
            story_structure={"description": "Three-act story structure"}
        )
    
    def test_shot_list_creation(self, sample_shot_list):
        """Test creating a shot list"""
        assert sample_shot_list.project_id == "proj-001"
        assert sample_shot_list.project_name == "Test Project"
        assert sample_shot_list.total_shots == 0
        assert sample_shot_list.is_valid is True
    
    def test_add_sequence_to_shot_list(self, sample_shot_list):
        """Test adding sequences to shot list"""
        sequence = SequenceStructure(
            sequence_id="seq-001",
            sequence_name="Test Sequence",
            sequence_description="A test sequence"
        )
        
        sample_shot_list.sequences.append(sequence)
        sample_shot_list.calculate_totals()
        
        assert sample_shot_list.total_sequences == 1
        assert sample_shot_list.sequences[0] == sequence
    
    def test_add_shot_to_sequence(self, sample_shot_list):
        """Test adding shots to sequences"""
        shot = GenerativeShot(
            shot_id="shot-001",
            shot_number="1",
            shot_type=ShotType.MEDIUM,
            shot_description="Medium shot of character",
            shot_synopsis="Character introduction",
            composition=ShotComposition(
                shot_type=ShotType.MEDIUM,
                shot_angle=ShotAngle.EYE_LEVEL,
                camera_movement=CameraMovement.STATIC
            ),
            lighting=ShotLighting(
                lighting_setup="three_point",
                color_grade_style=ColorGradeStyle.NATURAL
            ),
            audio=ShotAudio(
                audio_design="naturalistic",
                primary_source="dialogue"
            ),
            requirements=ShotRequirements(
                mood="neutral",
                tone="conversational",
                visual_style="standard medium shot"
            ),
            generative_prompt={"prompt_text": "Standard medium shot"},
            timing=ShotTiming(estimated_duration=4.0)
        )
        
        sequence = SequenceStructure(
            sequence_id="seq-001",
            sequence_name="Character Introduction",
            sequence_description="Introducing the main character",
            shots=[shot],
            shot_order=["shot-001"]
        )
        
        sample_shot_list.sequences.append(sequence)
        sample_shot_list.calculate_totals()
        
        assert sample_shot_list.total_shots == 1
        assert sample_shot_list.total_duration == 4.0
    
    def test_get_shot_by_id(self, sample_shot_list):
        """Test retrieving shots by ID"""
        shot = GenerativeShot(
            shot_id="shot-001",
            shot_number="1",
            shot_type=ShotType.CLOSEUP,
            shot_description="Close-up shot",
            shot_synopsis="Emotional moment",
            composition=ShotComposition(
                shot_type=ShotType.CLOSEUP,
                shot_angle=ShotAngle.EYE_LEVEL,
                camera_movement=CameraMovement.STATIC
            ),
            lighting=ShotLighting(
                lighting_setup="three_point",
                color_grade_style=ColorGradeStyle.WARM
            ),
            audio=ShotAudio(
                audio_design="emotional",
                primary_source="dialogue"
            ),
            requirements=ShotRequirements(
                mood="emotional",
                tone="intimate",
                visual_style="intimate close-up"
            ),
            generative_prompt={"prompt_text": "Emotional close-up"},
            timing=ShotTiming(estimated_duration=3.0)
        )
        
        sequence = SequenceStructure(
            sequence_id="seq-001",
            sequence_name="Emotional Scene",
            sequence_description="Character's emotional moment",
            shots=[shot],
            shot_order=["shot-001"]
        )
        
        sample_shot_list.sequences.append(sequence)
        
        retrieved_shot = sample_shot_list.get_shot_by_id("shot-001")
        assert retrieved_shot is not None
        assert retrieved_shot.shot_id == "shot-001"
    
    def test_validate_shot_list(self, sample_shot_list):
        """Test shot list validation"""
        # Valid shot list
        assert sample_shot_list.validate_shot_list() is True
        assert len(sample_shot_list.validation_errors) == 0
        
        # Create a shot with duplicate ID
        shot1 = GenerativeShot(
            shot_id="shot-001",
            shot_number="1",
            shot_type=ShotType.CLOSEUP,
            shot_description="First shot",
            shot_synopsis="First shot action",
            composition=ShotComposition(
                shot_type=ShotType.CLOSEUP,
                shot_angle=ShotAngle.EYE_LEVEL,
                camera_movement=CameraMovement.STATIC
            ),
            lighting=ShotLighting(
                lighting_setup="three_point",
                color_grade_style=ColorGradeStyle.NATURAL
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
            generative_prompt={"prompt_text": "Test shot 1"},
            timing=ShotTiming(estimated_duration=3.0)
        )
        
        shot2 = GenerativeShot(
            shot_id="shot-001",  # Duplicate ID
            shot_number="2",
            shot_type=ShotType.MEDIUM,
            shot_description="Second shot",
            shot_synopsis="Second shot action",
            composition=ShotComposition(
                shot_type=ShotType.MEDIUM,
                shot_angle=ShotAngle.EYE_LEVEL,
                camera_movement=CameraMovement.STATIC
            ),
            lighting=ShotLighting(
                lighting_setup="three_point",
                color_grade_style=ColorGradeStyle.NATURAL
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
            generative_prompt={"prompt_text": "Test shot 2"},
            timing=ShotTiming(estimated_duration=4.0)
        )
        
        sequence = SequenceStructure(
            sequence_id="seq-test",
            sequence_name="Test Sequence",
            sequence_description="Sequence with duplicate shot IDs",
            shots=[shot1, shot2],
            shot_order=["shot-001", "shot-001"]
        )
        
        sample_shot_list.sequences.append(sequence)
        
        # Should detect duplicate shot IDs
        result = sample_shot_list.validate_shot_list()
        assert result is False
        assert len(sample_shot_list.validation_errors) > 0
        assert "Duplicate shot IDs found" in sample_shot_list.validation_errors
    
    def test_export_to_json(self, sample_shot_list):
        """Test JSON export"""
        shot = GenerativeShot(
            shot_id="shot-001",
            shot_number="1",
            shot_type=ShotType.MEDIUM,
            shot_description="Test export shot",
            shot_synopsis="Export test",
            composition=ShotComposition(
                shot_type=ShotType.MEDIUM,
                shot_angle=ShotAngle.EYE_LEVEL,
                camera_movement=CameraMovement.STATIC
            ),
            lighting=ShotLighting(
                lighting_setup="three_point",
                color_grade_style=ColorGradeStyle.NATURAL
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
            generative_prompt={"prompt_text": "Test export"},
            timing=ShotTiming(estimated_duration=5.0)
        )
        
        sequence = SequenceStructure(
            sequence_id="seq-001",
            sequence_name="Export Test",
            sequence_description="Testing export",
            shots=[shot],
            shot_order=["shot-001"]
        )
        
        sample_shot_list.sequences.append(sequence)
        
        json_export = sample_shot_list.export_to_json()
        assert json_export is not None
        assert "shot-001" in json_export
        assert "seq-001" in json_export
    
    def test_export_to_csv(self, sample_shot_list):
        """Test CSV export"""
        shot = GenerativeShot(
            shot_id="shot-001",
            shot_number="1",
            shot_type=ShotType.WIDE,
            shot_description="CSV export test",
            shot_synopsis="CSV test",
            composition=ShotComposition(
                shot_type=ShotType.WIDE,
                shot_angle=ShotAngle.HIGH_ANGLE,
                camera_movement=CameraMovement.STATIC
            ),
            lighting=ShotLighting(
                lighting_setup="natural",
                color_grade_style=ColorGradeStyle.NATURAL
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
            generative_prompt={"prompt_text": "CSV export test"},
            timing=ShotTiming(estimated_duration=8.0)
        )
        
        sequence = SequenceStructure(
            sequence_id="seq-001",
            sequence_name="CSV Test",
            sequence_description="CSV export test",
            shots=[shot],
            shot_order=["shot-001"]
        )
        
        sample_shot_list.sequences.append(sequence)
        
        csv_export = sample_shot_list.export_to_csv()
        assert csv_export is not None
        assert "shot_id" in csv_export
        assert "shot-001" in csv_export


class TestFactoryFunctions:
    """Test factory functions for shot list creation"""
    
    def test_create_from_structure(self):
        """Test creating shot list from structure"""
        story_structure = {
            "acts": "3 acts",
            "scenes": "15 scenes",
            "characters": "2 main characters",
            "locations": "2 primary locations",
            "type": "three_act"
        }
        
        shot_list = create_shot_list_from_structure(
            project_id="test-001",
            project_name="Test Project",
            story_structure=story_structure
        )
        
        assert shot_list.project_id == "test-001"
        assert shot_list.story_structure == story_structure
        assert shot_list.total_shots == 0
    
    def test_validate_shot_list_json(self):
        """Test JSON validation"""
        # Valid JSON
        valid_data = {
            "project_id": "test-001",
            "project_name": "Test Project",
            "sequences": [],
            "standalone_shots": []
        }
        
        valid_json = json.dumps(valid_data)
        assert validate_shot_list_json(valid_json) is True
        
        # Invalid JSON
        invalid_json = '{"invalid": "data"}'
        assert validate_shot_list_json(invalid_json) is False


class TestComplexShotList:
    """Test complex shot list scenarios"""
    
    def test_three_act_structure(self):
        """Test creating shot list for three-act structure"""
        shot_list = GenerativeShotList(
            project_id="three-act-test",
            project_name="Three Act Structure Test",
            story_structure={
                "structure_type": "three_act",
                "total_scenes": 12,
                "act_1": "setup",
                "act_2": "confrontation",
                "act_3": "resolution"
            }
        )
        
        # Create sequences for each act
        acts = ["act_1", "act_2", "act_3"]
        scenes_per_act = [3, 6, 3]
        
        for i, act_name in enumerate(acts):
            act_num = i + 1
            scenes_count = scenes_per_act[i]
            purpose = shot_list.story_structure[act_name]
            
            sequence = SequenceStructure(
                sequence_id=f"seq-{act_name}",
                sequence_name=f"Act {act_num}",
                sequence_description=purpose,
                act=act_name
            )
            
            # Create shots for each scene
            for scene_num in range(1, scenes_count + 1):
                shot = GenerativeShot(
                    shot_id=f"{act_name}-scene-{scene_num}",
                    shot_number=f"{act_num}{scene_num}",
                    shot_type=ShotType.ESTABLISHING if scene_num == 1 else ShotType.MEDIUM,
                    shot_description=f"Scene {scene_num} in {act_name}",
                    shot_synopsis=f"Scene {scene_num} action",
                    composition=ShotComposition(
                        shot_type=ShotType.ESTABLISHING,
                        shot_angle=ShotAngle.EYE_LEVEL,
                        camera_movement=CameraMovement.STATIC
                    ),
                    lighting=ShotLighting(
                        lighting_setup="three_point",
                        color_grade_style=ColorGradeStyle.NATURAL
                    ),
                    audio=ShotAudio(
                        audio_design="naturalistic",
                        primary_source="dialogue"
                    ),
                    requirements=ShotRequirements(
                        mood="varies",
                        tone="story-driven",
                        visual_style="cinematic"
                    ),
                    generative_prompt={"prompt_text": f"Scene {scene_num}"},
                    timing=ShotTiming(estimated_duration=5.0 + scene_num)
                )
                sequence.shots.append(shot)
                sequence.shot_order.append(shot.shot_id)
            
            shot_list.sequences.append(sequence)
        
        shot_list.calculate_totals()
        
        assert shot_list.total_sequences == 3
        assert shot_list.total_shots == 12
        assert shot_list.total_duration == 93.0  # Sum of (6+7+8) + (7+8+9+10+11+12) + (7+8+9)
    
    def test_character_arc_shots(self):
        """Test creating shots for character development"""
        shot_list = GenerativeShotList(
            project_id="character-arc",
            project_name="Character Arc Test",
            story_structure={
                "structure_type": "character_arc",
                "total_states": 4,
                "description": "Character development arc"
            }
        )
        
        states = ["intro", "conflict", "growth", "resolution"]
        for i, state in enumerate(states):
            shot = GenerativeShot(
                shot_id=f"char-{state}",
                shot_number=str(i + 1),
                shot_type=ShotType.CLOSEUP if state in ["intro", "resolution"] else ShotType.MEDIUM,
                shot_description=f"Character in {state} state",
                shot_synopsis=f"Character {state} moment",
                composition=ShotComposition(
                    shot_type=ShotType.CLOSEUP,
                    shot_angle=ShotAngle.EYE_LEVEL,
                    camera_movement=CameraMovement.STATIC
                ),
                lighting=ShotLighting(
                    lighting_setup="three_point",
                    color_grade_style=ColorGradeStyle.WARM if state == "resolution" else ColorGradeStyle.COOL
                ),
                audio=ShotAudio(
                    audio_design="emotional",
                    primary_source="dialogue"
                ),
                requirements=ShotRequirements(
                    mood=state,
                    tone=state,
                    visual_style=f"character_{state}"
                ),
                generative_prompt={"prompt_text": f"Character {state}"},
                timing=ShotTiming(estimated_duration=4.0)
            )
            
            shot_list.standalone_shots.append(shot)
        
        shot_list.calculate_totals()
        
        assert shot_list.total_shots == 4
        assert shot_list.total_duration == 16.0
        assert len(shot_list.sequences) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])