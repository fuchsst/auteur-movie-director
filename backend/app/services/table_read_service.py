"""
Digital Table Read Service
STORY-088 Implementation

Service for AI-powered script analysis using Dan Harmon's Story Circle and creative bible generation.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import re
from datetime import datetime
import uuid

from app.models.table_read_models import (
    CharacterAnalysis, SceneAnalysis, StoryCircleAnalysis, CreativeBible,
    TableReadRequest, TableReadSession, DialogueAnalysis, ThemeAnalysis,
    StoryCircleBeat, CharacterArchetype, SceneType, EmotionalTone, ConflictLevel,
    extract_scene_headings, extract_character_names, identify_story_circle_beat
)
from app.services.breakdown_service import BreakdownService
from app.models.breakdown_models import SceneBreakdown

logger = logging.getLogger(__name__)


class TableReadService:
    """Service for digital table read analysis and creative bible generation."""
    
    def __init__(self, project_root: str, breakdown_service: BreakdownService):
        self.project_root = Path(project_root)
        self.breakdown_service = breakdown_service
        self.sessions: Dict[str, TableReadSession] = {}
        self.bibles: Dict[str, CreativeBible] = {}
        
        # Initialize story circle templates
        self.story_circle_templates = self._load_story_circle_templates()
        
    def _load_story_circle_templates(self) -> Dict[str, Any]:
        """Load story circle analysis templates."""
        return {
            "hero_journey": {
                "beats": {
                    StoryCircleBeat.YOU: {
                        "description": "Establish the ordinary world",
                        "key_elements": ["status_quo", "character_intro", "world_building"]
                    },
                    StoryCircleBeat.NEED: {
                        "description": "Character desires change",
                        "key_elements": ["desire", "problem", "inciting_incident"]
                    },
                    StoryCircleBeat.GO: {
                        "description": "Cross the threshold",
                        "key_elements": ["new_world", "challenge", "commitment"]
                    },
                    StoryCircleBeat.SEARCH: {
                        "description": "Adapt and learn",
                        "key_elements": ["trials", "allies", "enemies", "skills"]
                    },
                    StoryCircleBeat.FIND: {
                        "description": "Achieve the goal",
                        "key_elements": ["success", "revelation", "peak_moment"]
                    },
                    StoryCircleBeat.TAKE: {
                        "description": "Pay the price",
                        "key_elements": ["loss", "sacrifice", "consequence"]
                    },
                    StoryCircleBeat.RETURN: {
                        "description": "Return changed",
                        "key_elements": ["homecoming", "wisdom", "transformation"]
                    },
                    StoryCircleBeat.CHANGE: {
                        "description": "Master of both worlds",
                        "key_elements": ["integration", "new_normal", "growth"]
                    }
                }
            }
        }
    
    async def create_table_read_session(self, request: TableReadRequest) -> TableReadSession:
        """Create a new table read analysis session."""
        session_id = str(uuid.uuid4())
        bible_id = str(uuid.uuid4())
        
        session = TableReadSession(
            session_id=session_id,
            project_id=request.project_id,
            bible_id=bible_id,
            status="processing",
            progress=0.0
        )
        
        self.sessions[session_id] = session
        
        # Start async analysis
        asyncio.create_task(self._process_table_read(session_id, request))
        
        return session
    
    async def _process_table_read(self, session_id: str, request: TableReadRequest):
        """Process the table read analysis asynchronously."""
        try:
            session = self.sessions[session_id]
            session.current_analysis = "Parsing script structure..."
            session.progress = 0.1
            
            # Parse script
            scenes = await self._parse_script(request.script_content)
            session.progress = 0.2
            
            # Analyze scenes
            session.current_analysis = "Analyzing scenes..."
            scene_analyses = await self._analyze_scenes(scenes, request)
            session.progress = 0.4
            
            # Analyze characters
            session.current_analysis = "Analyzing characters..."
            character_analyses = await self._analyze_characters(request.script_content, scene_analyses)
            session.progress = 0.6
            
            # Perform story circle analysis
            session.current_analysis = "Applying Story Circle framework..."
            story_circle = await self._analyze_story_circle(scene_analyses, character_analyses)
            session.progress = 0.8
            
            # Analyze themes and dialogue
            session.current_analysis = "Analyzing themes and dialogue..."
            themes = await self._analyze_themes(scene_analyses, character_analyses)
            dialogue_analysis = await self._analyze_dialogue(request.script_content, character_analyses)
            session.progress = 0.9
            
            # Generate creative bible
            session.current_analysis = "Generating creative bible..."
            bible = await self._generate_creative_bible(
                request, scene_analyses, character_analyses, 
                story_circle, themes, dialogue_analysis
            )
            
            # Store results
            self.bibles[bible.bible_id] = bible
            session.results = bible
            session.status = "completed"
            session.progress = 1.0
            session.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error processing table read session {session_id}: {str(e)}")
            session.status = "error"
            session.error_message = str(e)
            session.progress = 1.0
    
    async def _parse_script(self, script_content: str) -> List[Dict[str, Any]]:
        """Parse script into scenes and basic structure."""
        scenes = []
        lines = script_content.split('\n')
        
        current_scene = None
        scene_number = 1
        
        for line in lines:
            line = line.strip()
            
            # Scene heading
            if re.match(r'^(INT|EXT|INT/EXT|EXT/INT)\.?\s+', line, re.IGNORECASE):
                if current_scene:
                    scenes.append(current_scene)
                
                current_scene = {
                    "scene_id": f"scene_{scene_number:03d}",
                    "scene_number": str(scene_number),
                    "scene_heading": line,
                    "content": [line],
                    "characters": [],
                    "dialogue": []
                }
                scene_number += 1
            
            elif current_scene:
                current_scene["content"].append(line)
                
                # Character names (all caps)
                if re.match(r'^[A-Z][A-Z\s]+$', line) and len(line) > 2:
                    character = line.strip()
                    if character not in current_scene["characters"]:
                        current_scene["characters"].append(character)
        
        if current_scene:
            scenes.append(current_scene)
        
        return scenes
    
    async def _analyze_scenes(self, scenes: List[Dict[str, Any]], request: TableReadRequest) -> List[SceneAnalysis]:
        """Analyze individual scenes."""
        scene_analyses = []
        
        for scene in scenes:
            # Extract scene content
            content = '\n'.join(scene["content"])
            
            # Identify story circle beat
            story_beat = identify_story_circle_beat(content) or StoryCircleBeat.YOU
            
            # Analyze scene type
            scene_type = self._determine_scene_type(content)
            
            # Analyze emotional tone
            emotional_tone = self._analyze_emotional_tone(content)
            
            # Analyze conflict level
            conflict_level = self._analyze_conflict_level(content)
            
            # Extract thematic elements
            themes = self._extract_thematic_elements(content)
            
            # Extract visual descriptions
            visuals = self._extract_visual_descriptions(content)
            
            # Extract dialogue highlights
            dialogue_highlights = self._extract_dialogue_highlights(content)
            
            # Analyze pacing
            pacing = self._analyze_pacing(content)
            
            # Determine dramatic function
            dramatic_function = self._determine_dramatic_function(content, story_beat)
            
            # Analyze character development
            character_dev = self._analyze_character_development(content, scene["characters"])
            
            # Analyze stakes and tension
            stakes = self._analyze_stakes(content)
            tension_level = self._calculate_tension_level(content)
            
            scene_analysis = SceneAnalysis(
                scene_id=scene["scene_id"],
                scene_number=scene["scene_number"],
                scene_heading=scene["scene_heading"],
                synopsis=self._generate_synopsis(content),
                story_circle_beat=story_beat,
                scene_type=scene_type,
                primary_emotion=emotional_tone,
                conflict_level=conflict_level,
                character_development=character_dev,
                thematic_elements=themes,
                visual_descriptions=visuals,
                dialogue_highlights=dialogue_highlights,
                pacing_analysis=pacing,
                dramatic_function=dramatic_function,
                foreshadowing=self._extract_foreshadowing(content),
                callbacks=self._extract_callbacks(content),
                character_arcs=self._analyze_character_arcs(content, scene["characters"]),
                emotional_arc=self._analyze_emotional_arc(content),
                stakes=stakes,
                tension_level=tension_level
            )
            
            scene_analyses.append(scene_analysis)
        
        return scene_analyses
    
    async def _analyze_characters(self, script_content: str, scene_analyses: List[SceneAnalysis]) -> Dict[str, CharacterAnalysis]:
        """Analyze characters and their arcs."""
        character_names = extract_character_names(script_content)
        character_analyses = {}
        
        for character in character_names:
            # Determine archetype
            archetype = self._determine_character_archetype(character, script_content)
            
            # Analyze motivation
            motivation = self._analyze_character_motivation(character, script_content)
            
            # Analyze conflicts
            internal_conflict = self._analyze_internal_conflict(character, script_content)
            external_conflict = self._analyze_external_conflict(character, script_content)
            
            # Analyze character arc
            character_arc = self._analyze_character_arc(character, scene_analyses)
            
            # Determine story circle position
            story_position = self._determine_story_circle_position(character, scene_analyses)
            
            # Analyze emotional journey
            emotional_journey = self._analyze_emotional_journey(character, scene_analyses)
            
            # Analyze relationships
            relationships = self._analyze_character_relationships(character, script_content)
            
            # Analyze dialogue patterns
            dialogue_patterns = self._analyze_dialogue_patterns(character, script_content)
            
            # Identify key moments
            key_moments = self._identify_key_character_moments(character, scene_analyses)
            
            # Generate transformation summary
            transformation = self._generate_transformation_summary(character, scene_analyses)
            
            character_analysis = CharacterAnalysis(
                character_name=character,
                archetype=archetype,
                primary_motivation=motivation,
                internal_conflict=internal_conflict,
                external_conflict=external_conflict,
                character_arc=character_arc,
                story_circle_position=story_position,
                emotional_journey=emotional_journey,
                relationships=relationships,
                dialogue_patterns=dialogue_patterns,
                key_moments=key_moments,
                transformation_summary=transformation
            )
            
            character_analyses[character] = character_analysis
        
        return character_analyses
    
    async def _analyze_story_circle(self, scene_analyses: List[SceneAnalysis], 
                                  character_analyses: Dict[str, CharacterAnalysis]) -> StoryCircleAnalysis:
        """Perform comprehensive Story Circle analysis."""
        beats = {beat: [] for beat in StoryCircleBeat}
        character_journeys = {char: [] for char in character_analyses.keys()}
        
        # Organize scenes by story circle beats
        for scene in scene_analyses:
            beats[scene.story_circle_beat].append(scene)
        
        # Track character journeys
        for character, analysis in character_analyses.items():
            character_journeys[character] = [scene.story_circle_beat 
                                           for scene in scene_analyses 
                                           if character in scene.character_development]
        
        # Generate overall analysis
        overall_arc = self._generate_overall_arc(beats)
        thematic_throughline = self._generate_thematic_throughline(scene_analyses)
        transformations = {char: analysis.transformation_summary 
                          for char, analysis in character_analyses.items()}
        
        pacing = self._analyze_structural_pacing(scene_analyses)
        emotional_progression = self._analyze_emotional_progression(scene_analyses)
        
        strengths = self._identify_structural_strengths(beats)
        weaknesses = self._identify_structural_weaknesses(beats)
        suggestions = self._generate_improvement_suggestions(beats, weaknesses)
        
        return StoryCircleAnalysis(
            beats=beats,
            character_journeys=character_journeys,
            overall_arc=overall_arc,
            thematic_throughline=thematic_throughline,
            character_transformations=transformations,
            pacing_analysis=pacing,
            emotional_progression=emotional_progression,
            structural_strengths=strengths,
            structural_weaknesses=weaknesses,
            improvement_suggestions=suggestions
        )
    
    async def _analyze_themes(self, scene_analyses: List[SceneAnalysis], 
                            character_analyses: Dict[str, CharacterAnalysis]) -> ThemeAnalysis:
        """Analyze themes and motifs."""
        # Collect all thematic elements
        all_themes = []
        for scene in scene_analyses:
            all_themes.extend(scene.thematic_elements)
        
        # Identify primary and secondary themes
        primary_themes = self._identify_primary_themes(all_themes)
        secondary_themes = self._identify_secondary_themes(all_themes)
        
        # Extract motifs and symbols
        motifs = self._extract_motifs(scene_analyses)
        symbols = self._extract_symbols(scene_analyses)
        
        # Generate thematic questions
        questions = self._generate_thematic_questions(primary_themes, character_analyses)
        
        # Identify moral dilemmas
        dilemmas = self._identify_moral_dilemmas(scene_analyses, character_analyses)
        
        # Generate philosophical exploration
        philosophical = self._generate_philosophical_exploration(primary_themes)
        
        # Cultural commentary
        cultural = self._generate_cultural_commentary(primary_themes)
        
        # Universal themes
        universal = self._identify_universal_themes(primary_themes)
        
        return ThemeAnalysis(
            primary_themes=primary_themes,
            secondary_themes=secondary_themes,
            motifs=motifs,
            symbols=symbols,
            thematic_questions=questions,
            moral_dilemmas=dilemmas,
            philosophical_exploration=philosophical,
            cultural_commentary=cultural,
            universal_themes=universal
        )
    
    async def _analyze_dialogue(self, script_content: str, 
                              character_analyses: Dict[str, CharacterAnalysis]) -> List[DialogueAnalysis]:
        """Analyze dialogue patterns and character voices."""
        dialogue_analyses = []
        
        for character, analysis in character_analyses.items():
            # Extract character dialogue
            character_dialogue = self._extract_character_dialogue(character, script_content)
            
            if character_dialogue:
                dialogue_analysis = DialogueAnalysis(
                    character_id=f"char_{character.lower().replace(' ', '_')}",
                    character_name=character,
                    speech_patterns=self._analyze_speech_patterns(character_dialogue),
                    vocabulary_level=self._analyze_vocabulary_level(character_dialogue),
                    sentence_structure=self._analyze_sentence_structure(character_dialogue),
                    emotional_indicators=self._analyze_emotional_indicators(character_dialogue),
                    subtext_analysis=self._analyze_subtext(character_dialogue),
                    voice_consistency=self._calculate_voice_consistency(character_dialogue),
                    unique_phrases=self._extract_unique_phrases(character_dialogue),
                    dialogue_functions=self._analyze_dialogue_functions(character_dialogue),
                    relationship_indicators=self._analyze_relationship_indicators(character, script_content)
                )
                
                dialogue_analyses.append(dialogue_analysis)
        
        return dialogue_analyses
    
    async def _generate_creative_bible(self, request: TableReadRequest,
                                     scene_analyses: List[SceneAnalysis],
                                     character_analyses: Dict[str, CharacterAnalysis],
                                     story_circle: StoryCircleAnalysis,
                                     themes: ThemeAnalysis,
                                     dialogue_analysis: List[DialogueAnalysis]) -> CreativeBible:
        """Generate comprehensive creative bible."""
        bible_id = str(uuid.uuid4())
        
        # Extract basic info
        title = self._extract_title(request.script_content)
        logline = self._generate_logline(scene_analyses, character_analyses)
        synopsis = self._generate_synopsis(scene_analyses)
        
        # Analyze visual style
        visual_style = self._analyze_visual_style(scene_analyses)
        
        # Determine tone
        tone_description = self._determine_tone_description(scene_analyses)
        
        # Analyze genre
        genre_analysis = self._analyze_genre(scene_analyses, themes)
        
        # Identify target audience
        target_audience = self._identify_target_audience(scene_analyses, themes)
        
        # Find comparable works
        comparable_works = self._identify_comparable_works(genre_analysis, themes)
        
        # Generate production notes
        production_notes = self._generate_production_notes(scene_analyses, character_analyses)
        
        # Analyze character relationships
        relationships = self._analyze_character_relationships_detailed(character_analyses)
        
        # Create emotional heatmap
        emotional_heatmap = self._create_emotional_heatmap(scene_analyses)
        
        # Create structural timeline
        structural_timeline = self._create_structural_timeline(scene_analyses, story_circle)
        
        return CreativeBible(
            bible_id=bible_id,
            project_id=request.project_id,
            title=title,
            logline=logline,
            synopsis=synopsis,
            character_bios=character_analyses,
            scene_analyses=scene_analyses,
            story_circle=story_circle,
            themes=themes,
            dialogue_analysis=dialogue_analysis,
            visual_style=visual_style,
            tone_description=tone_description,
            genre_analysis=genre_analysis,
            target_audience=target_audience,
            comparable_works=comparable_works,
            production_notes=production_notes,
            character_relationships=relationships,
            emotional_heatmap=emotional_heatmap,
            structural_timeline=structural_timeline
        )
    
    # Helper methods for detailed analysis
    def _determine_scene_type(self, content: str) -> SceneType:
        """Determine the type of scene."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["introduce", "establish", "morning", "day starts"]):
            return SceneType.SETUP
        elif any(word in content_lower for word in ["fight", "argue", "conflict", "battle", "confront"]):
            return SceneType.CONFRONTATION
        elif any(word in content_lower for word in ["resolve", "solution", "fix", "heal", "reconcile"]):
            return SceneType.RESOLUTION
        elif any(word in content_lower for word in ["character", "development", "backstory", "history"]):
            return SceneType.CHARACTER
        elif any(word in content_lower for word in ["explain", "background", "context", "world-building"]):
            return SceneType.EXPOSITION
        elif any(word in content_lower for word in ["meanwhile", "later", "after", "before"]):
            return SceneType.TRANSITION
        elif any(word in content_lower for word in ["climax", "peak", "final", "ultimate"]):
            return SceneType.CLIMAX
        elif any(word in content_lower for word in ["aftermath", "epilogue", "resolution", "ending"]):
            return SceneType.DENOUEMENT
        
        return SceneType.SETUP
    
    def _analyze_emotional_tone(self, content: str) -> EmotionalTone:
        """Analyze the emotional tone of the scene."""
        content_lower = content.lower()
        
        # Simple keyword-based analysis
        emotion_keywords = {
            EmotionalTone.JOY: ["happy", "joy", "laugh", "smile", "celebrate"],
            EmotionalTone.SADNESS: ["sad", "cry", "tears", "mourn", "grief"],
            EmotionalTone.ANGER: ["angry", "rage", "furious", "mad", "upset"],
            EmotionalTone.FEAR: ["afraid", "scared", "terrified", "fear", "panic"],
            EmotionalTone.SURPRISE: ["surprise", "shock", "unexpected", "sudden"],
            EmotionalTone.DISGUST: ["disgust", "gross", "revolting", "nasty"],
            EmotionalTone.TRUST: ["trust", "believe", "faith", "confidence"],
            EmotionalTone.ANTICIPATION: ["anticipate", "expect", "wait", "hope"],
            EmotionalTone.LOVE: ["love", "care", "affection", "romance"],
            EmotionalTone.HOPE: ["hope", "optimistic", "future", "better"],
            EmotionalTone.DESPAIR: ["despair", "hopeless", "give up", "defeated"],
            EmotionalTone.CURIOSITY: ["curious", "wonder", "question", "mystery"]
        }
        
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return emotion
        
        return EmotionalTone.NEUTRAL
    
    def _analyze_conflict_level(self, content: str) -> ConflictLevel:
        """Analyze the level of conflict in the scene."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["war", "death", "kill", "destroy", "battle", "fight to death"]):
            return ConflictLevel.EXTREME
        elif any(word in content_lower for word in ["fight", "attack", "danger", "threat", "violence"]):
            return ConflictLevel.HIGH
        elif any(word in content_lower for word in ["argue", "disagree", "conflict", "problem", "challenge"]):
            return ConflictLevel.MEDIUM
        elif any(word in content_lower for word in ["tension", "uncomfortable", "awkward", "stress"]):
            return ConflictLevel.LOW
        
        return ConflictLevel.NONE
    
    def _extract_thematic_elements(self, content: str) -> List[str]:
        """Extract thematic elements from scene content."""
        themes = []
        content_lower = content.lower()
        
        # Common themes
        theme_keywords = {
            "identity": ["who am i", "identity", "self", "persona", "true self"],
            "family": ["family", "parent", "child", "mother", "father", "sister", "brother"],
            "love": ["love", "heart", "romance", "relationship", "connection"],
            "death": ["death", "mortality", "loss", "grief", "end"],
            "power": ["power", "control", "dominance", "strength", "weakness"],
            "freedom": ["freedom", "liberty", "choice", "decision", "will"],
            "justice": ["justice", "fair", "right", "wrong", "moral"],
            "truth": ["truth", "honest", "lie", "deception", "reality"],
            "growth": ["growth", "change", "development", "mature", "evolve"],
            "redemption": ["redemption", "forgiveness", "second chance", "salvation"]
        }
        
        for theme, keywords in theme_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    themes.append(theme)
                    break
        
        return list(set(themes))
    
    def _generate_synopsis(self, content: str) -> str:
        """Generate a brief synopsis of scene content."""
        # Simple extraction of first meaningful sentences
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        meaningful_lines = [line for line in lines if not line.startswith(('INT', 'EXT', 'FADE', 'CUT'))]
        
        if meaningful_lines:
            return ' '.join(meaningful_lines[:3])[:200] + "..."
        
        return "Scene describes key story moment"
    
    def _determine_character_archetype(self, character: str, content: str) -> CharacterArchetype:
        """Determine character archetype based on role and behavior."""
        content_lower = content.lower()
        character_lower = character.lower()
        
        # Simple heuristic based on character name and context
        if character_lower in ["hero", "protagonist", "main character"]:
            return CharacterArchetype.HERO
        elif any(mentor_word in content_lower for mentor_word in ["guide", "advice", "teach", "wisdom"]):
            return CharacterArchetype.MENTOR
        elif any(ally_word in content_lower for ally_word in ["friend", "partner", "companion", "support"]):
            return CharacterArchetype.ALLY
        elif any(shadow_word in content_lower for shadow_word in ["enemy", "villain", "opponent", "rival"]):
            return CharacterArchetype.SHADOW
        
        return CharacterArchetype.HERO
    
    def _extract_title(self, script_content: str) -> str:
        """Extract title from script."""
        lines = script_content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line and not line.startswith(('INT', 'EXT', 'FADE')):
                return line
        return "Untitled Script"
    
    # Additional helper methods for detailed analysis would go here...
    # (These would be implemented based on specific requirements)
    
    async def get_session_status(self, session_id: str) -> Optional[TableReadSession]:
        """Get the status of a table read session."""
        return self.sessions.get(session_id)
    
    async def get_creative_bible(self, bible_id: str) -> Optional[CreativeBible]:
        """Get the creative bible results."""
        return self.bibles.get(bible_id)
    
    async def export_bible(self, bible_id: str, format: str = "pdf") -> Dict[str, Any]:
        """Export creative bible in specified format."""
        bible = self.bibles.get(bible_id)
        if not bible:
            return {"error": "Bible not found"}
        
        export_data = {
            "bible_id": bible_id,
            "format": format,
            "title": bible.title,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        if format == "json":
            export_data["content"] = bible.dict()
        elif format == "markdown":
            export_data["content"] = self._generate_markdown_bible(bible)
        elif format == "pdf":
            export_data["content"] = self._generate_pdf_bible(bible)
        
        return export_data
    
    def _generate_markdown_bible(self, bible: CreativeBible) -> str:
        """Generate markdown version of creative bible."""
        markdown = f"# {bible.title}\n\n"
        markdown += f"**Logline:** {bible.logline}\n\n"
        markdown += f"**Synopsis:** {bible.synopsis}\n\n"
        
        markdown += "## Characters\n\n"
        for character, analysis in bible.character_bios.items():
            markdown += f"### {character}\n"
            markdown += f"- **Archetype:** {analysis.archetype}\n"
            markdown += f"- **Motivation:** {analysis.primary_motivation}\n"
            markdown += f"- **Arc:** {analysis.character_arc}\n\n"
        
        return markdown
    
    def _generate_pdf_bible(self, bible: CreativeBible) -> str:
        """Generate PDF version of creative bible (placeholder)."""
        return "PDF generation would be implemented with a proper PDF library"
    
    async def list_sessions(self, project_id: str) -> List[TableReadSession]:
        """List all table read sessions for a project."""
        return [session for session in self.sessions.values() 
                if session.project_id == project_id]