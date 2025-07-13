<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { gitApi } from '$lib/api/git';
  import { gitPerformanceApi } from '$lib/api/gitPerformance';
  import { gitStore } from '$lib/stores/git';
  import type { EnhancedGitCommit } from '$lib/api/git';
  import CommitNode from './CommitNode.svelte';
  import CommitDetails from './CommitDetails.svelte';
  import TimelineControls from './TimelineControls.svelte';
  import { fly, fade } from 'svelte/transition';
  
  export let projectId: string;
  export let maxHeight = '600px';
  
  let commits: EnhancedGitCommit[] = [];
  let filteredCommits: EnhancedGitCommit[] = [];
  let selectedCommit: string | null = null;
  let loading = false;
  let error: string | null = null;
  let timelineScale: 'hours' | 'days' | 'weeks' | 'months' = 'days';
  let searchQuery = '';
  let selectedFileType: string | null = null;
  let timelineContainer: HTMLElement;
  let refreshInterval: number;
  let currentPage = 1;
  let totalPages = 1;
  let usePerformanceApi = true; // Use performance-optimized API
  
  interface TimeGroup {
    label: string;
    date: Date;
    commits: EnhancedGitCommit[];
  }
  
  // Load commits with performance optimization
  async function loadCommits(page = 1, limit = 50) {
    loading = true;
    error = null;
    
    try {
      if (usePerformanceApi) {
        // Use performance-optimized API with pagination
        const result = await gitPerformanceApi.getCachedHistory(projectId, page, limit);
        commits = result.commits;
        currentPage = result.pagination.page;
        totalPages = result.pagination.pages;
        
        // Update store
        gitStore.setHistory(projectId, commits);
        gitStore.setPagination(projectId, result.pagination);
      } else {
        // Fallback to standard API
        commits = await gitApi.getEnhancedHistory(projectId, limit);
      }
      
      filterCommits();
      
      // Load performance metrics
      const metrics = await gitPerformanceApi.getMetrics();
      gitStore.setPerformance(metrics);
    } catch (err) {
      // If performance API fails, fallback to standard API
      if (usePerformanceApi) {
        console.warn('Performance API failed, falling back to standard API:', err);
        usePerformanceApi = false;
        return loadCommits(page, limit);
      }
      
      error = err.message || 'Failed to load commit history';
      console.error('Error loading commits:', err);
    } finally {
      loading = false;
    }
  }
  
  // Load more commits (pagination)
  async function loadMore() {
    if (currentPage < totalPages && !loading) {
      await loadCommits(currentPage + 1);
    }
  }
  
  // Filter commits based on search and file type
  function filterCommits() {
    filteredCommits = commits.filter(commit => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesMessage = commit.message.toLowerCase().includes(query);
        const matchesAuthor = commit.author.toLowerCase().includes(query);
        if (!matchesMessage && !matchesAuthor) return false;
      }
      
      // File type filter
      if (selectedFileType) {
        const hasFileType = commit.files.some(file => {
          const ext = file.path.split('.').pop()?.toLowerCase();
          return ext === selectedFileType;
        });
        if (!hasFileType) return false;
      }
      
      return true;
    });
  }
  
  // Group commits by time scale
  function groupCommitsByTime(commits: EnhancedGitCommit[], scale: string): TimeGroup[] {
    const groups = new Map<string, TimeGroup>();
    
    commits.forEach(commit => {
      const date = new Date(commit.date);
      let key: string;
      let label: string;
      
      switch (scale) {
        case 'hours':
          key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`;
          label = date.toLocaleString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            hour: 'numeric',
            hour12: true 
          });
          break;
        case 'days':
          key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
          label = date.toLocaleDateString('en-US', { 
            weekday: 'short',
            month: 'short', 
            day: 'numeric' 
          });
          break;
        case 'weeks':
          const weekStart = new Date(date);
          weekStart.setDate(date.getDate() - date.getDay());
          key = `${weekStart.getFullYear()}-${weekStart.getMonth()}-${weekStart.getDate()}`;
          label = `Week of ${weekStart.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
          })}`;
          break;
        case 'months':
          key = `${date.getFullYear()}-${date.getMonth()}`;
          label = date.toLocaleDateString('en-US', { 
            month: 'long', 
            year: 'numeric' 
          });
          break;
      }
      
      if (!groups.has(key)) {
        groups.set(key, { label, date, commits: [] });
      }
      groups.get(key)!.commits.push(commit);
    });
    
    // Sort groups by date (newest first)
    return Array.from(groups.values()).sort((a, b) => b.date.getTime() - a.date.getTime());
  }
  
  // Keyboard navigation
  function handleKeydown(event: KeyboardEvent) {
    if (!filteredCommits.length) return;
    
    const currentIndex = selectedCommit 
      ? filteredCommits.findIndex(c => c.hash === selectedCommit)
      : -1;
    
    switch (event.key) {
      case 'ArrowUp':
        event.preventDefault();
        if (currentIndex > 0) {
          selectedCommit = filteredCommits[currentIndex - 1].hash;
          scrollToCommit(selectedCommit);
        }
        break;
      case 'ArrowDown':
        event.preventDefault();
        if (currentIndex < filteredCommits.length - 1) {
          selectedCommit = filteredCommits[currentIndex + 1].hash;
          scrollToCommit(selectedCommit);
        }
        break;
      case 'Enter':
        event.preventDefault();
        if (selectedCommit) {
          // Commit details are already shown
        }
        break;
      case 'r':
      case 'R':
        if (selectedCommit && !event.ctrlKey && !event.metaKey) {
          event.preventDefault();
          // Rollback handled by CommitDetails component
        }
        break;
    }
  }
  
  // Scroll to commit node
  function scrollToCommit(hash: string) {
    const element = timelineContainer?.querySelector(`[data-commit-hash="${hash}"]`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
  
  // Extract unique file types from commits
  function getFileTypes(commits: EnhancedGitCommit[]): string[] {
    const types = new Set<string>();
    commits.forEach(commit => {
      commit.files.forEach(file => {
        const ext = file.path.split('.').pop()?.toLowerCase();
        if (ext) types.add(ext);
      });
    });
    return Array.from(types).sort();
  }
  
  $: groupedCommits = groupCommitsByTime(filteredCommits, timelineScale);
  $: fileTypes = getFileTypes(commits);
  $: if (searchQuery !== undefined || selectedFileType !== undefined) filterCommits();
  
  onMount(() => {
    loadCommits();
    window.addEventListener('keydown', handleKeydown);
    
    // Auto-refresh every 30 seconds
    refreshInterval = window.setInterval(() => {
      loadCommits();
    }, 30000);
  });
  
  onDestroy(() => {
    window.removeEventListener('keydown', handleKeydown);
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
</script>

<div class="git-timeline" style:max-height={maxHeight}>
  <TimelineControls
    bind:timelineScale
    bind:searchQuery
    bind:selectedFileType
    {fileTypes}
    on:refresh={() => loadCommits()}
  />
  
  <div class="timeline-container" bind:this={timelineContainer}>
    {#if loading && !commits.length}
      <div class="loading" in:fade>
        <div class="spinner" />
        <p>Loading commit history...</p>
      </div>
    {:else if error}
      <div class="error" in:fade>
        <p>{error}</p>
        <button on:click={() => loadCommits()}>Retry</button>
      </div>
    {:else if !filteredCommits.length}
      <div class="empty" in:fade>
        {#if commits.length}
          <p>No commits match your filters</p>
        {:else}
          <p>No commits yet</p>
        {/if}
      </div>
    {:else}
      <div class="timeline-track">
        {#each groupedCommits as group (group.label)}
          <div class="time-group" in:fly={{ y: 20, duration: 300 }}>
            <h3 class="group-label">{group.label}</h3>
            <div class="group-commits">
              {#each group.commits as commit (commit.hash)}
                <CommitNode
                  {commit}
                  selected={commit.hash === selectedCommit}
                  on:select={() => selectedCommit = commit.hash}
                />
              {/each}
            </div>
          </div>
        {/each}
        
        {#if currentPage < totalPages}
          <div class="load-more-container">
            <button 
              class="load-more" 
              on:click={loadMore}
              disabled={loading}
            >
              {loading ? 'Loading...' : `Load More (Page ${currentPage + 1} of ${totalPages})`}
            </button>
          </div>
        {/if}
        
        {#if loading && commits.length > 0}
          <div class="loading-indicator">
            <div class="small-spinner" />
          </div>
        {/if}
      </div>
    {/if}
  </div>
  
  {#if selectedCommit}
    <div class="details-panel" transition:fly={{ x: 300, duration: 200 }}>
      <CommitDetails
        {projectId}
        commitHash={selectedCommit}
        commit={filteredCommits.find(c => c.hash === selectedCommit)}
        on:close={() => selectedCommit = null}
        on:rollback
      />
    </div>
  {/if}
</div>

<style>
  .git-timeline {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--surface-secondary);
    border-radius: 8px;
    overflow: hidden;
  }
  
  .timeline-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    position: relative;
  }
  
  .timeline-track {
    max-width: 800px;
    margin: 0 auto;
  }
  
  .time-group {
    margin-bottom: 2rem;
  }
  
  .group-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
    padding-left: 2rem;
    position: sticky;
    top: 0;
    background: var(--surface-secondary);
    z-index: 1;
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
  }
  
  .group-commits {
    position: relative;
    padding-left: 1rem;
  }
  
  .group-commits::before {
    content: '';
    position: absolute;
    left: 1rem;
    top: 1rem;
    bottom: 1rem;
    width: 2px;
    background: var(--border-color);
  }
  
  .loading,
  .error,
  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 200px;
    color: var(--text-secondary);
  }
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--border-color);
    border-top-color: var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .error button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .error button:hover {
    background: var(--primary-hover);
  }
  
  .load-more-container {
    display: flex;
    justify-content: center;
    margin: 2rem 0;
  }
  
  .load-more {
    padding: 0.75rem 1.5rem;
    background: var(--surface-primary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.875rem;
  }
  
  .load-more:hover:not(:disabled) {
    background: var(--surface-hover);
    border-color: var(--primary-color);
  }
  
  .load-more:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .loading-indicator {
    display: flex;
    justify-content: center;
    padding: 2rem;
  }
  
  .small-spinner {
    width: 24px;
    height: 24px;
    border: 2px solid var(--border-color);
    border-top-color: var(--primary-color);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  .details-panel {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 400px;
    background: var(--surface-primary);
    border-left: 1px solid var(--border-color);
    box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
    z-index: 10;
  }
  
  @media (max-width: 768px) {
    .details-panel {
      width: 100%;
    }
    
    .group-label {
      font-size: 0.75rem;
    }
  }
</style>