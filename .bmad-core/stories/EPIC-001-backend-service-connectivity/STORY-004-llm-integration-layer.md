# User Story: LLM Integration Layer

**Story ID:** STORY-004  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Integration Layer  
**Story Points:** 3  
**Priority:** Critical (P0)  

---

## Story Description

**As a** screenwriter using AI for narrative development  
**I want** a unified interface to multiple LLM providers  
**So that** I can leverage the best models for script analysis and generation  

## Acceptance Criteria

### Functional Requirements
- [ ] Integrates LiteLLM library for unified LLM access
- [ ] Supports multiple LLM providers (OpenAI, Anthropic, Azure, etc.)
- [ ] Manages API keys securely
- [ ] Provides model selection and fallback options
- [ ] Implements conversation context management
- [ ] Supports both streaming and non-streaming responses
- [ ] Handles rate limiting and retries
- [ ] Tracks token usage and costs

### Technical Requirements
- [ ] Uses `litellm` Python library
- [ ] Environment variable support for API keys
- [ ] Model availability checking
- [ ] Response caching for repeated queries
- [ ] Async/sync operation modes
- [ ] Error handling for provider failures
- [ ] Token counting and limits
- [ ] Proper cleanup and resource management

### Quality Requirements
- [ ] Response time <2s for simple queries
- [ ] Provider fallback working seamlessly
- [ ] API keys stored securely
- [ ] Clear error messages for failures
- [ ] Unit tests for all providers
- [ ] Mock mode for testing
- [ ] Cost tracking accurate
- [ ] Thread-safe operations

## Implementation Notes

### Technical Approach

**LLM Integration Manager:**
```python
import litellm
import os
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import asyncio

@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    primary_model: str = "gpt-3.5-turbo"
    fallback_models: List[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    cache_responses: bool = True
    
class LLMIntegrationLayer:
    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()
        self.available_models = []
        self.conversation_cache = {}
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize LLM providers from environment or config"""
        # Set API keys from environment
        if openai_key := os.getenv("OPENAI_API_KEY"):
            litellm.openai_key = openai_key
            
        if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
            litellm.anthropic_key = anthropic_key
            
        # Azure configuration
        if azure_key := os.getenv("AZURE_API_KEY"):
            litellm.azure_key = azure_key
            litellm.api_base = os.getenv("AZURE_API_BASE")
            litellm.api_version = os.getenv("AZURE_API_VERSION", "2023-07-01-preview")
            
        # Check available models
        self._check_available_models()
```

**Model Availability Checking:**
```python
def _check_available_models(self):
    """Check which models are available with current API keys"""
    self.available_models = []
    
    test_models = [
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-2",
        "claude-instant-1",
        "command-nightly",
        "llama-2-70b-chat"
    ]
    
    for model in test_models:
        try:
            # Test with minimal tokens
            is_valid = litellm.check_valid_key(
                model=model,
                api_key=self._get_api_key_for_model(model)
            )
            if is_valid:
                self.available_models.append(model)
        except:
            pass
            
    if not self.available_models:
        raise ValueError("No LLM models available. Please configure API keys.")
        
def get_available_models(self) -> List[str]:
    """Get list of currently available models"""
    return self.available_models.copy()
```

**Completion Interface:**
```python
def complete(self,
            prompt: str,
            model: Optional[str] = None,
            messages: Optional[List[Dict]] = None,
            **kwargs) -> Dict:
    """Generate completion using specified or default model"""
    
    # Use provided model or default
    model = model or self.config.primary_model
    
    # Prepare messages
    if messages is None:
        messages = [{"role": "user", "content": prompt}]
        
    # Merge kwargs with config
    completion_kwargs = {
        "model": model,
        "messages": messages,
        "temperature": kwargs.get("temperature", self.config.temperature),
        "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        "timeout": self.config.timeout
    }
    
    try:
        # Try primary model
        response = litellm.completion(**completion_kwargs)
        return self._process_response(response)
        
    except Exception as e:
        # Try fallback models
        if self.config.fallback_models:
            for fallback_model in self.config.fallback_models:
                if fallback_model in self.available_models:
                    try:
                        completion_kwargs["model"] = fallback_model
                        response = litellm.completion(**completion_kwargs)
                        return self._process_response(response)
                    except:
                        continue
                        
        # All models failed
        raise LLMError(f"All models failed. Last error: {e}")
```

**Streaming Support:**
```python
async def complete_stream(self,
                         prompt: str,
                         model: Optional[str] = None,
                         callback = None,
                         **kwargs):
    """Stream completion responses"""
    
    model = model or self.config.primary_model
    
    # Enable streaming
    kwargs["stream"] = True
    
    try:
        response = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        # Process streaming response
        full_response = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                
                if callback:
                    await callback(content)
                    
        return full_response
        
    except Exception as e:
        raise LLMError(f"Streaming failed: {e}")
```

**Conversation Management:**
```python
class ConversationManager:
    """Manage conversation context for LLM interactions"""
    
    def __init__(self, llm: LLMIntegrationLayer):
        self.llm = llm
        self.conversations = {}
        
    def create_conversation(self, conversation_id: str, system_prompt: str = None):
        """Create a new conversation context"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        self.conversations[conversation_id] = {
            "messages": messages,
            "token_count": 0,
            "created_at": datetime.now()
        }
        
    def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to conversation history"""
        if conversation_id not in self.conversations:
            self.create_conversation(conversation_id)
            
        self.conversations[conversation_id]["messages"].append({
            "role": role,
            "content": content
        })
        
        # Update token count
        self._update_token_count(conversation_id)
```

**Cost Tracking:**
```python
class CostTracker:
    """Track LLM usage and costs"""
    
    # Cost per 1K tokens (example rates)
    MODEL_COSTS = {
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "claude-2": {"input": 0.008, "output": 0.024}
    }
    
    def __init__(self):
        self.usage = {}
        
    def track_usage(self, model: str, input_tokens: int, output_tokens: int):
        """Track token usage for a model"""
        if model not in self.usage:
            self.usage[model] = {"input": 0, "output": 0, "requests": 0}
            
        self.usage[model]["input"] += input_tokens
        self.usage[model]["output"] += output_tokens
        self.usage[model]["requests"] += 1
        
    def get_cost_estimate(self) -> Dict[str, float]:
        """Calculate estimated costs"""
        costs = {}
        
        for model, usage in self.usage.items():
            if model in self.MODEL_COSTS:
                input_cost = (usage["input"] / 1000) * self.MODEL_COSTS[model]["input"]
                output_cost = (usage["output"] / 1000) * self.MODEL_COSTS[model]["output"]
                costs[model] = round(input_cost + output_cost, 4)
                
        return costs
```

### Blender Integration
```python
class LLMPropertyGroup(bpy.types.PropertyGroup):
    """Blender properties for LLM configuration"""
    
    model: EnumProperty(
        name="Model",
        items=get_available_model_items,
        description="Select LLM model"
    )
    
    api_key_configured: BoolProperty(
        name="API Key Configured",
        default=False,
        description="Whether API key is set"
    )
    
    enable_streaming: BoolProperty(
        name="Enable Streaming",
        default=True,
        description="Stream responses as they generate"
    )
    
    temperature: FloatProperty(
        name="Temperature",
        default=0.7,
        min=0.0,
        max=2.0,
        description="Control randomness of output"
    )
```

### Error Handling
- API key errors: Clear message about configuration
- Rate limit errors: Automatic retry with backoff
- Model errors: Fallback to alternative models
- Network errors: Timeout and retry logic

## Testing Strategy

### Unit Tests
```python
class TestLLMIntegration(unittest.TestCase):
    def test_model_initialization(self):
        # Test with mock API keys
        
    def test_completion(self):
        # Test completion with mock responses
        
    def test_fallback_behavior(self):
        # Test model fallback logic
        
    def test_cost_tracking(self):
        # Verify cost calculations
```

### Integration Tests
- Test with real API keys (in CI/CD)
- Test model switching
- Test conversation management
- Verify streaming functionality

## Dependencies
- `litellm` Python package
- Environment variables for API keys
- Optional: `tiktoken` for accurate token counting

## Related Stories
- Used by Screenwriter agent in EPIC-006
- Monitored differently than backend services
- Configuration in STORY-014

## Definition of Done
- [ ] LiteLLM integrated successfully
- [ ] Multiple providers supported
- [ ] API key management secure
- [ ] Model fallback working
- [ ] Streaming responses functional
- [ ] Cost tracking accurate
- [ ] Unit tests >90% coverage
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] Backend Engineer
- [ ] QA Engineer