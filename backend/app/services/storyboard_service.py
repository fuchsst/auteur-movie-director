"""
Storyboard/Pre-vis Integration Service
STORY-087 Implementation

Service for managing storyboard creation and pre-visualization generation,
integrating with the professional script breakdown system.
"""

import json
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from app.models.storyboard_models import (
    StoryboardSequence, StoryboardShot, StoryboardFrame, 
    PrevisGenerationRequest, PrevisGenerationResult, StoryboardTemplate,
    StoryboardFrameStatus, CameraMovement, ShotComposition
)
from app.models.breakdown_models import SceneBreakdown, BreakdownElement
from app.models.generative_shotlist import ShotSpecification
from app.services.breakdown_service import BreakdownService
import aiofiles


class StoryboardService:
    """Service for managing storyboard and pre-visualization workflows."""
    
    def __init__(self, project_root: str, breakdown_service: BreakdownService):
        self.project_root = Path(project_root)
        self.breakdown_service = breakdown_service
        self.sequences: Dict[str, StoryboardSequence] = {}
        self.templates: Dict[str, StoryboardTemplate] = {}
        
        # Ensure directories exist
        self.storyboard_dir = self.project_root / "02_Story" / "storyboards"
        self.previs_dir = self.project_root / "02_Story" / "previs"
        self.storyboard_dir.mkdir(parents=True, exist_ok=True)
        self.previs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize default templates
        self._initialize_templates()
    
    def _initialize_templates(self) -> None:
        """Initialize default storyboard templates."""
        
        # Standard template
        standard_template = StoryboardTemplate(
            template_id="standard",
            template_name="Standard Storyboard",
            description="Standard storyboard template with basic camera setups",
            default_frames_per_shot=3,
            default_shot_duration=3.0,
            camera_presets={
                "standard": {
                    "focal_length": 35,
                    "camera_height": "eye_level",
                    "movement": "static"
                },
                "closeup": {
                    "focal_length": 85,
                    "camera_height": "eye_level",
                    "movement": "static"
                },
                "wide": {
                    "focal_length": 24,
                    "camera_height": "eye_level",
                    "movement": "static"
                }
            },
            composition_templates={
                "rule_of_thirds": {
                    "grid": "3x3",
                    "subject_position": "intersection"
                },
                "center": {
                    "grid": "center",
                    "subject_position": "center"
                }
            }
        )
        
        # Cinematic template
        cinematic_template = StoryboardTemplate(
            template_id="cinematic",
            template_name="Cinematic Storyboard",
            description="Cinematic template with advanced camera movements",
            default_frames_per_shot=4,
            default_shot_duration=4.0,
            camera_presets={
                "tracking": {
                    "focal_length": 35,
                    "camera_height": "eye_level",
                    "movement": "tracking",
                    "movement_speed": "slow"
                },
                "dolly": {
                    "focal_length": 35,
                    "camera_height": "eye_level",
                    "movement": "dolly",
                    "movement_direction": "in"
                },
                "crane": {
                    "focal_length": 24,
                    "camera_height": "high",
                    "movement": "crane",
                    "movement_direction": "down"
                }
            },
            composition_templates={
                "leading_lines": {
                    "grid": "dynamic",
                    "subject_position": "leading"
                },
                "depth": {
                    "grid": "foreground_midground_background",
                    "subject_position": "midground"
                }
            },
            visual_style="cinematic",
            color_palette=["#1a1a1a", "#2c3e50", "#34495e", "#7f8c8d", "#95a5a6"]
        )
        
        self.templates[standard_template.template_id] = standard_template
        self.templates[cinematic_template.template_id] = cinematic_template
    
    async def create_sequence_from_breakdown(
        self, 
        project_id: str, 
        scene_id: str,
        template_id: str = "standard"
    ) -> StoryboardSequence:
        """Create storyboard sequence from scene breakdown."""
        
        # Get scene breakdown
        breakdown = await self.breakdown_service.get_breakdown(project_id)
        if not breakdown or scene_id not in breakdown.scenes:
            raise ValueError(f"Scene {scene_id} not found")
        
        scene_breakdown = breakdown.scenes[scene_id]
        
        # Create sequence
        sequence = StoryboardSequence(
            sequence_id=f"sequence_{scene_id}",
            scene_id=scene_id,
            sequence_name=f"Storyboard for {scene_breakdown.scene_heading}",
            description=f"Visual storyboard for scene {scene_breakdown.scene_number}",
            scene_breakdown=scene_breakdown
        )
        
        # Apply template
        template = self.templates.get(template_id, self.templates["standard"])
        template.apply_template(sequence)
        
        # Generate initial shots based on scene elements
        await self._generate_initial_shots(sequence, scene_breakdown)
        
        # Save sequence
        await self._save_sequence(sequence)
        
        self.sequences[sequence.sequence_id] = sequence
        return sequence
    
    async def _generate_initial_shots(
        self, 
        sequence: StoryboardSequence, 
        scene_breakdown: SceneBreakdown
    ) -> None:
        """Generate initial shots based on scene breakdown."""
        
        # Determine shot count based on scene complexity
        total_elements = scene_breakdown.get_total_elements()
        base_shots = max(1, min(5, total_elements // 3))
        
        # Create shots
        for i in range(base_shots):
            shot = StoryboardShot(
                shot_id=f"shot_{sequence.sequence_id}_{i+1}",
                scene_id=sequence.scene_id,
                shot_number=i+1,
                shot_type=self._determine_shot_type(i, scene_breakdown),
                duration=3.0,
                characters=scene_breakdown.characters.copy()
            )
            
            # Link elements to this shot
            all_elements = []
            for elements in scene_breakdown.elements.values():
                all_elements.extend(elements)
            
            # Distribute elements across shots
            shot.linked_elements = [
                elem.element_id 
                for j, elem in enumerate(all_elements) 
                if j % base_shots == i
            ]
            
            # Add default frames
            await self._add_default_frames(shot)
            
            sequence.add_shot(shot)
    
    def _determine_shot_type(self, index: int, scene_breakdown: SceneBreakdown) -> str:
        """Determine shot type based on scene content and index."""
        
        # Simple heuristic for shot types
        if index == 0:
            return "establishing"
        elif scene_breakdown.characters and index < len(scene_breakdown.characters):
            return f"character_{scene_breakdown.characters[index]}"
        elif "locations" in scene_breakdown.elements and scene_breakdown.elements["locations"]:
            return "location_detail"
        else:
            return "action"
    
    async def _add_default_frames(self, shot: StoryboardShot) -> None:
        """Add default frames to a shot."""
        
        # Add 3 default frames per shot
        for i in range(3):
            frame = StoryboardFrame(
                frame_id=f"frame_{shot.shot_id}_{i+1}",
                scene_id=shot.scene_id,
                shot_number=shot.shot_number,
                frame_number=i+1,
                description=f"Frame {i+1} of shot {shot.shot_number}",
                camera_angle="eye_level" if i == 0 else ("high_angle" if i == 1 else "low_angle"),
                composition=ShotComposition.MEDIUM,
                focal_length=35.0
            )
            
            shot.add_frame(frame)
    
    async def add_frame(
        self, 
        sequence_id: str, 
        shot_id: str, 
        frame_data: Dict[str, Any]
    ) -> StoryboardFrame:
        """Add a new frame to a shot."""
        
        if sequence_id not in self.sequences:
            raise ValueError(f"Sequence {sequence_id} not found")
        
        sequence = self.sequences[sequence_id]
        shot = next((s for s in sequence.shots if s.shot_id == shot_id), None)
        
        if not shot:
            raise ValueError(f"Shot {shot_id} not found")
        
        frame = StoryboardFrame(
            frame_id=f"frame_{shot_id}_{len(shot.frames)+1}",
            scene_id=sequence.scene_id,
            shot_number=shot.shot_number,
            frame_number=len(shot.frames)+1,
            **frame_data
        )
        
        shot.add_frame(frame)
        sequence._recalculate_duration()
        
        await self._save_sequence(sequence)
        return frame
    
    async def update_frame(
        self, 
        sequence_id: str, 
        shot_id: str, 
        frame_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update a storyboard frame."""
        
        if sequence_id not in self.sequences:
            return False
        
        sequence = self.sequences[sequence_id]
        shot = next((s for s in sequence.shots if s.shot_id == shot_id), None)
        
        if not shot:
            return False
        
        frame = next((f for f in shot.frames if f.frame_id == frame_id), None)
        
        if not frame:
            return False
        
        # Update frame
        for key, value in updates.items():
            if hasattr(frame, key):
                setattr(frame, key, value)
        
        frame.updated_at = datetime.now()
        await self._save_sequence(sequence)
        
        return True
    
    async def generate_previs(
        self, 
        request: PrevisGenerationRequest
    ) -> PrevisGenerationResult:
        """Generate pre-visualization for a sequence."""
        
        if request.sequence_id not in self.sequences:
            raise ValueError(f"Sequence {request.sequence_id} not found")
        
        sequence = self.sequences[request.sequence_id]
        
        # Create result
        result = PrevisGenerationResult(
            result_id=f"previs_{request.sequence_id}_{uuid.uuid4().hex[:8]}",
            sequence_id=request.sequence_id,
            status="processing"
        )
        
        # Start generation in background
        asyncio.create_task(self._generate_previs_async(sequence, request, result))
        
        return result
    
    async def _generate_previs_async(
        self, 
        sequence: StoryboardSequence, 
        request: PrevisGenerationRequest,
        result: PrevisGenerationResult
    ) -> None:
        """Generate pre-visualization asynchronously."""
        
        try:
            # Simulate generation process
            total_frames = sequence.get_frame_count()
            
            for i in range(total_frames):
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                # Update progress
                result.progress = (i + 1) / total_frames
                
                # Generate frame path
                frame_path = self.previs_dir / f"{result.result_id}_frame_{i+1:04d}.png"
                result.frame_paths.append(str(frame_path))
                
                # Create placeholder frame
                placeholder_content = f"Pre-vis frame {i+1} for sequence {sequence.sequence_id}"
                async with aiofiles.open(frame_path, 'w') as f:
                    await f.write(placeholder_content)
            
            # Generate sequence file
            sequence_path = self.previs_dir / f"{result.result_id}_sequence.json"
            sequence_data = {
                "sequence": sequence.model_dump(),
                "generation_params": request.model_dump(),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_frames": total_frames,
                    "duration": sequence.total_duration
                }
            }
            
            async with aiofiles.open(sequence_path, 'w') as f:
                await f.write(json.dumps(sequence_data, indent=2))
            
            result.sequence_path = str(sequence_path)
            result.status = "completed"
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)
            result.completed_at = datetime.now()
    
    async def get_sequence(self, sequence_id: str) -> Optional[StoryboardSequence]:
        """Get storyboard sequence by ID."""
        if sequence_id in self.sequences:
            return self.sequences[sequence_id]
        
        # Try to load from file
        sequence_file = self.storyboard_dir / f"{sequence_id}.json"
        if sequence_file.exists():
            return await self._load_sequence_from_file(sequence_file)
        
        return None
    
    async def get_previs_result(self, result_id: str) -> Optional[PrevisGenerationResult]:
        """Get pre-vis generation result."""
        # In a real implementation, this would query a database
        # For now, simulate by checking if files exist
        result_file = self.previs_dir / f"{result_id}_result.json"
        if result_file.exists():
            async with aiofiles.open(result_file, 'r') as f:
                data = json.loads(await f.read())
                return PrevisGenerationResult(**data)
        
        return None
    
    async def export_sequence(
        self, 
        sequence_id: str, 
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export storyboard sequence."""
        
        sequence = await self.get_sequence(sequence_id)
        if not sequence:
            raise ValueError(f"Sequence {sequence_id} not found")
        
        if format == "json":
            return {
                "sequence": sequence.model_dump(),
                "export_metadata": {
                    "format": "json",
                    "exported_at": datetime.now().isoformat(),
                    "total_shots": sequence.get_shot_count(),
                    "total_frames": sequence.get_frame_count(),
                    "total_duration": sequence.total_duration
                }
            }
        elif format == "pdf":
            # Placeholder for PDF export
            return {
                "format": "pdf",
                "message": "PDF export not yet implemented",
                "sequence": sequence.model_dump()
            }
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def _save_sequence(self, sequence: StoryboardSequence) -> None:
        """Save sequence to file."""
        sequence_file = self.storyboard_dir / f"{sequence.sequence_id}.json"
        sequence_file.write_text(sequence.model_dump_json(indent=2))
    
    async def _load_sequence_from_file(self, file_path: Path) -> StoryboardSequence:
        """Load sequence from file."""
        data = json.loads(file_path.read_text())
        sequence = StoryboardSequence(**data)
        self.sequences[sequence.sequence_id] = sequence
        return sequence
    
    async def sync_with_shotlist(
        self, 
        sequence_id: str, 
        shotlist: List[ShotSpecification]
    ) -> bool:
        """Sync storyboard with generative shot list."""
        
        sequence = await self.get_sequence(sequence_id)
        if not sequence:
            return False
        
        # Clear existing shots
        sequence.shots.clear()
        
        # Create shots from shotlist
        for i, shot_spec in enumerate(shotlist):
            shot = StoryboardShot(
                shot_id=f"shot_{sequence_id}_{i+1}",
                scene_id=sequence.scene_id,
                shot_number=i+1,
                shot_type=shot_spec.shot_type,
                duration=float(shot_spec.duration) if shot_spec.duration else 3.0,
                camera_setup={
                    "focal_length": shot_spec.focal_length,
                    "camera_angle": shot_spec.camera_angle,
                    "camera_height": shot_spec.camera_height
                },
                lighting_setup={
                    "lighting_type": shot_spec.lighting_type,
                    "intensity": shot_spec.lighting_intensity
                }
            )
            
            # Map shot requirements to linked elements
            if shot_spec.requirements:
                shot.linked_elements = [
                    req.get("element_id") 
                    for req in shot_spec.requirements 
                    if req.get("element_id")
                ]
            
            sequence.add_shot(shot)
        
        sequence._recalculate_duration()
        await self._save_sequence(sequence)
        
        return True