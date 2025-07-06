<script lang="ts">
  import { assetStore } from '$lib/stores/assets';
  import AssetGrid from '../asset/AssetGrid.svelte';
  import AssetFilters from '../asset/AssetFilters.svelte';

  export let projectId: string;

  let selectedCategory = 'all';
  let searchQuery = '';

  $: assets = assetStore.getProjectAssets(projectId);
  $: filteredAssets = filterAssets(assets, selectedCategory, searchQuery);

  function filterAssets(assets: any[], category: string, query: string) {
    let filtered = assets;

    if (category !== 'all') {
      filtered = filtered.filter((a) => a.category === category);
    }

    if (query) {
      const q = query.toLowerCase();
      filtered = filtered.filter(
        (a) =>
          a.name.toLowerCase().includes(q) || a.metadata?.description?.toLowerCase().includes(q)
      );
    }

    return filtered;
  }
</script>

<div class="assets-view">
  <div class="assets-header">
    <h2>Project Assets</h2>
    <div class="header-actions">
      <input
        type="search"
        placeholder="Search assets..."
        bind:value={searchQuery}
        class="search-input"
      />
      <button type="button">Import Assets</button>
    </div>
  </div>

  <AssetFilters bind:selectedCategory />

  <div class="assets-content">
    <AssetGrid assets={filteredAssets} />
  </div>
</div>

<style>
  .assets-view {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .assets-header {
    padding: 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .assets-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }

  .header-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .search-input {
    width: 200px;
    padding: 6px 12px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 13px;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--color-primary);
  }

  .assets-content {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
  }
</style>
