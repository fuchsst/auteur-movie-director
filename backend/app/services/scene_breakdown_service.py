"""
Scene Breakdown Service
======================

Business logic for scene-by-scene breakdown visualization system.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json
import uuid
from datetime import datetime

from backend.app.schemas.scene_breakdown import (
    SceneBreakdown,
    SceneSummary,
    SceneReorderRequest,
    SceneBulkUpdate,
    SceneAnalysis,
    SceneStatus
)


class SceneBreakdownService:
    """Service for managing scene breakdowns and visualizations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_project_scenes(
        self,
        project_id: str,
        act_number: Optional[int] = None,
        chapter_number: Optional[int] = None,
        status: Optional[SceneStatus] = None
    ) -> List[SceneSummary]:
        """Get all scenes for a project with optional filtering."""
        query = """
            SELECT 
                scene_id, title, scene_number, act_number, chapter_number,
                duration_minutes, status, completion_percentage,
                json_array_length(characters::json) as character_count,
                json_array_length(assets::json) as asset_count,
                json_array_length(story_beats::json) as story_beat_count,
                thumbnail_url, color_indicator
            FROM scene_breakdowns
            WHERE project_id = %s
        """
        
        params = [project_id]
        
        if act_number:
            query += " AND act_number = %s"
            params.append(act_number)
        
        if chapter_number:
            query += " AND chapter_number = %s"
            params.append(chapter_number)
        
        if status:
            query += " AND status = %s"
            params.append(status.value)
        
        query += " ORDER BY act_number, chapter_number, scene_number"
        
        result = self.db.execute(query, params)
        scenes = []
        
        for row in result:
            scenes.append(SceneSummary(
                scene_id=row[0],
                title=row[1],
                scene_number=row[2],
                act_number=row[3],
                chapter_number=row[4],
                duration_minutes=row[5],
                status=SceneStatus(row[6]),
                completion_percentage=row[7],
                character_count=row[8] or 0,
                asset_count=row[9] or 0,
                story_beat_count=row[10] or 0,
                thumbnail_url=row[11],
                color_indicator=row[12] or "#3b82f6"
            ))
        
        return scenes
    
    async def create_scene(self, project_id: str, scene_id: str, scene_data: dict) -> SceneBreakdown:
        """Create a new scene breakdown."""
        # Initialize with defaults
        defaults = {
            'scene_id': scene_id,
            'project_id': project_id,
            'act_number': 1,
            'scene_number': 1,
            'title': f"Scene {scene_id[:8]}",
            'description': '',
            'scene_type': 'dialogue',
            'location': 'TBD',
            'time_of_day': 'TBD',
            'duration_minutes': 2.0,
            'slug_line': 'INT. LOCATION - DAY',
            'synopsis': '',
            'status': 'draft',
            'completion_percentage': 0.0,
            'characters': '[]',
            'assets': '[]',
            'story_beats': '[]',
            'color_palette': '[]',
            'mood_tags': '[]',
            'camera_angles': '[]',
            'connections': '[]',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'version': 1
        }
        
        # Merge with provided data
        defaults.update(scene_data)
        
        query = """
            INSERT INTO scene_breakdowns (
                scene_id, project_id, act_number, chapter_number, scene_number,
                title, description, scene_type, location, time_of_day,
                duration_minutes, slug_line, synopsis, script_notes, status,
                completion_percentage, characters, assets, story_beats,
                story_circle_position, conflict_level, stakes_level,
                color_palette, mood_tags, camera_angles, canvas_position,
                connections, created_at, updated_at, version
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = [
            defaults['scene_id'], defaults['project_id'], defaults['act_number'],
            defaults.get('chapter_number'), defaults['scene_number'],
            defaults['title'], defaults['description'], defaults['scene_type'],
            defaults['location'], defaults['time_of_day'], defaults['duration_minutes'],
            defaults['slug_line'], defaults['synopsis'], defaults.get('script_notes', ''),
            defaults['status'], defaults['completion_percentage'],
            defaults['characters'], defaults['assets'], defaults['story_beats'],
            defaults.get('story_circle_position'), defaults.get('conflict_level', 1),
            defaults.get('stakes_level', 1), json.dumps(defaults['color_palette']),
            json.dumps(defaults['mood_tags']), json.dumps(defaults['camera_angles']),
            json.dumps(defaults.get('canvas_position')), json.dumps(defaults['connections']),
            defaults['created_at'], defaults['updated_at'], defaults['version']
        ]
        
        self.db.execute(query, params)
        self.db.commit()
        
        return await self.get_scene(scene_id)
    
    async def get_scene(self, scene_id: str) -> Optional[SceneBreakdown]:
        """Get complete scene breakdown details."""
        query = """
            SELECT * FROM scene_breakdowns WHERE scene_id = %s
        """
        
        result = self.db.execute(query, [scene_id])
        row = result.fetchone()
        
        if not row:
            return None
        
        return self._row_to_scene_breakdown(row)
    
    async def update_scene(self, scene_id: str, updates: dict) -> Optional[SceneBreakdown]:
        """Update scene breakdown details."""
        # Handle JSON fields
        json_fields = ['characters', 'assets', 'story_beats', 'color_palette', 
                      'mood_tags', 'camera_angles', 'connections', 'canvas_position']
        
        for field in json_fields:
            if field in updates and isinstance(updates[field], (list, dict)):
                updates[field] = json.dumps(updates[field])
        
        updates['updated_at'] = datetime.utcnow()
        
        # Build dynamic update query
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            if key != 'scene_id':
                set_clauses.append(f"{key} = %s")
                params.append(value)
        
        if not set_clauses:
            return await self.get_scene(scene_id)
        
        params.append(scene_id)
        query = f"""
            UPDATE scene_breakdowns 
            SET {', '.join(set_clauses)}
            WHERE scene_id = %s
            RETURNING *
        """
        
        result = self.db.execute(query, params)
        row = result.fetchone()
        
        if not row:
            return None
        
        self.db.commit()
        return self._row_to_scene_breakdown(row)
    
    async def delete_scene(self, scene_id: str) -> bool:
        """Delete a scene breakdown."""
        query = "DELETE FROM scene_breakdowns WHERE scene_id = %s"
        result = self.db.execute(query, [scene_id])
        self.db.commit()
        return result.rowcount > 0
    
    async def reorder_scene(
        self, 
        scene_id: str, 
        reorder_request: SceneReorderRequest
    ) -> List[SceneSummary]:
        """Reorder scenes with drag and drop functionality."""
        # Get the scene to move
        scene = await self.get_scene(scene_id)
        if not scene:
            raise ValueError("Scene not found")
        
        # Update target act/chapter if specified
        updates = {}
        if reorder_request.target_act:
            updates['act_number'] = reorder_request.target_act
        if reorder_request.target_chapter:
            updates['chapter_number'] = reorder_request.target_chapter
        
        await self.update_scene(scene_id, updates)
        
        # Reorder scenes within the target scope
        query = """
            UPDATE scene_breakdowns 
            SET scene_number = CASE 
                WHEN scene_id = %s THEN %s
                WHEN scene_number >= %s AND scene_id != %s THEN scene_number + 1
                ELSE scene_number
            END
            WHERE act_number = %s AND (chapter_number = %s OR (%s IS NULL AND chapter_number IS NULL))
        """
        
        params = [
            scene_id, reorder_request.new_position,
            reorder_request.new_position, scene_id,
            reorder_request.target_act or scene.act_number,
            reorder_request.target_chapter or scene.chapter_number,
            reorder_request.target_chapter or scene.chapter_number
        ]
        
        self.db.execute(query, params)
        self.db.commit()
        
        # Renumber scenes to ensure sequential ordering
        await self._renumber_scenes(
            scene.project_id,
            reorder_request.target_act or scene.act_number,
            reorder_request.target_chapter or scene.chapter_number
        )
        
        return await self.get_project_scenes(scene.project_id)
    
    async def bulk_update_scenes(self, bulk_update: SceneBulkUpdate) -> dict:
        """Update multiple scenes at once."""
        updated_count = 0
        
        for scene_id in bulk_update.scene_ids:
            success = await self.update_scene(scene_id, bulk_update.updates)
            if success:
                updated_count += 1
        
        return {"updated_count": updated_count, "total_count": len(bulk_update.scene_ids)}
    
    async def analyze_scene(self, scene_id: str) -> Optional[SceneAnalysis]:
        """Analyze scene for pacing, character balance, and story progression."""
        scene = await self.get_scene(scene_id)
        if not scene:
            return None
        
        # Pacing analysis
        pacing_score = min(100, (scene.duration_minutes / 3) * 100)
        if len(scene.story_beats) > 5:
            pacing_score *= 0.9
        
        # Character balance
        character_balance = {}
        total_screen_time = sum(c.screen_time for c in scene.characters) or 1
        for character in scene.characters:
            character_balance[character.character_name] = (character.screen_time / total_screen_time) * 100
        
        # Story progression
        story_progression = min(100, (scene.completion_percentage * 0.7) + (len(scene.story_beats) * 6))
        
        # Missing elements analysis
        missing_elements = []
        if not scene.characters:
            missing_elements.append("No characters assigned")
        if not scene.story_beats:
            missing_elements.append("No story beats defined")
        if scene.duration_minutes < 1:
            missing_elements.append("Scene duration too short")
        if not scene.assets:
            missing_elements.append("No assets assigned")
        
        # Suggestions
        suggestions = []
        if len(scene.story_beats) < 2:
            suggestions.append("Add more story beats to improve scene structure")
        if len(scene.characters) > 5:
            suggestions.append("Consider reducing character count for clarity")
        if scene.duration_minutes > 5:
            suggestions.append("Consider splitting long scene into smaller ones")
        
        return SceneAnalysis(
            scene_id=scene_id,
            pacing_score=pacing_score,
            character_balance=character_balance,
            story_progression=story_progression,
            missing_elements=missing_elements,
            suggestions=suggestions
        )
    
    async def analyze_project(self, project_id: str) -> List[SceneAnalysis]:
        """Analyze all scenes in a project."""
        scenes = await self.get_project_scenes(project_id)
        analyses = []
        
        for scene_summary in scenes:
            analysis = await self.analyze_scene(scene_summary.scene_id)
            if analysis:
                analyses.append(analysis)
        
        return analyses
    
    async def get_canvas_data(self, project_id: str) -> dict:
        """Get scene data formatted for canvas visualization."""
        scenes = await self.get_project_scenes(project_id)
        
        # Group by act and chapter
        act_chapters = {}
        for scene in scenes:
            key = f"act_{scene.act_number}_chapter_{scene.chapter_number or 0}"
            if key not in act_chapters:
                act_chapters[key] = []
            act_chapters[key].append(scene)
        
        return {
            "scenes": [scene.dict() for scene in scenes],
            "act_chapters": act_chapters,
            "total_scenes": len(scenes),
            "total_duration": sum(s.duration_minutes for s in scenes),
            "completion_stats": {
                "draft": len([s for s in scenes if s.status == SceneStatus.DRAFT]),
                "in_progress": len([s for s in scenes if s.status == SceneStatus.IN_PROGRESS]),
                "complete": len([s for s in scenes if s.status == SceneStatus.COMPLETE])
            }
        }
    
    async def save_canvas_layout(self, project_id: str, layout_data: dict) -> dict:
        """Save scene positions and connections for canvas view."""
        updates = layout_data.get('scene_positions', {})
        
        for scene_id, position in updates.items():
            await self.update_scene(scene_id, {
                'canvas_position': position
            })
        
        return {"message": "Canvas layout saved successfully"}
    
    async def get_story_circle_mapping(self, project_id: str) -> dict:
        """Get story circle mapping for scenes."""
        scenes = await self.get_project_scenes(project_id)
        
        story_circle_positions = {i: [] for i in range(1, 9)}
        
        for scene in scenes:
            if scene.story_circle_position:
                story_circle_positions[scene.story_circle_position].append(scene)
        
        return {
            "positions": story_circle_positions,
            "mapping": {
                1: "You (Protagonist Introduction)",
                2: "Need (Character Desire)",
                3: "Go (Crossing the Threshold)",
                4: "Search (Trials and Tribulations)",
                5: "Find (Meeting the Goddess)",
                6: "Take (Supreme Ordeal)",
                7: "Return (Reward and Consequences)",
                8: "Change (New Self)")
            }
        }
    
    async def add_scene_character(self, scene_id: str, character_data: dict) -> SceneBreakdown:
        """Add a character to a scene."""
        scene = await self.get_scene(scene_id)
        if not scene:
            raise ValueError("Scene not found")
        
        characters = scene.characters.copy()
        characters.append(character_data)
        
        return await self.update_scene(scene_id, {'characters': [c.dict() for c in characters]})
    
    async def remove_scene_character(self, scene_id: str, character_id: str) -> bool:
        """Remove a character from a scene."""
        scene = await self.get_scene(scene_id)
        if not scene:
            return False
        
        characters = [c for c in scene.characters if c.character_id != character_id]
        await self.update_scene(scene_id, {'characters': [c.dict() for c in characters]})
        return True
    
    async def add_scene_asset(self, scene_id: str, asset_data: dict) -> SceneBreakdown:
        """Add an asset to a scene."""
        scene = await self.get_scene(scene_id)
        if not scene:
            raise ValueError("Scene not found")
        
        assets = scene.assets.copy()
        assets.append(asset_data)
        
        return await self.update_scene(scene_id, {'assets': [a.dict() for a in assets]})
    
    async def remove_scene_asset(self, scene_id: str, asset_id: str) -> bool:
        """Remove an asset from a scene."""
        scene = await self.get_scene(scene_id)
        if not scene:
            return False
        
        assets = [a for a in scene.assets if a.asset_id != asset_id]
        await self.update_scene(scene_id, {'assets': [a.dict() for a in assets]})
        return True
    
    async def add_story_beat(self, scene_id: str, beat_data: dict) -> SceneBreakdown:
        """Add a story beat to a scene."""
        scene = await self.get_scene(scene_id)
        if not scene:
            raise ValueError("Scene not found")
        
        story_beats = scene.story_beats.copy()
        story_beats.append(beat_data)
        
        return await self.update_scene(scene_id, {'story_beats': [b.dict() for b in story_beats]})
    
    async def remove_story_beat(self, scene_id: str, beat_id: str) -> bool:
        """Remove a story beat from a scene."""
        scene = await self.get_scene(scene_id)
        if not scene:
            return False
        
        story_beats = [b for b in scene.story_beats if b.beat_id != beat_id]
        await self.update_scene(scene_id, {'story_beats': [b.dict() for b in story_beats]})
        return True
    
    async def export_breakdown(self, project_id: str, format: str) -> dict:
        """Export scene breakdown data."""
        scenes = await self.get_project_scenes(project_id)
        
        if format == "json":
            return {
                "project_id": project_id,
                "scenes": [scene.dict() for scene in scenes],
                "export_date": datetime.utcnow().isoformat()
            }
        
        return {"message": f"Export format '{format}' not yet implemented"}
    
    def _row_to_scene_breakdown(self, row) -> SceneBreakdown:
        """Convert database row to SceneBreakdown model."""
        return SceneBreakdown(
            scene_id=row.scene_id,
            project_id=row.project_id,
            act_number=row.act_number,
            chapter_number=row.chapter_number,
            scene_number=row.scene_number,
            title=row.title,
            description=row.description,
            scene_type=row.scene_type,
            location=row.location,
            time_of_day=row.time_of_day,
            duration_minutes=row.duration_minutes,
            slug_line=row.slug_line,
            synopsis=row.synopsis,
            script_notes=row.script_notes or "",
            status=SceneStatus(row.status),
            completion_percentage=row.completion_percentage,
            characters=json.loads(row.characters) if isinstance(row.characters, str) else row.characters,
            assets=json.loads(row.assets) if isinstance(row.assets, str) else row.assets,
            story_beats=json.loads(row.story_beats) if isinstance(row.story_beats, str) else row.story_beats,
            story_circle_position=row.story_circle_position,
            conflict_level=row.conflict_level,
            stakes_level=row.stakes_level,
            color_palette=json.loads(row.color_palette) if isinstance(row.color_palette, str) else row.color_palette,
            mood_tags=json.loads(row.mood_tags) if isinstance(row.mood_tags, str) else row.mood_tags,
            camera_angles=json.loads(row.camera_angles) if isinstance(row.camera_angles, str) else row.camera_angles,
            canvas_position=json.loads(row.canvas_position) if isinstance(row.canvas_position, str) else row.canvas_position,
            connections=json.loads(row.connections) if isinstance(row.connections, str) else row.connections,
            created_at=row.created_at,
            updated_at=row.updated_at,
            version=row.version
        )
    
    async def _renumber_scenes(self, project_id: str, act_number: int, chapter_number: Optional[int]):
        """Renumber scenes to ensure sequential ordering."""
        query = """
            UPDATE scene_breakdowns 
            SET scene_number = subquery.new_number
            FROM (
                SELECT scene_id, ROW_NUMBER() OVER (ORDER BY scene_number) as new_number
                FROM scene_breakdowns
                WHERE project_id = %s AND act_number = %s 
                AND (chapter_number = %s OR (%s IS NULL AND chapter_number IS NULL))
            ) as subquery
            WHERE scene_breakdowns.scene_id = subquery.scene_id
        """
        
        params = [project_id, act_number, chapter_number, chapter_number]
        self.db.execute(query, params)
        self.db.commit()