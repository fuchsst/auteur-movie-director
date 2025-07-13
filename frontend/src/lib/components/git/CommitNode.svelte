<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { EnhancedGitCommit } from '$lib/api/git';

  export let commit: EnhancedGitCommit;
  export let selected = false;

  const dispatch = createEventDispatcher();

  function formatTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60));
      return minutes === 1 ? '1 minute ago' : `${minutes} minutes ago`;
    } else if (hours < 24) {
      return hours === 1 ? '1 hour ago' : `${hours} hours ago`;
    } else if (days < 7) {
      return days === 1 ? '1 day ago' : `${days} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  function getCommitIcon(message: string): string {
    const lower = message.toLowerCase();
    if (lower.startsWith('feat:')) return '✨';
    if (lower.startsWith('fix:')) return '🐛';
    if (lower.startsWith('docs:')) return '📝';
    if (lower.startsWith('style:')) return '💄';
    if (lower.startsWith('refactor:')) return '♻️';
    if (lower.startsWith('test:')) return '✅';
    if (lower.startsWith('chore:')) return '🔧';
    if (lower.startsWith('[auto]')) return '🤖';
    return '📦';
  }

  function handleClick() {
    dispatch('select');
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick();
    }
  }
</script>

<div
  class="commit-node"
  class:selected
  data-commit-hash={commit.hash}
  on:click={handleClick}
  on:keydown={handleKeydown}
  role="button"
  tabindex="0"
  aria-label="Commit: {commit.message}"
>
  <div class="node-marker" class:selected>
    <span class="icon">{getCommitIcon(commit.message)}</span>
  </div>

  <div class="node-content">
    <div class="commit-header">
      <p class="message" title={commit.message}>
        {commit.message}
      </p>
      <span class="hash" title={commit.hash}>
        {commit.shortHash}
      </span>
    </div>

    <div class="metadata">
      <span class="author" title={commit.email}>
        {commit.author}
      </span>
      <span class="separator">•</span>
      <time datetime={commit.date} title={new Date(commit.date).toLocaleString()}>
        {formatTime(commit.date)}
      </time>
      {#if commit.stats}
        <span class="separator">•</span>
        <span class="stats" title="{commit.stats.files} files changed">
          <span class="additions">+{commit.stats.additions}</span>
          <span class="deletions">-{commit.stats.deletions}</span>
        </span>
      {/if}
    </div>

    {#if commit.files.length > 0}
      <div class="file-summary">
        {#each commit.files.slice(0, 3) as file}
          <span class="file-badge" title={file.path}>
            {file.path.split('/').pop()}
          </span>
        {/each}
        {#if commit.files.length > 3}
          <span class="more-files">+{commit.files.length - 3} more</span>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .commit-node {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 0.75rem 1rem;
    margin-left: -1rem;
    margin-right: -1rem;
    cursor: pointer;
    transition: all 0.2s;
    border-radius: 8px;
    position: relative;
  }

  .commit-node:hover {
    background: var(--surface-hover);
  }

  .commit-node.selected {
    background: var(--surface-selected);
  }

  .commit-node:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: -2px;
  }

  .node-marker {
    position: relative;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--surface-primary);
    border: 2px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: all 0.2s;
    z-index: 1;
  }

  .node-marker.selected {
    border-color: var(--primary-color);
    background: var(--primary-color);
  }

  .node-marker .icon {
    font-size: 14px;
    filter: grayscale(0.5);
  }

  .node-marker.selected .icon {
    filter: none;
  }

  .node-content {
    flex: 1;
    min-width: 0;
  }

  .commit-header {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
  }

  .message {
    flex: 1;
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .hash {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-tertiary);
    flex-shrink: 0;
  }

  .metadata {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
  }

  .separator {
    color: var(--text-tertiary);
  }

  .author {
    font-weight: 500;
  }

  .stats {
    font-family: var(--font-mono);
    font-size: 0.75rem;
  }

  .additions {
    color: var(--success-color);
  }

  .deletions {
    color: var(--error-color);
  }

  .file-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .file-badge {
    display: inline-block;
    padding: 0.125rem 0.5rem;
    background: var(--surface-secondary);
    border-radius: 12px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    max-width: 150px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .more-files {
    display: inline-block;
    padding: 0.125rem 0.5rem;
    font-size: 0.75rem;
    color: var(--text-tertiary);
  }

  @media (max-width: 768px) {
    .commit-node {
      padding: 0.5rem;
    }

    .node-marker {
      width: 28px;
      height: 28px;
    }

    .message {
      font-size: 0.875rem;
    }

    .metadata {
      font-size: 0.75rem;
    }

    .file-summary {
      display: none;
    }
  }
</style>
