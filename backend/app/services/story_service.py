from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json
import uuid
from datetime import datetime

from app.models.story_models import (
    SceneTimeline, StoryBeat, CharacterArc,
    NarrativeAnalytics, StoryStructureValidation
)
from app.models.story_structure import Scene, Character, StoryBeat as StoryBeatModel
from app.models.asset_types import Asset
from app.models.scene_breakdown import SceneBreakdown

class StoryService:
    def __init__(self, db: Session):
        self.db = db

    async def generate_timeline(self, project_id: str) -> Dict[str, Any]:
        """Generate comprehensive story timeline with scenes, beats, and character arcs."""
        
        # Get all scenes for the project
        scenes = self.db.query(Scene).filter(
            Scene.project_id == project_id
        ).order_by(Scene.position).all()

        # Get story beats
        beats = self.db.query(StoryBeatModel).filter(
            StoryBeatModel.project_id == project_id
        ).order_by(StoryBeatModel.position).all()

        # Get character arcs
        characters = self.db.query(Character).filter(
            Character.project_id == project_id
        ).all()

        # Generate timeline data
        timeline_data = {
            "scenes": [
                {
                    "id": scene.id,
                    "title": scene.title,
                    "description": scene.description,
                    "startPosition": scene.position / len(scenes) if scenes else 0,
                    "duration": scene.estimated_duration or 2.5,
                    "characters": [c.name for c in scene.characters],
                    "assetCount": len(scene.assets),
                    "emotionalIntensity": self._calculate_emotional_intensity(scene),
                    "beatType": self._get_beat_type(scene),
                    "storyPosition": scene.position,
                    "metadata": {
                        "location": scene.location or "Unknown",
                        "timeOfDay": scene.time_of_day or "Day",
                        "mood": scene.mood or "Neutral",
                        "status": scene.status or "planned"
                    }
                }
                for scene in scenes
            ],
            "beats": [
                {
                    "id": beat.id,
                    "name": beat.name,
                    "type": beat.type,
                    "position": beat.position,
                    "description": beat.description,
                    "emotionalGoal": beat.emotional_goal,
                    "keywords": beat.keywords or [],
                    "scenes": beat.scene_ids or []
                }
                for beat in beats
            ],
            "characterArcs": await self.get_character_arcs(project_id)
        }

        return timeline_data

    async def get_story_beats(self, project_id: str) -> List[Dict[str, Any]]:
        """Get organized story beats by framework."""
        beats = self.db.query(StoryBeatModel).filter(
            StoryBeatModel.project_id == project_id
        ).order_by(StoryBeatModel.position).all()

        return [
            {
                "id": beat.id,
                "name": beat.name,
                "type": beat.type,
                "position": beat.position,
                "description": beat.description,
                "emotionalGoal": beat.emotional_goal,
                "keywords": beat.keywords or []
            }
            for beat in beats
        ]

    async def get_character_arcs(self, project_id: str) -> List[Dict[str, Any]]:
        """Generate character arc data for all characters."""
        characters = self.db.query(Character).filter(
            Character.project_id == project_id
        ).all()

        arcs = []
        for character in characters:
            # Get character's scenes
            scenes = self.db.query(Scene).filter(
                Scene.project_id == project_id,
                Scene.characters.contains(character)
            ).order_by(Scene.position).all()

            if not scenes:
                continue

            # Generate arc points
            points = []
            for i, scene in enumerate(scenes):
                # Calculate emotional arc based on scene data
                emotional_arc = self._calculate_character_emotional_arc(character, scene)
                
                points.append({
                    "position": scene.position / len(scenes),
                    "emotionalArc": emotional_arc,
                    "sceneId": scene.id,
                    "description": f"{character.name}'s emotional state in {scene.title}"
                })

            # Calculate arc metrics
            if points:
                start_emotion = points[0]["emotionalArc"]
                end_emotion = points[-1]["emotionalArc"]
                
                # Determine arc type
                if end_emotion > start_emotion + 0.3:
                    arc_type = "positive"
                elif end_emotion < start_emotion - 0.3:
                    arc_type = "negative"
                elif abs(end_emotion - start_emotion) < 0.2:
                    arc_type = "flat"
                else:
                    arc_type = "complex"

                # Calculate consistency and development scores
                consistency_score = self._calculate_consistency_score(character, scenes)
                development_score = abs(end_emotion - start_emotion)

                arcs.append({
                    "id": character.id,
                    "name": character.name,
                    "color": self._get_character_color(character.id),
                    "points": points,
                    "arcType": arc_type,
                    "consistencyScore": consistency_score,
                    "developmentScore": development_score
                })

        return arcs

    async def validate_structure(self, project_id: str, framework: str = "three_act") -> Dict[str, Any]:
        """Validate story structure against selected framework."""
        
        scenes = self.db.query(Scene).filter(
            Scene.project_id == project_id
        ).order_by(Scene.position).all()

        beats = self.db.query(StoryBeatModel).filter(
            StoryBeatModel.project_id == project_id
        ).order_by(StoryBeatModel.position).all()

        # Framework definitions
        frameworks = {
            "three_act": {
                "acts": [
                    {"name": "Act I: Setup", "type": "setup", "start": 0, "end": 0.25},
                    {"name": "Act II: Confrontation", "type": "confrontation", "start": 0.25, "end": 0.75},
                    {"name": "Act III: Resolution", "type": "resolution", "start": 0.75, "end": 1.0}
                ],
                "plot_points": [
                    {"name": "Hook", "expected_position": 0.0},
                    {"name": "Inciting Incident", "expected_position": 0.12},
                    {"name": "Plot Point 1", "expected_position": 0.25},
                    {"name": "Midpoint", "expected_position": 0.5},
                    {"name": "Plot Point 2", "expected_position": 0.75},
                    {"name": "Climax", "expected_position": 0.9},
                    {"name": "Resolution", "expected_position": 1.0}
                ]
            },
            "blake_snyder": {
                "beats": [
                    {"name": "Opening Image", "expected_position": 0.0},
                    {"name": "Theme Stated", "expected_position": 0.05},
                    {"name": "Catalyst", "expected_position": 0.1},
                    {"name": "Debate", "expected_position": 0.12},
                    {"name": "Break into Two", "expected_position": 0.2},
                    {"name": "Fun and Games", "expected_position": 0.3},
                    {"name": "Midpoint", "expected_position": 0.5},
                    {"name": "Bad Guys Close In", "expected_position": 0.55},
                    {"name": "All Is Lost", "expected_position": 0.75},
                    {"name": "Dark Night of the Soul", "expected_position": 0.8},
                    {"name": "Break into Three", "expected_position": 0.85},
                    {"name": "Finale", "expected_position": 0.9},
                    {"name": "Final Image", "expected_position": 1.0}
                ]
            }
        }

        if framework not in frameworks:
            framework = "three_act"

        framework_data = frameworks[framework]
        validation = {
            "isValid": True,
            "framework": framework,
            "acts": [],
            "plotPoints": [],
            "gaps": [],
            "warnings": [],
            "suggestions": []
        }

        # Validate acts
        if framework == "three_act":
            for act in framework_data["acts"]:
                act_scenes = [s for s in scenes if act["start"] <= s.position / len(scenes) <= act["end"]]
                completeness = len(act_scenes) / max(1, len(scenes) * (act["end"] - act["start"]))
                
                validation["acts"].append({
                    "name": act["name"],
                    "type": act["type"],
                    "startPosition": act["start"],
                    "endPosition": act["end"],
                    "scenes": [s.id for s in act_scenes],
                    "completeness": min(1.0, completeness)
                })

        # Validate plot points
        for plot_point in framework_data.get("plot_points", framework_data.get("beats", [])):
            expected_pos = plot_point["expected_position"]
            closest_beat = min(
                beats,
                key=lambda b: abs(b.position - expected_pos),
                default=None
            )

            if closest_beat:
                actual_pos = closest_beat.position
                deviation = abs(actual_pos - expected_pos)
                
                if deviation < 0.05:
                    status = "present"
                elif deviation < 0.1:
                    status = "misplaced"
                else:
                    status = "missing"

                validation["plotPoints"].append({
                    "name": plot_point["name"],
                    "expectedPosition": expected_pos,
                    "actualPosition": actual_pos,
                    "status": status,
                    "sceneId": closest_beat.scene_ids[0] if closest_beat.scene_ids else None
                })
            else:
                validation["plotPoints"].append({
                    "name": plot_point["name"],
                    "expectedPosition": expected_pos,
                    "actualPosition": None,
                    "status": "missing"
                })

        # Generate warnings and suggestions
        if len(scenes) < 10:
            validation["warnings"].append("Story has fewer than 10 scenes")
            validation["suggestions"].append("Consider adding more scenes for better pacing")

        if not any(p["status"] == "present" for p in validation["plotPoints"]):
            validation["isValid"] = False
            validation["suggestions"].append("Add key story beats to improve structure")

        return validation

    async def get_narrative_analytics(self, project_id: str) -> Dict[str, Any]:
        """Generate comprehensive narrative analytics."""
        
        scenes = self.db.query(Scene).filter(
            Scene.project_id == project_id
        ).all()

        characters = self.db.query(Character).filter(
            Character.project_id == project_id
        ).all()

        assets = self.db.query(Asset).filter(
            Asset.project_id == project_id
        ).all()

        # Calculate metrics
        structure_validation = await self.validate_structure(project_id)
        character_arcs = await self.get_character_arcs(project_id)

        # Structure compliance
        structure_compliance = sum(
            act["completeness"] for act in structure_validation["acts"]
        ) / max(1, len(structure_validation["acts"]))

        # Character consistency
        character_consistency = sum(
            arc["consistencyScore"] for arc in character_arcs
        ) / max(1, len(character_arcs))

        # Pacing score
        durations = [s.estimated_duration or 2.5 for s in scenes]
        avg_duration = sum(durations) / max(1, len(durations))
        duration_variance = sum((d - avg_duration) ** 2 for d in durations) / max(1, len(durations))
        pacing_score = 1.0 - min(1.0, duration_variance / 25.0)  # Normalize to 0-1

        # Emotional arc
        emotional_arc = [s.emotional_intensity or 0.5 for s in scenes]

        # Asset utilization
        asset_utilization = {}
        for asset in assets:
            usage = self.db.query(Scene).filter(
                Scene.project_id == project_id,
                Scene.assets.contains(asset)
            ).count()
            asset_utilization[asset.name] = usage

        # Quality metrics
        quality_metrics = {
            "narrativeCoherence": structure_compliance,
            "characterDevelopment": character_consistency,
            "pacingBalance": pacing_score,
            "visualConsistency": 0.85  # Placeholder
        }

        # Recommendations
        recommendations = {
            "structure": [],
            "pacing": [],
            "character": [],
            "assets": []
        }

        if structure_compliance < 0.8:
            recommendations["structure"].append("Consider adding missing story beats")

        if pacing_score < 0.7:
            recommendations["pacing"].append("Review scene durations for better balance")

        if character_consistency < 0.8:
            recommendations["character"].append("Ensure character consistency across scenes")

        if any(v < 2 for v in asset_utilization.values()):
            recommendations["assets"].append("Consider better asset distribution")

        return {
            "structureCompliance": structure_compliance,
            "characterConsistency": character_consistency,
            "pacingScore": pacing_score,
            "emotionalArc": emotional_arc,
            "assetUtilization": asset_utilization,
            "qualityMetrics": quality_metrics,
            "recommendations": recommendations
        }

    async def optimize_pacing(self, project_id: str) -> Dict[str, Any]:
        """Optimize story pacing based on analysis."""
        
        analytics = await self.get_narrative_analytics(project_id)
        
        # Simple optimization suggestions
        optimization = {
            "optimizedScenes": [],
            "analytics": analytics,
            "suggestions": []
        }

        if analytics["pacingScore"] < 0.7:
            optimization["suggestions"].append(
                "Consider adjusting scene durations for better pacing"
            )

        if analytics["structureCompliance"] < 0.8:
            optimization["suggestions"].append(
                "Add missing story beats to improve structure"
            )

        return optimization

    async def update_scene_beat(self, scene_id: str, beat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update beat analysis for a specific scene."""
        
        scene = self.db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")

        if "emotional_intensity" in beat_data:
            scene.emotional_intensity = beat_data["emotional_intensity"]
        
        if "beat_type" in beat_data:
            scene.beat_type = beat_data["beat_type"]

        self.db.commit()

        return {
            "id": scene.id,
            "title": scene.title,
            "emotionalIntensity": scene.emotional_intensity,
            "beatType": scene.beat_type
        }

    async def export_story_report(self, project_id: str, format: str = "pdf") -> Dict[str, str]:
        """Export comprehensive story report."""
        
        timeline = await self.generate_timeline(project_id)
        analytics = await self.get_narrative_analytics(project_id)
        validation = await self.validate_structure(project_id)

        report_data = {
            "project_id": project_id,
            "generated_at": datetime.utcnow().isoformat(),
            "timeline": timeline,
            "analytics": analytics,
            "validation": validation
        }

        # Generate report URL (placeholder)
        report_id = str(uuid.uuid4())
        report_url = f"/reports/story/{project_id}/{report_id}.{format}"

        return {"url": report_url}

    def _calculate_emotional_intensity(self, scene: Scene) -> float:
        """Calculate emotional intensity for a scene."""
        # Simple calculation based on scene metadata
        intensity = 0.5  # Base intensity
        
        if scene.mood:
            mood_intensities = {
                "intense": 0.8,
                "dramatic": 0.7,
                "emotional": 0.9,
                "neutral": 0.3,
                "calm": 0.2
            }
            intensity = mood_intensities.get(scene.mood.lower(), 0.5)
        
        return min(1.0, max(0.0, intensity))

    def _calculate_character_emotional_arc(self, character: Character, scene: Scene) -> float:
        """Calculate character's emotional arc point in a scene."""
        # Placeholder calculation
        return 0.5  # Neutral baseline

    def _calculate_consistency_score(self, character: Character, scenes: List[Scene]) -> float:
        """Calculate character consistency score across scenes."""
        # Placeholder calculation
        return 0.85

    def _get_beat_type(self, scene: Scene) -> str:
        """Determine the beat type for a scene."""
        # Simple mapping based on scene position
        position = scene.position or 0
        
        beat_types = [
            "opening", "setup", "catalyst", "debate", "break_into_two",
            "fun_and_games", "midpoint", "bad_guys_close_in", "all_is_lost",
            "dark_night_of_soul", "break_into_three", "finale", "final_image"
        ]
        
        index = int(position * len(beat_types)) % len(beat_types)
        return beat_types[index]

    def _get_character_color(self, character_id: str) -> str:
        """Generate consistent color for character based on ID."""
        import hashlib
        hash_value = int(hashlib.md5(character_id.encode()).hexdigest(), 16)
        hue = hash_value % 360
        return f"hsl({hue}, 70%, 50%)"