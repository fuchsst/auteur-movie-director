<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { fade } from 'svelte/transition';
    import type { SceneBreakdown } from '../types/scene-breakdown';

    export let scene: SceneBreakdown;

    const dispatch = createEventDispatcher();

    let isAddingCharacter = false;
    let newCharacter = {
        character_id: '',
        character_name: '',
        role_in_scene: '',
        dialogue_lines: 0,
        screen_time: 0,
        emotions: [],
        objectives: []
    };
    let newEmotion = '';
    let newObjective = '';

    $: characters = scene.characters || [];

    function handleAddCharacter() {
        isAddingCharacter = true;
        newCharacter = {
            character_id: `char_${Date.now()}`,
            character_name: '',
            role_in_scene: '',
            dialogue_lines: 0,
            screen_time: 0,
            emotions: [],
            objectives: []
        };
    }

    function handleSaveCharacter() {
        if (newCharacter.character_name.trim()) {
            const updatedCharacters = [...characters, { ...newCharacter }];
            dispatch('update', updatedCharacters);
            isAddingCharacter = false;
        }
    }

    function handleRemoveCharacter(index: number) {
        const updatedCharacters = characters.filter((_, i) => i !== index);
        dispatch('update', updatedCharacters);
    }

    function handleUpdateCharacter(index: number, updates: any) {
        const updatedCharacters = characters.map((char, i) => 
            i === index ? { ...char, ...updates } : char
        );
        dispatch('update', updatedCharacters);
    }

    function handleAddEmotion() {
        if (newEmotion.trim()) {
            newCharacter.emotions = [...newCharacter.emotions, newEmotion.trim()];
            newEmotion = '';
        }
    }

    function handleRemoveEmotion(index: number) {
        newCharacter.emotions = newCharacter.emotions.filter((_, i) => i !== index);
    }

    function handleAddObjective() {
        if (newObjective.trim()) {
            newCharacter.objectives = [...newCharacter.objectives, newObjective.trim()];
            newObjective = '';
        }
    }

    function handleRemoveObjective(index: number) {
        newCharacter.objectives = newCharacter.objectives.filter((_, i) => i !== index);
    }
</script>

<div class="character-manager" in:fade={{ duration: 200 }}>
    <div class="manager-header">
        <h3>Characters in Scene</h3>
        <button class="btn btn-primary" on:click={handleAddCharacter}>
            + Add Character
        </button>
    </div>

    {#if characters.length === 0}
        <div class="empty-state">
            <div class="empty-icon">👥</div>
            <p>No characters assigned to this scene yet.</p>
            <button class="btn btn-secondary" on:click={handleAddCharacter}>
                Add First Character
            </button>
        </div>
    {:else}
        <div class="characters-list">
            {#each characters as character, index}
                <div class="character-card" in:fade={{ duration: 200 }}>
                    <div class="character-header">
                        <h4>{character.character_name}</h4>
                        <button class="btn btn-sm btn-danger" on:click={() => handleRemoveCharacter(index)}>
                            ×
                        </button>
                    </div>

                    <div class="character-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Name</label>
                                <input
                                    type="text"
                                    value={character.character_name}
                                    on:input={(e) => handleUpdateCharacter(index, { character_name: e.target.value })}
                                    placeholder="Character name"
                                />
                            </div>
                            <div class="form-group">
                                <label>Role</label>
                                <input
                                    type="text"
                                    value={character.role_in_scene}
                                    on:input={(e) => handleUpdateCharacter(index, { role_in_scene: e.target.value })}
                                    placeholder="Role in scene"
                                />
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Dialogue Lines</label>
                                <input
                                    type="number"
                                    value={character.dialogue_lines}
                                    on:input={(e) => handleUpdateCharacter(index, { dialogue_lines: parseInt(e.target.value) || 0 })}
                                    min="0"
                                />
                            </div>
                            <div class="form-group">
                                <label>Screen Time (min)</label>
                                <input
                                    type="number"
                                    step="0.5"
                                    value={character.screen_time}
                                    on:input={(e) => handleUpdateCharacter(index, { screen_time: parseFloat(e.target.value) || 0 })}
                                    min="0"
                                />
                            </div>
                        </div>

                        <div class="form-group">
                            <label>Emotions</label>
                            <div class="tags-input">
                                {#each character.emotions as emotion}
                                    <span class="tag">{emotion}</span>
                                {/each}
                                <input
                                    type="text"
                                    placeholder="Add emotion..."
                                    on:keydown={(e) => {
                                        if (e.key === 'Enter') {
                                            e.preventDefault();
                                            const newEmotions = [...character.emotions, e.target.value.trim()];
                                            handleUpdateCharacter(index, { emotions: newEmotions });
                                            e.target.value = '';
                                        }
                                    }}
                                />
                            </div>
                        </div>

                        <div class="form-group">
                            <label>Objectives</label>
                            <div class="tags-input">
                                {#each character.objectives as objective}
                                    <span class="tag">{objective}</span>
                                {/each}
                                <input
                                    type="text"
                                    placeholder="Add objective..."
                                    on:keydown={(e) => {
                                        if (e.key === 'Enter') {
                                            e.preventDefault();
                                            const newObjectives = [...character.objectives, e.target.value.trim()];
                                            handleUpdateCharacter(index, { objectives: newObjectives });
                                            e.target.value = '';
                                        }
                                    }}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    {/if}

    {#if isAddingCharacter}
        <div class="add-character-form" in:fade={{ duration: 200 }}>
            <h4>Add New Character</h4>
            
            <div class="form-row">
                <div class="form-group">
                    <label>Name *</label>
                    <input bind:value={newCharacter.character_name} placeholder="Character name" />
                </div>
                <div class="form-group">
                    <label>Role in Scene *</label>
                    <input bind:value={newCharacter.role_in_scene} placeholder="e.g., Protagonist, Antagonist" />
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label>Dialogue Lines</label>
                    <input type="number" bind:value={newCharacter.dialogue_lines} min="0" />
                </div>
                <div class="form-group">
                    <label>Screen Time (minutes)</label>
                    <input type="number" step="0.5" bind:value={newCharacter.screen_time} min="0" />
                </div>
            </div>

            <div class="form-group">
                <label>Emotions</label>
                <div class="tags-input">
                    {#each newCharacter.emotions as emotion, i}
                        <span class="tag">
                            {emotion}
                            <button on:click={() => handleRemoveEmotion(i)}>×</button>
                        </span>
                    {/each}
                    <input bind:value={newEmotion} placeholder="Add emotion..." on:keydown={(e) => e.key === 'Enter' && handleAddEmotion()} />
                </div>
            </div>

            <div class="form-group">
                <label>Objectives</label>
                <div class="tags-input">
                    {#each newCharacter.objectives as objective, i}
                        <span class="tag">
                            {objective}
                            <button on:click={() => handleRemoveObjective(i)}>×</button>
                        </span>
                    {/each}
                    <input bind:value={newObjective} placeholder="Add objective..." on:keydown={(e) => e.key === 'Enter' && handleAddObjective()} />
                </div>
            </div>

            <div class="form-actions">
                <button class="btn btn-secondary" on:click={() => isAddingCharacter = false}>
                    Cancel
                </button>
                <button class="btn btn-primary" on:click={handleSaveCharacter}>
                    Save Character
                </button>
            </div>
        </div>
    {/if}
</div>

<style>
.character-manager {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
}

.manager-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.manager-header h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
    color: #6b7280;
}

.empty-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}

.characters-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.character-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
}

.character-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.character-header h4 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #111827;
}

.character-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.75rem;
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

.form-group input {
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 0.875rem;
}

.tags-input {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    min-height: 2rem;
    padding: 0.25rem;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    align-items: center;
}

.tag {
    background: #e0e7ff;
    color: #3730a3;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.tag button {
    background: none;
    border: none;
    color: #6366f1;
    cursor: pointer;
    font-size: 0.875rem;
    padding: 0;
    line-height: 1;
}

.add-character-form {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
}

.add-character-form h4 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    font-weight: 600;
    color: #111827;
}

.form-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 1rem;
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

.btn-sm {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
}
</style>