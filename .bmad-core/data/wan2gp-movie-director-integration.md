# Wan2GP Movie Director Integration

## Overview

Integration patterns for using Wan2GP with the Movie Director addon's Cinematographer agent. This module handles shot generation, batch processing, and workflow integration with Blender's asset system.

## Cinematographer Agent Integration

### Setup and Connection Management
```python
class Wan2GPCinematographer:
    """Wan2GP integration for Cinematographer agent"""
    
    def __init__(self, wan2gp_url="http://localhost:7860"):
        self.client = Wan2GPClient(wan2gp_url)
        self.generation_cache = {}
    
    def setup_connection(self):
        """Initialize connection to Wan2GP service"""
        if not self.client.connect():
            raise RuntimeError("Failed to connect to Wan2GP service")
        
        if not self.client.check_health():
            raise RuntimeError("Wan2GP service is not healthy")
```

### Shot Generation Workflows
```python
def generate_shot_preview(self, shot_obj):
    """Generate quick preview for shot using fast models"""
    prompt = self.build_shot_prompt(shot_obj)
    
    # Use fast model for preview
    result = self.client.generate_text_to_video(
        prompt, 
        model="hunyuan_fast"
    )
    
    if result["success"]:
        shot_obj.movie_director.preview_video_path = result["video_path"]
        shot_obj.movie_director.generation_status = "preview_ready"
    else:
        shot_obj.movie_director.generation_status = "preview_failed"
        shot_obj.movie_director.generation_error = result["error"]
    
    return result

def generate_shot_final(self, shot_obj):
    """Generate final quality shot using Hunyuan Video"""
    prompt = self.build_shot_prompt(shot_obj)
    
    # Use full Hunyuan model for final quality
    result = self.client.generate_text_to_video(
        prompt, 
        model="hunyuan"
    )
    
    if result["success"]:
        shot_obj.movie_director.generated_video_path = result["video_path"]
        shot_obj.movie_director.generation_status = "completed"
    else:
        shot_obj.movie_director.generation_status = "failed"
        shot_obj.movie_director.generation_error = result["error"]
    
    return result

def build_shot_prompt(self, shot_obj):
    """Build comprehensive prompt for shot generation"""
    prompt_parts = []
    
    # Basic shot description
    if shot_obj.movie_director.action_description:
        prompt_parts.append(shot_obj.movie_director.action_description)
    
    # Camera direction
    if shot_obj.movie_director.camera_direction:
        prompt_parts.append(f"Camera: {shot_obj.movie_director.camera_direction}")
    
    # Style context
    if shot_obj.movie_director.style_reference:
        style_obj = shot_obj.movie_director.style_reference
        if hasattr(style_obj, 'movie_director'):
            style_desc = style_obj.movie_director.style_description
            if style_desc:
                prompt_parts.append(f"Style: {style_desc}")
    
    # Character context
    characters = self.get_shot_characters(shot_obj)
    if characters:
        char_descriptions = [char.movie_director.character_description 
                           for char in characters 
                           if char.movie_director.character_description]
        if char_descriptions:
            prompt_parts.append(f"Characters: {', '.join(char_descriptions)}")
    
    return " | ".join(prompt_parts)

def get_shot_characters(self, shot_obj):
    """Get character objects associated with shot"""
    # Implementation depends on how character-shot relationships are stored
    # This would integrate with the addon's asset management system
    return []
```

## Batch Processing for Scene Generation

### Scene-Level Batch Operations
```python
def generate_scene_batch(self, scene_shots, quality="standard"):
    """Generate multiple shots in batch for efficiency"""
    results = []
    
    for shot_obj in scene_shots:
        # Determine generation strategy based on quality
        if quality == "preview":
            result = self.generate_shot_preview(shot_obj)
        elif quality == "final":
            result = self.generate_shot_final(shot_obj)
        else:  # standard
            # Use standard Hunyuan model
            prompt = self.build_shot_prompt(shot_obj)
            result = self.client.generate_text_to_video(prompt, model="hunyuan")
        
        results.append({
            "shot": shot_obj,
            "result": result
        })
        
        # Update progress for UI
        progress = len(results) / len(scene_shots)
        self.update_generation_progress(progress)
    
    return results

def update_generation_progress(self, progress):
    """Update generation progress in Blender UI"""
    scene = bpy.context.scene
    if hasattr(scene, 'movie_director'):
        scene.movie_director.generation_progress = progress
        scene.movie_director.generation_active = progress < 1.0
```

## Advanced Integration Features

### Model-Native Camera Control
```python
def apply_camera_control(self, prompt, camera_params):
    """Apply model-native camera control parameters"""
    camera_prompts = {
        "zoom_in": "slow zoom in, approaching subject",
        "zoom_out": "zoom out, revealing wider scene",
        "pan_left": "camera pans left, smooth movement",
        "pan_right": "camera pans right, following action",
        "tilt_up": "camera tilts up, low angle shot",
        "tilt_down": "camera tilts down, high angle shot",
        "tracking": "tracking shot, following subject movement",
        "dolly_forward": "dolly forward, smooth camera approach",
        "dolly_back": "dolly back, camera pulls away"
    }
    
    # Build camera-enhanced prompt
    enhanced_prompt = prompt
    
    for movement, description in camera_prompts.items():
        if movement in camera_params:
            enhanced_prompt += f", {description}"
    
    return enhanced_prompt

def generate_with_camera_control(self, shot_obj, camera_movements):
    """Generate shot with specific camera movements"""
    base_prompt = self.build_shot_prompt(shot_obj)
    camera_prompt = self.apply_camera_control(base_prompt, camera_movements)
    
    return self.client.generate_text_to_video(camera_prompt, model="hunyuan")
```

### Configuration Templates
```python
class Wan2GPConfigTemplates:
    """Predefined configuration templates for different use cases"""
    
    TEMPLATES = {
        "quick_preview": {
            "model": "hunyuan_fast",
            "description": "Fast preview generation"
        },
        
        "standard_generation": {
            "model": "hunyuan",
            "description": "Standard quality generation"
        },
        
        "high_quality": {
            "model": "ltxv_13B",
            "description": "High quality generation with LTX-Video"
        },
        
        "character_focus": {
            "model": "hunyuan_avatar",
            "description": "Character-focused generation"
        },
        
        "fantasy_content": {
            "model": "fantasy",
            "description": "Fantasy-themed content generation"
        }
    }
    
    @classmethod
    def get_template(cls, template_name):
        """Get configuration template by name"""
        return cls.TEMPLATES.get(template_name, cls.TEMPLATES["standard_generation"])
    
    @classmethod
    def apply_template(cls, template_name, prompt):
        """Apply template to generate video"""
        config = cls.get_template(template_name)
        return {
            "prompt": prompt,
            "model": config["model"],
            "description": config["description"]
        }
```

## Error Handling and Fallbacks

### Robust Error Management
```python
def generate_with_fallback(self, prompt, primary_model, fallback_model=None):
    """Generate video with fallback configuration on failure"""
    result = self.client.generate_text_to_video(prompt, primary_model)
    
    if result["success"]:
        return result
    
    # If primary fails, try fallback
    if fallback_model:
        print(f"Primary generation failed: {result['error']}")
        print("Attempting fallback configuration...")
        
        fallback_result = self.client.generate_text_to_video(prompt, fallback_model)
        
        if fallback_result["success"]:
            fallback_result["used_fallback"] = True
            fallback_result["primary_error"] = result["error"]
        
        return fallback_result
    
    return result

def handle_wan2gp_errors(self, error, shot_obj):
    """Handle Wan2GP-specific errors with appropriate responses"""
    error_handlers = {
        "connection_error": self.handle_connection_error,
        "model_error": self.handle_model_error,
        "memory_error": self.handle_memory_error,
        "timeout_error": self.handle_timeout_error
    }
    
    error_type = self.classify_error(error)
    handler = error_handlers.get(error_type, self.handle_generic_error)
    
    return handler(error, shot_obj)

def classify_error(self, error):
    """Classify error type for appropriate handling"""
    error_str = str(error).lower()
    
    if "connection" in error_str or "timeout" in error_str:
        return "connection_error"
    elif "model" in error_str or "cuda" in error_str:
        return "model_error"
    elif "memory" in error_str or "oom" in error_str:
        return "memory_error"
    else:
        return "generic_error"
```

## Async Operations for UI Responsiveness

### Non-Blocking Generation
```python
async def async_generate_shot(self, shot_obj):
    """Generate shot asynchronously to avoid blocking UI"""
    loop = asyncio.get_event_loop()
    
    # Run generation in thread pool
    result = await loop.run_in_executor(
        None, 
        self.generate_shot_final, 
        shot_obj
    )
    
    # Update UI on main thread
    bpy.app.timers.register(lambda: self.update_shot_ui(shot_obj, result))
    
    return result

def update_shot_ui(self, shot_obj, result):
    """Update shot UI elements after generation"""
    # Force UI redraw
    for area in bpy.context.screen.areas:
        if area.type in {'VIEW_3D', 'PROPERTIES'}:
            area.tag_redraw()
    
    return None  # Don't reschedule timer
```

This integration guide provides comprehensive patterns for using Wan2GP within the Movie Director addon's film production workflow, ensuring efficient and reliable video generation through the Cinematographer agent.