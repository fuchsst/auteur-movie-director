# Screenwriter Agent - Script Development

## Role
LLM-powered agent responsible for collaborative script development, transforming high-level concepts into structured narrative blueprints ready for production.

## Responsibilities
- **Concept Development** - Collaborate with user to develop story ideas
- **Script Formatting** - Generate properly formatted screenplays
- **Scene Breakdown** - Parse script into Scene and Shot data structures
- **Creative Suggestions** - Provide LLM-powered creative assistance

## Implementation Pattern
```python
class ScreenwriterAgent(Agent):
    role = "Expert Screenwriter"
    goal = "Transform concepts into compelling, structured screenplays"
    backstory = "Professional screenwriter with expertise in narrative structure"
    
    tools = [
        generate_script_tool,
        parse_script_tool,
        create_scene_breakdown_tool
    ]
```

## Workflow
1. **User Input** - Receive high-level concept or story idea
2. **LLM Generation** - Use LiteLLM for script development
3. **Script Parsing** - Extract scenes, shots, and dialogue
4. **Blender Integration** - Create Scene Collections and Shot objects

## Backend Integration
- **LiteLLM** for text generation and creative assistance
- **Script Parser** for extracting structured data
- **Blender API** for creating scene hierarchy

## Reference
- [LiteLLM Integration](/.bmad-core/data/blender-addon-development-kb.md)