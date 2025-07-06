<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { Notification } from '$lib/types';

  export let notification: Notification;

  const dispatch = createEventDispatcher();

  function getIcon(type: string): string {
    const icons = {
      info: 'ℹ️',
      success: '✅',
      warning: '⚠️',
      error: '❌'
    };
    return icons[type] || 'ℹ️';
  }

  function formatTime(timestamp: number): string {
    const now = Date.now();
    const diff = now - timestamp;

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return new Date(timestamp).toLocaleDateString();
  }
</script>

<div class="notification-item" class:unread={!notification.read}>
  <span class="notification-icon">{getIcon(notification.type)}</span>

  <div class="notification-content">
    <div class="notification-title">{notification.title}</div>
    {#if notification.message}
      <div class="notification-message">{notification.message}</div>
    {/if}

    {#if notification.actions && notification.actions.length > 0}
      <div class="notification-actions">
        {#each notification.actions as action}
          <button class="action-button {action.style || 'secondary'}" on:click={action.action}>
            {action.label}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <div class="notification-meta">
    <span class="notification-time">{formatTime(notification.timestamp)}</span>
    <button class="dismiss-button" on:click={() => dispatch('dismiss')}> × </button>
  </div>
</div>

<style>
  .notification-item {
    display: flex;
    gap: 8px;
    padding: 10px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    border: 1px solid var(--border-color);
    transition: all 0.2s;
  }

  .notification-item.unread {
    border-color: var(--color-primary-dim);
    background: var(--bg-tertiary-light);
  }

  .notification-icon {
    font-size: 16px;
    flex-shrink: 0;
    margin-top: 2px;
  }

  .notification-content {
    flex: 1;
    min-width: 0;
  }

  .notification-title {
    font-size: 13px;
    font-weight: 500;
    line-height: 1.4;
  }

  .notification-message {
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 2px;
    line-height: 1.4;
  }

  .notification-actions {
    display: flex;
    gap: 6px;
    margin-top: 6px;
  }

  .action-button {
    padding: 4px 8px;
    font-size: 11px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .action-button.primary {
    background: var(--color-primary);
    color: white;
  }

  .action-button.primary:hover {
    background: var(--color-primary-hover);
  }

  .action-button.secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }

  .action-button.secondary:hover {
    background: var(--bg-hover);
    border-color: var(--border-hover);
  }

  .action-button.danger {
    background: var(--color-error);
    color: white;
  }

  .action-button.danger:hover {
    background: var(--color-error-hover);
  }

  .notification-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
  }

  .notification-time {
    font-size: 11px;
    color: var(--text-tertiary);
    white-space: nowrap;
  }

  .dismiss-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: var(--text-secondary);
    border-radius: 3px;
    transition: all 0.2s;
  }

  .dismiss-button:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
</style>
