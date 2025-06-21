# implement-crewai-agents

## Task Overview
Implement the film crew AI agents using CrewAI framework, mapping film production roles to specialized AI agents within Blender addon constraints.

## Objective
Create a coordinated team of AI agents that handle different aspects of film production, from script development to final assembly, using the CrewAI framework for orchestration.

## Key Requirements
- [ ] Implement film crew agents using CrewAI framework
- [ ] Map agents to film production roles (Producer, Cinematographer, etc.)
- [ ] Integrate agents with Blender addon architecture
- [ ] Connect agents to generative backends (ComfyUI, Wan2GP, LiteLLM)
- [ ] Implement proper error handling and resource management
- [ ] Maintain state consistency across agent interactions

## Film Crew Agent Architecture

### Agent Hierarchy
```
Producer (Master Orchestrator)
├── Screenwriter (Script Development)
├── Casting Director (Character Management)
├── Art Director (Style Management)
├── Cinematographer (Video Generation)
├── Sound Designer (Audio Generation)
└── Editor (Post-Production)
```

### Core Agent Implementation Pattern
```python
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool

class BlenderAgentTool(BaseTool):
    """Base tool for Blender-specific agent operations"""
    
    def __init__(self, addon_context):
        super().__init__()
        self.addon_context = addon_context
        self.vram_manager = addon_context.vram_manager
        self.backend_clients = addon_context.backend_clients
    
    def _check_resources(self):
        """Verify system resources before execution"""
        return self.vram_manager.check_availability()
    
    def _handle_error(self, error):
        """Standardized error handling for all tools"""
        self.addon_context.log_error(f"{self.__class__.__name__}: {error}")
        return {"success": False, "error": str(error)}
```

## Individual Agent Implementations

### 1. Producer Agent (Master Orchestrator)
```python
class ProducerAgent:
    """Master orchestrator managing the entire film production pipeline"""
    
    def __init__(self, addon_context):
        self.addon_context = addon_context
        self.agent = Agent(
            role="Film Producer and Project Orchestrator",
            goal="Coordinate the entire film production pipeline from concept to final delivery",
            backstory="Expert film producer with deep knowledge of generative AI workflows",
            tools=[
                ProjectManagementTool(addon_context),
                ResourceBudgetingTool(addon_context),
                WorkflowOrchestrationTool(addon_context)
            ],
            verbose=True,
            allow_delegation=True
        )
    
    def create_production_plan(self, script_data):
        """Create comprehensive production plan from script"""
        task = Task(
            description=f"Create production plan for script: {script_data['title']}",
            expected_output="Detailed production breakdown with resource requirements",
            agent=self.agent
        )
        return task.execute()
```

### 2. Screenwriter Agent
```python
class ScreenwriterAgent:
    """AI agent specializing in script development and scene breakdown"""
    
    def __init__(self, addon_context):
        self.agent = Agent(
            role="Expert Screenwriter and Story Developer",
            goal="Transform creative concepts into well-structured screenplays",
            backstory="Professional screenwriter with expertise in visual storytelling",
            tools=[
                ScriptDevelopmentTool(addon_context),
                SceneBreakdownTool(addon_context),
                CharacterDefinitionTool(addon_context)
            ],
            verbose=True
        )
    
    def develop_script(self, concept):
        """Develop full script from initial concept"""
        task = Task(
            description=f"Develop screenplay from concept: {concept}",
            expected_output="Complete screenplay with scene and character breakdowns",
            agent=self.agent
        )
        return task.execute()
```

### 3. Cinematographer Agent
```python
class CinematographerAgent:
    """AI agent for video generation and visual storytelling"""
    
    def __init__(self, addon_context):
        self.agent = Agent(
            role="Expert Cinematographer and Visual Director",
            goal="Transform script descriptions into compelling video sequences",
            backstory="Master cinematographer with expertise in generative video techniques",
            tools=[
                VideoGenerationTool(addon_context),
                CameraControlTool(addon_context),
                CompositionTool(addon_context),
                StyleApplicationTool(addon_context)
            ],
            verbose=True
        )
    
    def generate_shot(self, shot_description, characters, style):
        """Generate video for specific shot"""
        task = Task(
            description=f"Generate video for shot: {shot_description}",
            expected_output="High-quality video file with metadata",
            agent=self.agent
        )
        return task.execute()
```

## Agent Tools Implementation

### Video Generation Tool
```python
class VideoGenerationTool(BlenderAgentTool):
    name = "video_generation"
    description = "Generate video clips using ComfyUI or Wan2GP backends"
    
    def _run(self, prompt: str, characters: list, style: str, duration: float):
        """Execute video generation workflow"""
        try:
            # Check VRAM availability
            if not self._check_resources():
                return self._handle_error("Insufficient VRAM for video generation")
            
            # Select appropriate backend
            backend = self._select_backend(prompt, characters, style)
            
            # Execute generation
            if backend == "comfyui":
                result = self._generate_with_comfyui(prompt, characters, style, duration)
            else:
                result = self._generate_with_wan2gp(prompt, characters, style, duration)
            
            return {"success": True, "video_path": result["output_path"]}
            
        except Exception as e:
            return self._handle_error(e)
    
    def _select_backend(self, prompt, characters, style):
        """Choose optimal backend based on requirements"""
        if characters or style:
            return "comfyui"  # Complex workflows need ComfyUI
        else:
            return "wan2gp"   # Simple prompts can use Wan2GP
```

### Character Management Tool
```python
class CharacterManagementTool(BlenderAgentTool):
    name = "character_management"
    description = "Create and manage character assets including LoRA training"
    
    def _run(self, action: str, character_name: str, reference_images: list = None):
        """Manage character assets"""
        try:
            if action == "create":
                return self._create_character(character_name, reference_images)
            elif action == "train_lora":
                return self._train_character_lora(character_name)
            elif action == "update":
                return self._update_character(character_name, reference_images)
            
        except Exception as e:
            return self._handle_error(e)
    
    def _train_character_lora(self, character_name):
        """Train character-specific LoRA model"""
        # Implementation for LoRA training pipeline
        pass
```

## Crew Orchestration

### Film Production Crew
```python
class FilmProductionCrew:
    """Main crew orchestration for complete film production"""
    
    def __init__(self, addon_context):
        self.addon_context = addon_context
        
        # Initialize all agents
        self.producer = ProducerAgent(addon_context)
        self.screenwriter = ScreenwriterAgent(addon_context)
        self.casting_director = CastingDirectorAgent(addon_context)
        self.art_director = ArtDirectorAgent(addon_context)
        self.cinematographer = CinematographerAgent(addon_context)
        self.sound_designer = SoundDesignerAgent(addon_context)
        self.editor = EditorAgent(addon_context)
        
        # Create crew
        self.crew = Crew(
            agents=[
                self.producer.agent,
                self.screenwriter.agent,
                self.casting_director.agent,
                self.art_director.agent,
                self.cinematographer.agent,
                self.sound_designer.agent,
                self.editor.agent
            ],
            process=Process.hierarchical,
            manager_agent=self.producer.agent,
            verbose=True
        )
    
    def produce_film(self, concept):
        """Execute complete film production pipeline"""
        tasks = [
            Task(
                description="Develop screenplay from concept",
                expected_output="Complete screenplay with breakdowns",
                agent=self.screenwriter.agent
            ),
            Task(
                description="Create character assets",
                expected_output="Character definitions and models",
                agent=self.casting_director.agent
            ),
            Task(
                description="Generate video sequences",
                expected_output="All shot videos with metadata",
                agent=self.cinematographer.agent
            ),
            Task(
                description="Generate audio tracks",
                expected_output="Audio files for all scenes",
                agent=self.sound_designer.agent
            ),
            Task(
                description="Assemble final film",
                expected_output="Complete film assembled in Blender VSE",
                agent=self.editor.agent
            )
        ]
        
        return self.crew.kickoff(tasks=tasks)
```

## Blender Integration Patterns

### Async Execution
```python
import asyncio
import bpy
from bpy.app.handlers import persistent

class AsyncAgentExecutor:
    """Execute agent tasks without blocking Blender UI"""
    
    @staticmethod
    def run_agent_task(agent_task, callback=None):
        """Run agent task in background"""
        def execute():
            try:
                result = agent_task.execute()
                if callback:
                    bpy.app.timers.register(lambda: callback(result))
            except Exception as e:
                if callback:
                    bpy.app.timers.register(lambda: callback({"error": str(e)}))
        
        # Run in thread to avoid blocking UI
        import threading
        thread = threading.Thread(target=execute)
        thread.daemon = True
        thread.start()
```

## Success Criteria
- [ ] All film crew agents implemented using CrewAI
- [ ] Agents coordinate effectively for complete workflows
- [ ] Integration with Blender addon architecture works smoothly
- [ ] Backend connections (ComfyUI, Wan2GP, LiteLLM) function correctly
- [ ] Resource management prevents VRAM issues
- [ ] Error handling provides clear user feedback
- [ ] Async execution keeps Blender UI responsive

## Related Tasks
- `connect-generative-backends.md` - Backend API integration
- `implement-vram-budgeting.md` - Resource management
- `design-ui-panels.md` - User interface integration

## Dependencies
- `crewai-integration-checklist` checklist
- `crewai-agent-template` template
- `crewai-blender-bridge` utils