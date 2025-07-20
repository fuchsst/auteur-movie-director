"""
Breakdown Service
STORY-086 Implementation

Provides comprehensive breakdown management for the professional script breakdown interface,
including scene analysis, element detection, asset linking, and export capabilities.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from app.models.breakdown_models import (
    ScriptBreakdown, SceneBreakdown, BreakdownElement, ElementCategory,
    BreakdownElementStatus, BreakdownExportRequest, BreakdownExportFormat
)
from app.services.script_parser import ScriptParserService, ParsedScript
from app.services.asset_registry import AssetRegistry
from app.models.asset_types import AssetType, create_asset_from_dict
import uuid


class BreakdownService:
    """Service for managing script breakdowns and production elements."""
    
    def __init__(self, project_root: str, asset_registry: AssetRegistry):
        self.project_root = Path(project_root)
        self.asset_registry = asset_registry
        self.parser = ScriptParserService()
        self.breakdowns: Dict[str, ScriptBreakdown] = {}
        
        # Ensure breakdown directory exists
        self.breakdown_dir = self.project_root / "02_Story" / "breakdowns"
        self.breakdown_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_breakdown_from_script(
        self, 
        project_id: str, 
        project_name: str,
        script_path: str,
        script_content: bytes = None
    ) -> ScriptBreakdown:
        """Create a complete breakdown from a script file."""
        
        # Parse the script
        parsed_script = await self.parser.parse_file(script_path, script_content)
        
        # Create breakdown
        breakdown = ScriptBreakdown(
            project_id=project_id,
            project_name=project_name,
            script_title=parsed_script.title,
            script_author=parsed_script.author,
            total_scenes=parsed_script.total_scenes,
            total_pages=parsed_script.total_pages,
            all_characters=parsed_script.characters,
            all_locations=parsed_script.locations,
            scene_order=[scene.scene_id for scene in parsed_script.scenes]
        )
        
        # Process each scene
        for parsed_scene in parsed_script.scenes:
            scene_breakdown = await self._create_scene_breakdown(parsed_scene)
            breakdown.scenes[scene_breakdown.scene_id] = scene_breakdown
        
        # Calculate totals
        breakdown.calculate_totals()
        breakdown.validate_breakdown()
        
        # Save breakdown
        await self._save_breakdown(breakdown)
        
        self.breakdowns[project_id] = breakdown
        return breakdown
    
    async def _create_scene_breakdown(self, parsed_scene) -> SceneBreakdown:
        """Create a scene breakdown from parsed scene data."""
        
        location, time_of_day, interior_exterior = self._parse_scene_details(
            parsed_scene.scene_heading
        )
        
        scene_breakdown = SceneBreakdown(
            scene_id=parsed_scene.scene_id,
            scene_number=parsed_scene.scene_number,
            scene_heading=parsed_scene.scene_heading,
            synopsis=parsed_scene.synopsis,
            location=location,
            time_of_day=time_of_day,
            interior_exterior=interior_exterior,
            characters=parsed_scene.characters,
            estimated_pages=parsed_scene.estimated_pages if hasattr(parsed_scene, 'estimated_pages') else 0.5,
            estimated_duration=parsed_scene.estimated_pages * 60 if hasattr(parsed_scene, 'estimated_pages') else 30.0,
            day_night=time_of_day
        )
        
        # Process detected elements
        await self._process_detected_elements(scene_breakdown, parsed_scene)
        
        return scene_breakdown
    
    def _parse_scene_details(self, scene_heading: str) -> Tuple[str, str, str]:
        """Parse scene heading for location, time, and interior/exterior."""
        heading = scene_heading.strip()
        
        # Determine interior/exterior
        if heading.upper().startswith("INT."):
            interior_exterior = "INT"
            location_part = heading[4:].strip()
        elif heading.upper().startswith("EXT."):
            interior_exterior = "EXT"
            location_part = heading[4:].strip()
        elif heading.upper().startswith("INT./EXT.") or heading.upper().startswith("EXT./INT."):
            interior_exterior = "INT/EXT"
            location_part = heading[9:].strip()
        else:
            interior_exterior = "UNKNOWN"
            location_part = heading
        
        # Extract location and time
        location_parts = location_part.split(" - ")
        location = location_parts[0].strip() if location_parts else location_part
        time_of_day = location_parts[1].strip() if len(location_parts) > 1 else "DAY"
        
        return location, time_of_day, interior_exterior
    
    async def _process_detected_elements(self, scene_breakdown: SceneBreakdown, parsed_scene) -> None:
        """Process detected elements and create breakdown elements."""
        
        # Initialize element categories
        for category in ElementCategory:
            scene_breakdown.elements[category] = []
        
        # Map parser element types to our categories
        type_mapping = {
            "character": ElementCategory.CAST,
            "prop": ElementCategory.PROPS,
            "wardrobe": ElementCategory.WARDROBE,
            "vehicle": ElementCategory.VEHICLES,
            "location": ElementCategory.LOCATIONS,
            "sound": ElementCategory.SOUNDS,
            "sfx": ElementCategory.SFX,
            "set_dressing": ElementCategory.SET_DRESSING,
            "music": ElementCategory.MUSIC,
        }
        
        # Process elements from parser
        for detected_element in parsed_scene.elements:
            element_type = type_mapping.get(detected_element.element_type)
            if element_type:
                breakdown_element = BreakdownElement(
                    element_id=detected_element.element_id,
                    element_type=element_type,
                    name=detected_element.text,
                    description=f"{element_type.value}: {detected_element.text}",
                    scene_id=scene_breakdown.scene_id,
                    script_position={
                        "start": detected_element.start_pos,
                        "end": detected_element.end_pos,
                        "line": detected_element.context.get("line", 0)
                    },
                    context_text=parsed_scene.raw_text[
                        max(0, detected_element.start_pos-50):
                        min(len(parsed_scene.raw_text), detected_element.end_pos+50)
                    ],
                    confidence=detected_element.confidence,
                    status=BreakdownElementStatus.DETECTED
                )
                scene_breakdown.elements[element_type].append(breakdown_element)
    
    async def update_element_status(
        self, 
        project_id: str, 
        scene_id: str, 
        element_id: str, 
        new_status: BreakdownElementStatus
    ) -> bool:
        """Update the status of a breakdown element."""
        
        if project_id not in self.breakdowns:
            return False
        
        breakdown = self.breakdowns[project_id]
        if scene_id not in breakdown.scenes:
            return False
        
        scene = breakdown.scenes[scene_id]
        
        for category_elements in scene.elements.values():
            for element in category_elements:
                if element.element_id == element_id:
                    element.status = new_status
                    element.updated_at = datetime.now()
                    
                    # If creating an asset, create it in registry
                    if new_status == BreakdownElementStatus.CREATED and not element.asset_id:
                        await self._create_asset_from_element(element, project_id)
                    
                    await self._save_breakdown(breakdown)
                    return True
        
        return False
    
    async def _create_asset_from_element(self, element: BreakdownElement, project_id: str) -> str:
        """Create an asset from a breakdown element."""
        
        asset_data = {
            "asset_id": str(uuid.uuid4()),
            "asset_type": self._map_element_to_asset_type(element.element_type),
            "name": element.name,
            "description": element.description,
            "category": element.element_type.value,
            "tags": ["breakdown", element.element_type.value],
            "created_by": "breakdown_system"
        }
        
        asset = create_asset_from_dict(asset_data)
        asset_id = await self.asset_registry.register_asset(asset)
        
        element.asset_id = asset_id
        return asset_id
    
    def _map_element_to_asset_type(self, element_type: ElementCategory) -> AssetType:
        """Map element category to asset type."""
        mapping = {
            ElementCategory.CAST: AssetType.CHARACTER,
            ElementCategory.PROPS: AssetType.PROP,
            ElementCategory.WARDROBE: AssetType.WARDROBE,
            ElementCategory.VEHICLES: AssetType.VEHICLE,
            ElementCategory.LOCATIONS: AssetType.LOCATION,
            ElementCategory.SOUNDS: AssetType.SOUND,
            ElementCategory.SFX: AssetType.SFX,
            ElementCategory.SET_DRESSING: AssetType.SET_DRESSING,
            ElementCategory.MUSIC: AssetType.MUSIC,
            ElementCategory.SPECIAL_EFFECTS: AssetType.SFX,
        }
        return mapping.get(element_type, AssetType.PROP)
    
    async def add_custom_element(
        self,
        project_id: str,
        scene_id: str,
        element_data: Dict[str, Any]
    ) -> BreakdownElement:
        """Add a custom element to a scene breakdown."""
        
        if project_id not in self.breakdowns:
            raise ValueError(f"Project {project_id} not found")
        
        breakdown = self.breakdowns[project_id]
        if scene_id not in breakdown.scenes:
            raise ValueError(f"Scene {scene_id} not found")
        
        element = BreakdownElement(
            element_id=f"custom_{scene_id}_{uuid.uuid4().hex[:8]}",
            element_type=ElementCategory(element_data["element_type"]),
            name=element_data["name"],
            description=element_data.get("description", ""),
            scene_id=scene_id,
            quantity=element_data.get("quantity", 1),
            notes=element_data.get("notes", ""),
            special_instructions=element_data.get("special_instructions", ""),
            estimated_cost=element_data.get("estimated_cost", 0.0),
            estimated_time=element_data.get("estimated_time", 0.0),
            context_text=element_data.get("context_text", ""),
            confidence=1.0,
            status=BreakdownElementStatus.CONFIRMED
        )
        
        # Add to appropriate category
        category = element.element_type
        if category not in breakdown.scenes[scene_id].elements:
            breakdown.scenes[scene_id].elements[category] = []
        breakdown.scenes[scene_id].elements[category].append(element)
        
        # Update totals
        breakdown.calculate_totals()
        await self._save_breakdown(breakdown)
        
        return element
    
    async def get_breakdown(self, project_id: str) -> Optional[ScriptBreakdown]:
        """Get breakdown for a project."""
        if project_id in self.breakdowns:
            return self.breakdowns[project_id]
        
        # Try to load from file
        breakdown_file = self.breakdown_dir / f"{project_id}_breakdown.json"
        if breakdown_file.exists():
            return await self._load_breakdown_from_file(breakdown_file)
        
        return None
    
    async def export_breakdown(
        self, 
        project_id: str, 
        export_request: BreakdownExportRequest
    ) -> Dict[str, Any]:
        """Export breakdown data in requested format."""
        
        breakdown = await self.get_breakdown(project_id)
        if not breakdown:
            raise ValueError(f"Breakdown not found for project {project_id}")
        
        # Filter scenes if specified
        scenes_to_export = []
        if export_request.include_scenes:
            scenes_to_export = [
                scene for scene_id, scene in breakdown.scenes.items()
                if scene_id in export_request.include_scenes
            ]
        else:
            scenes_to_export = list(breakdown.scenes.values())
        
        # Filter elements by category and confidence
        filtered_scenes = []
        for scene in scenes_to_export:
            filtered_scene = scene.copy()
            filtered_scene.elements = {}
            
            for category, elements in scene.elements.items():
                if export_request.filter_categories and category not in export_request.filter_categories:
                    continue
                
                filtered_elements = [
                    e for e in elements 
                    if e.confidence >= export_request.min_confidence
                ]
                filtered_scene.elements[category] = filtered_elements
            
            filtered_scenes.append(filtered_scene)
        
        # Export based on format
        if export_request.export_format == BreakdownExportFormat.JSON:
            return self._export_json(breakdown, filtered_scenes, export_request)
        elif export_request.export_format == BreakdownExportFormat.CSV:
            return self._export_csv(breakdown, filtered_scenes, export_request)
        elif export_request.export_format == BreakdownExportFormat.PDF:
            return self._export_pdf(breakdown, filtered_scenes, export_request)
        else:
            raise ValueError(f"Unsupported export format: {export_request.export_format}")
    
    def _export_json(self, breakdown: ScriptBreakdown, scenes: List[SceneBreakdown], request: BreakdownExportRequest) -> Dict[str, Any]:
        """Export as JSON."""
        return {
            "breakdown": breakdown.model_dump(exclude_none=True),
            "exported_scenes": [scene.model_dump(exclude_none=True) for scene in scenes],
            "export_metadata": {
                "format": "json",
                "timestamp": datetime.now().isoformat(),
                "filtered": bool(request.filter_categories),
                "include_costs": request.include_costs,
                "include_notes": request.include_notes
            }
        }
    
    def _export_csv(self, breakdown: ScriptBreakdown, scenes: List[SceneBreakdown], request: BreakdownExportRequest) -> str:
        """Export as CSV."""
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = ["Scene", "Scene Heading", "Element Type", "Name", "Description", "Quantity"]
        if request.include_costs:
            headers.extend(["Estimated Cost", "Total Cost"])
        if request.include_notes:
            headers.append("Notes")
        
        writer.writerow(headers)
        
        # Data
        for scene in scenes:
            for category, elements in scene.elements.items():
                for element in elements:
                    row = [
                        scene.scene_number,
                        scene.scene_heading,
                        category.value,
                        element.name,
                        element.description,
                        element.quantity
                    ]
                    
                    if request.include_costs:
                        row.extend([element.estimated_cost, element.estimated_cost * element.quantity])
                    
                    if request.include_notes:
                        row.append(element.notes)
                    
                    writer.writerow(row)
        
        return output.getvalue()
    
    def _export_pdf(self, breakdown: ScriptBreakdown, scenes: List[SceneBreakdown], request: BreakdownExportRequest) -> bytes:
        """Export as PDF."""
        # This would require a PDF library like reportlab
        # For now, return placeholder
        return b"PDF export placeholder - would use reportlab"
    
    async def _save_breakdown(self, breakdown: ScriptBreakdown) -> None:
        """Save breakdown to file."""
        breakdown_file = self.breakdown_dir / f"{breakdown.project_id}_breakdown.json"
        breakdown_file.write_text(breakdown.model_dump_json(indent=2))
    
    async def _load_breakdown_from_file(self, file_path: Path) -> ScriptBreakdown:
        """Load breakdown from file."""
        data = json.loads(file_path.read_text())
        breakdown = ScriptBreakdown(**data)
        self.breakdowns[breakdown.project_id] = breakdown
        return breakdown
    
    async def sync_with_canvas(self, project_id: str, canvas_data: Dict[str, Any]) -> bool:
        """Sync breakdown data with Production Canvas."""
        # Implementation would integrate with canvas system
        # For now, return success
        return True