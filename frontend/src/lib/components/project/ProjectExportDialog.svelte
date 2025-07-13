<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { exportApi } from '$lib/api/export';
  import type { ExportOptions, ExportProgress } from '$lib/api/export';
  import { websocketStore } from '$lib/stores/websocket';
  import { notificationStore } from '$lib/stores/notifications';
  import Dialog from '../common/Dialog.svelte';
  import { Download, Archive, History, Database, HardDrive } from 'lucide-svelte';

  export let open = false;
  export let projectId: string;
  export let projectName: string;

  const dispatch = createEventDispatcher();

  let exporting = false;
  let exportProgress = 0;
  let exportMessage = '';
  let downloadUrl: string | null = null;

  // Export options
  let options: ExportOptions = {
    format: 'zip',
    includeHistory: true,
    includeCache: false,
    compressMedia: false,
    splitSizeMb: undefined
  };

  // Listen for export progress via WebSocket
  $: if ($websocketStore.lastMessage?.type === 'export_progress') {
    const msg = $websocketStore.lastMessage as ExportProgress;
    if (msg.projectId === projectId) {
      exportProgress = (msg.progress || 0) * 100;
      exportMessage = msg.message || '';
    }
  }

  $: if ($websocketStore.lastMessage?.type === 'export_complete') {
    const msg = $websocketStore.lastMessage as ExportProgress;
    if (msg.projectId === projectId && msg.filename) {
      exporting = false;
      exportProgress = 100;
      exportMessage = 'Export completed successfully!';
      downloadUrl = exportApi.getDownloadUrl(projectId, msg.filename);

      notificationStore.add({
        type: 'success',
        title: 'Export Complete',
        message: `${projectName} has been exported successfully`,
        action: {
          label: 'Download',
          callback: () => window.open(downloadUrl!, '_blank')
        }
      });
    }
  }

  $: if ($websocketStore.lastMessage?.type === 'export_error') {
    const msg = $websocketStore.lastMessage as ExportProgress;
    if (msg.projectId === projectId) {
      exporting = false;
      exportProgress = 0;
      exportMessage = '';

      notificationStore.add({
        type: 'error',
        title: 'Export Failed',
        message: msg.error || 'An error occurred during export'
      });
    }
  }

  async function handleExport() {
    if (exporting) return;

    exporting = true;
    exportProgress = 0;
    exportMessage = 'Initializing export...';
    downloadUrl = null;

    try {
      const clientId = $websocketStore.clientId;
      await exportApi.exportProject(projectId, options, clientId);
    } catch (error) {
      exporting = false;
      notificationStore.add({
        type: 'error',
        title: 'Export Failed',
        message: error.message || 'Failed to start export'
      });
    }
  }

  function handleClose() {
    if (!exporting) {
      open = false;
      dispatch('close');
    }
  }

  function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }
</script>

<Dialog bind:open title="Export Project" on:close={handleClose}>
  <div class="export-dialog">
    <div class="project-info">
      <Archive size={20} />
      <div>
        <h3>{projectName}</h3>
        <p>Export this project as a portable archive</p>
      </div>
    </div>

    {#if !exporting && !downloadUrl}
      <div class="export-options">
        <div class="option-group">
          <h4>Archive Format</h4>
          <div class="format-options">
            <label class="radio-option">
              <input type="radio" bind:group={options.format} value="zip" />
              <span>ZIP</span>
              <small>Compatible with all platforms</small>
            </label>
            <label class="radio-option">
              <input type="radio" bind:group={options.format} value="tar.gz" />
              <span>TAR.GZ</span>
              <small>Better compression, Unix-friendly</small>
            </label>
          </div>
        </div>

        <div class="option-group">
          <h4>Export Options</h4>
          <label class="checkbox-option">
            <input type="checkbox" bind:checked={options.includeHistory} />
            <History size={16} />
            <div>
              <span>Include Git History</span>
              <small>Preserve all version control history</small>
            </div>
          </label>

          <label class="checkbox-option">
            <input type="checkbox" bind:checked={options.includeCache} />
            <Database size={16} />
            <div>
              <span>Include Cache Files</span>
              <small>Export temporary and cache data</small>
            </div>
          </label>

          <label class="checkbox-option">
            <input type="checkbox" bind:checked={options.compressMedia} />
            <HardDrive size={16} />
            <div>
              <span>Compress Media Files</span>
              <small>Reduce archive size (may affect quality)</small>
            </div>
          </label>
        </div>

        <div class="option-group">
          <h4>Archive Splitting</h4>
          <label class="input-option">
            <span>Split archives larger than:</span>
            <div class="split-input">
              <input
                type="number"
                bind:value={options.splitSizeMb}
                placeholder="No splitting"
                min="100"
                max="10000"
                step="100"
              />
              <span>MB</span>
            </div>
            <small>Leave empty to create single archive</small>
          </label>
        </div>
      </div>
    {/if}

    {#if exporting}
      <div class="export-progress">
        <div class="progress-header">
          <span>{exportMessage}</span>
          <span>{Math.round(exportProgress)}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: {exportProgress}%" />
        </div>
      </div>
    {/if}

    {#if downloadUrl}
      <div class="export-complete">
        <div class="success-icon">
          <Download size={48} />
        </div>
        <h3>Export Complete!</h3>
        <p>Your project has been exported successfully.</p>
        <a href={downloadUrl} download class="download-button" target="_blank">
          <Download size={16} />
          Download Archive
        </a>
      </div>
    {/if}
  </div>

  <div slot="actions">
    {#if !exporting && !downloadUrl}
      <button on:click={handleClose}>Cancel</button>
      <button class="primary" on:click={handleExport}>
        <Archive size={16} />
        Start Export
      </button>
    {:else if downloadUrl}
      <button class="primary" on:click={handleClose}>Close</button>
    {/if}
  </div>
</Dialog>

<style>
  .export-dialog {
    padding: 1rem;
  }

  .project-info {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    background: var(--surface-secondary);
    border-radius: 8px;
    margin-bottom: 1.5rem;
  }

  .project-info h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .project-info p {
    margin: 0.25rem 0 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .export-options {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .option-group h4 {
    margin: 0 0 0.75rem;
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .format-options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  .radio-option {
    display: flex;
    flex-direction: column;
    padding: 0.75rem;
    background: var(--surface-secondary);
    border: 2px solid var(--border-color);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .radio-option:hover {
    border-color: var(--primary-color);
  }

  .radio-option:has(input:checked) {
    border-color: var(--primary-color);
    background: var(--primary-color-alpha);
  }

  .radio-option input {
    position: absolute;
    opacity: 0;
  }

  .radio-option span {
    font-weight: 500;
    margin-bottom: 0.25rem;
  }

  .radio-option small {
    color: var(--text-secondary);
    font-size: 0.8125rem;
  }

  .checkbox-option {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
    background: var(--surface-secondary);
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .checkbox-option:hover {
    background: var(--surface-hover);
  }

  .checkbox-option input {
    margin-top: 0.125rem;
  }

  .checkbox-option div {
    flex: 1;
  }

  .checkbox-option span {
    display: block;
    font-weight: 500;
    margin-bottom: 0.25rem;
  }

  .checkbox-option small {
    display: block;
    color: var(--text-secondary);
    font-size: 0.8125rem;
  }

  .input-option {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .split-input {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .split-input input {
    flex: 1;
    padding: 0.5rem;
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.9375rem;
  }

  .split-input span {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .export-progress {
    padding: 1.5rem;
    background: var(--surface-secondary);
    border-radius: 8px;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    font-size: 0.9375rem;
  }

  .progress-bar {
    height: 8px;
    background: var(--border-color);
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s ease;
  }

  .export-complete {
    text-align: center;
    padding: 2rem;
  }

  .success-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 80px;
    height: 80px;
    background: var(--success-color-alpha);
    color: var(--success-color);
    border-radius: 50%;
    margin-bottom: 1rem;
  }

  .export-complete h3 {
    margin: 0 0 0.5rem;
    font-size: 1.25rem;
  }

  .export-complete p {
    margin: 0 0 1.5rem;
    color: var(--text-secondary);
  }

  .download-button {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: var(--primary-color);
    color: white;
    text-decoration: none;
    border-radius: 6px;
    font-weight: 500;
    transition: background 0.2s;
  }

  .download-button:hover {
    background: var(--primary-hover);
  }

  button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
</style>
