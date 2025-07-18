<script lang="ts">
  import type { NodeProps } from '@xyflow/svelte';
  import { Handle, Position } from '@xyflow/svelte';
  import type { SceneNodeData } from '$lib/canvas/types/canvas';

  type $$Props = NodeProps;
  export let data: SceneNodeData;
  export let selected: boolean;
  export let dragging: boolean;

  $: color = '#06b6d4';
  $: hasCharacters = data.characters && data.characters.length > 0;
  $: hasLocations = data.locations && data.locations.length > 0;
  $: hasShots = data.shots && data.shots.length > 0;

  function getDurationColor(duration: number = 0): string {
    if (duration < 3) return '#ef4444';
    if (duration < 5) return '#f59e0b';
    return '#10b981';
  }
</script>

<div class="scene-node" class:selected class:dragging style:--color={color}>
  <Handle type="target" position={Position.Left} />
  
  <div class="node-content">
    <div class="node-header">
      <span class="node-icon">🎭</span>
      <span class="node-title">{data.title}</span>
      <span class="scene-id">{data.act}.{data.scene}</span>
    </div>
    
    <div class="node-body">
      {#if data.description}
        <p class="description">{data.description}</p>
      {/if}
      
      <div class="scene-stats">
        {#if data.duration}
          <span class="duration" style:color={getDurationColor(data.duration)}>
            {data.duration}min
          </span>
        {/if}
        
        {#if hasShots}
          <span class="shots-count">
            {data.shots.length} shot{data.shots.length !== 1 ? 's' : ''}
          </span>
        {/if}
      </div>
      
      <div class="scene-assets">
        {#if hasCharacters}
          <div class="asset-group">
            <span class="asset-label">👥</span>
            <span class="asset-count">{data.characters.length}</span>
          </div>
        {/if}
        
        {#if hasLocations}
          <div class="asset-group">
            <span class="asset-label">📍</span>
            <span class="asset-count">{data.locations.length}</span>
          </div>
        {/if}
      </div>
    </div>
  </div>
  
  <Handle type="source" position={Position.Right} />
</div>

<style>
  .scene-node {
    background: var(--color);
    border: 2px solid transparent;
    border-radius: 8px;
    color: white;
    min-width: 180px;
    padding: 10px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
  }

  .scene-node.selected {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  }

  .scene-node.dragging {
    opacity: 0.8;
    transform: scale(1.05);
  }

  .node-content {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .node-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 600;
    font-size: 13px;
  }

  .node-icon {
    font-size: 14px;
  }

  .node-title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .scene-id {
    background: rgba(255, 255, 255, 0.2);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 500;
  }

  .node-body {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .description {
    font-size: 11px;
    line-height: 1.3;
    opacity: 0.9;
    margin: 0;
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .scene-stats {
    display: flex;
    gap: 8px;
    align-items: center;
    font-size: 10px;
    opacity: 0.9;
  }

  .duration {
    font-weight: 600;
  }

  .shots-count {
    background: rgba(255, 255, 255, 0.2);
    padding: 1px 4px;
    border-radius: 3px;
  }

  .scene-assets {
    display: flex;
    gap: 8px;
    justify-content: center;
  }

  .asset-group {
    display: flex;
    align-items: center;
    gap: 2px;
    background: rgba(255, 255, 255, 0.1);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 9px;
  }

  .asset-label {
    font-size: 10px;
  }

  .asset-count {
    font-weight: 600;
    min-width: 12px;
    text-align: center;
  }
</style>