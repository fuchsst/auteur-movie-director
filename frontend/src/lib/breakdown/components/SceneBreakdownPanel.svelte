<!--
Scene Breakdown Panel
STORY-086: Individual scene breakdown interface

Displays detailed breakdown for a single scene including elements,
characters, and production notes.
-->

<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { breakdownStore } from '$lib/stores/breakdownStore';
  import { notifications } from '$lib/stores/notifications';
  import { getApiClient } from '$lib/api/client';
  import ElementCategoryDisplay from './ElementCategoryDisplay.svelte';
  import CharacterList from './CharacterList.svelte';
  import SceneNotes from './SceneNotes.svelte';
  import AddElementDialog from './AddElementDialog.svelte';

  export let selectedScene: any;
  export let projectId: string;

  const dispatch = createEventDispatcher();
  const api = getApiClient();

  let showAddElement = false;
  let activeCategory: string = 'all';

  $: sceneElements = selectedScene ? Object.entries(selectedScene.elements || {}) : [];
  $: totalElements = selectedScene ? selectedScene.get_total_elements?.() || 0 : 0;
  $: totalCost = selectedScene ? selectedScene.get_total_cost?.() || 0 : 0;

  function getAllElements() {
    if (!selectedScene) return [];
    return Object.values(selectedScene.elements || {}).flat();
  }

  function getElementsByCategory(category: string) {
    if (!selectedScene || !selectedScene.elements) return [];
    return selectedScene.elements[category] || [];
  }

  async function handleElementUpdate(element: any, updates: any) {
    try {
      await breakdownStore.updateElement(projectId, selectedScene.scene_id, element.element_id, updates);
      notifications.success('Element updated');
    } catch (error) {
      notifications.error('Failed to update element');
    }
  }

  async function handleAddElement(event: CustomEvent) {
    try {
      await breakdownStore.addElement(projectId, selectedScene.scene_id, event.detail);
      notifications.success('Element added');
      showAddElement = false;
    } catch (error) {
      notifications.error('Failed to add element');
    }
  }

  function formatDuration(seconds: number) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }

  function formatCost(cost: number) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(cost);
  }
</script>

<div class="scene-breakdown-panel">
  {#if selectedScene}
    <div class="scene-header">
      <div class="scene-info">
        <h2>Scene {selectedScene.scene_number}</h2>
        <p class="scene-heading">{selectedScene.scene_heading}</p>
        <p class="scene-synopsis">{selectedScene.synopsis}</p>
      </div>
      
      <div class="scene-stats">
        <div class="stat">
          <span class="stat-label">Duration</span>
          <span class="stat-value">{formatDuration(selectedScene.estimated_duration || 0)}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Pages</span>
          <span class="stat-value">{selectedScene.estimated_pages?.toFixed(1) || '0.0'}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Elements</span>
          <span class="stat-value">{totalElements}</span>
        </div>
        <div class="stat">
          <span class="stat-label">Cost</span>
          <span class="stat-value">{formatCost(totalCost)}</span>
        </div>
      </div>
    </div>

    <!-- Scene Details -->
    <div class="scene-details">
      <div class="details-grid">
        <!-- Characters -->
        <div class="detail-section">
          <h3>Characters</h3>
          <CharacterList characters={selectedScene.characters} />
        </div>

        <!-- Location Details -->
        <div class="detail-section">
          <h3>Location Details</h3>
          <dl class="detail-list">
            <dt>Location</dt>
            <dd>{selectedScene.location}</dd>
            <dt>Time of Day</dt>
            <dd>{selectedScene.time_of_day}</dd>
            <dt>Interior/Exterior</dt>
            <dd>{selectedScene.interior_exterior}</dd>
          </dl>
        </div>

        <!-- Production Notes -->
        <div class="detail-section">
          <SceneNotes 
            notes={selectedScene.continuity_notes || ''}
            specialNotes={selectedScene.special_notes || ''}
            on:update={async (e) => {
              await breakdownStore.updateSceneNotes(projectId, selectedScene.scene_id, e.detail);
            }}
          />
        </div>
      </div>

      <!-- Elements -->
      <div class="elements-section">
        <div class="section-header">
          <h3>Production Elements</h3>
          <button 
            class="btn btn-primary"
            on:click={() => showAddElement = true}
          >
            Add Element
          </button>
        </div>

        <!-- Category Tabs -->
        <nav class="category-tabs">
          <button
            class="tab {activeCategory === 'all' ? 'active' : ''}"
            on:click={() => activeCategory = 'all'}
          >
            All ({getAllElements().length})
          </button>
          
          {#each sceneElements as [category, elements]}
            {#if elements.length > 0}
              <button
                class="tab {activeCategory === category ? 'active' : ''}"
                on:click={() => activeCategory = category}
              >
                {category.replace('_', ' ').toUpperCase()} ({elements.length})
              </button>
            {/if}
          {/each}
        </nav>

        <!-- Elements Display -->
        <div class="elements-grid">
          {#if activeCategory === 'all'}
            {#each getAllElements() as element}
              <ElementCategoryDisplay 
                {element} 
                on:update={(e) => handleElementUpdate(element, e.detail)}
              />
            {/each}
          {:else}
            {#each getElementsByCategory(activeCategory) as element}
              <ElementCategoryDisplay 
                {element} 
                on:update={(e) => handleElementUpdate(element, e.detail)}
              />
            {/each}
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

{#if showAddElement}
  <AddElementDialog 
    {projectId}
    sceneId={selectedScene.scene_id}
    on:save={handleAddElement}
    on:close={() => showAddElement = false}
  />
{/if}

<style>
  .scene-breakdown-panel {
    height: 100%;
    overflow-y: auto;
    padding: 1.5rem;
  }

  .scene-header {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 2rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--color-border);
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
    color: var(--color-text);
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
    color: var(--color-text);
  }

  .scene-details {
    margin-bottom: 2rem;
  }

  .details-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .detail-section h3 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    color: var(--color-text);
  }

  .detail-list {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .detail-list dt {
    font-weight: 600;
    color: var(--color-text-secondary);
  }

  .detail-list dd {
    margin: 0;
    color: var(--color-text);
  }

  .elements-section {
    margin-top: 2rem;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .section-header h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
  }

  .category-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    overflow-x: auto;
  }

  .tab {
    padding: 0.5rem 1rem;
    background: none;
    border: 1px solid var(--color-border);
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.875rem;
    white-space: nowrap;
    transition: all 0.2s;
  }

  .tab:hover {
    background: var(--color-surface-hover);
  }

  .tab.active {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .elements-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
  }

  .btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: 0.375rem;
    background: var(--color-surface);
    color: var(--color-text);
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
  }

  .btn:hover {
    background: var(--color-surface-hover);
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .btn-primary:hover {
    background: var(--color-primary-hover);
  }

  @media (max-width: 768px) {
    .scene-header {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .details-grid {
      grid-template-columns: 1fr;
    }

    .elements-grid {
      grid-template-columns: 1fr;
    }
  }
</style>