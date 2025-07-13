<script lang="ts">
  import { createEventDispatcher, onDestroy } from 'svelte';
  import { Dialog, Button, Icon, Spinner } from '$lib/components/ui';
  import { importApi, type ImportOptions, type ValidationResult } from '$lib/api/import';
  import { websocketStore } from '$lib/stores/websocket';
  import { notificationStore } from '$lib/stores/notifications';
  import type { Unsubscriber } from 'svelte/store';

  export let open = false;

  const dispatch = createEventDispatcher();

  let fileInput: HTMLInputElement;
  let selectedFile: File | null = null;
  let targetName = '';
  let importing = false;
  let uploading = false;
  let validating = false;
  let uploadProgress = 0;
  let importProgress = 0;
  let importMessage = '';
  let validation: ValidationResult | null = null;
  let tempPath = '';

  // Import options
  let options: ImportOptions = {
    overwrite: false,
    renameOnConflict: true,
    restoreGitHistory: true,
    verifyLfsObjects: true
  };

  // WebSocket subscription
  let wsUnsubscribe: Unsubscriber;
  let clientId: string | undefined;

  $: if (open) {
    // Subscribe to WebSocket messages
    wsUnsubscribe = websocketStore.subscribe((state) => {
      clientId = state.clientId;

      if (state.lastMessage) {
        const msg = state.lastMessage;

        if (msg.type === 'import_progress') {
          importProgress = msg.progress * 100;
          importMessage = msg.message;
        } else if (msg.type === 'import_complete') {
          handleImportComplete(msg.result);
        } else if (msg.type === 'import_error') {
          handleImportError(msg.error);
        }
      }
    });
  }

  onDestroy(() => {
    wsUnsubscribe?.();
  });

  function handleFileSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      selectedFile = input.files[0];

      // Auto-fill target name from filename
      const filename = selectedFile.name;
      const match = filename.match(/^(.+?)(?:_export_\d+)?\.(?:zip|tar\.gz)$/);
      if (match) {
        targetName = match[1];
      }

      // Auto-validate
      validateFile();
    }
  }

  async function validateFile() {
    if (!selectedFile) return;

    validating = true;
    validation = null;

    try {
      validation = await importApi.validateArchive(selectedFile);

      if (validation.projectId && !targetName) {
        targetName = validation.projectId;
      }
    } catch (error) {
      notificationStore.add({
        type: 'error',
        title: 'Validation Failed',
        message: error instanceof Error ? error.message : 'Failed to validate archive'
      });
    } finally {
      validating = false;
    }
  }

  async function handleImport() {
    if (!selectedFile || !targetName || !validation?.valid) return;

    uploading = true;
    uploadProgress = 0;

    try {
      // Upload file
      const uploadResult = await importApi.uploadArchive(selectedFile, clientId);
      tempPath = uploadResult.tempPath;
      uploadProgress = 100;

      // Start import
      importing = true;
      uploading = false;
      importProgress = 0;

      await importApi.importProject(tempPath, targetName, options, clientId);

      // Import will complete via WebSocket
    } catch (error) {
      notificationStore.add({
        type: 'error',
        title: 'Import Failed',
        message: error instanceof Error ? error.message : 'Failed to import project'
      });
      reset();
    }
  }

  function handleImportComplete(result: any) {
    importing = false;

    notificationStore.add({
      type: 'success',
      title: 'Import Complete',
      message: `${result.projectName} has been imported successfully`,
      action: {
        label: 'Open Project',
        onClick: () => {
          dispatch('imported', result);
          handleClose();
        }
      }
    });

    // Show statistics
    if (result.statistics) {
      const stats = result.statistics;
      console.log('Import statistics:', {
        files: stats.totalFiles,
        size: `${stats.totalSizeMb}MB`,
        commits: stats.gitCommits
      });
    }

    dispatch('imported', result);
    handleClose();
  }

  function handleImportError(error: string) {
    importing = false;

    notificationStore.add({
      type: 'error',
      title: 'Import Failed',
      message: error
    });

    reset();
  }

  function reset() {
    selectedFile = null;
    targetName = '';
    uploading = false;
    importing = false;
    uploadProgress = 0;
    importProgress = 0;
    importMessage = '';
    validation = null;
    tempPath = '';

    if (fileInput) {
      fileInput.value = '';
    }
  }

  function handleClose() {
    if (!importing && !uploading) {
      reset();
      dispatch('close');
    }
  }
</script>

<Dialog bind:open on:close={handleClose}>
  <svelte:fragment slot="header">
    <Icon name="upload" size={20} />
    Import Project
  </svelte:fragment>

  <div class="import-content">
    {#if !importing && !uploading}
      <div class="file-section">
        <label>
          <span class="label">Select Archive</span>
          <input
            type="file"
            accept=".zip,.tar.gz"
            on:change={handleFileSelect}
            bind:this={fileInput}
            class="file-input"
          />
          <div class="file-display">
            {#if selectedFile}
              <Icon name="file-zip" size={16} />
              <span class="filename">{selectedFile.name}</span>
              <span class="size">({(selectedFile.size / 1024 / 1024).toFixed(1)}MB)</span>
            {:else}
              <span class="placeholder">Choose a project archive...</span>
            {/if}
          </div>
        </label>
      </div>

      {#if validating}
        <div class="validating">
          <Spinner size={16} />
          <span>Validating archive...</span>
        </div>
      {/if}

      {#if validation}
        <div class="validation-result" class:valid={validation.valid}>
          {#if validation.valid}
            <Icon name="check-circle" size={16} />
            <span>Valid project archive</span>
            {#if validation.version}
              <span class="version">(v{validation.version})</span>
            {/if}
          {:else}
            <Icon name="alert-circle" size={16} />
            <span>Invalid archive</span>
          {/if}

          {#if validation.errors.length > 0}
            <div class="errors">
              {#each validation.errors as error}
                <div class="error">{error}</div>
              {/each}
            </div>
          {/if}

          {#if validation.warnings.length > 0}
            <div class="warnings">
              {#each validation.warnings as warning}
                <div class="warning">{warning}</div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      {#if validation?.valid}
        <div class="form-section">
          <label>
            <span class="label">Project Name</span>
            <input
              type="text"
              bind:value={targetName}
              placeholder="Enter project name"
              class="text-input"
            />
          </label>

          <div class="options">
            <h4>Import Options</h4>

            <label class="checkbox">
              <input type="checkbox" bind:checked={options.renameOnConflict} />
              <span>Rename if project exists</span>
            </label>

            <label class="checkbox">
              <input type="checkbox" bind:checked={options.restoreGitHistory} />
              <span>Restore Git history</span>
            </label>

            <label class="checkbox">
              <input type="checkbox" bind:checked={options.verifyLfsObjects} />
              <span>Verify LFS objects</span>
            </label>

            <label class="checkbox">
              <input type="checkbox" bind:checked={options.overwrite} />
              <span>Overwrite existing project</span>
            </label>
          </div>
        </div>
      {/if}
    {:else if uploading}
      <div class="progress-section">
        <h3>Uploading Archive</h3>
        <div class="progress-bar">
          <div class="progress-fill" style="width: {uploadProgress}%"></div>
        </div>
        <span class="progress-text">{uploadProgress}%</span>
      </div>
    {:else if importing}
      <div class="progress-section">
        <h3>Importing Project</h3>
        <p class="import-message">{importMessage}</p>
        <div class="progress-bar">
          <div class="progress-fill" style="width: {importProgress}%"></div>
        </div>
        <span class="progress-text">{importProgress}%</span>
      </div>
    {/if}
  </div>

  <svelte:fragment slot="footer">
    <Button variant="ghost" on:click={handleClose} disabled={importing || uploading}>Cancel</Button>
    <Button
      variant="primary"
      on:click={handleImport}
      disabled={!selectedFile || !targetName || !validation?.valid || importing || uploading}
    >
      {#if importing}
        <Spinner size={16} />
        Importing...
      {:else if uploading}
        <Spinner size={16} />
        Uploading...
      {:else}
        Import Project
      {/if}
    </Button>
  </svelte:fragment>
</Dialog>

<style>
  .import-content {
    padding: 1rem;
    min-height: 300px;
  }

  .file-section {
    margin-bottom: 1.5rem;
  }

  .label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .file-input {
    display: none;
  }

  .file-display {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    border: 2px dashed var(--border-color);
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .file-display:hover {
    border-color: var(--primary);
    background: var(--bg-secondary);
  }

  .filename {
    font-weight: 500;
  }

  .size {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .placeholder {
    color: var(--text-secondary);
  }

  .validating {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    color: var(--text-secondary);
  }

  .validation-result {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.75rem;
    margin-bottom: 1rem;
    border-radius: 0.5rem;
    background: var(--bg-secondary);
  }

  .validation-result.valid {
    color: var(--success);
  }

  .validation-result:not(.valid) {
    color: var(--error);
  }

  .version {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .errors,
  .warnings {
    margin-top: 0.5rem;
  }

  .error,
  .warning {
    padding: 0.25rem 0;
    font-size: 0.875rem;
  }

  .error {
    color: var(--error);
  }

  .warning {
    color: var(--warning);
  }

  .form-section {
    margin-top: 1.5rem;
  }

  .text-input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 0.25rem;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .options {
    margin-top: 1.5rem;
  }

  .options h4 {
    margin-bottom: 0.75rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
    cursor: pointer;
  }

  .checkbox input {
    cursor: pointer;
  }

  .progress-section {
    text-align: center;
    padding: 2rem 0;
  }

  .progress-section h3 {
    margin-bottom: 1rem;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .import-message {
    margin-bottom: 1rem;
    color: var(--text-secondary);
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: var(--bg-secondary);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 0.5rem;
  }

  .progress-fill {
    height: 100%;
    background: var(--primary);
    transition: width 0.3s ease;
  }

  .progress-text {
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
</style>
