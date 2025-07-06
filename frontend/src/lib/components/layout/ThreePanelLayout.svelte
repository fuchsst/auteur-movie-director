<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  // Panel sizes (percentages)
  let leftPanelWidth = 20;
  let rightPanelWidth = 25;

  // Resize state
  let isResizingLeft = false;
  let isResizingRight = false;

  // Load saved sizes from localStorage
  onMount(() => {
    if (browser) {
      const savedLeftWidth = localStorage.getItem('panel-left-width');
      const savedRightWidth = localStorage.getItem('panel-right-width');

      if (savedLeftWidth) leftPanelWidth = parseFloat(savedLeftWidth);
      if (savedRightWidth) rightPanelWidth = parseFloat(savedRightWidth);
    }
  });

  // Handle mouse events for resizing
  function handleMouseMove(e: MouseEvent) {
    if (isResizingLeft) {
      const containerWidth = document.body.clientWidth;
      const newWidth = (e.clientX / containerWidth) * 100;
      leftPanelWidth = Math.max(15, Math.min(40, newWidth));
      savePanelSizes();
    } else if (isResizingRight) {
      const containerWidth = document.body.clientWidth;
      const newWidth = ((containerWidth - e.clientX) / containerWidth) * 100;
      rightPanelWidth = Math.max(15, Math.min(40, newWidth));
      savePanelSizes();
    }
  }

  function handleMouseUp() {
    isResizingLeft = false;
    isResizingRight = false;
  }

  function savePanelSizes() {
    if (browser) {
      localStorage.setItem('panel-left-width', leftPanelWidth.toString());
      localStorage.setItem('panel-right-width', rightPanelWidth.toString());
    }
  }

  // Calculate center panel width
  $: centerPanelWidth = 100 - leftPanelWidth - rightPanelWidth;
</script>

<svelte:window on:mousemove={handleMouseMove} on:mouseup={handleMouseUp} />

<div class="three-panel-layout">
  <!-- Left Panel -->
  <div class="panel panel-left" style="width: {leftPanelWidth}%">
    <div class="panel-content">
      <slot name="left" />
    </div>
    <div
      class="resize-handle resize-handle-left"
      on:mousedown={() => (isResizingLeft = true)}
      role="separator"
      aria-label="Resize left panel"
      tabindex="0"
    />
  </div>

  <!-- Center Panel -->
  <div class="panel panel-center" style="width: {centerPanelWidth}%">
    <div class="panel-content">
      <slot name="center" />
    </div>
  </div>

  <!-- Right Panel -->
  <div class="panel panel-right" style="width: {rightPanelWidth}%">
    <div
      class="resize-handle resize-handle-right"
      on:mousedown={() => (isResizingRight = true)}
      role="separator"
      aria-label="Resize right panel"
      tabindex="0"
    />
    <div class="panel-content">
      <slot name="right" />
    </div>
  </div>
</div>

<style>
  .three-panel-layout {
    display: flex;
    height: 100vh;
    width: 100%;
    overflow: hidden;
    background-color: var(--color-background, #1a1a1a);
  }

  .panel {
    position: relative;
    display: flex;
    flex-direction: column;
    background-color: var(--color-panel, #242424);
    border: 1px solid var(--color-border, #333);
  }

  .panel-content {
    flex: 1;
    overflow: auto;
    padding: 1rem;
  }

  .resize-handle {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 4px;
    background-color: var(--color-border, #333);
    cursor: col-resize;
    transition: background-color 0.2s;
    z-index: 10;
  }

  .resize-handle:hover {
    background-color: var(--color-primary, #4a9eff);
  }

  .resize-handle-left {
    right: -2px;
  }

  .resize-handle-right {
    left: -2px;
  }

  /* Panel specific styles */
  .panel-left {
    border-right: none;
  }

  .panel-center {
    border-left: none;
    border-right: none;
  }

  .panel-right {
    border-left: none;
  }

  /* Responsive behavior */
  @media (max-width: 768px) {
    .three-panel-layout {
      flex-direction: column;
    }

    .panel {
      width: 100% !important;
      height: 33.333%;
      border: 1px solid var(--color-border, #333);
    }

    .resize-handle {
      display: none;
    }
  }
</style>
