<script lang="ts">
  import { onMount } from 'svelte';
  import { storyVisualizationStore } from '../stores/story-visualization-store';
  import { assetsStore } from '../stores/assets-store';
  import type { SceneGridItem, StoryVisualizationConfig } from '../types/story-visualization';
  import { format } from 'date-fns';

  export let projectId: string;

  let scenes: SceneGridItem[] = [];
  let filteredScenes: SceneGridItem[] = [];
  let loading = true;
  let error: string | null = null;

  let config: StoryVisualizationConfig = {
    viewType: 'grid',
    filters: {},
    sortBy: 'position',
    sortOrder: 'asc',
    showGrid: true,
    showCharacterArcs: false,
    showBeats: true,
    showAssetUsage: true
  };

  let searchTerm = '';
  let selectedFilter = 'all';
  let selectedSort = 'position';

  $: if (projectId) {
    loadScenes();
  }

  $: filteredScenes = filterAndSortScenes(scenes, searchTerm, config);

  async function loadScenes() {
    try {
      loading = true;
      error = null;
      
      const [sceneData, assetUsage] = await Promise.all([
        storyVisualizationStore.loadTimelineData(projectId),
        storyVisualizationStore.getAssetUsage(projectId)
      ]);
      
      // Transform timeline data to grid items
      scenes = sceneData.map(scene => ({
        id: scene.id,
        title: scene.title,
        beat: scene.beatType,
        characters: scene.characters,
        location: scene.metadata.location,
        duration: scene.duration,
        emotionalIntensity: scene.emotionalIntensity,
        assetCount: scene.assetCount,
        thumbnail: scene.thumbnail,
        status: scene.metadata.status || 'planned'
      }));
      
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load scenes';
    } finally {
      loading = false;
    }
  }

  function filterAndSortScenes(
    items: SceneGridItem[],
    search: string,
    cfg: StoryVisualizationConfig
  ): SceneGridItem[] {
    let filtered = items;

    // Search filter
    if (search) {
      const searchLower = search.toLowerCase();
      filtered = filtered.filter(scene => 
        scene.title.toLowerCase().includes(searchLower) ||
        scene.characters.some(c => c.toLowerCase().includes(searchLower)) ||
        scene.location.toLowerCase().includes(searchLower) ||
        scene.beat.toLowerCase().includes(searchLower)
      );
    }

    // Config filters
    if (cfg.filters.characters?.length) {
      filtered = filtered.filter(scene => 
        scene.characters.some(c => cfg.filters.characters!.includes(c))
      );
    }

    if (cfg.filters.beats?.length) {
      filtered = filtered.filter(scene => cfg.filters.beats!.includes(scene.beat));
    }

    if (cfg.filters.status?.length) {
      filtered = filtered.filter(scene => cfg.filters.status!.includes(scene.status));
    }

    if (cfg.filters.intensityRange) {
      const [min, max] = cfg.filters.intensityRange;
      filtered = filtered.filter(scene => 
        scene.emotionalIntensity >= min && scene.emotionalIntensity <= max
      );
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      let comparison = 0;
      
      switch (cfg.sortBy) {
        case 'position':
          comparison = a.id.localeCompare(b.id);
          break;
        case 'duration':
          comparison = b.duration - a.duration;
          break;
        case 'intensity':
          comparison = b.emotionalIntensity - a.emotionalIntensity;
          break;
        case 'alphabetical':
          comparison = a.title.localeCompare(b.title);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
      }
      
      return cfg.sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }

  function getStatusColor(status: string): string {
    const colors = {
      planned: '#6b7280',
      generated: '#3b82f6',
      approved: '#10b981',
      needs_revision: '#ef4444'
    };
    return colors[status as keyof typeof colors] || '#6b7280';
  }

  function getIntensityColor(intensity: number): string {
    if (intensity >= 0.8) return '#dc2626';
    if (intensity >= 0.6) return '#ea580c';
    if (intensity >= 0.4) return '#f59e0b';
    if (intensity >= 0.2) return '#84cc16';
    return '#22c55e';
  }

  function handleSceneClick(scene: SceneGridItem) {
    // Emit event for parent to handle
    const event = new CustomEvent('sceneSelected', { detail: scene });
    dispatchEvent(event);
  }

  function handleFilterChange(type: string, value: string[]) {
    config = {
      ...config,
      filters: {
        ...config.filters,
        [type]: value
      }
    };
  }

  function toggleSortOrder() {
    config = {
      ...config,
      sortOrder: config.sortOrder === 'asc' ? 'desc' : 'asc'
    };
  }
</script>

<div class="scene-grid-container">
  <!-- Header with controls -->
  <div class="grid-header">
    <div class="search-section">
      <input
        type="text"
        bind:value={searchTerm}
        placeholder="Search scenes, characters, locations..."
        class="search-input"
      />
    </div>

    <div class="controls-section">
      <div class="filter-group">
        <select bind:value={selectedFilter} on:change={(e) => handleFilterChange('status', [e.target.value])}
          class="filter-select"
        >
          <option value="all">All Status</option>
          <option value="planned">Planned</option>
          <option value="generated">Generated</option>
          <option value="approved">Approved</option>
          <option value="needs_revision">Needs Revision</option>
        </select>

        <select bind:value={selectedSort} on:change={(e) => config = { ...config, sortBy: e.target.value as any }}
          class="filter-select"
        >
          <option value="position">Position</option>
          <option value="duration">Duration</option>
          <option value="intensity">Intensity</option>
          <option value="alphabetical">Alphabetical</option>
        </select>

        <button on:click={toggleSortOrder} class="sort-toggle"
          title="Toggle sort order"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            {#if config.sortOrder === 'asc'}
              <polyline points="6 9 12 15 18 9" />
            {:else}
              <polyline points="18 15 12 9 6 15" />
            {/if}
          </svg>
        </button>
      </div>
    </div>
  </div>

  {#if loading}
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Loading scenes...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <p>{error}</p>
      <button on:click={loadScenes} class="retry-btn">Retry</button>
    </div>
  {:else if filteredScenes.length === 0}
    <div class="empty-state">
      <p>No scenes found</p>
      {#if searchTerm || selectedFilter !== 'all'}
        <button on:click={() => { searchTerm = ''; selectedFilter = 'all'; }} class="clear-btn">Clear filters</button>
      {/if}
    </div>
  {:else}
    <!-- Stats summary -->
    <div class="stats-summary">
      <div class="stat-card">
        <span class="stat-number">{filteredScenes.length}</span>
        <span class="stat-label">Total Scenes</span>
      </div>
      <div class="stat-card">
        <span class="stat-number">{filteredScenes.reduce((sum, s) => sum + s.duration, 0)}min</span>
        <span class="stat-label">Total Duration</span>
      </div>
      <div class="stat-card">
        <span class="stat-number">{new Set(filteredScenes.flatMap(s => s.characters)).size}</span>
        <span class="stat-label">Unique Characters</span>
      </div>
      <div class="stat-card">
        <span class="stat-number">{filteredScenes.reduce((sum, s) => sum + s.assetCount, 0)}</span>
        <span class="stat-label">Total Assets</span>
      </div>
    </div>

    <!-- Scene grid -->
    <div class="scene-grid">
      {#each filteredScenes as scene}
        <div 
          class="scene-card"
          class:has-thumbnail={scene.thumbnail}
          on:click={() => handleSceneClick(scene)}
        >
          <!-- Thumbnail -->
          {#if scene.thumbnail}
            <div class="scene-thumbnail"
              style="background-image: url({scene.thumbnail})"
            >
              <div class="status-badge" style="background-color: {getStatusColor(scene.status)}">{scene.status}</div>
            </div>
          {/if}

          <!-- Content -->
          <div class="scene-content">
            <div class="scene-header">
              <h3 class="scene-title">{scene.title}</h3>
              <div class="scene-beat">{scene.beat}</div>
            </div>

            <div class="scene-details">
              <div class="detail-row">
                <span class="detail-label">Location:</span>
                <span class="detail-value">{scene.location}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Duration:</span>
                <span class="detail-value">{scene.duration}min</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Characters:</span>
                <span class="detail-value characters">{scene.characters.join(', ')}</span>
              </div>
            </div>

            <div class="scene-metrics">
              <div class="metric intensity-metric">
                <span class="metric-label">Intensity</span>
                <div class="intensity-bar">
                  <div 
                    class="intensity-fill"
                    style="width: {scene.emotionalIntensity * 100}%; background-color: {getIntensityColor(scene.emotionalIntensity)}"
                  ></div>
                </div>
                <span class="intensity-value">{Math.round(scene.emotionalIntensity * 100)}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">Assets</span>
                <span class="metric-value">{scene.assetCount}</span>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .scene-grid-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .grid-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
    gap: 1rem;
    flex-wrap: wrap;
  }

  .search-section {
    flex: 1;
    min-width: 200px;
  }

  .search-input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .controls-section {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .filter-group {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .filter-select {
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .sort-toggle {
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s;
  }

  .sort-toggle:hover {
    background: var(--bg-tertiary);
  }

  .loading-state,
  .error-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    color: var(--text-secondary);
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .retry-btn,
  .clear-btn {
    padding: 0.5rem 1rem;
    margin-top: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
  }

  .stats-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
  }

  .stat-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
  }

  .stat-number {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--accent-color);
  }

  .stat-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
  }

  .scene-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    padding: 1rem;
    overflow-y: auto;
  }

  .scene-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.2s;
  }

  .scene-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .scene-thumbnail {
    position: relative;
    height: 150px;
    background-size: cover;
    background-position: center;
  }

  .status-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    color: white;
  }

  .scene-content {
    padding: 1rem;
  }

  .scene-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
  }

  .scene-title {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0;
  }

  .scene-beat {
    padding: 0.25rem 0.5rem;
    background: var(--accent-color);
    color: white;
    border-radius: 0.25rem;
    font-size: 0.75rem;
  }

  .scene-details {
    margin-bottom: 1rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
    font-size: 0.875rem;
  }

  .detail-label {
    color: var(--text-secondary);
  }

  .detail-value {
    color: var(--text-primary);
  }

  .characters {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .scene-metrics {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .metric {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .metric-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .metric-value {
    font-size: 1rem;
    font-weight: 600;
  }

  .intensity-metric {
    flex: 1;
    align-items: flex-start;
  }

  .intensity-bar {
    width: 100%;
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }

  .intensity-fill {
    height: 100%;
    transition: width 0.3s ease;
  }

  .intensity-value {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  @media (max-width: 768px) {
    .grid-header {
      flex-direction: column;
      align-items: stretch;
    }

    .search-section,
    .controls-section {
      width: 100%;
    }

    .scene-grid {
      grid-template-columns: 1fr;
    }
  }
</style>