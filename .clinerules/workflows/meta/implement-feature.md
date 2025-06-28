# Complete Feature Development Cycle

Orchestrates the full BMAD methodology for implementing a complete feature in the Blender Movie Director addon.

$ARGUMENTS: feature_name, priority (high/medium/low), target_sprint

## Task
Execute the complete BMAD feature development lifecycle from requirements definition through validation and deployment. This meta-command ensures proper methodology adherence across all development phases.

## BMAD Methodology Application
This command implements the full BMAD workflow using our established film crew personas and templates from .bmad-core/:

1. **Requirements Phase** - Business Analyst persona
2. **Epic Definition** - Product Owner persona  
3. **Story Breakdown** - Development Lead persona
4. **Implementation** - Developer persona with agent-specific templates
5. **Validation** - QA Engineer persona with comprehensive testing
6. **Status Tracking** - Project Manager persona

## Execution Flow
The AI developer (Cline) orchestrates the development process by assuming the defined personas for each stage of the BMAD methodology.

1.  **Requirements Analysis (Business Analyst):**
    -   Receive and analyze the Product Requirements Document (PRD) for the given feature.
    -   Clarify any ambiguities with the project stakeholders.

2.  **Epic Definition (Product Owner):**
    -   Based on the PRD, define a structured Epic that outlines the feature's scope, goals, and acceptance criteria.

3.  **Story Breakdown (Development Lead):**
    -   Break the Epic down into smaller, manageable user stories.
    -   Each story will have a clear goal and definition of done.

4.  **Iterative Implementation & Validation (Developer & QA Engineer):**
    -   For each story, the AI developer will:
        -   Implement the required code changes, adhering to project standards.
        -   Run relevant tests using `make test` or `make test-quick`.
        -   Perform validation to ensure the implementation meets the story's requirements.

5.  **Final Integration Validation (QA Engineer):**
    -   After all stories are implemented, perform a full integration test of the addon.
    -   This may involve using `make run` for manual testing in Blender and `make test` for automated checks.

6.  **Status Update (Project Manager):**
    -   Provide a final report on the feature's implementation, including test results and any relevant notes.

## Integration with BMAD Structure
- Uses personas from `.bmad-core/personas/`
- References templates from `.bmad-core/templates/`
- Follows checklists from `.bmad-core/checklists/`
- Maintains film crew agent metaphor throughout development
- Ensures addon structure consistency with `blender_movie_director/` architecture

## Expected Outcomes
- Complete feature implementation following BMAD methodology
- Proper Blender addon integration with bpy patterns
- Agent integration with CrewAI framework
- Full test coverage and validation
- Updated project documentation and status
