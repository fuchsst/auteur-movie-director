<script lang="ts">
  import { Handle, Position } from '@xyflow/svelte';
  import type { AudioNodeProps } from '$lib/types/nodes';
  import { NodeStatus } from '$lib/types/nodes';
  import { createEventDispatcher } from 'svelte';

  type $$Props = AudioNodeProps;
  export let data: $$Props['data'];
  export let selected: boolean = false;

  const dispatch = createEventDispatcher();

  let canvas: HTMLCanvasElement;

  // Waveform visualization
  function drawWaveform(canvas: HTMLCanvasElement, waveform?: Float32Array) {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 1;

    if (!waveform || waveform.length === 0) {
      // Draw placeholder line
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();
      return;
    }

    const step = canvas.width / waveform.length;
    const amplitude = canvas.height / 2;

    ctx.beginPath();
    for (let i = 0; i < waveform.length; i++) {
      const x = i * step;
      const y = amplitude + waveform[i] * amplitude;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
  }

  function handleSourceChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    dispatch('parameterChange', {
      parameter: 'audioSource',
      value: target.value
    });
  }

  function handleVolumeChange(e: Event) {
    const target = e.target as HTMLInputElement;
    dispatch('parameterChange', {
      parameter: 'volume',
      value: parseFloat(target.value)
    });
  }

  function handleTextChange(e: Event) {
    const target = e.target as HTMLTextAreaElement;
    dispatch('parameterChange', {
      parameter: 'text',
      value: target.value
    });
  }

  $: statusClass = {
    [NodeStatus.IDLE]: 'status-idle',
    [NodeStatus.READY]: 'status-ready',
    [NodeStatus.EXECUTING]: 'status-executing',
    [NodeStatus.COMPLETE]: 'status-complete',
    [NodeStatus.ERROR]: 'status-error'
  }[data.status];
</script>

<div class="audio-node node {statusClass}" class:selected>
  <div class="node-header">
    <span class="node-icon">🎵</span>
    <span class="node-title">{data.label}</span>
  </div>

  <div class="node-content">
    <div class="audio-source">
      <label>
        Source:
        <select value={data.audioSource || 'file'} on:change={handleSourceChange}>
          <option value="file">File</option>
          <option value="generate">Generate</option>
          <option value="record">Record</option>
        </select>
      </label>
    </div>

    {#if data.audioSource === 'generate'}
      <div class="text-input">
        <label>
          Text:
          <textarea
            value={data.text || ''}
            on:input={handleTextChange}
            placeholder="Enter text for voice synthesis..."
            rows="2"
          />
        </label>
      </div>
    {/if}

    <div class="waveform-container">
      <canvas
        bind:this={canvas}
        width="200"
        height="60"
        use:drawWaveform={data.waveform}
      />
    </div>

    <div class="volume-control">
      <label>
        Volume:
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={data.volume || 1}
          on:input={handleVolumeChange}
        />
        <span>{((data.volume || 1) * 100).toFixed(0)}%</span>
      </label>
    </div>

    {#if data.duration}
      <div class="duration">
        Duration: {data.duration.toFixed(1)}s
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

  <Handle type="target" position={Position.Left} id="audio-in" />
  <Handle type="source" position={Position.Right} id="audio-out" />
</div>

<style>
  .audio-node {
    background: var(--node-bg, #1e293b);
    border: 2px solid var(--node-border, #334155);
    border-radius: 8px;
    min-width: 240px;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    transition: all 0.2s;
  }

  .audio-node.selected {
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

  .audio-source label,
  .text-input label,
  .volume-control label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    color: var(--text-secondary, #94a3b8);
    font-size: 12px;
  }

  select,
  textarea,
  input[type="range"] {
    width: 100%;
    background: var(--input-bg, #0f172a);
    border: 1px solid var(--input-border, #334155);
    border-radius: 4px;
    padding: 4px 8px;
    color: var(--text-primary, #f1f5f9);
  }

  textarea {
    resize: vertical;
    min-height: 40px;
  }

  .waveform-container {
    margin: 12px 0;
    border: 1px solid var(--node-border, #334155);
    border-radius: 4px;
    overflow: hidden;
  }

  canvas {
    display: block;
    width: 100%;
    height: 60px;
    background: var(--canvas-bg, #0f172a);
  }

  .volume-control {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .volume-control label {
    flex-direction: row;
    align-items: center;
    flex: 1;
  }

  .duration {
    margin-top: 8px;
    font-size: 12px;
    color: var(--text-secondary, #94a3b8);
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
    background: #3b82f6;
    border: 2px solid #1e293b;
  }

  :global(.svelte-flow__handle-left) {
    left: -6px;
  }

  :global(.svelte-flow__handle-right) {
    right: -6px;
  }
</style>