<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { WorkspaceProject } from '$lib/types/project';

  export let project: WorkspaceProject;
  export let selected = false;

  const dispatch = createEventDispatcher();

  let expanded = false;

  // Project structure directories
  const directories = [
    { name: '01_Assets', icon: '📁', hasSubdirs: true },
    { name: '02_Source_Creative', icon: '📝', hasSubdirs: true },
    { name: '03_Renders', icon: '🎬', hasSubdirs: false },
    { name: '04_Project_Files', icon: '💾', hasSubdirs: true },
    { name: '05_Cache', icon: '⚡', hasSubdirs: false },
    { name: '06_Exports', icon: '📦', hasSubdirs: true }
  ];

  // Git status helpers
  $: isDirty = project.git_status?.is_dirty || false;
  $: modifiedCount =
    (project.git_status?.modified_files?.length || 0) +
    (project.git_status?.staged_files?.length || 0);
  $: untrackedCount = project.git_status?.untracked_files?.length || 0;

  function handleClick() {
    dispatch('select');
  }

  function toggleExpanded(e: Event) {
    e.stopPropagation();
    expanded = !expanded;
  }
</script>

<div class="project-tree" class:selected role="treeitem" aria-label={`Project: ${project.name}`}>
  <div 
    class="project-header" 
    on:click={handleClick}
    on:keydown={(e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleClick();
      }
    }}
    role="button"
    tabindex="0"
    aria-expanded={expanded}
  >
    <button
      class="expand-toggle"
      on:click={toggleExpanded}
      on:keydown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          toggleExpanded(e);
        }
      }}
      aria-label={expanded ? 'Collapse project structure' : 'Expand project structure'}
      aria-expanded={expanded}
      type="button"
    >
      {expanded ? '▼' : '▶'}
    </button>

    <span class="project-icon">📁</span>
    <span class="project-name">{project.name}</span>

    {#if isDirty}
      <div class="git-status" title="Git status">
        {#if modifiedCount > 0}
          <span class="modified">M {modifiedCount}</span>
        {/if}
        {#if untrackedCount > 0}
          <span class="untracked">U {untrackedCount}</span>
        {/if}
      </div>
    {/if}

    {#if project.git_status?.lfs_files && project.git_status.lfs_files.length > 0}
      <span class="lfs-indicator" title="Git LFS enabled">LFS</span>
    {/if}
  </div>

  {#if expanded}
    <div class="project-structure" role="tree">
      {#each directories as dir}
        <div 
          class="directory" 
          role="treeitem"
          tabindex="0"
          on:keydown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
            }
          }}
          aria-label={`${dir.name} directory ${dir.hasSubdirs ? 'with subdirectories' : ''}`}
        >
          <span class="dir-icon" aria-hidden="true">{dir.icon}</span>
          <span class="dir-name">{dir.name}</span>
        </div>
      {/each}

      <div 
        class="directory" 
        role="treeitem"
        tabindex="0"
        on:keydown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
          }
        }}
        aria-label="project.json configuration file"
      >
        <span class="dir-icon" aria-hidden="true">📋</span>
        <span class="dir-name">project.json</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .project-tree {
    margin-bottom: 0.5rem;
    border-radius: 0.375rem;
    overflow: hidden;
    background: var(--surface);
    border: 1px solid transparent;
    transition: all 0.2s;
  }

  .project-tree:hover {
    border-color: var(--border-color);
  }

  .project-tree.selected {
    border-color: var(--primary-color);
    background: color-mix(in srgb, var(--primary-color) 10%, var(--surface));
  }

  .project-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    cursor: pointer;
    user-select: none;
    outline: none;
  }

  .project-header:focus-visible {
    outline: 2px solid var(--primary-color);
    outline-offset: -2px;
  }

  .expand-toggle {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 0.75rem;
    width: 1rem;
    padding: 0;
    cursor: pointer;
    transition: transform 0.2s;
  }

  .project-icon {
    font-size: 1.125rem;
  }

  .project-name {
    flex: 1;
    font-weight: 500;
    color: var(--text-primary);
  }

  .git-status {
    display: flex;
    gap: 0.5rem;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .modified {
    color: var(--warning-color);
  }

  .untracked {
    color: var(--text-secondary);
  }

  .lfs-indicator {
    font-size: 0.625rem;
    padding: 0.125rem 0.375rem;
    background: var(--primary-color);
    color: white;
    border-radius: 0.25rem;
    font-weight: 600;
  }

  .project-structure {
    padding: 0 0.75rem 0.75rem 2.75rem;
  }

  .directory {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
    transition: color 0.2s;
    outline: none;
  }

  .directory:focus-visible {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
    border-radius: 2px;
  }

  .directory:hover {
    color: var(--text-primary);
  }

  .directory:focus {
    color: var(--text-primary);
  }

  .dir-icon {
    font-size: 1rem;
    width: 1.25rem;
    text-align: center;
  }

  .dir-name {
    flex: 1;
  }
</style>
