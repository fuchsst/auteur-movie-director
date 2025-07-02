# Story: File Upload Component

**Story ID**: STORY-010  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 3 (Small)  
**Priority**: Medium  

## Story Description
As a user, I need an intuitive drag-and-drop file upload interface so that I can easily add scripts, images, audio, and other assets to my project with visual feedback on upload progress.

## Acceptance Criteria

### Functional Requirements
- [ ] Support drag-and-drop file uploads
- [ ] Allow click-to-browse file selection
- [ ] Display upload progress for each file
- [ ] Support multiple file uploads simultaneously
- [ ] Validate file types based on asset category
- [ ] Show file size and warn about large files
- [ ] Allow canceling uploads in progress

### UI/UX Requirements
- [ ] Visual drop zone with clear affordance
- [ ] Progress bars for individual files
- [ ] Success/error states for each upload
- [ ] File type icons for different assets
- [ ] Responsive design for mobile/tablet
- [ ] Keyboard accessible interface
- [ ] Clear error messages for invalid files

### Technical Requirements
- [ ] Use native HTML5 drag-and-drop API
- [ ] Implement chunked uploads for large files
- [ ] Validate files before upload starts
- [ ] Handle network errors gracefully
- [ ] Update project file list on success
- [ ] Integrate with WebSocket for real-time updates

## Implementation Notes

### File Upload Component
```svelte
<!-- src/lib/components/FileUpload.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { uploadFiles } from '$lib/api/files';
  import { getFileIcon, formatBytes } from '$lib/utils';
  import type { AssetType, UploadFile } from '$types';
  
  export let projectId: string;
  export let assetType: AssetType = 'scripts';
  export let multiple = true;
  export let maxFileSize = 100 * 1024 * 1024; // 100MB
  
  const dispatch = createEventDispatcher();
  
  let isDragging = false;
  let fileInput: HTMLInputElement;
  let uploads: Map<string, UploadFile> = new Map();
  
  const ALLOWED_EXTENSIONS: Record<AssetType, string[]> = {
    scripts: ['.fdx', '.txt', '.md', '.fountain'],
    characters: ['.json', '.yaml', '.png', '.jpg'],
    styles: ['.jpg', '.png', '.webp', '.gif'],
    environments: ['.hdr', '.exr', '.jpg', '.png'],
    audio: ['.wav', '.mp3', '.ogg', '.m4a']
  };
  
  function handleDragEnter(e: DragEvent) {
    e.preventDefault();
    isDragging = true;
  }
  
  function handleDragLeave(e: DragEvent) {
    e.preventDefault();
    if (e.currentTarget === e.target) {
      isDragging = false;
    }
  }
  
  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    e.dataTransfer!.dropEffect = 'copy';
  }
  
  async function handleDrop(e: DragEvent) {
    e.preventDefault();
    isDragging = false;
    
    const files = Array.from(e.dataTransfer!.files);
    await processFiles(files);
  }
  
  async function handleFileSelect(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files) {
      const files = Array.from(input.files);
      await processFiles(files);
    }
  }
  
  async function processFiles(files: File[]) {
    const validFiles = files.filter(file => validateFile(file));
    
    if (validFiles.length === 0) {
      dispatch('error', { message: 'No valid files selected' });
      return;
    }
    
    // Create upload entries
    validFiles.forEach(file => {
      const id = crypto.randomUUID();
      uploads.set(id, {
        id,
        file,
        progress: 0,
        status: 'pending',
        error: null
      });
    });
    
    uploads = uploads; // Trigger reactivity
    
    // Start uploads
    for (const [id, upload] of uploads) {
      if (upload.status === 'pending') {
        await uploadFile(id, upload.file);
      }
    }
  }
  
  function validateFile(file: File): boolean {
    // Check file extension
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const allowed = ALLOWED_EXTENSIONS[assetType];
    
    if (!allowed.includes(ext)) {
      dispatch('error', { 
        message: `Invalid file type: ${file.name}. Allowed: ${allowed.join(', ')}`
      });
      return false;
    }
    
    // Check file size
    if (file.size > maxFileSize) {
      dispatch('error', { 
        message: `File too large: ${file.name} (${formatBytes(file.size)}). Max: ${formatBytes(maxFileSize)}`
      });
      return false;
    }
    
    return true;
  }
  
  async function uploadFile(id: string, file: File) {
    const upload = uploads.get(id)!;
    upload.status = 'uploading';
    uploads = uploads;
    
    try {
      const response = await uploadFiles(
        projectId,
        assetType,
        [file],
        (progress) => {
          upload.progress = progress;
          uploads = uploads;
        }
      );
      
      upload.status = 'completed';
      upload.progress = 100;
      uploads = uploads;
      
      dispatch('upload', { file: response.files[0] });
      
      // Remove completed upload after delay
      setTimeout(() => {
        uploads.delete(id);
        uploads = uploads;
      }, 3000);
      
    } catch (error) {
      upload.status = 'error';
      upload.error = error.message;
      uploads = uploads;
      
      dispatch('error', { message: `Upload failed: ${file.name}` });
    }
  }
  
  function cancelUpload(id: string) {
    // TODO: Implement upload cancellation
    uploads.delete(id);
    uploads = uploads;
  }
  
  function formatProgress(progress: number): string {
    return `${Math.round(progress)}%`;
  }
</script>

<div class="upload-container">
  <div
    class="drop-zone"
    class:dragging={isDragging}
    on:dragenter={handleDragEnter}
    on:dragleave={handleDragLeave}
    on:dragover={handleDragOver}
    on:drop={handleDrop}
  >
    <input
      bind:this={fileInput}
      type="file"
      accept={ALLOWED_EXTENSIONS[assetType].join(',')}
      {multiple}
      on:change={handleFileSelect}
      class="hidden"
    />
    
    <div class="drop-content">
      <svg class="upload-icon" viewBox="0 0 24 24">
        <path d="M9 16h6v-6h4l-7-7-7 7h4v6z"/>
        <path d="M5 18h14v2H5z"/>
      </svg>
      
      <p class="drop-text">
        Drag and drop {assetType} here or
        <button class="browse-button" on:click={() => fileInput.click()}>
          browse files
        </button>
      </p>
      
      <p class="allowed-types">
        Allowed: {ALLOWED_EXTENSIONS[assetType].join(', ')}
      </p>
    </div>
  </div>
  
  {#if uploads.size > 0}
    <div class="upload-list">
      {#each [...uploads.values()] as upload (upload.id)}
        <div class="upload-item" data-status={upload.status}>
          <img 
            src={getFileIcon(upload.file.name)} 
            alt="" 
            class="file-icon"
          />
          
          <div class="upload-info">
            <div class="file-name">{upload.file.name}</div>
            <div class="file-size">{formatBytes(upload.file.size)}</div>
          </div>
          
          {#if upload.status === 'uploading'}
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                style="width: {upload.progress}%"
              />
            </div>
            <span class="progress-text">{formatProgress(upload.progress)}</span>
          {/if}
          
          {#if upload.status === 'completed'}
            <svg class="status-icon success" viewBox="0 0 24 24">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
          {/if}
          
          {#if upload.status === 'error'}
            <div class="error-message">{upload.error}</div>
            <svg class="status-icon error" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
          {/if}
          
          {#if upload.status === 'pending' || upload.status === 'uploading'}
            <button 
              class="cancel-button" 
              on:click={() => cancelUpload(upload.id)}
              title="Cancel upload"
            >
              ×
            </button>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .upload-container {
    width: 100%;
  }
  
  .drop-zone {
    border: 2px dashed var(--border-color);
    border-radius: 8px;
    padding: 3rem;
    text-align: center;
    transition: all 0.3s;
    cursor: pointer;
  }
  
  .drop-zone.dragging {
    border-color: var(--primary-color);
    background: var(--primary-color-light);
  }
  
  .upload-icon {
    width: 48px;
    height: 48px;
    fill: var(--text-muted);
    margin-bottom: 1rem;
  }
  
  .hidden {
    display: none;
  }
  
  .browse-button {
    color: var(--primary-color);
    text-decoration: underline;
    background: none;
    border: none;
    cursor: pointer;
  }
  
  .upload-list {
    margin-top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .upload-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: var(--bg-secondary);
    border-radius: 4px;
  }
  
  .progress-bar {
    flex: 1;
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s;
  }
  
  .status-icon {
    width: 20px;
    height: 20px;
  }
  
  .status-icon.success {
    fill: var(--color-success);
  }
  
  .status-icon.error {
    fill: var(--color-error);
  }
</style>
```

### API Integration
```typescript
// src/lib/api/files.ts
export async function uploadFiles(
  projectId: string,
  assetType: string,
  files: File[],
  onProgress?: (progress: number) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  
  files.forEach(file => {
    formData.append('files', file);
  });
  
  const xhr = new XMLHttpRequest();
  
  return new Promise((resolve, reject) => {
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        const progress = (e.loaded / e.total) * 100;
        onProgress(progress);
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`Upload failed: ${xhr.statusText}`));
      }
    });
    
    xhr.addEventListener('error', () => {
      reject(new Error('Network error during upload'));
    });
    
    xhr.open('POST', `/api/v1/projects/${projectId}/assets?asset_type=${assetType}`);
    xhr.send(formData);
  });
}
```

## Dependencies
- File upload API endpoint (STORY-004)
- API client setup (STORY-011)
- WebSocket for real-time updates (STORY-009)

## Testing Criteria
- [ ] Drag-and-drop works in all browsers
- [ ] File validation prevents invalid uploads
- [ ] Progress tracking updates smoothly
- [ ] Multiple simultaneous uploads work
- [ ] Error handling shows clear messages
- [ ] Large file uploads complete successfully

## Definition of Done
- [ ] Component supports all required features
- [ ] File validation implemented for all asset types
- [ ] Progress tracking works for uploads
- [ ] Error states handled gracefully
- [ ] Accessibility requirements met
- [ ] Component documented with examples

## Story Links
- **Depends On**: STORY-004-file-management-api, STORY-011-api-client-setup
- **Enhances**: Project workspace functionality
- **Related PRD**: PRD-004-project-asset-management