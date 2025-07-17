# Story: Blake Snyder Beat Sheet Integration

**Story ID**: STORY-059  
**Epic**: EPIC-004-production-canvas  
**Type**: Feature  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description

As a filmmaker, I want Blake Snyder's Save the Cat beat sheet integrated into my visual story canvas so that I can follow the proven 15-beat structure with automatic positioning, emotional arc visualization, and beat-by-beat story guidance.

## Acceptance Criteria

### Blake Snyder Beat Sheet Nodes
- [ ] **15 distinct beat nodes** with Save the Cat terminology
- [ ] **Beat positioning** at specific story percentages (0%, 1%, 10%, 20%, 22%, 25%, 37%, 50%, 55%, 75%, 80%, 85%, 88%, 90%, 100%)
- [ **Beat type identification** with clear labels and icons
- [ ] **Emotional state visualization** showing character arc progression
- [ ] **Beat connectivity** showing story flow between beats

### Beat Node Types
- [ ] **Opening Image (0%)**: World establishment with visual impact
- [ ] **Theme Stated (1%)**: Foreshadowing the story's message
- [ ] **Set-Up (1-10%)**: Character and world introduction
- [ ] **Catalyst (10%)**: Life-changing event
- [ ] **Debate (10-20%)**: Should I go or not?
- [ ] **Break into Two (20%)**: The decision to act
- [ ] **B Story (22%)**: Love story or secondary plot
- [ ] **Fun and Games (20-50%)**: Promise of the premise
- [ ] **Midpoint (50%)**: False victory or false defeat
- [ ] **Bad Guys Close In (50-75%)**: Rising tension
- [ ] **All Is Lost (75%)**: The lowest point
- [ ] **Dark Night of the Soul (75-80%)**: Reflection and doubt
- [ ] **Break into Three (80%)**: The solution appears
- [ ] **Finale (85-100%)**: Final confrontation and resolution
- [ ] **Final Image (100%)**: Mirror of opening image

### Emotional Arc Visualization
- [ ] **Character arc tracking** showing emotional journey
- [ ] **Beat intensity indicators** with color coding
- [ ] **Story momentum visualization** with tension graph
- [ ] **Character state progression** through beats
- [ ] **Arc completion** showing story health

### Smart Beat System
- [ ] **Automatic beat placement** at exact story percentages
- [ ] **Beat suggestion engine** based on story context
- [ ] **Beat completion tracking** with progress indicators
- [ ] **Missing beat alerts** with guidance
- [ ] **Beat template library** for common story types

## Implementation Notes

### Technical Architecture
```typescript
// Blake Snyder beat types
enum BlakeSnyderBeatType {
  OPENING_IMAGE = 'opening-image',
  THEME_STATED = 'theme-stated',
  SET_UP = 'set-up',
  CATALYST = 'catalyst',
  DEBATE = 'debate',
  BREAK_INTO_TWO = 'break-into-two',
  B_STORY = 'b-story',
  FUN_AND_GAMES = 'fun-and-games',
  MIDPOINT = 'midpoint',
  BAD_GUYS_CLOSE_IN = 'bad-guys-close-in',
  ALL_IS_LOST = 'all-is-lost',
  DARK_NIGHT_SOUL = 'dark-night-soul',
  BREAK_INTO_THREE = 'break-into-three',
  FINALE = 'finale',
  FINAL_IMAGE = 'final-image'
}

// Beat positioning configuration
interface BlakeSnyderBeat {
  type: BlakeSnyderBeatType;
  position: number; // 0-100%
  duration: number; // percentage range
  emotionalState: string;
  intensity: number; // 1-10
  description: string;
  characterArc: number; // -5 to +5
}

// Beat node data
interface BeatNodeData {
  beatType: BlakeSnyderBeatType;
  storyPosition: number;
  emotionalIntensity: number;
  characterState: string;
  beatDescription: string;
  connectedElements: string[];
  completionStatus: 'missing' | 'incomplete' | 'complete';
  suggestions: string[];
}

// Beat positioning service
class BlakeSnyderPositioningService {
  private beatPositions = {
    [BlakeSnyderBeatType.OPENING_IMAGE]: 0,
    [BlakeSnyderBeatType.THEME_STATED]: 1,
    [BlakeSnyderBeatType.SET_UP]: 5,
    [BlakeSnyderBeatType.CATALYST]: 10,
    [BlakeSnyderBeatType.DEBATE]: 15,
    [BlakeSnyderBeatType.BREAK_INTO_TWO]: 20,
    [BlakeSnyderBeatType.B_STORY]: 22,
    [BlakeSnyderBeatType.FUN_AND_GAMES]: 35,
    [BlakeSnyderBeatType.MIDPOINT]: 50,
    [BlakeSnyderBeatType.BAD_GUYS_CLOSE_IN]: 62.5,
    [BlakeSnyderBeatType.ALL_IS_LOST]: 75,
    [BlakeSnyderBeatType.DARK_NIGHT_SOUL]: 77.5,
    [BlakeSnyderBeatType.BREAK_INTO_THREE]: 80,
    [BlakeSnyderBeatType.FINALE]: 92.5,
    [BlakeSnyderBeatType.FINAL_IMAGE]: 100
  };

  getBeatPosition(beatType: BlakeSnyderBeatType): number {
    return this.beatPositions[beatType];
  }

  validateBeatStructure(beats: BeatNodeData[]): ValidationResult {
    const requiredBeats = [
      BlakeSnyderBeatType.OPENING_IMAGE,
      BlakeSnyderBeatType.CATALYST,
      BlakeSnyderBeatType.BREAK_INTO_TWO,
      BlakeSnyderBeatType.MIDPOINT,
      BlakeSnyderBeatType.ALL_IS_LOST,
      BlakeSnyderBeatType.FINALE
    ];
    
    const presentBeats = beats.map(b => b.beatType);
    const missing = requiredBeats.filter(type => !presentBeats.includes(type));
    
    return {
      isComplete: missing.length === 0,
      missingBeats: missing,
      arcHealth: this.calculateCharacterArc(beats),
      beatProgress: this.calculateBeatProgress(beats),
      suggestions: this.generateBeatSuggestions(beats)
    };
  }

  private calculateCharacterArc(beats: BeatNodeData[]): CharacterArc {
    const arc = beats.sort((a, b) => a.storyPosition - b.storyPosition);
    const startState = arc[0]?.characterState || 'neutral';
    const endState = arc[arc.length - 1]?.characterState || 'neutral';
    
    return {
      progression: this.calculateProgression(arc),
      transformation: this.calculateTransformation(startState, endState),
      consistency: this.checkArcConsistency(arc)
    };
  }
}
```

### Beat Node Component
```svelte
<!-- BlakeSnyderBeatNode component -->
<script lang="ts">
  import { Node, Handle } from '@xyflow/svelte';
  export let data: BeatNodeData;
  
  const beatConfig = {
    [BlakeSnyderBeatType.OPENING_IMAGE]: { 
      color: '#EF4444', 
      icon: '🎬', 
      label: 'Opening Image' 
    },
    [BlakeSnyderBeatType.THEME_STATED]: { 
      color: '#8B5CF6', 
      icon: '💭', 
      label: 'Theme Stated' 
    },
    [BlakeSnyderBeatType.CATALYST]: { 
      color: '#F59E0B', 
      icon: '⚡', 
      label: 'Catalyst' 
    },
    [BlakeSnyderBeatType.MIDPOINT]: { 
      color: '#10B981', 
      icon: '🎯', 
      label: 'Midpoint' 
    },
    [BlakeSnyderBeatType.ALL_IS_LOST]: { 
      color: '#1F2937', 
      icon: '😢', 
      label: 'All Is Lost' 
    },
    [BlakeSnyderBeatType.FINALE]: { 
      color: '#EF4444', 
      icon: '🏆', 
      label: 'Finale' 
    }
  };
</script>

<Node class="blake-snyder-beat" 
       style="--beat-color: {beatConfig[data.beatType].color}"
       position={{ x: data.storyPosition * 10, y: 250 - (data.emotionalIntensity * 20) }}>
  <div class="beat-header">
    <span class="beat-icon">{beatConfig[data.beatType].icon}</span>
    <h4>{beatConfig[data.beatType].label}</h4>
    <span class="position">{data.storyPosition}%</span>
  </div>
  
  <div class="beat-intensity">
    <div class="intensity-bar">
      <div class="intensity-fill" style="width: {data.emotionalIntensity * 10}%"></div>
    </div>
    <span>{data.emotionalIntensity}/10</span>
  </div>
  
  <div class="beat-state">{data.characterState}</div>
  
  <div class="beat-status {data.completionStatus}">{data.completionStatus}</div>
  
  <Handle type="target" position="top" id="beat-input" />
  <Handle type="source" position="bottom" id="beat-output" />
</Node>
```

### Character Arc Visualization
```svelte
<!-- CharacterArcVisualization component -->
<script lang="ts">
  import { Node } from '@xyflow/svelte';
  export let beats: BeatNodeData[];
  
  const canvasWidth = 1200;
  const canvasHeight = 400;
</script>

<Node class="character-arc" width={canvasWidth} height={canvasHeight}>
  <!-- Character arc curve -->
  <path d="M 0 350 
           Q 120 200 120 300 
           Q 240 150 360 250 
           Q 480 100 600 50 
           Q 720 100 840 200 
           Q 960 50 1080 100 
           Q 1140 150 1200 350" 
        stroke="#3B82F6" stroke-width="3" fill="none" />
  
  <!-- Beat markers -->
  {#each beats as beat}
    <circle cx={beat.storyPosition * canvasWidth / 100} 
            cy={350 - (beat.characterArc + 5) * 30} 
            r="8" 
            fill={getBeatColor(beat.beatType)} />
    
    <line x1={beat.storyPosition * canvasWidth / 100} 
            y1={350 - (beat.characterArc + 5) * 30} 
            x2={beat.storyPosition * canvasWidth / 100} 
            y2="380" 
            stroke="#6B7280" stroke-width="1" />
    
    <text x={beat.storyPosition * canvasWidth / 100} y="395" 
          text-anchor="middle" font-size="10">{beat.beatType}</text>
  {/each}
  
  <!-- Emotional state labels -->
  <text x="50" y="30" font-size="14" font-weight="bold">Character Arc</text>
  <text x="50" y="50" font-size="12">Negative → Positive Transformation</text>
</Node>
```

### Beat Template System
```typescript
const BLAKE_SNYDER_TEMPLATES = {
  'save-the-cat': {
    beats: [
      {
        type: BlakeSnyderBeatType.OPENING_IMAGE,
        position: 0,
        intensity: 8,
        description: 'Visual representation of the "before" state',
        suggestions: ['Start with striking image', 'Set tone', 'Establish world']
      },
      {
        type: BlakeSnyderBeatType.THEME_STATED,
        position: 1,
        intensity: 6,
        description: 'Foreshadowing the story\'s message',
        suggestions: ['Subtle dialogue', 'Visual metaphor', 'Character statement']
      },
      {
        type: BlakeSnyderBeatType.CATALYST,
        position: 10,
        intensity: 9,
        description: 'Life-changing event that sets story in motion',
        suggestions: ['Unexpected event', 'Loss or gain', 'Call to action']
      },
      {
        type: BlakeSnyderBeatType.BREAK_INTO_TWO,
        position: 20,
        intensity: 8,
        description: 'Decision to act - crossing the threshold',
        suggestions: ['Clear choice', 'Point of no return', 'New world entry']
      }
    ]
  }
};
```

### Beat Suggestion Engine
```typescript
class BeatSuggestionEngine {
  generateBeatSuggestions(context: StoryContext): BeatSuggestion[] {
    const suggestions: BeatSuggestion[] = [];
    
    // Analyze current story state
    const currentBeats = context.existingBeats;
    const storyProgress = this.calculateStoryProgress(context);
    
    // Generate next beat suggestions
    const nextExpectedBeat = this.getNextExpectedBeat(currentBeats, storyProgress);
    
    if (nextExpectedBeat) {
      suggestions.push({
        beatType: nextExpectedBeat,
        position: this.getBeatPosition(nextExpectedBeat),
        description: this.getBeatDescription(nextExpectedBeat),
        rationale: this.getBeatRationale(nextExpectedBeat, context),
        examples: this.getBeatExamples(nextExpectedBeat)
      });
    }
    
    return suggestions;
  }

  private getBeatRationale(beatType: BlakeSnyderBeatType, context: StoryContext): string {
    const rationales = {
      [BlakeSnyderBeatType.CATALYST]: 'Your protagonist needs a clear reason to act',
      [BlakeSnyderBeatType.MIDPOINT]: 'This is where the stakes get raised significantly',
      [BlakeSnyderBeatType.ALL_IS_LOST]: 'Your character needs to hit rock bottom'
    };
    
    return rationales[beatType] || 'This beat will strengthen your story structure';
  }
}
```

### Testing Requirements

#### Unit Tests
- [ ] Beat positioning accuracy (exact percentages)
- [ ] Beat type identification and styling
- [ ] Character arc calculation and visualization
- [ ] Beat validation and completeness checking
- [ ] Template application accuracy

#### Integration Tests
- [ ] 15-beat structure integrity
- [ ] Character arc progression tracking
- [ ] Beat suggestion engine effectiveness
- [ ] Visual arc rendering accuracy
- [ ] Story health monitoring

#### E2E Tests
- [ ] Complete Blake Snyder beat sheet creation
- [ ] Guided beat development workflow
- [ ] Character arc visualization
- [ ] Missing beat detection and alerts
- [ ] Template-based story building

### Dependencies
- **STORY-055**: Story Structure Node Types (for beat containers)
- **STORY-057**: Three-Act Structure Support (for story progression)
- **STORY-058**: Seven-Point Method Implementation (for story structure)
- **STORY-056**: Asset Node Integration (for scene asset connections)
- **EPIC-001**: Project structure for story data persistence

### Definition of Done
- [ ] All 15 Blake Snyder beats implemented
- [ ] Beat positioning at exact story percentages
- [ ] Character arc visualization functional
- [ ] Beat suggestion engine providing useful guidance
- [ ] Templates for Save the Cat structure available
- [ ] Story health monitoring active
- [ ] Documentation with examples provided
- [ ] Ready for STORY-060 (Automatic Canvas Population) implementation