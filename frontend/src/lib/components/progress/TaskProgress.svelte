<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { Task } from '$lib/types';

  export let task: Task;
  export let compact = false;

  const dispatch = createEventDispatcher();

  function formatTime(seconds: number): string {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  }

  function getTaskIcon(type: string): string {
    const icons = {
      upload: '📤',
      download: '📥',
      generation: '🎨',
      training: '🧠',
      processing: '⚙️',
      export: '📦'
    };
    return icons[type] || '📋';
  }

  $: progressPercent = task.progress || 0;
  $: isActive = task.status === 'running' || task.status === 'pending';
  $: timeRemaining = task.estimatedTimeRemaining ? formatTime(task.estimatedTimeRemaining) : null;
</script>

<div class="task-progress" class:compact class:active={isActive}>
  <div class="task-header">
    <span class="task-icon">{getTaskIcon(task.type)}</span>
    <div class="task-info">
      <div class="task-name">{task.name}</div>
      {#if !compact && task.details}
        <div class="task-details">{task.details}</div>
      {/if}
    </div>
    <div class="task-actions">
      {#if timeRemaining && isActive}
        <span class="time-remaining">{timeRemaining}</span>
      {/if}
      {#if task.status === 'completed'}
        <span class="status-icon">✅</span>
      {:else if task.status === 'failed'}
        <span class="status-icon">❌</span>
      {:else if task.cancellable}
        <button class="cancel-button" on:click={() => dispatch('cancel')}> ✕ </button>
      {/if}
    </div>
  </div>

  {#if !compact && isActive}
    <div class="progress-bar-container">
      <div class="progress-bar" style="width: {progressPercent}%"></div>
      <span class="progress-text">{progressPercent}%</span>
    </div>
  {/if}
</div>

<style>
  .task-progress {
    background: var(--bg-tertiary);
    border-radius: 6px;
    padding: 8px 12px;
    transition: all 0.2s;
  }

  .task-progress.compact {
    padding: 6px 10px;
  }

  .task-progress.active {
    border: 1px solid var(--border-active);
  }

  .task-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .task-icon {
    font-size: 16px;
    flex-shrink: 0;
  }

  .task-info {
    flex: 1;
    min-width: 0;
  }

  .task-name {
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .task-details {
    font-size: 11px;
    color: var(--text-secondary);
    margin-top: 2px;
  }

  .task-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .time-remaining {
    font-size: 11px;
    color: var(--text-secondary);
  }

  .status-icon {
    font-size: 14px;
  }

  .cancel-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px 6px;
    color: var(--text-secondary);
    font-size: 14px;
    border-radius: 3px;
    transition: all 0.2s;
  }

  .cancel-button:hover {
    background: var(--bg-hover);
    color: var(--color-error);
  }

  .progress-bar-container {
    margin-top: 6px;
    height: 4px;
    background: var(--bg-secondary);
    border-radius: 2px;
    position: relative;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: var(--color-primary);
    transition: width 0.3s ease;
    border-radius: 2px;
  }

  .progress-text {
    position: absolute;
    right: 0;
    top: -16px;
    font-size: 10px;
    color: var(--text-secondary);
  }
</style>
