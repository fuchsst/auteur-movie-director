<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { X, RotateCcw, Tag, FileText, Image } from 'lucide-svelte';
  import type { EnhancedGitCommit } from '$lib/api/git';
  import DiffViewer from './DiffViewer.svelte';
  import RollbackDialog from './RollbackDialog.svelte';
  
  export let projectId: string;
  export let commitHash: string;
  export let commit: EnhancedGitCommit | undefined;
  
  const dispatch = createEventDispatcher();
  
  let selectedFile: string | null = null;
  let showRollbackDialog = false;
  let showTagDialog = false;
  let tagName = '';
  let tagMessage = '';
  
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }
  
  function getFileIcon(path: string): typeof FileText {
    const ext = path.split('.').pop()?.toLowerCase();
    if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext || '')) {
      return Image;
    }
    return FileText;
  }
  
  function getChangeTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      'A': 'Added',
      'M': 'Modified',
      'D': 'Deleted',
      'R': 'Renamed',
      'C': 'Copied'
    };
    return labels[type] || type;
  }
  
  function getChangeTypeColor(type: string): string {
    const colors: Record<string, string> = {
      'A': 'var(--success-color)',
      'M': 'var(--warning-color)',
      'D': 'var(--error-color)',
      'R': 'var(--info-color)',
      'C': 'var(--info-color)'
    };
    return colors[type] || 'var(--text-secondary)';
  }
  
  function handleClose() {
    dispatch('close');
  }
  
  function handleRollback() {
    showRollbackDialog = true;
  }
  
  function confirmRollback(mode: 'soft' | 'mixed' | 'hard') {
    dispatch('rollback', { commitHash, mode });
    showRollbackDialog = false;
  }
  
  function handleCreateTag() {
    showTagDialog = true;
  }
  
  function createTag() {
    if (tagName.trim()) {
      dispatch('tag', { 
        commitHash, 
        tagName: tagName.trim(), 
        message: tagMessage.trim() || null 
      });
      showTagDialog = false;
      tagName = '';
      tagMessage = '';
    }
  }
</script>

<div class="commit-details">
  <div class="details-header">
    <h2>Commit Details</h2>
    <button class="close-button" on:click={handleClose} aria-label="Close">
      <X size={20} />
    </button>
  </div>
  
  {#if commit}
    <div class="details-content">
      <div class="commit-info">
        <div class="info-row">
          <span class="label">Hash:</span>
          <code class="hash">{commit.hash}</code>
        </div>
        
        <div class="info-row">
          <span class="label">Author:</span>
          <span>{commit.author} &lt;{commit.email}&gt;</span>
        </div>
        
        <div class="info-row">
          <span class="label">Date:</span>
          <span>{formatDate(commit.date)}</span>
        </div>
        
        <div class="message-section">
          <span class="label">Message:</span>
          <p class="commit-message">{commit.message}</p>
        </div>
        
        {#if commit.stats}
          <div class="stats-section">
            <div class="stat">
              <span class="stat-value additions">+{commit.stats.additions}</span>
              <span class="stat-label">additions</span>
            </div>
            <div class="stat">
              <span class="stat-value deletions">-{commit.stats.deletions}</span>
              <span class="stat-label">deletions</span>
            </div>
            <div class="stat">
              <span class="stat-value">{commit.stats.files}</span>
              <span class="stat-label">files changed</span>
            </div>
          </div>
        {/if}
      </div>
      
      <div class="action-buttons">
        <button class="action-button rollback" on:click={handleRollback}>
          <RotateCcw size={16} />
          Rollback to this commit
        </button>
        <button class="action-button tag" on:click={handleCreateTag}>
          <Tag size={16} />
          Create tag
        </button>
      </div>
      
      {#if commit.files.length > 0}
        <div class="files-section">
          <h3>Changed Files ({commit.files.length})</h3>
          <div class="file-list">
            {#each commit.files as file}
              <button
                class="file-item"
                class:selected={selectedFile === file.path}
                on:click={() => selectedFile = selectedFile === file.path ? null : file.path}
              >
                <svelte:component this={getFileIcon(file.path)} size={16} />
                <span class="file-path">{file.path}</span>
                <span 
                  class="change-type" 
                  style:color={getChangeTypeColor(file.changeType)}
                >
                  {getChangeTypeLabel(file.changeType)}
                </span>
                {#if file.additions || file.deletions}
                  <span class="file-stats">
                    <span class="additions">+{file.additions}</span>
                    <span class="deletions">-{file.deletions}</span>
                  </span>
                {/if}
              </button>
            {/each}
          </div>
        </div>
      {/if}
      
      {#if selectedFile}
        <div class="diff-section">
          <h3>Changes in {selectedFile}</h3>
          <DiffViewer
            {projectId}
            {commitHash}
            filePath={selectedFile}
          />
        </div>
      {/if}
    </div>
  {:else}
    <div class="loading">
      <div class="spinner" />
      <p>Loading commit details...</p>
    </div>
  {/if}
</div>

{#if showRollbackDialog}
  <RollbackDialog
    {commit}
    on:confirm={(e) => confirmRollback(e.detail.mode)}
    on:cancel={() => showRollbackDialog = false}
  />
{/if}

{#if showTagDialog}
  <div class="tag-dialog-overlay" on:click={() => showTagDialog = false}>
    <div class="tag-dialog" on:click|stopPropagation>
      <h3>Create Tag</h3>
      <div class="form-group">
        <label for="tag-name">Tag Name:</label>
        <input
          id="tag-name"
          type="text"
          bind:value={tagName}
          placeholder="v1.0.0"
          class="tag-input"
        />
      </div>
      <div class="form-group">
        <label for="tag-message">Message (optional):</label>
        <textarea
          id="tag-message"
          bind:value={tagMessage}
          placeholder="Release notes..."
          class="tag-textarea"
          rows="3"
        />
      </div>
      <div class="dialog-actions">
        <button class="cancel-button" on:click={() => showTagDialog = false}>
          Cancel
        </button>
        <button 
          class="create-button" 
          on:click={createTag}
          disabled={!tagName.trim()}
        >
          Create Tag
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .commit-details {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--surface-primary);
  }
  
  .details-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .details-header h2 {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0;
  }
  
  .close-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: none;
    border: none;
    border-radius: 4px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .close-button:hover {
    background: var(--surface-hover);
    color: var(--text-primary);
  }
  
  .details-content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .commit-info {
    background: var(--surface-secondary);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
  
  .info-row {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }
  
  .label {
    font-weight: 600;
    color: var(--text-secondary);
    flex-shrink: 0;
  }
  
  .hash {
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    background: var(--surface-primary);
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
  }
  
  .message-section {
    margin-top: 1rem;
  }
  
  .commit-message {
    margin: 0.5rem 0 0;
    line-height: 1.5;
    white-space: pre-wrap;
  }
  
  .stats-section {
    display: flex;
    gap: 1.5rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color);
  }
  
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }
  
  .stat-value {
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .stat-value.additions {
    color: var(--success-color);
  }
  
  .stat-value.deletions {
    color: var(--error-color);
  }
  
  .stat-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }
  
  .action-buttons {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  
  .action-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 0.875rem;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .action-button:hover {
    background: var(--surface-hover);
    border-color: var(--primary-color);
  }
  
  .action-button.rollback:hover {
    border-color: var(--warning-color);
    color: var(--warning-color);
  }
  
  .files-section {
    margin-bottom: 1rem;
  }
  
  .files-section h3 {
    font-size: 0.9375rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
  }
  
  .file-list {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .file-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 0.8125rem;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }
  
  .file-item:hover,
  .file-item.selected {
    background: var(--surface-hover);
    border-color: var(--primary-color);
  }
  
  .file-path {
    flex: 1;
    font-family: var(--font-mono);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .change-type {
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .file-stats {
    font-family: var(--font-mono);
    font-size: 0.75rem;
  }
  
  .file-stats .additions {
    color: var(--success-color);
  }
  
  .file-stats .deletions {
    color: var(--error-color);
  }
  
  .diff-section {
    margin-top: 1rem;
  }
  
  .diff-section h3 {
    font-size: 0.9375rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
  }
  
  .loading {
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
    to { transform: rotate(360deg); }
  }
  
  /* Tag Dialog */
  .tag-dialog-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }
  
  .tag-dialog {
    background: var(--surface-primary);
    border-radius: 8px;
    padding: 1.5rem;
    width: 90%;
    max-width: 400px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  }
  
  .tag-dialog h3 {
    margin-top: 0;
    margin-bottom: 1rem;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  .form-group label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
  }
  
  .tag-input,
  .tag-textarea {
    width: 100%;
    padding: 0.5rem;
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.875rem;
    color: var(--text-primary);
    transition: border-color 0.2s;
  }
  
  .tag-input:focus,
  .tag-textarea:focus {
    outline: none;
    border-color: var(--primary-color);
  }
  
  .tag-textarea {
    resize: vertical;
    min-height: 60px;
  }
  
  .dialog-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 1.5rem;
  }
  
  .cancel-button,
  .create-button {
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .cancel-button {
    background: none;
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
  }
  
  .cancel-button:hover {
    background: var(--surface-hover);
    color: var(--text-primary);
  }
  
  .create-button {
    background: var(--primary-color);
    border: none;
    color: white;
  }
  
  .create-button:hover:not(:disabled) {
    background: var(--primary-hover);
  }
  
  .create-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>