<script lang="ts">
  import { onMount } from 'svelte';
  import { templateLibraryService } from '$lib/canvas/services/template-library';
  import { canvasStore } from '$lib/canvas/core/canvas-store';
  import type { CanvasTemplate } from '$lib/canvas/services/template-library';

  export let isOpen = false;

  let templates = [];
  let categories = [];
  let isLoading = false;
  let searchQuery = '';
  let selectedCategory = 'all';
  let sortBy = 'downloads';
  let sortOrder = 'desc';

  $: templates = $templateLibraryService.templates;
  $: categories = $templateLibraryService.categories;
  $: isLoading = $templateLibraryService.isLoading;

  onMount(() => {
    // Subscribe to service updates
    const unsubscribe = templateLibraryService.getStore().subscribe(() => {
      // Store is updated automatically
    });

    return unsubscribe;
  });

  async function handleSearch() {
    await templateLibraryService.searchTemplates(searchQuery);
  }

  async function handleCategoryChange(category: string) {
    selectedCategory = category;
    await templateLibraryService.filterByCategory(category);
  }

  async function handleSortChange(newSortBy: string) {
    sortBy = newSortBy;
    await templateLibraryService.sortTemplates(sortBy, sortOrder);
  }

  async function handleApplyTemplate(template: CanvasTemplate) {
    try {
      // Load template data into canvas
      canvasStore.update(state => ({
        ...state,
        nodes: template.data.nodes,
        edges: template.data.edges,
        viewport: template.data.viewport,
        selectedNodes: [],
        selectedEdges: []
      }));

      // Close the library
      isOpen = false;
    } catch (error) {
      console.error('Failed to apply template:', error);
    }
  }

  async function handleToggleFavorite(templateId: string) {
    await templateLibraryService.toggleFavorite(templateId);
  }

  async function handleExportTemplate(template: CanvasTemplate) {
    try {
      const jsonData = await templateLibraryService.exportTemplate(template.id);
      const blob = new Blob([jsonData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `${template.name.replace(/\s+/g, '-').toLowerCase()}.json`;
      a.click();
      
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export template:', error);
    }
  }

  async function handleShareTemplate(template: CanvasTemplate) {
    try {
      const shareUrl = await templateLibraryService.shareTemplate(template.id);
      alert(`Template shared! URL: ${shareUrl}`);
    } catch (error) {
      console.error('Failed to share template:', error);
    }
  }

  function getDifficultyColor(difficulty: string): string {
    const colors = {
      beginner: 'text-green-600',
      intermediate: 'text-yellow-600',
      advanced: 'text-orange-600',
      expert: 'text-red-600'
    };
    return colors[difficulty] || 'text-gray-600';
  }

  function getDifficultyIcon(difficulty: string): string {
    const icons = {
      beginner: '🟢',
      intermediate: '🟡',
      advanced: '🟠',
      expert: '🔴'
    };
    return icons[difficulty] || '⚪';
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">Template Library</h2>
          <p class="text-sm text-gray-600 mt-1">Choose from pre-built canvas templates</p>
        </div>
        <button 
          on:click={() => isOpen = false}
          class="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex h-[75vh]">
        <!-- Sidebar -->
        <div class="w-64 border-r bg-gray-50 p-4 overflow-y-auto">
          <!-- Search -->
          <div class="mb-6">
            <input
              type="text"
              bind:value={searchQuery}
              on:input={handleSearch}
              placeholder="Search templates..."
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <!-- Categories -->
          <div class="mb-6">
            <h3 class="text-sm font-semibold text-gray-900 mb-3">Categories</h3>
            <div class="space-y-1">
              {#each categories as category}
                <button
                  on:click={() => handleCategoryChange(category.id)}
                  class="w-full text-left px-3 py-2 text-sm rounded-md transition-colors {selectedCategory === category.id ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'}"
                >
                  <div class="flex items-center space-x-2">
                    <span>{category.icon}</span>
                    <span>{category.name}</span>
                    <span class="ml-auto text-xs text-gray-500">{category.count}</span>
                  </div>
                </button>
              {/each}
            </div>
          </div>

          <!-- Sort Options -->
          <div>
            <h3 class="text-sm font-semibold text-gray-900 mb-3">Sort By</h3>
            <select
              bind:value={sortBy}
              on:change={() => handleSortChange(sortBy)}
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="name">Name</option>
              <option value="downloads">Downloads</option>
              <option value="rating">Rating</option>
              <option value="created">Created</option>
            </select>
          </div>
        </div>

        <!-- Template Grid -->
        <div class="flex-1 overflow-y-auto p-6">
          {#if isLoading}
            <div class="flex items-center justify-center h-64">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          {:else if templates.length === 0}
            <div class="text-center py-12">
              <div class="text-4xl mb-4">📋</div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
              <p class="text-gray-600">Try adjusting your search or filters</p>
            </div>
          {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {#each templates as template}
                <div class="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                  <!-- Thumbnail -->
                  <div class="bg-gray-100 h-32 flex items-center justify-center">
                    <div class="text-2xl">{template.thumbnail || '📊'}</div>
                  </div>

                  <!-- Content -->
                  <div class="p-4">
                    <div class="flex items-start justify-between mb-2">
                      <h3 class="text-sm font-semibold text-gray-900 truncate">{template.name}</h3>
                      <button
                        on:click={() => handleToggleFavorite(template.id)}
                        class="text-yellow-500 hover:text-yellow-600"
                        title="Toggle favorite"
                      >
                        {template.metadata.author === 'System' ? '⭐' : '⭐'}
                      </button>
                    </div>

                    <p class="text-sm text-gray-600 mb-3">{template.description}</p>

                    <!-- Metadata -->
                    <div class="flex items-center space-x-4 text-xs text-gray-500 mb-3">
                      <span class="flex items-center">
                        {getDifficultyIcon(template.difficulty)}
                        <span class={getDifficultyColor(template.difficulty)}>{template.difficulty}</span>
                      </span>
                      <span>📥 {template.metadata.downloads}</span>
                      <span>⭐ {template.metadata.rating}</span>
                    </div>

                    <!-- Tags -->
                    <div class="flex flex-wrap gap-1 mb-4">
                      {#each template.tags.slice(0, 3) as tag}
                        <span class="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">{tag}</span>
                      {/each}
                      {#if template.tags.length > 3}
                        <span class="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">+{template.tags.length - 3}</span>
                      {/if}
                    </div>

                    <!-- Actions -->
                    <div class="flex space-x-2">
                      <button
                        on:click={() => handleApplyTemplate(template)}
                        class="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                      >
                        Apply
                      </button>
                      <button
                        on:click={() => handleExportTemplate(template)}
                        class="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                        title="Export template"
                      >
                        📤
                      </button>
                      <button
                        on:click={() => handleShareTemplate(template)}
                        class="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                        title="Share template"
                      >
                        🔗
                      </button>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .template-library {
    z-index: 1000;
  }
</style>