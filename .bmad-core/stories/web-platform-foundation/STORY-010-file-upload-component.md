# Story: File Upload Component

**Story ID**: STORY-010  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 3 (Small)  
**Priority**: Medium  

## Story Description
As a user, I need an intuitive drag-and-drop file upload interface so that I can easily add scripts, images, audio, and other assets to my project with visual feedback on upload progress. The system must automatically organize files according to the numbered directory structure, track large files with Git LFS, and provide real-time progress updates via WebSocket/Celery integration.

## Acceptance Criteria

### Functional Requirements
- [ ] Support drag-and-drop file uploads
- [ ] Allow click-to-browse file selection
- [ ] Display upload progress for each file via Celery task tracking
- [ ] Support multiple file uploads simultaneously
- [ ] Validate file types based on asset category
- [ ] Show file size and warn about large files (>10MB)
- [ ] Allow canceling uploads in progress
- [ ] Automatically route files to correct numbered directories (01_Assets, etc.)
- [ ] Trigger Git LFS tracking for applicable file types
- [ ] Validate against project structure API contract

### UI/UX Requirements
- [ ] Visual drop zone with clear affordance
- [ ] Progress bars for individual files with percentage
- [ ] Success/error states for each upload
- [ ] File type icons for different assets
- [ ] Responsive design for mobile/tablet
- [ ] Keyboard accessible interface
- [ ] Clear error messages for invalid files
- [ ] Display target directory for uploaded files
- [ ] Show LFS tracking status for large files

### Technical Requirements
- [ ] Use native HTML5 drag-and-drop API
- [ ] Implement chunked uploads for large files
- [ ] Validate files before upload starts
- [ ] Handle network errors gracefully
- [ ] Update project file list on success
- [ ] Integrate with WebSocket for real-time updates
- [ ] Support container volume paths (/Generative_Studio_Workspace)
- [ ] Honor Git LFS patterns from .gitattributes
- [ ] Integrate with Celery task progress tracking
- [ ] Respect numbered directory structure enforced by backend

## Implementation Notes

### Directory Structure Mapping
The component must understand the numbered directory structure and route files accordingly:

```typescript
const DIRECTORY_MAPPING = {
  scripts: '02_Source_Creative/Scripts',
  characters: '01_Assets/Generative_Assets/Characters',
  styles: '01_Assets/Generative_Assets/Styles', 
  environments: '01_Assets/Environments',
  audio: '01_Assets/Audio',
  media: '01_Assets/Media',
  models: '01_Assets/Models'
};
```

### File Upload Component
```svelte
<!-- src/lib/components/FileUpload.svelte -->
<script lang="ts">
  import { createEventDispatcher, onDestroy } from 'svelte';
  import { uploadFiles } from '$lib/api/files';
  import { websocket } from '$lib/stores/websocket';
  import { getFileIcon, formatBytes, isLFSRequired } from '$lib/utils';
  import type { AssetType, UploadFile, CeleryTask } from '$types';
  
  export let projectId: string;
  export let assetType: AssetType = 'scripts';
  export let multiple = true;
  export let maxFileSize = 100 * 1024 * 1024; // 100MB
  export let warnSize = 10 * 1024 * 1024; // 10MB - warn about LFS
  
  const dispatch = createEventDispatcher();
  
  let isDragging = false;
  let fileInput: HTMLInputElement;
  let uploads: Map<string, UploadFile> = new Map();
  let taskSubscriptions: Map<string, () => void> = new Map();
  
  const ALLOWED_EXTENSIONS: Record<AssetType, string[]> = {
    scripts: ['.fdx', '.txt', '.md', '.fountain'],
    characters: ['.json', '.yaml', '.png', '.jpg'],
    styles: ['.jpg', '.png', '.webp', '.gif'],
    environments: ['.hdr', '.exr', '.jpg', '.png'],
    audio: ['.wav', '.mp3', '.ogg', '.m4a'],
    media: ['.mp4', '.mov', '.webm', '.avi'],
    models: ['.glb', '.gltf', '.usdz', '.fbx']
  };
  
  const LFS_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.exr', '.mp4', '.mov', '.webm',
    '.wav', '.mp3', '.flac', '.glb', '.gltf', '.usdz',
    '.safetensors', '.ckpt'
  ];
  
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
    
    // Warn about LFS for large files
    if (file.size > warnSize && LFS_EXTENSIONS.includes(ext)) {
      dispatch('info', {
        message: `Large file ${file.name} will be tracked with Git LFS`
      });
    }
    
    return true;
  }
  
  // Subscribe to Celery task progress updates via WebSocket
  function subscribeToTaskProgress(taskId: string, uploadId: string) {
    const unsubscribe = websocket.subscribe(
      `task.progress.${taskId}`,
      (message) => {
        const upload = uploads.get(uploadId);
        if (upload && message.data) {
          upload.progress = message.data.progress || 0;
          upload.status = message.data.status || upload.status;
          
          if (message.data.status === 'completed') {
            upload.targetPath = message.data.result?.path;
            upload.lfsTracked = message.data.result?.lfs_tracked;
          }
          
          uploads = uploads;
        }
      }
    );
    
    taskSubscriptions.set(uploadId, unsubscribe);
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
          // XHR progress callback
          upload.progress = progress;
          uploads = uploads;
        }
      );
      
      // If backend returns a Celery task ID, subscribe to progress
      if (response.taskId) {
        subscribeToTaskProgress(response.taskId, id);
      } else {
        // Direct upload completed
        upload.status = 'completed';
        upload.progress = 100;
        upload.targetPath = response.files[0].path;
        upload.lfsTracked = response.files[0].lfs_tracked;
        uploads = uploads;
        
        dispatch('upload', { 
          file: response.files[0],
          targetPath: response.files[0].path,
          lfsTracked: response.files[0].lfs_tracked
        });
        
        // Remove completed upload after delay
        setTimeout(() => {
          cleanupUpload(id);
        }, 3000);
      }
      
    } catch (error) {
      upload.status = 'error';
      upload.error = error.message;
      uploads = uploads;
      
      dispatch('error', { message: `Upload failed: ${file.name}` });
    }
  }
  
  function cleanupUpload(id: string) {
    const unsubscribe = taskSubscriptions.get(id);
    if (unsubscribe) {
      unsubscribe();
      taskSubscriptions.delete(id);
    }
    uploads.delete(id);
    uploads = uploads;
  }
  
  function cancelUpload(id: string) {
    const upload = uploads.get(id);
    if (upload) {
      // TODO: Implement XHR abort for in-progress uploads
      // TODO: Send cancel request to backend for Celery tasks
      cleanupUpload(id);
    }
  }
  
  function formatProgress(progress: number): string {
    return `${Math.round(progress)}%`;
  }
  
  function getTargetDirectory(): string {
    return DIRECTORY_MAPPING[assetType] || '01_Assets';
  }
  
  // Cleanup subscriptions on component destroy
  onDestroy(() => {
    taskSubscriptions.forEach(unsubscribe => unsubscribe());
    taskSubscriptions.clear();
  });
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
      
      <p class="target-directory">
        Files will be uploaded to: {getTargetDirectory()}
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
            <div class="file-details">
              <span class="file-size">{formatBytes(upload.file.size)}</span>
              {#if upload.lfsTracked}
                <span class="lfs-badge" title="Tracked with Git LFS">LFS</span>
              {/if}
              {#if upload.targetPath}
                <span class="target-path" title={upload.targetPath}>
                  → {upload.targetPath.split('/').slice(-2).join('/')}
                </span>
              {/if}
            </div>
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
  
  .target-directory {
    font-size: 0.875rem;
    color: var(--text-muted);
    margin-top: 0.5rem;
  }
  
  .file-details {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-muted);
  }
  
  .lfs-badge {
    background: var(--primary-color);
    color: white;
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .target-path {
    font-family: monospace;
    font-size: 0.75rem;
  }
</style>
```

### API Integration
```typescript
// src/lib/api/files.ts
export interface UploadResponse {
  taskId?: string; // If processing asynchronously via Celery
  files?: Array<{
    id: string;
    name: string;
    path: string; // Full path within project structure
    size: number;
    mime_type: string;
    lfs_tracked: boolean; // Whether file is tracked by Git LFS
    created_at: string;
  }>;
}

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
  
  // Include target directory information
  formData.append('asset_type', assetType);
  formData.append('validate_structure', 'true');
  
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
        const error = JSON.parse(xhr.responseText);
        reject(new Error(error.detail || `Upload failed: ${xhr.statusText}`));
      }
    });
    
    xhr.addEventListener('error', () => {
      reject(new Error('Network error during upload'));
    });
    
    xhr.open('POST', `/api/v1/projects/${projectId}/assets`);
    xhr.send(formData);
  });
}
```

### Type Definitions
```typescript
// src/lib/types/upload.ts
export interface UploadFile {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error: string | null;
  targetPath?: string;
  lfsTracked?: boolean;
}

export interface CeleryTask {
  task_id: string;
  status: 'pending' | 'started' | 'progress' | 'completed' | 'failed';
  progress?: number;
  result?: any;
  error?: string;
}
```

### Container Path Considerations

The backend runs in a Docker container with the workspace mounted at `/Generative_Studio_Workspace`. The component must handle path translation:

1. **API Response Paths**: Backend returns container paths (e.g., `/Generative_Studio_Workspace/Projects/my-project/01_Assets/...`)
2. **UI Display**: Component should display project-relative paths for clarity
3. **Path Translation**: Frontend utilities should handle conversion between container and relative paths

```typescript
// src/lib/utils/paths.ts
export function toProjectRelativePath(fullPath: string, projectId: string): string {
  const projectPrefix = `/Generative_Studio_Workspace/Projects/${projectId}/`;
  if (fullPath.startsWith(projectPrefix)) {
    return fullPath.substring(projectPrefix.length);
  }
  return fullPath;
}
```

### WebSocket Integration Pattern

The component subscribes to task-specific channels for progress updates:

```typescript
// WebSocket message format for task progress
interface TaskProgressMessage {
  type: 'task.progress';
  task_id: string;
  data: {
    status: 'pending' | 'started' | 'progress' | 'completed' | 'failed';
    progress: number; // 0-100
    result?: {
      path: string;
      lfs_tracked: boolean;
    };
    error?: string;
  };
  timestamp: string;
}
```

## Dependencies
- File upload API endpoint (STORY-004)
- API client setup (STORY-011)
- WebSocket for real-time updates (STORY-009)
- Git integration service (STORY-006)

## Testing Criteria
- [ ] Drag-and-drop works in all browsers
- [ ] File validation prevents invalid uploads
- [ ] Progress tracking updates smoothly via WebSocket
- [ ] Multiple simultaneous uploads work
- [ ] Error handling shows clear messages
- [ ] Large file uploads complete successfully
- [ ] Files are placed in correct numbered directories
- [ ] Git LFS tracking is applied to large files
- [ ] Container volume paths are correctly resolved
- [ ] Celery task progress updates work correctly

## Definition of Done
- [ ] Component supports all required features
- [ ] File validation implemented for all asset types
- [ ] Progress tracking works for uploads (XHR and Celery)
- [ ] Error states handled gracefully
- [ ] Accessibility requirements met
- [ ] Component documented with examples
- [ ] Files uploaded to correct project structure directories
- [ ] Git LFS integration verified for large files
- [ ] WebSocket progress updates working
- [ ] Target directory displayed to users
- [ ] LFS tracking status shown in UI

## Story Links
- **Depends On**: STORY-004-file-management-api, STORY-011-api-client-setup
- **Enhances**: Project workspace functionality
- **Related PRD**: PRD-004-project-asset-management