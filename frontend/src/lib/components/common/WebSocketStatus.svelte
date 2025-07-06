<script lang="ts">
  import { wsState } from '$lib/stores';
  import { websocket } from '$lib/services/websocket';

  // Reconnect manually
  function handleReconnect() {
    const currentProjectId = sessionStorage.getItem('current-project-id');
    if (currentProjectId) {
      websocket.connect(currentProjectId);
    }
  }

  // Format last heartbeat time
  function formatHeartbeat(date: Date | null): string {
    if (!date) return 'Never';

    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  }

  $: heartbeatText = formatHeartbeat($wsState.lastHeartbeat);
</script>

<div class="websocket-status" class:error={$wsState.error}>
  {#if $wsState.connected}
    <span class="status-dot connected"></span>
    <span class="status-text">Connected</span>
    <span class="heartbeat" title="Last heartbeat">♥ {heartbeatText}</span>
  {:else if $wsState.connecting}
    <span class="status-dot connecting"></span>
    <span class="status-text">Connecting...</span>
    {#if $wsState.reconnectAttempts > 0}
      <span class="attempts">(Attempt {$wsState.reconnectAttempts})</span>
    {/if}
  {:else}
    <span class="status-dot disconnected"></span>
    <span class="status-text">Disconnected</span>
    <button class="reconnect-btn" on:click={handleReconnect}> Reconnect </button>
  {/if}

  {#if $wsState.error}
    <span class="error-text" title={$wsState.error}>!</span>
  {/if}
</div>

<style>
  .websocket-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    padding: 0.25rem 0.75rem;
    background: var(--surface);
    border-radius: 1rem;
    transition: all 0.2s;
  }

  .websocket-status.error {
    background: color-mix(in srgb, var(--error-color) 20%, var(--surface));
  }

  .status-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    transition: all 0.2s;
  }

  .status-dot.connected {
    background: var(--success-color);
    box-shadow: 0 0 4px var(--success-color);
  }

  .status-dot.connecting {
    background: var(--warning-color);
    animation: pulse 1.5s infinite;
  }

  .status-dot.disconnected {
    background: var(--text-secondary);
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  .status-text {
    color: var(--text-primary);
    font-weight: 500;
  }

  .heartbeat {
    color: var(--text-secondary);
    font-size: 0.7rem;
  }

  .attempts {
    color: var(--text-secondary);
    font-size: 0.7rem;
  }

  .reconnect-btn {
    padding: 0.125rem 0.5rem;
    font-size: 0.7rem;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .reconnect-btn:hover {
    background: color-mix(in srgb, var(--primary-color) 85%, black);
    transform: translateY(-1px);
  }

  .error-text {
    color: var(--error-color);
    font-weight: bold;
    font-size: 0.875rem;
    cursor: help;
  }
</style>
