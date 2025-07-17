# Story: Three-Act Structure Support

**Story ID**: STORY-057  
**Epic**: EPIC-004-production-canvas  
**Type**: Feature  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description

As a filmmaker, I want automatic three-act structure support that positions my scenes and shots according to classic narrative timing so that my story follows established dramatic structure without manual calculation.

## Acceptance Criteria

### Three-Act Structure Implementation
- [ ] **Automatic act sizing** with 25%-50%-25% duration distribution
- [ ] **Visual act containers** with color coding (Act 1: blue, Act 2: orange, Act 3: green)
- [ ] **Act boundary validation** preventing scenes from crossing act boundaries
- [ ] **Act progression indicators** showing story momentum
- [ ] **Act-based scene positioning** with automatic timeline alignment

### Visual Timeline Integration
- [ ] **Horizontal timeline** showing act boundaries at 25% and 75% marks
- [ ] **Scene positioning** based on narrative timing
- [ ] **Visual act separators** with clear boundary indicators
- [ ] **Act labels** with duration percentages
- [ ] **Progress tracking** showing completion by act

### Smart Positioning System
- [ ] **Automatic scene placement** based on story percentage
- [ ] **Snap-to-act-boundary** functionality
- [ ] **Collision detection** preventing scene overlap
- [ ] **Dynamic resizing** when acts are adjusted
- [ ] **Position validation** ensuring logical story flow

### Three-Act Templates
- [ ] **Pre-configured three-act template** for new projects
- [ ] **Automatic scene suggestions** for each act
- [ ] **Act-specific guidelines** and tooltips
- [ ] **Story arc visualization** showing dramatic tension
- [ ] **Act completion indicators**

## Implementation Notes

### Technical Architecture
```typescript
// Three-act structure configuration
interface ThreeActStructure {
  act1: {
    start: 0,
    end: 25,
    color: '#3B82F6',
    label: 'Setup',
    scenes: Scene[]
  };
  act2: {
    start: 25,
    end: 75,
    color: '#F59E0B',
    label: 'Confrontation',
    scenes: Scene[]
  };
  act3: {
    start: 75,
    end: 100,
    color: '#10B981',
    label: 'Resolution',
    scenes: Scene[]
  };
}

// Act positioning service
class ThreeActPositioningService {
  calculateScenePosition(scene: Scene, act: Act): Position {
    const actDuration = act.end - act.start;
    const scenePercent = scene.duration / actDuration;
    
    return {
      x: act.start + (scenePercent * actDuration),
      y: this.calculateVerticalPosition(scene)
    };
  }

  validateActBoundaries(scenes: Scene[]): ValidationResult {
    const act1Scenes = scenes.filter(s => s.position.x <= 25);
    const act2Scenes = scenes.filter(s => s.position.x > 25 && s.position.x <= 75);
    const act3Scenes = scenes.filter(s => s.position.x > 75);

    return {
      isValid: this.checkActBalance(act1Scenes, act2Scenes, act3Scenes),
      warnings: this.generateWarnings(scenes),
      suggestions: this.generateSuggestions(scenes)
    };
  }
}
```

### Visual Timeline Component
```svelte
<!-- ThreeActTimeline component -->
<script lang="ts">
  import { Node } from '@xyflow/svelte';
  export let structure: ThreeActStructure;
  export let scenes: Scene[];
  
  let timelineWidth = 800;
  let actBoundaries = [25, 75];
</script>

<Node class="three-act-timeline" width={timelineWidth} height={120}>
  <!-- Act 1 -->
  <rect x="0" y="0" width={timelineWidth * 0.25} height="100" 
        fill="#3B82F6" opacity="0.2" />
  <text x="{timelineWidth * 0.125}" y="30" text-anchor="middle">Act 1: Setup (25%)</text>
  
  <!-- Act 2 -->
  <rect x="{timelineWidth * 0.25}" y="0" width={timelineWidth * 0.5} height="100" 
        fill="#F59E0B" opacity="0.2" />
  <text x="{timelineWidth * 0.5}" y="30" text-anchor="middle">Act 2: Confrontation (50%)</text>
  
  <!-- Act 3 -->
  <rect x="{timelineWidth * 0.75}" y="0" width={timelineWidth * 0.25} height="100" 
        fill="#10B981" opacity="0.2" />
  <text x="{timelineWidth * 0.875}" y="30" text-anchor="middle">Act 3: Resolution (25%)</text>
  
  <!-- Act boundaries -->
  <line x1="{timelineWidth * 0.25}" y1="0" x2="{timelineWidth * 0.25}" y2="100" 
        stroke="#6B7280" stroke-width="2" />
  <line x1="{timelineWidth * 0.75}" y1="0" x2="{timelineWidth * 0.75}" y2="100" 
        stroke="#6B7280" stroke-width="2" />
  
  <!-- Scene markers -->
  {#each scenes as scene}
    <circle cx={scene.position.x * timelineWidth / 100} cy="50" r="8" 
            fill={getActColor(scene.position.x)} />
  {/each}
</Node>
```

### Act Group Node Component
```svelte
<!-- ActGroupNode component -->
<script lang="ts">
  import { Node, Handle } from '@xyflow/svelte';
  export let data: ActGroupData;
  
  const actConfig = {
    1: { color: '#3B82F6', label: 'Setup', duration: 25 },
    2: { color: '#F59E0B', label: 'Confrontation', duration: 50 },
    3: { color: '#10B981', label: 'Resolution', duration: 25 }
  };
</script>

<Node class="act-group"
       style="--act-color: {actConfig[data.actNumber].color}"
       width={data.duration * 20} 
       height={200}>
  <div class="act-header">
    <h3>Act {data.actNumber}: {actConfig[data.actNumber].label}</h3>
    <span class="duration">{actConfig[data.actNumber].duration}%</span>
    <span class="progress">{data.completion}% complete</span>
  </div>
  
  <div class="act-progress-bar">
    <div class="progress-fill" style="width: {data.completion}%"></div>
  </div>
  
  <div class="act-content">
    <slot />
  </div>
  
  <Handle type="target" position="left" id="act-input" />
  <Handle type="source" position="right" id="act-output" />
</Node>
```

### Smart Positioning System
```typescript
class SmartPositioningEngine {
  private canvasWidth = 1200;
  private actBoundaries = [0.25, 0.75];

  positionScene(scene: Scene, scenes: Scene[]): Position {
    const act = this.determineAct(scene.storyPosition);
    const actStart = act === 1 ? 0 : act === 2 ? 0.25 : 0.75;
    const actEnd = act === 1 ? 0.25 : act === 2 ? 0.75 : 1.0;
    
    const actWidth = (actEnd - actStart) * this.canvasWidth;
    const sceneX = actStart * this.canvasWidth + 
                   (scene.storyPosition / 100) * actWidth;
    
    return {
      x: sceneX,
      y: this.calculateOptimalY(scene, scenes.filter(s => 
        this.determineAct(s.storyPosition) === act))
    };
  }

  private calculateOptimalY(scene: Scene, siblingScenes: Scene[]): number {
    // Stagger scenes vertically to prevent overlap
    const sceneIndex = siblingScenes.findIndex(s => s.id === scene.id);
    return 100 + (sceneIndex * 120);
  }

  private determineAct(position: number): 1 | 2 | 3 {
    if (position <= 25) return 1;
    if (position <= 75) return 2;
    return 3;
  }
}
```

### Three-Act Templates
```typescript
const THREE_ACT_TEMPLATES = {
  'standard': {
    act1: {
      scenes: [
        { name: 'Opening Scene', position: 10, description: 'Establish world' },
        { name: 'Inciting Incident', position: 20, description: 'Change occurs' },
        { name: 'First Turning Point', position: 25, description: 'Decision made' }
      ]
    },
    act2: {
      scenes: [
        { name: 'Rising Action', position: 35, description: 'Complications arise' },
        { name: 'Midpoint', position: 50, description: 'Major revelation' },
        { name: 'Second Turning Point', position: 65, description: 'Crisis deepens' }
      ]
    },
    act3: {
      scenes: [
        { name: 'Climax Preparation', position: 80, description: 'Final setup' },
        { name: 'Climax', position: 90, description: 'Peak conflict' },
        { name: 'Resolution', position: 100, description: 'Conclusion' }
      ]
    }
  }
};
```

### Validation System
```typescript
class ThreeActValidator {
  validateStructure(scenes: Scene[]): ValidationResult {
    const act1Scenes = scenes.filter(s => s.position <= 25);
    const act2Scenes = scenes.filter(s => s.position > 25 && s.position <= 75);
    const act3Scenes = scenes.filter(s => s.position > 75);

    return {
      isValid: act1Scenes.length > 0 && act2Scenes.length > 0 && act3Scenes.length > 0,
      actBalance: {
        act1: act1Scenes.length,
        act2: act2Scenes.length,
        act3: act3Scenes.length
      },
      warnings: this.generateWarnings(scenes),
      suggestions: this.generateSuggestions(scenes)
    };
  }

  private generateWarnings(scenes: Scene[]): string[] {
    const warnings = [];
    
    const act1Scenes = scenes.filter(s => s.position <= 25);
    const act2Scenes = scenes.filter(s => s.position > 25 && s.position <= 75);
    
    if (act1Scenes.length > 5) {
      warnings.push('Act 1 may be too crowded');
    }
    
    if (act2Scenes.length < 3) {
      warnings.push('Act 2 may lack sufficient development');
    }
    
    return warnings;
  }
}
```

### Testing Requirements

#### Unit Tests
- [ ] Act sizing calculations (25%-50%-25%)
- [ ] Scene positioning within act boundaries
- [ ] Collision detection and resolution
- [ ] Validation rules for act balance
- [ ] Template application accuracy

#### Integration Tests
- [ ] Timeline visualization accuracy
- [ ] Smart positioning system effectiveness
- [ ] Act boundary enforcement
- [ ] Template-based story creation
- [ ] Real-time validation feedback

#### E2E Tests
- [ ] Complete three-act story creation workflow
- [ ] Scene positioning accuracy
- [ ] Act boundary validation
- [ ] Template application and customization
- [ ] Story completion indicators

### Dependencies
- **STORY-055**: Story Structure Node Types (for act containers)
- **STORY-056**: Asset Node Integration (for scene asset connections)
- **EPIC-001**: Project structure for story persistence

### Definition of Done
- [ ] Three-act structure visual representation complete
- [ ] Automatic scene positioning working correctly
- [ ] Act boundary validation functional
- [ ] Timeline visualization accurate
- [ ] Templates for three-act structure available
- [ ] Validation system providing useful feedback
- [ ] Documentation with examples provided
- [ ] Ready for STORY-058 (Seven-Point Method) implementation