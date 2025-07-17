# Story: Seven-Point Method Implementation

**Story ID**: STORY-058  
**Epic**: EPIC-004-production-canvas  
**Type**: Feature  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description

As a filmmaker, I want visual seven-point story structure support that automatically positions key story moments at precise narrative turning points so that my story follows the classic seven-point method without manual calculation or positioning.

## Acceptance Criteria

### Seven-Point Structure Implementation
- [ ] **Plot point nodes** positioned at exact percentages: 0%, 12.5%, 25%, 37.5%, 50%, 62.5%, 75%, 87.5%, 100%
- [ ] **Visual plot point markers** with distinct styling for each point type
- [ ] **Automatic positioning** based on story percentage calculation
- [ ] **Plot point validation** ensuring complete story arc
- [ ] **Missing point indicators** showing gaps in story structure

### Seven-Point Node Types
- [ ] **Hook (0%)**: Opening grabber with high visual impact
- [ ] **Plot Point 1 (25%)**: First major turning point
- [ ] **Pinch Point 1 (37.5%)**: First pressure application
- [ ] **Midpoint (50%)**: Central revelation or shift
- [ ] **Pinch Point 2 (62.5%)**: Second pressure intensification
- [ ] **Plot Point 2 (75%)**: Second major turning point
- [ ] **Resolution (100%)**: Final resolution
- [ ] **Climax (87.5%)**: Peak conflict moment

### Visual Story Arc
- [ ] **Emotional arc visualization** showing tension progression
- [ ] **Plot point connectivity** showing story flow
- [ ] **Intensity indicators** for each plot point
- [ ] **Story momentum tracking** with visual feedback
- [ ] **Arc completion** showing story structure health

### Smart Positioning System
- [ ] **Automatic scene alignment** to nearest plot point
- [ ] **Scene clustering** around plot points
- [ ] **Visual grouping** of related story elements
- [ ] **Progressive revelation** of story complexity
- [ ] **Guided story development** with suggestions

## Implementation Notes

### Technical Architecture
```typescript
// Seven-point structure configuration
interface SevenPointStructure {
  hook: { position: 0, intensity: 9, label: 'Hook' };
  plotPoint1: { position: 25, intensity: 8, label: 'Plot Point 1' };
  pinch1: { position: 37.5, intensity: 7, label: 'Pinch 1' };
  midpoint: { position: 50, intensity: 10, label: 'Midpoint' };
  pinch2: { position: 62.5, intensity: 8, label: 'Pinch 2' };
  plotPoint2: { position: 75, intensity: 9, label: 'Plot Point 2' };
  climax: { position: 87.5, intensity: 10, label: 'Climax' };
  resolution: { position: 100, intensity: 5, label: 'Resolution' };
}

// Plot point node data
interface PlotPointNodeData {
  pointType: 'hook' | 'plot-point-1' | 'pinch-1' | 'midpoint' | 'pinch-2' | 'plot-point-2' | 'climax' | 'resolution';
  storyPosition: number; // 0-100%
  emotionalIntensity: number; // 1-10
  description: string;
  connectedScenes: Scene[];
  isComplete: boolean;
}

// Seven-point positioning service
class SevenPointPositioningService {
  calculatePlotPointPosition(pointType: string): number {
    const positions = {
      'hook': 0,
      'plot-point-1': 25,
      'pinch-1': 37.5,
      'midpoint': 50,
      'pinch-2': 62.5,
      'plot-point-2': 75,
      'climax': 87.5,
      'resolution': 100
    };
    return positions[pointType] || 0;
  }

  validateSevenPointStructure(points: PlotPointNodeData[]): ValidationResult {
    const requiredPoints = ['hook', 'plot-point-1', 'midpoint', 'plot-point-2', 'resolution'];
    const presentPoints = points.map(p => p.pointType);
    
    return {
      isComplete: requiredPoints.every(point => presentPoints.includes(point)),
      missingPoints: requiredPoints.filter(point => !presentPoints.includes(point)),
      arcProgress: this.calculateArcProgress(points),
      suggestions: this.generateSuggestions(points)
    };
  }

  private calculateArcProgress(points: PlotPointNodeData[]): number {
    // Calculate story arc health based on point placement and intensity
    return Math.round((points.length / 8) * 100);
  }
}
```

### Plot Point Node Component
```svelte
<!-- PlotPointNode component -->
<script lang="ts">
  import { Node, Handle } from '@xyflow/svelte';
  export let data: PlotPointNodeData;
  
  const pointConfig = {
    'hook': { color: '#EF4444', icon: '🎯' },
    'plot-point-1': { color: '#F59E0B', icon: '🔄' },
    'pinch-1': { color: '#8B5CF6', icon: '🔥' },
    'midpoint': { color: '#10B981', icon: '⚡' },
    'pinch-2': { color: '#8B5CF6', icon: '💥' },
    'plot-point-2': { color: '#F59E0B', icon: '🎭' },
    'climax': { color: '#EF4444', icon: '🌟' },
    'resolution': { color: '#3B82F6', icon: '🏁' }
  };
</script>

<Node class="plot-point" 
       style="--point-color: {pointConfig[data.pointType].color}"
       position={{ x: data.storyPosition * 12, y: 200 - (data.emotionalIntensity * 15) }}>
  <div class="point-header">
    <span class="point-icon">{pointConfig[data.pointType].icon}</span>
    <h4>{data.label}</h4>
    <span class="position">{data.storyPosition}%</span>
  </div>
  
  <div class="point-intensity">
    <div class="intensity-bar">
      <div class="intensity-fill" style="width: {data.emotionalIntensity * 10}%"></div>
    </div>
    <span>Intensity: {data.emotionalIntensity}/10</span>
  </div>
  
  <div class="point-description">{data.description}</div>
  
  <div class="connected-scenes">{data.connectedScenes.length} scenes</div>
  
  <Handle type="target" position="left" id="story-input" />
  <Handle type="source" position="right" id="story-output" />
</Node>
```

### Seven-Point Story Arc Visualization
```svelte
<!-- SevenPointArc component -->
<script lang="ts">
  import { Node } from '@xyflow/svelte';
  export let plotPoints: PlotPointNodeData[];
  
  const canvasWidth = 1000;
  const canvasHeight = 300;
</script>

<Node class="seven-point-arc" width={canvasWidth} height={canvasHeight}>
  <!-- Background arc -->
  <path d="M 0 250 Q 125 50 250 150 Q 375 250 500 50 Q 625 250 750 150 Q 875 50 1000 250" 
        stroke="#E5E7EB" stroke-width="2" fill="none" />
  
  <!-- Plot points -->
  {#each plotPoints as point}
    <circle cx={point.storyPosition * canvasWidth / 100} 
            cy={250 - (point.emotionalIntensity * 20)} 
            r="12" 
            fill={getPointColor(point.pointType)} />
    
    <line x1={point.storyPosition * canvasWidth / 100} 
            y1={250 - (point.emotionalIntensity * 20)} 
            x2={point.storyPosition * canvasWidth / 100} 
            y2="280" 
            stroke="#6B7280" stroke-width="1" />
    
    <text x={point.storyPosition * canvasWidth / 100} y="295" 
          text-anchor="middle" font-size="12">{point.label}</text>
  {/each}
  
  <!-- Connecting lines -->
  {#each plotPoints.slice(0, -1) as point, i}
    {#if plotPoints[i + 1]}
      <line x1={point.storyPosition * canvasWidth / 100} 
              y1={250 - (point.emotionalIntensity * 20)} 
              x2={plotPoints[i + 1].storyPosition * canvasWidth / 100} 
              y2={250 - (plotPoints[i + 1].emotionalIntensity * 20)} 
              stroke="#3B82F6" stroke-width="2" />
    {/if}
  {/each}
</Node>
```

### Seven-Point Templates
```typescript
const SEVEN_POINT_TEMPLATES = {
  'standard': {
    plotPoints: [
      {
        type: 'hook',
        position: 0,
        intensity: 9,
        description: 'Grab the audience immediately',
        suggestions: ['Start with action', 'Create intrigue', 'Establish stakes']
      },
      {
        type: 'plot-point-1',
        position: 25,
        intensity: 8,
        description: 'First major turning point',
        suggestions: ['Change direction', 'Raise stakes', 'New goal']
      },
      {
        type: 'pinch-1',
        position: 37.5,
        intensity: 7,
        description: 'First major pressure',
        suggestions: ['Introduce conflict', 'Add pressure', 'Reveal opposition']
      },
      {
        type: 'midpoint',
        position: 50,
        intensity: 10,
        description: 'Central revelation or shift',
        suggestions: ['Major revelation', 'Change in direction', 'Point of no return']
      },
      {
        type: 'pinch-2',
        position: 62.5,
        intensity: 8,
        description: 'Second pressure intensification',
        suggestions: ['Increase stakes', 'Major setback', 'Rising tension']
      },
      {
        type: 'plot-point-2',
        position: 75,
        intensity: 9,
        description: 'Second major turning point',
        suggestions: ['Climax set-up', 'Final push', 'No way back']
      },
      {
        type: 'climax',
        position: 87.5,
        intensity: 10,
        description: 'Peak conflict moment',
        suggestions: ['Ultimate confrontation', 'Highest stakes', 'Resolution']
      },
      {
        type: 'resolution',
        position: 100,
        intensity: 5,
        description: 'Final resolution',
        suggestions: ['Wrap up loose ends', 'Character growth', 'New equilibrium']
      }
    ]
  }
};
```

### Validation Engine
```typescript
class SevenPointValidator {
  validateStructure(points: PlotPointNodeData[]): ValidationResult {
    const requiredTypes = ['hook', 'plot-point-1', 'midpoint', 'plot-point-2', 'resolution'];
    const presentTypes = points.map(p => p.pointType);
    
    const missing = requiredTypes.filter(type => !presentTypes.includes(type));
    const duplicates = this.findDuplicates(presentTypes);
    
    return {
      isComplete: missing.length === 0,
      missingPoints: missing,
      duplicatePoints: duplicates,
      arcHealth: this.calculateArcHealth(points),
      suggestions: this.generateStructureSuggestions(points)
    };
  }

  private calculateArcHealth(points: PlotPointNodeData[]): ArcHealth {
    const intensityPattern = this.analyzeIntensityPattern(points);
    const positioning = this.validatePositioning(points);
    
    return {
      overall: Math.round((points.length / 8) * 100),
      intensity: this.calculateIntensityScore(intensityPattern),
      positioning: positioning.accuracy,
      suggestions: this.generateHealthSuggestions(intensityPattern, positioning)
    };
  }

  private analyzeIntensityPattern(points: PlotPointNodeData[]): number[] {
    return points
      .sort((a, b) => a.storyPosition - b.storyPosition)
      .map(p => p.emotionalIntensity);
  }
}
```

### Testing Requirements

#### Unit Tests
- [ ] Plot point positioning accuracy
- [ ] Seven-point structure validation
- [ ] Arc health calculation
- [ ] Intensity pattern analysis
- [ ] Missing point detection

#### Integration Tests
- [ ] Seven-point template application
- [ ] Visual arc rendering
- [ ] Scene clustering around plot points
- [ ] Story structure completeness checking
- [ ] Real-time validation feedback

#### E2E Tests
- [ ] Complete seven-point story creation
- [ ] Guided story development workflow
- [ ] Arc visualization accuracy
- [ ] Story health monitoring
- [ ] Template-based story building

### Dependencies
- **STORY-055**: Story Structure Node Types (for plot point nodes)
- **STORY-057**: Three-Act Structure Support (for story progression)
- **STORY-056**: Asset Node Integration (for scene asset connections)
- **EPIC-001**: Project structure for story data persistence

### Definition of Done
- [ ] All seven plot point types implemented
- [ ] Automatic positioning at correct percentages
- [ ] Visual story arc rendering functional
- [ ] Validation system providing useful feedback
- [ ] Templates for seven-point structure available
- [ ] Guided story development features working
- [ ] Documentation with examples provided
- [ ] Ready for STORY-059 (Blake Snyder Beats) implementation