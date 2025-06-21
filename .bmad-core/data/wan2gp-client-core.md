# Wan2GP Client Core - Basic Connection and API

## Overview

Core client implementation for connecting to and communicating with the Wan2GP (Gradio-based video generation service). This module handles the fundamental connection management and basic API interactions.

## Basic Client Implementation

### Connection Management
```python
from gradio_client import Client
import asyncio
import json
import os

class Wan2GPClient:
    """Client for interacting with Wan2GP video generation service"""
    
    def __init__(self, base_url="http://localhost:7860"):
        self.base_url = base_url
        self.client = None
        self.is_connected = False
    
    def connect(self):
        """Establish connection to Wan2GP service"""
        try:
            self.client = Client(self.base_url)
            self.is_connected = True
            print(f"Connected to Wan2GP at {self.base_url}")
            return True
        except Exception as e:
            print(f"Failed to connect to Wan2GP: {e}")
            self.is_connected = False
            return False
    
    def check_health(self):
        """Check if Wan2GP service is healthy and responsive"""
        try:
            # Check service status
            result = self.client.predict(api_name="/refresh_status_async")
            return result is not None
        except Exception as e:
            print(f"Wan2GP health check failed: {e}")
            return False
```

## Available Models and Endpoints

### Text-to-Video Models
The Wan2GP service supports a comprehensive range of video generation models:

**Primary Text-to-Video Models:**
- `hunyuan`: Hunyuan Video (high quality) - `/hunyuan_t2v`
- `hunyuan_fast`: Hunyuan Video (fast mode) - `/hunyuan_t2v_fast`
- `ltxv_13B`: LTX-Video 13B (full precision) - `/ltxv_13B_t2v`
- `ltxv_13B_distilled`: LTX-Video 13B (distilled/optimized) - `/ltxv_13B_distilled_t2v`

**General Purpose Models:**
- `t2v_1.3B`: General text-to-video model - `/t2v_1.3B`
- `t2v`: Standard text-to-video - `/t2v`
- `vace_1.3B`, `vace_14B`: VACE models - `/vace_1.3B_t2v`, `/vace_14B_t2v`
- `phantom_1.3B`, `phantom_14B`: Phantom models - `/phantom_1.3B_t2v`, `/phantom_14B_t2v`

**Specialized Models:**
- `moviigen`: MovieGen integration - `/moviigen_t2v`

### Image-to-Video Models
- `hunyuan_i2v`: Hunyuan Image-to-Video - `/hunyuan_i2v`
- `i2v`: General image-to-video - `/i2v`
- `i2v_720p`: 720p image-to-video - `/i2v_720p`

### Specialized Generation Models
- `hunyuan_custom_audio`: Audio-guided video generation - `/hunyuan_custom_audio`
- `hunyuan_avatar`: Avatar/character generation - `/hunyuan_avatar`
- `fantasy`: Fantasy-themed content - `/fantasy`
- `fun_inp_1.3B`: Input-guided generation - `/fun_inp_1.3B`
- `recam_1.3B`: Recam model - `/recam_1.3B`

## Core Generation Functions

### Text-to-Video Generation
```python
def generate_text_to_video(self, prompt, model="hunyuan"):
    """Generate video from text prompt using specified model
    
    Args:
        prompt (str): Text description of the video to generate
        model (str): Model to use for generation
    
    Returns:
        dict: Generation result with video path and metadata
    """
    if not self.is_connected:
        raise RuntimeError("Not connected to Wan2GP service")
    
    # Available models with their endpoints
    model_endpoints = {
        "hunyuan": "/hunyuan_t2v",
        "hunyuan_fast": "/hunyuan_t2v_fast",
        "ltxv_13B": "/ltxv_13B_t2v",
        "ltxv_13B_distilled": "/ltxv_13B_distilled_t2v", 
        "t2v_1.3B": "/t2v_1.3B",
        "t2v": "/t2v",
        "vace_1.3B": "/vace_1.3B_t2v",
        "vace_14B": "/vace_14B_t2v",
        "moviigen": "/moviigen_t2v",
        "phantom_1.3B": "/phantom_1.3B_t2v",
        "phantom_14B": "/phantom_14B_t2v"
    }
    
    if model not in model_endpoints:
        raise ValueError(f"Unknown model: {model}. Available: {list(model_endpoints.keys())}")
    
    try:
        endpoint = model_endpoints[model]
        result = self.client.predict(prompt, api_name=endpoint)
        
        return {
            "success": True,
            "video_path": result,
            "metadata": {
                "prompt": prompt,
                "model": model,
                "endpoint": endpoint
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "prompt": prompt,
            "model": model
        }
```

### Image-to-Video Generation
```python
def generate_image_to_video(self, image_path, model="hunyuan_i2v", prompt=""):
    """Generate video from input image with optional text guidance
    
    Args:
        image_path (str): Path to input image
        model (str): I2V model to use for generation
        prompt (str): Optional text guidance for video generation
    
    Returns:
        dict: Generation result with video path
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")
    
    # Available I2V models with their endpoints
    i2v_endpoints = {
        "hunyuan_i2v": "/hunyuan_i2v",
        "i2v": "/i2v", 
        "i2v_720p": "/i2v_720p"
    }
    
    if model not in i2v_endpoints:
        raise ValueError(f"Unknown I2V model: {model}. Available: {list(i2v_endpoints.keys())}")
    
    try:
        endpoint = i2v_endpoints[model]
        result = self.client.predict(image_path, prompt, api_name=endpoint)
        
        return {
            "success": True,
            "video_path": result,
            "metadata": {
                "input_image": image_path,
                "prompt": prompt,
                "model": model,
                "endpoint": endpoint
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "input_image": image_path,
            "prompt": prompt,
            "model": model
        }
```

### Specialized Generation Functions
```python
def generate_with_audio_guidance(self, prompt, audio_path=None):
    """Generate video with audio guidance using Hunyuan Custom Audio model"""
    try:
        result = self.client.predict(prompt, audio_path, api_name="/hunyuan_custom_audio")
        return {"success": True, "video_path": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_avatar_video(self, prompt):
    """Generate avatar/character video using Hunyuan Avatar model"""
    try:
        result = self.client.predict(prompt, api_name="/hunyuan_avatar")
        return {"success": True, "video_path": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

def generate_fantasy_video(self, prompt):
    """Generate fantasy-themed video content"""
    try:
        result = self.client.predict(prompt, api_name="/fantasy")
        return {"success": True, "video_path": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Best Practices

### 1. Connection Management
```python
# GOOD: Proper connection lifecycle
def safe_wan2gp_operation(self, operation_func, *args, **kwargs):
    if not self.client.is_connected:
        self.client.connect()
    
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        # Try reconnecting once
        if self.client.connect():
            return operation_func(*args, **kwargs)
        else:
            raise RuntimeError(f"Wan2GP operation failed: {e}")

# AVOID: Assuming connection is always available
def unsafe_operation(self):
    return self.client.generate_text_to_video(prompt, config)  # May fail
```

### 2. Error Handling
```python
# GOOD: Comprehensive error handling
def generate_with_fallback(self, prompt, primary_model, fallback_model=None):
    """Generate video with fallback model on failure"""
    result = self.generate_text_to_video(prompt, primary_model)
    
    if result["success"]:
        return result
    
    if fallback_model:
        print(f"Primary model {primary_model} failed: {result['error']}")
        print(f"Attempting fallback model: {fallback_model}")
        
        fallback_result = self.generate_text_to_video(prompt, fallback_model)
        
        if fallback_result["success"]:
            fallback_result["used_fallback"] = True
            fallback_result["primary_error"] = result["error"]
        
        return fallback_result
    
    return result
```

This core client provides the foundation for all Wan2GP interactions in the Movie Director addon.