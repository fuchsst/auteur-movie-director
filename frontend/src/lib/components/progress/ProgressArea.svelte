<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import TaskProgress from './TaskProgress.svelte';
  import NotificationItem from './NotificationItem.svelte';
  import { taskStore } from '$lib/stores/tasks';
  import { notificationStore } from '$lib/stores/notifications';
  import { websocket } from '$lib/services/websocket';
  import { MessageType } from '$lib/types/websocket';
  import type { Task, Notification } from '$lib/types';
  import type { TaskProgressPayload } from '$lib/types/websocket';

  export let expanded = true;

  let tasks: Task[] = [];
  let notifications: Notification[] = [];
  let hasUnread = false;

  // Subscribe to stores
  const unsubscribeTasks = taskStore.subscribe((value) => {
    tasks = value.filter((t) => t.status !== 'completed' || t.completedAt > Date.now() - 5000);
  });

  const unsubscribeNotifications = notificationStore.subscribe((value) => {
    notifications = value;
    hasUnread = value.some((n) => !n.read);
  });

  // WebSocket handlers
  function handleTaskProgress(data: TaskProgressPayload) {
    taskStore.updateProgress(data.task_id, {
      progress: data.progress * 100, // Convert to percentage
      status: 'running',
      details: data.message,
      estimatedTimeRemaining: data.result?.eta
    });
  }

  function handleTaskComplete(data: TaskProgressPayload) {
    taskStore.updateProgress(data.task_id, {
      status: 'completed',
      progress: 100,
      completedAt: Date.now()
    });

    notificationStore.add({
      type: 'success',
      title: 'Task Completed',
      message: data.message || 'Task completed successfully',
      priority: 'medium'
    });
  }

  function handleTaskError(data: TaskProgressPayload) {
    taskStore.updateProgress(data.task_id, {
      status: 'failed',
      error: data.error,
      completedAt: Date.now()
    });

    notificationStore.add({
      type: 'error',
      title: 'Task Failed',
      message: data.error || 'Task failed with an error',
      priority: 'high'
    });
  }

  let unsubscribeWebSocket: (() => void)[] = [];

  onMount(() => {
    // Subscribe to WebSocket events
    unsubscribeWebSocket = [
      websocket.on(MessageType.TASK_PROGRESS, handleTaskProgress),
      websocket.on(MessageType.TASK_COMPLETE, handleTaskComplete),
      websocket.on(MessageType.TASK_ERROR, handleTaskError)
    ];
  });

  onDestroy(() => {
    unsubscribeTasks();
    unsubscribeNotifications();
    unsubscribeWebSocket.forEach((unsub) => unsub());
  });

  function toggleExpanded() {
    expanded = !expanded;
    if (expanded) {
      notificationStore.markAllRead();
    }
  }

  function clearCompleted() {
    taskStore.clearCompleted();
    notificationStore.clearRead();
  }

  function cancelTask(taskId: string) {
    taskStore.cancel(taskId);
  }

  $: activeTasks = tasks.filter((t) => t.status === 'running' || t.status === 'pending');
  $: completedTasks = tasks.filter((t) => t.status === 'completed' || t.status === 'failed');
</script>

<div class="progress-area" class:expanded>
  <button class="progress-header" on:click={toggleExpanded} type="button">
    <h3>
      Progress & Notifications
      {#if hasUnread && !expanded}
        <span class="unread-badge">{notifications.filter((n) => !n.read).length}</span>
      {/if}
    </h3>
    <div class="header-actions">
      {#if expanded && (completedTasks.length > 0 || notifications.length > 0)}
        <button class="clear-button" on:click|stopPropagation={clearCompleted} type="button">
          Clear
        </button>
      {/if}
      <span class="toggle-icon">
        <svg class="chevron" class:rotated={expanded} width="12" height="12">
          <path d="M2 4l4 4 4-4" stroke="currentColor" fill="none" />
        </svg>
      </span>
    </div>
  </button>

  {#if expanded}
    <div class="progress-content">
      {#if activeTasks.length === 0 && notifications.length === 0}
        <div class="empty-state">
          <p>No active tasks or notifications</p>
        </div>
      {:else}
        <!-- Active Tasks -->
        {#if activeTasks.length > 0}
          <div class="section">
            <h4>Active Tasks ({activeTasks.length})</h4>
            <div class="task-list">
              {#each activeTasks as task (task.id)}
                <TaskProgress {task} on:cancel={() => cancelTask(task.id)} />
              {/each}
            </div>
          </div>
        {/if}

        <!-- Recent Completed -->
        {#if completedTasks.length > 0}
          <div class="section">
            <h4>Recently Completed</h4>
            <div class="task-list completed">
              {#each completedTasks as task (task.id)}
                <TaskProgress {task} compact />
              {/each}
            </div>
          </div>
        {/if}

        <!-- Notifications -->
        {#if notifications.length > 0}
          <div class="section">
            <h4>Notifications</h4>
            <div class="notification-list">
              {#each notifications as notification (notification.id)}
                <NotificationItem
                  {notification}
                  on:dismiss={() => notificationStore.dismiss(notification.id)}
                />
              {/each}
            </div>
          </div>
        {/if}
      {/if}
    </div>
  {/if}
</div>

<style>
  .progress-area {
    border-top: 1px solid var(--border-color);
    background: var(--bg-secondary);
    transition: all 0.3s ease;
  }

  .progress-header {
    width: 100%;
    padding: 12px 16px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    user-select: none;
    background: transparent;
    border: none;
    text-align: left;
  }

  .progress-header:hover {
    background: var(--bg-hover);
  }

  .progress-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .unread-badge {
    background: var(--color-primary);
    color: white;
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 10px;
    font-weight: bold;
  }

  .header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .clear-button {
    padding: 4px 8px;
    font-size: 12px;
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .clear-button:hover {
    background: var(--bg-hover);
    border-color: var(--border-hover);
  }

  .toggle-icon {
    padding: 4px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
  }

  .chevron {
    transition: transform 0.2s;
  }

  .chevron.rotated {
    transform: rotate(180deg);
  }

  .progress-content {
    max-height: 400px;
    overflow-y: auto;
    padding: 0 16px 16px;
  }

  .section {
    margin-bottom: 20px;
  }

  .section:last-child {
    margin-bottom: 0;
  }

  .section h4 {
    margin: 0 0 8px 0;
    font-size: 12px;
    text-transform: uppercase;
    color: var(--text-secondary);
    font-weight: 500;
  }

  .task-list,
  .notification-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .task-list.completed {
    opacity: 0.7;
  }

  .empty-state {
    text-align: center;
    padding: 24px;
    color: var(--text-secondary);
  }

  .empty-state p {
    margin: 0;
    font-size: 13px;
  }
</style>
