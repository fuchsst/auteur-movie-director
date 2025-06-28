"""LiteLLM Integration for Blender Movie Director.

This module provides a unified interface to various LLM providers using the litellm library.
Assumes litellm is properly installed and configured via environment variables.
"""

import logging
import os
from typing import Dict, List, Optional

from litellm import completion, acompletion

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client using litellm library."""

    def __init__(self):
        """Initialize the LLM client."""
        self.default_model = "gpt-3.5-turbo"
        
    def get_available_models(self) -> List[str]:
        """Get list of commonly available models."""
        return [
            # OpenAI models
            "gpt-4",
            "gpt-4-turbo", 
            "gpt-3.5-turbo",
            
            # Anthropic models
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            
            # Local models (Ollama)
            "ollama/llama2",
            "ollama/mistral",
            "ollama/codellama",
        ]

    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using the specified model."""
        model = model or self.default_model
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        logger.info(f"Generating text with model: {model}")
        
        response = completion(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        content = response.choices[0].message.content
        logger.info(f"Successfully generated text with {model}")
        return content

    async def generate_text_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text asynchronously using the specified model."""
        model = model or self.default_model
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        logger.info(f"Generating text async with model: {model}")
        
        response = await acompletion(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        content = response.choices[0].message.content
        logger.info(f"Successfully generated text with {model}")
        return content

    def get_model_info(self, model: str) -> Dict[str, str]:
        """Get basic information about a model."""
        info = {"name": model, "provider": "unknown"}
        
        if model.startswith("gpt-"):
            info["provider"] = "openai"
        elif model.startswith("claude-"):
            info["provider"] = "anthropic"
        elif model.startswith("ollama/"):
            info["provider"] = "ollama"
        
        return info


# Singleton instance for the addon
_llm_client = None


def get_llm_client() -> LLMClient:
    """Get the singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# Convenience functions for common use cases
def generate_script_content(prompt: str, **kwargs) -> str:
    """Generate script content using the LLM."""
    system_prompt = """You are a professional screenwriter. Generate compelling, 
    cinematic dialogue and scene descriptions. Focus on visual storytelling 
    and character development."""
    
    return get_llm_client().generate_text(
        prompt=prompt,
        system_prompt=system_prompt,
        **kwargs
    )


def generate_character_description(character_name: str, context: str = "", **kwargs) -> str:
    """Generate a detailed character description."""
    prompt = f"Create a detailed visual description for a character named '{character_name}'"
    if context:
        prompt += f" in the context of: {context}"
    
    system_prompt = """You are a character designer. Create detailed visual 
    descriptions that can be used for AI image generation. Focus on physical 
    appearance, clothing, and distinctive features."""
    
    return get_llm_client().generate_text(
        prompt=prompt,
        system_prompt=system_prompt,
        **kwargs
    )


def generate_scene_description(scene_context: str, **kwargs) -> str:
    """Generate a detailed scene description for image/video generation."""
    system_prompt = """You are a cinematographer. Create detailed scene 
    descriptions that include lighting, camera angles, mood, and visual elements. 
    Focus on creating compelling visual compositions."""
    
    return get_llm_client().generate_text(
        prompt=scene_context,
        system_prompt=system_prompt,
        **kwargs
    )
