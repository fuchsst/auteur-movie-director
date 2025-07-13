<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { gitPerformanceApi } from '$lib/api/gitPerformance';
  import { gitStore } from '$lib/stores/git';
  import type { GitPerformanceMetrics } from '$lib/api/gitPerformance';
  import { Activity, Database, Zap, AlertCircle } from 'lucide-svelte';
  
  let metrics: GitPerformanceMetrics | null = null;
  let loading = false;
  let error: string | null = null;
  let refreshInterval: number;
  
  // Subscribe to store metrics
  $: metrics = $gitStore.performance;
  
  async function loadMetrics() {
    loading = true;
    error = null;
    
    try {
      const data = await gitPerformanceApi.getMetrics();
      gitStore.setPerformance(data);
    } catch (err) {
      error = 'Failed to load performance metrics';
      console.error('Error loading metrics:', err);
    } finally {
      loading = false;
    }
  }
  
  function formatTime(ms: number): string {
    if (ms < 1000) {
      return `${Math.round(ms)}ms`;
    }
    return `${(ms / 1000).toFixed(1)}s`;
  }
  
  function formatPercentage(rate: number): string {
    return `${Math.round(rate * 100)}%`;
  }
  
  function getStatusColor(value: number, threshold: number, inverse = false): string {
    const ratio = inverse ? threshold / value : value / threshold;
    if (ratio <= 0.5) return 'var(--success-color)';
    if (ratio <= 0.8) return 'var(--warning-color)';
    return 'var(--error-color)';
  }
  
  onMount(() => {
    loadMetrics();
    // Refresh metrics every 30 seconds
    refreshInterval = setInterval(loadMetrics, 30000);
  });
  
  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
</script>

<div class="performance-monitor">
  <div class="monitor-header">
    <h3>
      <Activity size={16} />
      Performance Monitor
    </h3>
    <button 
      class="refresh-button" 
      on:click={loadMetrics}
      disabled={loading}
      title="Refresh metrics"
    >
      <Zap size={14} class:spinning={loading} />
    </button>
  </div>
  
  {#if error}
    <div class="error">
      <AlertCircle size={16} />
      {error}
    </div>
  {:else if metrics}
    <div class="metrics-grid">
      <!-- Cache Performance -->
      <div class="metric-card">
        <div class="metric-header">
          <Database size={14} />
          <span>Cache Performance</span>
        </div>
        <div class="metric-value">
          <span 
            class="value" 
            style="color: {getStatusColor(metrics.cache_hit_rate, metrics.thresholds.cache_hit_rate)}"
          >
            {formatPercentage(metrics.cache_hit_rate)}
          </span>
          <span class="label">Hit Rate</span>
        </div>
        <div class="metric-stats">
          <span>{metrics.cache_hits} hits</span>
          <span>{metrics.cache_misses} misses</span>
        </div>
      </div>
      
      <!-- Operation Times -->
      <div class="metric-card">
        <div class="metric-header">
          <Zap size={14} />
          <span>Operation Speed</span>
        </div>
        {#if metrics.average_operation_times_ms}
          <div class="operation-times">
            {#each Object.entries(metrics.average_operation_times_ms) as [operation, time]}
              <div class="operation-time">
                <span class="operation-name">{operation.replace(/_/g, ' ')}</span>
                <span 
                  class="operation-value"
                  style="color: {getStatusColor(time, metrics.thresholds[`${operation}_ms`] || 1000, true)}"
                >
                  {formatTime(time)}
                </span>
              </div>
            {/each}
          </div>
        {:else}
          <p class="no-data">No operations recorded</p>
        {/if}
      </div>
      
      <!-- Cache Status -->
      <div class="metric-card">
        <div class="metric-header">
          <span class="status-indicator" class:enabled={metrics.cache_enabled} />
          <span>Cache Status</span>
        </div>
        <div class="cache-status">
          {#if metrics.cache_enabled}
            <p class="status-text success">Enabled</p>
            <p class="requests-count">{metrics.total_requests} total requests</p>
          {:else}
            <p class="status-text warning">Disabled</p>
            <p class="hint">Redis not available</p>
          {/if}
        </div>
      </div>
    </div>
  {:else if loading}
    <div class="loading">
      <div class="spinner" />
      <p>Loading metrics...</p>
    </div>
  {/if}
</div>

<style>
  .performance-monitor {
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
  }
  
  .monitor-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }
  
  .monitor-header h3 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 600;
  }
  
  .refresh-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .refresh-button:hover:not(:disabled) {
    background: var(--surface-hover);
    border-color: var(--primary-color);
  }
  
  .refresh-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .spinning {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .error {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(239, 68, 68, 0.1);
    color: var(--error-color);
    border-radius: 4px;
    font-size: 0.875rem;
  }
  
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    color: var(--text-secondary);
  }
  
  .spinner {
    width: 32px;
    height: 32px;
    border: 2px solid var(--border-color);
    border-top-color: var(--primary-color);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 0.5rem;
  }
  
  .metrics-grid {
    display: grid;
    gap: 1rem;
  }
  
  .metric-card {
    background: var(--surface-primary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 1rem;
  }
  
  .metric-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    color: var(--text-secondary);
    font-size: 0.8125rem;
    font-weight: 500;
  }
  
  .metric-value {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .metric-value .value {
    font-size: 1.5rem;
    font-weight: 600;
  }
  
  .metric-value .label {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  
  .metric-stats {
    display: flex;
    gap: 1rem;
    font-size: 0.8125rem;
    color: var(--text-secondary);
  }
  
  .operation-times {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .operation-time {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.8125rem;
  }
  
  .operation-name {
    color: var(--text-secondary);
    text-transform: capitalize;
  }
  
  .operation-value {
    font-weight: 500;
    font-family: var(--font-mono);
  }
  
  .status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--error-color);
  }
  
  .status-indicator.enabled {
    background: var(--success-color);
  }
  
  .cache-status {
    font-size: 0.875rem;
  }
  
  .status-text {
    font-weight: 500;
    margin-bottom: 0.25rem;
  }
  
  .status-text.success {
    color: var(--success-color);
  }
  
  .status-text.warning {
    color: var(--warning-color);
  }
  
  .requests-count,
  .hint {
    color: var(--text-secondary);
    font-size: 0.8125rem;
  }
  
  .no-data {
    color: var(--text-secondary);
    font-size: 0.8125rem;
    margin: 0;
  }
</style>