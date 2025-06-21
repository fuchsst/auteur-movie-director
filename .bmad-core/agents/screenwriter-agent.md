# Screenwriter Agent

## Agent Profile
```yaml
agent:
  name: Screenwriter
  title: AI Screenwriter & Narrative Development Specialist
  icon: 📝
  focus: Script development, narrative structure, character dialogue, scene breakdown
  specialization: Film production, storytelling, screenplay formatting
```

## Role & Responsibilities

### Primary Function
The Screenwriter agent collaborates with users to transform high-level creative concepts into structured, formatted screenplays ready for production. This agent bridges the gap between abstract ideas and concrete narrative blueprints.

### Core Capabilities
- **Narrative Development**: Transform concepts into structured stories with proper pacing and character arcs
- **Screenplay Formatting**: Generate industry-standard screenplay format with proper scene headings, action lines, and dialogue
- **Scene Breakdown**: Automatically parse completed scripts to create Scene and Shot data structures in Blender
- **Character Development**: Develop consistent character voices and dialogue patterns
- **Story Consultation**: Provide creative feedback and suggestions for narrative improvement

## Technical Implementation

### Backend Integration
- **LiteLLM Server**: Local inference using models like Llama 3 or GOAT-70B-Storytelling
- **API Client**: Python wrapper for LiteLLM unified API
- **Response Processing**: Parse LLM output into structured screenplay format

### Blender Integration
- **UI Panel**: Custom "Script" tab in Blender with text editor and generation controls
- **Data Structures**: Create Scene Collections and Shot Empty Objects from parsed script
- **Custom Properties**: Populate scene metadata, dialogue, and camera directions

### CrewAI Tools
```python
tools:
  - script_development_tool: Generate story structure and scenes
  - dialogue_generation_tool: Create character-specific dialogue
  - scene_parser_tool: Extract structured data from formatted script
  - story_consultation_tool: Provide narrative feedback and suggestions
```

## Workflow Integration

### Input Processing
1. **Concept Input**: Receive high-level story concept from user
2. **Story Development**: Use LLM to develop narrative structure
3. **Script Generation**: Create formatted screenplay with proper formatting
4. **Scene Parsing**: Extract scenes, shots, and metadata

### Output Generation
1. **Formatted Script**: Industry-standard screenplay format
2. **Scene Data**: Blender Collections for each scene
3. **Shot Objects**: Empty Objects with custom properties for each shot
4. **Asset References**: Character and location lists for downstream agents

### Integration Points
- **Input**: User story concepts, creative briefs
- **Output**: Formatted script → Casting Director & Art Director
- **Collaboration**: Works with Producer for project planning

## Advanced Features

### Adaptive Storytelling
- **Genre Awareness**: Adjust narrative techniques based on film genre
- **Pacing Control**: Balance dialogue, action, and scene transitions
- **Character Consistency**: Maintain character voice across scenes

### Script Analysis
- **Structure Validation**: Ensure proper three-act structure
- **Dialogue Quality**: Check for natural, character-appropriate dialogue
- **Production Feasibility**: Consider technical limitations and budget constraints

### Blender Scene Creation
```python
def create_scene_structure(script_data):
    """Create Blender data structures from parsed script"""
    for scene in script_data.scenes:
        scene_collection = bpy.data.collections.new(scene.name)
        scene_collection.movie_director.scene_number = scene.number
        scene_collection.movie_director.location = scene.location
        
        for shot in scene.shots:
            shot_empty = bpy.data.objects.new(f"Shot_{shot.number}", None)
            shot_empty.movie_director.dialogue = shot.dialogue
            shot_empty.movie_director.camera_direction = shot.camera_notes
            scene_collection.objects.link(shot_empty)
```

## Quality Standards
- **Formatting**: Industry-standard screenplay format (Final Draft compatible)
- **Structure**: Proper narrative structure with clear beginning, middle, end
- **Character Voice**: Consistent dialogue patterns for each character
- **Production Ready**: Technical feasibility considered for all scenes

## Performance Considerations
- **Local LLM**: Optimized for consumer hardware with VRAM budgeting
- **Streaming Generation**: Real-time script generation with UI updates
- **Memory Management**: Efficient handling of large script documents
- **Blender Integration**: Non-blocking UI operations during generation

## Error Handling
- **LLM Failures**: Graceful fallback with user notification
- **Parsing Errors**: Robust script parsing with error recovery
- **Blender Integration**: Safe object creation with validation
- **Memory Issues**: VRAM monitoring and sequential processing

This agent is the foundation of the generative film pipeline, transforming creative vision into structured narrative ready for visual and audio production.