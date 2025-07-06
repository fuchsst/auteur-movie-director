<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { api } from '$lib/api/client';
  import { setError } from '$lib/stores';

  const dispatch = createEventDispatcher();

  let name = '';
  let narrative_structure = 'three-act';
  let quality = 'standard';
  let director = '';
  let description = '';
  let creating = false;

  const narrativeOptions = [
    { value: 'three-act', label: 'Three Act Structure' },
    { value: 'hero-journey', label: "Hero's Journey" },
    { value: 'beat-sheet', label: 'Beat Sheet' },
    { value: 'story-circle', label: 'Story Circle' }
  ];

  const qualityOptions = [
    { value: 'low', label: 'Low (Draft/Preview)' },
    { value: 'standard', label: 'Standard (Production)' },
    { value: 'high', label: 'High (Final Render)' }
  ];

  async function handleSubmit() {
    if (!name.trim()) {
      setError('Project name is required');
      return;
    }

    creating = true;
    try {
      await api.createProject({
        name: name.trim(),
        narrative_structure,
        quality,
        director: director.trim() || undefined,
        description: description.trim() || undefined
      });

      dispatch('created');
    } catch (error) {
      setError(`Failed to create project: ${error}`);
    } finally {
      creating = false;
    }
  }

  function handleCancel() {
    dispatch('close');
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      handleCancel();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="dialog-backdrop" on:click={handleCancel}>
  <div class="dialog" on:click|stopPropagation>
    <div class="dialog-header">
      <h2>Create New Project</h2>
      <button class="close-btn" on:click={handleCancel} aria-label="Close"> × </button>
    </div>

    <form on:submit|preventDefault={handleSubmit}>
      <div class="form-group">
        <label for="name">Project Name *</label>
        <input
          id="name"
          type="text"
          bind:value={name}
          placeholder="My Amazing Film"
          required
          autofocus
        />
      </div>

      <div class="form-group">
        <label for="narrative">Narrative Structure</label>
        <select id="narrative" bind:value={narrative_structure}>
          {#each narrativeOptions as option}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </div>

      <div class="form-group">
        <label for="quality">Default Quality</label>
        <select id="quality" bind:value={quality}>
          {#each qualityOptions as option}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </div>

      <div class="form-group">
        <label for="director">Director Name</label>
        <input id="director" type="text" bind:value={director} placeholder="Your name" />
      </div>

      <div class="form-group">
        <label for="description">Description</label>
        <textarea
          id="description"
          bind:value={description}
          placeholder="Brief description of your project"
          rows="3"
        ></textarea>
      </div>

      <div class="dialog-footer">
        <button type="button" class="btn" on:click={handleCancel}> Cancel </button>
        <button type="submit" class="btn btn-primary" disabled={creating}>
          {creating ? 'Creating...' : 'Create Project'}
        </button>
      </div>
    </form>
  </div>
</div>

<style>
  .dialog-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .dialog {
    background: var(--surface);
    border-radius: 0.5rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
  }

  .dialog-header h2 {
    margin: 0;
    font-size: 1.25rem;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: var(--text-secondary);
    cursor: pointer;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.25rem;
    transition: all 0.2s;
  }

  .close-btn:hover {
    background: var(--border-color);
    color: var(--text-primary);
  }

  form {
    padding: 1.5rem;
    overflow-y: auto;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  input,
  select,
  textarea {
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: var(--background);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    color: var(--text-primary);
    font-size: 0.875rem;
    transition: border-color 0.2s;
  }

  input:focus,
  select:focus,
  textarea:focus {
    outline: none;
    border-color: var(--primary-color);
  }

  textarea {
    resize: vertical;
    min-height: 60px;
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding: 1.5rem;
    border-top: 1px solid var(--border-color);
    background: var(--background);
  }
</style>
