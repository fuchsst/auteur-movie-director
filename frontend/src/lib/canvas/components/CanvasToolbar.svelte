<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { canvasStore } from '$lib/canvas/core/canvas-store';

  export let readonly: boolean = false;

  const dispatch = createEventDispatcher();

  function handlePopulate() {
    dispatch('populateCanvas');
  }

  function handleClear() {
    if (confirm('Are you sure you want to clear the canvas? This action cannot be undone.')) {
      canvasStore.clearCanvas();
    }
  }

  function handleSave() {
    canvasStore.saveProject();
  }

  function handleUndo() {
    canvasStore.undo();
  }

  function handleRedo() {
    canvasStore.redo();
  }

  function handleZoomIn() {
    // This would need to be implemented via Svelte Flow controls
    console.log('Zoom in');
  }

  function handleZoomOut() {
    console.log('Zoom out');
  }

  function handleFitView() {
    console.log('Fit view');
  }
</script>

<div class="canvas-toolbar bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
  <div class="flex items-center space-x-4">
    <!-- Title -->
    <div class="text-sm font-medium text-gray-900">
      Production Canvas
    </div>

    <!-- Actions -->
    <div class="flex items-center space-x-2">
      <button
        on:click={handlePopulate}
        disabled={readonly}
        class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Populate canvas from project"
      >
        🎬 Populate
      </button>

      <button
        on:click={handleSave}
        disabled={readonly}
        class="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Save canvas"
      >
        💾 Save
      </button>

      <button
        on:click={handleClear}
        disabled={readonly}
        class="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Clear canvas"
      >
        🗑️ Clear
      </button>

      <button
        on:click={() => dispatch('openTemplateLibrary')}
        class="px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title="Open template library"
      >
        📚 Templates
      </button>
    </div>
  </div>

  <div class="flex items-center space-x-2">
    <!-- Undo/Redo -->
    <button
      on:click={handleUndo}
      disabled={!$canvasStore.canUndo || readonly}
      class="px-2 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      title="Undo (Ctrl+Z)"
    >
      ↩️ Undo
    </button>

    <button
      on:click={handleRedo}
      disabled={!$canvasStore.canRedo || readonly}
      class="px-2 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      title="Redo (Ctrl+Y)"
    >
      ↪️ Redo
    </button>

    <!-- View Controls -->
    <button
      on:click={handleZoomIn}
      class="px-2 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
      title="Zoom In"
    >
      🔍+
    </button>

    <button
      on:click={handleZoomOut}
      class="px-2 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
      title="Zoom Out"
    >
      🔍-
    </button>

    <button
      on:click={handleFitView}
      class="px-2 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
      title="Fit to View"
    >
      📐 Fit
    </button>
  </div>

  <!-- Stats -->
  <div class="flex items-center space-x-4 text-sm text-gray-600">
    <span>Nodes: {$canvasStore.nodeCount}</span>
    <span>Selected: {$canvasStore.selectedNodeCount}</span>
  </div>
</div>

<style>
  .canvas-toolbar {
    position: relative;
    z-index: 10;
  }
</style>