<!--
  Scene Visualization Component
  STORY-090: Scene-by-Scene Breakdown Visualization
  
  Provides comprehensive visual representation of scene breakdown data including
  timeline view, story beats, character tracking, and asset usage analytics.
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { SceneBreakdown, BreakdownElement, ElementCategory } from '$lib/types/breakdown';
  import { breakdownStore } from '$lib/stores/breakdownStore';
  import { assetStore } from '$lib/stores/assetStore';
  import { CharacterAvatar } from '$lib/components/common/CharacterAvatar.svelte';
  import TimelineView from './TimelineView.svelte';
  import StoryBeatsPanel from './StoryBeatsPanel.svelte';
  import CharacterArcsPanel from './CharacterArcsPanel.svelte';
  import AssetAnalytics from './AssetAnalytics.svelte';
  
  export let scene: SceneBreakdown;
  export let projectId: string;

  const dispatch = createEventDispatcher();

  let activeTab: 'timeline' | 'beats' | 'characters' | 'assets' | 'analytics' = 'timeline';
  let selectedBeat: any = null;
  let selectedCharacter: string | null = null;

  $: sceneElements = scene ? Object.values(scene.elements || {}).flat() : [];
  $: characters = scene?.characters || [];
  $: assets = sceneElements.filter(el => el.asset_id);

  function handleBeatSelect(beat: any) {
    selectedBeat = beat;
    dispatch('beatSelect', { beat, scene });
  }

  function handleCharacterSelect(characterId: string) {
    selectedCharacter = characterId;
    dispatch('characterSelect', { characterId, scene });
  }

  function formatDuration(seconds: number) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function getElementByCategory(category: ElementCategory) {
    return sceneElements.filter(el => el.element_type === category);
  }

  function getCostByCategory() {
    const costs: Record<ElementCategory, number> = {} as Record<ElementCategory, number>;
    Object.values(ElementCategory).forEach(cat => {
      costs[cat] = getElementByCategory(cat).reduce((sum, el) => sum + (el.estimated_cost || 0), 0);
    });
    return costs;
  }
</script>

<div class="scene-visualization">
  <!-- Scene Header -->
  <div class="scene-header">
    <div class="scene-info">
      <h2>Scene {scene.scene_number}</h2>
      <p class="scene-heading">{scene.scene_heading}</p>
      <p class="scene-synopsis">{scene.synopsis}</p>
    </div>
    
    <div class="scene-stats">
      <div class="stat">
        <span class="stat-label">Duration</span>
        <span class="stat-value">{formatDuration(scene.estimated_duration || 0)}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Pages</span>
        <span class="stat-value">{scene.estimated_pages?.toFixed(1) || '0.0'}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Elements</span>
        <span class="stat-value">{sceneElements.length}</span>
      </div>
      <div class="stat">
        <span class="stat-label">Cost</span>
        <span class="stat-value">${sceneElements.reduce((sum, el) => sum + (el.estimated_cost || 0), 0).toLocaleString()}</span>
      </div>
    </div>
  </div>

  <!-- Navigation Tabs -->
  <nav class="visualization-tabs">
    <button 
      class="tab {activeTab === 'timeline' ? 'active' : ''}"
      on:click={() => activeTab = 'timeline'}
    >
      Timeline
    </button>
    <button 
      class="tab {activeTab === 'beats' ? 'active' : ''}"
      on:click={() => activeTab = 'beats'}
    >
      Story Beats
    </button>
    <button 
      class="tab {activeTab === 'characters' ? 'active' : ''}"
      on:click={() => activeTab = 'characters'}
    >
      Characters
    </button>
    <button 
      class="tab {activeTab === 'assets' ? 'active' : ''}"
      on:click={() => activeTab = 'assets'}
    >
      Assets
    </button>
    <button 
      class="tab {activeTab === 'analytics' ? 'active' : ''}"
      on:click={() => activeTab = 'analytics'}
    >
      Analytics
    </button>
  </nav>

  <!-- Content Area -->
  <div class="visualization-content">
    {#if activeTab === 'timeline'}
      <TimelineView 
        {scene} 
        elements={sceneElements}
        on:beatSelect={handleBeatSelect}
      />
    {:else if activeTab === 'beats'}
      <StoryBeatsPanel 
        {scene} 
        selectedBeat={selectedBeat}
        on:beatSelect={handleBeatSelect}
      />
    {:else if activeTab === 'characters'}
      <CharacterArcsPanel 
        {scene} 
        characters={characters}
        selectedCharacter={selectedCharacter}
        on:characterSelect={handleCharacterSelect}
      />
    {:else if activeTab === 'assets'}
      <AssetAnalytics 
        {scene} 
        assets={assets}
        costByCategory={getCostByCategory()}
      />
    {:else if activeTab === 'analytics'}
      <div class="analytics-panel">
        <h3>Scene Analytics</h3>
        <div class="analytics-grid">
          <div class="analytics-card">
            <h4>Element Distribution</h4>
            <div class="category-bars">
              {#each Object.entries(ElementCategory) as [key, category]}
                {@const count = getElementByCategory(category).length}
                {@const maxCount = Math.max(...Object.values(ElementCategory).map(c => getElementByCategory(c).length))}
                <div class="category-bar">
                  <span class="category-label">{category}</span>
                  <div class="bar-container">
                    <div 
                      class="bar" 
                      style="width: {(count / maxCount) * 100}%"
                    ></div>
                  </div>
                  <span class="category-count">{count}</span>
                </div>
              {/each}
            </div>
          </div>
          
          <div class="analytics-card">
            <h4>Cost Analysis</h4>
            <div class="cost-breakdown">
              {#each Object.entries(getCostByCategory()) as [category, cost]}
                {#if cost > 0}
                  <div class="cost-item">
                    <span class="cost-label">{category}</span>
                    <span class="cost-value">${cost.toLocaleString()}</span>
                  </div>
                {/if}
              {/each}
            </div>
          </div>

          <div class="analytics-card">
            <h4>Scene Complexity</h4>
            <div class="complexity-metrics">
              <div class="metric">
                <span class="metric-label">Characters</span>
                <span class="metric-value">{characters.length}</span>
              </div>
              <div class="metric">
                <span class="metric-label">Unique Assets</span>
                <span class="metric-value">{assets.length}</span>
              </div>
              <div class="metric">
                <span class="metric-label">Production Elements</span>
                <span class="metric-value">{sceneElements.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .scene-visualization {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--color-background);
    color: var(--color-text);
  }

  .scene-header {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 2rem;
    padding: 1.5rem;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-surface);
  }

  .scene-info h2 {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
    color: var(--color-primary);
  }

  .scene-heading {
    font-size: 1.125rem;
    font-weight: 500;
    margin: 0 0 0.5rem 0;
  }

  .scene-synopsis {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    line-height: 1.5;
  }

  .scene-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    min-width: 200px;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .stat-label {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .stat-value {
    font-size: 1.25rem;
    font-weight: 600;
  }

  .visualization-tabs {
    display: flex;
    gap: 0.5rem;
    padding: 0 1.5rem;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-surface);
  }

  .tab {
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
  }

  .tab:hover {
    color: var(--color-text);
  }

  .tab.active {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
  }

  .visualization-content {
    flex: 1;
    overflow: auto;
    padding: 1.5rem;
  }

  .analytics-panel h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0 0 1.5rem 0;
  }

  .analytics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .analytics-card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: 0.5rem;
    padding: 1.5rem;
  }

  .analytics-card h4 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
  }

  .category-bars {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .category-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.875rem;
  }

  .category-label {
    min-width: 80px;
    font-weight: 500;
    text-transform: capitalize;
  }

  .bar-container {
    flex: 1;
    height: 6px;
    background: var(--color-border);
    border-radius: 3px;
    overflow: hidden;
  }

  .bar {
    height: 100%;
    background: var(--color-primary);
    transition: width 0.3s ease;
  }

  .category-count {
    min-width: 30px;
    text-align: right;
    font-weight: 600;
  }

  .cost-breakdown {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .cost-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  .cost-label {
    text-transform: capitalize;
  }

  .cost-value {
    font-weight: 600;
    color: var(--color-primary);
  }

  .complexity-metrics {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  .metric-label {
    color: var(--color-text-secondary);
  }

  .metric-value {
    font-weight: 600;
  }

  @media (max-width: 768px) {
    .scene-header {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .scene-stats {
      grid-template-columns: repeat(4, 1fr);
    }

    .visualization-tabs {
      overflow-x: auto;
    }

    .analytics-grid {
      grid-template-columns: 1fr;
    }
  }
</style>