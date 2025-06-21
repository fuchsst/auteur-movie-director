# Sound Designer Agent

## Agent Profile
```yaml
agent:
  name: Sound Designer
  title: Audio Generation & Voice Synthesis Specialist
  icon: 🎵
  focus: Voice cloning, sound effects, ambient audio, audio-visual synchronization
  specialization: RVC voice synthesis, AudioLDM generation, audio post-production
```

## Role & Responsibilities

### Primary Function
The Sound Designer agent creates the complete auditory landscape of the film, from character dialogue through environmental soundscapes to specific sound effects. This agent ensures audio consistency and professional quality across all generated content.

### Core Capabilities
- **Voice Cloning**: Generate consistent character dialogue using RVC voice models
- **Sound Effects Generation**: Create specific sound effects from text descriptions
- **Ambient Audio Creation**: Generate environmental soundscapes and background audio
- **Audio Synchronization**: Match generated audio to video timing and cues
- **Audio Quality Control**: Ensure professional audio standards and consistency

## Technical Implementation

### RVC Voice Synthesis Pipeline
```python
rvc_integration:
  model_format: ".pth files from Casting Director"
  voice_quality: "40kHz sample rate for professional quality"
  emotion_control: "Adaptive emotional expression based on dialogue context"
  batch_processing: "Multiple dialogue lines with consistent voice characteristics"
```

### AudioLDM Sound Generation
```python
audioLDM_capabilities:
  sound_effects: "Footsteps, doors, environmental sounds"
  ambient_audio: "Forest ambience, city noise, weather sounds"
  musical_elements: "Score segments, emotional underlays"
  duration_control: "Precise timing to match video segments"
```

### Audio Processing Pipeline
```python
def generate_character_dialogue(shot_object, character_asset):
    """Generate character dialogue using trained RVC model"""
    dialogue_text = shot_object.movie_director.dialogue
    voice_model_path = character_asset.movie_director.rvc_voice_model_path
    
    # Load character-specific RVC model
    rvc_model = load_rvc_model(voice_model_path)
    
    # Generate speech with emotional context
    emotion_context = analyze_dialogue_emotion(dialogue_text)
    audio_clip = rvc_model.synthesize(
        text=dialogue_text,
        emotion=emotion_context,
        sample_rate=40000
    )
    
    return audio_clip
```

## CrewAI Tools
```python
tools:
  - voice_synthesis_tool: Generate character dialogue using RVC models
  - sound_effects_tool: Create specific sound effects from descriptions
  - ambient_audio_tool: Generate environmental soundscapes
  - audio_sync_tool: Synchronize audio to video timing
  - audio_quality_tool: Validate and enhance audio quality
  - script_parser_tool: Extract audio cues from script annotations
```

## Workflow Integration

### Audio Generation Pipeline
1. **Script Analysis**: Parse script for dialogue and sound effect cues
2. **Character Voice Generation**: Use RVC models for all character dialogue
3. **Sound Effect Creation**: Generate specific sounds from script annotations
4. **Ambient Audio**: Create environmental soundscapes for each location
5. **Audio Synchronization**: Match all audio elements to video timing
6. **Quality Enhancement**: Apply professional audio processing

### Sound Cue Extraction
```python
def extract_audio_cues(script_text):
    """Extract sound cues from script annotations"""
    import re
    
    # Extract parenthetical sound cues: [Footsteps on gravel]
    sound_cues = re.findall(r'\[([^\]]+)\]', script_text)
    
    # Extract action lines that imply sounds
    action_sounds = extract_implied_sounds(script_text)
    
    # Extract dialogue for voice synthesis
    dialogue_lines = extract_character_dialogue(script_text)
    
    return {
        "explicit_sounds": sound_cues,
        "implied_sounds": action_sounds,
        "dialogue": dialogue_lines
    }
```

### Multi-Track Audio Assembly
```python
def create_audio_layers(shot_object):
    """Create multiple audio layers for professional mixing"""
    audio_layers = {
        "dialogue": generate_dialogue_track(shot_object),
        "sound_effects": generate_sfx_track(shot_object),
        "ambient": generate_ambient_track(shot_object),
        "foley": generate_foley_track(shot_object)
    }
    
    # Mix layers with appropriate levels
    final_mix = mix_audio_layers(audio_layers, shot_object.audio_mix_settings)
    return final_mix
```

## Advanced Features

### Intelligent Sound Effect Generation
```python
def generate_contextual_sound_effects(scene_description, action_cues):
    """Generate sound effects based on scene context"""
    sound_prompts = []
    
    # Analyze scene environment
    environment = extract_location_info(scene_description)
    
    # Generate environment-appropriate base sounds
    if "forest" in environment:
        sound_prompts.append("forest ambience, birds chirping, wind through trees")
    elif "city" in environment:
        sound_prompts.append("urban ambience, distant traffic, footsteps on pavement")
    
    # Add specific action sounds
    for action in action_cues:
        sound_prompt = action_to_sound_description(action)
        sound_prompts.append(sound_prompt)
    
    # Generate all sounds with AudioLDM
    generated_sounds = []
    for prompt in sound_prompts:
        audio_clip = audioLDM.generate(prompt, duration=calculate_duration(prompt))
        generated_sounds.append(audio_clip)
    
    return generated_sounds
```

### Voice Consistency Management
```python
def ensure_voice_consistency(character_name, dialogue_segments):
    """Ensure voice consistency across multiple dialogue segments"""
    character_asset = get_character_asset(character_name)
    voice_model = load_rvc_model(character_asset.rvc_voice_model_path)
    
    # Generate all dialogue with consistent model settings
    consistent_audio = []
    for segment in dialogue_segments:
        audio = voice_model.synthesize(
            text=segment.text,
            emotion=segment.emotion,
            pitch_variation=0.1,  # Minimal variation for consistency
            speed_variation=0.05
        )
        consistent_audio.append(audio)
    
    return consistent_audio
```

### Audio-Visual Synchronization
```python
def synchronize_audio_to_video(audio_tracks, video_clip):
    """Synchronize generated audio to video timing"""
    video_duration = get_video_duration(video_clip)
    
    # Adjust audio timing to match video
    synchronized_tracks = {}
    for track_name, audio_data in audio_tracks.items():
        if track_name == "dialogue":
            # Sync dialogue to lip movements (if available)
            sync_audio = sync_dialogue_to_lips(audio_data, video_clip)
        else:
            # Sync ambient and effects to video events
            sync_audio = sync_to_video_events(audio_data, video_clip)
        
        synchronized_tracks[track_name] = sync_audio
    
    return synchronized_tracks
```

## Quality Standards
- **Sample Rate**: Minimum 48kHz for professional production
- **Bit Depth**: 24-bit for high dynamic range
- **Format**: WAV or FLAC for lossless quality
- **Loudness**: -23 LUFS for broadcast standards
- **Dynamic Range**: Appropriate for cinematic presentation

## Performance Considerations
- **RVC Model Loading**: Efficient model caching and reuse
- **Audio Generation**: Batch processing for multiple sound effects
- **Memory Management**: Stream processing for long audio segments
- **File Management**: Organized audio asset storage and retrieval

## Integration Points
- **Input**: Character voice models from Casting Director, script from Screenwriter
- **Output**: Audio tracks → Editor for final synchronization
- **Collaboration**: Works with Cinematographer for audio-visual timing
- **Resource Sharing**: Coordinates with other agents for VRAM usage during intensive processing

## Error Handling
- **RVC Model Failures**: Fallback to text-to-speech alternatives
- **AudioLDM Issues**: Pre-recorded sound effect libraries as backup
- **Synchronization Problems**: Manual timing adjustment tools
- **Quality Issues**: Automatic audio enhancement and noise reduction

## Blender Integration
```python
def import_audio_to_blender(shot_object, audio_tracks):
    """Import generated audio tracks into Blender VSE"""
    vse_scene = bpy.context.scene
    sequencer = vse_scene.sequence_editor
    
    if not sequencer:
        sequencer = vse_scene.sequence_editor_create()
    
    # Import each audio track as separate channel
    for track_name, audio_file in audio_tracks.items():
        audio_strip = sequencer.sequences.new_sound(
            name=f"{shot_object.name}_{track_name}",
            filepath=audio_file,
            channel=get_audio_channel(track_name),
            frame_start=shot_object.movie_director.start_frame
        )
        
        # Set audio properties
        audio_strip.movie_director.audio_type = track_name
        audio_strip.movie_director.source_shot = shot_object.name
```

## UI Integration
```python
def create_sound_designer_ui(shot_object):
    """Create Blender UI for audio generation"""
    layout.label(text="Audio Generation")
    
    # Dialogue generation
    if shot_object.movie_director.dialogue:
        layout.operator("movie_director.generate_dialogue", text="Generate Character Voice")
    
    # Sound effects
    layout.prop(shot_object.movie_director, "sound_effects_cues")
    layout.operator("movie_director.generate_sound_effects", text="Generate Sound Effects")
    
    # Ambient audio
    layout.prop(shot_object.movie_director, "ambient_description")
    layout.operator("movie_director.generate_ambient", text="Generate Ambient Audio")
    
    # Audio preview
    if shot_object.movie_director.generated_audio_path:
        layout.operator("movie_director.preview_audio", text="Preview Audio")
```

This agent completes the sensory experience of the generated film by providing professional-quality audio that matches the visual content and maintains character consistency throughout the production.