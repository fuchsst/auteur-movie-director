# Initialize BMAD Film Studio Project

Initialize a new generative film project with proper Blender addon structure following BMAD methodology.

$ARGUMENTS can include: project name, target resolution, style preferences

## Task
Set up complete BMAD project structure with Blender addon boilerplate and agent configuration. Create the foundational .blend file with the generative asset data model.

## Context
This command establishes the base architecture for a local-first generative film studio using the BMAD (Breakthrough Method of Agile AI-Driven Development) framework. It creates the necessary directory structure, initializes the Blender addon environment, and sets up the agent orchestration system.

## Implementation Steps
1. Analyze $ARGUMENTS for project configuration
2. Create addon directory structure following Python package conventions
3. Generate __init__.py files with proper Blender addon registration
4. Initialize .blend file with custom properties for the asset data model
5. Set up agent configuration files for CrewAI integration
6. Create template directories for ComfyUI and Wan2GP workflows
7. Configure backend service connections
8. Initialize project documentation

## Expected Output
- Complete blender_movie_director/ addon structure
- Initialized .blend file with BMAD project properties
- Agent configuration ready for deployment
- Backend service templates prepared
- Project ready for screenplay development