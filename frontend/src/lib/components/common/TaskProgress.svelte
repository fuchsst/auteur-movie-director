<script lang="ts">
  import { activeTasks } from '$lib/stores/websocket';
  import type { TaskProgressPayload } from '$lib/types/websocket';

  function getProgressColor(progress: number): string {
    if (progress < 0) return 'var(--error-color)';
    if (progress < 0.3) return 'var(--warning-color)';
    if (progress < 1) return 'var(--primary-color)';
    return 'var(--success-color)';
  }

  function formatTaskId(taskId: string): string {
    // Extract meaningful part from task ID
    const parts = taskId.split(':');
    return parts.length > 1 ? parts[1] : taskId;
  }
</script>

{#if $activeTasks.length > 0}
  <div class="task-progress-container">
    <h4>Active Tasks</h4>
    {#each $activeTasks as task (task.task_id)}
      <div class="task-item" class:error={task.error}>
        <div class="task-header">
          <span class="task-name">{formatTaskId(task.task_id)}</span>
          <span class="task-percentage">
            {task.progress >= 0 ? Math.round(task.progress * 100) : 0}%
          </span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-fill"
            style="width: {Math.max(0, task.progress * 100)}%; background-color: {getProgressColor(
              task.progress
            )}"
          ></div>
        </div>
        <div class="task-message">
          {task.message}
        </div>
        {#if task.error}
          <div class="task-error">
            Error: {task.error}
          </div>
        {/if}
      </div>
    {/each}
  </div>
{/if}

<style>
  .task-progress-container {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 300px;
    background: var(--surface);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    z-index: 100;
  }

  .task-progress-container h4 {
    margin: 0 0 0.75rem 0;
    font-size: 0.875rem;
    color: var(--text-primary);
  }

  .task-item {
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-color);
  }

  .task-item:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
  }

  .task-item.error {
    color: var(--error-color);
  }

  .task-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.375rem;
  }

  .task-name {
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
  }

  .task-percentage {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-left: 0.5rem;
  }

  .progress-bar {
    width: 100%;
    height: 4px;
    background: var(--border-color);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 0.375rem;
  }

  .progress-fill {
    height: 100%;
    transition:
      width 0.3s ease,
      background-color 0.3s ease;
    border-radius: 2px;
  }

  .task-message {
    font-size: 0.75rem;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .task-error {
    font-size: 0.75rem;
    color: var(--error-color);
    margin-top: 0.25rem;
  }
</style>
