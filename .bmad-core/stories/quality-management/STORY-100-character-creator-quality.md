# Story: STORY-101 - Character Creator Quality Integration

## Story Description
As a content creator, I need to select quality tiers for character generation in the Character Creator so that I can control the quality and detail level of generated characters based on my needs.

## Acceptance Criteria
- [ ] Quality tier selection integrated into Character Creator
- [ ] Character-specific quality workflows mapped correctly
- [ ] Quality parameters applied to character generation
- [ ] Preview and comparison between quality tiers
- [ ] User preference persistence for character quality
- [ ] Simple quality selection without resource analysis

## Technical Details

### Character Creator Quality Integration
```python
# backend/app/services/character_quality_service.py
from typing import Dict, Any, Optional
import json
from pathlib import Path

class CharacterQualityService:
    def __init__(self, 
                 workflows_root: str,
                 quality_config_manager):
        self.workflows_root = Path(workflows_root)
        self.quality_config = quality_config_manager
    
    def get_character_quality_config(self, 
                                   character_type: str,
                                   quality_tier: str) -> Dict[str, Any]:
        """Get character-specific quality configuration"""
        
        task_mapping = {
            "character_portrait": "character_portrait",
            "character_fullbody": "character_fullbody", 
            "character_expression": "character_expression",
            "character_style": "character_style"
        }
        
        task_type = task_mapping.get(character_type, "character_portrait")
        
        config = self.quality_config.get_quality_config(task_type, quality_tier)
        if not config:
            raise ValueError(f"No quality config for {character_type}/{quality_tier}")
        
        return {
            "workflow_path": config["workflow_path"],
            "parameters": self._get_character_specific_params(character_type, config["parameters"]),
            "description": config["description"],
            "estimated_time": self._estimate_character_time(character_type, quality_tier)
        }
    
    def _get_character_specific_params(self, 
                                     character_type: str, 
                                     base_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get character-specific parameters"""
        
        character_params = {
            "character_portrait": {
                "width": 512,
                "height": 768,
                "positive_prompt_suffix": ", detailed face, portrait, high quality"
            },
            "character_fullbody": {
                "width": 768,
                "height": 1024,
                "positive_prompt_suffix": ", full body character, detailed clothing"
            },
            "character_expression": {
                "width": 512,
                "height": 512,
                "positive_prompt_suffix": ", expressive face, emotions"
            },
            "character_style": {
                "width": 768,
                "height": 768,
                "positive_prompt_suffix": ", artistic style, unique design"
            }
        }
        
        params = base_params.copy()
        if character_type in character_params:
            params.update(character_params[character_type])
        
        return params
    
    def _estimate_character_time(self, 
                               character_type: str, 
                               quality_tier: str) -> int:
        """Estimate character generation time"""
        
        time_multipliers = {
            "character_portrait": 1.0,
            "character_fullbody": 1.5,
            "character_expression": 0.8,
            "character_style": 1.2
        }
        
        base_times = {
            "low": 45,
            "standard": 90,
            "high": 180
        }
        
        multiplier = time_multipliers.get(character_type, 1.0)
        base_time = base_times.get(quality_tier, 90)
        
        return int(base_time * multiplier)
```

### Character Creator API Integration
```python
# backend/app/api/v1/character_quality.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/character-quality", tags=["character-quality"])

@router.get("/character-types")
async def get_character_types() -> Dict[str, Any]:
    """Get available character types"""
    
    character_types = {
        "character_portrait": {
            "name": "Character Portrait",
            "description": "High-quality character face portraits",
            "supports_quality": True,
            "default_quality": "standard"
        },
        "character_fullbody": {
            "name": "Character Full Body", 
            "description": "Complete character with full body",
            "supports_quality": True,
            "default_quality": "standard"
        },
        "character_expression": {
            "name": "Character Expression",
            "description": "Character with specific emotions/expressions",
            "supports_quality": True,
            "default_quality": "standard"
        },
        "character_style": {
            "name": "Character Style",
            "description": "Character in specific artistic style",
            "supports_quality": True,
            "default_quality": "standard"
        }
    }
    
    return {"character_types": character_types}

@router.get("/quality-options/{character_type}")
async def get_quality_options(character_type: str) -> Dict[str, Any]:
    """Get quality options for character type"""
    
    valid_types = [
        "character_portrait",
        "character_fullbody", 
        "character_expression",
        "character_style"
    ]
    
    if character_type not in valid_types:
        raise HTTPException(status_code=404, detail="Character type not supported")
    
    service = CharacterQualityService(
        workflows_root="/comfyui_workflows",
        quality_config_manager=QualityConfigManager(
            "/comfyui_workflows/config/quality_mappings.yaml"
        )
    )
    
    options = {}
    for tier in ["low", "standard", "high"]:
        try:
            config = service.get_character_quality_config(character_type, tier)
            options[tier] = {
                "description": config["description"],
                "estimated_time": config["estimated_time"],
                "parameters": config["parameters"]
            }
        except ValueError:
            continue
    
    return {
        "character_type": character_type,
        "quality_options": options
    }

@router.post("/generate")
async def generate_character(request: Dict[str, Any]) -> Dict[str, Any]:
    """Generate character with quality tier"""
    
    required_fields = [
        "character_type", "quality_tier", "character_parameters", "user_id"
    ]
    
    for field in required_fields:
        if field not in request:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    service = CharacterQualityService(
        workflows_root="/comfyui_workflows",
        quality_config_manager=QualityConfigManager(
            "/comfyui_workflows/config/quality_mappings.yaml"
        )
    )
    
    try:
        quality_config = service.get_character_quality_config(
            request["character_type"],
            request["quality_tier"]
        )
        
        # Merge character parameters with quality parameters
        final_params = {**quality_config["parameters"], **request["character_parameters"]}
        
        return {
            "character_type": request["character_type"],
            "quality_tier": request["quality_tier"],
            "workflow_path": quality_config["workflow_path"],
            "parameters": final_params,
            "estimated_time": quality_config["estimated_time"],
            "status": "prepared"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Frontend Character Creator Component
```svelte
<!-- frontend/src/lib/components/CharacterCreatorQuality.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { createEventDispatcher } from 'svelte';

  export let characterType: string = 'character_portrait';
  export let selectedQuality: string = 'standard';

  const dispatch = createEventDispatcher();

  let qualityOptions = {};
  let loading = true;
  let characterTypes = {};

  onMount(async () => {
    const [typesResponse, optionsResponse] = await Promise.all([
      fetch('/api/v1/character-quality/character-types'),
      fetch(`/api/v1/character-quality/quality-options/${characterType}`)
    ]);

    const typesData = await typesResponse.json();
    const optionsData = await optionsResponse.json();

    characterTypes = typesData.character_types;
    qualityOptions = optionsData.quality_options;
    loading = false;
  });

  function selectQuality(quality: string) {
    selectedQuality = quality;
    dispatch('qualityChange', { quality, characterType });
  }

  async function handleCharacterTypeChange(newType: string) {
    characterType = newType;
    selectedQuality = 'standard';
    
    const response = await fetch(`/api/v1/character-quality/quality-options/${newType}`);
    const data = await response.json();
    qualityOptions = data.quality_options;
    
    dispatch('characterTypeChange', { type: newType });
  }
</script>

<div class="character-creator-quality">
  {#if loading}
    <div class="loading">Loading quality options...</div>
  {:else}
    <div class="character-type-selector">
      <label>Character Type</label>
      <select bind:value={characterType} on:change={(e) => handleCharacterTypeChange(e.target.value)}>
        {#each Object.entries(characterTypes) as [type, config]}
          <option value={type}>{config.name}</option>
        {/each}
      </select>
    </div>

    <div class="quality-selector">
      <label>Quality Tier</label>
      <div class="quality-cards">
        {#each Object.entries(qualityOptions) as [tier, config]}
          <div 
            class="quality-card"
            class:selected={selectedQuality === tier}
            on:click={() => selectQuality(tier)}
          >
            <h4>{tier.charAt(0).toUpperCase() + tier.slice(1)}</h4>
            <p>{config.description}</p>
            <div class="time-estimate">~{config.estimated_time}s</div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .character-creator-quality {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-width: 600px;
  }

  .character-type-selector select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  .quality-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }

  .quality-card {
    border: 2px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
  }

  .quality-card:hover {
    border-color: #007bff;
    transform: translateY(-2px);
  }

  .quality-card.selected {
    border-color: #007bff;
    background-color: #f0f8ff;
  }

  .quality-card h4 {
    margin: 0 0 0.5rem 0;
    color: #333;
  }

  .quality-card p {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    color: #666;
  }

  .time-estimate {
    font-size: 0.75rem;
    color: #888;
  }

  .loading {
    text-align: center;
    padding: 2rem;
    color: #666;
  }
</style>
```

### Character Generation Store
```typescript
// frontend/src/lib/stores/character-quality-store.ts
import { writable } from 'svelte/store';
import { persistent } from '$lib/stores/persistent';

interface CharacterQualityPreferences {
  [characterType: string]: {
    preferredQuality: string;
    lastUsed: string;
  };
}

const defaultPreferences: CharacterQualityPreferences = {
  character_portrait: { preferredQuality: 'standard', lastUsed: new Date().toISOString() },
  character_fullbody: { preferredQuality: 'standard', lastUsed: new Date().toISOString() },
  character_expression: { preferredQuality: 'standard', lastUsed: new Date().toISOString() },
  character_style: { preferredQuality: 'standard', lastUsed: new Date().toISOString() }
};

export const characterQualityStore = {
  preferences: persistent<CharacterQualityPreferences>('character-quality-preferences', defaultPreferences),

  setQualityPreference(characterType: string, quality: string) {
    characterQualityStore.preferences.update(prefs => ({
      ...prefs,
      [characterType]: {
        preferredQuality: quality,
        lastUsed: new Date().toISOString()
      }
    }));
  },

  getQualityPreference(characterType: string): string {
    return characterQualityStore.preferences.get()[characterType]?.preferredQuality || 'standard';
  }
};
```

### Character Quality Configuration
```yaml
# /comfyui_workflows/config/character_quality_mappings.yaml
version: "1.0"
mappings:
  character_portrait:
    low:
      workflow_path: "library/character/character_portrait/low_v1"
      description: "Fast character portrait generation"
      parameters:
        steps: 20
        cfg_scale: 7.0
        width: 512
        height: 768
        positive_prompt_suffix: ", detailed face, portrait"
    
    standard:
      workflow_path: "library/character/character_portrait/standard_v1"
      description: "Balanced quality character portrait"
      parameters:
        steps: 35
        cfg_scale: 7.5
        width: 512
        height: 768
        positive_prompt_suffix: ", detailed face, portrait, high quality"
    
    high:
      workflow_path: "library/character/character_portrait/high_v1"
      description: "High quality character portrait with fine details"
      parameters:
        steps: 60
        cfg_scale: 8.0
        width: 768
        height: 1024
        positive_prompt_suffix: ", ultra detailed face, portrait, masterpiece"

  character_fullbody:
    low:
      workflow_path: "library/character/character_fullbody/low_v1"
      description: "Fast full body character generation"
      parameters:
        steps: 25
        cfg_scale: 7.0
        width: 768
        height: 1024
    
    standard:
      workflow_path: "library/character/character_fullbody/standard_v1"
      description: "Balanced quality full body character"
      parameters:
        steps: 40
        cfg_scale: 7.5
        width: 768
        height: 1024
    
    high:
      workflow_path: "library/character/character_fullbody/high_v1"
      description: "High quality full body character with details"
      parameters:
        steps: 70
        cfg_scale: 8.5
        width: 1024
        height: 1536
```

## Test Requirements
- Character type quality mapping accuracy
- Parameter merging for character-specific needs
- UI component functionality
- User preference persistence
- API endpoint correctness
- Integration with character generation flow

## Definition of Done
- Character Creator supports quality tier selection
- Character-specific workflows are properly mapped
- Quality parameters are applied correctly
- User preferences persist across sessions
- UI provides clear quality options
- Integration with character generation works seamlessly