# LiteLLM Backend Integration

## Role
Text generation service providing unified access to multiple LLM providers. Powers the Screenwriter agent and provides creative assistance throughout the production pipeline.

## Capabilities
- **Multiple Models** - Llama 3, specialized fine-tunes, custom models
- **Unified API** - Provider-agnostic interface
- **High Performance** - Low-latency local inference
- **Creative Tools** - Script generation, character development, prompt enhancement

## Client Implementation
```python
class LiteLLMClient:
    def __init__(self, base_url="http://localhost:4000"):
        self.base_url = base_url
        self.client = AsyncOpenAI(base_url=base_url)
    
    async def generate_text(self, prompt, model="llama3"):
        """Generate text using specified model"""
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

## Text Generation Tasks
- **Script Development** - Collaborative screenplay writing
- **Character Backstories** - Rich character development
- **Prompt Enhancement** - Improve generation prompts
- **Creative Suggestions** - Story and dialogue assistance

## Use Cases
- Screenwriter agent text generation
- Creative brainstorming and ideation
- Prompt optimization for visual generation
- Script formatting and structure

## Reference
- [LiteLLM Documentation](/.bmad-core/data/blender-addon-development-kb.md)