<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { canvasPopulationService } from '$lib/canvas/services/canvas-population';
  import { canvasStore } from '$lib/canvas/core/canvas-store';
  import type { ProjectData } from '$lib/types/project';
  import QualitySelector from '$lib/components/QualitySelector.svelte';

  export let project: ProjectData;
  export let isOpen = false;

  const dispatch = createEventDispatcher();

  let options = {
    structureType: 'auto' as 'three-act' | 'seven-point' | 'blake-snyder' | 'auto',
    includeAssets: true,
    includeScenes: true,
    includeShots: true,
    autoLayout: true,
    startPosition: { x: 100, y: 100 },
    quality: 'standard' as 'low' | 'standard' | 'high'
  };

  let isLoading = false;
  let previewVisible = false;
  let previewResult: any = null;

  $: if (isOpen && project) {
    generatePreview();
  }

  async function generatePreview() {
    if (!project) return;
    
    isLoading = true;
    try {
      previewResult = await canvasPopulationService.populateFromProject(project, {
        ...options,
        autoLayout: false // Don't layout for preview
      });
      previewVisible = true;
    } catch (error) {
      console.error('Preview generation failed:', error);
    } finally {
      isLoading = false;
    }
  }

  async function handlePopulate() {
    if (!project) return;
    
    isLoading = true;
    try {
      const result = await canvasPopulationService.populateFromProject(project, options);
      
      // Load into canvas store
      canvasStore.update(state => ({
        ...state,
        nodes: result.nodes,
        edges: result.edges,
        selectedNodes: [],
        selectedEdges: []
      }));

      dispatch('populated', { result });
      handleClose();
    } catch (error) {
      console.error('Population failed:', error);
    } finally {
      isLoading = false;
    }
  }

  function handleClose() {
    isOpen = false;
    previewVisible = false;
    previewResult = null;
    dispatch('close');
  }

  function handleResetOptions() {
    options = {
      structureType: 'auto',
      includeAssets: true,
      includeScenes: true,
      includeShots: true,
      autoLayout: true,
      startPosition: { x: 100, y: 100 }
    };
    generatePreview();
  }
</script>

{#if isOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">Populate Canvas</h2>
          <p class="text-sm text-gray-600 mt-1">Automatically generate story structure from project data</p>
        </div>
        <button 
          on:click={handleClose}
          class="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex h-[70vh]">
        <!-- Options Panel -->
        <div class="w-80 border-r bg-gray-50 p-6 overflow-y-auto">
          <h3 class="font-semibold text-gray-900 mb-4">Options</h3>
          
          <!-- Structure Type -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Story Structure
            </label>
            <select 
              bind:value={options.structureType}
              on:change={generatePreview}
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="auto">Auto-detect</option>
              <option value="three-act">Three-Act Structure</option>
              <option value="seven-point">Seven-Point Method</option>
              <option value="blake-snyder">Blake Snyder Beats</option>
            </select>
          </div>

          <!-- Content Options -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Include Content
            </label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input 
                  type="checkbox" 
                  bind:checked={options.includeAssets}
                  on:change={generatePreview}
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2 text-sm text-gray-700">Assets (Characters, Styles)</span>
              </label>
              <label class="flex items-center">
                <input 
                  type="checkbox" 
                  bind:checked={options.includeScenes}
                  on:change={generatePreview}
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2 text-sm text-gray-700">Scenes</span>
              </label>
              <label class="flex items-center">
                <input 
                  type="checkbox" 
                  bind:checked={options.includeShots}
                  on:change={generatePreview}
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2 text-sm text-gray-700">Shots</span>
              </label>
            </div>
          </div>

          <!-- Quality Selection -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Generation Quality
            </label>
            <QualitySelector 
              taskType="scene_generation" 
              bind:selectedTier={options.quality}
              on:qualityChange={(e) => {
                options.quality = e.detail.tier as 'low' | 'standard' | 'high';
                generatePreview();
              }}
            />
          </div>

          <!-- Layout Options -->
          <div class="mb-6">
            <label class="flex items-center">
              <input 
                type="checkbox" 
                bind:checked={options.autoLayout}
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span class="ml-2 text-sm font-medium text-gray-700">Auto-layout</span>
            </label>
            <p class="text-xs text-gray-500 mt-1">
              Automatically arrange nodes in a hierarchical layout
            </p>
          </div>

          <!-- Preview Stats -->
          {#if previewResult}
            <div class="mb-6">
              <h4 class="font-medium text-gray-900 mb-2">Preview</h4>
              <div class="bg-white p-3 rounded-md border">
                <div class="text-sm space-y-1">
                  <div class="flex justify-between">
                    <span class="text-gray-600">Story Nodes:</span>
                    <span class="font-medium">{previewResult.metadata.nodeCount}</span>
                  </div>
                  {#if options.includeAssets}
                    <div class="flex justify-between">
                      <span class="text-gray-600">Assets:</span>
                      <span class="font-medium">{previewResult.metadata.assetCount}</span>
                    </div>
                  {/if}
                  {#if options.includeScenes}
                    <div class="flex justify-between">
                      <span class="text-gray-600">Scenes:</span>
                      <span class="font-medium">{previewResult.metadata.sceneCount}</span>
                    </div>
                  {/if}
                  {#if options.includeShots}
                    <div class="flex justify-between">
                      <span class="text-gray-600">Shots:</span>
                      <span class="font-medium">{previewResult.metadata.shotCount}</span>
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          {/if}

          <!-- Actions -->
          <div class="space-y-2">
            <button
              on:click={handleResetOptions}
              class="w-full px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Reset Options
            </button>
            <button
              on:click={generatePreview}
              disabled={isLoading}
              class="w-full px-4 py-2 text-sm text-blue-700 bg-blue-50 border border-blue-300 rounded-md hover:bg-blue-100 disabled:opacity-50 transition-colors"
            >
              {isLoading ? 'Generating...' : 'Regenerate Preview'}
            </button>
          </div>
        </div>

        <!-- Preview Panel -->
        <div class="flex-1 p-6 overflow-y-auto">
          <h3 class="font-semibold text-gray-900 mb-4">Canvas Preview</h3>
          
          {#if isLoading}
            <div class="flex items-center justify-center h-64">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          {:else if previewResult}
            <div class="bg-gray-50 rounded-lg p-4 h-full">
              <!-- Simple preview visualization -->
              <div class="relative h-96 bg-white border-2 border-dashed border-gray-300 rounded">
                <div class="absolute inset-0 flex items-center justify-center">
                  <div class="text-center">
                    <div class="text-4xl mb-2">🎬</div>
                    <div class="text-lg font-medium text-gray-900">
                      {previewResult.metadata.structureType} Structure
                    </div>
                    <div class="text-sm text-gray-600 mt-2">
                      {previewResult.metadata.nodeCount} story nodes
                    </div>
                    {#if previewResult.metadata.assetCount > 0}
                      <div class="text-sm text-gray-600">
                        {previewResult.metadata.assetCount} assets
                      </div>
                    {/if}
                    {#if previewResult.metadata.sceneCount > 0}
                      <div class="text-sm text-gray-600">
                        {previewResult.metadata.sceneCount} scenes
                      </div>
                    {/if}
                    {#if previewResult.metadata.shotCount > 0}
                      <div class="text-sm text-gray-600">
                        {previewResult.metadata.shotCount} shots
                      </div>
                    {/if}
                  </div>
                </div>
              </div>

              <!-- Warnings -->
              {#if previewResult.warnings.length > 0}
                <div class="mt-4 p-3 bg-yellow-50 border border-yellow-300 rounded-md">
                  <div class="text-sm font-medium text-yellow-800 mb-1">Warnings</div>
                  <ul class="text-sm text-yellow-700 space-y-1">
                    {#each previewResult.warnings as warning}
                      <li>• {warning}</li>
                    {/each}
                  </ul>
                </div>
              {/if}
            </div>
          {:else}
            <div class="flex items-center justify-center h-64 text-gray-500">
              No preview available
            </div>
          {/if}
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between p-6 border-t">
        <button
          on:click={handleClose}
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          on:click={handlePopulate}
          disabled={isLoading || !previewResult}
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {isLoading ? 'Populating...' : 'Populate Canvas'}
        </button>
      </div>
    </div>
  </div>
{/if}