<!--
Breakdown View Component
STORY-086: Professional Script Breakdown Interface

Provides a comprehensive script breakdown interface that mirrors traditional
production workflows with scene-by-scene element management.
-->

<script lang="ts">
  import { onMount } from 'svelte';
  import { breakdownStore } from '$lib/stores/breakdownStore';
  import { projectStore } from '$lib/stores/projectStore';
  import { notifications } from '$lib/stores/notifications';
  import { getApiClient } from '$lib/api/client';
  
  import SceneBreakdownPanel from './components/SceneBreakdownPanel.svelte';
  import ElementManager from './components/ElementManager.svelte';
  import BreakdownSummary from './components/BreakdownSummary.svelte';
  import ScriptUploader from './components/ScriptUploader.svelte';
  import ExportDialog from './components/ExportDialog.svelte';
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte';

  export let projectId: string;

  let loading = true;
  let selectedSceneId: string | null = null;
  let showExportDialog = false;
  let activeTab: 'breakdown' | 'summary' | 'export' = 'breakdown';

  const api = getApiClient();

  onMount(async () => {
    try {
      await breakdownStore.loadBreakdown(projectId);
    } catch (error) {
      notifications.error('Failed to load breakdown data');
    } finally {
      loading = false;
    }
  });

  async function handleScriptUpload(event: CustomEvent) {
    const { file, projectName } = event.detail;
    try {
      loading = true;
      await breakdownStore.parseScript(projectId, file, projectName);
      notifications.success('Script parsed successfully');
    } catch (error) {
      notifications.error('Failed to parse script');
    } finally {
      loading = false;
    }
  }

  function selectScene(sceneId: string) {
    selectedSceneId = sceneId;
  }

  $: breakdown = $breakdownStore.breakdowns[projectId];
  $: scenes = breakdown ? Object.values(breakdown.scenes) : [];
  $: selectedScene = selectedSceneId && breakdown ? breakdown.scenes[selectedSceneId] : null;
</script>

<div class="breakdown-view">
  {#if loading}
    <div class="loading-container">
      <LoadingSpinner size="large" />
      <p>Loading breakdown data...</p>
    </div>
  {:else if !breakdown}
    <div class="empty-state">
      <ScriptUploader {projectId} on:upload={handleScriptUpload} />
    </div>
  {:else}
    <div class="breakdown-container">
      <!-- Header -->
      <header class="breakdown-header">
        <div class="header-content">
          <h1>{breakdown.script_title || 'Untitled Script'}</h1>
          <div class="header-actions">
            <button 
              class="btn btn-secondary"
              on:click={() => showExportDialog = true}
            >
              Export
            </button>
            <button 
              class="btn btn-primary"
              on:click={() => document.getElementById('script-uploader')?.click()}
            >
              Upload New Script
            </button>
          </div>
        </div>
        
        <!-- Tabs -->
        <nav class="breakdown-tabs">
          <button 
            class="tab {activeTab === 'breakdown' ? 'active' : ''}"
            on:click={() => activeTab = 'breakdown'}
          >
            Scene Breakdown
          </button>
          <button 
            class="tab {activeTab === 'summary' ? 'active' : ''}"
            on:click={() => activeTab = 'summary'}
          >
            Summary
          </button>
        </nav>
      </header>

      <!-- Content -->
      <div class="breakdown-content">
        {#if activeTab === 'breakdown'}
          <div class="breakdown-layout">
            <!-- Scene List -->
            <div class="scene-list">
              <h3>Scenes ({scenes.length})</h3>
              <div class="scene-items">
                {#each scenes as scene}
                  <button
                    class="scene-item {selectedSceneId === scene.scene_id ? 'selected' : ''}"
                    on:click={() => selectScene(scene.scene_id)}
                  >
                    <div class="scene-number">{scene.scene_number}</div>
                    <div class="scene-heading">{scene.scene_heading}</div>
                    <div class="scene-stats">
                      <span>{scene.get_total_elements()} elements</span>
                    </div>
                  </button>
                {/each}
              </div>
            </div>

            <!-- Scene Detail -->
            <div class="scene-detail">
              {#if selectedScene}
                <SceneBreakdownPanel {selectedScene} {projectId} />
              {:else}
                <div class="empty-detail">
                  <p>Select a scene to view breakdown details</p>
                </div>
              {/if}
            </div>
          </div>
        {:else if activeTab === 'summary'}
          <BreakdownSummary {breakdown} />
        {/if}
      </div>
    </div>
  {/if}
</div>

{#if showExportDialog}
  <ExportDialog 
    {projectId} 
    {breakdown}
    on:close={() => showExportDialog = false}
  />
{/if}

<style>
  .breakdown-view {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--color-background);
    color: var(--color-text);
  }

  .loading-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
  }

  .empty-state {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .breakdown-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .breakdown-header {
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    padding: 1rem;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .header-content h1 {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
  }

  .breakdown-tabs {
    display: flex;
    gap: 1rem;
    border-bottom: 1px solid var(--color-border);
  }

  .tab {
    padding: 0.5rem 1rem;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    border-bottom: 2px solid transparent;
  }

  .tab.active {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
  }

  .breakdown-content {
    flex: 1;
    overflow: hidden;
  }

  .breakdown-layout {
    display: grid;
    grid-template-columns: 300px 1fr;
    height: 100%;
    gap: 1px;
    background: var(--color-border);
  }

  .scene-list {
    background: var(--color-surface);
    padding: 1rem;
    overflow-y: auto;
  }

  .scene-list h3 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 1rem;
  }

  .scene-items {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .scene-item {
    display: flex;
    flex-direction: column;
    padding: 0.75rem;
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    font-size: 0.875rem;
  }

  .scene-item:hover {
    background: var(--color-surface-hover);
  }

  .scene-item.selected {
    border-color: var(--color-primary);
    background: var(--color-primary-transparent);
  }

  .scene-number {
    font-weight: 600;
    color: var(--color-primary);
    font-size: 0.75rem;
  }

  .scene-heading {
    font-weight: 500;
    margin: 0.25rem 0;
  }

  .scene-stats {
    font-size: 0.75rem;
    color: var(--color-text-secondary);
  }

  .scene-detail {
    background: var(--color-background);
    overflow-y: auto;
  }

  .empty-detail {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--color-text-secondary);
    font-style: italic;
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

  .btn-secondary {
    background: var(--color-secondary);
    color: white;
    border-color: var(--color-secondary);
  }

  .btn-secondary:hover {
    background: var(--color-secondary-hover);
  }
</style>