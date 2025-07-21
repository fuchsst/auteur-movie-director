<script lang="ts">
  import { onMount } from 'svelte';
  import TimelineView from './TimelineView.svelte';
  import SceneGridView from './SceneGridView.svelte';
  import CharacterArcView from './CharacterArcView.svelte';
  import { storyVisualizationStore } from '../stores/story-visualization-store';
  import type { StoryVisualizationConfig } from '../types/story-visualization';

  export let projectId: string;

  let activeView: StoryVisualizationConfig['viewType'] = 'timeline';
  let config: StoryVisualizationConfig = {
    viewType: 'timeline',
    filters: {},
    sortBy: 'position',
    sortOrder: 'asc',
    showGrid: true,
    showCharacterArcs: true,
    showBeats: true,
    showAssetUsage: true
  };

  let selectedScene: any = null;
  let loading = true;
  let error: string | null = null;

  const views = [
    { id: 'timeline', name: 'Timeline', icon: '📊' },
    { id: 'grid', name: 'Grid', icon: '🏗️' },
    { id: 'character', name: 'Character Arcs', icon: '👥' },
    { id: 'analytics', name: 'Analytics', icon: '📈' }
  ];

  $: if (projectId) {
    loadVisualizationData();
  }

  async function loadVisualizationData() {
    try {
      loading = true;
      error = null;
      
      await Promise.all([
        storyVisualizationStore.loadTimelineData(projectId),
        storyVisualizationStore.getAnalytics(projectId),
        storyVisualizationStore.validateStructure(projectId)
      ]);
      
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load visualization data';
    } finally {
      loading = false;
    }
  }

  function handleViewChange(view: StoryVisualizationConfig['viewType']) {
    activeView = view;
    config = { ...config, viewType: view };
  }

  function handleSceneSelected(event: CustomEvent) {
    selectedScene = event.detail;
  }

  function handleConfigUpdate(newConfig: Partial<StoryVisualizationConfig>) {
    config = { ...config, ...newConfig };
  }

  function exportReport(format: 'pdf' | 'json') {
    storyVisualizationStore.exportStoryReport(projectId, format);
  }
</script>

<div class="story-visualization-container">
  <!-- Header -->
  <div class="visualization-header">
    <div class="header-left">
      <h1>Story Visualization</h1>
      <p>Visualize and analyze your story structure</p>
    </div>
    
    <div class="header-right">
      <div class="view-tabs">
        {#each views as view}
          <button 
            class="tab {activeView === view.id ? 'active' : ''}"
            on:click={() => handleViewChange(view.id)}
          >
            <span class="tab-icon">{view.icon}</span>
            {view.name}
          </button>
        {/each}
      </div>
      
      <div class="action-buttons">
        <button class="export-btn" on:click={() => exportReport('pdf')}>
          📄 Export PDF
        </button>
        <button class="export-btn" on:click={() => exportReport('json')}>
          📊 Export JSON
        </button>
      </div>
    </div>
  </div>

  <!-- Content -->
  <div class="visualization-content">
    {#if loading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading story visualization...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <p>{error}</p>
        <button on:click={loadVisualizationData} class="retry-btn">Retry</button>
      </div>
    {:else}
      <!-- View switcher -->
      <div class="view-container">
        {#if activeView === 'timeline'}
          <TimelineView {projectId} {config} on:configUpdate={handleConfigUpdate} />
        {:else if activeView === 'grid'}
          <SceneGridView {projectId} {config} on:sceneSelected={handleSceneSelected} />
        {:else if activeView === 'character'}
          <CharacterArcView {projectId} {config} />
        {:else if activeView === 'analytics'}
          <!-- Analytics view will be implemented next -->
          <div class="coming-soon">
            <h2>Analytics View</h2>
            <p>Coming soon...</p>
          </div>
        {/if}
      </div>

      <!-- Selected scene details -->
      {#if selectedScene}
        <div class="scene-details-panel">
          <h3>{selectedScene.title}</h3>
          <p>{selectedScene.description}</p>
          
          <div class="scene-stats">
            <div class="stat">
              <span class="label">Duration</span>
              <span class="value">{selectedScene.duration}min</span>
            </div>
            <div class="stat">
              <span class="label">Characters</span>
              <span class="value">{selectedScene.characters?.length || 0}</span>
            </div>
            <div class="stat">
              <span class="label">Assets</span>
              <span class="value">{selectedScene.assetCount || 0}</span>
            </div>
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .story-visualization-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .visualization-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-secondary);
    flex-wrap: wrap;
    gap: 1rem;
  }

  .header-left h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
  }

  .header-left p {
    margin: 0.25rem 0 0 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .header-right {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
  }

  .view-tabs {
    display: flex;
    gap: 0.25rem;
    background: var(--bg-tertiary);
    border-radius: 0.5rem;
    padding: 0.25rem;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.875rem;
  }

  .tab:hover {
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .tab.active {
    background: var(--accent-color);
    color: white;
  }

  .tab-icon {
    font-size: 1rem;
  }

  .action-buttons {
    display: flex;
    gap: 0.5rem;
  }

  .export-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-primary);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.875rem;
  }

  .export-btn:hover {
    background: var(--bg-tertiary);
  }

  .visualization-content {
    flex: 1;
    display: flex;
    overflow: hidden;
  }

  .view-container {
    flex: 1;
    overflow: hidden;
  }

  .loading-state,
  .error-state {
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

  .retry-btn {
    padding: 0.5rem 1rem;
    margin-top: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
  }

  .coming-soon {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
  }

  .scene-details-panel {
    width: 300px;
    border-left: 1px solid var(--border-color);
    background: var(--bg-secondary);
    padding: 1rem;
    overflow-y: auto;
  }

  .scene-details-panel h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .scene-details-panel p {
    margin: 0 0 1rem 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .scene-stats {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stat .label {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  .stat .value {
    font-size: 0.875rem;
    font-weight: 600;
  }

  @media (max-width: 768px) {
    .visualization-header {
      flex-direction: column;
      align-items: stretch;
    }

    .header-right {
      flex-direction: column;
      align-items: stretch;
    }

    .view-tabs {
      flex-wrap: wrap;
    }

    .action-buttons {
      justify-content: center;
    }

    .visualization-content {
      flex-direction: column;
    }

    .scene-details-panel {
      width: 100%;
      max-height: 200px;
    }
  }
</style>