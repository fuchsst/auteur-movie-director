<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { onMount } from 'svelte';
  import { functionRunner } from '$lib/api/functionRunner';
  import QualitySelector from '$lib/components/QualitySelector.svelte';
  import { mapQualityTierToFunctionRunner } from '$lib/utils/quality-mapping';

  export let templateId: string;
  export let inputs: Record<string, any> = {};
  export let taskType: string = 'character_portrait';
  export let selectedQuality: string = 'standard';
  export let showAdvanced: boolean = false;

  const dispatch = createEventDispatcher();

  let loading = false;
  let error: string | null = null;
  let template: any = null;
  let estimatedTime: string = '';

  async function loadTemplate() {
    loading = true;
    error = null;
    
    try {
      template = await functionRunner.getTemplate(templateId);
      estimatedTime = template.estimated_time || '5-10 minutes';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load template';
    } finally {
      loading = false;
    }
  }

  async function submitTask() {
    if (!template) return;
    
    loading = true;
    error = null;
    
    try {
      const functionRunnerQuality = mapQualityTierToFunctionRunner(selectedQuality as any);
      
      const taskHandle = await functionRunner.submitTask(templateId, inputs, {
        quality: functionRunnerQuality,
        onProgress: (progress) => {
          dispatch('progress', progress);
        },
        onComplete: (result) => {
          dispatch('complete', result);
          loading = false;
        },
        onError: (err) => {
          error = err.message;
          loading = false;
          dispatch('error', err);
        }
      });
      
      dispatch('submitted', { taskHandle, quality: selectedQuality });
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to submit task';
      loading = false;
      dispatch('error', err);
    }
  }

  function handleQualityChange(event: CustomEvent) {
    selectedQuality = event.detail.tier;
    dispatch('qualityChange', event.detail);
  }

  onMount(() => {
    loadTemplate();
  });
</script>

<div class="function-runner-integration">
  {#if loading}
    <div class="loading">
      <span class="spinner"></span>
      <span>Loading template...</span>
    </div>
  {:else if error}
    <div class="error">
      <span class="error-icon">⚠️</span>
      <span>{error}</span>
    </div>
  {:else if template}
    <div class="integration-content">
      <div class="template-info">
        <h3>{template.name}</h3>
        <p>{template.description}</p>
        <small>Est. time: {estimatedTime}</small>
      </div>

      <div class="quality-section">
        <QualitySelector 
          {taskType} 
          {selectedQuality} 
          on:qualityChange={handleQualityChange}
        />
      </div>

      <div class="actions">
        <button 
          class="submit-button"
          disabled={loading}
          on:click={submitTask}
        >
          {loading ? 'Submitting...' : 'Submit Task'}
        </button>
      </div>

      {#if showAdvanced}
        <div class="advanced-info">
          <h4>Advanced Information</h4>
          <div class="info-grid">
            <div class="info-item">
              <span>Template ID:</span>
              <code>{templateId}</code>
            </div>
            <div class="info-item">
              <span>Quality Tier:</span>
              <code>{selectedQuality}</code>
            </div>
            <div class="info-item">
              <span>Function Runner Quality:</span>
              <code>{mapQualityTierToFunctionRunner(selectedQuality as any)}</code>
            </div>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .function-runner-integration {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .loading, .error {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
  }

  .loading {
    background: var(--color-background-subtle);
    color: var(--color-text-secondary);
  }

  .error {
    background: var(--color-error-subtle);
    color: var(--color-error);
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid var(--color-border);
    border-top: 2px solid var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .integration-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .template-info h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .template-info p {
    margin: 0 0 0.25rem 0;
    color: var(--color-text-secondary);
  }

  .template-info small {
    color: var(--color-text-muted);
  }

  .quality-section {
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 1rem;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
  }

  .submit-button {
    padding: 0.75rem 1.5rem;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: background-color 0.2s ease;
  }

  .submit-button:hover:not(:disabled) {
    background: var(--color-primary-hover);
  }

  .submit-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .advanced-info {
    padding: 1rem;
    background: var(--color-background-subtle);
    border-radius: 8px;
    border: 1px solid var(--color-border);
  }

  .advanced-info h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .info-grid {
    display: grid;
    gap: 0.5rem;
    font-size: 0.875rem;
  }

  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .info-item span:first-child {
    color: var(--color-text-secondary);
  }

  .info-item code {
    padding: 0.125rem 0.25rem;
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 3px;
    font-family: monospace;
    font-size: 0.75rem;
  }
</style>