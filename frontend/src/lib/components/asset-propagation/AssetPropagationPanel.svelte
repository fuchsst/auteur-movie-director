<!--
  Asset Propagation Panel
  STORY-089 Implementation
  
  UI component for managing asset propagation across story hierarchy
-->

<script lang="ts">
  import { onMount } from 'svelte';
  import type { HierarchyLevel, AssetResolutionResponse } from '$lib/types/asset-propagation';
  import assetPropagationStore from '$lib/stores/asset-propagation';

  export let projectId: string;
  export let level: HierarchyLevel;
  export let levelId: string;

  let resolvedAssets: AssetResolutionResponse | null = null;
  let loading = false;
  let error: string | null = null;

  // Subscribe to store changes
  $: if (projectId && level && levelId) {
    loadAssets();
  }

  async function loadAssets() {
    loading = true;
    error = null;
    
    try {
      resolvedAssets = await assetPropagationStore.resolveAssets(projectId, level, levelId);
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  async function refreshAssets() {
    await loadAssets();
  }

  function getAssetIcon(type: string): string {
    const iconMap: Record<string, string> = {
      character: '👤',
      style: '🎨',
      location: '📍',
      prop: '🧩',
      wardrobe: '👗',
      vehicle: '🚗',
      set_dressing: '🏠',
      sfx: '✨',
      sound: '🔊',
      music: '🎵'
    };
    return iconMap[type] || '📦';
  }

  function formatLevelName(level: HierarchyLevel): string {
    return level.charAt(0).toUpperCase() + level.slice(1);
  }
</script>

<div class="asset-propagation-panel">
  <div class="panel-header">
    <h3>Asset Propagation</h3>
    <div class="panel-controls">
      <span class="level-info">
        {formatLevelName(level)}: {levelId}
      </span>
      <button class="refresh-btn" on:click={refreshAssets} disabled={loading}>
        {loading ? '⟳ Refreshing...' : '⟳ Refresh'}
      </button>
    </div>
  </div>

  {#if error}
    <div class="error-message">
      <span>⚠️ {error}</span>
    </div>
  {/if}

  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <span>Loading assets...</span>
    </div>
  {:else if resolvedAssets}
    <div class="assets-summary">
      <div class="summary-stats">
        <div class="stat">
          <span class="stat-number">{resolvedAssets.totalAssets}</span>
          <span class="stat-label">Total Assets</span>
        </div>
        {#each Object.entries(resolvedAssets.assetTypes) as [type, count]}
          <div class="stat">
            <span class="stat-number">{count}</span>
            <span class="stat-label">{type}</span>
          </div>
        {/each}
      </div>
    </div>

    <div class="assets-list">
      {#each Object.entries(resolvedAssets.resolvedAssets) as [type, assets]}
        {#if assets.length > 0}
          <div class="asset-group">
            <h4>
              <span class="asset-icon">{getAssetIcon(type)}</span>
              {type.charAt(0).toUpperCase() + type.slice(1)}
              <span class="asset-count">({assets.length})</span>
            </h4>
            
            <div class="asset-items">
              {#each assets as asset}
                <div class="asset-item" class:inherited={asset.sourceLevel !== level}>
                  <div class="asset-info">
                    <span class="asset-name">{asset.assetId}</span>
                    {#if asset.isOverridden}
                      <span class="override-badge">Override</span>
                    {/if}
                    {#if asset.sourceLevel !== level}
                      <span class="inherited-badge">
                        Inherited from {asset.sourceLevel}
                      </span>
                    {/if}
                  </div>
                  {#if Object.keys(asset.overrideData).length > 0}
                    <div class="override-data">
                      Override: {JSON.stringify(asset.overrideData)}
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/if}
      {/each}
    </div>
  {:else}
    <div class="empty-state">
      <p>No assets assigned to this level.</p>
      <p>Assets will be inherited from parent levels or can be added specifically.</p>
    </div>
  {/if}
</div>

<style>
  .asset-propagation-panel {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    max-height: 600px;
    overflow-y: auto;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
  }

  .panel-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .panel-controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .level-info {
    font-size: 0.9rem;
    color: var(--text-secondary);
    font-family: monospace;
  }

  .refresh-btn {
    background: var(--accent-color);
    color: white;
    border: none;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .refresh-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error-message {
    background: var(--error-bg);
    color: var(--error-color);
    padding: 0.75rem;
    border-radius: 4px;
    margin-bottom: 1rem;
  }

  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 2rem;
    color: var(--text-secondary);
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid var(--border-color);
    border-top: 2px solid var(--accent-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .assets-summary {
    margin-bottom: 1rem;
  }

  .summary-stats {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5rem;
    background: var(--bg-tertiary);
    border-radius: 4px;
    min-width: 60px;
  }

  .stat-number {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--accent-color);
  }

  .stat-label {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .asset-group {
    margin-bottom: 1.5rem;
  }

  .asset-group h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.9rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .asset-icon {
    font-size: 1.1rem;
  }

  .asset-count {
    color: var(--text-secondary);
    font-weight: normal;
  }

  .asset-items {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .asset-item {
    padding: 0.5rem;
    background: var(--bg-tertiary);
    border-radius: 4px;
    border-left: 3px solid transparent;
  }

  .asset-item.inherited {
    border-left-color: var(--info-color);
    background: var(--bg-tertiary);
  }

  .asset-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .asset-name {
    font-family: monospace;
    font-size: 0.9rem;
  }

  .override-badge,
  .inherited-badge {
    font-size: 0.7rem;
    padding: 0.125rem 0.25rem;
    border-radius: 2px;
  }

  .override-badge {
    background: var(--warning-bg);
    color: var(--warning-color);
  }

  .inherited-badge {
    background: var(--info-bg);
    color: var(--info-color);
  }

  .override-data {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
    font-family: monospace;
  }

  .empty-state {
    text-align: center;
    padding: 2rem;
    color: var(--text-secondary);
  }

  .empty-state p {
    margin: 0.5rem 0;
  }
</style>