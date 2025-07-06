<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { takesApi, type TakeMetadata } from '$lib/api/takes';
  import { formatRelativeTime } from '$lib/utils/date';
  import { formatBytes } from '$lib/utils/format';
  import Icon from '$lib/components/common/Icon.svelte';
  import { progressStore } from '$lib/stores/progress';

  export let projectId: string;
  export let shotId: string;
  export let compact = false;

  const dispatch = createEventDispatcher<{
    select: { take: TakeMetadata };
    generate: void;
    activateChanged: { takeId: string };
  }>();

  let takes: TakeMetadata[] = [];
  let activeTakeId: string | undefined;
  let loading = true;
  let error: string | null = null;
  let selectedTakeId: string | null = null;

  onMount(() => {
    loadTakes();
  });

  async function loadTakes() {
    try {
      loading = true;
      error = null;
      const response = await takesApi.listTakes(projectId, shotId);
      takes = response.takes;
      activeTakeId = response.activeTakeId;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load takes';
      console.error('Error loading takes:', e);
    } finally {
      loading = false;
    }
  }

  function selectTake(take: TakeMetadata) {
    selectedTakeId = take.id;
    dispatch('select', { take });
  }

  async function setActiveTake(takeId: string) {
    try {
      await takesApi.setActiveTake(projectId, shotId, takeId);
      activeTakeId = takeId;
      dispatch('activateChanged', { takeId });
      progressStore.addNotification({
        message: `Set active take to ${takeId}`,
        type: 'success'
      });
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to set active take';
      progressStore.addNotification({
        message,
        type: 'error'
      });
    }
  }

  async function deleteTake(take: TakeMetadata) {
    if (!confirm(`Delete ${take.id}? This action cannot be undone.`)) {
      return;
    }

    try {
      const response = await takesApi.deleteTake(projectId, shotId, take.id);

      // Remove from list
      takes = takes.filter((t) => t.id !== take.id);

      // Update active take if needed
      if (response.newActiveTakeId) {
        activeTakeId = response.newActiveTakeId;
      }

      progressStore.addNotification({
        message: response.message,
        type: 'success'
      });
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to delete take';
      progressStore.addNotification({
        message,
        type: 'error'
      });
    }
  }

  async function exportTake(take: TakeMetadata) {
    try {
      const response = await takesApi.exportTake(projectId, shotId, {
        takeId: take.id,
        includeMetadata: true
      });

      progressStore.addNotification({
        message: `Exported to ${response.exportPath}`,
        type: 'success'
      });
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to export take';
      progressStore.addNotification({
        message,
        type: 'error'
      });
    }
  }

  function generateNewTake() {
    dispatch('generate');
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'complete':
        return 'check-circle';
      case 'generating':
        return 'loader';
      case 'failed':
        return 'x-circle';
      default:
        return 'circle';
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'complete':
        return 'text-green-500';
      case 'generating':
        return 'text-blue-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  }
</script>

<div class="takes-gallery" class:compact>
  <div class="takes-header">
    <h3>Takes ({takes.length})</h3>
    <button class="btn-primary" on:click={generateNewTake}>
      <Icon name="plus" size={16} />
      New Take
    </button>
  </div>

  {#if loading}
    <div class="loading">
      <Icon name="loader" size={24} class="animate-spin" />
      <span>Loading takes...</span>
    </div>
  {:else if error}
    <div class="error">
      <Icon name="alert-circle" size={20} />
      <span>{error}</span>
      <button class="btn-secondary" on:click={loadTakes}>Retry</button>
    </div>
  {:else if takes.length === 0}
    <div class="empty">
      <Icon name="film" size={48} />
      <p>No takes yet</p>
      <button class="btn-primary" on:click={generateNewTake}> Generate First Take </button>
    </div>
  {:else}
    <div class="takes-grid" class:compact>
      {#each takes as take (take.id)}
        <div
          class="take-item"
          class:active={take.id === activeTakeId}
          class:selected={take.id === selectedTakeId}
          class:failed={take.status === 'failed'}
          on:click={() => selectTake(take)}
          role="button"
          tabindex="0"
          on:keypress={(e) => e.key === 'Enter' && selectTake(take)}
        >
          <div class="take-thumbnail">
            {#if take.thumbnailPath}
              <img
                src={takesApi.getThumbnailUrl(projectId, take.thumbnailPath)}
                alt={take.id}
                loading="lazy"
              />
            {:else}
              <div class="placeholder">
                <Icon name="film" size={32} />
              </div>
            {/if}

            {#if take.id === activeTakeId}
              <div class="active-badge" title="Active take">
                <Icon name="star" size={14} />
              </div>
            {/if}

            <div class="status-badge {getStatusColor(take.status)}" title={take.status}>
              <Icon name={getStatusIcon(take.status)} size={14} />
            </div>
          </div>

          <div class="take-info">
            <div class="take-id">{take.id}</div>
            <div class="take-meta">
              <span class="date">{formatRelativeTime(take.created)}</span>
              {#if take.fileSize}
                <span class="size">{formatBytes(take.fileSize)}</span>
              {/if}
              {#if take.resources?.quality}
                <span class="quality">{take.resources.quality}</span>
              {/if}
            </div>
            {#if take.error}
              <div class="error-message" title={take.error}>
                {take.error}
              </div>
            {/if}
          </div>

          <div class="take-actions" on:click|stopPropagation>
            {#if take.status === 'complete'}
              {#if take.id !== activeTakeId}
                <button
                  class="btn-icon"
                  title="Set as active"
                  on:click={() => setActiveTake(take.id)}
                >
                  <Icon name="star" size={16} />
                </button>
              {/if}
              <button class="btn-icon" title="Export" on:click={() => exportTake(take)}>
                <Icon name="download" size={16} />
              </button>
            {/if}
            <button class="btn-icon danger" title="Delete" on:click={() => deleteTake(take)}>
              <Icon name="trash-2" size={16} />
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .takes-gallery {
    display: flex;
    flex-direction: column;
    height: 100%;
    gap: 1rem;
  }

  .takes-gallery.compact {
    gap: 0.5rem;
  }

  .takes-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 0.5rem;
  }

  .takes-header h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .takes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
    overflow-y: auto;
    padding: 0.5rem;
  }

  .takes-grid.compact {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.5rem;
  }

  .take-item {
    background: var(--bg-secondary);
    border: 2px solid var(--border-color);
    border-radius: 0.5rem;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
  }

  .take-item:hover {
    border-color: var(--primary-color);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .take-item.active {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(255, 193, 7, 0.2);
  }

  .take-item.selected {
    border-color: var(--primary-color);
    background: var(--bg-primary);
  }

  .take-item.failed {
    opacity: 0.7;
  }

  .take-thumbnail {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: var(--bg-tertiary);
    overflow: hidden;
  }

  .take-thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .take-thumbnail .placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-tertiary);
  }

  .active-badge {
    position: absolute;
    top: 0.5rem;
    left: 0.5rem;
    background: var(--accent-color);
    color: var(--bg-primary);
    padding: 0.25rem;
    border-radius: 0.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .status-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    padding: 0.25rem;
    border-radius: 0.25rem;
    background: var(--bg-primary);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .take-info {
    padding: 0.75rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .take-id {
    font-weight: 500;
    color: var(--text-primary);
    font-size: 0.875rem;
  }

  .take-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .take-meta .quality {
    padding: 0.125rem 0.375rem;
    background: var(--bg-tertiary);
    border-radius: 0.25rem;
    font-weight: 500;
  }

  .error-message {
    font-size: 0.75rem;
    color: var(--error-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .take-actions {
    display: flex;
    gap: 0.25rem;
    padding: 0.5rem 0.75rem;
    background: var(--bg-tertiary);
    border-top: 1px solid var(--border-color);
  }

  .loading,
  .error,
  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    color: var(--text-secondary);
  }

  .error {
    color: var(--error-color);
  }

  .btn-icon {
    padding: 0.375rem;
    background: transparent;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    color: var(--text-secondary);
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .btn-icon:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .btn-icon.danger:hover {
    background: var(--error-color);
    color: white;
  }

  .btn-primary,
  .btn-secondary {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.2s;
    cursor: pointer;
    border: none;
  }

  .btn-primary {
    background: var(--primary-color);
    color: white;
  }

  .btn-primary:hover {
    background: var(--primary-hover);
  }

  .btn-secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }

  .btn-secondary:hover {
    background: var(--bg-tertiary);
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
