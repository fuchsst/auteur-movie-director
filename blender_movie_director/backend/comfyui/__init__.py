"""ComfyUI Client Integration for Blender Movie Director.

This module provides a client interface to ComfyUI for image and video generation.
Uses the comfyuiclient library for workflow submission and result handling.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from comfyuiclient import ComfyUIClient, ComfyUIClientAsync

logger = logging.getLogger(__name__)


class ComfyUIClientWrapper:
    """Wrapper for ComfyUI API client with addon-specific functionality."""

    def __init__(self, server_address: str = "localhost:8188", workflow_file: str = ""):
        """Initialize the ComfyUI client wrapper."""
        self.server_address = server_address
        self.workflow_file = workflow_file or self._get_default_workflow()
        self.client = None
        self.async_client = None
        logger.info(f"ComfyUI client initialized for {server_address}")

    def _get_default_workflow(self) -> str:
        """Get the default workflow file path."""
        # Look for workflow files in the workflows/comfyui directory
        workflow_dir = os.path.join(os.path.dirname(__file__), "..", "..", "workflows", "comfyui")
        
        # Try workflow_api.json first, then workflow.json
        for filename in ["video_generation.json", "character_creation.json", "workflow_api.json", "workflow.json"]:
            workflow_path = os.path.join(workflow_dir, filename)
            if os.path.exists(workflow_path):
                return workflow_path
        
        # If no workflow found, we'll need to create a basic one
        logger.warning("No workflow file found, will need to provide one")
        return ""

    def connect(self):
        """Connect to ComfyUI server synchronously."""
        if not self.workflow_file:
            raise ValueError("No workflow file specified")
        
        self.client = ComfyUIClient(self.server_address, self.workflow_file)
        self.client.connect()
        logger.info("Connected to ComfyUI server")

    async def connect_async(self):
        """Connect to ComfyUI server asynchronously."""
        if not self.workflow_file:
            raise ValueError("No workflow file specified")
        
        self.async_client = ComfyUIClientAsync(self.server_address, self.workflow_file)
        await self.async_client.connect()
        logger.info("Connected to ComfyUI server (async)")

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        seed: int = -1,
        steps: int = 20,
        cfg_scale: float = 7.0,
        width: int = 512,
        height: int = 512,
        output_nodes: List[str] = []
    ) -> Dict[str, Any]:
        """Generate images using the synchronous client."""
        if not self.client:
            self.connect()
        
        # Set parameters
        self.client.set_data(key='CLIP Text Encode Positive', text=prompt)
        if negative_prompt:
            self.client.set_data(key='CLIP Text Encode Negative', text=negative_prompt)
        
        if seed != -1:
            self.client.set_data(key='KSampler', seed=seed)
        
        self.client.set_data(key='KSampler', steps=steps)
        self.client.set_data(key='KSampler', cfg=cfg_scale)
        self.client.set_data(key='EmptyLatentImage', width=width, height=height)
        
        # Generate
        output_nodes = output_nodes or ["Result Image"]
        results = self.client.generate(output_nodes)
        
        logger.info(f"Generated {len(results)} images")
        return results

    async def generate_image_async(
        self,
        prompt: str,
        negative_prompt: str = "",
        seed: int = -1,
        steps: int = 20,
        cfg_scale: float = 7.0,
        width: int = 512,
        height: int = 512,
        output_nodes: List[str] = []
    ) -> Dict[str, Any]:
        """Generate images using the asynchronous client."""
        if not self.async_client:
            await self.connect_async()
        
        # Set parameters
        await self.async_client.set_data(key='CLIP Text Encode Positive', text=prompt)
        if negative_prompt:
            await self.async_client.set_data(key='CLIP Text Encode Negative', text=negative_prompt)
        
        if seed != -1:
            await self.async_client.set_data(key='KSampler', seed=seed)
        
        await self.async_client.set_data(key='KSampler', steps=steps)
        await self.async_client.set_data(key='KSampler', cfg=cfg_scale)
        await self.async_client.set_data(key='EmptyLatentImage', width=width, height=height)
        
        # Generate
        output_nodes = output_nodes or ["Result Image"]
        results = await self.async_client.generate(output_nodes)
        
        logger.info(f"Generated {len(results)} images")
        return results

    def generate_character_image(
        self,
        character_description: str,
        style_prompt: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a character image."""
        prompt = character_description
        if style_prompt:
            prompt += f", {style_prompt}"
        
        return self.generate_image(prompt=prompt, **kwargs)

    async def generate_character_image_async(
        self,
        character_description: str,
        style_prompt: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a character image asynchronously."""
        prompt = character_description
        if style_prompt:
            prompt += f", {style_prompt}"
        
        return await self.generate_image_async(prompt=prompt, **kwargs)

    def generate_scene_image(
        self,
        scene_description: str,
        lighting: str = "",
        camera_angle: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a scene image."""
        prompt = scene_description
        if lighting:
            prompt += f", {lighting}"
        if camera_angle:
            prompt += f", {camera_angle}"
        
        return self.generate_image(prompt=prompt, **kwargs)

    async def generate_scene_image_async(
        self,
        scene_description: str,
        lighting: str = "",
        camera_angle: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a scene image asynchronously."""
        prompt = scene_description
        if lighting:
            prompt += f", {lighting}"
        if camera_angle:
            prompt += f", {camera_angle}"
        
        return await self.generate_image_async(prompt=prompt, **kwargs)

    def close(self):
        """Close the synchronous client connection."""
        if self.client:
            self.client.close()
            self.client = None

    async def close_async(self):
        """Close the asynchronous client connection."""
        if self.async_client:
            await self.async_client.close()
            self.async_client = None


# Singleton instance for the addon
_comfyui_client = None


def get_comfyui_client(server_address: str = "localhost:8188", workflow_file: str = "") -> ComfyUIClientWrapper:
    """Get the singleton ComfyUI client instance."""
    global _comfyui_client
    if _comfyui_client is None or _comfyui_client.server_address != server_address:
        _comfyui_client = ComfyUIClientWrapper(server_address, workflow_file)
    return _comfyui_client


# Convenience functions for common workflows
def generate_character_image(
    character_description: str,
    style_prompt: str = "",
    **kwargs
) -> Dict[str, Any]:
    """Generate a character image using ComfyUI."""
    return get_comfyui_client().generate_character_image(
        character_description=character_description,
        style_prompt=style_prompt,
        **kwargs
    )


async def generate_character_image_async(
    character_description: str,
    style_prompt: str = "",
    **kwargs
) -> Dict[str, Any]:
    """Generate a character image using ComfyUI asynchronously."""
    return await get_comfyui_client().generate_character_image_async(
        character_description=character_description,
        style_prompt=style_prompt,
        **kwargs
    )


def generate_scene_image(
    scene_description: str,
    lighting: str = "",
    camera_angle: str = "",
    **kwargs
) -> Dict[str, Any]:
    """Generate a scene image using ComfyUI."""
    return get_comfyui_client().generate_scene_image(
        scene_description=scene_description,
        lighting=lighting,
        camera_angle=camera_angle,
        **kwargs
    )


async def generate_scene_image_async(
    scene_description: str,
    lighting: str = "",
    camera_angle: str = "",
    **kwargs
) -> Dict[str, Any]:
    """Generate a scene image using ComfyUI asynchronously."""
    return await get_comfyui_client().generate_scene_image_async(
        scene_description=scene_description,
        lighting=lighting,
        camera_angle=camera_angle,
        **kwargs
    )
