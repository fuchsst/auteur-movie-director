<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import FunctionRunnerIntegration from './FunctionRunnerIntegration.svelte';
  import QualitySelector from './QualitySelector.svelte';
  import FunctionRunnerQualitySelector from './FunctionRunnerQualitySelector.svelte';

  export let showExample: string = 'simple';
  export let templateId: string = 'character_portrait';

  const dispatch = createEventDispatcher();

  let selectedQuality = 'standard';
  let inputs = {
    prompt: 'A cinematic portrait of a detective in film noir style',
    style: 'film-noir',
    aspect_ratio: '16:9'
  };

  function handleQualityChange(event: CustomEvent) {
    console.log('Quality changed:', event.detail);
    selectedQuality = event.detail.tier;
  }

  function handleTaskSubmitted(event: CustomEvent) {
    console.log('Task submitted:', event.detail);
    dispatch('taskSubmitted', event.detail);
  }

  function handleTaskProgress(event: CustomEvent) {
    console.log('Task progress:', event.detail);
    dispatch('taskProgress', event.detail);
  }

  function handleTaskComplete(event: CustomEvent) {
    console.log('Task complete:', event.detail);
    dispatch('taskComplete', event.detail);
  }

  function handleTaskError(event: CustomEvent) {
    console.error('Task error:', event.detail);
    dispatch('taskError', event.detail);
  }
</script>

<div class="quality-integration-examples">
  <h2>Quality Integration Examples</h2>

  <div class="example-tabs">
    <button 
      class:active={showExample === 'simple'} 
      on:click={() => showExample = 'simple'}
    >
      Simple Quality Selector
    </button>
    <button 
      class:active={showExample === 'advanced'} 
      on:click={() => showExample = 'advanced'}
    >
      Advanced Integration
    </button>
    <button 
      class:active={showExample === 'full'} 
      on:click={() => showExample = 'full'}
    >
      Full Function Runner
    </button>
  </div>

  {#if showExample === 'simple'}
    <div class="example-section">
      <h3>Simple Quality Selector</h3>
      <p>Basic three-tier quality selection with persistent preferences.</p>
      
      <QualitySelector 
        taskType="character_portrait" 
        bind:selectedTier={selectedQuality}
        on:qualityChange={handleQualityChange}
      />
      
      <div class="code-example">
        <pre><code>{
  "quality": "{selectedQuality}",
  "taskType": "character_portrait"
}</code></pre>
      </div>
    </div>
  {/if}

  {#if showExample === 'advanced'}
    <div class="example-section">
      <h3>Advanced Quality Selector</h3>
      <p>Quality selection with function runner mapping and advanced options.</p>
      
      <FunctionRunnerQualitySelector
        {templateId}
        taskType="character_portrait"
        bind:selectedQuality
        showFunctionRunnerMapping={true}
        on:qualityChange={handleQualityChange}
      />
    </div>
  {/if}

  {#if showExample === 'full'}
    <div class="example-section">
      <h3>Full Function Runner Integration</h3>
      <p>Complete integration with template loading and task submission.</p>
      
      <FunctionRunnerIntegration
        {templateId}
        {inputs}
        taskType="character_portrait"
        bind:selectedQuality
        showAdvanced={true}
        on:submitted={handleTaskSubmitted}
        on:progress={handleTaskProgress}
        on:complete={handleTaskComplete}
        on:error={handleTaskError}
      />
    </div>
  {/if}
</div>

<style>
  .quality-integration-examples {
    padding: 2rem;
    max-width: 800px;
    margin: 0 auto;
  }

  h2 {
    margin-bottom: 1.5rem;
    color: var(--color-text);
  }

  .example-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--color-border);
  }

  .example-tabs button {
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    transition: all 0.2s ease;
  }

  .example-tabs button.active,
  .example-tabs button:hover {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
  }

  .example-section {
    background: var(--color-background-subtle);
    border-radius: 12px;
    padding: 2rem;
    border: 1px solid var(--color-border);
  }

  .example-section h3 {
    margin-bottom: 0.5rem;
    color: var(--color-text);
  }

  .example-section p {
    color: var(--color-text-secondary);
    margin-bottom: 1.5rem;
  }

  .code-example {
    margin-top: 1rem;
    padding: 1rem;
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 8px;
  }

  .code-example pre {
    margin: 0;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 0.875rem;
    color: var(--color-text);
  }

  .code-example code {
    background: none;
    border: none;
    padding: 0;
  }
</style>