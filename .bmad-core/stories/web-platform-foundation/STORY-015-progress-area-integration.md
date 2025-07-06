# Story: Progress Area Integration

**Story ID**: STORY-015  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 2 (Small)  
**Priority**: High  
**Status**: ✅ Completed

## Story Description
As a user, I need a unified progress and notification area in the right panel that builds upon the WebSocket task progress events from STORY-009 and integrates the existing TaskProgress component, showing me the status of all running tasks, file uploads, and system notifications in one place, allowing me to track multiple operations and respond to important events.

## Acceptance Criteria

### Functional Requirements
- [ ] Display all active tasks with progress bars
- [ ] Show file upload progress with percentage
- [ ] Queue notifications from various sources
- [ ] Allow dismissing completed notifications
- [ ] Show task details on hover/click
- [ ] Cancel running tasks when possible
- [ ] Group similar notifications
- [ ] Persist important notifications
- [ ] Clear all completed notifications
- [ ] Show estimated time remaining for tasks

### UI/UX Requirements
- [ ] Collapsible progress area to save space
- [ ] Visual distinction between task types
- [ ] Smooth progress bar animations
- [ ] Toast notifications for important events
- [ ] Sound alerts for critical notifications (optional)
- [ ] Notification badges when collapsed
- [ ] Auto-expand on new important notifications
- [ ] Compact view for many concurrent tasks

### Technical Requirements
- [ ] Integrate existing TaskProgress component
- [ ] Create notification queue system
- [ ] WebSocket event handling for progress
- [ ] Local storage for notification history
- [ ] Task cancellation API integration
- [ ] Memory-efficient for long-running tasks
- [ ] Handle connection loss gracefully

## Implementation Notes

### Progress Area Component
```svelte
<!-- src/lib/components/progress/ProgressArea.svelte -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import TaskProgress from './TaskProgress.svelte';
  import NotificationItem from './NotificationItem.svelte';
  import { taskStore } from '$lib/stores/tasks';
  import { notificationStore } from '$lib/stores/notifications';
  import { websocket } from '$lib/stores/websocket';
  import type { Task, Notification } from '$lib/types';
  
  export let expanded = true;
  
  let tasks: Task[] = [];
  let notifications: Notification[] = [];
  let hasUnread = false;
  
  // Subscribe to stores
  const unsubscribeTasks = taskStore.subscribe(value => {
    tasks = value.filter(t => t.status !== 'completed' || t.completedAt > Date.now() - 5000);
  });
  
  const unsubscribeNotifications = notificationStore.subscribe(value => {
    notifications = value;
    hasUnread = value.some(n => !n.read);
  });
  
  // WebSocket handlers
  function handleTaskProgress(event: CustomEvent) {
    taskStore.updateProgress(event.detail.taskId, event.detail);
  }
  
  function handleNotification(event: CustomEvent) {
    notificationStore.add(event.detail);
    if (event.detail.priority === 'high' && !expanded) {
      expanded = true;
    }
  }
  
  onMount(() => {
    websocket.addEventListener('task_progress', handleTaskProgress);
    websocket.addEventListener('notification', handleNotification);
  });
  
  onDestroy(() => {
    websocket.removeEventListener('task_progress', handleTaskProgress);
    websocket.removeEventListener('notification', handleNotification);
    unsubscribeTasks();
    unsubscribeNotifications();
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
  
  $: activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'pending');
  $: completedTasks = tasks.filter(t => t.status === 'completed' || t.status === 'failed');
</script>

<div class="progress-area" class:expanded>
  <div class="progress-header" on:click={toggleExpanded}>
    <h3>
      Progress & Notifications
      {#if hasUnread && !expanded}
        <span class="unread-badge">{notifications.filter(n => !n.read).length}</span>
      {/if}
    </h3>
    <div class="header-actions">
      {#if expanded && (completedTasks.length > 0 || notifications.length > 0)}
        <button class="clear-button" on:click|stopPropagation={clearCompleted}>
          Clear
        </button>
      {/if}
      <button class="toggle-button">
        <svg class="chevron" class:rotated={expanded} width="12" height="12">
          <path d="M2 4l4 4 4-4" stroke="currentColor" fill="none" />
        </svg>
      </button>
    </div>
  </div>
  
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
                <TaskProgress
                  {task}
                  on:cancel={() => cancelTask(task.id)}
                />
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
      {/div}
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
    padding: 12px 16px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    user-select: none;
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
  
  .toggle-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    color: var(--text-secondary);
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
```

### Enhanced Task Progress Component
```svelte
<!-- Update src/lib/components/progress/TaskProgress.svelte -->
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
        <button class="cancel-button" on:click={() => dispatch('cancel')}>
          ✕
        </button>
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
```

### Notification Store
```typescript
// src/lib/stores/notifications.ts
import { writable } from 'svelte/store';
import type { Notification } from '$lib/types';

function createNotificationStore() {
  const { subscribe, update } = writable<Notification[]>([]);
  
  return {
    subscribe,
    
    add(notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) {
      const newNotification: Notification = {
        ...notification,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        read: false
      };
      
      update(notifications => {
        // Limit to 50 most recent
        const updated = [newNotification, ...notifications];
        return updated.slice(0, 50);
      });
      
      // Auto-dismiss low priority after 5 seconds
      if (notification.priority === 'low') {
        setTimeout(() => {
          this.dismiss(newNotification.id);
        }, 5000);
      }
    },
    
    dismiss(id: string) {
      update(notifications => 
        notifications.filter(n => n.id !== id)
      );
    },
    
    markRead(id: string) {
      update(notifications =>
        notifications.map(n => 
          n.id === id ? { ...n, read: true } : n
        )
      );
    },
    
    markAllRead() {
      update(notifications =>
        notifications.map(n => ({ ...n, read: true }))
      );
    },
    
    clearRead() {
      update(notifications =>
        notifications.filter(n => !n.read)
      );
    }
  };
}

export const notificationStore = createNotificationStore();
```

### Task Store
```typescript
// src/lib/stores/tasks.ts
import { writable } from 'svelte/store';
import type { Task } from '$lib/types';
import { api } from '$lib/api/client';

function createTaskStore() {
  const { subscribe, update } = writable<Task[]>([]);
  
  return {
    subscribe,
    
    add(task: Omit<Task, 'id' | 'createdAt' | 'status'>) {
      const newTask: Task = {
        ...task,
        id: crypto.randomUUID(),
        createdAt: Date.now(),
        status: 'pending',
        progress: 0
      };
      
      update(tasks => [...tasks, newTask]);
      return newTask.id;
    },
    
    updateProgress(taskId: string, progress: Partial<Task>) {
      update(tasks =>
        tasks.map(t => 
          t.id === taskId ? { ...t, ...progress } : t
        )
      );
    },
    
    async cancel(taskId: string) {
      try {
        await api.post(`/tasks/${taskId}/cancel`);
        this.updateProgress(taskId, { 
          status: 'cancelled',
          completedAt: Date.now()
        });
      } catch (error) {
        console.error('Failed to cancel task:', error);
      }
    },
    
    clearCompleted() {
      update(tasks =>
        tasks.filter(t => 
          t.status === 'running' || 
          t.status === 'pending' ||
          (t.completedAt && t.completedAt > Date.now() - 5000)
        )
      );
    }
  };
}

export const taskStore = createTaskStore();
```

### Type Definitions
```typescript
// Add to src/lib/types/index.ts
export interface Task {
  id: string;
  name: string;
  type: 'upload' | 'download' | 'generation' | 'training' | 'processing' | 'export';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress?: number;
  details?: string;
  createdAt: number;
  completedAt?: number;
  estimatedTimeRemaining?: number;
  cancellable?: boolean;
  error?: string;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;
  priority: 'low' | 'medium' | 'high';
  timestamp: number;
  read: boolean;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}
```

### Integration with Layout
```svelte
<!-- Update right panel in main layout -->
<div slot="right">
  <PropertiesInspector selection={currentSelection} />
  <ProgressArea />
</div>
```

### WebSocket Integration
```typescript
// Add to websocket message handlers
websocket.on('task_progress', (data) => {
  taskStore.updateProgress(data.task_id, {
    progress: data.progress,
    status: data.status,
    details: data.message,
    estimatedTimeRemaining: data.eta
  });
});

websocket.on('task_complete', (data) => {
  taskStore.updateProgress(data.task_id, {
    status: 'completed',
    progress: 100,
    completedAt: Date.now()
  });
  
  notificationStore.add({
    type: 'success',
    title: 'Task Completed',
    message: data.message,
    priority: 'medium'
  });
});

websocket.on('task_failed', (data) => {
  taskStore.updateProgress(data.task_id, {
    status: 'failed',
    error: data.error,
    completedAt: Date.now()
  });
  
  notificationStore.add({
    type: 'error',
    title: 'Task Failed',
    message: data.error,
    priority: 'high'
  });
});
```

## Dependencies
- WebSocket connection for real-time updates
- Task management API endpoints
- Notification system design
- TaskProgress component (already exists)

## Testing Criteria
- [ ] Progress updates in real-time
- [ ] Multiple concurrent tasks display correctly
- [ ] Notifications appear and dismiss properly
- [ ] Task cancellation works
- [ ] Area expands/collapses smoothly
- [ ] Unread badge shows correct count
- [ ] Memory usage stays reasonable with many tasks
- [ ] Reconnection handles progress updates

## Definition of Done
- [ ] Progress area component implemented
- [ ] Task and notification stores created
- [ ] WebSocket integration complete
- [ ] Auto-expand for important notifications
- [ ] Task cancellation functional
- [ ] Visual design matches app theme
- [ ] Performance optimized for many tasks
- [ ] Documentation updated

## Story Links
- **Depends On**: STORY-005 (WebSocket Service), STORY-009 (WebSocket Client)
- **Blocks**: None
- **Related PRD**: PRD-001-web-platform-foundation