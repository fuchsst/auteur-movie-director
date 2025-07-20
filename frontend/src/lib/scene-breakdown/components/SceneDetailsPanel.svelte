<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, fly } from 'svelte/transition';
    import { sceneBreakdownStore } from '../stores/scene-breakdown-store';
    import SceneCharacterManager from './SceneCharacterManager.svelte';
    import SceneAssetManager from './SceneAssetManager.svelte';
    import StoryBeatEditor from './StoryBeatEditor.svelte';
    import SceneAnalysis from './SceneAnalysis.svelte';
    import type { SceneBreakdown } from '../types/scene-breakdown';

    export let scene: SceneBreakdown;

    const dispatch = createEventDispatcher();

    let activeTab = 'details';
    let isEditing = false;
    let editedScene: Partial<SceneBreakdown> = {};
    let analysis: any = null;
    let isAnalyzing = false;

    $: sceneData = scene;

    const tabs = [
        { id: 'details', label: 'Details', icon: '📝' },
        { id: 'characters', label: 'Characters', icon: '👥' },
        { id: 'assets', label: 'Assets', icon: '🎭' },
        { id: 'beats', label: 'Story Beats', icon: '🎯' },
        { id: 'analysis', label: 'Analysis', icon: '📊' }
    ];

    onMount(async () => {
        editedScene = { ...scene };
        await loadAnalysis();
    });

    async function loadAnalysis() {
        isAnalyzing = true;
        try {
            analysis = await sceneBreakdownStore.analyzeScene(scene.scene_id);
        } catch (error) {
            console.error('Failed to load analysis:', error);
        } finally {
            isAnalyzing = false;
        }
    }

    function handleTabChange(tab: string) {
        activeTab = tab;
    }

    function handleEdit() {
        isEditing = true;
        editedScene = { ...scene };
    }

    function handleCancel() {
        isEditing = false;
        editedScene = {};
    }

    async function handleSave() {
        try {
            await sceneBreakdownStore.updateScene(scene.scene_id, editedScene);
            isEditing = false;
            editedScene = {};
            await loadAnalysis();
        } catch (error) {
            console.error('Failed to save scene:', error);
        }
    }

    async function handleCharacterUpdate(characters: any[]) {
        await sceneBreakdownStore.updateScene(scene.scene_id, { characters });
        await loadAnalysis();
    }

    async function handleAssetUpdate(assets: any[]) {
        await sceneBreakdownStore.updateScene(scene.scene_id, { assets });
    }

    async function handleStoryBeatsUpdate(story_beats: any[]) {
        await sceneBreakdownStore.updateScene(scene.scene_id, { story_beats });
        await loadAnalysis();
    }

    function formatDuration(minutes: number) {
        const mins = Math.floor(minutes);
        const secs = Math.round((minutes - mins) * 60);
        return secs > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${mins}m`;
    }
</script>

<div class="scene-details-panel" in:fly={{ x: 300, duration: 300 }}>
    <div class="panel-header">
        <h2>Scene Details</h2>
        <button class="close-btn" on:click={() => dispatch('close')}>
            ×
        </button>
    </div>

    <div class="panel-content">
        <!-- Tab Navigation -->
        <div class="tab-navigation">
            {#each tabs as tab}
                <button
                    class="tab-button"
                    class:active={activeTab === tab.id}
                    on:click={() => handleTabChange(tab.id)}
                >
                    <span>{tab.icon}</span>
                    <span>{tab.label}</span>
                </button>
            {/each}
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
            {#if activeTab === 'details'}
                <div class="details-section">
                    {#if isEditing}
                        <div class="edit-form">
                            <div class="form-group">
                                <label>Title</label>
                                <input
                                    type="text"
                                    bind:value={editedScene.title}
                                    placeholder="Scene title"
                                />
                            </div>

                            <div class="form-row">
                                <div class="form-group">
                                    <label>Scene Number</label>
                                    <input
                                        type="number"
                                        bind:value={editedScene.scene_number}
                                        min="1"
                                    />
                                </div>
                                <div class="form-group">
                                    <label>Act</label>
                                    <select bind:value={editedScene.act_number}>
                                        <option value={1}>Act 1</option>
                                        <option value={2}>Act 2</option>
                                        <option value={3}>Act 3</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Chapter</label>
                                    <input
                                        type="number"
                                        bind:value={editedScene.chapter_number}
                                        placeholder="Optional"
                                    />
                                </div>
                            </div>

                            <div class="form-row">
                                <div class="form-group">
                                    <label>Scene Type</label>
                                    <select bind:value={editedScene.scene_type}>
                                        <option value="action">Action</option>
                                        <option value="dialogue">Dialogue</option>
                                        <option value="transition">Transition</option>
                                        <option value="montage">Montage</option>
                                        <option value="flashback">Flashback</option>
                                        <option value="dream">Dream</option>
                                        <option value="introspection">Introspection</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Duration (minutes)</label>
                                    <input
                                        type="number"
                                        bind:value={editedScene.duration_minutes}
                                        step="0.5"
                                        min="0.5"
                                    />
                                </div>
                            </div>

                            <div class="form-row">
                                <div class="form-group">
                                    <label>Location</label>
                                    <input
                                        type="text"
                                        bind:value={editedScene.location}
                                        placeholder="Scene location"
                                    />
                                </div>
                                <div class="form-group">
                                    <label>Time of Day</label>
                                    <input
                                        type="text"
                                        bind:value={editedScene.time_of_day}
                                        placeholder="Morning, Afternoon, etc."
                                    />
                                </div>
                            </div>

                            <div class="form-group">
                                <label>Slug Line</label>
                                <input
                                    type="text"
                                    bind:value={editedScene.slug_line}
                                    placeholder="INT. LOCATION - TIME"
                                />
                            </div>

                            <div class="form-group">
                                <label>Synopsis</label>
                                <textarea
                                    bind:value={editedScene.synopsis}
                                    rows="3"
                                    placeholder="Brief scene description"
                                />
                            </div>

                            <div class="form-group">
                                <label>Description</label>
                                <textarea
                                    bind:value={editedScene.description}
                                    rows="4"
                                    placeholder="Detailed scene description"
                                />
                            </div>

                            <div class="form-group">
                                <label>Script Notes</label>
                                <textarea
                                    bind:value={editedScene.script_notes}
                                    rows="3"
                                    placeholder="Director's notes"
                                />
                            </div>

                            <div class="form-row">
                                <div class="form-group">
                                    <label>Status</label>
                                    <select bind:value={editedScene.status}>
                                        <option value="draft">Draft</option>
                                        <option value="in_progress">In Progress</option>
                                        <option value="complete">Complete</option>
                                        <option value="review">Review</option>
                                        <option value="approved">Approved</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Completion %</label>
                                    <input
                                        type="range"
                                        bind:value={editedScene.completion_percentage}
                                        min="0"
                                        max="100"
                                    />
                                    <span>{editedScene.completion_percentage || 0}%</span>
                                </div>
                            </div>

                            <div class="form-row">
                                <div class="form-group">
                                    <label>Conflict Level</label>
                                    <input
                                        type="range"
                                        bind:value={editedScene.conflict_level}
                                        min="1"
                                        max="5"
                                    />
                                    <span>{editedScene.conflict_level || 1}/5</span>
                                </div>
                                <div class="form-group">
                                    <label>Stakes Level</label>
                                    <input
                                        type="range"
                                        bind:value={editedScene.stakes_level}
                                        min="1"
                                        max="5"
                                    />
                                    <span>{editedScene.stakes_level || 1}/5</span>
                                </div>
                            </div>

                            <div class="form-group">
                                <label>Story Circle Position</label>
                                <select bind:value={editedScene.story_circle_position}>
                                    <option value="">None</option>
                                    <option value={1}>1 - You</option>
                                    <option value={2}>2 - Need</option>
                                    <option value={3}>3 - Go</option>
                                    <option value={4}>4 - Search</option>
                                    <option value={5}>5 - Find</option>
                                    <option value={6}>6 - Take</option>
                                    <option value={7}>7 - Return</option>
                                    <option value={8}>8 - Change</option>
                                </select>
                            </div>

                            <div class="form-actions">
                                <button class="btn btn-secondary" on:click={handleCancel}>
                                    Cancel
                                </button>
                                <button class="btn btn-primary" on:click={handleSave}>
                                    Save Changes
                                </button>
                            </div>
                        </div>
                    {:else}
                        <div class="scene-info">
                            <div class="info-header">
                                <h3>{scene.title}</h3>
                                <button class="btn btn-secondary" on:click={handleEdit}>
                                    Edit
                                </button>
                            </div>

                            <div class="info-grid">
                                <div class="info-item">
                                    <label>Scene Number</label>
                                    <span>{scene.scene_number}</span>
                                </div>
                                <div class="info-item">
                                    <label>Act</label>
                                    <span>Act {scene.act_number}</span>
                                </div>
                                {#if scene.chapter_number}
                                    <div class="info-item">
                                        <label>Chapter</label>
                                        <span>{scene.chapter_number}</span>
                                    </div>
                                {/if}
                                <div class="info-item">
                                    <label>Duration</label>
                                    <span>{formatDuration(scene.duration_minutes)}</span>
                                </div>
                                <div class="info-item">
                                    <label>Type</label>
                                    <span class="capitalize">{scene.scene_type}</span>
                                </div>
                                <div class="info-item">
                                    <label>Status</label>
                                    <span class="capitalize">{scene.status}</span>
                                </div>
                                <div class="info-item">
                                    <label>Completion</label>
                                    <span>{scene.completion_percentage}%</span>
                                </div>
                                <div class="info-item">
                                    <label>Location</label>
                                    <span>{scene.location}</span>
                                </div>
                                <div class="info-item">
                                    <label>Time</label>
                                    <span>{scene.time_of_day}</span>
                                </div>
                            </div>

                            {#if scene.story_circle_position}
                                <div class="info-item">
                                    <label>Story Circle</label>
                                    <span>Position {scene.story_circle_position}</span>
                                </div>
                            {/if}

                            <div class="info-item full-width">
                                <label>Synopsis</label>
                                <p>{scene.synopsis || 'No synopsis available'}</p>
                            </div>

                            <div class="info-item full-width">
                                <label>Description</label>
                                <p>{scene.description || 'No description available'}</p>
                            </div>

                            {#if scene.script_notes}
                                <div class="info-item full-width">
                                    <label>Script Notes</label>
                                    <p>{scene.script_notes}</p>
                                </div>
                            {/if}
                        </div>
                    {/if}
                </div>
            {:else if activeTab === 'characters'}
                <SceneCharacterManager
                    {scene}
                    on:update={(e) => handleCharacterUpdate(e.detail)}
                />
            {:else if activeTab === 'assets'}
                <SceneAssetManager
                    {scene}
                    on:update={(e) => handleAssetUpdate(e.detail)}
                />
            {:else if activeTab === 'beats'}
                <StoryBeatEditor
                    {scene}
                    on:update={(e) => handleStoryBeatsUpdate(e.detail)}
                />
            {:else if activeTab === 'analysis'}
                <SceneAnalysis
                    {analysis}
                    {isAnalyzing}
                    on:refresh={loadAnalysis}
                />
            {/if}
        </div>

        <!-- Action Buttons -->
        <div class="panel-actions">
            <button class="btn btn-danger" on:click={() => dispatch('delete')}>
                Delete Scene
            </button>
        </div>
    </div>
</div>

<style>
.scene-details-panel {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: white;
    border-left: 1px solid #e5e7eb;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #e5e7eb;
    background: #f9fafb;
}

.panel-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #111827;
}

.close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6b7280;
    padding: 0;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s;
}

.close-btn:hover {
    background: #f3f4f6;
    color: #374151;
}

.panel-content {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}

.tab-navigation {
    display: flex;
    border-bottom: 1px solid #e5e7eb;
    background: white;
    position: sticky;
    top: 0;
    z-index: 10;
}

.tab-button {
    flex: 1;
    padding: 0.75rem 0.5rem;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    color: #6b7280;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.2s;
    border-bottom: 2px solid transparent;
}

.tab-button:hover {
    background: #f9fafb;
    color: #374151;
}

.tab-button.active {
    color: #3b82f6;
    border-bottom-color: #3b82f6;
    background: #eff6ff;
}

.tab-content {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
}

.details-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.edit-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.form-group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
}

.form-group input,
.form-group select,
.form-group textarea {
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 0.875rem;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
}

.scene-info {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.info-header h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #111827;
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1rem;
}

.info-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.info-item label {
    font-size: 0.75rem;
    font-weight: 500;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.info-item span,
.info-item p {
    font-size: 0.875rem;
    color: #111827;
}

.info-item.full-width {
    grid-column: 1 / -1;
}

.info-item.full-width p {
    margin: 0;
    line-height: 1.5;
    color: #6b7280;
}

.capitalize {
    text-transform: capitalize;
}

.panel-actions {
    padding: 1rem;
    border-top: 1px solid #e5e7eb;
    background: #f9fafb;
}

.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
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

.btn-secondary {
    background: #6b7280;
    color: white;
}

.btn-secondary:hover {
    background: #4b5563;
}

.btn-danger {
    background: #ef4444;
    color: white;
}

.btn-danger:hover {
    background: #dc2626;
}

@media (max-width: 768px) {
    .tab-button {
        font-size: 0.75rem;
        padding: 0.5rem 0.25rem;
    }
    
    .tab-button span:last-child {
        display: none;
    }
    
    .form-row {
        grid-template-columns: 1fr;
    }
    
    .info-grid {
        grid-template-columns: 1fr 1fr;
    }
}
</style>