<script lang="ts">
  import type { NodeProps } from '@xyflow/svelte';
  import { Handle, Position } from '@xyflow/svelte';
  import type { AssetNodeData } from '$lib/canvas/types/canvas';

  type $$Props = NodeProps;
  export let data: AssetNodeData;
  export let selected: boolean;
  export let dragging: boolean;

  $: color = '#f59e0b';
  $: thumbnail = data.thumbnail || '/assets/character-placeholder.svg';
  $: qualityColor = getQualityColor(data.quality || 'standard');
  $: statusColor = getStatusColor(data.status || 'ready');
  $: tags = data.tags || [];

  function getQualityColor(quality: string): string {
    const colors = {
      low: '#ef4444',
      standard: '#f59e0b',
      high: '#10b981',
      ultra: '#8b5cf6'
    };
    return colors[quality] || '#6b7280';
  }

  function getStatusColor(status: string): string {
    const colors = {
      pending: '#f59e0b',
      processing: '#3b82f6',
      ready: '#10b981',
      error: '#ef4444'
    };
    return colors[status] || '#6b7280';
  }

  function formatAssetName(name: string): string {
    return name.length > 12 ? name.substring(0, 12) + '...' : name;
  }
</script>

<div class="character-asset-node" class:selected class:dragging style="--color: {color}; --quality-color: {qualityColor}; --status-color: {statusColor}">
  <Handle type="target" position={Position.Left} />
  
  <div class="node-content">
    <div class="thumbnail-container">
      <img src={thumbnail} alt={data.assetName} class="thumbnail" />
      <div class="quality-badge" title="Quality: {data.quality}">{data.quality?.charAt(0).toUpperCase()}</div>
      <div class="status-indicator" title="Status: {data.status}"></div>
    </div>
    
    <div class="asset-info">
      <div class="asset-name" title={data.assetName}>{formatAssetName(data.assetName)}</div>
      <div class="asset-type">Character</div>
      
      {#if tags.length > 0}
        <div class="tags">
          {#each tags.slice(0, 2) as tag}
            <span class="tag">{tag}</span>
          {/each}
          {#if tags.length > 2}
            <span class="tag-more">+{tags.length - 2}</span>
          {/if}
        </div>
      {/if}
    </div>
  </div>
  
  <Handle type="source" position={Position.Right} />
</div>

<style>
  .character-asset-node {
    background: var(--color);
    border: 2px solid transparent;
    border-radius: 8px;
    color: white;
    min-width: 120px;
    padding: 6px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
    position: relative;
  }

  .character-asset-node.selected {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  }

  .character-asset-node.dragging {
    opacity: 0.8;
    transform: scale(1.05);
  }

  .node-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
    align-items: center;
  }

  .thumbnail-container {
    position: relative;
    width: 60px;
    height: 60px;
  }

  .thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 4px;
  }

  .quality-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: var(--quality-color);
    color: white;
    font-size: 8px;
    font-weight: bold;
    padding: 1px 3px;
    border-radius: 50%;
    min-width: 12px;
    text-align: center;
  }

  .status-indicator {
    position: absolute;
    bottom: -2px;
    right: -2px;
    width: 8px;
    height: 8px;
    background: var(--status-color);
    border: 1px solid white;
    border-radius: 50%;
  }

  .asset-info {
    text-align: center;
  }

  .asset-name {
    font-weight: 600;
    font-size: 11px;
    margin-bottom: 1px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .asset-type {
    font-size: 9px;
    opacity: 0.8;
  }

  .tags {
    display: flex;
    gap: 2px;
    flex-wrap: wrap;
    justify-content: center;
    margin-top: 2px;
  }

  .tag, .tag-more {
    background: rgba(255, 255, 255, 0.2);
    padding: 1px 3px;
    border-radius: 2px;
    font-size: 7px;
    font-weight: 500;
  }

  .tag-more {
    background: rgba(255, 255, 255, 0.1);
  }
</style>