"""
Script Parser Service
STORY-086 Implementation

Provides screenplay parsing capabilities for the breakdown view interface,
supporting standard screenplay formats (FDX, PDF, TXT) and automatic element detection.
"""

import re
import json
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import pdfplumber
from xml.etree import ElementTree as ET


class ScriptElementType(str, Enum):
    """Types of elements detected in scripts."""
    CHARACTER = "character"
    PROP = "prop"
    WARDROBE = "wardrobe"
    VEHICLE = "vehicle"
    LOCATION = "location"
    SOUND = "sound"
    MUSIC = "music"
    SET_DRESSING = "set_dressing"
    SFX = "sfx"


@dataclass
class ScriptElement:
    """A detected element in the script."""
    element_id: str
    element_type: ScriptElementType
    text: str
    start_pos: int
    end_pos: int
    confidence: float
    scene_id: str
    context: Dict[str, Any]
    metadata: Dict[str, Any] = None


@dataclass
class ParsedScene:
    """A parsed scene from the script."""
    scene_id: str
    scene_number: str
    scene_heading: str
    synopsis: str
    location: str
    time_of_day: str
    characters: List[str]
    elements: List[ScriptElement]
    raw_text: str
    start_line: int
    end_line: int


@dataclass
class ParsedScript:
    """Complete parsed script data."""
    title: str
    author: str
    scenes: List[ParsedScene]
    characters: List[str]
    locations: List[str]
    elements_by_type: Dict[str, List[ScriptElement]]
    total_scenes: int
    total_pages: float
    created_at: datetime
    parser_version: str = "1.0.0"


class ScriptParserService:
    """Service for parsing screenplay files and extracting production elements."""
    
    def __init__(self):
        self.element_patterns = self._load_element_patterns()
        self.scene_patterns = self._load_scene_patterns()
    
    def _load_element_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Load regex patterns for element detection."""
        return {
            ScriptElementType.CHARACTER: [
                re.compile(r'^[A-Z][A-Z\s]+$', re.MULTILINE),  # Character names in caps
            ],
            ScriptElementType.PROP: [
                re.compile(r'\b(?:a|an|the)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.IGNORECASE),
                re.compile(r'\b(?:holds|carries|uses|wields|grabs)\s+(?:the|a|an)?\s*([a-z]+(?:\s+[a-z]+)*)\b', re.IGNORECASE),
                re.compile(r'\b(?:sword|gun|book|phone|car|knife|key|bag|box|bottle)\b', re.IGNORECASE),
            ],
            ScriptElementType.WARDROBE: [
                re.compile(r'\b(?:wearing|dressed in|wears|puts on)\s+(?:a|an|the)?\s*([a-z]+(?:\s+[a-z]+)*)\b', re.IGNORECASE),
                re.compile(r'\b(?:t-shirt|jacket|coat|dress|suit|uniform|gown|hat|shoes)\b', re.IGNORECASE),
                re.compile(r'\b(?:red|blue|green|black|white|brown|leather|tattered|elegant)\s+(?:coat|shirt|dress|suit)\b', re.IGNORECASE),
            ],
            ScriptElementType.VEHICLE: [
                re.compile(r'\b(?:car|truck|motorcycle|bicycle|bus|train|plane|boat|ship)\b', re.IGNORECASE),
                re.compile(r'\b(?:drives|parks|enters|exits)\s+(?:the|a)?\s*([a-z]+(?:\s+[a-z]+)*)\b', re.IGNORECASE),
            ],
            ScriptElementType.LOCATION: [
                re.compile(r'^((?:INT\.|EXT\.|INT\.\/EXT\.|EXT\.\/INT\.)\s+.+?)(?=\s*-|\s*$)', re.MULTILINE),
            ],
            ScriptElementType.SOUND: [
                re.compile(r'\b(?:hears|sounds|noise|voice|music|singing)\b', re.IGNORECASE),
            ],
            ScriptElementType.SFX: [
                re.compile(r'\b(?:BOOM|CRASH|BANG|WHOOSH|FLASH|explosion|gunshot)\b', re.IGNORECASE),
            ],
            ScriptElementType.SET_DRESSING: [
                re.compile(r'\b(?:table|chair|desk|lamp|picture|window|door|book|plant)\b', re.IGNORECASE),
            ],
        }
    
    def _load_scene_patterns(self) -> Dict[str, re.Pattern]:
        """Load patterns for scene detection."""
        return {
            'scene_heading': re.compile(r'^\s*((?:INT\.|EXT\.|INT\.\/EXT\.|EXT\.\/INT\.)\s+.+?)(?=\s*-|\s*$)', re.MULTILINE),
            'scene_number': re.compile(r'^\s*\d+(?:[A-Z]\d?)?(?:\.\d+)?', re.MULTILINE),
            'character_name': re.compile(r'^\s*[A-Z][A-Z\s]+$', re.MULTILINE),
            'dialogue': re.compile(r'^\s*([A-Z][A-Z\s]+)$\s*\n\s*(.+?)(?=\n[A-Z][A-Z\s]+$|\n\s*$)', re.MULTILINE | re.DOTALL),
        }
    
    async def parse_file(self, file_path: str, file_content: bytes = None) -> ParsedScript:
        """Parse a screenplay file."""
        path = Path(file_path)
        
        if file_content is None:
            file_content = path.read_bytes()
        
        if path.suffix.lower() == '.fdx':
            return await self._parse_fdx(file_content)
        elif path.suffix.lower() == '.pdf':
            return await self._parse_pdf(file_content)
        elif path.suffix.lower() in ['.txt', '.fountain']:
            return await self._parse_text(file_content.decode('utf-8'))
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    async def _parse_fdx(self, content: bytes) -> ParsedScript:
        """Parse Final Draft (.fdx) format."""
        try:
            root = ET.fromstring(content)
            
            # Extract basic info
            title = root.find('.//Title') or "Untitled"
            author = root.find('.//Author') or "Unknown"
            
            # Parse scenes
            scenes = []
            characters = set()
            locations = set()
            
            for scene_elem in root.findall('.//Scene'):
                scene_data = self._parse_fdx_scene(scene_elem)
                scenes.append(scene_data)
                characters.update(scene_data.characters)
                locations.add(scene_data.location)
            
            return ParsedScript(
                title=str(title),
                author=str(author),
                scenes=scenes,
                characters=list(characters),
                locations=list(locations),
                elements_by_type=self._organize_elements(scenes),
                total_scenes=len(scenes),
                total_pages=self._estimate_pages(scenes),
                created_at=datetime.now()
            )
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid FDX format: {e}")
    
    async def _parse_pdf(self, content: bytes) -> ParsedScript:
        """Parse PDF screenplay format."""
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            tmp_file.write(content)
            tmp_file.flush()
            
            with pdfplumber.open(tmp_file.name) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                
                return await self._parse_text(text)
    
    async def _parse_text(self, text: str) -> ParsedScript:
        """Parse plain text screenplay format."""
        lines = text.split('\n')
        
        # Extract title from first lines
        title = "Untitled"
        author = "Unknown"
        
        for line in lines[:10]:
            if line.strip().upper() == "TITLE:":
                title = lines[lines.index(line) + 1].strip()
            elif line.strip().upper() == "AUTHOR:":
                author = lines[lines.index(line) + 1].strip()
        
        # Parse scenes
        scenes = []
        characters = set()
        locations = set()
        
        scene_pattern = self.scene_patterns['scene_heading']
        matches = list(scene_pattern.finditer(text))
        
        for i, match in enumerate(matches):
            scene_start = match.start()
            scene_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            
            scene_text = text[scene_start:scene_end].strip()
            scene_data = self._parse_scene_text(scene_text, len(scenes) + 1)
            
            scenes.append(scene_data)
            characters.update(scene_data.characters)
            locations.add(scene_data.location)
        
        return ParsedScript(
            title=title,
            author=author,
            scenes=scenes,
            characters=list(characters),
            locations=list(locations),
            elements_by_type=self._organize_elements(scenes),
            total_scenes=len(scenes),
            total_pages=self._estimate_pages(scenes),
            created_at=datetime.now()
        )
    
    def _parse_fdx_scene(self, scene_elem) -> ParsedScene:
        """Parse individual FDX scene element."""
        scene_number = scene_elem.get('Number', str(len(self.scenes) + 1))
        scene_heading = scene_elem.find('.//SceneHeading')
        
        # Extract location and time from heading
        heading_text = str(scene_heading.text) if scene_heading else ""
        location, time_of_day = self._parse_scene_heading(heading_text)
        
        # Extract characters and elements
        scene_text = self._extract_scene_text(scene_elem)
        characters = self._extract_characters(scene_text)
        elements = self._detect_elements(scene_text, scene_number)
        
        return ParsedScene(
            scene_id=f"scene-{scene_number}",
            scene_number=scene_number,
            scene_heading=heading_text,
            synopsis=self._generate_synopsis(scene_text),
            location=location,
            time_of_day=time_of_day,
            characters=characters,
            elements=elements,
            raw_text=scene_text,
            start_line=0,
            end_line=0
        )
    
    def _parse_scene_text(self, text: str, scene_number: int) -> ParsedScene:
        """Parse scene text to extract components."""
        lines = text.split('\n')
        
        # Find scene heading
        heading_line = next((line for line in lines if self.scene_patterns['scene_heading'].match(line)), "")
        location, time_of_day = self._parse_scene_heading(heading_line)
        
        # Extract characters and elements
        characters = self._extract_characters(text)
        elements = self._detect_elements(text, f"scene-{scene_number}")
        
        return ParsedScene(
            scene_id=f"scene-{scene_number}",
            scene_number=str(scene_number),
            scene_heading=heading_line,
            synopsis=self._generate_synopsis(text),
            location=location,
            time_of_day=time_of_day,
            characters=characters,
            elements=elements,
            raw_text=text,
            start_line=0,
            end_line=len(lines)
        )
    
    def _parse_scene_heading(self, heading: str) -> Tuple[str, str]:
        """Parse scene heading to extract location and time."""
        heading = heading.strip()
        
        # Remove INT./EXT. prefixes
        location = re.sub(r'^(INT\.|EXT\.|INT\.\/EXT\.|EXT\.\/INT\.)\s*', '', heading)
        
        # Extract time of day
        time_patterns = [
            r'-\s*(DAY|NIGHT|MORNING|EVENING|AFTERNOON|DAWN|DUSK)',
            r'\b(DAY|NIGHT|MORNING|EVENING|AFTERNOON|DAWN|DUSK)\b'
        ]
        
        time_of_day = "DAY"  # Default
        for pattern in time_patterns:
            match = re.search(pattern, location, re.IGNORECASE)
            if match:
                time_of_day = match.group(1).upper()
                location = location.replace(match.group(0), '').strip()
                break
        
        return location.strip(), time_of_day
    
    def _extract_characters(self, text: str) -> List[str]:
        """Extract character names from scene text."""
        characters = set()
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if self.scene_patterns['character_name'].match(line):
                characters.add(line.strip())
        
        return list(characters)
    
    def _detect_elements(self, text: str, scene_id: str) -> List[ScriptElement]:
        """Detect production elements in scene text."""
        elements = []
        
        for element_type, patterns in self.element_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    element = ScriptElement(
                        element_id=f"{scene_id}_{element_type}_{len(elements)}",
                        element_type=element_type,
                        text=match.group(1) if match.groups() else match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.8,  # Could be improved with ML
                        scene_id=scene_id,
                        context={"line": text.count('\n', 0, match.start()) + 1}
                    )
                    elements.append(element)
        
        return elements
    
    def _generate_synopsis(self, scene_text: str) -> str:
        """Generate a brief synopsis of the scene."""
        # Simple approach: take first few sentences
        sentences = re.split(r'[.!?]+', scene_text)[:3]
        synopsis = ' '.join(sentences).strip()
        return synopsis[:200] + '...' if len(synopsis) > 200 else synopsis
    
    def _organize_elements(self, scenes: List[ParsedScene]) -> Dict[str, List[ScriptElement]]:
        """Organize elements by type across all scenes."""
        organized = {element_type: [] for element_type in ScriptElementType}
        
        for scene in scenes:
            for element in scene.elements:
                organized[element.element_type].append(element)
        
        return organized
    
    def _estimate_pages(self, scenes: List[ParsedScene]) -> float:
        """Estimate total page count based on scene text length."""
        total_chars = sum(len(scene.raw_text) for scene in scenes)
        # Rough estimate: 1 page ≈ 3000 characters
        return round(total_chars / 3000, 1)
    
    def _extract_scene_text(self, scene_elem) -> str:
        """Extract full text content from scene element."""
        text_parts = []
        for elem in scene_elem.iter():
            if elem.text:
                text_parts.append(elem.text)
            if elem.tail:
                text_parts.append(elem.tail)
        return ' '.join(text_parts)
    
    async def validate_script(self, parsed_script: ParsedScript) -> Dict[str, Any]:
        """Validate the parsed script for completeness and consistency."""
        issues = []
        
        # Check for missing elements
        if not parsed_script.scenes:
            issues.append("No scenes found")
        
        # Check for duplicate scene numbers
        scene_numbers = [scene.scene_number for scene in parsed_script.scenes]
        if len(scene_numbers) != len(set(scene_numbers)):
            issues.append("Duplicate scene numbers found")
        
        # Check for empty scenes
        empty_scenes = [scene.scene_number for scene in parsed_script.scenes if not scene.raw_text.strip()]
        if empty_scenes:
            issues.append(f"Empty scenes: {empty_scenes}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "total_elements": sum(len(elements) for elements in parsed_script.elements_by_type.values()),
            "total_characters": len(parsed_script.characters),
            "total_locations": len(parsed_script.locations)
        }