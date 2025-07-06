<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { takesApi, type GenerationParams } from '$lib/api/takes';
  import Icon from '$lib/components/common/Icon.svelte';
  import { progressStore } from '$lib/stores/progress';

  export let projectId: string;
  export let shotId: string;
  export let isOpen = false;

  const dispatch = createEventDispatcher<{
    close: void;
    generated: { takeId: string; taskId: string };
  }>();

  let generating = false;
  let error: string | null = null;

  // Generation parameters
  let params: GenerationParams = {
    model: 'stable-diffusion-xl',
    seed: Math.floor(Math.random() * 1000000),
    prompt: '',
    negativePrompt: '',
    steps: 20,
    cfg: 7.5
  };

  let quality = 'standard';

  const qualityOptions = [
    { value: 'draft', label: 'Draft', description: 'Fast preview, lower quality' },
    { value: 'standard', label: 'Standard', description: 'Production quality' },
    { value: 'high', label: 'High', description: 'Maximum quality, slower' }
  ];

  const modelOptions = [
    { value: 'stable-diffusion-xl', label: 'Stable Diffusion XL' },
    { value: 'flux-1', label: 'Flux 1.0' },
    { value: 'dall-e-3', label: 'DALL-E 3' }
  ];

  function close() {
    isOpen = false;
    dispatch('close');
  }

  async function generate() {
    if (!params.prompt.trim()) {
      error = 'Please enter a prompt';
      return;
    }

    try {
      generating = true;
      error = null;

      const response = await takesApi.createTake(projectId, shotId, {
        generationParams: params,
        quality
      });

      // Add to progress tracking
      if (response.taskId) {
        progressStore.addTask({
          id: response.taskId,
          title: `Generating ${response.takeId}`,
          progress: 0,
          status: 'running'
        });
      }

      dispatch('generated', {
        takeId: response.takeId,
        taskId: response.taskId || ''
      });

      close();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to start generation';
      console.error('Generation error:', e);
    } finally {
      generating = false;
    }
  }

  function randomizeSeed() {
    params.seed = Math.floor(Math.random() * 1000000);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && !generating) {
      close();
    }
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="dialog-backdrop" on:click={close} on:keydown={handleKeydown}>
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="dialog" on:click|stopPropagation on:keydown|stopPropagation>
      <div class="dialog-header">
        <h2>Generate New Take</h2>
        <button class="btn-icon" on:click={close} disabled={generating}>
          <Icon name="x" size={20} />
        </button>
      </div>

      <div class="dialog-content">
        {#if error}
          <div class="error-banner">
            <Icon name="alert-circle" size={16} />
            <span>{error}</span>
          </div>
        {/if}

        <div class="form-group">
          <label for="quality">Quality Level</label>
          <div class="quality-options">
            {#each qualityOptions as option}
              <label class="quality-option">
                <input
                  type="radio"
                  name="quality"
                  value={option.value}
                  bind:group={quality}
                  disabled={generating}
                />
                <div class="quality-info">
                  <span class="quality-label">{option.label}</span>
                  <span class="quality-description">{option.description}</span>
                </div>
              </label>
            {/each}
          </div>
        </div>

        <div class="form-group">
          <label for="model">Model</label>
          <select id="model" bind:value={params.model} disabled={generating}>
            {#each modelOptions as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
        </div>

        <div class="form-group">
          <label for="prompt">Prompt</label>
          <textarea
            id="prompt"
            bind:value={params.prompt}
            placeholder="Describe what you want to generate..."
            rows="3"
            disabled={generating}
          ></textarea>
        </div>

        <div class="form-group">
          <label for="negative-prompt">Negative Prompt (optional)</label>
          <textarea
            id="negative-prompt"
            bind:value={params.negativePrompt}
            placeholder="Describe what you want to avoid..."
            rows="2"
            disabled={generating}
          ></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="seed">
              Seed
              <button
                type="button"
                class="btn-icon small"
                on:click={randomizeSeed}
                title="Randomize seed"
                disabled={generating}
              >
                <Icon name="shuffle" size={14} />
              </button>
            </label>
            <input
              id="seed"
              type="number"
              bind:value={params.seed}
              min="0"
              max="999999"
              disabled={generating}
            />
          </div>

          <div class="form-group">
            <label for="steps">Steps</label>
            <input
              id="steps"
              type="number"
              bind:value={params.steps}
              min="1"
              max="150"
              disabled={generating}
            />
          </div>

          <div class="form-group">
            <label for="cfg">CFG Scale</label>
            <input
              id="cfg"
              type="number"
              bind:value={params.cfg}
              min="1"
              max="20"
              step="0.5"
              disabled={generating}
            />
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn-secondary" on:click={close} disabled={generating}> Cancel </button>
        <button class="btn-primary" on:click={generate} disabled={generating}>
          {#if generating}
            <Icon name="loader" size={16} class="animate-spin" />
            Generating...
          {:else}
            <Icon name="play" size={16} />
            Generate
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .dialog-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .dialog {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    width: 90%;
    max-width: 600px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  }

  .dialog-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
  }

  .dialog-header h2 {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .dialog-content {
    padding: 1.5rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .dialog-footer {
    display: flex;
    gap: 0.75rem;
    justify-content: flex-end;
    padding: 1.5rem;
    border-top: 1px solid var(--border-color);
    background: var(--bg-secondary);
  }

  .error-banner {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: var(--error-bg);
    color: var(--error-color);
    border-radius: 0.375rem;
    font-size: 0.875rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    padding: 0.5rem 0.75rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    color: var(--text-primary);
    font-size: 0.875rem;
    transition: border-color 0.2s;
  }

  .form-group input:focus,
  .form-group select:focus,
  .form-group textarea:focus {
    outline: none;
    border-color: var(--primary-color);
  }

  .form-group input:disabled,
  .form-group select:disabled,
  .form-group textarea:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .form-group textarea {
    resize: vertical;
    min-height: 60px;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1rem;
  }

  .quality-options {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .quality-option {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.75rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .quality-option:hover {
    border-color: var(--primary-color);
  }

  .quality-option input[type='radio'] {
    margin-top: 0.125rem;
  }

  .quality-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    flex: 1;
  }

  .quality-label {
    font-weight: 500;
    color: var(--text-primary);
    font-size: 0.875rem;
  }

  .quality-description {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .btn-icon {
    padding: 0.375rem;
    background: transparent;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    color: var(--text-secondary);
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .btn-icon:hover:not(:disabled) {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .btn-icon.small {
    padding: 0.25rem;
  }

  .btn-icon:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary,
  .btn-secondary {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.2s;
    cursor: pointer;
    border: none;
  }

  .btn-primary {
    background: var(--primary-color);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: var(--primary-hover);
  }

  .btn-secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--bg-tertiary);
  }

  .btn-primary:disabled,
  .btn-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>
