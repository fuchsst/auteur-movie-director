<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, fly } from 'svelte/transition';
    import { sceneBreakdownStore } from '../stores/scene-breakdown-store';
    import type { SceneSummary } from '../types/scene-breakdown';

    export let scenes: SceneSummary[] = [];
    export let selectedSceneId: string | null = null;

    const dispatch = createEventDispatcher();

    let circleRadius = 200;
    let centerX = 300;
    let centerY = 300;
    let hoveredPosition: number | null = null;
    let storyCircleData: any = null;

    const storyCirclePositions = [
        { position: 1, title: "You", description: "Protagonist in their ordinary world", color: "#ef4444" },
        { position: 2, title: "Need", description: "Character's desire or lack", color: "#f97316" },
        { position: 3, title: "Go", description: "Crossing the threshold", color: "#f59e0b" },
        { position: 4, title: "Search", description: "Trials and tribulations", color: "#84cc16" },
        { position: 5, title: "Find", description: "Meeting the goddess/revelation", color: "#22c55e" },
        { position: 6, title: "Take", description: "Supreme ordeal", color: "#06b6d4" },
        { position: 7, title: "Return", description: "Reward and consequences", color: "#3b82f6" },
        { position: 8, title: "Change", description: "New self/transformation", color: "#8b5cf6" }
    ];

    $: positionedScenes = scenes.filter(scene => scene.story_circle_position);
    $: scenesByPosition = groupScenesByPosition(scenes);

    onMount(async () => {
        try {
            const projectId = scenes.length > 0 ? scenes[0].project_id : null;
            if (projectId) {
                storyCircleData = await sceneBreakdownStore.getStoryCircleMapping(projectId);
            }
        } catch (error) {
            console.error('Failed to load story circle data:', error);
        }
    });

    function groupScenesByPosition(scenes: SceneSummary[]) {
        const grouped: Record<number, SceneSummary[]> = {};
        
        storyCirclePositions.forEach(pos => {
            grouped[pos.position] = [];
        });

        scenes.forEach(scene => {
            if (scene.story_circle_position && grouped[scene.story_circle_position]) {
                grouped[scene.story_circle_position].push(scene);
            }
        });

        return grouped;
    }

    function getPositionCoordinates(position: number) {
        const angle = ((position - 1) * 45 - 90) * (Math.PI / 180);
        const x = centerX + circleRadius * Math.cos(angle);
        const y = centerY + circleRadius * Math.sin(angle);
        return { x, y };
    }

    function handleSceneSelect(sceneId: string) {
        dispatch('sceneSelect', sceneId);
    }

    function handlePositionHover(position: number | null) {
        hoveredPosition = position;
    }

    function handleSceneDrop(event: DragEvent, position: number) {
        event.preventDefault();
        const sceneId = event.dataTransfer?.getData('sceneId');
        if (sceneId) {
            dispatch('sceneUpdate', { 
                sceneId, 
                updates: { story_circle_position: position } 
            });
        }
    }

    function handleDragOver(event: DragEvent) {
        event.preventDefault();
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

    function formatDuration(minutes: number) {
        return `${Math.round(minutes)}m`;
    }
</script>

<div class="story-circle-view">
    <div class="circle-container">
        <!-- Background Circle -->
        <svg class="circle-svg" viewBox="0 0 600 600">
            <!-- Outer Circle -->
            <circle cx="{centerX}" cy="{centerY}" r="{circleRadius}" 
                    fill="none" stroke="#e5e7eb" stroke-width="2"/>
            
            <!-- Spokes -->
            {#each storyCirclePositions as pos}
                {@const coords = getPositionCoordinates(pos.position)}
                <line x1="{centerX}" y1="{centerY}" 
                      x2="{coords.x}" y2="{coords.y}" 
                      stroke="#f3f4f6" stroke-width="1"/>
            {/each}
            
            <!-- Position Markers -->
            {#each storyCirclePositions as pos}
                {@const coords = getPositionCoordinates(pos.position)}
                {@const scenesAtPosition = scenesByPosition[pos.position] || []}
                {@const isHovered = hoveredPosition === pos.position}
                {@const isActive = selectedSceneId && 
                    scenesAtPosition.some(s => s.scene_id === selectedSceneId)}
                
                <g class="position-marker" 
                   class:hovered={isHovered}
                   class:active={isActive}
                   on:mouseenter={() => handlePositionHover(pos.position)}
                   on:mouseleave={() => handlePositionHover(null)}
                   on:drop={(e) => handleSceneDrop(e, pos.position)}
                   on:dragover={handleDragOver}>
                    
                    <!-- Position Circle -->
                    <circle cx="{coords.x}" cy="{coords.y}" r="{isHovered ? 25 : 20}"
                            fill="{pos.color}" opacity="{scenesAtPosition.length > 0 ? 0.9 : 0.3}"/>
                    
                    <!-- Position Number -->
                    <text x="{coords.x}" y="{coords.y + 5}" text-anchor="middle" 
                          fill="white" font-size="{isHovered ? 14 : 12}" font-weight="bold">
                        {pos.position}
                    </text>
                    
                    <!-- Position Label -->
                    <text x="{coords.x}" y="{coords.y - 35}" text-anchor="middle" 
                          fill="#374151" font-size="12" font-weight="600">
                        {pos.title}
                    </text>
                </g>
            {/each}
            
            <!-- Connection Lines between Scenes -->
            {#each Object.entries(scenesByPosition) as [position, scenes]}
                {#each scenes as scene, index}
                    {#if index < scenes.length - 1}
                        {@const nextScene = scenes[index + 1]}
                        {#if scene.canvas_position && nextScene.canvas_position}
                            <line x1="{scene.canvas_position.x}" y1="{scene.canvas_position.y}" 
                                  x2="{nextScene.canvas_position.x}" y2="{nextScene.canvas_position.y}" 
                                  stroke="#d1d5db" stroke-width="1" stroke-dasharray="3,3"/>
                        {/if}
                    {/if}
                {/each}
            {/each}
        </svg>

        <!-- Scene Cards for each position -->
        {#each storyCirclePositions as pos}
            {@const coords = getPositionCoordinates(pos.position)}
            {@const scenesAtPosition = scenesByPosition[pos.position] || []}
            
            {#if scenesAtPosition.length > 0}
                <div class="position-scenes" 
                     style="left: {coords.x - 100}px; top: {coords.y + 40}px;"
                     in:fade={{ duration: 200 }}>
                    
                    <div class="position-title">{pos.title}</div>
                    <div class="position-description">{pos.description}</div>
                    
                    <div class="scenes-list">
                        {#each scenesAtPosition as scene}
                            <div class="mini-scene-card"
                                 class:selected={selectedSceneId === scene.scene_id}
                                 style="border-color: {getStatusColor(scene.status)}"
                                 on:click={() => handleSceneSelect(scene.scene_id)}
                                 draggable="true"
                                 on:dragstart={(e) => e.dataTransfer?.setData('sceneId', scene.scene_id)}>
                                
                                <div class="mini-scene-number">{scene.scene_number}</div>
                                <div class="mini-scene-title">{scene.title}</div>
                                <div class="mini-scene-meta">
                                    {formatDuration(scene.duration_minutes)} • {scene.character_count} chars
                                </div>
                                <div class="mini-progress">
                                    <div class="mini-progress-bar" 
                                         style="width: {scene.completion_percentage}%; background: {getStatusColor(scene.status)}">
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        {/each}
    </div>

    <!-- Legend -->
    <div class="legend" in:fade={{ duration: 200 }}>
        <h4>Story Circle Guide</h4>
        <div class="legend-items">
            {#each storyCirclePositions as pos}
                <div class="legend-item">
                    <div class="legend-color" style="background: {pos.color}"></div>
                    <div class="legend-text">
                        <strong>{pos.position}. {pos.title}</strong>
                        <span>{pos.description}</span>
                    </div>
                </div>
            {/each}
        </div>
    </div>

    <!-- Unpositioned Scenes -->
    {#if scenes.filter(s => !s.story_circle_position).length > 0}
        <div class="unpositioned-panel" in:fade={{ duration: 200 }}>
            <h4>Unpositioned Scenes</h4>
            <div class="unpositioned-scenes">
                {#each scenes.filter(s => !s.story_circle_position) as scene}
                    <div class="unpositioned-scene"
                         draggable="true"
                         on:dragstart={(e) => e.dataTransfer?.setData('sceneId', scene.scene_id)}>
                        <span>{scene.scene_number}. {scene.title}</span>
                        <span>{formatDuration(scene.duration_minutes)}</span>
                    </div>
                {/each}
            </div>
            <p class="instructions">Drag scenes to positions to map story structure</p>
        </div>
    {/if}
</div>

<style>
.story-circle-view {
    display: flex;
    height: 100vh;
    background: #f8fafc;
    position: relative;
}

.circle-container {
    flex: 1;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.circle-svg {
    width: 100%;
    height: 100%;
    max-width: 600px;
    max-height: 600px;
}

.position-marker {
    cursor: pointer;
    transition: all 0.2s ease;
}

.position-marker:hover {
    transform: scale(1.1);
}

.position-marker.active circle {
    stroke: #3b82f6;
    stroke-width: 3;
}

.position-scenes {
    position: absolute;
    width: 200px;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    z-index: 10;
}

.position-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.25rem;
}

.position-description {
    font-size: 0.75rem;
    color: #6b7280;
    margin-bottom: 0.5rem;
}

.scenes-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.mini-scene-card {
    background: white;
    border: 1px solid;
    border-radius: 4px;
    padding: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.75rem;
}

.mini-scene-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.mini-scene-card.selected {
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

.mini-scene-number {
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.125rem;
}

.mini-scene-title {
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.125rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.mini-scene-meta {
    font-size: 0.625rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
}

.mini-progress {
    height: 2px;
    background: #e5e7eb;
    border-radius: 1px;
    overflow: hidden;
}

.mini-progress-bar {
    height: 100%;
    transition: width 0.2s ease;
}

.legend {
    width: 300px;
    background: white;
    border-left: 1px solid #e5e7eb;
    padding: 1.5rem;
    overflow-y: auto;
}

.legend h4 {
    margin: 0 0 1rem 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
}

.legend-items {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.legend-item {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
}

.legend-color {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    margin-top: 2px;
    flex-shrink: 0;
}

.legend-text strong {
    display: block;
    font-size: 0.875rem;
    color: #111827;
    margin-bottom: 0.125rem;
}

.legend-text span {
    font-size: 0.75rem;
    color: #6b7280;
}

.unpositioned-panel {
    position: absolute;
    top: 1rem;
    left: 1rem;
    width: 250px;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    z-index: 10;
}

.unpositioned-panel h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: #111827;
}

.unpositioned-scenes {
    max-height: 200px;
    overflow-y: auto;
    margin-bottom: 0.5rem;
}

.unpositioned-scene {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    margin-bottom: 0.25rem;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: grab;
    transition: all 0.2s;
}

.unpositioned-scene:hover {
    background: #f3f4f6;
}

.unpositioned-scene:active {
    cursor: grabbing;
}

.instructions {
    font-size: 0.75rem;
    color: #6b7280;
    font-style: italic;
    margin: 0;
}

@media (max-width: 768px) {
    .story-circle-view {
        flex-direction: column;
    }
    
    .legend {
        width: 100%;
        border-left: none;
        border-top: 1px solid #e5e7eb;
    }
    
    .position-scenes {
        left: 50% !important;
        transform: translateX(-50%);
        max-width: 90%;
    }
    
    .unpositioned-panel {
        position: relative;
        width: 100%;
        margin: 1rem;
    }
}
</style>