<script lang="ts">
    export let groupName: string;
    export let sceneCount: number;
    export let totalDuration: number;

    function formatDuration(minutes: number) {
        const hours = Math.floor(minutes / 60);
        const mins = Math.round(minutes % 60);
        return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
    }
</script>

<div class="scene-group">
    <div class="group-header">
        <h3 class="group-title">{groupName}</h3>
        <div class="group-stats">
            <span class="stat">{sceneCount} scenes</span>
            <span class="stat divider">•</span>
            <span class="stat">{formatDuration(totalDuration)} total</span>
        </div>
    </div>
    <div class="group-content">
        <slot />
    </div>
</div>

<style>
.scene-group {
    margin-bottom: 1rem;
}

.group-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding: 0.5rem 0;
    border-bottom: 2px solid #e5e7eb;
}

.group-title {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
}

.group-stats {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: #6b7280;
}

.stat.divider {
    opacity: 0.5;
}

.group-content {
    padding: 0;
}

@media (max-width: 768px) {
    .group-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
    
    .group-stats {
        font-size: 0.75rem;
    }
}
</style>