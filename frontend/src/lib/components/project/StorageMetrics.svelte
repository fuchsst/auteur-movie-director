<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import type { StorageMetrics } from '$lib/types/storage';
  import Icon from '$lib/components/common/Icon.svelte';
  import { formatBytes } from '$lib/utils/format';
  import { progressStore } from '$lib/stores/progress';

  export let projectId: string;

  let metrics: StorageMetrics | null = null;
  let loading = true;
  let error: string | null = null;
  let cleaning = false;

  onMount(() => {
    loadMetrics();
  });

  async function loadMetrics() {
    try {
      loading = true;
      error = null;
      const response = await fetch(`/api/v1/projects/${projectId}/storage`);
      if (!response.ok) throw new Error('Failed to load storage metrics');
      metrics = await response.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load metrics';
      console.error('Error loading storage metrics:', e);
    } finally {
      loading = false;
    }
  }

  async function runCleanup() {
    if (!confirm('Clean up orphaned files and old deleted takes? This cannot be undone.')) {
      return;
    }

    try {
      cleaning = true;
      const response = await fetch(`/api/v1/projects/${projectId}/cleanup`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Cleanup failed');
      
      const result = await response.json();
      progressStore.addNotification({
        message: result.message,
        type: 'success'
      });
      
      // Reload metrics
      await loadMetrics();
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Cleanup failed';
      progressStore.addNotification({
        message,
        type: 'error'
      });
    } finally {
      cleaning = false;
    }
  }

  function getUsageColor(percentage: number): string {
    if (percentage < 50) return 'var(--success-color)';
    if (percentage < 80) return 'var(--warning-color)';
    return 'var(--error-color)';
  }

  function getBreakdownItems(breakdown: StorageMetrics['breakdown']) {
    return [
      { label: 'Takes', value: breakdown.takes, color: '#3B82F6' },
      { label: 'Thumbnails', value: breakdown.thumbnails, color: '#10B981' },
      { label: 'Assets', value: breakdown.assets, color: '#F59E0B' },
      { label: 'Exports', value: breakdown.exports, color: '#8B5CF6' },
      { label: 'Other', value: breakdown.other, color: '#6B7280' }
    ].filter(item => item.value > 0);
  }
</script>

<div class="storage-metrics">
  <div class="metrics-header">
    <h3>
      <Icon name="hard-drive" size={20} />
      Storage Usage
    </h3>
    <button 
      class="btn-icon" 
      on:click={loadMetrics} 
      disabled={loading}
      title="Refresh"
    >
      <Icon name="refresh-cw" size={16} class={loading ? 'animate-spin' : ''} />
    </button>
  </div>

  {#if loading && !metrics}
    <div class="loading">
      <Icon name="loader" size={24} class="animate-spin" />
      <span>Loading storage metrics...</span>
    </div>
  {:else if error}
    <div class="error">
      <Icon name="alert-circle" size={20} />
      <span>{error}</span>
    </div>
  {:else if metrics}
    <div class="metrics-content">
      <!-- Usage Bar -->
      <div class="usage-section">
        <div class="usage-header">
          <span>{formatBytes(metrics.totalSize)} of {formatBytes(metrics.storageLimit)}</span>
          <span class="usage-percent" style="color: {getUsageColor(metrics.usagePercentage)}">
            {metrics.usagePercentage}%
          </span>
        </div>
        <div class="usage-bar">
          <div 
            class="usage-fill" 
            style="width: {metrics.usagePercentage}%; background-color: {getUsageColor(metrics.usagePercentage)}"
          />
        </div>
      </div>

      <!-- Breakdown Chart -->
      <div class="breakdown-section">
        <h4>Storage Breakdown</h4>
        <div class="breakdown-chart">
          {#each getBreakdownItems(metrics.breakdown) as item}
            <div class="breakdown-item">
              <div class="item-header">
                <span class="item-label">
                  <span class="color-dot" style="background-color: {item.color}" />
                  {item.label}
                </span>
                <span class="item-size">{formatBytes(item.value)}</span>
              </div>
              <div class="item-bar">
                <div 
                  class="bar-fill" 
                  style="width: {(item.value / metrics.totalSize) * 100}%; background-color: {item.color}"
                />
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Takes Details -->
      {#if metrics.takesDetails.count > 0}
        <div class="takes-section">
          <h4>Takes Storage ({metrics.takesDetails.count} takes)</h4>
          
          <div class="quality-breakdown">
            <h5>By Quality</h5>
            <div class="quality-items">
              {#each Object.entries(metrics.takesDetails.byQuality) as [quality, size]}
                <div class="quality-item">
                  <span class="quality-label">{quality}</span>
                  <span class="quality-size">{formatBytes(size)}</span>
                </div>
              {/each}
            </div>
          </div>

          {#if metrics.takesDetails.largest.length > 0}
            <div class="largest-takes">
              <h5>Largest Takes</h5>
              <div class="take-list">
                {#each metrics.takesDetails.largest as take}
                  <div class="large-take">
                    <span class="take-id" title={take.shotId}>{take.id}</span>
                    <span class="take-size">{formatBytes(take.size)}</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Cleanup Action -->
      <div class="cleanup-section">
        <button 
          class="btn-secondary cleanup-btn" 
          on:click={runCleanup}
          disabled={cleaning}
        >
          {#if cleaning}
            <Icon name="loader" size={16} class="animate-spin" />
            Cleaning...
          {:else}
            <Icon name="trash-2" size={16} />
            Clean Up Storage
          {/if}
        </button>
        <p class="cleanup-hint">Remove orphaned files and old deleted takes</p>
      </div>
    </div>
  {/if}
</div>

<style>
  .storage-metrics {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1rem;
  }

  .metrics-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .metrics-header h3 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .loading,
  .error {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 2rem;
    color: var(--text-secondary);
  }

  .error {
    color: var(--error-color);
  }

  .metrics-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .usage-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .usage-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .usage-percent {
    font-weight: 600;
  }

  .usage-bar {
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
  }

  .usage-fill {
    height: 100%;
    transition: width 0.3s ease;
  }

  .breakdown-section h4,
  .takes-section h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .breakdown-chart {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .breakdown-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  .item-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-primary);
  }

  .color-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .item-size {
    font-weight: 500;
    color: var(--text-secondary);
  }

  .item-bar {
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    transition: width 0.3s ease;
  }

  .takes-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .quality-breakdown h5,
  .largest-takes h5 {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .quality-items {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.5rem;
  }

  .quality-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    background: var(--bg-tertiary);
    border-radius: 0.25rem;
    font-size: 0.875rem;
  }

  .quality-label {
    text-transform: capitalize;
    color: var(--text-primary);
  }

  .quality-size {
    font-weight: 500;
    color: var(--text-secondary);
  }

  .take-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .large-take {
    display: flex;
    justify-content: space-between;
    padding: 0.375rem 0.5rem;
    background: var(--bg-tertiary);
    border-radius: 0.25rem;
    font-size: 0.875rem;
  }

  .take-id {
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .take-size {
    font-weight: 500;
    color: var(--text-secondary);
    flex-shrink: 0;
  }

  .cleanup-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color);
  }

  .cleanup-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .cleanup-hint {
    margin: 0;
    font-size: 0.75rem;
    color: var(--text-tertiary);
  }

  .btn-icon {
    padding: 0.375rem;
    background: transparent;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    color: var(--text-secondary);
    transition: all 0.2s;
  }

  .btn-icon:hover:not(:disabled) {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .btn-icon:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-secondary {
    padding: 0.5rem 1rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    color: var(--text-primary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--bg-secondary);
    border-color: var(--primary-color);
  }

  .btn-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>