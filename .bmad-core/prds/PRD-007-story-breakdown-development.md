# Product Requirements Document: Story Breakdown and Development

## Executive Summary

The Story Breakdown and Development feature transforms abstract creative concepts into structured, executable film production plans through an AI-powered hierarchical workflow. This system bridges the gap between high-level artistic vision and granular technical requirements, enabling filmmakers to rapidly develop coherent narratives that can be directly translated into generative media production.

By integrating proven storytelling frameworks (Three-Act Structure, Seven-Point Story Structure, Blake Snyder Beat Sheet) with specialized AI agents, the feature provides a guided, iterative process that maintains creative intent while generating production-ready shot lists. This dramatically reduces the time from concept to production while ensuring narrative coherence and professional story structure.

### Target User Personas
- **Independent Filmmakers**: Need rapid story development with limited resources
- **Content Creators**: Require consistent narrative structure across episodic content
- **Creative Directors**: Want to explore multiple narrative variations quickly
- **AI Artists**: Seek structured prompts for coherent generative sequences

### Expected Impact
- **80% reduction** in story development time from concept to shot list
- **Elimination of narrative drift** in AI-generated content
- **Professional story structure** accessible to non-screenwriters
- **Seamless integration** from story to visual production

## Problem Statement

### Current Limitations in Generative Film Production

1. **The Translation Gap**: Converting abstract creative ideas into machine-executable instructions results in:
   - Loss of narrative coherence across generated content
   - Inconsistent character arcs and motivations
   - Lack of dramatic structure in AI-generated sequences

2. **Manual Workflow Inefficiencies**:
   - Hours spent manually breaking down scripts into shots
   - No standardized process for narrative-to-visual translation
   - Difficulty maintaining consistency across team collaborations

3. **AI Generation Challenges**:
   - LLMs produce unfocused narratives without structural guidance
   - Generated content lacks emotional pacing and dramatic tension
   - No connection between story intent and visual execution

### Pain Points in Existing Workflows

- **For Filmmakers**: Manual script breakdowns are time-consuming and error-prone
- **For AI Artists**: Lack of narrative context produces disconnected visuals
- **For Teams**: No shared framework for story structure and progression
- **For Productions**: Inconsistent quality due to unstructured generation

## Solution Overview

### Hierarchical Story Breakdown System

The solution implements a multi-tiered narrative framework that progressively refines creative concepts through specialized AI agent crews, with explicit integration of proven storytelling structures:

1. **Concept Development** (Writers' Room)
   - Interactive chat interface for initial brainstorming
   - AI-assisted logline generation and world-building
   - Story structure template selection (Three-Act, Five-Act, Hero's Journey, Save the Cat)
   - Human-in-the-loop approval at each stage

2. **Structural Mapping** (Three-Act Framework)
   - Automatic plot structure generation with act percentages:
     - Act I (Setup): 25% of story
     - Act II (Confrontation): 50% of story
     - Act III (Resolution): 25% of story
   - Chapter-based organization aligned with dramatic acts
   - Visual representation in Production Canvas with color coding
   - Act metadata files capturing purpose and emotional arc

3. **Scene Definition** (Seven-Point Structure)
   - Plot-driven scene breakdown mapped to seven key points:
     - Hook (starting point)
     - Plot Point 1 (call to adventure)
     - Pinch Point 1 (first pressure)
     - Midpoint (protagonist becomes proactive)
     - Pinch Point 2 (second pressure)
     - Plot Point 2 (final piece needed)
     - Resolution (climax and denouement)
   - Functional purpose for every narrative beat
   - Integration with asset management system
   - Chapter metadata tracking plot point functions

4. **Shot Generation** (Blake Snyder Beat Sheet Integration)
   - Detailed shot lists with emotional beats:
     - Opening Image
     - Theme Stated
     - Setup
     - Catalyst
     - Debate
     - Break into Two
     - B Story
     - Fun and Games
     - Midpoint
     - Bad Guys Close In
     - All Is Lost
     - Dark Night of the Soul
     - Break into Three
     - Finale
     - Final Image
   - Camera and lighting specs informed by emotional intensity
   - Character and location consistency through asset references
   - Direct integration with generative nodes

### Integration with BMAD Agent Framework

The feature leverages four specialized agent crews:

1. **Concept Crew**: Story Analyst, Logline Writer, World Builder
2. **Structuralist Crew**: Plot Architect, Chapter Decomposer
3. **Scene-wright Crew**: Plot Point Specialist, Beat Sheet Writer
4. **Cinematographer Crew**: Script Parser, Character Prompter, Shot Designer

Each crew operates within the CrewAI framework, ensuring structured collaboration and predictable outputs.

## User Stories & Acceptance Criteria

### Story 1: Initial Concept Development
**As a** filmmaker  
**I want to** input my raw story idea and receive structured narrative options  
**So that** I can quickly develop a coherent story foundation

**Acceptance Criteria**:
- [ ] Chat interface accepts text input and file uploads
- [ ] System generates 3-5 logline options within 30 seconds
- [ ] User can select preferred logline with single click
- [ ] Approved concept saves to project structure

### Story 2: Automatic Plot Structure
**As a** content creator  
**I want to** see my story mapped to proven dramatic structures  
**So that** my narrative follows professional storytelling principles

**Acceptance Criteria**:
- [ ] One-click generation of Three-Act breakdown
- [ ] Visual representation of story structure in UI
- [ ] Editable chapter summaries in Markdown format
- [ ] Automatic save to Git repository

### Story 3: Scene-Level Breakdown
**As a** director  
**I want to** break chapters into specific scenes with clear purposes  
**So that** every moment serves the overall narrative

**Acceptance Criteria**:
- [ ] Context-aware scene generation based on chapter
- [ ] Each scene mapped to Seven-Point Structure element
- [ ] Beat sheets include emotional arcs and character actions
- [ ] Scenes link to relevant Character/Location assets

### Story 4: Shot List Generation
**As an** AI artist  
**I want to** receive detailed shot prompts from scene descriptions  
**So that** I can generate visually consistent content

**Acceptance Criteria**:
- [ ] Automatic shot list from approved beat sheets
- [ ] Structured prompts with camera, lighting, and mood specs
- [ ] Character/Style asset references included
- [ ] Direct population of generative node parameters

### Story 5: Collaborative Editing
**As a** creative team  
**I want to** edit and refine AI-generated story elements  
**So that** we maintain creative control while leveraging automation

**Acceptance Criteria**:
- [ ] All outputs editable in UI before progression
- [ ] Changes reflected in both human and machine artifacts
- [ ] Version history tracked in Git
- [ ] Real-time sync across team members

## Technical Requirements

### Frontend Requirements

1. **Writers' Room Interface**:
   - Chat-based UI component in top panel
   - File upload support (.txt, .md, .pdf)
   - Real-time streaming of agent responses
   - Markdown rendering for structured outputs
   - Story structure template gallery with visual previews
   - Interactive story arc visualization during development

2. **Enhanced Story Navigation**:
   - **Project Browser** with narrative structure:
     - 🎭 Act indicators with percentages (Act I: 25%, Act II: 50%, Act III: 25%)
     - 🎯 Plot point markers (Hook, PP1, Pinch 1, Midpoint, Pinch 2, PP2, Resolution)
     - 🎬 Scene nodes with Blake Snyder beat labels
     - Color coding: Setup (blue), Confrontation (orange), Resolution (green)
     - Progress bars per narrative element
   - **Breadcrumb Navigation**: Act I > Chapter 2 > Scene 3
   - **Story Timeline**: Bottom panel showing emotional arc
   - **Structure Validation**: Red indicators for missing elements

3. **Canvas Integration**:
   - **Story-Aware Node Types**:
     - ActGroupNodes with percentage sizing
     - PlotPointNodes as narrative markers
     - BeatNodes showing emotional function
     - SceneGroupNodes auto-generated from chapters
   - **Automatic Layout**:
     - Left-to-right narrative flow
     - Vertical grouping by dramatic function
     - Visual spacing reflects story pacing
   - **Smart Constraints**:
     - Enforce narrative sequence rules
     - Prevent invalid connections across acts
     - Maintain structural integrity

4. **Properties Inspector Enhancements**:
   - **Story Context Display**:
     - Current position in narrative structure
     - Act/Chapter/Scene/Beat information
     - Narrative function explanation
     - Suggested pacing and duration
   - **Structure Examples**:
     - Famous film examples for current beat
     - Common patterns for plot points
     - Genre-specific variations
   - **Validation Warnings**:
     - Pacing deviations from target
     - Missing structural elements
     - Continuity issues

### Backend Requirements

1. **Agent Orchestration**:
   - CrewAI integration for multi-agent collaboration
   - Sequential process execution for crews
   - Context chain management across hierarchies
   - Error handling and retry mechanisms

2. **Data Management**:
   - Dual artifact system (Markdown + JSON)
   - Hierarchical storage in `02_Source_Creative/story/`:
     ```
     story/
     ├── project_meta.json         # Story framework selection
     ├── concept.md               # Logline and theme
     ├── outline.md               # Full narrative structure
     ├── act_1_setup/
     │   ├── act_meta.json       # Act purpose, plot points
     │   ├── chapter_01_hook/
     │   │   ├── chapter_meta.json   # Seven-point mapping
     │   │   └── scene_01_opening_image/
     │   │       ├── scene_meta.json  # Beat information
     │   │       ├── beat_sheet.md
     │   │       └── shot_001/
     │   │           └── prompt.json
     ├── act_2_confrontation/
     └── act_3_resolution/
     ```
   - Metadata files at each level tracking narrative structure
   - Project.json schema extensions for story data
   - Git commit hooks for change tracking

3. **API Endpoints**:
   ```
   POST /api/v1/story/concept
   POST /api/v1/story/outline/{project_id}
   POST /api/v1/story/scenes/{chapter_id}
   POST /api/v1/story/shots/{scene_id}
   GET  /api/v1/story/status/{job_id}
   ```

4. **LLM Integration**:
   - LiteLLM for model abstraction
   - Streaming response support
   - Token usage tracking per project
   - Fallback to alternative models

### Performance Requirements

- **Response Times**:
  - Concept generation: < 30 seconds
  - Outline creation: < 45 seconds
  - Scene breakdown: < 20 seconds per chapter
  - Shot generation: < 15 seconds per scene

- **Scalability**:
  - Support 100+ concurrent story sessions
  - Handle scripts up to 120 pages
  - Process 500+ shots per project
  - Maintain sub-second UI responsiveness

### Integration Requirements

1. **Asset Management (PRD-002)**:
   - Automatic Character asset creation from script
   - Location extraction and linking
   - Style inference from genre/tone
   - Bidirectional asset-story references

2. **Production Canvas (PRD-004)**:
   - Story structure maps to canvas hierarchy
   - Shot prompts populate node parameters
   - Scene transitions as node connections
   - Takes system for narrative variations

3. **Video Assembly (PRD-005)**:
   - Story timing informs shot sequencing
   - Script annotations in EDL export
   - Chapter markers in final video
   - Narrative metadata preservation

4. **Quality Management (PRD-006)**:
   - Fast mode for story iteration
   - Standard mode for previz
   - High mode for final shots
   - Quality affects generation speed, not story

## Success Metrics

### User Adoption
- **Target**: 80% of new projects use story breakdown
- **Measurement**: Story API usage vs. total projects
- **Timeline**: Within 3 months of launch

### Quality Improvements
- **Narrative Coherence Score**: 85%+ (human evaluation)
- **Structure Compliance**: 95%+ follow three-act model
- **Asset Consistency**: 90%+ correct character/location refs
- **User Satisfaction**: 4.5+ stars on story features

### Workflow Efficiency
- **Time Savings**: 
  - Concept to outline: 10x faster than manual
  - Script to shot list: 20x faster than traditional
  - Full breakdown: < 2 hours for feature film
- **Iteration Speed**: 5+ story variations per hour
- **Collaboration**: 3x faster team alignment

### Business Impact
- **User Retention**: 25% increase for story users
- **Premium Conversions**: 40% of story users upgrade
- **Content Volume**: 300% more completed projects
- **Platform Differentiation**: Unique in market

## Risk Assessment

### Technical Risks
- **LLM Reliability**: Mitigated by fallback models and caching
- **Context Length Limits**: Chunking strategies for long scripts
- **Generation Quality**: Human-in-the-loop editing controls
- **Performance at Scale**: Queuing system and async processing

### User Adoption Risks
- **Learning Curve**: Progressive disclosure and tutorials
- **Creative Resistance**: Emphasize tool augmentation, not replacement
- **Output Quality Concerns**: Extensive editing capabilities
- **Workflow Disruption**: Optional integration, not mandatory

### Integration Risks
- **Data Model Changes**: Backward-compatible schema evolution
- **Cross-Feature Dependencies**: Modular design with clear APIs
- **Performance Impact**: Dedicated story processing queue
- **Storage Growth**: Efficient artifact compression

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
- [ ] CrewAI framework integration
- [ ] Basic Writers' Room UI
- [ ] Concept Crew implementation
- [ ] Initial data models

### Phase 2: Structure (Weeks 5-8)
- [ ] Structuralist Crew development
- [ ] Hierarchical UI navigation
- [ ] Canvas integration basics
- [ ] Markdown editing support

### Phase 3: Breakdown (Weeks 9-12)
- [ ] Scene-wright Crew completion
- [ ] Cinematographer Crew implementation
- [ ] Asset linking system
- [ ] Full workflow testing

### Phase 4: Polish (Weeks 13-16)
- [ ] Performance optimization
- [ ] Advanced editing features
- [ ] Tutorial and documentation
- [ ] Beta user feedback integration

## Appendix: Technical Specifications

### Project.json Schema Extensions

```json
{
  "story": {
    "structure": {
      "type": "three_act",
      "framework": "seven_point",
      "beat_system": "blake_snyder"
    },
    "concept": {
      "logline": "string",
      "dramatic_question": "string",
      "theme": "string",
      "protagonist": {
        "want": "string",
        "need": "string"
      },
      "world": {
        "description": "string",
        "tone": "string",
        "genre": "string"
      }
    },
    "acts": [
      {
        "id": "act_1",
        "name": "Setup",
        "type": "setup",
        "target_percentage": 25,
        "plot_points": ["hook", "plot_point_1"],
        "emotional_arc": "comfort_to_disruption",
        "chapters": [
          {
            "id": "uuid",
            "title": "string",
            "number": 1,
            "plot_point": "hook",
            "seven_point_function": "starting_point",
            "beats": ["opening_image", "theme_stated", "setup"],
            "scenes": [
              {
                "id": "uuid",
                "title": "string",
                "number": 1,
                "beat": "opening_image",
                "emotional_state": "ordinary_world",
                "conflict_level": 0,
                "tension": 3,
                "mood": "mysterious",
                "duration_estimate": "2:30",
                "beat_sheet": {
                  "location": "string",
                  "characters": ["uuid"],
                  "actions": ["string"],
                  "emotional_shift": "string"
                },
                "shots": [
                  {
                    "shot_number": "integer",
                    "marks_chapter_start": "boolean",
                    "marks_act_transition": "boolean",
                    "is_plot_point": "boolean",
                    "story_context": {
                      "act_name": "string",
                      "act_type": "string",
                      "act_number": "integer",
                      "chapter_title": "string",
                      "plot_point": "string",
                      "scene_title": "string",
                      "emotional_beat": "string",
                      "seven_point_function": "string",
                      "mood": "string",
                      "tension_level": "integer"
                    },
                    "character_prompt": "string",
                    "character_asset_ref": "uuid",
                    "action_description": "string",
                    "shot_type": "string",
                    "camera_angle": "string",
                    "movement": "string",
                    "lens": "string",
                    "lighting": "string",
                    "environment_prompt": "string",
                    "style_asset_ref": "uuid"
                  }
                ]
              }
            ]
          }
        ]
      }
    ],
    "narrative_arc": {
      "emotional_curve": ["comfort", "disruption", "struggle", "revelation", "resolution"],
      "tension_points": [0, 3, 5, 8, 10, 7, 9, 5, 2],
      "pacing_rhythm": ["slow", "medium", "fast", "intense", "reflective", "climactic", "peaceful"]
    }
  }
}
```

### Story Structure Templates

Pre-configured templates for common narrative frameworks:

```yaml
three_act_standard:
  name: "Classic Three-Act Structure"
  acts:
    - name: "Setup"
      percentage: 25
      chapters: 2
      plot_points: ["hook", "inciting_incident", "plot_point_1"]
    - name: "Confrontation"
      percentage: 50
      chapters: 4
      plot_points: ["pinch_point_1", "midpoint", "pinch_point_2", "plot_point_2"]
    - name: "Resolution"
      percentage: 25
      chapters: 2
      plot_points: ["climax", "resolution"]

save_the_cat:
  name: "Blake Snyder's Save the Cat"
  beats:
    - {beat: "opening_image", position: 0, duration: 1}
    - {beat: "theme_stated", position: 5, duration: 1}
    - {beat: "setup", position: 1, duration: 9}
    - {beat: "catalyst", position: 10, duration: 2}
    - {beat: "debate", position: 12, duration: 13}
    - {beat: "break_into_two", position: 25, duration: 1}
    - {beat: "b_story", position: 30, duration: 5}
    - {beat: "fun_and_games", position: 30, duration: 20}
    - {beat: "midpoint", position: 50, duration: 1}
    - {beat: "bad_guys_close_in", position: 55, duration: 20}
    - {beat: "all_is_lost", position: 75, duration: 1}
    - {beat: "dark_night_of_soul", position: 75, duration: 10}
    - {beat: "break_into_three", position: 85, duration: 1}
    - {beat: "finale", position: 85, duration: 20}
    - {beat: "final_image", position: 99, duration: 1}
```

### Story Validation Rules

Automated validation ensures narrative coherence:

```javascript
const storyValidationRules = {
  structure: {
    acts: {
      required: true,
      minCount: 3,
      percentageSum: 100,
      proportions: {
        setup: { min: 20, max: 30 },
        confrontation: { min: 40, max: 60 },
        resolution: { min: 15, max: 30 }
      }
    },
    plotPoints: {
      required: ["hook", "plot_point_1", "midpoint", "plot_point_2", "climax"],
      sequence: ["hook", "plot_point_1", "pinch_point_1", "midpoint", "pinch_point_2", "plot_point_2", "climax"]
    },
    beats: {
      opening: ["opening_image", "theme_stated"],
      closing: ["finale", "final_image"],
      emotional: {
        "all_is_lost": { tensionMin: 8 },
        "dark_night": { moodRequired: ["despair", "hopeless", "lost"] }
      }
    }
  },
  pacing: {
    sceneDuration: { min: "0:30", max: "5:00", average: "2:30" },
    chapterBalance: { maxDeviation: 20 }, // percentage
    tensionCurve: {
      startPoint: { max: 3 },
      midpoint: { min: 5, max: 8 },
      climax: { min: 9 },
      resolution: { max: 5 }
    }
  },
  continuity: {
    characterPresence: "consistent_across_scenes",
    locationTransitions: "logical_geography",
    timeProgression: "forward_or_explained",
    assetUsage: "defined_before_use"
  }
};
```

### Agent Configuration Samples

```yaml
# agents.yaml
story_analyst:
  role: "Literary and Narrative Analyst"
  goal: "Extract core narrative components from user input"
  backstory: "PhD in Comparative Literature with expertise in narrative structure"
  tools: ["text_analysis", "theme_extraction", "structure_validation"]
  
plot_architect:
  role: "Master Screenwriter & Structuralist"
  goal: "Map story concepts onto proven dramatic structures"
  backstory: "Expert in Three-Act, Seven-Point, and Blake Snyder methodologies"
  tools: ["structure_mapping", "pacing_analysis", "plot_validation"]

shot_designer:
  role: "Veteran Director of Photography"
  goal: "Translate narrative beats into cinematic shots"
  backstory: "30 years of cinematography experience across all genres"
  tools: ["shot_composition", "lighting_design", "camera_movement", "emotional_mapping"]
```

This PRD establishes Story Breakdown and Development as a cornerstone feature that transforms the platform from a technical tool into a complete creative companion for AI-assisted filmmaking, with explicit narrative frameworks visible and actionable throughout the entire creative process.