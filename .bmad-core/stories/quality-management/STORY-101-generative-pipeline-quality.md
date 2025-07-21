# Story: STORY-102 - Generative Pipeline Quality Integration

## Story Description
As a system architect, I need to integrate the quality tier system with the generative pipeline so that all AI-driven content generation respects user-selected quality preferences across different content types.

## Acceptance Criteria
- [ ] Quality tiers integrated into generative pipeline
- [ ] Pipeline respects fixed quality-to-workflow mappings
- [ ] Quality parameters applied throughout pipeline stages
- [ ] Consistent quality tier usage across all generation types
- [ ] Simple quality selection at pipeline entry point
- [ ] No dynamic quality adjustment based on resources

## Technical Details

### Generative Pipeline Quality Service
```python
# backend/app/services/generative_pipeline_quality.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class PipelineStage:
    stage_name: str
    task_type: str
    quality_tier: str
    workflow_path: str
    parameters: Dict[str, Any]

@dataclass
class PipelineConfig:
    pipeline_name: str
    stages: List[PipelineStage]
    quality_consistent: bool = True

class GenerativePipelineQualityService:
    def __init__(self, 
                 workflows_root: str,
                 quality_config_manager):
        self.workflows_root = workflows_root
        self.quality_config = quality_config_manager
    
    def configure_pipeline_with_quality(
        self,
        pipeline_name: str,
        quality_tier: str,
        base_parameters: Dict[str, Any]
    ) -> PipelineConfig:
        """Configure entire pipeline with consistent quality tier"""
        
        pipeline_mappings = {
            "storyboard_generation": [
                {"stage": "scene_layout", "task_type": "scene_generation"},
                {"stage": "character_placement", "task_type": "character_portrait"},
                {"stage": "style_consistency", "task_type": "style_generation"}
            ],
            "shot_generation": [
                {"stage": "shot_setup", "task_type": "scene_generation"},
                {"stage": "character_poses", "task_type": "character_fullbody"},
                {"stage": "lighting_setup", "task_type": "lighting_generation"}
            ],
            "sequence_generation": [
                {"stage": "sequence_planning", "task_type": "sequence_generation"},
                {"stage": "frame_generation", "task_type": "scene_generation"},
                {"stage": "consistency_check", "task_type": "consistency_generation"}
            ]
        }
        
        if pipeline_name not in pipeline_mappings:
            raise ValueError(f"Unknown pipeline: {pipeline_name}")
        
        stages = []
        for stage_config in pipeline_mappings[pipeline_name]:
            quality_config = self.quality_config.get_quality_config(
                stage_config["task_type"],
                quality_tier
            )
            
            if not quality_config:
                raise ValueError(
                    f"No quality config for {stage_config['task_type']}/{quality_tier}"
                )
            
            stage = PipelineStage(
                stage_name=stage_config["stage"],
                task_type=stage_config["task_type"],
                quality_tier=quality_tier,
                workflow_path=quality_config["workflow_path"],
                parameters=self._merge_pipeline_parameters(
                    quality_config["parameters"],
                    base_parameters,
                    stage_config["stage"]
                )
            )
            stages.append(stage)
        
        return PipelineConfig(
            pipeline_name=pipeline_name,
            stages=stages,
            quality_consistent=True
        )
    
    def _merge_pipeline_parameters(
        self,
        quality_params: Dict[str, Any],
        base_params: Dict[str, Any],
        stage_name: str
    ) -> Dict[str, Any]:
        """Merge parameters for pipeline stage"""
        
        merged = quality_params.copy()
        
        # Add stage-specific parameters
        stage_params = self._get_stage_specific_params(stage_name)
        merged.update(stage_params)
        
        # Override with user parameters
        merged.update(base_params)
        
        return merged
    
    def _get_stage_specific_params(self, stage_name: str) -> Dict[str, Any]:
        """Get stage-specific parameters"""
        
        stage_params = {
            "scene_layout": {
                "positive_prompt_suffix": ", scene layout, storyboard visualization"
            },
            "character_placement": {
                "positive_prompt_suffix": ", character placement, scene integration"
            },
            "style_consistency": {
                "positive_prompt_suffix": ", consistent style, scene coherence"
            },
            "shot_setup": {
                "positive_prompt_suffix": ", cinematic shot, storyboard frame"
            },
            "character_poses": {
                "positive_prompt_suffix": ", character pose, action shot"
            },
            "lighting_setup": {
                "positive_prompt_suffix": ", cinematic lighting, mood setting"
            },
            "sequence_planning": {
                "positive_prompt_suffix": ", sequence planning, story continuity"
            },
            "frame_generation": {
                "positive_prompt_suffix": ", frame generation, storyboard frame"
            },
            "consistency_check": {
                "positive_prompt_suffix": ", consistency check, style uniformity"
            }
        }
        
        return stage_params.get(stage_name, {})
    
    def get_pipeline_quality_summary(
        self,
        pipeline_name: str,
        quality_tier: str
    ) -> Dict[str, Any]:
        """Get summary of quality settings for pipeline"""
        
        config = self.configure_pipeline_with_quality(
            pipeline_name, quality_tier, {}
        )
        
        total_time = sum(
            self._estimate_stage_time(stage.task_type, stage.quality_tier)
            for stage in config.stages
        )
        
        return {
            "pipeline_name": pipeline_name,
            "quality_tier": quality_tier,
            "total_stages": len(config.stages),
            "estimated_total_time": total_time,
            "stages": [
                {
                    "stage_name": stage.stage_name,
                    "task_type": stage.task_type,
                    "workflow_path": stage.workflow_path,
                    "estimated_time": self._estimate_stage_time(
                        stage.task_type, stage.quality_tier
                    )
                }
                for stage in config.stages
            ]
        }
    
    def _estimate_stage_time(self, task_type: str, quality_tier: str) -> int:
        """Estimate time for pipeline stage"""
        
        base_times = {
            "scene_generation": {"low": 60, "standard": 120, "high": 240},
            "character_portrait": {"low": 45, "standard": 90, "high": 180},
            "character_fullbody": {"low": 90, "standard": 180, "high": 360},
            "style_generation": {"low": 30, "standard": 60, "high": 120},
            "lighting_generation": {"low": 45, "standard": 90, "high": 180},
            "sequence_generation": {"low": 120, "standard": 240, "high": 480},
            "consistency_generation": {"low": 60, "standard": 120, "high": 240}
        }
        
        if task_type in base_times:
            return base_times[task_type].get(quality_tier, 90)
        
        return 90
```

### Pipeline Execution Service
```python
# backend/app/services/pipeline_execution_service.py
import asyncio
from typing import Dict, Any, List
import uuid
from datetime import datetime

class PipelineExecutionService:
    def __init__(self, 
                 pipeline_quality_service,
                 task_storage,
                 workflow_executor):
        self.quality_service = pipeline_quality_service
        self.storage = task_storage
        self.executor = workflow_executor
    
    async def execute_quality_pipeline(
        self,
        pipeline_name: str,
        quality_tier: str,
        parameters: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Execute complete pipeline with quality tier"""
        
        pipeline_id = str(uuid.uuid4())
        
        try:
            # Configure pipeline with quality
            config = self.quality_service.configure_pipeline_with_quality(
                pipeline_name, quality_tier, parameters
            )
            
            # Store pipeline record
            pipeline_record = {
                "pipeline_id": pipeline_id,
                "user_id": user_id,
                "pipeline_name": pipeline_name,
                "quality_tier": quality_tier,
                "stages": [],
                "status": "preparing",
                "created_at": datetime.now().isoformat()
            }
            
            # Execute each stage
            stage_results = []
            for i, stage in enumerate(config.stages):
                stage_result = await self._execute_pipeline_stage(
                    pipeline_id,
                    stage,
                    i + 1,
                    len(config.stages)
                )
                stage_results.append(stage_result)
            
            pipeline_record["stages"] = stage_results
            pipeline_record["status"] = "completed"
            
            return {
                "pipeline_id": pipeline_id,
                "status": "completed",
                "quality_tier": quality_tier,
                "total_stages": len(config.stages),
                "stage_results": stage_results
            }
            
        except Exception as e:
            pipeline_record = {
                "pipeline_id": pipeline_id,
                "user_id": user_id,
                "pipeline_name": pipeline_name,
                "quality_tier": quality_tier,
                "status": "failed",
                "error": str(e),
                "created_at": datetime.now().isoformat()
            }
            
            return {
                "pipeline_id": pipeline_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _execute_pipeline_stage(
        self,
        pipeline_id: str,
        stage: PipelineStage,
        stage_number: int,
        total_stages: int
    ) -> Dict[str, Any]:
        """Execute single pipeline stage"""
        
        stage_id = f"{pipeline_id}_{stage_number}"
        
        try:
            # Execute stage workflow
            result = await self.executor.execute_workflow(
                stage.workflow_path,
                stage.parameters
            )
            
            return {
                "stage_id": stage_id,
                "stage_name": stage.stage_name,
                "task_type": stage.task_type,
                "quality_tier": stage.quality_tier,
                "workflow_path": stage.workflow_path,
                "status": "completed",
                "result": result,
                "stage_number": stage_number,
                "total_stages": total_stages
            }
            
        except Exception as e:
            return {
                "stage_id": stage_id,
                "stage_name": stage.stage_name,
                "task_type": stage.task_type,
                "quality_tier": stage.quality_tier,
                "workflow_path": stage.workflow_path,
                "status": "failed",
                "error": str(e),
                "stage_number": stage_number,
                "total_stages": total_stages
            }
```

### Frontend Pipeline Quality Interface
```svelte
<!-- frontend/src/lib/components/GenerativePipelineQuality.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  import { userPreferences } from '$lib/stores/user-preferences';

  export let pipelineName: string = 'storyboard_generation';
  export let selectedQuality: string = 'standard';

  const dispatch = createEventDispatcher();

  let qualitySummary = null;
  let loading = true;

  const pipelineOptions = {
    storyboard_generation: {
      name: 'Storyboard Generation',
      description: 'Generate complete storyboards from script'
    },
    shot_generation: {
      name: 'Shot Generation',
      description: 'Generate individual shots for scenes'
    },
    sequence_generation: {
      name: 'Sequence Generation',
      description: 'Generate sequence of frames'
    }
  };

  onMount(async () => {
    await loadQualitySummary();
  });

  async function loadQualitySummary() {
    const response = await fetch(`/api/v1/pipeline-quality/summary/${pipelineName}/${selectedQuality}`);
    qualitySummary = await response.json();
    loading = false;
  }

  async function handleQualityChange(quality: string) {
    selectedQuality = quality;
    loading = true;
    await loadQualitySummary();
    dispatch('qualityChange', { quality, pipelineName });
    
    // Persist preference
    userPreferences.setQualityPreference(pipelineName, quality);
  }

  async function handlePipelineChange(newPipeline: string) {
    pipelineName = newPipeline;
    selectedQuality = userPreferences.getQualityPreference(newPipeline) || 'standard';
    loading = true;
    await loadQualitySummary();
    dispatch('pipelineChange', { pipeline: newPipeline });
  }
</script>

<div class="generative-pipeline-quality">
  <div class="pipeline-selector">
    <label>Pipeline</label>
    <select bind:value={pipelineName} on:change={(e) => handlePipelineChange(e.target.value)}>
      {#each Object.entries(pipelineOptions) as [key, config]}
        <option value={key}>{config.name}</option>
      {/each}
    </select>
    <p class="description">{pipelineOptions[pipelineName]?.description}</p>
  </div>

  <div class="quality-selector">
    <label>Quality Tier</label>
    <div class="quality-options">
      {#each ['low', 'standard', 'high'] as tier}
        <button
          class="quality-btn"
          class:selected={selectedQuality === tier}
          on:click={() => handleQualityChange(tier)}
        >
          {tier.charAt(0).toUpperCase() + tier.slice(1)}
        </button>
      {/each}
    </div>
  </div>

  {#if loading}
    <div class="loading">Loading quality summary...</div>
  {:else if qualitySummary}
    <div class="quality-summary">
      <div class="summary-card">
        <h4>Pipeline Summary</h4>
        <p>{qualitySummary.total_stages} stages • ~{qualitySummary.estimated_total_time}s total</p>
      </div>

      <div class="stages-list">
        <h5>Stages:</h5>
        {#each qualitySummary.stages as stage}
          <div class="stage-item">
            <span class="stage-name">{stage.stage_name.replace('_', ' ')}</span>
            <span class="stage-time">~{stage.estimated_time}s</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .generative-pipeline-quality {
    max-width: 600px;
    padding: 1rem;
  }

  .pipeline-selector {
    margin-bottom: 1.5rem;
  }

  .pipeline-selector label,
  .quality-selector label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  .description {
    margin: 0.5rem 0 0 0;
    font-size: 0.875rem;
    color: #666;
  }

  .quality-options {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .quality-btn {
    flex: 1;
    padding: 0.75rem;
    border: 2px solid #ddd;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: capitalize;
  }

  .quality-btn:hover {
    border-color: #007bff;
  }

  .quality-btn.selected {
    border-color: #007bff;
    background: #007bff;
    color: white;
  }

  .quality-summary {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
  }

  .summary-card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
  }

  .stages-list {
    margin-top: 1rem;
  }

  .stage-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #eee;
  }

  .stage-name {
    text-transform: capitalize;
  }

  .stage-time {
    color: #666;
    font-size: 0.875rem;
  }

  .loading {
    text-align: center;
    padding: 2rem;
    color: #666;
  }
</style>
```

### API Endpoints
```python
# backend/app/api/v1/pipeline_quality.py
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/pipeline-quality", tags=["pipeline-quality"])

@router.get("/summary/{pipeline_name}/{quality_tier}")
async def get_pipeline_summary(pipeline_name: str, quality_tier: str) -> Dict[str, Any]:
    """Get pipeline quality summary"""
    
    valid_pipelines = [
        "storyboard_generation",
        "shot_generation",
        "sequence_generation"
    ]
    
    valid_tiers = ["low", "standard", "high"]
    
    if pipeline_name not in valid_pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    if quality_tier not in valid_tiers:
        raise HTTPException(status_code=400, detail="Invalid quality tier")
    
    service = GenerativePipelineQualityService(
        workflows_root="/comfyui_workflows",
        quality_config_manager=QualityConfigManager(
            "/comfyui_workflows/config/quality_mappings.yaml"
        )
    )
    
    return service.get_pipeline_quality_summary(pipeline_name, quality_tier)

@router.post("/execute")
async def execute_pipeline(request: Dict[str, Any]) -> Dict[str, Any]:
    """Execute pipeline with quality tier"""
    
    required_fields = ["pipeline_name", "quality_tier", "parameters", "user_id"]
    for field in required_fields:
        if field not in request:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    service = PipelineExecutionService(
        pipeline_quality_service=GenerativePipelineQualityService(
            workflows_root="/comfyui_workflows",
            quality_config_manager=QualityConfigManager(
                "/comfyui_workflows/config/quality_mappings.yaml"
            )
        ),
        task_storage=PipelineTaskStorage(),
        workflow_executor=ComfyUIExecutor()
    )
    
    try:
        result = await service.execute_quality_pipeline(
            pipeline_name=request["pipeline_name"],
            quality_tier=request["quality_tier"],
            parameters=request["parameters"],
            user_id=request["user_id"]
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Pipeline execution failed")
```

## Test Requirements
- Pipeline quality configuration accuracy
- Stage execution with quality parameters
- Total time estimation correctness
- API endpoint functionality
- Frontend integration
- Quality consistency across pipeline stages

## Definition of Done
- All pipeline types support quality tier selection
- Quality parameters applied consistently across stages
- Pipeline execution respects quality settings
- Estimated times are accurate
- Frontend provides clear pipeline quality selection
- No resource-based routing or adjustments present