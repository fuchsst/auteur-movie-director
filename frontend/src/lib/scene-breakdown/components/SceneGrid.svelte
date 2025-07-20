<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { dndzone } from 'svelte-dnd-action';
    import SceneCard from './SceneCard.svelte';
    import SceneGroup from './SceneGroup.svelte';
    import type { SceneSummary } from '../types/scene-breakdown';

    export let scenes: SceneSummary[] = [];
    export let selectedSceneId: string | null = null;
    export let enableDragDrop = true;

    const dispatch = createEventDispatcher();

    $: groupedScenes = groupScenesByAct(scenes);

    function groupScenesByAct(scenes: SceneSummary[]) {
        const groups: Record<string, SceneSummary[]> = {};
        
        scenes.forEach(scene => {
            const key = `Act ${scene.act_number}${scene.chapter_number ? ` - Chapter ${scene.chapter_number}` : ''}`;
            if (!groups[key]) {
                groups[key] = [];
            }
            groups[key].push(scene);
        });

        // Sort scenes within each group
        Object.keys(groups).forEach(key => {
            groups[key].sort((a, b) => a.scene_number - b.scene_number);
        });

        return groups;
    }

    function handleSceneSelect(sceneId: string) {
        dispatch('sceneSelect', sceneId);
    }

    function handleSceneUpdate(sceneId: string, updates: any) {
        dispatch('sceneUpdate', { sceneId, updates });
    }

    function handleDragConsider(e: CustomEvent) {
        const { items, info } = e.detail;
        // Handle drag consider logic
    }

    function handleDragFinalize(e: CustomEvent) {
        const { items, info } = e.detail;
        dispatch('sceneReorder', {
            sceneId: info.id,
            newPosition: info.index,
            targetAct: info.act,
            targetChapter: info.chapter
        });
    }

    function getStatusColor(status: string) {
        const colors = {
            draft: '#9ca3af',
            in_progress: '#f59e0b',
            complete: '#10b981',
            review: '#8b5cf6',
            approved: '#3b82f6'
        };
        return colors[status] || '#9ca3af';
    }
</script>

<div class="scene-grid" 
     use:dndzone={{ items: scenes, flipDurationMs: 200 }} 
     on:consider={handleDragConsider} 
     on:finalize={handleDragFinalize}>
    
    {#each Object.entries(groupedScenes) as [groupName, groupScenes] (groupName)}
        <SceneGroup 
            {groupName} 
            sceneCount={groupScenes.length}
            totalDuration={groupScenes.reduce((sum, s) => sum + s.duration_minutes, 0)}
        >
            <div class="scene-group-grid" 
                 class:drag-enabled={enableDragDrop}>
                {#each groupScenes as scene (scene.scene_id)}
                    <SceneCard
                        {scene}
                        isSelected={selectedSceneId === scene.scene_id}
                        statusColor={getStatusColor(scene.status)}
                        on:click={() => handleSceneSelect(scene.scene_id)}
                        on:update={(e) => handleSceneUpdate(scene.scene_id, e.detail)}
                    />
                {/each}
            </div>
        </SceneGroup>
    {/each}

    {#if scenes.length === 0}
        <div class="empty-state">
            <div class="empty-icon">🎬</div>
            <h3>No scenes yet</h3>
            <p>Start creating your scene breakdown by adding your first scene.</p>
            <button class="add-scene-btn" on:click={() => dispatch('addScene')} >
                + Add First Scene
            </button>
        </div>
    {/if}
</div>

<style>
.scene-grid {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 2rem;
    min-height: 100%;
    background: #f8fafc;
}

.scene-group-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    padding: 0.5rem 0;
}

.scene-group-grid.drag-enabled {
    cursor: grab;
}

.scene-group-grid.drag-enabled:active {
    cursor: grabbing;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
    color: #6b7280;
}

.empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.empty-state h3 {
    color: #374151;
    margin: 0 0 0.5rem 0;
    font-size: 1.25rem;
}

.empty-state p {
    margin: 0 0 1.5rem 0;
    font-size: 0.875rem;
}

.add-scene-btn {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: background-color 0.2s;
}

.add-scene-btn:hover {
    background: #2563eb;
}

@media (max-width: 768px) {
    .scene-grid {
        padding: 1rem;
    }
    
    .scene-group-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 480px) {
    .scene-group-grid {
        grid-template-columns: 1fr;
        gap: 0.75rem;
    }
}
</style>