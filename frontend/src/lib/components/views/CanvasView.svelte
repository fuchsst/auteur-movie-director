<script lang="ts">
  export let projectId: string;

  // Future: This will contain the node-based canvas
</script>

<div class="canvas-view">
  <div class="canvas-toolbar">
    <button type="button">Add Node</button>
    <button type="button">Zoom In</button>
    <button type="button">Zoom Out</button>
    <button type="button">Fit to Screen</button>
  </div>

  <div class="canvas-area">
    <div class="placeholder">
      <h2>Production Canvas</h2>
      <p>Node-based workflow will be implemented here</p>
      <p>Project: {projectId}</p>
    </div>
  </div>
</div>

<style>
  .canvas-view {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .canvas-toolbar {
    padding: 8px 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    gap: 8px;
  }

  .canvas-area {
    flex: 1;
    position: relative;
    background: var(--bg-canvas, #1a1a1a);
    background-image:
      linear-gradient(var(--grid-color, #333) 1px, transparent 1px),
      linear-gradient(90deg, var(--grid-color, #333) 1px, transparent 1px);
    background-size: 20px 20px;
  }

  .placeholder {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    color: var(--text-secondary);
  }
</style>
