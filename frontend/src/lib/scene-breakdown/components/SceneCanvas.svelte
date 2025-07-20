<script lang="ts">
    import { onMount, createEventDispatcher } from 'svelte';
    import { dndzone } from 'svelte-dnd-action';
    import { fade } from 'svelte/transition';
    import { sceneBreakdownStore } from '../stores/scene-breakdown-store';
    import type { SceneSummary } from '../types/scene-breakdown';

    export let scenes: SceneSummary[] = [];
    export let selectedSceneId: string | null = null;

    const dispatch = createEventDispatcher();

    let canvasWidth = 1200;
    let canvasHeight = 800;
    let scale = 1;
    let offsetX = 0;
    let offsetY = 0;
    let isDragging = false;
    let dragStart = { x: 0, y: 0 };
    let canvasRef: HTMLDivElement;

    $: positionedScenes = scenes.filter(scene => scene.canvas_position);
    $: unpositionedScenes = scenes.filter(scene => !scene.canvas_position);

    onMount(() => {
        if (canvasRef) {
            const rect = canvasRef.getBoundingClientRect();
            canvasWidth = rect.width;
            canvasHeight = rect.height;
        }
    });

    function handleSceneSelect(sceneId: string) {
        dispatch('sceneSelect', sceneId);
    }

    function handleSceneUpdate(sceneId: string, updates: any) {
        dispatch('sceneUpdate', { sceneId, updates });
    }

    function handleCanvasClick(event: MouseEvent) {
        if (event.target === canvasRef) {
            dispatch('sceneDeselect');
        }
    }

    function handleSceneDrag(event: CustomEvent) {
        const { items, info } = event.detail;
        if (info.trigger === 'draggedOver') {
            const sceneId = info.id;
            const rect = canvasRef.getBoundingClientRect();
            const x = (info.x - rect.left) / scale - offsetX;
            const y = (info.y - rect.top) / scale - offsetY;
            
            handleSceneUpdate(sceneId, {
                canvas_position: { x: Math.max(0, x), y: Math.max(0, y) }
            });
        }
    }

    function handleWheel(event: WheelEvent) {
        event.preventDefault();
        const delta = event.deltaY > 0 ? 0.9 : 1.1;
        scale = Math.max(0.5, Math.min(2, scale * delta));
    }

    function handleMouseDown(event: MouseEvent) {
        if (event.target === canvasRef) {
            isDragging = true;
            dragStart = { x: event.clientX - offsetX, y: event.clientY - offsetY };
            canvasRef.style.cursor = 'grabbing';
        }
    }

    function handleMouseMove(event: MouseEvent) {
        if (isDragging) {
            offsetX = event.clientX - dragStart.x;
            offsetY = event.clientY - dragStart.y;
        }
    }

    function handleMouseUp() {
        isDragging = false;
        if (canvasRef) {
            canvasRef.style.cursor = 'grab';
        }
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
        const mins = Math.floor(minutes);
        return `${mins}m`;
    }
</script>

<div class="scene-canvas-container">
    <div class="canvas-controls">
        <div class="control-group">
            <button class="btn" on:click={() => { scale = 1; offsetX = 0; offsetY = 0; }}>
                Reset View
            </button>
            <span class="zoom-level">{Math.round(scale * 100)}%</span>
        </div>
        <div class="control-group">
            <button class="btn" on:click={() => scale = Math.max(0.5, scale - 0.1)}>
                -
            </button>
            <button class="btn" on:click={() => scale = Math.min(2, scale + 0.1)}>
                +
            </button>
        </div>
    </div>

    <div 
        class="scene-canvas"
        bind:this={canvasRef}
        on:click={handleCanvasClick}
        on:wheel={handleWheel}
        on:mousedown={handleMouseDown}
        on:mousemove={handleMouseMove}
        on:mouseup={handleMouseUp}
        on:mouseleave={handleMouseUp}
        style="cursor: {isDragging ? 'grabbing' : 'grab'}"
    >
        <div 
            class="canvas-content"
            style="
                transform: translate({offsetX}px, {offsetY}px) scale({scale});
                width: {canvasWidth}px;
                height: {canvasHeight}px;
            "
        >
            <!-- Grid background -->
            <div class="grid-background"></div>
            
            <!-- Connection lines -->
            <svg class="connections" width="100%" height="100%">
                {#each positionedScenes as scene}
                    {#each scene.connections || [] as connection}
                        {@const connectedScene = scenes.find(s => s.scene_id === connection)}
                        {#if connectedScene && connectedScene.canvas_position}
                            <line 
                                x1={scene.canvas_position.x + 75}
                                y1={scene.canvas_position.y + 50}
                                x2={connectedScene.canvas_position.x + 75}
                                y2={connectedScene.canvas_position.y + 50}
                                stroke="#d1d5db"
                                stroke-width="1"
                                stroke-dasharray="5,5"
                            />
                        {/if}
                    {/each}
                {/each}
            </svg>

            <!-- Positioned scenes -->
            {#each positionedScenes as scene (scene.scene_id)}
                <div 
                    class="canvas-scene"
                    class:selected={selectedSceneId === scene.scene_id}
                    style="
                        left: {scene.canvas_position.x}px;
                        top: {scene.canvas_position.y}px;
                        border-color: {getStatusColor(scene.status)};
                    "
                    on:click={() => handleSceneSelect(scene.scene_id)}
                    use:dndzone={{ items: [scene], type: 'scene' }}
                    on:finalize={handleSceneDrag}
                    in:fade={{ duration: 200 }}
                >
                    <div class="canvas-scene-number">{scene.scene_number}</div>
                    <div class="canvas-scene-title">{scene.title}</div>
                    <div class="canvas-scene-meta">
                        {formatDuration(scene.duration_minutes)} • {scene.character_count} chars
                    </div>
                    <div class="canvas-scene-progress">
                        <div 
                            class="progress-fill" 
                            style="width: {scene.completion_percentage}%"
                        ></div>
                    </div>
                </div>
            {/each}

            <!-- Unpositioned scenes panel -->
            {#if unpositionedScenes.length > 0}
                <div class="unpositioned-panel" in:fade={{ duration: 200 }}>
                    <h4>Unpositioned Scenes</h4>
                    <div class="unpositioned-list">
                        {#each unpositionedScenes as scene (scene.scene_id)}
                            <div 
                                class="unpositioned-scene"
                                draggable="true"
                                on:click={() => handleSceneSelect(scene.scene_id)}
                                use:dndzone={{ items: [scene], type: 'scene' }}
                                on:finalize={handleSceneDrag}
                            >
                                <span>{scene.scene_number}. {scene.title}</span>
                                <span class="duration">{formatDuration(scene.duration_minutes)}</span>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
.scene-canvas-container {
    height: 100%;
    position: relative;
    background: #f8fafc;
    overflow: hidden;
}

.canvas-controls {
    position: absolute;
    top: 1rem;
    right: 1rem;
    display: flex;
    gap: 0.5rem;
    z-index: 100;
    background: white;
    padding: 0.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.control-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.btn {
    padding: 0.25rem 0.5rem;
    border: 1px solid #d1d5db;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
}

.btn:hover {
    background: #f3f4f6;
}

.zoom-level {
    font-size: 0.875rem;
    color: #6b7280;
    min-width: 3rem;
    text-align: center;
}

.scene-canvas {
    width: 100%;
    height: 100%;
    overflow: hidden;
    position: relative;
}

.canvas-content {
    position: relative;
    transform-origin: 0 0;
    transition: transform 0.1s ease-out;
}

.grid-background {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
        linear-gradient(to right, #e5e7eb 1px, transparent 1px),
        linear-gradient(to bottom, #e5e7eb 1px, transparent 1px);
    background-size: 20px 20px;
    opacity: 0.5;
}

.connections {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: none;
}

.canvas-scene {
    position: absolute;
    width: 150px;
    height: 100px;
    background: white;
    border: 2px solid;
    border-radius: 8px;
    padding: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.canvas-scene:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.canvas-scene.selected {
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
    transform: scale(1.05);
}

.canvas-scene-number {
    position: absolute;
    top: -8px;
    left: -8px;
    width: 20px;
    height: 20px;
    background: var(--border-color);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: bold;
}

.canvas-scene-title {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.canvas-scene-meta {
    font-size: 0.75rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
}

.canvas-scene-progress {
    height: 4px;
    background: #e5e7eb;
    border-radius: 2px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: var(--border-color);
    transition: width 0.3s ease;
}

.unpositioned-panel {
    position: absolute;
    top: 1rem;
    left: 1rem;
    width: 200px;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    z-index: 50;
}

.unpositioned-panel h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
}

.unpositioned-list {
    max-height: 200px;
    overflow-y: auto;
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
    cursor: pointer;
    transition: all 0.2s;
}

.unpositioned-scene:hover {
    background: #f3f4f6;
}

.duration {
    color: #6b7280;
    font-size: 0.75rem;
}
</style>