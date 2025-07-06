<script lang="ts">
  import { onMount } from 'svelte';
  import ThreePanelLayout from '$lib/components/layout/ThreePanelLayout.svelte';
  import ProjectBrowser from '$lib/components/project/ProjectBrowser.svelte';
  import AssetBrowser from '$lib/components/asset/AssetBrowser.svelte';
  import WebSocketStatus from '$lib/components/common/WebSocketStatus.svelte';
  import { initializeApp } from '$lib/stores';

  let connected = false;
  let backendStatus = 'checking...';

  // Use environment variables for API URL
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  onMount(async () => {
    // Initialize app
    initializeApp();

    // Check backend connection
    try {
      const response = await fetch(`${apiUrl}/api/v1/health`);
      if (response.ok) {
        connected = true;
        backendStatus = 'Connected';
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

  <!-- Center Panel: Canvas -->
  <div slot="center" class="panel-section canvas-panel">
    <div class="canvas-header">
      <h2>Production Canvas</h2>
      <div class="canvas-controls">
        <button class="btn btn-icon" title="Zoom In">+</button>
        <button class="btn btn-icon" title="Zoom Out">-</button>
        <button class="btn btn-icon" title="Fit to Screen">⊡</button>
      </div>
    </div>
    <div class="canvas-container">
      <p class="placeholder">Node-based canvas will be implemented in future stories</p>
    </div>
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
  <div slot="right" class="panel-section">
    <h2>Properties</h2>
    <div class="properties-content">
      <p class="placeholder">Node properties and details will appear here</p>
    </div>
  </div>
</ThreePanelLayout>

<style>
  .panel-divider {
    height: 1px;
    background: var(--border-color);
    margin: 1.5rem 0;
  }

  .status-left {
    flex: 1;
  }

  .status-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
</style>
