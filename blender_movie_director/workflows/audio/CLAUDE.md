# Audio Generation Workflows

## Role
Workflows for creating complete audio landscapes including character dialogue, sound effects, and ambient audio. Integrates with video generation for synchronized results.

## Audio Generation Types
- **Voice Synthesis** - Character dialogue using RVC models
- **Sound Effects** - Environmental and action sounds
- **Ambient Audio** - Background soundscapes
- **Audio Synchronization** - Align with video clips

## Workflow Templates
- **voice_synthesis.json** - RVC character dialogue generation
- **sound_effects.json** - AudioLDM effect generation
- **ambient_audio.json** - Environmental soundscape creation
- **audio_sync.json** - Video-audio synchronization
- **audio_enhancement.json** - Audio post-processing

## Voice Synthesis Pipeline
```python
def generate_character_dialogue(shot_obj, character_obj):
    """Generate character-specific dialogue"""
    
    # Extract dialogue text
    dialogue_text = shot_obj.movie_director.dialogue
    
    # Get character voice model
    voice_model = character_obj.movie_director.rvc_voice_model_path
    
    # Generate audio using RVC
    audio_path = rvc_client.synthesize_speech(
        text=dialogue_text,
        voice_model=voice_model
    )
    
    return audio_path
```

## Sound Effects Generation
- **Script Parsing** - Extract sound cues from action lines
- **AudioLDM Integration** - Text-to-audio generation
- **Effect Classification** - Categorize by type (footsteps, ambient, etc.)
- **Timing Alignment** - Sync with video events

## Audio Synchronization
```python
def synchronize_audio_with_video(shot_obj):
    """Align audio tracks with generated video"""
    
    video_duration = get_video_duration(shot_obj.generated_video_path)
    
    # Sync dialogue
    dialogue_audio = align_dialogue_timing(shot_obj)
    
    # Add sound effects
    sfx_audio = generate_sfx_for_shot(shot_obj)
    
    # Mix audio tracks
    final_audio = mix_audio_tracks([dialogue_audio, sfx_audio])
    
    return final_audio
```

## Audio Quality Control
- **Voice Consistency** - Ensure character voice stability
- **Audio Levels** - Balance dialogue, effects, and ambient
- **Sync Accuracy** - Precise video-audio alignment
- **Quality Enhancement** - Audio restoration and enhancement

## Reference
- [Sound Designer](/../agents/sound_designer/CLAUDE.md)