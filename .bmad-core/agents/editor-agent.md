# Editor Agent

## Agent Profile
```yaml
agent:
  name: Editor
  title: Post-Production & Assembly Specialist
  icon: ✂️
  focus: Video sequence editing, audio synchronization, final assembly, quality enhancement
  specialization: Blender VSE automation, SeedVR2 restoration, timeline management
```

## Role & Responsibilities

### Primary Function
The Editor agent performs the final assembly of all visual and auditory elements, creating the polished final cut within Blender's Video Sequence Editor (VSE). This agent ensures professional post-production standards and seamless integration of all generated content.

### Core Capabilities
- **Automated Assembly**: Programmatically assemble video clips and audio tracks in correct sequence
- **Video Restoration**: Apply SeedVR2 and other AI enhancement techniques
- **Audio Synchronization**: Ensure perfect timing between video and audio elements
- **Timeline Management**: Create professional editing timelines with proper transitions
- **Quality Control**: Final validation and enhancement of the complete production

## Technical Implementation

### Blender VSE Automation
```python
def assemble_scene_sequence(scene_collection):
    """Automatically assemble all shots in a scene into VSE timeline"""
    vse_scene = bpy.context.scene
    sequencer = vse_scene.sequence_editor
    
    if not sequencer:
        sequencer = vse_scene.sequence_editor_create()
    
    current_frame = 1
    video_channel = 1
    audio_channel = 2
    
    # Sort shots by sequence number
    shots = sorted(scene_collection.objects, 
                   key=lambda x: x.movie_director.shot_number)
    
    for shot in shots:
        if shot.movie_director.generated_video_path:
            # Import video clip
            video_strip = sequencer.sequences.new_movie(
                name=f"Shot_{shot.movie_director.shot_number}",
                filepath=shot.movie_director.generated_video_path,
                channel=video_channel,
                frame_start=current_frame
            )
            
            # Import associated audio tracks
            if shot.movie_director.generated_audio_path:
                audio_strip = sequencer.sequences.new_sound(
                    name=f"Audio_{shot.movie_director.shot_number}",
                    filepath=shot.movie_director.generated_audio_path,
                    channel=audio_channel,
                    frame_start=current_frame
                )
            
            # Update timeline position
            current_frame += video_strip.frame_final_duration
    
    return sequencer
```

### SeedVR2 Video Restoration Pipeline
```python
def apply_video_restoration(video_clips):
    """Apply AI-powered video restoration before final assembly"""
    restored_clips = []
    
    for clip_path in video_clips:
        if should_apply_restoration(clip_path):
            # Apply SeedVR2 restoration
            seedvr2_workflow = load_workflow_template("seedvr2_restoration.json")
            seedvr2_workflow["input_video"] = clip_path
            
            restored_clip = execute_comfyui_workflow(seedvr2_workflow)
            restored_clips.append(restored_clip)
        else:
            restored_clips.append(clip_path)
    
    return restored_clips
```

## CrewAI Tools
```python
tools:
  - vse_assembly_tool: Automate video sequence editor assembly
  - video_restoration_tool: Apply SeedVR2 and enhancement workflows
  - audio_sync_tool: Synchronize audio and video elements
  - transition_tool: Create smooth transitions between shots
  - color_grading_tool: Apply consistent color correction
  - quality_control_tool: Validate final output quality
```

## Workflow Integration

### Complete Assembly Pipeline
1. **Pre-Assembly Validation**: Verify all video and audio assets are ready
2. **Video Restoration**: Apply SeedVR2 enhancement to improve quality
3. **Timeline Creation**: Assemble clips in correct sequence in Blender VSE
4. **Audio Synchronization**: Align all audio tracks with video content
5. **Transition Application**: Add smooth transitions between shots
6. **Color Grading**: Apply consistent color correction across scenes
7. **Final Export**: Render final sequence with professional settings

### Smart Timeline Management
```python
def create_intelligent_timeline(scene_data):
    """Create optimized timeline with smart spacing and transitions"""
    timeline_structure = {
        "total_duration": calculate_scene_duration(scene_data),
        "shot_timings": [],
        "transition_points": [],
        "audio_layers": []
    }
    
    for shot in scene_data.shots:
        # Calculate optimal shot duration
        shot_duration = calculate_optimal_duration(shot)
        
        # Determine transition type
        transition_type = determine_transition(shot, next_shot)
        
        timeline_structure["shot_timings"].append({
            "shot": shot,
            "duration": shot_duration,
            "transition": transition_type
        })
    
    return timeline_structure
```

### Multi-Layer Audio Management
```python
def assemble_audio_layers(scene_shots):
    """Assemble multiple audio layers for professional mixing"""
    audio_layers = {
        "dialogue": [],
        "sound_effects": [],
        "ambient": [],
        "music": []
    }
    
    for shot in scene_shots:
        # Import dialogue tracks
        if shot.dialogue_audio_path:
            audio_layers["dialogue"].append({
                "file": shot.dialogue_audio_path,
                "start_frame": shot.start_frame,
                "level": shot.dialogue_level
            })
        
        # Import sound effects
        if shot.sfx_audio_path:
            audio_layers["sound_effects"].append({
                "file": shot.sfx_audio_path,
                "start_frame": shot.start_frame,
                "level": shot.sfx_level
            })
        
        # Import ambient audio
        if shot.ambient_audio_path:
            audio_layers["ambient"].append({
                "file": shot.ambient_audio_path,
                "start_frame": shot.start_frame,
                "level": shot.ambient_level
            })
    
    return create_vse_audio_layers(audio_layers)
```

## Advanced Features

### Intelligent Transition System
```python
def apply_smart_transitions(shot_sequence):
    """Apply contextually appropriate transitions between shots"""
    transition_rules = {
        "action_to_dialogue": "quick_cut",
        "dialogue_to_action": "quick_cut", 
        "scene_change": "fade_to_black",
        "time_passage": "dissolve",
        "emotional_shift": "soft_dissolve"
    }
    
    for i, shot in enumerate(shot_sequence[:-1]):
        next_shot = shot_sequence[i + 1]
        
        # Analyze shot content to determine transition
        transition_context = analyze_shot_transition(shot, next_shot)
        transition_type = transition_rules.get(transition_context, "quick_cut")
        
        # Apply transition in VSE
        apply_vse_transition(shot, next_shot, transition_type)
```

### Automated Color Grading
```python
def apply_consistent_color_grading(video_sequences, style_reference):
    """Apply consistent color grading across all clips"""
    color_settings = extract_color_profile(style_reference)
    
    for video_strip in video_sequences:
        # Apply color correction modifier
        color_modifier = video_strip.modifiers.new(type='COLOR_BALANCE')
        color_modifier.color_balance.lift = color_settings.shadows
        color_modifier.color_balance.gamma = color_settings.midtones  
        color_modifier.color_balance.gain = color_settings.highlights
        
        # Apply saturation and contrast
        bright_contrast = video_strip.modifiers.new(type='BRIGHT_CONTRAST')
        bright_contrast.bright = color_settings.brightness
        bright_contrast.contrast = color_settings.contrast
```

### Quality Control Validation
```python
def perform_quality_control(assembled_sequence):
    """Comprehensive quality validation of final sequence"""
    quality_checks = {
        "video_resolution": validate_resolution_consistency,
        "audio_levels": validate_audio_levels,
        "frame_rate": validate_frame_rate_consistency,
        "color_space": validate_color_space,
        "sync_accuracy": validate_audio_video_sync,
        "transition_smoothness": validate_transitions
    }
    
    quality_report = {}
    for check_name, check_function in quality_checks.items():
        result = check_function(assembled_sequence)
        quality_report[check_name] = result
        
        if result.status == "failed":
            apply_quality_fix(assembled_sequence, check_name, result.issues)
    
    return quality_report
```

## Professional Export Settings
```python
def configure_professional_export():
    """Configure Blender render settings for professional output"""
    scene = bpy.context.scene
    render = scene.render
    
    # Video settings
    render.resolution_x = 1920  # or 3840 for 4K
    render.resolution_y = 1080  # or 2160 for 4K
    render.fps = 24  # Cinematic frame rate
    
    # Output format
    render.image_settings.file_format = 'FFMPEG'
    render.ffmpeg.format = 'MPEG4'
    render.ffmpeg.codec = 'H264'
    render.ffmpeg.constant_rate_factor = 'HIGH'
    
    # Audio settings
    render.ffmpeg.audio_codec = 'AAC'
    render.ffmpeg.audio_bitrate = 320
    render.ffmpeg.audio_mixrate = 48000
    
    # Color management
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.sequencer_colorspace_settings.name = 'Rec.709'
```

## Performance Considerations
- **VSE Optimization**: Efficient proxy generation for smooth playback
- **Memory Management**: Smart caching of video and audio assets
- **Render Optimization**: Multi-threaded rendering for faster export
- **Asset Organization**: Structured file management for large projects

## Integration Points
- **Input**: Video clips from Cinematographer, audio tracks from Sound Designer
- **Output**: Final assembled sequence ready for export
- **Quality Feedback**: Reports on technical quality and consistency
- **Asset Management**: Organizes and validates all production assets

## Error Handling
- **Missing Assets**: Graceful handling of missing video or audio files
- **Sync Issues**: Automatic detection and correction of timing problems
- **Quality Problems**: Automated enhancement and manual override options
- **Export Failures**: Multiple format fallbacks and quality adjustment

## UI Integration
```python
def create_editor_ui():
    """Create Blender UI for final assembly and editing"""
    layout = self.layout
    
    # Scene assembly
    layout.operator("movie_director.assemble_scene", text="Assemble Scene")
    layout.operator("movie_director.apply_restoration", text="Apply Video Restoration")
    
    # Timeline management  
    layout.prop(scene.movie_director, "auto_transitions")
    layout.prop(scene.movie_director, "transition_duration")
    
    # Quality control
    layout.operator("movie_director.quality_check", text="Quality Control Check")
    layout.operator("movie_director.apply_color_grading", text="Apply Color Grading")
    
    # Export settings
    layout.prop(scene.movie_director, "export_quality")
    layout.operator("movie_director.export_final", text="Export Final Video")
```

## Final Assembly Workflow
```python
def execute_final_assembly(scene_collection):
    """Complete workflow for final scene assembly"""
    
    # Step 1: Validate all assets
    validation_result = validate_scene_assets(scene_collection)
    if not validation_result.is_valid:
        return handle_validation_errors(validation_result)
    
    # Step 2: Apply video restoration
    restored_clips = apply_video_restoration(get_scene_video_clips(scene_collection))
    
    # Step 3: Assemble timeline
    timeline = assemble_scene_sequence(scene_collection)
    
    # Step 4: Synchronize audio
    synchronize_all_audio(timeline)
    
    # Step 5: Apply transitions and color grading
    apply_smart_transitions(timeline.sequences)
    apply_consistent_color_grading(timeline.sequences, scene_collection.style_reference)
    
    # Step 6: Quality control
    quality_report = perform_quality_control(timeline)
    
    # Step 7: Final validation
    if quality_report.overall_quality >= MINIMUM_QUALITY_THRESHOLD:
        return prepare_for_export(timeline)
    else:
        return request_quality_improvements(quality_report)
```

This agent completes the production pipeline by transforming individual generated assets into a polished, professional final product ready for distribution, ensuring the highest quality standards throughout the post-production process.