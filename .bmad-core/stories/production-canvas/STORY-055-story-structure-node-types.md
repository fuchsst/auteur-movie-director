# Story: Story Structure Node Types

**Story ID**: STORY-055  
**Epic**: EPIC-004-production-canvas  
**Type**: Feature  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description

As a filmmaker, I want story-aware node types that automatically understand narrative structure so that I can build visual workflows that follow established storytelling patterns without needing to understand the underlying technical complexity.

## Acceptance Criteria

### Story Structure Node Types
- [ ] **ActGroupNode**: Container for three-act structure with visual indicators
  - Color-coded acts (Setup: blue, Confrontation: orange, Resolution: green)
  - Automatic sizing based on act duration (25%-50%-25%)
  - Contains SceneGroupNodes hierarchically
  - Visual timeline indicator showing act progression

- [ ] **SceneGroupNode**: Hierarchical story chapter containers
  - Nesting support for chapter/scene/shot hierarchy
  - Breadcrumb navigation support
  - Expandable/collapsible structure
  - Visual connection to parent story elements

- [ ] **PlotPointNode**: Seven-Point Structure markers
  - Hook, Plot Point 1, Pinch Point 1, Midpoint, Pinch Point 2, Plot Point 3, Resolution
  - Positioned automatically at narrative turning points
  - Visual indicators for story momentum
  - Validation rules for story flow completeness

- [ ] **BeatNode**: Blake Snyder emotional beats
  - Color-coded emotional intensity levels
  - Beat type identification (Opening Image, Theme Stated, etc.)
  - Emotional arc visualization
  - Story pacing indicators

### Visual Design Standards
- [ ] Consistent styling across all story structure nodes
- [ ] Clear visual hierarchy indicating narrative importance
- [ ] Progress indicators showing story completion
- [ ] Interactive tooltips with story guidance
- [ ] Responsive sizing based on content

### Story Validation System
- [ ] Automatic validation of story structure completeness
- [ ] Warning indicators for missing story elements
- [ ] Suggestions for story improvement based on structure gaps
- [ ] Real-time feedback during node placement

### Integration Points
- [ ] Connect to project.json narrative structure
- [ ] Sync with story breakdown from EPIC-001
- [ ] Validate against established storytelling patterns
- [ ] Export story structure to creative documents

## Implementation Notes

### Technical Architecture
```typescript
// Story structure node types
enum StoryNodeType {
  ACT_GROUP = 'story-act-group',
  SCENE_GROUP = 'story-scene-group',
  PLOT_POINT = 'story-plot-point',
  BEAT = 'story-beat'
}

// Story structure validation
interface StoryValidation {
  structure: 'three-act' | 'seven-point' | 'blake-snyder';
  completeness: number; // 0-100%
  warnings: string[];
  suggestions: string[];
}

// Act group node data
interface ActGroupNodeData {
  actNumber: 1 | 2 | 3;
  durationPercent: number;
  color: string;
  scenes: SceneGroupNodeData[];
  validation: StoryValidation;
}

// Plot point node data
interface PlotPointNodeData {
  pointType: 'hook' | 'plot-point-1' | 'pinch-1' | 'midpoint' | 'pinch-2' | 'plot-point-3' | 'resolution';
  position: number; // 0-100% through story
  emotionalIntensity: number; // 1-10
  description: string;
}

// Beat node data
interface BeatNodeData {
  beatType: string; // Blake Snyder beat types
  emotionalState: 'positive' | 'negative' | 'neutral';
  intensity: number; // 1-10
  timing: number; // 0-100% through story
}
```

### Visual Components
```svelte
<!-- ActGroupNode component -->
<script lang="ts">
  import { Node } from '@xyflow/svelte';
  export let data: ActGroupNodeData;
</script>

<Node class="act-group" style="--act-color: {data.color}">
  <div class="act-header">
    <h3>Act {data.actNumber}</h3>
    <span class="duration">{data.durationPercent}%</span>
  </div>
  <div class="act-progress" style="width: {data.validation.completeness}%"></div>
  <div class="act-content">
    <slot />
  </div>
</Node>

<!-- PlotPointNode component -->
<script lang="ts">
  import { Node } from '@xyflow/svelte';
  export let data: PlotPointNodeData;
</script>

<Node class="plot-point" data-type={data.pointType}>
  <div class="point-indicator" 
       style="--intensity: {data.emotionalIntensity}">
    {data.pointType}
  </div>
  <div class="point-description">{data.description}</div>
  <div class="position-marker">{data.position}%</div>
</Node>
```

### Story Validation Engine
```typescript
class StoryValidator {
  validateThreeActStructure(nodes: StoryNode[]): ValidationResult {
    const acts = nodes.filter(n => n.type === 'story-act-group');
    const scenes = nodes.filter(n => n.type === 'story-scene-group');
    
    return {
      isValid: this.checkActBalance(acts),
      warnings: this.generateWarnings(acts, scenes),
      suggestions: this.generateSuggestions(acts, scenes)
    };
  }

  validateSevenPointStructure(nodes: StoryNode[]): ValidationResult {
    const plotPoints = nodes.filter(n => n.type === 'story-plot-point');
    return this.validatePlotPointSequence(plotPoints);
  }

  validateBlakeSnyderBeats(nodes: StoryNode[]): ValidationResult {
    const beats = nodes.filter(n => n.type === 'story-beat');
    return this.validateBeatArc(beats);
  }
}
```

### Story Templates
```typescript
const STORY_TEMPLATES = {
  'three-act': {
    acts: [
      { act: 1, duration: 25, color: '#3B82F6' },
      { act: 2, duration: 50, color: '#F59E0B' },
      { act: 3, duration: 25, color: '#10B981' }
    ],
    defaultScenes: ['Setup', 'Inciting Incident', 'First Turning Point']
  },
  'seven-point': {
    plotPoints: [
      { type: 'hook', position: 0, intensity: 7 },
      { type: 'plot-point-1', position: 25, intensity: 8 },
      { type: 'pinch-1', position: 37, intensity: 6 },
      { type: 'midpoint', position: 50, intensity: 9 },
      { type: 'pinch-2', position: 62, intensity: 7 },
      { type: 'plot-point-3', position: 75, intensity: 9 },
      { type: 'resolution', position: 100, intensity: 10 }
    ]
  }
};
```

### Testing Requirements

#### Unit Tests
- [ ] Story node creation and validation
- [ ] Story structure completeness checking
- [ ] Visual styling consistency
- [ ] Template application accuracy

#### Integration Tests
- [ ] Story structure synchronization with project.json
- [ ] Validation engine with real story data
- [ ] Node hierarchy integrity
- [ ] Visual feedback responsiveness

#### E2E Tests
- [ ] Complete story structure workflow
- [ ] Template-based story creation
- [ ] Real-time validation feedback
- [ ] Story export functionality

### Dependencies
- **STORY-054**: Node System Architecture (must be completed first)
- **EPIC-001**: Project structure for story data persistence
- **EPIC-002**: Asset system for story element integration

### Definition of Done
- [ ] All story structure node types implemented
- [ ] Visual styling consistent across all nodes
- [ ] Story validation system working correctly
- [ ] Integration with project.json completed
- [ ] Templates for common story structures available
- [ ] Documentation with usage examples provided
- [ ] Ready for STORY-057 (Three-Act Structure Support) implementation