<script lang="ts">
  import type { NodeProps } from '@xyflow/svelte';
  import { Handle, Position } from '@xyflow/svelte';
  import type { ShotNodeData } from '$lib/canvas/types/canvas';

  type $$Props = NodeProps;
  export let data: ShotNodeData;
  export let selected: boolean;
  export let dragging: boolean;

  $: color = '#10b981';
  $: cameraIcon = getCameraIcon(data.camera || 'wide');
  $: hasAssets = data.assets && data.assets.length > 0;
  $: hasTakes = data.takes && data.takes.length > 0;

  function getCameraIcon(camera: string): string {
    const icons = {
      'wide': '🌍',
      'medium': '📏',
      'close': '🔍',
      'extreme': '🎯',
      'over': '📐',
      'under': '👀',
      'dutch': '🎭',
      'tracking': '🏃'
    };
    return icons[camera] || '📹';
  }

  function formatDuration(duration: number = 0): string {
    if (duration < 1) return `${Math.round(duration * 60)}s`;
    return `${duration}s`;
  }
</script>

<div class="shot-node" class:selected class:dragging style:--color={color}>
  <Handle type="target" position={Position.Left} />
  
  <div class="node-content">
    <div class="node-header">
      <span class="camera-icon">{cameraIcon}</span>
      <span class="shot-title">{data.title}</span>
      <span class="shot-id">{data.act}.{data.scene}.{data.shot}</span>
    </div>
    
    <div class="node-body">
      {#if data.description}
        <p class="description">{data.description}</p>
      {/if}
      
      <div class="shot-details">
        <div class="detail-row">
          <span class="label">Camera:</span>
          <span class="value">{data.camera || 'wide'}</span>
        </div>
        
        {#if data.duration}
          <div class="detail-row">
            <span class="label">Duration:</span>
            <span class="value">{formatDuration(data.duration)}</span>
          </div>
        {/if}
      </div>
      
      <div class="shot-counters">
        {#if hasAssets}
          <div class="counter">
            <span class="counter-icon">🎨</span>
            <span class="counter-value">{data.assets.length}</span>
          </div>
        {/if}
        
        {#if hasTakes}
          <div class="counter">
            <span class="counter-icon">🎬</span>
            <span class="counter-value">{data.takes.length}</span>
          </div>
        {/if}
      </div>
    </div>
  </div>
  
  <Handle type="source" position={Position.Right} />
</div>

<style>
  .shot-node {
    background: var(--color);
    border: 2px solid transparent;
    border-radius: 6px;
    color: white;
    min-width: 160px;
    padding: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
  }

  .shot-node.selected {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  }

  .shot-node.dragging {
    opacity: 0.8;
    transform: scale(1.05);
  }

  .node-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .node-header {
    display: flex;
    align-items: center;
    gap: 4px;
    font-weight: 600;
    font-size: 12px;
  }

  .camera-icon {
    font-size: 12px;
  }

  .shot-title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .shot-id {
    background: rgba(255, 255, 255, 0.2);
    padding: 1px 3px;
    border-radius: 2px;
    font-size: 9px;
    font-weight: 500;
  }

  .node-body {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .description {
    font-size: 10px;
    line-height: 1.2;
    opacity: 0.9;
    margin: 0;
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .shot-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 9px;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .label {
    opacity: 0.8;
  }

  .value {
    font-weight: 600;
    opacity: 0.9;
  }

  .shot-counters {
    display: flex;
    gap: 6px;
    justify-content: center;
    margin-top: 2px;
  }

  .counter {
    display: flex;
    align-items: center;
    gap: 2px;
    background: rgba(255, 255, 255, 0.1);
    padding: 1px 3px;
    border-radius: 2px;
    font-size: 8px;
  }

  .counter-icon {
    font-size: 8px;
  }

  .counter-value {
    font-weight: 600;
    min-width: 8px;
    text-align: center;
  }
</style>