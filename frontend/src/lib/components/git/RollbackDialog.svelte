<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { AlertTriangle } from 'lucide-svelte';
  import type { EnhancedGitCommit } from '$lib/api/git';
  
  export let commit: EnhancedGitCommit | undefined;
  
  const dispatch = createEventDispatcher();
  
  let selectedMode: 'soft' | 'mixed' | 'hard' = 'soft';
  
  const modeDescriptions = {
    soft: 'Moves HEAD to the selected commit. All changes since then will remain staged.',
    mixed: 'Moves HEAD and unstages changes. Files will remain modified in your working directory.',
    hard: 'Discards all changes since the selected commit. This cannot be undone!'
  };
  
  function handleConfirm() {
    dispatch('confirm', { mode: selectedMode });
  }
  
  function handleCancel() {
    dispatch('cancel');
  }
  
  function handleOverlayClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleCancel();
    }
  }
</script>

<div class="dialog-overlay" on:click={handleOverlayClick}>
  <div class="dialog">
    <div class="dialog-header">
      <AlertTriangle size={24} color="var(--warning-color)" />
      <h2>Rollback Project?</h2>
    </div>
    
    {#if commit}
      <div class="dialog-content">
        <p class="warning-text">
          You are about to rollback your project to:
        </p>
        
        <div class="commit-info">
          <div class="commit-hash">{commit.shortHash}</div>
          <div class="commit-message">{commit.message}</div>
          <div class="commit-meta">
            by {commit.author} • {new Date(commit.date).toLocaleDateString()}
          </div>
        </div>
        
        <div class="mode-selection">
          <h3>Rollback Mode:</h3>
          
          {#each Object.entries(modeDescriptions) as [mode, description]}
            <label class="mode-option" class:dangerous={mode === 'hard'}>
              <input
                type="radio"
                name="rollback-mode"
                value={mode}
                bind:group={selectedMode}
              />
              <div class="mode-content">
                <span class="mode-name">{mode.charAt(0).toUpperCase() + mode.slice(1)}</span>
                <span class="mode-description">{description}</span>
              </div>
            </label>
          {/each}
        </div>
        
        {#if selectedMode === 'hard'}
          <div class="danger-warning">
            <AlertTriangle size={16} />
            <p>
              <strong>Warning:</strong> Hard reset will permanently discard all uncommitted changes.
              Make sure you have backed up any important work!
            </p>
          </div>
        {/if}
      </div>
    {/if}
    
    <div class="dialog-actions">
      <button class="cancel-button" on:click={handleCancel}>
        Cancel
      </button>
      <button 
        class="confirm-button"
        class:dangerous={selectedMode === 'hard'}
        on:click={handleConfirm}
      >
        Rollback ({selectedMode})
      </button>
    </div>
  </div>
</div>

<style>
  .dialog-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
    animation: fadeIn 0.2s;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  .dialog {
    background: var(--surface-primary);
    border-radius: 12px;
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    animation: slideIn 0.3s ease-out;
  }
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .dialog-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1.5rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .dialog-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .dialog-content {
    padding: 1.5rem;
    overflow-y: auto;
    max-height: calc(90vh - 140px);
  }
  
  .warning-text {
    margin-bottom: 1rem;
    color: var(--text-secondary);
  }
  
  .commit-info {
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .commit-hash {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    color: var(--text-tertiary);
    margin-bottom: 0.25rem;
  }
  
  .commit-message {
    font-weight: 500;
    margin-bottom: 0.5rem;
  }
  
  .commit-meta {
    font-size: 0.8125rem;
    color: var(--text-secondary);
  }
  
  .mode-selection {
    margin-bottom: 1.5rem;
  }
  
  .mode-selection h3 {
    font-size: 0.9375rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
  }
  
  .mode-option {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    background: var(--surface-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .mode-option:hover {
    background: var(--surface-hover);
    border-color: var(--primary-color);
  }
  
  .mode-option.dangerous:hover {
    border-color: var(--error-color);
  }
  
  .mode-option input[type="radio"] {
    margin-top: 0.125rem;
  }
  
  .mode-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .mode-name {
    font-weight: 500;
    font-size: 0.9375rem;
  }
  
  .mode-description {
    font-size: 0.8125rem;
    color: var(--text-secondary);
    line-height: 1.4;
  }
  
  .danger-warning {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 6px;
    color: var(--error-color);
    font-size: 0.8125rem;
  }
  
  .danger-warning p {
    margin: 0;
    line-height: 1.4;
  }
  
  .dialog-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: flex-end;
    padding: 1.5rem;
    border-top: 1px solid var(--border-color);
  }
  
  .cancel-button,
  .confirm-button {
    padding: 0.625rem 1.25rem;
    border-radius: 6px;
    font-size: 0.9375rem;
    font-weight: 500;
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
    border-color: var(--text-secondary);
  }
  
  .confirm-button {
    background: var(--primary-color);
    border: none;
    color: white;
  }
  
  .confirm-button:hover {
    background: var(--primary-hover);
  }
  
  .confirm-button.dangerous {
    background: var(--error-color);
  }
  
  .confirm-button.dangerous:hover {
    background: var(--error-hover);
  }
  
  @media (max-width: 768px) {
    .dialog {
      margin: 1rem;
      max-height: calc(100vh - 2rem);
    }
    
    .dialog-content {
      max-height: calc(100vh - 2rem - 140px);
    }
  }
</style>