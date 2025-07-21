# Story: STORY-097 - Quality Selection Interface

## Story Description
As a content creator, I need a simple interface to select quality tiers (Low/Standard/High) for my generation tasks so that I can control output quality based on my preferences without complex configuration.

## Acceptance Criteria
- [ ] Three-tier quality selection UI (Low/Standard/High)
- [ ] Quality tier descriptions and trade-offs displayed
- [ ] Persistent quality preference storage per user
- [ ] Task-specific quality tier recommendations
- [ ] Simple dropdown or button selection interface
- [ ] No resource analysis or complex recommendations
- [ ] Direct mapping to ComfyUI workflows

## Technical Details

### Frontend Quality Selection Component
```svelte
<!-- frontend/src/lib/components/QualitySelector.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { userPreferences } from '$lib/stores/user-preferences';

  export let taskType: string = 'character_portrait';
  export let selectedTier: string = 'standard';

  const dispatch = createEventDispatcher();

  const qualityTiers = {
    low: {
      label: 'Low',
      description: 'Fast generation, basic quality',
      icon: '⚡',
      color: 'var(--color-low)'
    },
    standard: {
      label: 'Standard',
      description: 'Balanced quality and speed',
      icon: '⚖️',
      color: 'var(--color-standard)'
    },
    high: {
      label: 'High',
      description: 'Maximum quality, slower generation',
      icon: '✨',
      color: 'var(--color-high)'
    }
  };

  function selectTier(tier: string) {
    selectedTier = tier;
    dispatch('qualityChange', { tier, taskType });
    
    // Persist user preference
    userPreferences.setQualityPreference(taskType, tier);
  }
</script>

<div class="quality-selector">
  <label>Quality Tier</label>
  <div class="tier-options">
    {#each Object.entries(qualityTiers) as [tier, config]}
      <button
        class="tier-option"
        class:selected={selectedTier === tier}
        style="--tier-color: {config.color}"
        on:click={() => selectTier(tier)}
        title={config.description}
      >
        <span class="tier-icon">{config.icon}</span>
        <span class="tier-label">{config.label}</span>
      </button>
    {/each}
  </div>
</div>

<style>
  .quality-selector {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .tier-options {
    display: flex;
    gap: 0.5rem;
  }

  .tier-option {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    border: 2px solid #ddd;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
  }

  .tier-option:hover {
    border-color: var(--tier-color);
    transform: translateY(-2px);
  }

  .tier-option.selected {
    border-color: var(--tier-color);
    background: var(--tier-color);
    color: white;
  }

  .tier-icon {
    font-size: 1.5rem;
    margin-bottom: 0.25rem;
  }

  .tier-label {
    font-size: 0.875rem;
    font-weight: 500;
  }
</style>
```

### Quality Preference Store
```typescript
// frontend/src/lib/stores/user-preferences.ts
import { writable } from 'svelte/store';
import { persistent } from '$lib/stores/persistent';

interface QualityPreferences {
  [taskType: string]: {
    preferredTier: string;
    lastUsed: string;
  };
}

const defaultPreferences: QualityPreferences = {
  character_portrait: { preferredTier: 'standard', lastUsed: new Date().toISOString() },
  scene_generation: { preferredTier: 'standard', lastUsed: new Date().toISOString() },
  video_generation: { preferredTier: 'standard', lastUsed: new Date().toISOString() }
};

export const userPreferences = {
  quality: persistent<QualityPreferences>('quality-preferences', defaultPreferences),

  setQualityPreference(taskType: string, tier: string) {
    userPreferences.quality.update(prefs => ({
      ...prefs,
      [taskType]: {
        preferredTier: tier,
        lastUsed: new Date().toISOString()
      }
    }));
  },

  getQualityPreference(taskType: string): string {
    return userPreferences.quality.get()[taskType]?.preferredTier || 'standard';
  }
};
```

### API Integration
```python
# backend/app/api/v1/quality_selection.py
from fastapi import APIRouter, HTTPException
from typing import Dict, List

router = APIRouter(prefix="/api/v1/quality", tags=["quality"])

@router.get("/tiers/{task_type}")
async def get_quality_tiers(task_type: str) -> Dict:
    """Get available quality tiers for task type"""
    
    tier_mappings = {
        "character_portrait": {
            "low": {
                "description": "Fast generation with basic quality",
                "estimated_time": "30-60 seconds",
                "workflow_path": "library/image_generation/character_portrait/low_v1"
            },
            "standard": {
                "description": "Balanced quality and performance", 
                "estimated_time": "60-120 seconds",
                "workflow_path": "library/image_generation/character_portrait/standard_v1"
            },
            "high": {
                "description": "Maximum quality with fine details",
                "estimated_time": "120-300 seconds", 
                "workflow_path": "library/image_generation/character_portrait/high_v1"
            }
        }
    }
    
    if task_type not in tier_mappings:
        raise HTTPException(status_code=404, detail="Task type not supported")
    
    return {
        "task_type": task_type,
        "tiers": tier_mappings[task_type]
    }

@router.post("/select")
async def select_quality(request: Dict) -> Dict:
    """Select quality tier for task"""
    
    task_type = request.get("task_type")
    quality_tier = request.get("quality_tier")
    
    # Validate tier
    valid_tiers = {"low", "standard", "high"}
    if quality_tier not in valid_tiers:
        raise HTTPException(status_code=400, detail="Invalid quality tier")
    
    # Return workflow path
    mapper = QualityTierMapper("/comfyui_workflows")
    workflow_path = mapper.get_workflow_path(task_type, quality_tier)
    
    return {
        "task_type": task_type,
        "quality_tier": quality_tier,
        "workflow_path": workflow_path,
        "status": "selected"
    }
```

### Task-Specific Integration
```svelte
<!-- frontend/src/lib/components/TaskCreationDialog.svelte -->
<script lang="ts">
  import QualitySelector from './QualitySelector.svelte';
  
  let selectedQuality = 'standard';
  
  async function createTask() {
    const response = await fetch('/api/v1/quality/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_type: 'character_portrait',
        quality_tier: selectedQuality
      })
    });
    
    const result = await response.json();
    // Proceed with task creation using result.workflow_path
  }
</script>

<div class="task-dialog">
  <QualitySelector 
    taskType="character_portrait" 
    bind:selectedTier={selectedQuality}
    on:qualityChange={handleQualityChange}
  />
</div>
```

## Test Requirements
- Quality tier selection functionality
- User preference persistence
- API endpoint accuracy
- UI component rendering
- Integration with task creation

## Definition of Done
- Users can easily select quality tiers via UI
- Preferences persist across sessions
- API returns correct workflow paths
- UI is responsive and intuitive
- Integration with task creation works seamlessly