# Story: File Upload Component

**Story ID**: STORY-010  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 3 (Small)  
**Priority**: Medium  

## Story Description
As a user, I need an intuitive drag-and-drop file upload interface so that I can easily add scripts, images, audio, AI models (LoRAs, checkpoints), control maps, and other assets to my project with visual feedback on upload progress. The system must automatically organize files according to the numbered directory structure, track large files with Git LFS, provide real-time progress updates via WebSocket/Celery integration, capture metadata for future node-based connections, and support the generative filmmaking pipeline by properly categorizing character LoRAs, style references, location assets, and creative documents.

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
- [ ] Capture asset metadata for node connections (model type, dimensions, etc.)
- [ ] Support AI model file types (.safetensors, .ckpt, .pt)
- [ ] Handle control map uploads (depth, edge, pose)
- [ ] Extract and store asset properties for future AssetReference use

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
The component must understand the numbered directory structure and route files accordingly, with enhanced support for AI model files:

```typescript
const DIRECTORY_MAPPING = {
  // Creative documents (aligned with pipeline)
  treatments: '02_Source_Creative/Treatments',
  scripts: '02_Source_Creative/Scripts',
  shotlists: '02_Source_Creative/Shot_Lists',
  beatsheets: '02_Source_Creative/Scripts',  // Emotional beat sheets
  canvas: '02_Source_Creative/Canvas',
  // Asset categories (aligned with pipeline)
  characters: '01_Assets/Characters',
  styles: '01_Assets/Styles',
  locations: '01_Assets/Locations',
  music: '01_Assets/Music',
  // AI-specific subdirectories
  loras: '01_Assets/Characters',  // Character LoRAs go with characters
  stylemodels: '01_Assets/Styles',  // Style LoRAs/models
  controlmaps: '01_Assets/Styles',  // Control maps for style guidance
  // Project files
  projectfiles: '04_Project_Files'
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
  export let captureMetadata = true; // Extract asset properties for nodes
  
  const dispatch = createEventDispatcher();
  
  let isDragging = false;
  let fileInput: HTMLInputElement;
  let uploads: Map<string, UploadFile> = new Map();
  let taskSubscriptions: Map<string, () => void> = new Map();
  
  const ALLOWED_EXTENSIONS: Record<AssetType, string[]> = {
    // Creative documents
    treatments: ['.md', '.txt', '.docx', '.pdf'],
    scripts: ['.fountain', '.fdx', '.txt', '.md'],
    shotlists: ['.json', '.csv', '.xlsx'],
    beatsheets: ['.json', '.yaml', '.csv'],
    canvas: ['.json'],  // Node graph saves
    // Asset categories (aligned with pipeline)
    characters: ['.safetensors', '.ckpt', '.pt', '.json', '.yaml', '.png', '.jpg'],
    styles: ['.safetensors', '.ckpt', '.jpg', '.png', '.webp'],
    locations: ['.hdr', '.exr', '.jpg', '.png', '.json'],
    music: ['.wav', '.mp3', '.ogg', '.flac', '.m4a'],
    // AI-specific
    loras: ['.safetensors', '.ckpt', '.pt'],
    stylemodels: ['.safetensors', '.ckpt'],
    controlmaps: ['.png', '.jpg', '.exr', '.tiff'],
    // Project files
    projectfiles: ['.blend', '.ma', '.mb', '.c4d', '.hip']
  };
  
  const LFS_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.exr', '.mp4', '.mov', '.webm',
    '.wav', '.mp3', '.flac', '.glb', '.gltf', '.usdz',
    '.safetensors', '.ckpt', '.pt', '.tiff', '.hdr'
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
        error: null,
        metadata: extractAssetMetadata(file, assetType)
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
  
  // Extract metadata for AI assets to support node connections and filmmaking pipeline
  function extractAssetMetadata(file: File, type: AssetType): Record<string, any> {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const metadata: Record<string, any> = {
      originalName: file.name,
      fileSize: file.size,
      mimeType: file.type || 'application/octet-stream',
      fileExtension: ext,
      uploadedAt: new Date().toISOString()
    };
    
    // Character assets (including LoRAs)
    if (type === 'characters' || type === 'loras') {
      metadata.assetCategory = 'character';
      metadata.isAIModel = ext === '.safetensors' || ext === '.ckpt' || ext === '.pt';
      
      // Check if this is a base face image
      if (file.name.toLowerCase() === 'base_face.png' || 
          file.name.toLowerCase().includes('base_face')) {
        metadata.isBaseFace = true;
        metadata.characterSubdir = '';  // Goes in character root
      }
      
      // Check if this is a variation
      const variationTypes = ['expression', 'angle', 'pose', 'lighting'];
      const variationType = variationTypes.find(v => file.name.toLowerCase().includes(v));
      if (variationType) {
        metadata.isVariation = true;
        metadata.variationType = variationType;
        metadata.characterSubdir = 'variations';
      }
      
      // Check if this is a LoRA model
      if (metadata.isAIModel) {
        metadata.characterSubdir = 'lora';
        metadata.requiresTraining = false;  // Already trained
        
        // Extract character info from filename patterns
        const characterMatch = file.name.match(/(.+?)[-_]v?(\d+\.?\d*)[-_]?(\d+)?/i);
        if (characterMatch) {
          metadata.characterName = characterMatch[1];
          metadata.version = characterMatch[2];
          metadata.trainingSteps = characterMatch[3] || null;
        }
      }
      
      // Extract trigger word from filename if present
      const triggerMatch = file.name.match(/\[(.+?)\]/);  // e.g., hero_v1.5[hero_character].safetensors
      if (triggerMatch) {
        metadata.triggerWord = triggerMatch[1];
      }
      
      metadata.supportsCompositePrompts = true;
      metadata.agentCompatible = ['CastingDirector'];
    }
    
    // Style assets (including style LoRAs)
    if (type === 'styles' || type === 'stylemodels') {
      metadata.assetCategory = 'style';
      metadata.isAIModel = ext === '.safetensors' || ext === '.ckpt';
      metadata.canBeReference = true;
      
      // Detect style type from filename
      const styleTypes = ['cinematic', 'anime', 'realistic', 'painterly', 'abstract'];
      const detectedStyle = styleTypes.find(s => file.name.toLowerCase().includes(s));
      metadata.styleType = detectedStyle || 'general';
      
      metadata.supportsCompositePrompts = true;
      metadata.agentCompatible = ['ArtDirector'];
    }
    
    // Location assets
    if (type === 'locations') {
      metadata.assetCategory = 'location';
      metadata.isEnvironment = ext === '.hdr' || ext === '.exr';
      metadata.is360 = file.name.toLowerCase().includes('360') || file.name.toLowerCase().includes('spherical');
      metadata.supportsCompositePrompts = true;
      metadata.agentCompatible = ['ArtDirector', 'Cinematographer'];
    }
    
    // Music assets
    if (type === 'music') {
      metadata.assetCategory = 'music';
      // Extract BPM from filename if present
      const bpmMatch = file.name.match(/(\d+)bpm/i);
      if (bpmMatch) {
        metadata.bpm = parseInt(bpmMatch[1]);
      }
      // Extract mood/genre from filename
      const moods = ['dramatic', 'upbeat', 'sad', 'tense', 'romantic', 'action'];
      const detectedMood = moods.find(m => file.name.toLowerCase().includes(m));
      metadata.mood = detectedMood || 'neutral';
      metadata.agentCompatible = ['SoundDesigner'];
    }
    
    // Creative documents
    if (type === 'scripts' || type === 'treatments' || type === 'beatsheets') {
      metadata.assetCategory = 'creative_document';
      metadata.documentType = type;
      metadata.agentCompatible = ['Screenwriter', 'Producer'];
      
      // Detect if it's an emotional beat sheet
      if (file.name.toLowerCase().includes('beat') || file.name.toLowerCase().includes('emotion')) {
        metadata.hasEmotionalBeats = true;
      }
    }
    
    if (type === 'shotlists') {
      metadata.assetCategory = 'creative_document';
      metadata.documentType = 'shot_list';
      metadata.agentCompatible = ['Cinematographer', 'Producer'];
    }
    
    if (type === 'canvas') {
      metadata.assetCategory = 'project_file';
      metadata.documentType = 'node_graph';
      metadata.canRestore = true;
    }
    
    // Control maps
    if (type === 'controlmaps') {
      const mapTypes = ['depth', 'canny', 'openpose', 'normal', 'seg', 'mlsd', 'scribble'];
      const detectedType = mapTypes.find(t => file.name.toLowerCase().includes(t));
      metadata.controlType = detectedType || 'unknown';
      metadata.requiresPreprocessing = false;
      metadata.agentCompatible = ['Cinematographer'];
    }
    
    return metadata;
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
          lfsTracked: response.files[0].lfs_tracked,
          metadata: upload.metadata,
          assetId: response.files[0].id // For future AssetReference connections
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
      
      {#if assetType === 'characters' || assetType === 'loras'}
        <p class="asset-hint">
          💡 Character assets will be managed by the Casting Director agent
        </p>
        <p class="asset-hint">
          📸 Upload "base_face.png" to set character's canonical appearance
        </p>
        <p class="asset-hint">
          🧠 LoRA models (.safetensors) will be placed in the lora/ subdirectory
        </p>
        <p class="asset-hint">
          🎲 Character variations (expressions, poses) go to variations/ folder
        </p>
      {/if}
      
      {#if assetType === 'styles' || assetType === 'stylemodels'}
        <p class="asset-hint">
          💡 Style references will be curated by the Art Director agent
        </p>
      {/if}
      
      {#if assetType === 'locations'}
        <p class="asset-hint">
          💡 Location assets define the environments for your scenes
        </p>
      {/if}
      
      {#if assetType === 'scripts' || assetType === 'beatsheets'}
        <p class="asset-hint">
          💡 Creative documents guide the narrative structure and emotional beats
        </p>
      {/if}
      
      {#if assetType === 'controlmaps'}
        <p class="asset-hint">
          💡 Control maps enable precise cinematographic guidance
        </p>
      {/if}
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
              {#if upload.metadata?.modelType}
                <span class="model-badge" title="AI Model">
                  {upload.metadata.modelType}
                </span>
              {/if}
              {#if upload.metadata?.triggerWord}
                <span class="trigger-badge" title="Trigger Word">
                  [{upload.metadata.triggerWord}]
                </span>
              {/if}
              {#if upload.metadata?.styleType}
                <span class="style-badge" title="Style Type">
                  {upload.metadata.styleType}
                </span>
              {/if}
              {#if upload.metadata?.controlType && upload.metadata.controlType !== 'unknown'}
                <span class="control-badge" title="Control Map Type">
                  {upload.metadata.controlType}
                </span>
              {/if}
              {#if upload.metadata?.mood}
                <span class="mood-badge" title="Music Mood">
                  {upload.metadata.mood}
                </span>
              {/if}
              {#if upload.metadata?.hasEmotionalBeats}
                <span class="beats-badge" title="Contains Emotional Beats">
                  Beats
                </span>
              {/if}
              {#if upload.metadata?.isBaseFace}
                <span class="character-badge" title="Character Base Face">
                  Base Face
                </span>
              {/if}
              {#if upload.metadata?.isVariation}
                <span class="character-badge variation" title="Character Variation">
                  {upload.metadata.variationType}
                </span>
              {/if}
              {#if upload.metadata?.characterSubdir}
                <span class="subdir-badge" title="Subdirectory">
                  → {upload.metadata.characterSubdir}/
                </span>
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
  
  .model-badge, .control-badge, .trigger-badge, .style-badge, .mood-badge, .beats-badge {
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
  }
  
  .model-badge {
    background: var(--accent-color);
    color: white;
  }
  
  .control-badge {
    background: var(--secondary-color);
    color: white;
  }
  
  .trigger-badge {
    background: var(--primary-color);
    color: white;
    font-family: monospace;
    text-transform: none;
  }
  
  .style-badge {
    background: var(--tertiary-color);
    color: white;
  }
  
  .mood-badge {
    background: var(--info-color);
    color: white;
  }
  
  .beats-badge {
    background: var(--warning-color);
    color: var(--text-dark);
  }
  
  .asset-hint {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-top: 0.5rem;
    font-style: italic;
  }
  
  .character-badge {
    background: var(--primary-color);
    color: white;
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .character-badge.variation {
    background: var(--secondary-color);
    text-transform: capitalize;
  }
  
  .subdir-badge {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-family: monospace;
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
    // Asset metadata for node connections
    metadata?: {
      assetType: string;
      modelType?: string;
      controlType?: string;
      dimensions?: { width: number; height: number };
      duration?: number; // For video/audio
      nodeCompatibility?: string[];
    };
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
  
  // Include target directory information and metadata
  formData.append('asset_type', assetType);
  formData.append('validate_structure', 'true');
  
  // For character assets, include subdirectory routing
  if (assetType === 'characters') {
    const characterMeta = files.map(file => {
      const upload = Array.from(uploads.values()).find(u => u.file === file);
      return {
        filename: file.name,
        subdirectory: upload?.metadata?.characterSubdir || '',
        isBaseFace: upload?.metadata?.isBaseFace || false,
        isVariation: upload?.metadata?.isVariation || false,
        isLoRA: upload?.metadata?.isAIModel || false
      };
    });
    formData.append('character_routing', JSON.stringify(characterMeta));
  }
  
  // Include metadata for each file if available
  const metadata = files.map(file => {
    const upload = Array.from(uploads.values()).find(u => u.file === file);
    return upload?.metadata || {};
  });
  formData.append('metadata', JSON.stringify(metadata));
  
  // Include context for agent processing if applicable
  if (metadata.some(m => m.agentCompatible?.length > 0)) {
    formData.append('notify_agents', 'true');
  }
  
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
  metadata?: Record<string, any>; // Asset metadata for node connections
}

export interface AssetMetadata {
  originalName: string;
  fileSize: number;
  mimeType: string;
  fileExtension: string;
  uploadedAt: string;
  assetCategory: 'character' | 'style' | 'location' | 'music' | 'creative_document' | 'project_file';
  
  // Character specific (including LoRAs)
  characterName?: string;
  triggerWord?: string;  // For LoRA activation
  trainingSteps?: number;
  
  // AI Model specific
  isAIModel?: boolean;
  modelType?: 'safetensors' | 'checkpoint' | 'lora';
  version?: string;
  
  // Style specific
  styleType?: 'cinematic' | 'anime' | 'realistic' | 'painterly' | 'abstract' | 'general';
  
  // Location specific
  isEnvironment?: boolean;
  is360?: boolean;
  
  // Music specific
  bpm?: number;
  mood?: 'dramatic' | 'upbeat' | 'sad' | 'tense' | 'romantic' | 'action' | 'neutral';
  
  // Creative document specific
  documentType?: 'treatment' | 'script' | 'shot_list' | 'beat_sheet' | 'node_graph';
  hasEmotionalBeats?: boolean;
  
  // Control map specific
  controlType?: 'depth' | 'canny' | 'openpose' | 'normal' | 'seg' | 'mlsd' | 'scribble' | 'unknown';
  requiresPreprocessing?: boolean;
  
  // Pipeline integration
  supportsCompositePrompts?: boolean;
  agentCompatible?: string[];  // Which agents can use this asset
  canBeReference?: boolean;
  canRestore?: boolean;  // For canvas saves
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

### AssetReference Preparation

The upload component prepares assets for future node-based connections:

```typescript
// src/lib/types/assets.ts
export interface AssetReference {
  id: string;
  type: 'character' | 'style' | 'lora' | 'checkpoint' | 'controlmap';
  path: string;
  metadata: AssetMetadata;
  projectId: string;
  createdAt: string;
  // For node connections
  nodeCompatibility: {
    canConnectTo: string[]; // Node types this asset can connect to
    requiredInputs?: string[]; // Additional inputs needed
    outputType?: string; // What this asset produces
  };
}

// Asset compatibility mapping for nodes and agents
export const ASSET_NODE_COMPATIBILITY = {
  characters: {
    canConnectTo: ['text-to-image', 'image-to-image', 'character-consistency'],
    outputType: 'character-reference',
    agentOwner: 'CastingDirector',
    compositePromptField: 'character_refs'
  },
  styles: {
    canConnectTo: ['text-to-image', 'style-transfer', 'image-to-image'],
    outputType: 'style-reference',
    agentOwner: 'ArtDirector',
    compositePromptField: 'style_refs'
  },
  locations: {
    canConnectTo: ['text-to-image', 'environment-generator'],
    outputType: 'location-reference',
    agentOwner: 'ArtDirector',
    compositePromptField: 'location_ref'
  },
  music: {
    canConnectTo: ['audio-generator', 'music-composer'],
    outputType: 'audio-reference',
    agentOwner: 'SoundDesigner',
    compositePromptField: 'music_ref'
  },
  controlmaps: {
    canConnectTo: ['controlnet', 'text-to-image'],
    outputType: 'control-conditioning',
    agentOwner: 'Cinematographer',
    compositePromptField: 'control_ref'
  },
  scripts: {
    canConnectTo: ['script-analyzer', 'prompt-generator'],
    outputType: 'narrative-reference',
    agentOwner: 'Screenwriter',
    compositePromptField: null  // Not directly used in prompts
  },
  beatsheets: {
    canConnectTo: ['emotion-analyzer', 'prompt-enhancer'],
    outputType: 'emotional-reference',
    agentOwner: 'Screenwriter',
    compositePromptField: 'emotional_keywords'
  }
};
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
- [ ] AI model files (.safetensors, .ckpt) upload correctly
- [ ] Control map detection works from filenames
- [ ] Asset metadata is extracted and stored
- [ ] LoRA file patterns are parsed correctly
- [ ] Character and style assets are categorized properly
- [ ] Character base face images identified and routed correctly
- [ ] Character variations organized into proper subdirectories
- [ ] LoRA training status updated on model upload

## Definition of Done
- [ ] Component supports all required features
- [ ] File validation implemented for all asset types including AI models
- [ ] Progress tracking works for uploads (XHR and Celery)
- [ ] Error states handled gracefully
- [ ] Accessibility requirements met
- [ ] Component documented with examples
- [ ] Files uploaded to correct project structure directories
- [ ] Git LFS integration verified for large files
- [ ] WebSocket progress updates working
- [ ] Target directory displayed to users
- [ ] LFS tracking status shown in UI
- [ ] Asset metadata extraction implemented
- [ ] AI model file support tested (.safetensors, .ckpt, .pt)
- [ ] Control map type detection working
- [ ] AssetReference data structure prepared for node connections

## Story Links
- **Depends On**: STORY-004-file-management-api, STORY-011-api-client-setup
- **Enhances**: Project workspace functionality
- **Related PRD**: PRD-004-project-asset-management