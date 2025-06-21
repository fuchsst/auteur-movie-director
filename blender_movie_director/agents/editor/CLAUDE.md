# Editor Agent - Post-Production Assembly

## Role
Final agent in the production chain, responsible for assembling the finished product by sequencing video clips, synchronizing audio, and applying enhancements.

## Responsibilities
- **Video Restoration** - Enhance generated clips with SeedVR2
- **Sequence Assembly** - Arrange clips in Blender's Video Sequence Editor
- **Audio Synchronization** - Align dialogue and effects with video
- **Final Enhancement** - Apply color grading and effects

## Post-Production Pipeline
1. **Quality Enhancement** - Route clips through SeedVR2 restoration
2. **VSE Assembly** - Programmatically add clips to Video Sequence Editor
3. **Audio Sync** - Align sound designer's audio tracks
4. **Final Polish** - Apply transitions and effects

## Implementation Pattern
```python
class EditorAgent(Agent):
    role = "Post-Production Specialist"
    goal = "Assemble polished final film sequences"
    backstory = "Expert editor with knowledge of pacing and assembly"
    
    tools = [
        video_restoration_tool,
        vse_assembly_tool,
        audio_sync_tool,
        final_enhancement_tool
    ]
```

## Blender VSE Integration
```python
def assemble_scene_in_vse(scene_shots):
    """Programmatically assemble shots in Video Sequence Editor"""
    for i, shot in enumerate(scene_shots):
        # Add video strip
        bpy.ops.sequencer.movie_strip_add(
            filepath=shot.generated_video_path,
            frame_start=i * shot.duration
        )
        
        # Add audio strips
        add_audio_tracks(shot, i * shot.duration)
```

## Reference
- [Video Sequence Editor](/.bmad-core/data/bpy-data-guide.md)
- [SeedVR2 Integration](/.bmad-core/data/comfyui-api-guide.md)