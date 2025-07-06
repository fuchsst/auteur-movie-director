<script lang="ts">
  import { currentProject, setError } from '$lib/stores';
  import { selectionStore } from '$lib/stores/selection';
  import FileUpload from '$lib/components/upload/FileUpload.svelte';
  import { AssetType } from '$lib/types/project';

  // Asset categories with their target directories
  const assetCategories = [
    {
      type: AssetType.CHARACTER,
      label: 'Characters',
      icon: '👤',
      directory: '01_Assets/Characters'
    },
    {
      type: AssetType.STYLE,
      label: 'Styles',
      icon: '🎨',
      directory: '01_Assets/Styles'
    },
    {
      type: AssetType.LOCATION,
      label: 'Locations',
      icon: '📍',
      directory: '01_Assets/Locations'
    },
    {
      type: AssetType.MUSIC,
      label: 'Music',
      icon: '🎵',
      directory: '01_Assets/Music'
    },
    {
      type: AssetType.SCRIPT,
      label: 'Scripts',
      icon: '📄',
      directory: '01_Assets/Scripts'
    }
  ];

  let selectedCategory: AssetType = AssetType.CHARACTER;
  let searchQuery = '';

  // Filter assets based on search
  function filterAssets(assets: any[], query: string) {
    if (!query) return assets;
    const lowerQuery = query.toLowerCase();
    return assets.filter((asset) => asset.name.toLowerCase().includes(lowerQuery));
  }

  function handleCategorySelect(type: AssetType) {
    selectedCategory = type;
  }

  function getAcceptedTypes(category: AssetType): string[] {
    switch (category) {
      case AssetType.CHARACTER:
        return ['.png', '.jpg', '.jpeg', '.safetensors', '.pt', '.pth'];
      case AssetType.STYLE:
        return ['.safetensors', '.ckpt', '.pt', '.pth', '.png', '.jpg'];
      case AssetType.LOCATION:
        return ['.png', '.jpg', '.jpeg', '.exr', '.hdr'];
      case AssetType.MUSIC:
        return ['.mp3', '.wav', '.aiff', '.flac', '.ogg'];
      case AssetType.SCRIPT:
        return ['.txt', '.md', '.pdf', '.docx', '.fountain'];
      default:
        return [];
    }
  }

  function getMetadataForCategory(category: AssetType): Record<string, any> {
    switch (category) {
      case AssetType.CHARACTER:
        // Will be populated by dialog in future
        return { character_name: 'New Character' };
      case AssetType.STYLE:
        return { style_name: 'New Style' };
      case AssetType.LOCATION:
        return { location_name: 'New Location' };
      default:
        return {};
    }
  }

  function handleFilesUploaded(event: CustomEvent) {
    console.log('Files uploaded:', event.detail.files);
    // Refresh asset list (to be implemented)

    // For now, select the first uploaded file as a demo
    if (event.detail.files && event.detail.files.length > 0) {
      const file = event.detail.files[0];
      const assetType = selectedCategory.toLowerCase() as
        | 'character'
        | 'location'
        | 'style'
        | 'music';
      selectionStore.selectAsset(file.name, assetType);
    }
  }

  // Demo function to handle asset selection
  function handleAssetClick(
    assetId: string,
    assetType: 'character' | 'location' | 'style' | 'music'
  ) {
    selectionStore.selectAsset(assetId, assetType);
  }

  function handleUploadError(event: CustomEvent) {
    setError(event.detail.message);
  }
</script>

<div class="asset-browser">
  <div class="browser-header">
    <h3>Assets</h3>
    {#if $currentProject}
      <span class="project-indicator">{$currentProject.name}</span>
    {/if}
  </div>

  {#if !$currentProject}
    <div class="no-project">
      <p>Select a project to view assets</p>
    </div>
  {:else}
    <div class="search-bar">
      <input type="search" placeholder="Search assets..." bind:value={searchQuery} />
    </div>

    <div class="category-tabs">
      {#each assetCategories as category}
        <button
          class="category-tab"
          class:active={selectedCategory === category.type}
          on:click={() => handleCategorySelect(category.type)}
        >
          <span class="tab-icon">{category.icon}</span>
          <span class="tab-label">{category.label}</span>
        </button>
      {/each}
    </div>

    <div class="asset-grid">
      <FileUpload
        category={selectedCategory}
        acceptedTypes={getAcceptedTypes(selectedCategory)}
        multiple={true}
        metadata={getMetadataForCategory(selectedCategory)}
        on:uploaded={handleFilesUploaded}
        on:error={handleUploadError}
      />
    </div>
  {/if}
</div>

<style>
  .asset-browser {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .browser-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 1rem;
  }

  .browser-header h3 {
    margin: 0;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
  }

  .project-indicator {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    background: var(--primary-color);
    color: white;
    border-radius: 0.25rem;
  }

  .no-project {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    text-align: center;
  }

  .search-bar {
    margin-bottom: 1rem;
  }

  .search-bar input {
    width: 100%;
    padding: 0.5rem;
    background: var(--background);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    color: var(--text-primary);
    font-size: 0.875rem;
  }

  .search-bar input:focus {
    outline: none;
    border-color: var(--primary-color);
  }

  .category-tabs {
    display: flex;
    gap: 0.25rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }

  .category-tab {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.375rem 0.75rem;
    background: var(--surface);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
  }

  .category-tab:hover {
    background: var(--background);
    color: var(--text-primary);
  }

  .category-tab.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
  }

  .tab-icon {
    font-size: 1rem;
  }

  .asset-grid {
    flex: 1;
    overflow-y: auto;
  }
</style>
