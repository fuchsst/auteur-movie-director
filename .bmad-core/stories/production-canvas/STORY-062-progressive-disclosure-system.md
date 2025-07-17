# Story: Progressive Disclosure System

**Story ID**: STORY-062  
**Epic**: EPIC-004-production-canvas  
**Type**: Feature  
**Points**: 7 (Medium)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description

As a filmmaker of varying experience levels, I want the Production Canvas to intelligently reveal complexity based on my skill and needs so that beginners aren't overwhelmed while experts have full access to advanced features without cluttering the interface.

## Acceptance Criteria

### Progressive Complexity Levels
- [ ] **Beginner mode** showing only essential nodes (Story, Asset, Generate)
- [ ] **Intermediate mode** adding story structure nodes
- [ ] **Advanced mode** revealing all processing and optimization nodes
- [ ] **Expert mode** showing custom nodes and advanced configurations
- [ ] **Dynamic switching** between modes without data loss

### Smart Feature Reveal
- [ ] **Contextual suggestions** based on story progression
- [ ] **Tutorial mode** with step-by-step guidance
- [ ] **Feature discovery** through natural workflow progression
- [ ] **Hint system** for next logical actions
- [ ] **Complexity warnings** before revealing advanced features

### User Skill Assessment
- [ ] **Automatic skill detection** based on usage patterns
- [ ] **Manual skill level setting** in user preferences
- [ ] **Progress tracking** showing feature discovery
- [ ] **Achievement system** for learning milestones
- [ ] **Skill-based recommendations** for templates and workflows

### Interface Adaptation
- [ ] **Adaptive menus** showing relevant actions only
- [ ] **Collapsible panels** for advanced options
- [ ] **Contextual tooltips** appropriate to skill level
- [ ] **Simplified property panels** for beginners
- [ **Advanced property panels** for experts with full control

## Implementation Notes

### Technical Architecture
```typescript
// Progressive disclosure levels
enum ComplexityLevel {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
  EXPERT = 'expert'
}

// Feature visibility configuration
interface FeatureVisibility {
  nodeTypes: string[];
  advancedOptions: string[];
  shortcuts: string[];
  contextActions: string[];
}

// User skill profile
interface UserSkillProfile {
  level: ComplexityLevel;
  experience: number;
  discoveredFeatures: string[];
  lastComplexityIncrease: Date;
  usagePatterns: UsagePattern[];
}

// Progressive disclosure manager
class ProgressiveDisclosureManager {
  private userProfile: UserSkillProfile;
  private featureRegistry: Map<string, FeatureConfig>;

  getVisibleFeatures(context: CanvasContext): FeatureVisibility {
    const level = this.determineUserLevel(context);
    return this.buildVisibilityConfig(level, context);
  }

  suggestNextFeature(userId: string, context: CanvasContext): NextFeatureSuggestion {
    const profile = this.getUserProfile(userId);
    const availableFeatures = this.getAvailableFeatures(profile, context);
    
    return this.calculateBestNextFeature(availableFeatures, profile, context);
  }

  private determineUserLevel(context: CanvasContext): ComplexityLevel {
    const profile = context.userProfile;
    const usage = context.usageMetrics;
    
    // Automatic level detection
    if (usage.totalNodes > 50 && usage.advancedNodes > 10) {
      return ComplexityLevel.EXPERT;
    } else if (usage.totalNodes > 20 && usage.storyNodes > 5) {
      return ComplexityLevel.ADVANCED;
    } else if (usage.totalNodes > 5) {
      return ComplexityLevel.INTERMEDIATE;
    }
    
    return profile.level || ComplexityLevel.BEGINNER;
  }
}
```

### Feature Registry System
```typescript
const FEATURE_REGISTRY = {
  [ComplexityLevel.BEGINNER]: {
    nodeTypes: [
      'story-act',
      'story-scene',
      'story-shot',
      'asset-character',
      'asset-style',
      'asset-location',
      'process-generate'
    ],
    advancedOptions: [],
    shortcuts: ['basic_create', 'basic_connect'],
    contextActions: ['add_story', 'add_asset', 'generate_content']
  },
  
  [ComplexityLevel.INTERMEDIATE]: {
    nodeTypes: [
      ...FEATURE_REGISTRY[ComplexityLevel.BEGINNER].nodeTypes,
      'plot-point',
      'story-beat',
      'process-upscale',
      'process-enhance'
    ],
    advancedOptions: ['quality_settings', 'batch_processing'],
    shortcuts: [
      ...FEATURE_REGISTRY[ComplexityLevel.BEGINNER].shortcuts,
      'story_structure',
      'workflow_templates'
    ],
    contextActions: [
      ...FEATURE_REGISTRY[ComplexityLevel.BEGINNER].contextActions,
      'add_plot_point',
      'create_workflow'
    ]
  },
  
  [ComplexityLevel.ADVANCED]: {
    nodeTypes: [
      ...FEATURE_REGISTRY[ComplexityLevel.INTERMEDIATE].nodeTypes,
      'process-combine',
      'process-transition',
      'assembly-vse',
      'quality-tier-selector'
    ],
    advancedOptions: [
      ...FEATURE_REGISTRY[ComplexityLevel.INTERMEDIATE].advancedOptions,
      'custom_parameters',
      'batch_configurations',
      'workflow_chaining'
    ],
    shortcuts: [
      ...FEATURE_REGISTRY[ComplexityLevel.INTERMEDIATE].shortcuts,
      'advanced_workflows',
      'custom_templates'
    ],
    contextActions: [
      ...FEATURE_REGISTRY[ComplexityLevel.INTERMEDIATE].contextActions,
      'advanced_processing',
      'create_custom_workflow'
    ]
  },
  
  [ComplexityLevel.EXPERT]: {
    nodeTypes: [
      ...FEATURE_REGISTRY[ComplexityLevel.ADVANCED].nodeTypes,
      'custom-node',
      'script-node',
      'debug-node',
      'performance-node'
    ],
    advancedOptions: [
      ...FEATURE_REGISTRY[ComplexityLevel.ADVANCED].advancedOptions,
      'custom_code',
      'performance_tuning',
      'debug_mode',
      'api_configuration'
    ],
    shortcuts: [
      ...FEATURE_REGISTRY[ComplexityLevel.ADVANCED].shortcuts,
      'expert_mode',
      'custom_shortcuts',
      'keyboard_macros'
    ],
    contextActions: [
      ...FEATURE_REGISTRY[ComplexityLevel.ADVANCED].contextActions,
      'create_custom_node',
      'performance_analysis',
      'debug_workflow'
    ]
  }
};
```

### Smart Suggestion Engine
```typescript
class SmartSuggestionEngine {
  generateSuggestions(context: CanvasContext): Suggestion[] {
    const profile = context.userProfile;
    const canvas = context.canvasState;
    
    const suggestions: Suggestion[] = [];
    
    // Analyze canvas state
    const storyNodes = this.countStoryNodes(canvas);
    const assetNodes = this.countAssetNodes(canvas);
    const processingNodes = this.countProcessingNodes(canvas);
    
    // Generate context-aware suggestions
    if (storyNodes > 3 && assetNodes === 0) {
      suggestions.push({
        type: 'add_asset',
        message: 'Consider adding character or style assets to your story',
        priority: 'high',
        action: 'show_asset_browser'
      });
    }
    
    if (storyNodes > 5 && processingNodes === 0) {
      suggestions.push({
        type: 'add_processing',
        message: 'Ready to add processing nodes for content generation',
        priority: 'medium',
        action: 'show_processing_nodes'
      });
    }
    
    return suggestions;
  }

  private calculateComplexityIncrease(profile: UserSkillProfile): boolean {
    const recentUsage = this.getRecentUsage(profile);
    const complexityThreshold = this.getThresholdForLevel(profile.level);
    
    return recentUsage > complexityThreshold;
  }
}
```

### Adaptive Interface Components
```svelte
<!-- AdaptiveNodeLibrary component -->
<script lang="ts">
  import { progressiveStore } from '$lib/stores/progressive';
  import { userStore } from '$lib/stores/user';
  
  let currentLevel: ComplexityLevel;
  let visibleNodes: NodeType[];
  
  $: currentLevel = $userStore.skillLevel;
  $: visibleNodes = $progressiveStore.getVisibleNodeTypes(currentLevel);
  
  function increaseComplexity(): void {
    progressiveStore.requestLevelIncrease();
  }
  
  function decreaseComplexity(): void {
    progressiveStore.setLevel(
      Math.max(currentLevel - 1, ComplexityLevel.BEGINNER)
    );
  }
</script>

<div class="adaptive-node-library">
  <div class="complexity-controls">
    <button on:click={decreaseComplexity} disabled={currentLevel === ComplexityLevel.BEGINNER}>
      Simplify
    </button>
    
    <span class="current-level">{currentLevel}</span>
    
    <button on:click={increaseComplexity} disabled={currentLevel === ComplexityLevel.EXPERT}>
      Complexify
    </button>
  </div>
  
  <div class="node-grid">
    {#each visibleNodes as nodeType}
      <NodeCard {nodeType} level={currentLevel} />
    {/each}
  </div>
</div>

<style>
  .adaptive-node-library {
    padding: 1rem;
  }
  
  .complexity-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  
  .current-level {
    padding: 0.5rem 1rem;
    background: var(--surface-color);
    border-radius: 0.5rem;
    font-weight: bold;
  }
</style>
```

### Tutorial System
```typescript
class TutorialSystem {
  private tutorials: Map<string, TutorialStep[]> = new Map();

  getTutorialForLevel(level: ComplexityLevel): TutorialStep[] {
    return this.tutorials.get(level) || [];
  }

  generateNextTutorialStep(context: CanvasContext): TutorialStep {
    const profile = context.userProfile;
    const canvas = context.canvasState;
    
    const tutorials = {
      [ComplexityLevel.BEGINNER]: [
        {
          id: 'add_first_story',
          title: 'Add Your First Story Node',
          description: 'Start by adding a story act to your canvas',
          action: 'highlight_node_type',
          target: 'story-act',
          completion: () => this.hasNodeType(canvas, 'story-act')
        },
        {
          id: 'connect_story_elements',
          title: 'Connect Story Elements',
          description: 'Drag from output to input to create connections',
          action: 'show_connection_demo',
          completion: () => this.hasConnections(canvas)
        }
      ],
      [ComplexityLevel.INTERMEDIATE]: [
        {
          id: 'add_plot_point',
          title: 'Add Plot Points',
          description: 'Enhance your story with plot point nodes',
          action: 'highlight_node_type',
          target: 'plot-point',
          completion: () => this.hasNodeType(canvas, 'plot-point')
        }
      ]
    };
    
    return tutorials[profile.level]?.find(t => !t.completion()) || null;
  }
}
```

### Contextual Help System
```svelte
<!-- ContextualHelpTooltip component -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { progressiveStore } from '$lib/stores/progressive';
  
  export let context: string;
  export let userLevel: ComplexityLevel;
  
  let helpContent: HelpContent;
  let isVisible = false;
  
  $: helpContent = $progressiveStore.getHelpForContext(context, userLevel);
  
  function showHelp(): void {
    isVisible = true;
  }
  
  function hideHelp(): void {
    isVisible = false;
  }
</script>

<div class="contextual-help">
  <button on:mouseenter={showHelp} on:mouseleave={hideHelp}>
    ?
  </button>
  
  {#if isVisible}
    <div class="help-tooltip">
      <h4>{helpContent.title}</h4>
      <p>{helpContent.description}</p>
      
      {#if helpContent.examples}
        <ul>
          {#each helpContent.examples as example}
            <li>{example}</li>
          {/each}
        </ul>
      {/if}
      
      {#if helpContent.nextStep}
        <button on:click={helpContent.nextStep.action}>
          {helpContent.nextStep.label}
        </button>
      {/if}
    </div>
  {/if}
</div>
```

### Achievement System
```typescript
interface Achievement {
  id: string;
  title: string;
  description: string;
  level: ComplexityLevel;
  condition: (context: CanvasContext) => boolean;
  reward: string;
}

const ACHIEVEMENTS: Achievement[] = [
  {
    id: 'first_story_node',
    title: 'Storyteller',
    description: 'Add your first story structure node',
    level: ComplexityLevel.BEGINNER,
    condition: (ctx) => ctx.canvas.nodes.some(n => n.type.startsWith('story-')),
    reward: 'Unlock intermediate node types'
  },
  {
    id: 'complex_workflow',
    title: 'Workflow Master',
    description: 'Create a workflow with 10+ connected nodes',
    level: ComplexityLevel.INTERMEDIATE,
    condition: (ctx) => ctx.canvas.nodes.length >= 10 && ctx.canvas.edges.length >= 9,
    reward: 'Unlock advanced processing nodes'
  },
  {
    id: 'expert_crafter',
    title: 'Canvas Expert',
    description: 'Use all available node types in a single project',
    level: ComplexityLevel.EXPERT,
    condition: (ctx) => this.hasUsedAllNodeTypes(ctx),
    reward: 'Unlock expert mode and custom nodes'
  }
];
```

### Settings Panel
```svelte
<!-- ProgressiveSettingsPanel component -->
<script lang="ts">
  import { userStore } from '$lib/stores/user';
  import { progressiveStore } from '$lib/stores/progressive';
  
  let selectedLevel: ComplexityLevel;
  let autoDetect: boolean;
  let showTutorials: boolean;
  
  $: selectedLevel = $userStore.skillLevel;
  $: autoDetect = $userStore.autoDetectLevel;
  $: showTutorials = $userStore.showTutorials;
  
  function updateSettings(): void {
    userStore.updateSettings({
      skillLevel: selectedLevel,
      autoDetectLevel: autoDetect,
      showTutorials
    });
  }
</script>

<div class="progressive-settings">
  <h3>Complexity Management</h3>
  
  <div class="setting-group">
    <label>
      <input type="checkbox" bind:checked={autoDetect} />
      Automatically adjust complexity based on usage
    </label>
  </div>
  
  <div class="setting-group">
    <label>Skill Level</label>
    <select bind:value={selectedLevel} disabled={autoDetect}>
      <option value={ComplexityLevel.BEGINNER}>Beginner - Essential features only</option>
      <option value={ComplexityLevel.INTERMEDIATE}>Intermediate - Story structure tools</option>
      <option value={ComplexityLevel.ADVANCED}>Advanced - Full processing capabilities</option>
      <option value={ComplexityLevel.EXPERT}>Expert - All features and custom options</option>
    </select>
  </div>
  
  <div class="setting-group">
    <label>
      <input type="checkbox" bind:checked={showTutorials} />
      Show contextual tutorials and hints
    </label>
  </div>
  
  <button on:click={updateSettings}>Save Settings</button>
</div>
```

### Testing Requirements

#### Unit Tests
- [ ] Feature visibility by complexity level
- [ ] Skill level detection accuracy
- [ ] Tutorial suggestion relevance
- [ ] Achievement unlocking logic
- [ ] Contextual help appropriateness

#### Integration Tests
- [ ] Level switching without data loss
- [ ] Feature progression tracking
- [ ] Tutorial flow effectiveness
- [ ] Achievement system integration
- [ ] Settings persistence

#### E2E Tests
- [ ] Complete beginner-to-expert progression
- [ ] Tutorial-guided learning experience
- [ ] Achievement unlocking workflow
- [ ] Settings customization impact
- [ ] User skill development tracking

### Dependencies
- **STORY-053-060**: All previous node implementations (for feature visibility)
- **EPIC-001**: User preferences system from EPIC-001
- **EPIC-003**: User session management from EPIC-003

### Definition of Done
- [ ] All complexity levels working correctly
- [ ] Automatic skill detection functional
- [ ] Tutorial system providing helpful guidance
- [ ] Achievement system rewarding progression
- [ ] Settings panel allowing customization
- [ ] Contextual help appropriate to skill level
- [ ] Smooth progression between levels
- [ ] Documentation with examples provided
- [ ] Ready for STORY-063 (Template Library) implementation