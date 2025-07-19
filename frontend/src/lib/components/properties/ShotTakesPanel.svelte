<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import TakesGallery from '$lib/components/takes/TakesGallery.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import type { TakeMetadata } from '$lib/api/takes';

  export let projectId: string;
  export let shotId: string;
  export let expanded = true;

  const dispatch = createEventDispatcher<{
    takeSelected: { take: TakeMetadata };
    generateTake: void;
    activeTakeChanged: { takeId: string };
  }>();

  function handleTakeSelect(event: CustomEvent<{ take: TakeMetadata }>) {
    dispatch('takeSelected', event.detail);
  }

  function handleGenerate() {
    dispatch('generateTake');
  }

  function handleActivateChanged(event: CustomEvent<{ takeId: string }>) {
    dispatch('activeTakeChanged', event.detail);
  }
</script>

<div class="shot-takes-panel" class:expanded>
  <div 
    class="panel-header" 
    on:click={() => (expanded = !expanded)} 
    on:keydown={(e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        expanded = !expanded;
      }
    }}
    role="button" 
    tabindex="0"
    aria-expanded={expanded}
  >
    <div class="header-content">
      <Icon name="film" size={16} />
      <span>Takes</span>
    </div>
    <Icon name="chevron-down" size={16} class={expanded ? 'expanded' : 'collapsed'} />
  </div>

  {#if expanded}
    <div class="panel-content">
      <TakesGallery
        {projectId}
        {shotId}
        compact={true}
        on:select={handleTakeSelect}
        on:generate={handleGenerate}
        on:activateChanged={handleActivateChanged}
      />
    </div>
  {/if}
</div>

<style>
  .shot-takes-panel {
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    background: var(--bg-secondary);
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: var(--bg-tertiary);
    cursor: pointer;
    user-select: none;
    transition: background 0.2s;
  }

  .panel-header:hover {
    background: var(--bg-secondary);
  }

  .header-content {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .panel-content {
    padding: 1rem;
    max-height: 500px;
    overflow: auto;
  }

  :global(.shot-takes-panel .chevron-down.collapsed) {
    transform: rotate(-90deg);
  }

  :global(.shot-takes-panel .chevron-down.expanded) {
    transform: rotate(0deg);
  }

  :global(.shot-takes-panel .chevron-down) {
    transition: transform 0.2s;
  }
</style>
