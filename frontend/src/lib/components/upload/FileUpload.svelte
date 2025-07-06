<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { api } from '$lib/api/client';
  import { currentProject } from '$lib/stores';
  import { websocket } from '$lib/services/websocket';
  import { MessageType } from '$lib/types/websocket';
  import { taskStore } from '$lib/stores/tasks';
  import type { AssetType } from '$lib/types/project';

  export let category: string;
  export let acceptedTypes: string[] = [];
  export let multiple = false;
  export let metadata: Record<string, any> = {};

  const dispatch = createEventDispatcher();

  let files: File[] = [];
  let uploading = false;
  let uploadProgress: Record<string, number> = {};
  let dragActive = false;
  let fileInput: HTMLInputElement;

  // File size formatting
  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  // Validate file type
  function isValidFileType(file: File): boolean {
    if (acceptedTypes.length === 0) return true;
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    return acceptedTypes.some((type) => {
      if (type.startsWith('.')) {
        return type === ext;
      }
      return file.type.match(type) !== null;
    });
  }

  // Handle file selection
  function handleFileSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      handleFiles(Array.from(input.files));
    }
  }

  // Handle drag and drop
  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragActive = true;
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    dragActive = false;
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragActive = false;

    if (event.dataTransfer?.files) {
      handleFiles(Array.from(event.dataTransfer.files));
    }
  }

  // Process selected files
  function handleFiles(selectedFiles: File[]) {
    const validFiles = selectedFiles.filter(isValidFileType);

    if (validFiles.length !== selectedFiles.length) {
      const invalidCount = selectedFiles.length - validFiles.length;
      dispatch('error', {
        message: `${invalidCount} file(s) had invalid type and were skipped`
      });
    }

    if (multiple) {
      files = [...files, ...validFiles];
    } else {
      files = validFiles.slice(0, 1);
    }
  }

  // Remove file from list
  function removeFile(index: number) {
    files = files.filter((_, i) => i !== index);
    delete uploadProgress[files[index]?.name];
  }

  // Upload files
  async function uploadFiles() {
    if (!$currentProject || files.length === 0) return;

    uploading = true;
    uploadProgress = {};

    // Create tasks for each file
    const taskIds: Record<string, string> = {};

    try {
      for (const file of files) {
        const taskId = taskStore.add({
          name: `Upload ${file.name}`,
          type: 'upload',
          details: `${formatFileSize(file.size)} - ${category}`,
          cancellable: false
        });
        taskIds[file.name] = taskId;
      }

      // Subscribe to progress events
      const unsubscribe = websocket.on(MessageType.TASK_PROGRESS, (payload) => {
        // Update progress for matching file
        files.forEach((file) => {
          if (payload.task_id.includes(file.name)) {
            uploadProgress[file.name] = payload.progress;
            if (taskIds[file.name]) {
              taskStore.updateProgress(taskIds[file.name], {
                progress: payload.progress * 100,
                details: payload.message
              });
            }
          }
        });
      });

      // Upload files
      const results = [];
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append(
          'metadata',
          JSON.stringify({
            ...metadata,
            original_name: file.name,
            size: file.size,
            type: file.type
          })
        );
        formData.append('auto_commit', 'true');

        const response = await fetch(
          `${api.baseUrl}/api/v1/upload/${$currentProject.id}/${category}`,
          {
            method: 'POST',
            body: formData
          }
        );

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = await response.json();
        results.push(result);

        // Mark task as completed
        if (taskIds[file.name]) {
          taskStore.updateProgress(taskIds[file.name], {
            status: 'completed',
            progress: 100,
            completedAt: Date.now()
          });
        }
      }

      // Cleanup
      unsubscribe();

      // Dispatch success event
      dispatch('uploaded', { files: results });

      // Reset
      files = [];
      uploadProgress = {};
      if (fileInput) fileInput.value = '';
    } catch (error) {
      // Mark all tasks as failed
      Object.values(taskIds).forEach((taskId) => {
        taskStore.updateProgress(taskId, {
          status: 'failed',
          error: error.message,
          completedAt: Date.now()
        });
      });
      dispatch('error', { message: `Upload failed: ${error}` });
    } finally {
      uploading = false;
    }
  }
</script>

<div class="file-upload">
  <div
    class="drop-zone"
    class:active={dragActive}
    class:has-files={files.length > 0}
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
  >
    {#if files.length === 0}
      <div class="drop-content">
        <div class="upload-icon">📁</div>
        <p>Drag & drop files here</p>
        <p class="sub-text">or</p>
        <button class="btn btn-primary" on:click={() => fileInput?.click()} disabled={uploading}>
          Browse Files
        </button>
        {#if acceptedTypes.length > 0}
          <p class="accepted-types">
            Accepted: {acceptedTypes.join(', ')}
          </p>
        {/if}
      </div>
    {:else}
      <div class="file-list">
        {#each files as file, index}
          <div class="file-item">
            <div class="file-info">
              <span class="file-name">{file.name}</span>
              <span class="file-size">{formatFileSize(file.size)}</span>
            </div>
            {#if uploadProgress[file.name] !== undefined}
              <div class="progress-bar">
                <div class="progress-fill" style="width: {uploadProgress[file.name] * 100}%"></div>
              </div>
            {:else if !uploading}
              <button class="remove-btn" on:click={() => removeFile(index)} title="Remove file">
                ×
              </button>
            {/if}
          </div>
        {/each}
      </div>

      <div class="upload-actions">
        {#if !uploading}
          <button
            class="btn"
            on:click={() => {
              files = [];
              if (fileInput) fileInput.value = '';
            }}
          >
            Clear All
          </button>
          <button class="btn btn-primary" on:click={uploadFiles}>
            Upload {files.length} File{files.length !== 1 ? 's' : ''}
          </button>
        {:else}
          <p class="uploading-text">Uploading...</p>
        {/if}
      </div>
    {/if}
  </div>

  <input
    bind:this={fileInput}
    type="file"
    accept={acceptedTypes.join(',')}
    {multiple}
    on:change={handleFileSelect}
    style="display: none"
  />
</div>

<style>
  .file-upload {
    width: 100%;
    height: 100%;
  }

  .drop-zone {
    min-height: 200px;
    height: 100%;
    border: 2px dashed var(--border-color);
    border-radius: 0.5rem;
    background: var(--surface);
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    cursor: pointer;
  }

  .drop-zone:hover,
  .drop-zone.active {
    border-color: var(--primary-color);
    background: color-mix(in srgb, var(--primary-color) 5%, var(--surface));
  }

  .drop-zone.has-files {
    cursor: default;
    padding: 1rem;
    justify-content: space-between;
  }

  .drop-content {
    text-align: center;
    color: var(--text-secondary);
  }

  .upload-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .sub-text {
    margin: 0.5rem 0;
    font-size: 0.875rem;
    opacity: 0.7;
  }

  .accepted-types {
    margin-top: 1rem;
    font-size: 0.75rem;
    opacity: 0.7;
  }

  .file-list {
    width: 100%;
    flex: 1;
    overflow-y: auto;
    margin-bottom: 1rem;
  }

  .file-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem;
    background: var(--background);
    border-radius: 0.375rem;
    margin-bottom: 0.5rem;
    position: relative;
    overflow: hidden;
  }

  .file-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    flex: 1;
  }

  .file-name {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .file-size {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .progress-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--border-color);
  }

  .progress-fill {
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s ease;
  }

  .remove-btn {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 1.5rem;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .remove-btn:hover {
    background: var(--error-color);
    color: white;
  }

  .upload-actions {
    display: flex;
    gap: 0.75rem;
    width: 100%;
    justify-content: center;
  }

  .uploading-text {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }
</style>
