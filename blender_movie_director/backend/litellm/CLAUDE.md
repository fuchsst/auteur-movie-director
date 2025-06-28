# LiteLLM Integration Layer

## Overview

LiteLLM is a **Python library** (not a backend service) that provides unified access to multiple LLM providers. It's used by the Screenwriter agent for narrative development and prompt generation.

## Purpose

As defined in [PRD-001](/.bmad-core/prds/PRD-001-backend-integration-service-layer.md), LiteLLM serves as our LLM integration layer:
- Unified API for multiple providers (OpenAI, Anthropic, Azure, local models)
- Automatic fallback between providers
- Cost tracking and rate limiting
- Streaming support for real-time interaction

## Integration Pattern

```python
import litellm
from litellm import completion

class LLMIntegration:
    """LLM integration using litellm library"""
    
    def __init__(self):
        # Configure providers via environment variables
        # OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
        self.models = self._get_available_models()
    
    async def generate_text(self, prompt: str, model: str = None):
        """Generate text using configured LLM"""
        if not model:
            model = self.get_best_available_model()
            
        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _get_available_models(self):
        """Check which models are available based on API keys"""
        available = []
        
        if litellm.check_valid_key("gpt-3.5-turbo"):
            available.append("gpt-3.5-turbo")
        if litellm.check_valid_key("claude-3-sonnet"):
            available.append("claude-3-sonnet")
            
        return available
```

## Usage by Agents

### Screenwriter Agent
The primary consumer of LLM capabilities:
```python
class ScreenwriterAgent:
    def __init__(self):
        self.llm = LLMIntegration()
    
    async def develop_script(self, concept: str):
        prompt = f"Transform this concept into a screenplay: {concept}"
        return await self.llm.generate_text(prompt)
```

### Producer Agent
Uses LLMs for task planning and orchestration decisions.

## Configuration

Set API keys in `.env` file:
```bash
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
AZURE_API_KEY=your_key_here
```

## Testing

```bash
# Test LLM integration
pytest tests/test_llm_integration.py -v
```

## Reference
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [PRD-001: Backend Integration](/.bmad-core/prds/PRD-001-backend-integration-service-layer.md)
- [STORY-004: LLM Integration Layer](/.bmad-core/stories/EPIC-001-backend-service-connectivity/STORY-004-llm-integration-layer.md)