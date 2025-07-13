<script lang="ts">
  import { gitApi } from '$lib/api/git';
  import { gitPerformanceApi } from '$lib/api/gitPerformance';
  import { gitStore } from '$lib/stores/git';
  import { notificationStore } from '$lib/stores/notifications';
  import GitTimeline from '../git/GitTimeline.svelte';
  import GitPerformanceMonitor from '../git/GitPerformanceMonitor.svelte';
  import { History, GitBranch, RefreshCw, Gauge } from 'lucide-svelte';

  export let projectId: string;

  let gitStatus: any = null;
  let loading = true;
  let showPerformance = false;

  async function loadGitStatus() {
    try {
      gitStatus = await gitApi.getStatus(projectId);
      gitStore.setStatus(projectId, gitStatus);
    } catch (error) {
      console.error('Failed to load Git status:', error);
      notificationStore.add({
        type: 'error',
        title: 'Git Error',
        message: 'Failed to load repository status'
      });
    } finally {
      loading = false;
    }
  }

  async function handleRollback(event: CustomEvent) {
    const { commitHash, mode } = event.detail;

    try {
      gitStore.setOperation('rollback', true);
      await gitApi.rollback(projectId, { commitHash, mode });

      notificationStore.add({
        type: 'success',
        title: 'Rollback Complete',
        message: `Successfully rolled back to commit ${commitHash.substring(0, 7)}`
      });

      // Reload status and history
      await loadGitStatus();
    } catch (error) {
      notificationStore.add({
        type: 'error',
        title: 'Rollback Failed',
        message: error.message || 'Failed to rollback repository'
      });
    } finally {
      gitStore.setOperation('rollback', false);
    }
  }

  async function handleCreateTag(event: CustomEvent) {
    const { commitHash, tagName, message } = event.detail;

    try {
      gitStore.setOperation('tag', true);
      await gitApi.createTag(projectId, { tagName, message });

      notificationStore.add({
        type: 'success',
        title: 'Tag Created',
        message: `Created tag "${tagName}" at commit ${commitHash.substring(0, 7)}`
      });
    } catch (error) {
      notificationStore.add({
        type: 'error',
        title: 'Tag Creation Failed',
        message: error.message || 'Failed to create tag'
      });
    } finally {
      gitStore.setOperation('tag', false);
    }
  }

  $: if (projectId) loadGitStatus();
</script>

<div class="git-view">
  {#if loading}
    <div class="loading-container">
      <div class="spinner" />
      <p>Loading repository information...</p>
    </div>
  {:else if !gitStatus?.initialized}
    <div class="empty-state">
      <GitBranch size={48} />
      <h2>Repository Not Initialized</h2>
      <p>This project doesn't have Git version control enabled yet.</p>
      <button class="primary-button" on:click={loadGitStatus}>
        <RefreshCw size={16} />
        Refresh Status
      </button>
    </div>
  {:else}
    <div class="git-header">
      <div class="header-info">
        <h2>
          <History size={20} />
          Version History
        </h2>
        {#if gitStatus.branch}
          <span class="branch-name">
            <GitBranch size={14} />
            {gitStatus.branch}
          </span>
        {/if}
        {#if gitStatus.is_dirty}
          <span class="dirty-indicator" title="Repository has uncommitted changes"> Modified </span>
        {/if}
      </div>

      <div class="header-stats">
        {#if gitStatus.untracked_files?.length > 0}
          <span class="stat">
            <span class="stat-value">{gitStatus.untracked_files.length}</span>
            <span class="stat-label">untracked</span>
          </span>
        {/if}
        {#if gitStatus.modified_files?.length > 0}
          <span class="stat">
            <span class="stat-value">{gitStatus.modified_files.length}</span>
            <span class="stat-label">modified</span>
          </span>
        {/if}
        {#if gitStatus.staged_files?.length > 0}
          <span class="stat">
            <span class="stat-value">{gitStatus.staged_files.length}</span>
            <span class="stat-label">staged</span>
          </span>
        {/if}
      </div>

      <button
        class="performance-toggle"
        on:click={() => (showPerformance = !showPerformance)}
        title="Toggle performance monitor"
      >
        <Gauge size={16} />
      </button>
    </div>

    <div class="content-container">
      <div class="timeline-container" class:with-performance={showPerformance}>
        <GitTimeline {projectId} on:rollback={handleRollback} on:tag={handleCreateTag} />
      </div>

      {#if showPerformance}
        <div class="performance-panel">
          <GitPerformanceMonitor />
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .git-view {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--surface-primary);
  }

  .loading-container,
  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
  }

  .spinner {
    width: 48px;
    height: 48px;
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

  .empty-state h2 {
    margin: 1rem 0 0.5rem;
    font-size: 1.25rem;
    color: var(--text-primary);
  }

  .empty-state p {
    margin-bottom: 1.5rem;
  }

  .primary-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 0.9375rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
  }

  .primary-button:hover {
    background: var(--primary-hover);
  }

  .git-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
    background: var(--surface-secondary);
  }

  .header-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .header-info h2 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .branch-name {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    background: var(--surface-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.875rem;
    font-family: var(--font-mono);
    color: var(--text-secondary);
  }

  .dirty-indicator {
    padding: 0.25rem 0.75rem;
    background: rgba(251, 191, 36, 0.1);
    color: var(--warning-color);
    border-radius: 4px;
    font-size: 0.8125rem;
    font-weight: 500;
  }

  .header-stats {
    display: flex;
    gap: 1.5rem;
  }

  .stat {
    display: flex;
    align-items: baseline;
    gap: 0.25rem;
  }

  .stat-value {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .stat-label {
    font-size: 0.8125rem;
    color: var(--text-secondary);
  }

  .performance-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text-secondary);
  }

  .performance-toggle:hover {
    background: var(--surface-hover);
    border-color: var(--primary-color);
    color: var(--text-primary);
  }

  .content-container {
    flex: 1;
    display: flex;
    gap: 1rem;
    overflow: hidden;
    padding: 0 1rem 1rem;
  }

  .timeline-container {
    flex: 1;
    overflow: hidden;
  }

  .timeline-container.with-performance {
    flex: 2;
  }

  .performance-panel {
    flex: 1;
    min-width: 320px;
    max-width: 400px;
    overflow-y: auto;
  }

  @media (max-width: 768px) {
    .git-header {
      flex-direction: column;
      gap: 0.75rem;
      align-items: flex-start;
    }

    .header-stats {
      gap: 1rem;
    }
  }
</style>
