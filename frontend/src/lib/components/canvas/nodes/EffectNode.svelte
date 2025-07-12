<script lang="ts">
  import { Handle, Position } from '@xyflow/svelte';
  import type { EffectNodeProps } from '$lib/types/nodes';
  import { NodeStatus } from '$lib/types/nodes';
  import { createEventDispatcher } from 'svelte';

  type $$Props = EffectNodeProps;
  export let data: $$Props['data'];
  export let selected: boolean = false;

  const dispatch = createEventDispatcher();

  const effectIcons = {
    blur: '🌫️',
    color: '🎨',
    filter: '🎭',
    sharpen: '🔪',
    denoise: '🧹',
    custom: '⚙️'
  };

  const effectParameters = {
    blur: [
      { name: 'radius', label: 'Blur Radius', type: 'range', min: 0, max: 50, step: 1 },
      { name: 'type', label: 'Blur Type', type: 'select', options: ['gaussian', 'motion', 'box'] }
    ],
    color: [
      { name: 'brightness', label: 'Brightness', type: 'range', min: -100, max: 100, step: 1 },
      { name: 'contrast', label: 'Contrast', type: 'range', min: -100, max: 100, step: 1 },
      { name: 'saturation', label: 'Saturation', type: 'range', min: -100, max: 100, step: 1 },
      { name: 'hue', label: 'Hue Shift', type: 'range', min: -180, max: 180, step: 1 }
    ],
    filter: [
      { name: 'preset', label: 'Filter Preset', type: 'select', options: ['vintage', 'noir', 'sepia', 'cool', 'warm'] },
      { name: 'strength', label: 'Strength', type: 'range', min: 0, max: 100, step: 1 }
    ],
    sharpen: [
      { name: 'amount', label: 'Sharpen Amount', type: 'range', min: 0, max: 300, step: 10 },
      { name: 'radius', label: 'Radius', type: 'range', min: 0.5, max: 5, step: 0.5 }
    ],
    denoise: [
      { name: 'strength', label: 'Denoise Strength', type: 'range', min: 0, max: 100, step: 5 },
      { name: 'detail', label: 'Preserve Detail', type: 'range', min: 0, max: 100, step: 5 }
    ],
    custom: [
      { name: 'shader', label: 'Shader Code', type: 'text' }
    ]
  };

  function handleEffectTypeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    dispatch('parameterChange', {
      parameter: 'effectType',
      value: target.value
    });
  }

  function handleParameterChange(paramName: string, e: Event) {
    const target = e.target as HTMLInputElement | HTMLSelectElement;
    const value = target.type === 'range' ? parseFloat(target.value) : target.value;
    
    dispatch('parameterChange', {
      parameter: `parameters.${paramName}`,
      value
    });
  }

  function handleIntensityChange(e: Event) {
    const target = e.target as HTMLInputElement;
    dispatch('parameterChange', {
      parameter: 'intensity',
      value: parseFloat(target.value)
    });
  }

  $: currentParameters = effectParameters[data.effectType] || [];
  $: icon = effectIcons[data.effectType] || '⚙️';

  $: statusClass = {
    [NodeStatus.IDLE]: 'status-idle',
    [NodeStatus.READY]: 'status-ready',
    [NodeStatus.EXECUTING]: 'status-executing',
    [NodeStatus.COMPLETE]: 'status-complete',
    [NodeStatus.ERROR]: 'status-error'
  }[data.status];
</script>

<div class="effect-node node {statusClass}" class:selected>
  <div class="node-header">
    <span class="node-icon">{icon}</span>
    <span class="node-title">{data.label}</span>
  </div>

  <div class="node-content">
    <div class="effect-type">
      <label>
        Effect Type:
        <select value={data.effectType} on:change={handleEffectTypeChange}>
          <option value="blur">Blur</option>
          <option value="color">Color Correction</option>
          <option value="filter">Filter</option>
          <option value="sharpen">Sharpen</option>
          <option value="denoise">Denoise</option>
          <option value="custom">Custom</option>
        </select>
      </label>
    </div>

    <div class="intensity-control">
      <label>
        Intensity:
        <input
          type="range"
          min="0"
          max="100"
          step="1"
          value={data.intensity || 100}
          on:input={handleIntensityChange}
        />
        <span>{data.intensity || 100}%</span>
      </label>
    </div>

    <div class="parameters">
      {#each currentParameters as param}
        <div class="parameter">
          <label>
            {param.label}:
            {#if param.type === 'range'}
              <input
                type="range"
                min={param.min}
                max={param.max}
                step={param.step}
                value={data.parameters[param.name] || 0}
                on:input={(e) => handleParameterChange(param.name, e)}
              />
              <span>{data.parameters[param.name] || 0}</span>
            {:else if param.type === 'select'}
              <select
                value={data.parameters[param.name] || param.options[0]}
                on:change={(e) => handleParameterChange(param.name, e)}
              >
                {#each param.options as option}
                  <option value={option}>{option}</option>
                {/each}
              </select>
            {:else if param.type === 'text'}
              <textarea
                value={data.parameters[param.name] || ''}
                on:input={(e) => handleParameterChange(param.name, e)}
                placeholder="Enter custom shader code..."
                rows="3"
              />
            {/if}
          </label>
        </div>
      {/each}
    </div>

    {#if data.preview}
      <div class="preview">
        <img src={data.preview} alt="Effect preview" />
      </div>
    {/if}

    {#if data.progress !== undefined && data.status === NodeStatus.EXECUTING}
      <div class="progress">
        <div class="progress-bar" style="width: {data.progress}%"></div>
      </div>
    {/if}

    {#if data.error}
      <div class="error-message">{data.error}</div>
    {/if}
  </div>

  <Handle type="target" position={Position.Left} id="input" />
  <Handle type="source" position={Position.Right} id="output" />
</div>

<style>
  .effect-node {
    background: var(--node-bg, #1e293b);
    border: 2px solid var(--node-border, #334155);
    border-radius: 8px;
    min-width: 280px;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    transition: all 0.2s;
  }

  .effect-node.selected {
    border-color: var(--node-selected, #3b82f6);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
  }

  .node-header {
    padding: 8px 12px;
    border-bottom: 1px solid var(--node-border, #334155);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .node-icon {
    font-size: 18px;
  }

  .node-title {
    font-weight: 600;
    color: var(--text-primary, #f1f5f9);
  }

  .node-content {
    padding: 12px;
  }

  .effect-type label,
  .intensity-control label,
  .parameter label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    color: var(--text-secondary, #94a3b8);
    font-size: 12px;
  }

  select,
  input[type="range"],
  textarea {
    width: 100%;
    background: var(--input-bg, #0f172a);
    border: 1px solid var(--input-border, #334155);
    border-radius: 4px;
    padding: 4px 8px;
    color: var(--text-primary, #f1f5f9);
  }

  textarea {
    resize: vertical;
    font-family: monospace;
    font-size: 11px;
  }

  .intensity-control,
  .parameter {
    margin-top: 12px;
  }

  .intensity-control label,
  .parameter label {
    flex-direction: row;
    align-items: center;
    gap: 8px;
  }

  .intensity-control input[type="range"],
  .parameter input[type="range"] {
    flex: 1;
  }

  .intensity-control span,
  .parameter span {
    min-width: 40px;
    text-align: right;
  }

  .parameters {
    max-height: 200px;
    overflow-y: auto;
  }

  .preview {
    margin-top: 12px;
    border: 1px solid var(--node-border, #334155);
    border-radius: 4px;
    overflow: hidden;
  }

  .preview img {
    display: block;
    width: 100%;
    height: auto;
  }

  .progress {
    margin-top: 8px;
    height: 4px;
    background: var(--progress-bg, #334155);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: var(--progress-fill, #3b82f6);
    transition: width 0.3s ease;
  }

  .error-message {
    margin-top: 8px;
    padding: 4px 8px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 4px;
    color: #ef4444;
    font-size: 12px;
  }

  /* Status colors */
  .status-idle {
    border-color: #64748b;
  }

  .status-ready {
    border-color: #10b981;
  }

  .status-executing {
    border-color: #3b82f6;
  }

  .status-complete {
    border-color: #10b981;
  }

  .status-error {
    border-color: #ef4444;
  }

  /* Handle styles */
  :global(.svelte-flow__handle) {
    width: 12px;
    height: 12px;
    background: #8b5cf6;
    border: 2px solid #1e293b;
  }

  :global(.svelte-flow__handle-left) {
    left: -6px;
  }

  :global(.svelte-flow__handle-right) {
    right: -6px;
  }
</style>