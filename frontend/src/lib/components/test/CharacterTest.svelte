<script lang="ts">
  /**
   * Test component for character asset data model.
   * This is for testing foundation functionality only.
   */
  import { onMount } from 'svelte';
  import { charactersApi, type CharacterAsset } from '$lib/api/characters';

  export let projectId: string;

  let characters: CharacterAsset[] = [];
  let loading = false;
  let error: string | null = null;

  // Test character creation
  let newCharacterName = '';
  let newCharacterDescription = '';

  async function loadCharacters() {
    loading = true;
    error = null;

    try {
      const response = await charactersApi.listCharacters(projectId);
      characters = response.characters;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load characters';
    } finally {
      loading = false;
    }
  }

  async function createCharacter() {
    if (!newCharacterName.trim()) return;

    loading = true;
    error = null;

    try {
      const response = await charactersApi.createCharacter(projectId, {
        name: newCharacterName,
        description: newCharacterDescription
      });

      if (response.success) {
        // Reload characters list
        await loadCharacters();

        // Clear form
        newCharacterName = '';
        newCharacterDescription = '';
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to create character';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadCharacters();
  });
</script>

<div class="character-test">
  <h3>Character Data Model Test</h3>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  <div class="create-form">
    <h4>Add Character (Foundation Only)</h4>
    <input
      type="text"
      placeholder="Character name"
      bind:value={newCharacterName}
      disabled={loading}
    />
    <textarea
      placeholder="Character description"
      bind:value={newCharacterDescription}
      disabled={loading}
      rows="3"
    />
    <button on:click={createCharacter} disabled={loading || !newCharacterName.trim()}>
      Add Character
    </button>
  </div>

  <div class="characters-list">
    <h4>Characters ({characters.length})</h4>
    {#if loading}
      <p>Loading...</p>
    {:else if characters.length === 0}
      <p>No characters yet</p>
    {:else}
      <ul>
        {#each characters as character}
          <li>
            <strong>{character.name}</strong>
            {#if character.description}
              <p>{character.description}</p>
            {/if}
            <small>
              Status: {character.loraTrainingStatus}
              {#if character.usage.length > 0}
                | Used in {character.usage.length} shots
              {/if}
            </small>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<style>
  .character-test {
    padding: 1rem;
    max-width: 600px;
  }

  .error {
    color: red;
    padding: 0.5rem;
    margin-bottom: 1rem;
    border: 1px solid red;
    border-radius: 4px;
    background-color: #fee;
  }

  .create-form {
    margin-bottom: 2rem;
    padding: 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
  }

  .create-form input,
  .create-form textarea {
    display: block;
    width: 100%;
    margin-bottom: 0.5rem;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
  }

  .create-form button {
    padding: 0.5rem 1rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .create-form button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .characters-list ul {
    list-style: none;
    padding: 0;
  }

  .characters-list li {
    padding: 1rem;
    margin-bottom: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: #f8f9fa;
  }

  .characters-list p {
    margin: 0.5rem 0;
    color: #666;
  }

  .characters-list small {
    color: #888;
  }
</style>
