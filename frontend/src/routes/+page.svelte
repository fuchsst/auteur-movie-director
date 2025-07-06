<script lang="ts">
  import { onMount } from 'svelte';
  import ThreePanelLayout from '$lib/components/layout/ThreePanelLayout.svelte';
  import ProjectBrowser from '$lib/components/project/ProjectBrowser.svelte';
  import AssetBrowser from '$lib/components/asset/AssetBrowser.svelte';
  import PropertiesInspector from '$lib/components/properties/PropertiesInspector.svelte';
  import ProgressArea from '$lib/components/progress/ProgressArea.svelte';
  import MainViewContainer from '$lib/components/layout/MainViewContainer.svelte';
  import WebSocketStatus from '$lib/components/common/WebSocketStatus.svelte';
  import LFSSetup from '$lib/components/help/LFSSetup.svelte';
  import { initializeApp } from '$lib/stores';
  import { currentProject } from '$lib/stores';
  import { selectionStore } from '$lib/stores/selection';
  import { lfsStore } from '$lib/stores/lfs';
  import type { SelectionContext } from '$lib/types/properties';

  let connected = false;
  let backendStatus = 'checking...';
  let currentSelection: SelectionContext | null = null;

  // Use environment variables for API URL
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Subscribe to selection changes
  $: currentSelection = $selectionStore;

  onMount(async () => {
    // Initialize app
    initializeApp();

    // Check backend connection
    try {
      const response = await fetch(`${apiUrl}/api/v1/health`);
      if (response.ok) {
        connected = true;
        backendStatus = 'Connected';

        // Check Git LFS after backend is connected
        await lfsStore.checkLFS();
      } else {
        backendStatus = 'Backend not responding';
      }
    } catch {
      backendStatus = 'Backend not running';
    }
  });
</script>

<ThreePanelLayout>
  <!-- Left Panel: Project Browser -->
  <div slot="left" class="panel-section">
    <ProjectBrowser />
    <div class="panel-divider"></div>
    <AssetBrowser />
  </div>

  <!-- Center Panel: Main View with Tabs -->
  <div slot="center" class="panel-section canvas-panel">
    {#if $currentProject}
      <MainViewContainer projectId={$currentProject.id} />
    {:else}
      <div class="no-project">
        <h2>No Project Selected</h2>
        <p>Create or select a project to get started</p>
      </div>
    {/if}
    <div class="status-bar">
      <div class="status-left">
        <span>Backend: <span class:connected>{backendStatus}</span></span>
      </div>
      <div class="status-right">
        <WebSocketStatus />
      </div>
    </div>
  </div>

  <!-- Right Panel: Properties/Details -->
  <div slot="right" class="panel-section right-panel">
    <PropertiesInspector selection={currentSelection} />
    <ProgressArea />
  </div>
</ThreePanelLayout>

<!-- Git LFS Setup Dialog -->
{#if $lfsStore.showSetupDialog}
  <div class="modal-backdrop">
    <div class="modal-content">
      <LFSSetup onClose={() => lfsStore.hideSetupDialog()} />
    </div>
  </div>
{/if}

<style>
  .panel-divider {
    height: 1px;
    background: var(--border-color);
    margin: 1.5rem 0;
  }

  .canvas-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .canvas-panel :global(.main-view-container) {
    flex: 1;
  }

  .no-project {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
  }

  .no-project h2 {
    margin: 0 0 8px 0;
  }

  .right-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .right-panel :global(.properties-inspector) {
    flex: 1;
  }

  .right-panel :global(.progress-area) {
    flex-shrink: 0;
  }

  .status-bar {
    display: flex;
    align-items: center;
    padding: 8px 16px;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    font-size: 12px;
  }

  .status-left {
    flex: 1;
  }

  .status-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .connected {
    color: var(--success-color);
  }

  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s;
  }

  .modal-content {
    animation: slideIn 0.3s;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
