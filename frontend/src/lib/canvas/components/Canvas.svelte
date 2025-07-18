<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { SvelteFlow, Controls, Background, MiniMap, NodeTypes, EdgeTypes } from '@xyflow/svelte';
  import { canvasStore } from '$lib/canvas/core/canvas-store';
  import { storyNodeTypes } from '$lib/canvas/nodes/story-nodes';
  import { assetNodeTypes } from '$lib/canvas/nodes/asset-nodes';
  import { defaultEdgeTypes } from '$lib/canvas/edges/default-edges';
  import { CanvasToolbar } from '$lib/canvas/components/CanvasToolbar.svelte';
  import { CanvasContextMenu } from '$lib/canvas/components/CanvasContextMenu.svelte';
  import { CanvasMiniMap } from '$lib/canvas/components/CanvasMiniMap.svelte';
  import { CanvasControls } from '$lib/canvas/components/CanvasControls.svelte';
  import { CanvasDropzone } from '$lib/canvas/components/CanvasDropzone.svelte';
  import { CanvasPopulationDialog } from '$lib/canvas/components/CanvasPopulationDialog.svelte';
  import { CollaborationPanel } from '$lib/canvas/components/CollaborationPanel.svelte';
  import { ProgressiveDisclosurePanel } from '$lib/canvas/components/ProgressiveDisclosurePanel.svelte';
  import { TemplateLibrary } from '$lib/canvas/components/TemplateLibrary.svelte';

  // Props
  export let projectId: string | null = null;
  export let readonly: boolean = false;
  export let showGrid: boolean = true;
  export let showMinimap: boolean = true;
  export let showControls: boolean = true;
  export let projectData: any = null;

  // Reactive store values
  $: nodes = $canvasStore.nodes;
  $: edges = $canvasStore.edges;
  $: viewport = $canvasStore.viewport;
  $: isLoading = $canvasStore.isLoading;
  $: error = $canvasStore.error;

  // Node and edge type definitions
  const nodeTypes = {
    ...storyNodeTypes,
    ...assetNodeTypes
  };

  const edgeTypes = {
    ...defaultEdgeTypes
  };

  // Lifecycle
  onMount(async () => {
    if (projectId) {
      await canvasStore.loadProject(projectId);
    }

    // Set up keyboard shortcuts
    setupKeyboardShortcuts();

    // Set up auto-save
    setupAutoSave();
  });

  onDestroy(() => {
    // Clean up
    clearTimeout(autoSaveTimer);
  });

  // State
  let autoSaveTimer: NodeJS.Timeout;
  let showPopulationDialog = false;
  let showTemplateLibrary = false;

  function setupAutoSave() {
    const AUTO_SAVE_INTERVAL = 30000; // 30 seconds
    
    autoSaveTimer = setInterval(() => {
      if (projectId && !readonly) {
        canvasStore.saveProject();
      }
    }, AUTO_SAVE_INTERVAL);
  }

  // Keyboard shortcuts
  function setupKeyboardShortcuts() {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (readonly) return;

      const ctrlOrCmd = event.ctrlKey || event.metaKey;

      switch (event.key) {
        case 'z':
          if (ctrlOrCmd && !event.shiftKey) {
            event.preventDefault();
            canvasStore.undo();
          } else if (ctrlOrCmd && event.shiftKey) {
            event.preventDefault();
            canvasStore.redo();
          }
          break;

        case 'Delete':
        case 'Backspace':
          event.preventDefault();
          handleDeleteSelection();
          break;

        case 'a':
          if (ctrlOrCmd) {
            event.preventDefault();
            handleSelectAll();
          }
          break;

        case 'Escape':
          event.preventDefault();
          canvasStore.clearSelection();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }

  // Event handlers
  function handlePopulateCanvas(event: CustomEvent) {
    if (projectData) {
      showPopulationDialog = true;
    }
  }

  function handlePopulationComplete(event: CustomEvent) {
    const { result } = event.detail;
    console.log('Canvas populated:', result);
  }

  function handlePopulationClose() {
    showPopulationDialog = false;
  }

  function handleOpenTemplateLibrary() {
    showTemplateLibrary = true;
  }

  function handleTemplateLibraryClose() {
    showTemplateLibrary = false;
  }

  function handleNodesChange(event: CustomEvent) {
    const { detail } = event;
    if (detail.type === 'add') {
      detail.nodes.forEach(node => canvasStore.addNode(node));
    } else if (detail.type === 'remove') {
      detail.nodes.forEach(node => canvasStore.removeNode(node.id));
    } else if (detail.type === 'update') {
      detail.nodes.forEach(node => canvasStore.updateNode(node.id, node));
    }
  }

  function handleEdgesChange(event: CustomEvent) {
    const { detail } = event;
    if (detail.type === 'add') {
      detail.edges.forEach(edge => canvasStore.addEdge(edge));
    } else if (detail.type === 'remove') {
      detail.edges.forEach(edge => canvasStore.removeEdge(edge.id));
    } else if (detail.type === 'update') {
      detail.edges.forEach(edge => canvasStore.updateEdge(edge.id, edge));
    }
  }

  function handleViewportChange(event: CustomEvent) {
    canvasStore.setViewport(event.detail);
  }

  function handleConnect(event: CustomEvent) {
    const { source, target, sourceHandle, targetHandle } = event.detail;
    canvasStore.addEdge({
      source,
      target,
      sourceHandle,
      targetHandle,
      type: 'default'
    });
  }

  function handleNodeClick(event: CustomEvent) {
    const { node, event: mouseEvent } = event.detail;
    canvasStore.selectNode(node.id, mouseEvent.shiftKey);
  }

  function handleEdgeClick(event: CustomEvent) {
    const { edge, event: mouseEvent } = event.detail;
    canvasStore.selectEdge(edge.id, mouseEvent.shiftKey);
  }

  function handlePaneClick(event: CustomEvent) {
    canvasStore.clearSelection();
  }

  function handleDeleteSelection() {
    const state = $canvasStore;
    
    state.selectedNodes.forEach(id => canvasStore.removeNode(id));
    state.selectedEdges.forEach(id => canvasStore.removeEdge(id));
  }

  function handleSelectAll() {
    const state = $canvasStore;
    state.nodes.forEach(node => canvasStore.selectNode(node.id, true));
  }

  function handleDrop(event: CustomEvent) {
    const { data, position } = event.detail;
    
    if (data.type === 'node-template') {
      canvasStore.addNode({
        type: data.nodeType,
        position,
        data: data.data || {}
      });
    } else if (data.type === 'asset') {
      canvasStore.addNode({
        type: 'asset-node',
        position,
        data: {
          assetId: data.assetId,
          assetType: data.assetType,
          assetName: data.assetName
        }
      });
    }
  }
</script>

<div class="canvas-container">
  {#if isLoading}
    <div class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>Loading canvas...</p>
    </div>
  {/if}

  {#if error}
    <div class="error-overlay">
      <div class="error-message">
        <h3>Error Loading Canvas</h3>
        <p>{error}</p>
        <button on:click={() => window.location.reload()}>
          Reload
        </button>
      </div>
    </div>
  {/if}

  <CanvasToolbar {readonly} on:populateCanvas={handlePopulateCanvas} on:openTemplateLibrary={handleOpenTemplateLibrary} />
  
  <CanvasPopulationDialog
    bind:isOpen={showPopulationDialog}
    {projectData}
    on:populated={handlePopulationComplete}
    on:close={handlePopulationClose}
  />
  
  <TemplateLibrary bind:isOpen={showTemplateLibrary} on:close={handleTemplateLibraryClose} />
  
  <div class="canvas-wrapper">
    <SvelteFlow
      {nodes}
      {edges}
      {viewport}
      {nodeTypes}
      {edgeTypes}
      {readonly}
      fitView
      fitViewOptions={{ padding: 0.2 }}
      snapToGrid={showGrid}
      snapGrid={[20, 20]}
      on:nodesChange={handleNodesChange}
      on:edgesChange={handleEdgesChange}
      on:viewportChange={handleViewportChange}
      on:connect={handleConnect}
      on:nodeClick={handleNodeClick}
      on:edgeClick={handleEdgeClick}
      on:paneClick={handlePaneClick}
      on:drop={handleDrop}
    >
      {#if showGrid}
        <Background 
          gap={20} 
          size={1} 
          color="#e5e7eb"
          patternColor="#d1d5db"
        />
      {/if}

      {#if showControls}
        <CanvasControls {readonly} />
      {/if}

      {#if showMinimap}
        <CanvasMiniMap />
      {/if}

      <CanvasDropzone />
    </SvelteFlow>
  </div>

  <CanvasContextMenu {readonly} />
  
  <CollaborationPanel {projectId} />
  
  <ProgressiveDisclosurePanel />
</div>

<style>
  .canvas-container {
    position: relative;
    width: 100%;
    height: 100%;
    background: #f9fafb;
    border-radius: 8px;
    overflow: hidden;
  }

  .canvas-wrapper {
    width: 100%;
    height: 100%;
  }

  .loading-overlay,
  .error-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.9);
    z-index: 1000;
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #e5e7eb;
    border-top: 4px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .error-message {
    text-align: center;
    padding: 2rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .error-message h3 {
    color: #ef4444;
    margin-bottom: 0.5rem;
  }

  .error-message button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .error-message button:hover {
    background: #2563eb;
  }
</style>