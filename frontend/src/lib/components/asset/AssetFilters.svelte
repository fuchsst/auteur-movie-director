<script lang="ts">
  export let selectedCategory = 'all';

  const categories = [
    { id: 'all', label: 'All Assets', icon: '📋' },
    { id: 'characters', label: 'Characters', icon: '👤' },
    { id: 'locations', label: 'Locations', icon: '🏞️' },
    { id: 'styles', label: 'Styles', icon: '🎨' },
    { id: 'music', label: 'Music', icon: '🎵' }
  ];
</script>

<div class="asset-filters">
  <div class="filter-tabs">
    {#each categories as category}
      <button
        class="filter-tab"
        class:active={selectedCategory === category.id}
        on:click={() => (selectedCategory = category.id)}
        type="button"
      >
        <span class="tab-icon">{category.icon}</span>
        <span class="tab-label">{category.label}</span>
      </button>
    {/each}
  </div>
</div>

<style>
  .asset-filters {
    padding: 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
  }

  .filter-tabs {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .filter-tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 20px;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;
  }

  .filter-tab:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .filter-tab.active {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .tab-icon {
    font-size: 16px;
  }
</style>
