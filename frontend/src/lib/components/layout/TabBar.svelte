<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ViewTab } from '$lib/types';

  export let tabs: ViewTab[];
  export let activeTab: string;

  const dispatch = createEventDispatcher();

  function selectTab(tabId: string) {
    if (tabId !== activeTab) {
      dispatch('change', tabId);
    }
  }
</script>

<div class="tab-bar">
  <div class="tabs">
    {#each tabs as tab (tab.id)}
      <button
        class="tab"
        class:active={tab.id === activeTab}
        on:click={() => selectTab(tab.id)}
        title="{tab.label} ({tab.shortcut})"
        type="button"
      >
        <span class="tab-icon">{tab.icon}</span>
        <span class="tab-label">{tab.label}</span>
      </button>
    {/each}
  </div>

  <div class="tab-actions">
    <slot name="actions" />
  </div>
</div>

<style>
  .tab-bar {
    display: flex;
    align-items: center;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    height: 40px;
    padding: 0 16px;
  }

  .tabs {
    display: flex;
    gap: 4px;
    flex: 1;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: transparent;
    border: none;
    border-radius: 4px 4px 0 0;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;
    position: relative;
  }

  .tab:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .tab.active {
    background: var(--bg-primary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-bottom-color: var(--bg-primary);
    margin-bottom: -1px;
  }

  .tab-icon {
    font-size: 16px;
  }

  .tab-label {
    @media (max-width: 768px) {
      display: none;
    }
  }

  .tab-actions {
    display: flex;
    gap: 8px;
  }
</style>
