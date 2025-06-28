"""Core Wan2GP client implementation.

This module provides the main client class for interacting with the Wan2GP
Gradio API, handling the complexities of the stateful interface.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from gradio_client import Client, handle_file

from .schemas import (
    GenerationSettings, GenerationResult, ServerStatus, QueueItem,
    QuickGenerationSettings, HighQualityGenerationSettings, VACEGenerationSettings
)
from .enums import Wan2GPModel, RECOMMENDED_SETTINGS

logger = logging.getLogger(__name__)


class Wan2GPClient:
    """A robust client for interacting with the Wan2GP Gradio API."""

    def __init__(self, server_address: str = "http://localhost:7860"):
        """Initialize the Wan2GP client.
        
        Args:
            server_address: The address of the Wan2GP server
        """
        self.server_address = server_address
        self.client: Optional[Client] = None
        self.active_model: Optional[str] = None
        self.connected = False
        logger.info(f"Wan2GP client initialized for {server_address}")

    def connect(self) -> bool:
        """Connect to the Wan2GP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = Client(self.server_address, verbose=False)
            self.connected = True
            logger.info(f"Successfully connected to Wan2GP server at {self.server_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Wan2GP server: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from the server."""
        if self.client:
            self.client = None
            self.connected = False
            self.active_model = None
            logger.info("Disconnected from Wan2GP server")

    def _ensure_connected(self):
        """Ensure we have a valid connection to the server."""
        if not self.connected or not self.client:
            if not self.connect():
                raise ConnectionError("Failed to connect to Wan2GP server")

    def _select_model(self, model_name: str) -> bool:
        """Select a model on the Wan2GP server.
        
        Args:
            model_name: The model to select
            
        Returns:
            True if model selection successful
        """
        if self.active_model == model_name:
            return True
            
        try:
            self._ensure_connected()
            if not self.client:
                return False
                
            logger.info(f"Changing model to {model_name}")
            
            result = self.client.predict(
                model_choice=model_name,
                api_name="/change_model"
            )
            
            self.active_model = model_name
            logger.info(f"Successfully changed model to {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to select model {model_name}: {e}")
            return False

    def _prepare_file_parameters(self, settings: GenerationSettings) -> Dict[str, Any]:
        """Prepare file parameters for the API call.
        
        Args:
            settings: The generation settings
            
        Returns:
            Dictionary of file parameters
        """
        file_params = {}
        
        # Handle video files
        if settings.control_video_path:
            file_params["video_guide"] = {"video": handle_file(settings.control_video_path)}
        
        if settings.video_source:
            file_params["video_source"] = {"video": handle_file(settings.video_source)}
            
        if settings.video_mask_path:
            file_params["video_mask"] = {"video": handle_file(settings.video_mask_path)}
        
        # Handle audio files
        if settings.audio_guide:
            file_params["audio_guide"] = handle_file(settings.audio_guide)
        
        # Handle image files
        if settings.image_start:
            file_params["image_start"] = [
                {"image": handle_file(img)} for img in settings.image_start
            ]
            
        if settings.image_end:
            file_params["image_end"] = [
                {"image": handle_file(img)} for img in settings.image_end
            ]
            
        if settings.reference_images:
            file_params["image_refs"] = [
                {"image": handle_file(img)} for img in settings.reference_images
            ]
        
        return file_params

    def _convert_settings_to_api_params(self, settings: GenerationSettings) -> Dict[str, Any]:
        """Convert GenerationSettings to API parameters.
        
        Args:
            settings: The generation settings
            
        Returns:
            Dictionary of API parameters
        """
        # Start with the basic parameters
        params = {
            "prompt": settings.prompt,
            "negative_prompt": settings.negative_prompt,
            "resolution": settings.resolution.value,
            "video_length": settings.video_length,
            "seed": settings.seed,
            "num_inference_steps": settings.num_inference_steps,
            "guidance_scale": settings.guidance_scale,
            "audio_guidance_scale": settings.audio_guidance_scale,
            "flow_shift": settings.flow_shift,
            "embedded_guidance_scale": settings.embedded_guidance_scale,
            "repeat_generation": settings.repeat_generation,
            "multi_prompts_gen_type": settings.multi_prompts_gen_type.value,
            "multi_images_gen_type": settings.multi_images_gen_type.value,
            "tea_cache_setting": settings.tea_cache_setting.value,
            "tea_cache_start_step_perc": settings.tea_cache_start_step_perc,
            "loras_choices": settings.loras_choices,
            "loras_multipliers": settings.loras_multipliers,
            "keep_frames_video_source": settings.keep_frames_video_source,
            "video_guide_outpainting": settings.video_guide_outpainting,
            "video_prompt_type": settings.video_prompt_type,
            "frames_positions": settings.frames_positions,
            "keep_frames_video_guide": "",  # Default from API
            "control_net_weight": settings.control_net_weight,
            "control_net_weight2": settings.control_net_weight2,
            "mask_expand": settings.mask_expand,
            "sliding_window_size": settings.sliding_window_size,
            "sliding_window_overlap": settings.sliding_window_overlap,
            "sliding_window_overlap_noise": settings.sliding_window_overlap_noise,
            "sliding_window_discard_last_frames": settings.sliding_window_discard_last_frames,
            "remove_background_images_ref": settings.remove_background_images_ref.value,
            "temporal_upsampling": settings.temporal_upsampling.value,
            "spatial_upsampling": settings.spatial_upsampling.value,
            "RIFLEx_setting": settings.riflex_setting.value,
            "slg_switch": settings.slg_switch.value,
            "slg_layers": [str(layer) for layer in settings.slg_layers],
            "slg_start_perc": settings.slg_start_perc,
            "slg_end_perc": settings.slg_end_perc,
            "cfg_star_switch": settings.cfg_star_switch.value,
            "cfg_zero_step": settings.cfg_zero_step,
            "prompt_enhancer": settings.prompt_enhancer.value,
        }
        
        # Add file parameters
        file_params = self._prepare_file_parameters(settings)
        params.update(file_params)
        
        # Handle special cases for different model types
        if "vace" in settings.model.value.lower():
            # VACE models need area processing
            params["area_processed"] = settings.area_processed.value
        
        return params

    def _wait_for_generation(self, timeout: float = 300.0) -> Optional[str]:
        """Wait for generation to complete and return the result path.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Path to generated video or None if failed
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check status
                status_result = self.client.predict(api_name="/refresh_status_async")
                status = status_result if isinstance(status_result, str) else ""
                
                # Check if generation is complete
                if "completed" in status.lower() or "finished" in status.lower():
                    # Get the generated videos
                    gallery_result = self.client.predict(api_name="/refresh_gallery")
                    
                    if gallery_result and len(gallery_result) >= 1 and gallery_result[0]:
                        videos = gallery_result[0]
                        if videos and len(videos) > 0:
                            # Extract video path from the first result
                            video_info = videos[0]
                            if isinstance(video_info, dict) and "video" in video_info:
                                return video_info["video"]
                            elif hasattr(video_info, 'name'):
                                return video_info.name
                            elif isinstance(video_info, str):
                                return video_info
                
                # Check for errors
                if "error" in status.lower() or "failed" in status.lower():
                    logger.error(f"Generation failed: {status}")
                    return None
                
                # Wait before checking again
                time.sleep(2.0)
                
            except Exception as e:
                logger.warning(f"Error checking generation status: {e}")
                time.sleep(2.0)
        
        logger.error(f"Generation timed out after {timeout} seconds")
        return None

    def generate(self, settings: GenerationSettings) -> GenerationResult:
        """Generate a video based on the provided settings.
        
        Args:
            settings: The generation settings
            
        Returns:
            GenerationResult with success status and video path or error
        """
        start_time = time.time()
        
        try:
            self._ensure_connected()
            
            # Select the appropriate model
            if not self._select_model(settings.model.value):
                return GenerationResult(
                    success=False,
                    error_message=f"Failed to select model: {settings.model.value}"
                )
            
            # Convert settings to API parameters
            api_params = self._convert_settings_to_api_params(settings)
            
            logger.info(f"Starting generation with model {settings.model.value}")
            logger.debug(f"Generation parameters: {api_params}")
            
            # Submit the generation task
            self.client.predict(
                model_choice=settings.model.value,
                api_name="/process_prompt_and_add_tasks"
            )
            
            # Wait for completion
            video_path = self._wait_for_generation()
            
            generation_time = time.time() - start_time
            
            if video_path:
                logger.info(f"Generation completed successfully in {generation_time:.1f}s: {video_path}")
                return GenerationResult(
                    success=True,
                    video_path=video_path,
                    generation_time=generation_time,
                    settings_used=settings.dict()
                )
            else:
                return GenerationResult(
                    success=False,
                    error_message="Generation failed or timed out",
                    generation_time=generation_time
                )
                
        except Exception as e:
            generation_time = time.time() - start_time
            error_msg = f"Generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return GenerationResult(
                success=False,
                error_message=error_msg,
                generation_time=generation_time
            )

    def get_server_status(self) -> ServerStatus:
        """Get the current status of the Wan2GP server.
        
        Returns:
            ServerStatus with connection and model information
        """
        try:
            self._ensure_connected()
            
            # Try to get server info
            api_info = self.client.view_api()
            endpoints_count = len(api_info.get("named_endpoints", {})) if isinstance(api_info, dict) else 0
            
            # Get available models (this is a simplified approach)
            available_models = [model.value for model in Wan2GPModel]
            
            return ServerStatus(
                connected=True,
                server_address=self.server_address,
                available_models=available_models,
                current_model=self.active_model,
                api_endpoints=endpoints_count
            )
            
        except Exception as e:
            logger.error(f"Failed to get server status: {e}")
            return ServerStatus(
                connected=False,
                server_address=self.server_address,
                error_message=str(e)
            )

    def abort_generation(self) -> bool:
        """Abort the current generation task.
        
        Returns:
            True if abort was successful
        """
        try:
            self._ensure_connected()
            self.client.predict(api_name="/abort_generation")
            logger.info("Generation aborted")
            return True
        except Exception as e:
            logger.error(f"Failed to abort generation: {e}")
            return False

    def clear_queue(self) -> bool:
        """Clear the generation queue.
        
        Returns:
            True if queue was cleared successfully
        """
        try:
            self._ensure_connected()
            self.client.predict(api_name="/clear_queue_action")
            logger.info("Queue cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            return False

    def get_queue_status(self) -> List[QueueItem]:
        """Get the current queue status.
        
        Returns:
            List of queue items
        """
        try:
            self._ensure_connected()
            # This is a simplified implementation
            # The actual queue data structure would need to be parsed from the API
            return []
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return []

    # Convenience methods for common generation types
    def generate_quick(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate a quick preview video.
        
        Args:
            prompt: Text prompt for generation
            **kwargs: Additional settings to override defaults
            
        Returns:
            GenerationResult
        """
        quick_settings = QuickGenerationSettings(prompt=prompt, **kwargs)
        full_settings = quick_settings.to_full_settings()
        return self.generate(full_settings)

    def generate_high_quality(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate a high-quality video.
        
        Args:
            prompt: Text prompt for generation
            **kwargs: Additional settings to override defaults
            
        Returns:
            GenerationResult
        """
        hq_settings = HighQualityGenerationSettings(prompt=prompt, **kwargs)
        full_settings = hq_settings.to_full_settings()
        return self.generate(full_settings)

    def generate_with_control(self, prompt: str, control_video_path: str, **kwargs) -> GenerationResult:
        """Generate a video using VACE ControlNet.
        
        Args:
            prompt: Text prompt for generation
            control_video_path: Path to control video
            **kwargs: Additional settings to override defaults
            
        Returns:
            GenerationResult
        """
        vace_settings = VACEGenerationSettings(
            prompt=prompt,
            control_video_path=control_video_path,
            **kwargs
        )
        full_settings = vace_settings.to_full_settings()
        return self.generate(full_settings)
