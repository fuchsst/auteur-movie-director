<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
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
  let filteredTakes: TakeMetadata[] = [];
  let activeTakeId: string | undefined;
  let loading = true;
  let error: string | null = null;
  let selectedTakeId: string | null = null;
  
  // View mode state
  type ViewMode = 'grid' | 'compare' | 'fullscreen';
  let viewMode: ViewMode = 'grid';
  let comparisonTakes: TakeMetadata[] = [];
  let fullscreenTake: TakeMetadata | null = null;
  
  // Filter state
  let filterStatus: 'all' | 'complete' | 'generating' | 'failed' = 'all';
  let filterQuality: 'all' | 'draft' | 'standard' | 'high' = 'all';
  let filterDateRange: { start: string; end: string } = { start: '', end: '' };
  let showFilters = false;
  
  // Keyboard navigation
  let focusedIndex = 0;
  let galleryElement: HTMLElement;

  onMount(() => {
    loadTakes();
    document.addEventListener('keydown', handleKeydown);
  });
  
  onDestroy(() => {
    document.removeEventListener('keydown', handleKeydown);
  });
  
  // Update filtered takes when takes or filters change
  $: {
    filteredTakes = filterTakes(takes);
    if (focusedIndex >= filteredTakes.length) {
      focusedIndex = Math.max(0, filteredTakes.length - 1);
    }
  }

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
  
  function filterTakes(allTakes: TakeMetadata[]): TakeMetadata[] {
    return allTakes.filter(take => {
      // Status filter
      if (filterStatus !== 'all' && take.status !== filterStatus) {
        return false;
      }
      
      // Quality filter
      if (filterQuality !== 'all' && take.resources?.quality !== filterQuality) {
        return false;
      }
      
      // Date range filter
      if (filterDateRange.start || filterDateRange.end) {
        const takeDate = new Date(take.created);
        if (filterDateRange.start && takeDate < new Date(filterDateRange.start)) {
          return false;
        }
        if (filterDateRange.end && takeDate > new Date(filterDateRange.end)) {
          return false;
        }
      }
      
      return true;
    });
  }
  
  function clearFilters() {
    filterStatus = 'all';
    filterQuality = 'all';
    filterDateRange = { start: '', end: '' };
  }
  
  function toggleComparison(take: TakeMetadata) {
    const index = comparisonTakes.findIndex(t => t.id === take.id);
    if (index >= 0) {
      comparisonTakes = comparisonTakes.filter(t => t.id !== take.id);
    } else if (comparisonTakes.length < 4) {
      comparisonTakes = [...comparisonTakes, take];
    }
    
    if (comparisonTakes.length >= 2 && viewMode === 'grid') {
      viewMode = 'compare';
    } else if (comparisonTakes.length < 2 && viewMode === 'compare') {
      viewMode = 'grid';
    }
  }
  
  function exitComparison() {
    viewMode = 'grid';
    comparisonTakes = [];
  }
  
  function openFullscreen(take: TakeMetadata) {
    fullscreenTake = take;
    viewMode = 'fullscreen';
  }
  
  function exitFullscreen() {
    viewMode = 'grid';
    fullscreenTake = null;
  }
  
  function handleKeydown(event: KeyboardEvent) {
    if (!galleryElement?.contains(document.activeElement)) return;
    
    switch (event.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault();
        focusedIndex = Math.min(focusedIndex + 1, filteredTakes.length - 1);
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault();
        focusedIndex = Math.max(focusedIndex - 1, 0);
        break;
      case ' ':
        event.preventDefault();
        if (filteredTakes[focusedIndex]) {
          setActiveTake(filteredTakes[focusedIndex].id);
        }
        break;
      case 'Delete':
        event.preventDefault();
        if (filteredTakes[focusedIndex]) {
          deleteTake(filteredTakes[focusedIndex]);
        }
        break;
      case 'Enter':
        event.preventDefault();
        if (filteredTakes[focusedIndex]) {
          openFullscreen(filteredTakes[focusedIndex]);
        }
        break;
      case 'Escape':
        event.preventDefault();
        if (viewMode === 'fullscreen') {
          exitFullscreen();
        } else if (viewMode === 'compare') {
          exitComparison();
        }
        break;
      case 'c':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          if (filteredTakes[focusedIndex]) {
            toggleComparison(filteredTakes[focusedIndex]);
          }
        }
        break;
    }
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

<div class="takes-gallery" class:compact bind:this={galleryElement} role="region" aria-label="Takes Gallery">
  <div class="takes-header">
    <div class="header-info">
      <h3>Takes ({filteredTakes.length}{filteredTakes.length !== takes.length ? ` of ${takes.length}` : ''})</h3>
      <div class="view-controls">
        <button 
          class="btn-icon" 
          class:active={viewMode === 'grid'}
          on:click={() => viewMode = 'grid'}
          title="Grid view"
          aria-label="Switch to grid view"
        >
          <Icon name="grid" size={16} />
        </button>
        <button 
          class="btn-icon" 
          class:active={viewMode === 'compare'}
          disabled={comparisonTakes.length < 2}
          on:click={() => viewMode = 'compare'}
          title="Compare view"
          aria-label="Switch to compare view"
        >
          <Icon name="columns" size={16} />
        </button>
        <button 
          class="btn-icon" 
          on:click={() => showFilters = !showFilters}
          class:active={showFilters}
          title="Toggle filters"
          aria-label="Toggle filter panel"
        >
          <Icon name="filter" size={16} />
        </button>
      </div>
    </div>
    <button class="btn-primary" on:click={generateNewTake}>
      <Icon name="plus" size={16} />
      New Take
    </button>
  </div>
  
  {#if showFilters}
    <div class="filters-panel" role="region" aria-label="Filters">
      <div class="filter-group">
        <label for="status-filter">Status:</label>
        <select id="status-filter" bind:value={filterStatus}>
          <option value="all">All</option>
          <option value="complete">Complete</option>
          <option value="generating">Generating</option>
          <option value="failed">Failed</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="quality-filter">Quality:</label>
        <select id="quality-filter" bind:value={filterQuality}>
          <option value="all">All</option>
          <option value="draft">Draft</option>
          <option value="standard">Standard</option>
          <option value="high">High</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="date-start">Date Range:</label>
        <div class="date-range">
          <input 
            id="date-start" 
            type="date" 
            bind:value={filterDateRange.start}
            aria-label="Start date"
          >
          <span>to</span>
          <input 
            type="date" 
            bind:value={filterDateRange.end}
            aria-label="End date"
          >
        </div>
      </div>
      <button class="btn-secondary small" on:click={clearFilters}>
        <Icon name="x" size={14} />
        Clear
      </button>
    </div>
  {/if}
  
  {#if viewMode === 'compare' && comparisonTakes.length >= 2}
    <div class="comparison-header">
      <h4>Comparing {comparisonTakes.length} takes</h4>
      <button class="btn-secondary" on:click={exitComparison}>
        <Icon name="x" size={16} />
        Exit Comparison
      </button>
    </div>
  {/if}

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
  {:else if filteredTakes.length === 0 && takes.length === 0}
    <div class="empty">
      <Icon name="film" size={48} />
      <p>No takes yet</p>
      <button class="btn-primary" on:click={generateNewTake}> Generate First Take </button>
    </div>
  {:else if filteredTakes.length === 0}
    <div class="empty">
      <Icon name="filter" size={48} />
      <p>No takes match your filters</p>
      <button class="btn-secondary" on:click={clearFilters}> Clear Filters </button>
    </div>
  {:else if viewMode === 'fullscreen' && fullscreenTake}
    <div class="fullscreen-modal" role="dialog" aria-label="Fullscreen take preview">
      <div class="fullscreen-content">
        <div class="fullscreen-header">
          <h3>{fullscreenTake.id}</h3>
          <button class="btn-icon" on:click={exitFullscreen} aria-label="Close fullscreen">
            <Icon name="x" size={24} />
          </button>
        </div>
        <div class="fullscreen-media">
          {#if fullscreenTake.filePath}
            <img
              src={takesApi.getMediaUrl(projectId, fullscreenTake.filePath)}
              alt={fullscreenTake.id}
            />
          {:else if fullscreenTake.thumbnailPath}
            <img
              src={takesApi.getThumbnailUrl(projectId, fullscreenTake.thumbnailPath)}
              alt={fullscreenTake.id}
            />
          {/if}
        </div>
        <div class="fullscreen-info">
          <div class="info-grid">
            <div class="info-item">
              <label>Created:</label>
              <span>{formatRelativeTime(fullscreenTake.created)}</span>
            </div>
            <div class="info-item">
              <label>Status:</label>
              <span class={getStatusColor(fullscreenTake.status)}>{fullscreenTake.status}</span>
            </div>
            {#if fullscreenTake.fileSize}
              <div class="info-item">
                <label>Size:</label>
                <span>{formatBytes(fullscreenTake.fileSize)}</span>
              </div>
            {/if}
            {#if fullscreenTake.resources?.quality}
              <div class="info-item">
                <label>Quality:</label>
                <span>{fullscreenTake.resources.quality}</span>
              </div>
            {/if}
          </div>
          {#if fullscreenTake.generationParams}
            <div class="generation-params">
              <h4>Generation Parameters</h4>
              <div class="params-grid">
                {#each Object.entries(fullscreenTake.generationParams) as [key, value]}
                  <div class="param-item">
                    <label>{key}:</label>
                    <span>{value}</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
        <div class="fullscreen-actions">
          {#if fullscreenTake.id !== activeTakeId}
            <button class="btn-primary" on:click={() => setActiveTake(fullscreenTake.id)}>
              <Icon name="star" size={16} />
              Set Active
            </button>
          {/if}
          <button class="btn-secondary" on:click={() => exportTake(fullscreenTake)}>
            <Icon name="download" size={16} />
            Export
          </button>
        </div>
      </div>
    </div>
  {:else if viewMode === 'compare'}
    <div class="comparison-view">
      <div class="comparison-grid">
        {#each comparisonTakes as take (take.id)}
          <div class="comparison-item">
            <div class="comparison-header">
              <h4>{take.id}</h4>
              <button class="btn-icon" on:click={() => toggleComparison(take)}>
                <Icon name="x" size={16} />
              </button>
            </div>
            <div class="comparison-media">
              {#if take.thumbnailPath}
                <img
                  src={takesApi.getThumbnailUrl(projectId, take.thumbnailPath)}
                  alt={take.id}
                  on:click={() => openFullscreen(take)}
                  role="button"
                  tabindex="0"
                />
              {:else}
                <div class="placeholder">
                  <Icon name="film" size={32} />
                </div>
              {/if}
            </div>
            <div class="comparison-info">
              <div class="take-meta">
                <span class="date">{formatRelativeTime(take.created)}</span>
                <span class="quality">{take.resources?.quality || 'N/A'}</span>
                <span class={getStatusColor(take.status)}>{take.status}</span>
              </div>
              {#if take.generationParams}
                <div class="params-summary">
                  <div>Model: {take.generationParams.model || 'N/A'}</div>
                  <div>Steps: {take.generationParams.steps || 'N/A'}</div>
                  <div>CFG: {take.generationParams.cfg || 'N/A'}</div>
                </div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {:else}
    <div class="takes-grid" class:compact role="grid" aria-label="Takes grid">
      {#each filteredTakes as take, index (take.id)}
        <div
          class="take-item"
          class:active={take.id === activeTakeId}
          class:selected={take.id === selectedTakeId}
          class:failed={take.status === 'failed'}
          class:focused={index === focusedIndex}
          class:in-comparison={comparisonTakes.some(t => t.id === take.id)}
          on:click={() => selectTake(take)}
          on:dblclick={() => openFullscreen(take)}
          role="gridcell"
          tabindex={index === focusedIndex ? 0 : -1}
          aria-label="Take {take.id}, status: {take.status}"
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
            
            {#if comparisonTakes.some(t => t.id === take.id)}
              <div class="comparison-badge" title="In comparison">
                <Icon name="columns" size={14} />
              </div>
            {/if}
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
              <button class="btn-icon" title="Compare" on:click={() => toggleComparison(take)}>
                <Icon name="columns" size={16} />
              </button>
              <button class="btn-icon" title="Fullscreen" on:click={() => openFullscreen(take)}>
                <Icon name="maximize" size={16} />
              </button>
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
  
  .header-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .takes-header h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .view-controls {
    display: flex;
    gap: 0.25rem;
  }
  
  .filters-panel {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border-radius: 0.5rem;
    border: 1px solid var(--border-color);
    align-items: end;
  }
  
  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 120px;
  }
  
  .filter-group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
  }
  
  .filter-group select,
  .filter-group input {
    padding: 0.375rem 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 0.25rem;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.875rem;
  }
  
  .date-range {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .date-range span {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  
  .comparison-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    background: var(--bg-secondary);
    border-radius: 0.375rem;
    border: 1px solid var(--border-color);
  }
  
  .comparison-header h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 500;
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
  
  .take-item.focused {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
  }
  
  .take-item.in-comparison {
    border-color: var(--accent-color);
    background: var(--bg-primary);
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
  
  .comparison-badge {
    position: absolute;
    top: 0.5rem;
    right: 2.5rem;
    background: var(--accent-color);
    color: var(--bg-primary);
    padding: 0.25rem;
    border-radius: 0.25rem;
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
  
  .btn-icon.active {
    background: var(--primary-color);
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
  
  .btn-secondary.small {
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
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
  
  /* Fullscreen Modal */
  .fullscreen-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .fullscreen-content {
    background: var(--bg-primary);
    border-radius: 0.5rem;
    max-width: 90vw;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .fullscreen-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .fullscreen-header h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
  }
  
  .fullscreen-media {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    min-height: 400px;
    padding: 1rem;
  }
  
  .fullscreen-media img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }
  
  .fullscreen-info {
    padding: 1rem;
    border-top: 1px solid var(--border-color);
    max-height: 200px;
    overflow-y: auto;
  }
  
  .info-grid,
  .params-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  
  .info-item,
  .param-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    background: var(--bg-secondary);
    border-radius: 0.25rem;
  }
  
  .info-item label,
  .param-item label {
    font-weight: 500;
    color: var(--text-secondary);
  }
  
  .generation-params h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .fullscreen-actions {
    display: flex;
    gap: 0.5rem;
    padding: 1rem;
    border-top: 1px solid var(--border-color);
    justify-content: flex-end;
  }
  
  /* Comparison View */
  .comparison-view {
    flex: 1;
    overflow: auto;
  }
  
  .comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    padding: 1rem;
  }
  
  .comparison-item {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    overflow: hidden;
  }
  
  .comparison-item .comparison-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-color);
  }
  
  .comparison-item h4 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .comparison-media {
    position: relative;
    aspect-ratio: 16 / 9;
    background: var(--bg-tertiary);
  }
  
  .comparison-media img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    cursor: pointer;
  }
  
  .comparison-info {
    padding: 0.75rem;
  }
  
  .params-summary {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
</style>
