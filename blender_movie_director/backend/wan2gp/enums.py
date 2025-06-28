"""Enumerations for Wan2GP API constants.

This module defines all the fixed values and options available in the Wan2GP API,
extracted from the API documentation at http://localhost:7860/?view=api
"""

from enum import Enum


class Wan2GPModel(str, Enum):
    """Available Wan2GP models for video generation."""
    
    # Text-to-Video Models
    T2V_1_3B = "t2v_1.3B"
    T2V_14B = "t2v"
    
    # Image-to-Video Models
    I2V_14B = "i2v"
    I2V_720P = "i2v_720p"
    FLF2V_720P = "flf2v_720p"
    
    # VACE ControlNet Models
    VACE_1_3B = "vace_1.3B"
    VACE_14B = "vace_14B"
    
    # Specialized Models
    MOVIIGEN = "moviigen"
    PHANTOM_1_3B = "phantom_1.3B"
    PHANTOM_14B = "phantom_14B"
    FANTASY = "fantasy"
    FUN_INP_1_3B = "fun_inp_1.3B"
    FUN_INP_14B = "fun_inp"
    RECAM_1_3B = "recam_1.3B"
    SKY_DF_1_3B = "sky_df_1.3B"
    SKY_DF_14B = "sky_df_14B"
    SKY_DF_720P_14B = "sky_df_720p_14B"
    
    # LTX Video Models
    LTXV_13B = "ltxv_13B"
    LTXV_13B_DISTILLED = "ltxv_13B_distilled"
    
    # Hunyuan Video Models
    HUNYUAN_T2V = "hunyuan"
    HUNYUAN_I2V = "hunyuan_i2v"
    HUNYUAN_CUSTOM = "hunyuan_custom"
    HUNYUAN_CUSTOM_AUDIO = "hunyuan_custom_audio"
    HUNYUAN_CUSTOM_EDIT = "hunyuan_custom_edit"
    HUNYUAN_AVATAR = "hunyuan_avatar"
    HUNYUAN_T2V_ACCVIDEO = "hunyuan_t2v_accvideo"
    HUNYUAN_T2V_FAST = "hunyuan_t2v_fast"
    
    # Fusion Models
    T2V_FUSIONIX = "t2v_fusionix"
    T2V_SF = "t2v_sf"
    VACE_14B_FUSIONIX = "vace_14B_fusionix"
    VACE_14B_SF = "vace_14B_sf"


class Resolution(str, Enum):
    """Supported video resolutions."""
    
    # Standard resolutions
    R_1920x832 = "1920x832"
    R_832x1920 = "832x1920"
    R_1280x720 = "1280x720"
    R_720x1280 = "720x1280"
    R_1024x1024 = "1024x1024"
    R_1280x544 = "1280x544"
    R_544x1280 = "544x1280"
    R_1104x832 = "1104x832"
    R_832x1104 = "832x1104"
    R_960x960 = "960x960"
    R_960x544 = "960x544"
    R_544x960 = "544x960"
    R_832x480 = "832x480"
    R_480x832 = "480x832"
    R_832x624 = "832x624"
    R_624x832 = "624x832"
    R_720x720 = "720x720"
    R_512x512 = "512x512"


class ControlVideoProcess(str, Enum):
    """Control video processing types for VACE models."""
    
    KEEP_UNCHANGED = "Keep Unchanged"
    TRANSFER_HUMAN_MOTION = "Transfer Human Motion"
    INPAINTING = "Inpainting"
    DEPTH = "Depth"
    CANNY = "Canny"
    OPENPOSE = "OpenPose"


class AreaProcessed(str, Enum):
    """Area processing options for VACE models."""
    
    WHOLE_VIDEO = ""
    MASKED_AREA = "A"
    NON_MASKED_AREA = "NA"
    X_MASKED_AREA = "XA"
    X_NON_MASKED_AREA = "XNA"
    Y_MASKED_AREA = "YA"
    Y_NON_MASKED_AREA = "YNA"
    W_MASKED_AREA = "WA"
    W_NON_MASKED_AREA = "WNA"
    Z_MASKED_AREA = "ZA"
    Z_NON_MASKED_AREA = "ZNA"


class TeaCacheSetting(str, Enum):
    """Tea Cache acceleration settings."""
    
    DISABLED = "0"
    LEVEL_1_5 = "1.5"
    LEVEL_1_75 = "1.75"
    LEVEL_2_0 = "2.0"
    LEVEL_2_25 = "2.25"
    LEVEL_2_5 = "2.5"


class TemporalUpsampling(str, Enum):
    """Temporal upsampling options."""
    
    DISABLED = ""
    RIFE2 = "rife2"
    RIFE4 = "rife4"


class SpatialUpsampling(str, Enum):
    """Spatial upsampling options."""
    
    DISABLED = ""
    LANCZOS_1_5 = "lanczos1.5"
    LANCZOS_2 = "lanczos2"


class RIFLExSetting(str, Enum):
    """RIFLEx positional embedding settings for long video generation."""
    
    DISABLED = "0"
    ENABLED = "1"
    ENHANCED = "2"


class SkipLayerGuidance(str, Enum):
    """Skip Layer Guidance settings."""
    
    DISABLED = "0"
    ENABLED = "1"


class CFGStar(str, Enum):
    """CFG Star settings."""
    
    DISABLED = "0"
    ENABLED = "1"


class PromptEnhancer(str, Enum):
    """Prompt enhancer options."""
    
    DISABLED = ""
    TEXT_ONLY = "T"
    IMAGE_ONLY = "I"
    TEXT_AND_IMAGE = "TI"


class RemoveBackground(str, Enum):
    """Background removal options for reference images."""
    
    DISABLED = "0"
    ENABLED = "1"
    AUTO = "2"


class MultiPromptsGenType(str, Enum):
    """Multi-prompts generation type."""
    
    SINGLE = "0"
    MULTIPLE = "1"


class MultiImagesGenType(str, Enum):
    """Multi-images generation type."""
    
    SINGLE = "0"
    MULTIPLE = "1"


# Model categories for easier selection
MODEL_CATEGORIES = {
    "text_to_video": [
        Wan2GPModel.T2V_1_3B,
        Wan2GPModel.T2V_14B,
        Wan2GPModel.HUNYUAN_T2V,
        Wan2GPModel.LTXV_13B,
        Wan2GPModel.LTXV_13B_DISTILLED,
    ],
    "image_to_video": [
        Wan2GPModel.I2V_14B,
        Wan2GPModel.I2V_720P,
        Wan2GPModel.FUN_INP_1_3B,
        Wan2GPModel.FUN_INP_14B,
        Wan2GPModel.HUNYUAN_I2V,
    ],
    "controlnet": [
        Wan2GPModel.VACE_1_3B,
        Wan2GPModel.VACE_14B,
        Wan2GPModel.VACE_14B_FUSIONIX,
        Wan2GPModel.VACE_14B_SF,
    ],
    "specialized": [
        Wan2GPModel.FANTASY,
        Wan2GPModel.PHANTOM_1_3B,
        Wan2GPModel.PHANTOM_14B,
        Wan2GPModel.HUNYUAN_AVATAR,
    ],
    "fast": [
        Wan2GPModel.LTXV_13B_DISTILLED,
        Wan2GPModel.T2V_1_3B,
        Wan2GPModel.HUNYUAN_T2V_FAST,
    ],
    "high_quality": [
        Wan2GPModel.HUNYUAN_T2V,
        Wan2GPModel.T2V_14B,
        Wan2GPModel.VACE_14B,
    ]
}

# Recommended settings for different use cases
RECOMMENDED_SETTINGS = {
    "quick_preview": {
        "model": Wan2GPModel.LTXV_13B_DISTILLED,
        "resolution": Resolution.R_832x480,
        "video_length": 32,  # 2 seconds
        "num_inference_steps": 4,
        "guidance_scale": 1.0,
    },
    "high_quality": {
        "model": Wan2GPModel.HUNYUAN_T2V,
        "resolution": Resolution.R_1280x720,
        "video_length": 129,  # ~8 seconds
        "num_inference_steps": 50,
        "guidance_scale": 6.0,
    },
    "character_animation": {
        "model": Wan2GPModel.HUNYUAN_CUSTOM,
        "resolution": Resolution.R_1280x720,
        "video_length": 81,  # 5 seconds
        "num_inference_steps": 30,
        "guidance_scale": 5.0,
    },
    "controlnet": {
        "model": Wan2GPModel.VACE_14B,
        "resolution": Resolution.R_832x480,
        "video_length": 81,
        "num_inference_steps": 30,
        "guidance_scale": 5.0,
    }
}
