<script lang="ts">
    import { onMount } from 'svelte';
    import { sceneBreakdownStore } from '../stores/scene-breakdown-store';
    import SceneGrid from './SceneGrid.svelte';
    import SceneCanvas from './SceneCanvas.svelte';
    import SceneDetailsPanel from './SceneDetailsPanel.svelte';
    import SceneToolbar from './SceneToolbar.svelte';
    import StoryCircleView from './StoryCircleView.svelte';
    import { fade, fly } from 'svelte/transition';

    export let projectId: string;

    let viewMode: 'grid' | 'canvas' | 'story-circle' = 'grid';
    let selectedSceneId: string | null = null;
    let isDetailsPanelOpen = false;
    let isLoading = true;
    let error: string | null = null;

    $: scenes = $sceneBreakdownStore.scenes;
    $: selectedScene = selectedSceneId ? scenes.find(s => s.scene_id === selectedSceneId) : null;

    onMount(async () => {
        try {
            await sceneBreakdownStore.loadProjectScenes(projectId);
            isLoading = false;
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to load scenes';
            isLoading = false;
        }
    });

    function handleSceneSelect(sceneId: string) {
        selectedSceneId = sceneId;
        isDetailsPanelOpen = true;
    }

    function handleSceneDeselect() {
        selectedSceneId = null;
        isDetailsPanelOpen = false;
    }

    function handleViewModeChange(mode: 'grid' | 'canvas' | 'story-circle') {
        viewMode = mode;
    }

    async function handleSceneUpdate(sceneId: string, updates: any) {
        try {
            await sceneBreakdownStore.updateScene(sceneId, updates);
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to update scene';
        }
    }

    async function handleSceneReorder(reorderData: any) {
        try {
            await sceneBreakdownStore.reorderScene(reorderData);
        } catch (err) {
            error = err instanceof Error ? err.message : 'Failed to reorder scenes';
        }
    }

    function handleErrorClose() {
        error = null;
    }

    function closeDetailsPanel() {
        isDetailsPanelOpen = false;
        selectedSceneId = null;
    }
</script>

<div class="scene-breakdown-view" 
     class:details-open={isDetailsPanelOpen}>
    
    {#if isLoading}
        <div class="loading-container" 
             in:fade={{ duration: 200 }}>
            <div class="loading-spinner"></div>
            <p>Loading scene breakdown...</p>
        </div>
    {:else if error}
        <div class="error-container" 
             in:fade={{ duration: 200 }}>
            <div class="error-message">
                <h3>Error Loading Scenes</h3>
                <p>{error}</p>
                <button class="btn btn-primary" on:click={handleErrorClose}>
                    Dismiss
                </button>
            </div>
        </div>
    {:else}
        <SceneToolbar
            {viewMode}
            on:viewModeChange={handleViewModeChange}
            on:refresh={() => sceneBreakdownStore.loadProjectScenes(projectId)}
        />

        <div class="view-content">
            {#if viewMode === 'grid'}
                <SceneGrid
                    {scenes}
                    {selectedSceneId}
                    on:sceneSelect={handleSceneSelect}
                    on:sceneUpdate={handleSceneUpdate}
                />
            {:else if viewMode === 'canvas'}
                <SceneCanvas
                    {scenes}
                    {selectedSceneId}
                    on:sceneSelect={handleSceneSelect}
                    on:sceneUpdate={handleSceneUpdate}
                    on:sceneReorder={handleSceneReorder}
                />
            {:else if viewMode === 'story-circle'}
                <StoryCircleView
                    {scenes}
                    {selectedSceneId}
                    on:sceneSelect={handleSceneSelect}
                    on:sceneUpdate={handleSceneUpdate}
                />
            {/if}
        </div>

        {#if isDetailsPanelOpen && selectedScene}
            <div class="details-panel-container" 
                 in:fly={{ x: 300, duration: 300 }}
                 out:fly={{ x: 300, duration: 200 }}>
                <SceneDetailsPanel
                    scene={selectedScene}
                    on:close={closeDetailsPanel}
                    on:update={(e) => handleSceneUpdate(selectedSceneId, e.detail)}
                    on:delete={async () => {
                        await sceneBreakdownStore.deleteScene(selectedSceneId);
                        closeDetailsPanel();
                    }}
                />
            </div>
        {/if}
    {/if}
</div>

<style>
.scene-breakdown-view {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: #f8fafc;
    position: relative;
}

.scene-breakdown-view.details-open {
    padding-right: 400px;
}

.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 1rem;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #e5e7eb;
    border-top: 4px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.error-container {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 2rem;
}

.error-message {
    background: white;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    max-width: 400px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.error-message h3 {
    color: #dc2626;
    margin: 0 0 0.5rem 0;
}

.error-message p {
    color: #6b7280;
    margin: 0 0 1rem 0;
}

.view-content {
    flex: 1;
    overflow: hidden;
    position: relative;
}

.details-panel-container {
    position: fixed;
    top: 0;
    right: 0;
    width: 400px;
    height: 100vh;
    background: white;
    border-left: 1px solid #e5e7eb;
    box-shadow: -4px 0 6px -1px rgba(0, 0, 0, 0.1);
    z-index: 1000;
}

.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary {
    background: #3b82f6;
    color: white;
}

.btn-primary:hover {
    background: #2563eb;
}

@media (max-width: 768px) {
    .scene-breakdown-view.details-open {
        padding-right: 0;
    }
    
    .details-panel-container {
        width: 100%;
    }
}
</style>