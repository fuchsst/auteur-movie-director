<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Search, Calendar, Filter, RefreshCw } from 'lucide-svelte';
  
  export let timelineScale: 'hours' | 'days' | 'weeks' | 'months' = 'days';
  export let searchQuery = '';
  export let selectedFileType: string | null = null;
  export let fileTypes: string[] = [];
  
  const dispatch = createEventDispatcher();
  
  let showFilters = false;
  let searchInput: HTMLInputElement;
  
  const scaleOptions = [
    { value: 'hours', label: 'Hours' },
    { value: 'days', label: 'Days' },
    { value: 'weeks', label: 'Weeks' },
    { value: 'months', label: 'Months' }
  ];
  
  function handleSearch(event: Event) {
    const target = event.target as HTMLInputElement;
    searchQuery = target.value;
  }
  
  function clearSearch() {
    searchQuery = '';
    searchInput?.focus();
  }
  
  function handleRefresh() {
    dispatch('refresh');
  }
  
  function toggleFilters() {
    showFilters = !showFilters;
  }
  
  function clearFilters() {
    searchQuery = '';
    selectedFileType = null;
  }
  
  $: hasActiveFilters = searchQuery || selectedFileType;
</script>

<div class="timeline-controls">
  <div class="controls-row">
    <div class="search-container">
      <Search size={16} />
      <input
        bind:this={searchInput}
        type="text"
        placeholder="Search commits..."
        value={searchQuery}
        on:input={handleSearch}
        class="search-input"
      />
      {#if searchQuery}
        <button 
          class="clear-search" 
          on:click={clearSearch}
          aria-label="Clear search"
        >
          ×
        </button>
      {/if}
    </div>
    
    <div class="scale-selector">
      <Calendar size={16} />
      <select bind:value={timelineScale} class="scale-select">
        {#each scaleOptions as option}
          <option value={option.value}>{option.label}</option>
        {/each}
      </select>
    </div>
    
    <div class="action-buttons">
      <button
        class="filter-button"
        class:active={hasActiveFilters}
        on:click={toggleFilters}
        title="Filter commits"
      >
        <Filter size={16} />
        {#if hasActiveFilters}
          <span class="filter-badge" />
        {/if}
      </button>
      
      <button
        class="refresh-button"
        on:click={handleRefresh}
        title="Refresh history"
      >
        <RefreshCw size={16} />
      </button>
    </div>
  </div>
  
  {#if showFilters}
    <div class="filters-row">
      <div class="filter-group">
        <label for="file-type-filter">File Type:</label>
        <select 
          id="file-type-filter"
          bind:value={selectedFileType} 
          class="filter-select"
        >
          <option value={null}>All types</option>
          {#each fileTypes as type}
            <option value={type}>.{type}</option>
          {/each}
        </select>
      </div>
      
      {#if hasActiveFilters}
        <button class="clear-filters" on:click={clearFilters}>
          Clear all filters
        </button>
      {/if}
    </div>
  {/if}
</div>

<style>
  .timeline-controls {
    background: var(--surface-primary);
    border-bottom: 1px solid var(--border-color);
    padding: 1rem;
  }
  
  .controls-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }
  
  .search-container {
    flex: 1;
    min-width: 200px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    transition: border-color 0.2s;
  }
  
  .search-container:focus-within {
    border-color: var(--primary-color);
  }
  
  .search-input {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    font-size: 0.875rem;
    color: var(--text-primary);
  }
  
  .search-input::placeholder {
    color: var(--text-tertiary);
  }
  
  .clear-search {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 1.25rem;
    cursor: pointer;
    padding: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s;
  }
  
  .clear-search:hover {
    background: var(--surface-hover);
    color: var(--text-primary);
  }
  
  .scale-selector {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--text-secondary);
  }
  
  .scale-select {
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 0.375rem 0.75rem;
    font-size: 0.875rem;
    color: var(--text-primary);
    cursor: pointer;
  }
  
  .action-buttons {
    display: flex;
    gap: 0.5rem;
  }
  
  .filter-button,
  .refresh-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
  }
  
  .filter-button:hover,
  .refresh-button:hover {
    background: var(--surface-hover);
    color: var(--text-primary);
    border-color: var(--primary-color);
  }
  
  .filter-button.active {
    color: var(--primary-color);
    border-color: var(--primary-color);
  }
  
  .filter-badge {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 6px;
    height: 6px;
    background: var(--primary-color);
    border-radius: 50%;
  }
  
  .filters-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color);
  }
  
  .filter-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .filter-group label {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  
  .filter-select {
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 0.375rem 0.75rem;
    font-size: 0.875rem;
    color: var(--text-primary);
    cursor: pointer;
  }
  
  .clear-filters {
    margin-left: auto;
    padding: 0.375rem 0.75rem;
    background: none;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.8125rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .clear-filters:hover {
    background: var(--surface-hover);
    color: var(--text-primary);
    border-color: var(--primary-color);
  }
  
  @media (max-width: 768px) {
    .controls-row {
      gap: 0.5rem;
    }
    
    .search-container {
      min-width: 150px;
    }
    
    .scale-selector {
      display: none;
    }
  }
</style>