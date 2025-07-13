<script lang="ts">
  import { onMount } from 'svelte';
  import { Read } from '$lib/api/client';
  import { Play, Image as ImageIcon } from 'lucide-svelte';

  export let projectId: string;
  export let commitHash: string;
  export let filePath: string;

  let diffContent = '';
  let loading = true;
  let error: string | null = null;
  let fileType: 'text' | 'image' | 'video' | 'binary' = 'text';
  let mediaUrl: string | null = null;

  const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'];
  const videoExtensions = ['mp4', 'mov', 'avi', 'mkv', 'webm'];

  function detectFileType(path: string): typeof fileType {
    const ext = path.split('.').pop()?.toLowerCase();
    if (!ext) return 'text';

    if (imageExtensions.includes(ext)) return 'image';
    if (videoExtensions.includes(ext)) return 'video';

    // Check if likely binary
    const binaryExtensions = ['pdf', 'zip', 'rar', '7z', 'exe', 'bin', 'dll'];
    if (binaryExtensions.includes(ext)) return 'binary';

    return 'text';
  }

  async function loadDiff() {
    loading = true;
    error = null;

    try {
      fileType = detectFileType(filePath);

      if (fileType === 'text') {
        // For text files, get the diff
        // This is a simplified version - in real implementation,
        // you'd call a git diff API endpoint
        const response = await fetch(
          `/api/git/projects/${projectId}/diff/${commitHash}?file=${encodeURIComponent(filePath)}`
        );
        if (!response.ok) throw new Error('Failed to load diff');
        diffContent = await response.text();
      } else if (fileType === 'image' || fileType === 'video') {
        // For media files, get the URL to the file at this commit
        mediaUrl = `/api/workspace/projects/${projectId}/file/${encodeURIComponent(filePath)}?commit=${commitHash}`;
      }
    } catch (err) {
      error = err.message || 'Failed to load file changes';
      console.error('Error loading diff:', err);
    } finally {
      loading = false;
    }
  }

  function parseDiff(
    diff: string
  ): Array<{ type: 'header' | 'add' | 'remove' | 'context'; content: string }> {
    const lines = diff.split('\n');
    const parsed = [];

    for (const line of lines) {
      if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
        parsed.push({ type: 'header', content: line });
      } else if (line.startsWith('+')) {
        parsed.push({ type: 'add', content: line.substring(1) });
      } else if (line.startsWith('-')) {
        parsed.push({ type: 'remove', content: line.substring(1) });
      } else {
        parsed.push({ type: 'context', content: line });
      }
    }

    return parsed;
  }

  onMount(() => {
    loadDiff();
  });

  $: parsedDiff = fileType === 'text' ? parseDiff(diffContent) : [];
</script>

<div class="diff-viewer">
  {#if loading}
    <div class="loading">
      <div class="spinner" />
      <p>Loading changes...</p>
    </div>
  {:else if error}
    <div class="error">
      <p>{error}</p>
    </div>
  {:else if fileType === 'binary'}
    <div class="binary-file">
      <p>Binary file changed</p>
      <p class="file-path">{filePath}</p>
    </div>
  {:else if fileType === 'image' && mediaUrl}
    <div class="media-preview">
      <div class="media-header">
        <ImageIcon size={16} />
        <span>Image Preview</span>
      </div>
      <img src={mediaUrl} alt={filePath} class="preview-image" />
    </div>
  {:else if fileType === 'video' && mediaUrl}
    <div class="media-preview">
      <div class="media-header">
        <Play size={16} />
        <span>Video Preview</span>
      </div>
      <video controls class="preview-video">
        <source src={mediaUrl} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </div>
  {:else if fileType === 'text' && parsedDiff.length > 0}
    <div class="diff-content">
      <pre class="diff-pre"><code
          >{#each parsedDiff as line}<div
              class="diff-line {line.type}"
              class:header={line.type === 'header'}
              class:add={line.type === 'add'}
              class:remove={line.type === 'remove'}><span class="line-marker"
                >{line.type === 'add' ? '+' : line.type === 'remove' ? '-' : ' '}</span
              ><span class="line-content">{line.content}</span></div>{/each}</code
        ></pre>
    </div>
  {:else}
    <div class="no-changes">
      <p>No changes to display</p>
    </div>
  {/if}
</div>

<style>
  .diff-viewer {
    background: var(--surface-secondary);
    border-radius: 8px;
    overflow: hidden;
    min-height: 200px;
  }

  .loading,
  .error,
  .binary-file,
  .no-changes {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 200px;
    color: var(--text-secondary);
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-color);
    border-top-color: var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .file-path {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    color: var(--text-tertiary);
  }

  .media-preview {
    padding: 1rem;
  }

  .media-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .preview-image,
  .preview-video {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    display: block;
  }

  .diff-content {
    font-size: 0.8125rem;
    overflow-x: auto;
  }

  .diff-pre {
    margin: 0;
    padding: 0;
  }

  .diff-line {
    display: flex;
    line-height: 1.4;
    font-family: var(--font-mono);
    white-space: pre;
  }

  .diff-line.header {
    background: var(--surface-tertiary);
    color: var(--text-secondary);
    font-weight: 600;
    padding: 0.25rem 0.5rem;
  }

  .diff-line.add {
    background: rgba(34, 197, 94, 0.1);
  }

  .diff-line.remove {
    background: rgba(239, 68, 68, 0.1);
  }

  .line-marker {
    width: 1.5rem;
    text-align: center;
    color: var(--text-tertiary);
    flex-shrink: 0;
    user-select: none;
  }

  .diff-line.add .line-marker {
    color: var(--success-color);
  }

  .diff-line.remove .line-marker {
    color: var(--error-color);
  }

  .line-content {
    flex: 1;
    padding-right: 1rem;
  }

  @media (max-width: 768px) {
    .diff-content {
      font-size: 0.75rem;
    }
  }
</style>
