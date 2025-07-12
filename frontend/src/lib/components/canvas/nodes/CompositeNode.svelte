<script lang="ts">
  import { Handle, Position } from '@xyflow/svelte';
  import type { CompositeNodeProps, CompositeLayer, BlendMode } from '$lib/types/nodes';
  import { NodeStatus } from '$lib/types/nodes';
  import { createEventDispatcher } from 'svelte';
  import { flip } from 'svelte/animate';

  type $$Props = CompositeNodeProps;
  export let data: $$Props['data'];
  export let selected: boolean = false;

  const dispatch = createEventDispatcher();

  let draggedLayerIndex: number | null = null;

  function handleBlendModeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    dispatch('parameterChange', {
      parameter: 'blendMode',
      value: target.value
    });
  }

  function handleOutputFormatChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    dispatch('parameterChange', {
      parameter: 'outputFormat',
      value: target.value
    });
  }

  function handleLayerVisibilityToggle(layerId: string) {
    const layers = [...data.layers];
    const layer = layers.find(l => l.id === layerId);
    if (layer) {
      layer.visible = !layer.visible;
      dispatch('parameterChange', {
        parameter: 'layers',
        value: layers
      });
    }
  }

  function handleLayerOpacityChange(layerId: string, e: Event) {
    const target = e.target as HTMLInputElement;
    const layers = [...data.layers];
    const layer = layers.find(l => l.id === layerId);
    if (layer) {
      layer.opacity = parseFloat(target.value);
      dispatch('parameterChange', {
        parameter: 'layers',
        value: layers
      });
    }
  }

  function handleLayerBlendModeChange(layerId: string, e: Event) {
    const target = e.target as HTMLSelectElement;
    const layers = [...data.layers];
    const layer = layers.find(l => l.id === layerId);
    if (layer) {
      layer.blendMode = target.value as BlendMode;
      dispatch('parameterChange', {
        parameter: 'layers',
        value: layers
      });
    }
  }

  function handleDragStart(e: DragEvent, index: number) {
    draggedLayerIndex = index;
    e.dataTransfer!.effectAllowed = 'move';
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    e.dataTransfer!.dropEffect = 'move';
  }

  function handleDrop(e: DragEvent, targetIndex: number) {
    e.preventDefault();
    if (draggedLayerIndex === null || draggedLayerIndex === targetIndex) return;

    const layers = [...data.layers];
    const [draggedLayer] = layers.splice(draggedLayerIndex, 1);
    layers.splice(targetIndex, 0, draggedLayer);

    dispatch('parameterChange', {
      parameter: 'layers',
      value: layers
    });

    draggedLayerIndex = null;
  }

  function addLayer() {
    const newLayer: CompositeLayer = {
      id: `layer-${Date.now()}`,
      name: `Layer ${data.layers.length + 1}`,
      visible: true,
      opacity: 1,
      blendMode: BlendMode.NORMAL,
      transform: { x: 0, y: 0, scale: 1, rotation: 0 }
    };

    dispatch('parameterChange', {
      parameter: 'layers',
      value: [...data.layers, newLayer]
    });
  }

  function removeLayer(layerId: string) {
    dispatch('parameterChange', {
      parameter: 'layers',
      value: data.layers.filter(l => l.id !== layerId)
    });
  }

  $: statusClass = {
    [NodeStatus.IDLE]: 'status-idle',
    [NodeStatus.READY]: 'status-ready',
    [NodeStatus.EXECUTING]: 'status-executing',
    [NodeStatus.COMPLETE]: 'status-complete',
    [NodeStatus.ERROR]: 'status-error'
  }[data.status];
</script>

<div class="composite-node node {statusClass}" class:selected>
  <div class="node-header">
    <span class="node-icon">🎬</span>
    <span class="node-title">{data.label}</span>
  </div>

  <div class="node-content">
    <div class="output-format">
      <label>
        Output:
        <select value={data.outputFormat} on:change={handleOutputFormatChange}>
          <option value="image">Image</option>
          <option value="video">Video</option>
        </select>
      </label>
    </div>

    <div class="blend-mode">
      <label>
        Base Blend:
        <select value={data.blendMode} on:change={handleBlendModeChange}>
          <option value="normal">Normal</option>
          <option value="multiply">Multiply</option>
          <option value="screen">Screen</option>
          <option value="overlay">Overlay</option>
          <option value="soft-light">Soft Light</option>
          <option value="hard-light">Hard Light</option>
        </select>
      </label>
    </div>

    <div class="layers-section">
      <div class="layers-header">
        <span>Layers ({data.layers.length})</span>
        <button type="button" class="add-layer-btn" on:click={addLayer}>+</button>
      </div>

      <div class="layers-list">
        {#each data.layers as layer, index (layer.id)}
          <div
            class="layer"
            animate:flip={{ duration: 200 }}
            draggable="true"
            on:dragstart={(e) => handleDragStart(e, index)}
            on:dragover={handleDragOver}
            on:drop={(e) => handleDrop(e, index)}
          >
            <div class="layer-header">
              <button
                type="button"
                class="visibility-toggle"
                class:visible={layer.visible}
                on:click={() => handleLayerVisibilityToggle(layer.id)}
              >
                {layer.visible ? '👁️' : '👁️‍🗨️'}
              </button>
              <span class="layer-name">{layer.name}</span>
              <button
                type="button"
                class="remove-layer-btn"
                on:click={() => removeLayer(layer.id)}
              >
                ×
              </button>
            </div>

            <div class="layer-controls">
              <div class="opacity-control">
                <label>
                  Opacity:
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={layer.opacity}
                    on:input={(e) => handleLayerOpacityChange(layer.id, e)}
                  />
                  <span>{Math.round(layer.opacity * 100)}%</span>
                </label>
              </div>

              <div class="blend-control">
                <label>
                  Blend:
                  <select
                    value={layer.blendMode}
                    on:change={(e) => handleLayerBlendModeChange(layer.id, e)}
                  >
                    <option value="normal">Normal</option>
                    <option value="multiply">Multiply</option>
                    <option value="screen">Screen</option>
                    <option value="overlay">Overlay</option>
                    <option value="darken">Darken</option>
                    <option value="lighten">Lighten</option>
                  </select>
                </label>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>

    {#if data.preview}
      <div class="preview">
        <img src={data.preview} alt="Composite preview" />
      </div>
    {/if}

    {#if data.progress !== undefined && data.status === NodeStatus.EXECUTING}
      <div class="progress">
        <div class="progress-bar" style="width: {data.progress}%"></div>
      </div>
    {/if}

    {#if data.error}
      <div class="error-message">{data.error}</div>
    {/if}
  </div>

  <!-- Multiple input handles for layers -->
  <Handle type="target" position={Position.Left} id="layer-1" style="top: 30%" />
  <Handle type="target" position={Position.Left} id="layer-2" style="top: 50%" />
  <Handle type="target" position={Position.Left} id="layer-3" style="top: 70%" />
  
  <Handle type="source" position={Position.Right} id="composite-out" />
</div>

<style>
  .composite-node {
    background: var(--node-bg, #1e293b);
    border: 2px solid var(--node-border, #334155);
    border-radius: 8px;
    min-width: 320px;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    transition: all 0.2s;
  }

  .composite-node.selected {
    border-color: var(--node-selected, #3b82f6);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
  }

  .node-header {
    padding: 8px 12px;
    border-bottom: 1px solid var(--node-border, #334155);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .node-icon {
    font-size: 18px;
  }

  .node-title {
    font-weight: 600;
    color: var(--text-primary, #f1f5f9);
  }

  .node-content {
    padding: 12px;
  }

  .output-format label,
  .blend-mode label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    color: var(--text-secondary, #94a3b8);
    font-size: 12px;
    margin-bottom: 12px;
  }

  select,
  input[type="range"] {
    width: 100%;
    background: var(--input-bg, #0f172a);
    border: 1px solid var(--input-border, #334155);
    border-radius: 4px;
    padding: 4px 8px;
    color: var(--text-primary, #f1f5f9);
  }

  .layers-section {
    margin-top: 12px;
    border: 1px solid var(--node-border, #334155);
    border-radius: 4px;
  }

  .layers-header {
    padding: 8px;
    background: var(--layer-header-bg, #0f172a);
    border-bottom: 1px solid var(--node-border, #334155);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .add-layer-btn {
    width: 24px;
    height: 24px;
    border: 1px solid var(--node-border, #334155);
    background: var(--button-bg, #1e293b);
    color: var(--text-primary, #f1f5f9);
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
  }

  .add-layer-btn:hover {
    background: var(--button-hover, #334155);
  }

  .layers-list {
    max-height: 200px;
    overflow-y: auto;
  }

  .layer {
    padding: 8px;
    border-bottom: 1px solid var(--node-border, #334155);
    cursor: move;
    transition: background-color 0.2s;
  }

  .layer:hover {
    background: rgba(59, 130, 246, 0.1);
  }

  .layer:last-child {
    border-bottom: none;
  }

  .layer-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .visibility-toggle {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 16px;
    opacity: 0.5;
  }

  .visibility-toggle.visible {
    opacity: 1;
  }

  .layer-name {
    flex: 1;
    font-size: 12px;
    color: var(--text-primary, #f1f5f9);
  }

  .remove-layer-btn {
    width: 20px;
    height: 20px;
    border: none;
    background: none;
    color: var(--text-secondary, #94a3b8);
    cursor: pointer;
    font-size: 18px;
    line-height: 1;
  }

  .remove-layer-btn:hover {
    color: #ef4444;
  }

  .layer-controls {
    display: flex;
    gap: 12px;
  }

  .opacity-control,
  .blend-control {
    flex: 1;
  }

  .opacity-control label,
  .blend-control label {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    color: var(--text-secondary, #94a3b8);
  }

  .opacity-control input {
    flex: 1;
  }

  .opacity-control span {
    min-width: 35px;
    text-align: right;
  }

  .preview {
    margin-top: 12px;
    border: 1px solid var(--node-border, #334155);
    border-radius: 4px;
    overflow: hidden;
  }

  .preview img {
    display: block;
    width: 100%;
    height: auto;
  }

  .progress {
    margin-top: 8px;
    height: 4px;
    background: var(--progress-bg, #334155);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: var(--progress-fill, #3b82f6);
    transition: width 0.3s ease;
  }

  .error-message {
    margin-top: 8px;
    padding: 4px 8px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 4px;
    color: #ef4444;
    font-size: 12px;
  }

  /* Status colors */
  .status-idle {
    border-color: #64748b;
  }

  .status-ready {
    border-color: #10b981;
  }

  .status-executing {
    border-color: #3b82f6;
  }

  .status-complete {
    border-color: #10b981;
  }

  .status-error {
    border-color: #ef4444;
  }

  /* Handle styles */
  :global(.svelte-flow__handle) {
    width: 12px;
    height: 12px;
    background: #f59e0b;
    border: 2px solid #1e293b;
  }

  :global(.svelte-flow__handle-left) {
    left: -6px;
  }

  :global(.svelte-flow__handle-right) {
    right: -6px;
  }
</style>