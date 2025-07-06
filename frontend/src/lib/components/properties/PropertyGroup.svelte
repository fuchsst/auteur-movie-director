<script lang="ts">
  import { slide } from 'svelte/transition';

  export let name: string;
  export let defaultExpanded: boolean = true;
  export let icon: string = '';

  let expanded = defaultExpanded;

  function toggle() {
    expanded = !expanded;
  }
</script>

<div class="property-group">
  <button class="group-header" class:expanded on:click={toggle} type="button">
    <span class="group-toggle">
      <svg
        width="12"
        height="12"
        viewBox="0 0 12 12"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        class="toggle-icon"
      >
        <path
          d="M3 4.5L6 7.5L9 4.5"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </span>
    {#if icon}
      <span class="group-icon">{icon}</span>
    {/if}
    <span class="group-name">{name}</span>
  </button>

  {#if expanded}
    <div class="group-content" transition:slide={{ duration: 200 }}>
      <slot />
    </div>
  {/if}
</div>

<style>
  .property-group {
    margin-bottom: 1rem;
  }

  .group-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem;
    background: var(--color-surface-secondary, #2a2a2a);
    border: 1px solid var(--color-border, #3a3a3a);
    border-radius: 4px;
    cursor: pointer;
    text-align: left;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text-secondary, #b0b0b0);
    transition: all 0.2s ease;
  }

  .group-header:hover {
    background: var(--color-surface-hover, #333);
    color: var(--color-text-primary, #fff);
  }

  .group-header.expanded {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    border-bottom-color: transparent;
  }

  .group-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
  }

  .toggle-icon {
    transform: rotate(-90deg);
    transition: transform 0.2s ease;
  }

  .expanded .toggle-icon {
    transform: rotate(0deg);
  }

  .group-icon {
    font-size: 1rem;
  }

  .group-name {
    flex: 1;
  }

  .group-content {
    padding: 0.75rem;
    background: var(--color-surface-primary, #1a1a1a);
    border: 1px solid var(--color-border, #3a3a3a);
    border-top: none;
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
</style>
