<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { fade } from 'svelte/transition';
    import type { SceneSummary } from '../types/scene-breakdown';

    export let scene: SceneSummary;
    export let isSelected: boolean = false;
    export let statusColor: string = '#3b82f6';

    const dispatch = createEventDispatcher();

    $: progressWidth = `${scene.completion_percentage}%`;

    function handleClick() {
        dispatch('click');
    }

    function handleQuickEdit(field: string, value: any) {
        dispatch('update', { [field]: value });
    }

    function getStatusIcon(status: string) {
        const icons = {
            draft: '✏️',
            in_progress: '🔄',
            complete: '✅',
            review: '👀',
            approved: '⭐'
        };
        return icons[status] || '⏳';
    }

    function formatDuration(minutes: number) {
        const mins = Math.floor(minutes);
        const secs = Math.round((minutes - mins) * 60);
        return secs > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${mins}m`;
    }
</script>

<div class="scene-card" 
     class:selected={isSelected}
     style="--status-color: {statusColor}"
     on:click={handleClick}
     in:fade={{ duration: 200 }}>
    
    <div class="scene-header">
        <div class="scene-number">{scene.scene_number}</div>
        <div class="scene-status">
            <span class="status-icon" title={scene.status}>{getStatusIcon(scene.status)}</span>
        </div>
    </div>

    <div class="scene-thumbnail">
        {#if scene.thumbnail_url}
            <img src={scene.thumbnail_url} alt={scene.title} />
        {:else}
            <div class="thumbnail-placeholder" style="background-color: {statusColor}20">
                <div class="placeholder-icon">🎬</div>
            </div>
        {/if}
    </div>

    <div class="scene-content">
        <h3 class="scene-title">{scene.title}</h3>
        <p class="scene-synopsis">{scene.synopsis || 'No description available'}</p>
        
        <div class="scene-meta">
            <span class="meta-item">📍 {scene.character_count} characters</span>
            <span class="meta-item">🎭 {scene.asset_count} assets</span>
            <span class="meta-item">⏱️ {formatDuration(scene.duration_minutes)}</span>
        </div>

        <div class="scene-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progressWidth}"></div>
            </div>
            <span class="progress-text">{Math.round(scene.completion_percentage)}%</span>
        </div>

        <div class="scene-tags">
            {#if scene.story_beat_count > 0}
                <span class="tag">{scene.story_beat_count} beats</span>
            {/if}
            <span class="tag act-tag">Act {scene.act_number}</span>
            {#if scene.chapter_number}
                <span class="tag chapter-tag">Ch {scene.chapter_number}</span>
            {/if}
        </div>
    </div>

    <div class="scene-actions">
        <button 
            class="quick-edit-btn"
            title="Quick edit"
            on:click|stopPropagation={() => dispatch('quickEdit')}
        >
            ⚙️
        </button>
    </div>
</div>

<style>
.scene-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 2px solid transparent;
    position: relative;
}

.scene-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.scene-card.selected {
    border-color: var(--status-color);
    box-shadow: 0 0 0 3px var(--status-color)20;
}

.scene-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: #f8fafc;
    border-bottom: 1px solid #e5e7eb;
}

.scene-number {
    background: var(--status-color);
    color: white;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    font-weight: 600;
}

.scene-status {
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.status-icon {
    font-size: 1rem;
}

.scene-thumbnail {
    height: 120px;
    background: #f3f4f6;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.scene-thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.thumbnail-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.placeholder-icon {
    font-size: 2rem;
    opacity: 0.5;
}

.scene-content {
    padding: 1rem;
}

.scene-title {
    margin: 0 0 0.5rem 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
    line-height: 1.3;
}

.scene-synopsis {
    margin: 0 0 0.75rem 0;
    font-size: 0.875rem;
    color: #6b7280;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.scene-meta {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
}

.meta-item {
    font-size: 0.75rem;
    color: #6b7280;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.scene-progress {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
}

.progress-bar {
    flex: 1;
    height: 4px;
    background: #e5e7eb;
    border-radius: 2px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: var(--status-color);
    transition: width 0.3s ease;
}

.progress-text {
    font-size: 0.75rem;
    font-weight: 500;
    color: #374151;
    min-width: 2rem;
    text-align: right;
}

.scene-tags {
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
}

.tag {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    background: #f3f4f6;
    color: #374151;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

.tag.act-tag {
    background: #dbeafe;
    color: #1e40af;
    border-color: #bfdbfe;
}

.tag.chapter-tag {
    background: #fef3c7;
    color: #92400e;
    border-color: #fcd34d;
}

.scene-actions {
    position: absolute;
    top: 8px;
    right: 8px;
    opacity: 0;
    transition: opacity 0.2s;
}

.scene-card:hover .scene-actions {
    opacity: 1;
}

.quick-edit-btn {
    background: rgba(0, 0, 0, 0.1);
    border: none;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 0.875rem;
    transition: background-color 0.2s;
}

.quick-edit-btn:hover {
    background: rgba(0, 0, 0, 0.2);
}

@media (max-width: 768px) {
    .scene-card {
        max-width: 100%;
    }
    
    .scene-meta {
        flex-direction: column;
        gap: 0.25rem;
    }
    
    .scene-tags {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .tag {
        align-self: flex-start;
    }
}
</style>