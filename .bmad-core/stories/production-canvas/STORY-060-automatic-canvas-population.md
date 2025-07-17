# Story: Automatic Canvas Population

**Story ID**: STORY-060  
**Epic**: EPIC-004-production-canvas  
**Type**: Feature  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description

As a filmmaker, I want my canvas to automatically populate with story structure nodes based on my project's narrative breakdown so that I can start visual storytelling immediately without manual node placement and configuration.

## Acceptance Criteria

### Automatic Population System
- [ ] **Story structure parsing** from project.json narrative data
- [ ] **Intelligent node placement** based on story hierarchy
- [ ] **Structure type detection** (Three-Act, Seven-Point, Blake Snyder)
- [ ] **Hierarchical layout** preserving story relationships
- [ ] **Collision avoidance** preventing node overlap

### Smart Layout Algorithm
- [ ] **Timeline-based positioning** using story percentages
- [ ] **Vertical grouping** by story level (Act → Scene → Shot)
- [ ] **Responsive spacing** based on content complexity
- [ ] **Visual flow indication** showing story progression
- [ ] **Auto-connection** of related story elements

### Structure Recognition
- [ ] **Three-act structure** automatic detection and layout
- [ ] **Seven-point method** plot point positioning
- [ ] **Blake Snyder beats** precise placement at percentages
- [ ] **Hybrid structure** support for combined methods
- [ ] **Custom structure** recognition and handling

### Asset Integration
- [ ] **Asset node creation** from project assets
- [ ] **Asset-to-story linking** automatic connections
- [ ] **Character integration** with role-based positioning
- [ ] **Style and location** asset integration
- [ ] **Takes system** integration with story nodes

## Implementation Notes

### Technical Architecture
```typescript
// Canvas population service
class CanvasPopulationService {
  async populateCanvas(project: Project): Promise<CanvasState> {
    const structure = this.detectStoryStructure(project);
    const nodes = this.generateNodes(project, structure);
    const layout = this.calculateLayout(nodes, structure);
    const connections = this.createConnections(nodes);
    
    return {
      nodes: layout.nodes,
      edges: connections,
      viewport: this.calculateViewport(layout.bounds)
    };
  }

  private detectStoryStructure(project: Project): StoryStructure {
    if (project.narrative.structure === 'blake-snyder') {
      return new BlakeSnyderStructure();
    } else if (project.narrative.structure === 'seven-point') {
      return new SevenPointStructure();
    } else {
      return new ThreeActStructure();
    }
  }

  private generateNodes(project: Project, structure: StoryStructure): BaseNode[] {
    const nodes: BaseNode[] = [];
    
    // Generate story structure nodes
    nodes.push(...this.generateStoryNodes(project, structure));
    
    // Generate asset nodes
    nodes.push(...this.generateAssetNodes(project));
    
    // Generate processing nodes
    nodes.push(...this.generateProcessingNodes(project));
    
    return nodes;
  }

  private calculateLayout(nodes: BaseNode[], structure: StoryStructure): LayoutResult {
    const layout = new StoryLayoutEngine();
    return layout.arrangeNodes(nodes, structure);
  }
}
```

### Layout Engine
```typescript
class StoryLayoutEngine {
  arrangeNodes(nodes: BaseNode[], structure: StoryStructure): LayoutResult {
    switch (structure.type) {
      case 'three-act':
        return this.arrangeThreeAct(nodes);
      case 'seven-point':
        return this.arrangeSevenPoint(nodes);
      case 'blake-snyder':
        return this.arrangeBlakeSnyder(nodes);
      default:
        return this.arrangeTimeline(nodes);
    }
  }

  private arrangeThreeAct(nodes: BaseNode[]): LayoutResult {
    const actGroups = this.groupByAct(nodes);
    const positions: Position[] = [];
    
    // Act 1: 0-25%
    actGroups.act1.forEach((node, index) => {
      positions.push({
        x: 100 + (index * 200),
        y: 100
      });
    });
    
    // Act 2: 25-75%
    actGroups.act2.forEach((node, index) => {
      positions.push({
        x: 400 + (index * 150),
        y: 300
      });
    });
    
    // Act 3: 75-100%
    actGroups.act3.forEach((node, index) => {
      positions.push({
        x: 800 + (index * 200),
        y: 500
      });
    });
    
    return { nodes: this.applyPositions(nodes, positions), bounds: this.calculateBounds(positions) };
  }

  private arrangeBlakeSnyder(nodes: BaseNode[]): LayoutResult {
    const beatGroups = this.groupByBeat(nodes);
    const positions: Position[] = [];
    
    Object.entries(beatGroups).forEach(([beatType, beatNodes], index) => {
      const beatPosition = this.getBeatPosition(beatType);
      
      beatNodes.forEach((node, nodeIndex) => {
        positions.push({
          x: (beatPosition * 12) + (nodeIndex * 100),
          y: 200 + (nodeIndex * 50)
        });
      });
    });
    
    return { nodes: this.applyPositions(nodes, positions), bounds: this.calculateBounds(positions) };
  }

  private calculateBounds(positions: Position[]): Bounds {
    const minX = Math.min(...positions.map(p => p.x));
    const maxX = Math.max(...positions.map(p => p.x));
    const minY = Math.min(...positions.map(p => p.y));
    const maxY = Math.max(...positions.map(p => p.y));
    
    return { minX, maxX, minY, maxY, width: maxX - minX, height: maxY - minY };
  }
}
```

### Auto-Connection System
```typescript
class AutoConnectionEngine {
  createConnections(nodes: BaseNode[]): Edge[] {
    const connections: Edge[] = [];
    
    // Connect story structure nodes
    connections.push(...this.connectStoryStructure(nodes));
    
    // Connect assets to story elements
    connections.push(...this.connectAssetsToStory(nodes));
    
    // Connect processing nodes
    connections.push(...this.connectProcessingNodes(nodes));
    
    return connections;
  }

  private connectStoryStructure(nodes: BaseNode[]): Edge[] {
    const storyNodes = nodes.filter(n => n.type.startsWith('story-'));
    const connections: Edge[] = [];
    
    // Connect hierarchical story elements
    const actNodes = storyNodes.filter(n => n.type === 'story-act');
    const sceneNodes = storyNodes.filter(n => n.type === 'story-scene');
    const shotNodes = storyNodes.filter(n => n.type === 'story-shot');
    
    actNodes.forEach(act => {
      const relatedScenes = sceneNodes.filter(scene => scene.parentId === act.id);
      relatedScenes.forEach(scene => {
        connections.push({
          id: `${act.id}-${scene.id}`,
          source: act.id,
          target: scene.id,
          type: 'smoothstep'
        });
      });
    });
    
    return connections;
  }

  private connectAssetsToStory(nodes: BaseNode[]): Edge[] {
    const assetNodes = nodes.filter(n => n.type.startsWith('asset-'));
    const storyNodes = nodes.filter(n => n.type.startsWith('story-'));
    const connections: Edge[] = [];
    
    assetNodes.forEach(asset => {
      const relatedStoryElements = this.findRelatedStoryElements(asset, storyNodes);
      relatedStoryElements.forEach(element => {
        connections.push({
          id: `${asset.id}-${element.id}`,
          source: asset.id,
          target: element.id,
          type: 'smoothstep',
          animated: true
        });
      });
    });
    
    return connections;
  }
}
```

### Structure Detection Engine
```typescript
class StructureDetectionEngine {
  detectStructure(project: Project): StoryStructure {
    const narrative = project.narrative;
    
    if (narrative.structure) {
      return this.createStructure(narrative.structure);
    }
    
    // Auto-detect based on content
    return this.autoDetectStructure(project);
  }

  private autoDetectStructure(project: Project): StoryStructure {
    const scenes = project.narrative.scenes || [];
    
    if (scenes.length > 10) {
      // Likely Blake Snyder structure
      return new BlakeSnyderStructure();
    } else if (scenes.length > 5) {
      // Likely Seven-Point structure
      return new SevenPointStructure();
    } else {
      // Default to Three-Act
      return new ThreeActStructure();
    }
  }

  private createStructure(type: string): StoryStructure {
    const structures = {
      'three-act': new ThreeActStructure(),
      'seven-point': new SevenPointStructure(),
      'blake-snyder': new BlakeSnyderStructure()
    };
    
    return structures[type] || new ThreeActStructure();
  }
}
```

### Canvas Population Component
```svelte
<!-- CanvasPopulationDialog component -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { canvasStore } from '$lib/stores/canvas';
  
  export let project: Project;
  export let onComplete: (state: CanvasState) => void;
  
  let structureType = 'auto';
  let isPopulating = false;
  let progress = 0;
  
  async function populateCanvas() {
    isPopulating = true;
    
    try {
      const state = await canvasStore.populate(project, structureType);
      onComplete(state);
    } catch (error) {
      console.error('Failed to populate canvas:', error);
    } finally {
      isPopulating = false;
    }
  }
  
  onMount(() => {
    populateCanvas();
  });
</script>

<div class="canvas-population-dialog">
  {#if isPopulating}
    <div class="progress-indicator">
      <div class="progress-bar">
        <div class="progress-fill" style="width: {progress}%"></div>
      </div>
      <p>Populating story canvas... {progress}%</p>
    </div>
  {/if}
</div>
```

### Population Templates
```typescript
const POPULATION_TEMPLATES = {
  'three-act': {
    nodes: [
      { type: 'story-act-1', position: { x: 100, y: 100 } },
      { type: 'story-act-2', position: { x: 400, y: 300 } },
      { type: 'story-act-3', position: { x: 800, y: 500 } }
    ],
    connections: [
      { source: 'act-1', target: 'act-2' },
      { source: 'act-2', target: 'act-3' }
    ]
  },
  'seven-point': {
    nodes: [
      { type: 'plot-point', position: { x: 0, y: 200 }, data: { position: 0 } },
      { type: 'plot-point', position: { x: 300, y: 200 }, data: { position: 25 } },
      { type: 'plot-point', position: { x: 600, y: 200 }, data: { position: 50 } },
      { type: 'plot-point', position: { x: 900, y: 200 }, data: { position: 75 } },
      { type: 'plot-point', position: { x: 1200, y: 200 }, data: { position: 100 } }
    ]
  },
  'blake-snyder': {
    nodes: [
      { type: 'beat', position: { x: 0, y: 200 }, data: { position: 0 } },
      { type: 'beat', position: { x: 120, y: 200 }, data: { position: 10 } },
      { type: 'beat', position: { x: 240, y: 200 }, data: { position: 20 } },
      { type: 'beat', position: { x: 360, y: 200 }, data: { position: 35 } },
      { type: 'beat', position: { x: 600, y: 200 }, data: { position: 50 } },
      { type: 'beat', position: { x: 750, y: 200 }, data: { position: 75 } },
      { type: 'beat', position: { x: 1080, y: 200 }, data: { position: 92.5 } },
      { type: 'beat', position: { x: 1200, y: 200 }, data: { position: 100 } }
    ]
  }
};
```

### Testing Requirements

#### Unit Tests
- [ ] Structure detection accuracy
- [ ] Node positioning calculations
- [ ] Layout engine effectiveness
- [ ] Connection creation
- [ ] Collision avoidance

#### Integration Tests
- [ ] Complete canvas population workflow
- [ ] Structure type recognition
- [ ] Asset integration
- [ ] Auto-connection accuracy
- [ ] Layout responsiveness

#### E2E Tests
- [ ] New project canvas population
- [ ] Structure switching
- [ ] Asset auto-placement
- [ ] Story hierarchy preservation
- [ ] Manual override capabilities

### Dependencies
- **STORY-055**: Story Structure Node Types (for node creation)
- **STORY-056**: Asset Node Integration (for asset placement)
- **STORY-057**: Three-Act Structure Support (for layout)
- **STORY-058**: Seven-Point Method Implementation (for positioning)
- **STORY-059**: Blake Snyder Beat Sheet Integration (for beat placement)
- **EPIC-001**: Project structure for story data access
- **EPIC-002**: Asset system for asset integration

### Definition of Done
- [ ] Automatic canvas population working for all structure types
- [ ] Smart layout algorithm preventing overlaps
- [ ] Structure detection accurate
- [ ] Asset integration complete
- [ ] Auto-connections functional
- [ ] Performance acceptable for large projects
- [ ] Manual override capabilities available
- [ ] Documentation with examples provided
- [ ] Ready for STORY-061 (Real-time Collaborative Editing) implementation