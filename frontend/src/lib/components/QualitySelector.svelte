<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { userPreferences } from '$lib/stores/user-preferences';
  import { qualityTiersApi } from '$lib/api/quality-tiers';
  import { onMount } from 'svelte';

  export let taskType: string = 'character_portrait';
  export let selectedTier: string = 'standard';

  const dispatch = createEventDispatcher();

  interface QualityTier {
    tier: string;
    label: string;
    description: string;
    icon: string;
    color: string;
    estimatedTime?: string;
    parameters: any;
  }

  let loading = true;
  let error: string | null = null;
  let qualityTiers: QualityTier[] = [];

  const tierDisplay = {
    low: {
      label: 'Low',
      icon: '⚡',
      color: 'var(--color-low, #ff9500)',
      description: 'Fast generation, basic quality'
    },
    standard: {
      label: 'Standard',
      icon: '⚖️',
      color: 'var(--color-standard, #007aff)',
      description: 'Balanced quality and speed'
    },
    high: {
      label: 'High',
      icon: '✨',
      color: 'var(--color-high, #34c759)',
      description: 'Maximum quality, slower generation'
    }
  };

  async function loadQualityTiers() {
    loading = true;
    error = null;
    
    try {
      const userPref = userPreferences.getQualityPreference(taskType);
      if (userPref) {
        selectedTier = userPref;
      }

      const response = await qualityTiersApi.getQualityTiers(taskType);
      qualityTiers = response.available_tiers.map(tier => ({
        tier: tier.tier,
        label: tierDisplay[tier.tier as keyof typeof tierDisplay]?.label || tier.tier,
        description: tier.description,
        icon: tierDisplay[tier.tier as keyof typeof tierDisplay]?.icon || '•',
        color: tierDisplay[tier.tier as keyof typeof tierDisplay]?.color || '#666',
        estimatedTime: tier.estimated_time,
        parameters: tier.parameters_preview
      }));
      
      loading = false;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load quality tiers';
      loading = false;
    }
  }

  onMount(() => {
    loadQualityTiers();
  });

  function selectTier(tier: string) {
    selectedTier = tier;
    userPreferences.setQualityPreference(taskType, tier);
    dispatch('qualityChange', { 
      tier, 
      taskType, 
      config: qualityTiers.find(t => t.tier === tier) 
    });
  }

  $: if (taskType) {
    loadQualityTiers();
  }
</script>

<div class="quality-selector">
  <label class="selector-label">Quality Tier</label>
  
  {#if loading}
    <div class="loading">
      <span class="spinner"></span>
      <span>Loading quality options...</span>
    </div>
  {:else if error}
    <div class="error">
      <span class="error-icon">⚠️</span>
      <span>{error}</span>
    </div>
  {:else if qualityTiers.length > 0}
    <div class="tier-options">
      {#each qualityTiers as tier (tier.tier)}
        <button
          class="tier-option"
          class:selected={selectedTier === tier.tier}
          style="--tier-color: {tier.color}"
          on:click={() => selectTier(tier.tier)}
          title={tier.description}
        >
          <span class="tier-icon">{tier.icon}</span>
          <span class="tier-label">{tier.label}</span>
          {#if tier.estimatedTime}
            <span class="tier-time">{tier.estimatedTime}</span>
          {/if}
        </button>
      {/each}
    </div>
    
    <div class="tier-details">
      {#if selectedTier}
        {@const selected = qualityTiers.find(t => t.tier === selectedTier)}
        {#if selected}
          <div class="selected-info">
            <strong>{selected.label}</strong>
            <p>{selected.description}</p>
            {#if selected.estimatedTime}
              <small>Est. time: {selected.estimatedTime}</small>
            {/if}
          </div>
        {/if}
      {/if}
    </div>
  {/if}
</div>

<style>
  .quality-selector {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .selector-label {
    font-weight: 600;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
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

  .tier-options {
    display: flex;
    gap: 0.75rem;
  }

  .tier-option {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    padding: 1rem;
    min-width: 100px;
    border: 2px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-background);
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: inherit;
  }

  .tier-option:hover {
    border-color: var(--tier-color);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .tier-option.selected {
    border-color: var(--tier-color);
    background: var(--tier-color);
    color: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .tier-icon {
    font-size: 1.5rem;
    margin-bottom: 0.25rem;
  }

  .tier-label {
    font-size: 0.875rem;
    font-weight: 600;
  }

  .tier-time {
    font-size: 0.75rem;
    opacity: 0.8;
  }

  .tier-details {
    margin-top: 0.5rem;
  }

  .selected-info {
    padding: 0.75rem;
    background: var(--color-background-subtle);
    border-radius: 8px;
    border-left: 3px solid var(--tier-color);
  }

  .selected-info strong {
    display: block;
    margin-bottom: 0.25rem;
    color: var(--color-text);
  }

  .selected-info p {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .selected-info small {
    font-size: 0.75rem;
    color: var(--color-text-muted);
  }
</style>