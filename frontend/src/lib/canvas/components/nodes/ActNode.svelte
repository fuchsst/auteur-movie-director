<script lang="ts">
  import type { NodeProps } from '@xyflow/svelte';
  import { Handle, Position } from '@xyflow/svelte';
  import type { ActNodeData } from '$lib/canvas/types/canvas';

  type $$Props = NodeProps;
  export let data: ActNodeData;
  export let selected: boolean;
  export let dragging: boolean;

  $: progress = data.duration || 0;
  $: color = data.act === 1 ? '#ef4444' : data.act === 2 ? '#f97316' : '#84cc16';
  $: icon = data.act === 1 ? '🎪' : data.act === 2 ? '⚔️' : '🏁';

  function formatDuration(duration: number): string {
    return `${duration}%`;
  }
</script>

<div class="act-node" class:selected class:dragging style:--color={color}>
  <Handle type="target" position={Position.Left} />
  
  <div class="node-content">
    <div class="node-header">
      <span class="node-icon">{icon}</span>
      <span class="node-title">{data.title}</span>
    </div>
    
    <div class="node-body">
      <div class="act-info">
        <span class="act-number">Act {data.act}</span>
        <span class="duration">{formatDuration(progress)}</span>
      </div>
      
      {#if data.description}
        <p class="description">{data.description}</p>
      {/if}
      
      <div class="progress-bar">
        <div class="progress-fill" style:width="{progress}%"></div>
      </div>
      
      {#if data.scenes && data.scenes.length > 0}
        <div class="scenes-count">
          {data.scenes.length} scene{data.scenes.length !== 1 ? 's' : ''}
        </div>
      {/if}
    </div>
  </div>
  
  <Handle type="source" position={Position.Right} />
</div>

<style>
  .act-node {
    background: var(--color);
    border: 2px solid transparent;
    border-radius: 12px;
    color: white;
    min-width: 200px;
    padding: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
  }

  .act-node.selected {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  }

  .act-node.dragging {
    opacity: 0.8;
    transform: scale(1.05);
  }

  .node-content {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .node-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 14px;
  }

  .node-icon {
    font-size: 16px;
  }

  .node-title {
    flex: 1;
  }

  .node-body {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .act-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    opacity: 0.9;
  }

  .act-number {
    background: rgba(255, 255, 255, 0.2);
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 500;
  }

  .duration {
    font-weight: 600;
  }

  .description {
    font-size: 12px;
    line-height: 1.4;
    opacity: 0.9;
    margin: 0;
  }

  .progress-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: rgba(255, 255, 255, 0.8);
    transition: width 0.3s ease;
  }

  .scenes-count {
    font-size: 11px;
    opacity: 0.8;
    text-align: center;
  }
</style>