"""Pydantic schemas for Wan2GP API parameters and responses.

This module defines data models that ensure type safety and validation
for all interactions with the Wan2GP API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union, Dict, Any
from pathlib import Path

from .enums import (
    Wan2GPModel, Resolution, ControlVideoProcess, AreaProcessed,
    TeaCacheSetting, TemporalUpsampling, SpatialUpsampling,
    RIFLExSetting, SkipLayerGuidance, CFGStar, PromptEnhancer,
    RemoveBackground, MultiPromptsGenType, MultiImagesGenType
)


class GenerationSettings(BaseModel):
    """Complete settings for a video generation task."""
    
    # Core generation parameters
    model: Wan2GPModel
    prompt: str = Field(..., description="Text prompt for video generation")
    negative_prompt: str = Field("", description="Negative prompt to avoid certain content")
    
    # Video parameters
    resolution: Resolution = Resolution.R_832x480
    video_length: int = Field(81, ge=5, le=257, description="Number of frames (16 = 1s)")
    seed: int = Field(-1, ge=-1, le=999999999, description="Random seed (-1 for random)")
    
    # Generation quality parameters
    num_inference_steps: int = Field(default=30, ge=1, le=100, description="Number of denoising steps")
    guidance_scale: float = Field(default=5.0, ge=1.0, le=20.0, description="Classifier-free guidance scale")
    audio_guidance_scale: float = Field(default=5.0, ge=1.0, le=20.0, description="Audio guidance scale")
    flow_shift: float = Field(default=5.0, ge=0.0, le=25.0, description="Shift scale")
    embedded_guidance_scale: float = Field(default=6.0, ge=1.0, le=20.0, description="Embedded guidance scale")
    
    # Generation behavior
    repeat_generation: int = Field(default=1, ge=1, le=25, description="Number of videos to generate")
    multi_prompts_gen_type: MultiPromptsGenType = MultiPromptsGenType.SINGLE
    multi_images_gen_type: MultiImagesGenType = MultiImagesGenType.SINGLE
    
    # Performance optimizations
    tea_cache_setting: TeaCacheSetting = TeaCacheSetting.DISABLED
    tea_cache_start_step_perc: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # LoRA settings
    loras_choices: List[str] = Field(default_factory=list, description="Selected LoRA names")
    loras_multipliers: str = Field(default="", description="LoRA multipliers (space-separated)")
    
    # Image-to-Video specific
    image_start: Optional[List[str]] = Field(default=None, description="Start images for I2V")
    image_end: Optional[List[str]] = Field(default=None, description="End images for I2V")
    video_source: Optional[str] = Field(default=None, description="Source video path")
    keep_frames_video_source: str = Field(default="", description="Frames to keep from source video")
    
    # VACE ControlNet specific
    control_video_path: Optional[str] = Field(default=None, description="Control video for VACE")
    video_prompt_type: str = Field(default="", description="Video prompt type")
    control_video_process: ControlVideoProcess = ControlVideoProcess.KEEP_UNCHANGED
    area_processed: AreaProcessed = AreaProcessed.WHOLE_VIDEO
    video_mask_path: Optional[str] = Field(default=None, description="Video mask for inpainting")
    control_net_weight: float = Field(default=1.0, ge=0.0, le=2.0, description="ControlNet weight #1")
    control_net_weight2: float = Field(default=1.0, ge=0.0, le=2.0, description="ControlNet weight #2")
    mask_expand: float = Field(default=0.0, ge=-10.0, le=50.0, description="Expand/shrink mask area")
    
    # Reference images
    reference_images: Optional[List[str]] = Field(default=None, description="Reference image paths")
    frames_positions: str = Field(default="", description="Positions of injected frames")
    remove_background_images_ref: RemoveBackground = RemoveBackground.ENABLED
    
    # Audio
    audio_guide: Optional[str] = Field(default=None, description="Audio guide file path")
    
    # Sliding window for long videos
    sliding_window_size: int = Field(default=81, ge=5, le=257, description="Sliding window size")
    sliding_window_overlap: int = Field(default=5, ge=1, le=97, description="Window overlap frames")
    sliding_window_overlap_noise: int = Field(default=20, ge=0, le=150, description="Noise for overlapped frames")
    sliding_window_discard_last_frames: int = Field(default=8, ge=0, le=20, description="Discard last frames")
    
    # Post-processing
    temporal_upsampling: TemporalUpsampling = TemporalUpsampling.DISABLED
    spatial_upsampling: SpatialUpsampling = SpatialUpsampling.DISABLED
    
    # Advanced settings
    riflex_setting: RIFLExSetting = RIFLExSetting.DISABLED
    slg_switch: SkipLayerGuidance = SkipLayerGuidance.DISABLED
    slg_layers: List[int] = Field(default_factory=lambda: [9], description="Skip layers")
    slg_start_perc: float = Field(default=10.0, ge=0.0, le=100.0, description="Skip layer start %")
    slg_end_perc: float = Field(default=90.0, ge=0.0, le=100.0, description="Skip layer end %")
    cfg_star_switch: CFGStar = CFGStar.DISABLED
    cfg_zero_step: float = Field(default=-1.0, ge=-1.0, le=39.0, description="CFG zero below layer")
    
    # Prompt enhancement
    prompt_enhancer: PromptEnhancer = PromptEnhancer.DISABLED
    
    # Outpainting settings
    video_guide_outpainting: str = Field(default="#", description="Outpainting configuration")
    
    class Config:
        use_enum_values = True
        validate_assignment = True
    
    @field_validator('prompt')
    def prompt_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v.strip()
    
    @field_validator('video_length')
    def validate_video_length(cls, v):
        if v < 5:
            raise ValueError('Video length must be at least 5 frames')
        return v
    
    @field_validator('reference_images', 'image_start', 'image_end')
    def validate_image_paths(cls, v):
        if v is None:
            return v
        for path in v:
            if path and not Path(path).exists():
                raise ValueError(f'Image file does not exist: {path}')
        return v
    
    @field_validator('control_video_path', 'video_source', 'video_mask_path', 'audio_guide')
    def validate_file_paths(cls, v):
        if v and not Path(v).exists():
            raise ValueError(f'File does not exist: {v}')
        return v


class QuickGenerationSettings(BaseModel):
    """Simplified settings for quick video generation."""
    
    model: Wan2GPModel = Wan2GPModel.LTXV_13B_DISTILLED
    prompt: str
    negative_prompt: str = ""
    resolution: Resolution = Resolution.R_832x480
    video_length: int = 32  # 2 seconds
    seed: int = -1
    
    def to_full_settings(self) -> GenerationSettings:
        """Convert to full GenerationSettings with optimized parameters."""
        return GenerationSettings(
            model=self.model,
            prompt=self.prompt,
            negative_prompt=self.negative_prompt,
            resolution=self.resolution,
            video_length=self.video_length,
            seed=self.seed,
            num_inference_steps=4 if self.model == Wan2GPModel.LTXV_13B_DISTILLED else 15,
            guidance_scale=1.0 if self.model == Wan2GPModel.LTXV_13B_DISTILLED else 5.0,
        )


class HighQualityGenerationSettings(BaseModel):
    """Settings optimized for high-quality video generation."""
    
    model: Wan2GPModel = Wan2GPModel.HUNYUAN_T2V
    prompt: str
    negative_prompt: str = ""
    resolution: Resolution = Resolution.R_1280x720
    video_length: int = 129  # ~8 seconds
    seed: int = -1
    reference_image: Optional[str] = None
    
    def to_full_settings(self) -> GenerationSettings:
        """Convert to full GenerationSettings with high-quality parameters."""
        settings = GenerationSettings(
            model=self.model,
            prompt=self.prompt,
            negative_prompt=self.negative_prompt,
            resolution=self.resolution,
            video_length=self.video_length,
            seed=self.seed,
            num_inference_steps=50,
            guidance_scale=6.0,
            slg_switch=SkipLayerGuidance.ENABLED,  # Better quality
        )
        
        if self.reference_image:
            settings.reference_images = [self.reference_image]
            if self.model == Wan2GPModel.HUNYUAN_T2V:
                settings.model = Wan2GPModel.HUNYUAN_CUSTOM
        
        return settings


class VACEGenerationSettings(BaseModel):
    """Settings for VACE ControlNet video generation."""
    
    model: Wan2GPModel = Wan2GPModel.VACE_14B
    prompt: str
    control_video_path: str
    negative_prompt: str = ""
    resolution: Resolution = Resolution.R_832x480
    video_length: int = 81
    seed: int = -1
    control_video_process: ControlVideoProcess = ControlVideoProcess.KEEP_UNCHANGED
    area_processed: AreaProcessed = AreaProcessed.WHOLE_VIDEO
    reference_images: Optional[List[str]] = None
    video_mask_path: Optional[str] = None
    
    def to_full_settings(self) -> GenerationSettings:
        """Convert to full GenerationSettings with VACE-specific parameters."""
        return GenerationSettings(
            model=self.model,
            prompt=self.prompt,
            negative_prompt=self.negative_prompt,
            resolution=self.resolution,
            video_length=self.video_length,
            seed=self.seed,
            control_video_path=self.control_video_path,
            control_video_process=self.control_video_process,
            area_processed=self.area_processed,
            reference_images=self.reference_images or [],
            video_mask_path=self.video_mask_path,
            num_inference_steps=30,
            guidance_scale=5.0,
            slg_switch=SkipLayerGuidance.ENABLED,  # Recommended for VACE
        )


class GenerationResult(BaseModel):
    """Result of a video generation task."""
    
    success: bool
    video_path: Optional[str] = None
    error_message: Optional[str] = None
    generation_time: Optional[float] = None
    settings_used: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ServerStatus(BaseModel):
    """Status information about the Wan2GP server."""
    
    connected: bool
    server_address: str
    available_models: List[str] = Field(default_factory=list)
    current_model: Optional[str] = None
    queue_length: int = 0
    error_message: Optional[str] = None
    api_endpoints: int = 0


class QueueItem(BaseModel):
    """Item in the generation queue."""
    
    id: str
    prompt: str
    model: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float = 0.0
    estimated_time: Optional[float] = None
