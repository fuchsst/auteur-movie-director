<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api/client';
  import { projects, currentProject, selectProject, setLoading, setError } from '$lib/stores';
  import { selectionStore } from '$lib/stores/selection';
  import type { WorkspaceProject, GitStatus } from '$lib/types/project';
  import ProjectTree from './ProjectTree.svelte';
  import NewProjectDialog from './NewProjectDialog.svelte';

  let showNewProjectDialog = false;
  let refreshing = false;

  // Load projects on mount
  onMount(() => {
    loadProjects();
  });

  async function loadProjects() {
    setLoading(true);
    try {
      const projectList = await api.listProjects();

      // Load Git status for each project
      const projectsWithStatus = await Promise.all(
        projectList.map(async (project) => {
          try {
            const gitStatus = await api.getGitStatus(project.manifest?.id || '');
            return { ...project, git_status: gitStatus };
          } catch {
            // Git status might fail if not initialized
            return project;
          }
        })
      );

      projects.set(projectsWithStatus);
    } catch (error) {
      setError(`Failed to load projects: ${error}`);
    } finally {
      setLoading(false);
    }
  }

  async function refreshProjects() {
    refreshing = true;
    await loadProjects();
    refreshing = false;
  }

  function handleProjectSelect(project: WorkspaceProject) {
    if (project.manifest) {
      selectProject(project.manifest);
      selectionStore.selectProject(project.manifest.id);
    }
  }

  function handleNewProject() {
    showNewProjectDialog = true;
  }

  async function handleProjectCreated() {
    showNewProjectDialog = false;
    await loadProjects();
  }
</script>

<div class="project-browser">
  <div class="browser-header">
    <h3>Projects</h3>
    <div class="header-actions">
      <button class="btn-icon" title="Refresh" on:click={refreshProjects} disabled={refreshing}>
        <span class:spinning={refreshing}>⟳</span>
      </button>
      <button class="btn-icon" title="New Project" on:click={handleNewProject}> + </button>
    </div>
  </div>

  <div class="project-list">
    {#if $projects.length === 0}
      <div class="empty-state">
        <p>No projects found</p>
        <button class="btn btn-primary" on:click={handleNewProject}> Create First Project </button>
      </div>
    {:else}
      {#each $projects as project}
        <ProjectTree
          {project}
          selected={$currentProject?.id === project.manifest?.id}
          on:select={() => handleProjectSelect(project)}
        />
      {/each}
    {/if}
  </div>
</div>

{#if showNewProjectDialog}
  <NewProjectDialog
    on:close={() => (showNewProjectDialog = false)}
    on:created={handleProjectCreated}
  />
{/if}

<style>
  .project-browser {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .browser-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 1rem;
  }

  .browser-header h3 {
    margin: 0;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
  }

  .header-actions {
    display: flex;
    gap: 0.25rem;
  }

  .btn-icon {
    background: none;
    border: none;
    color: var(--text-secondary);
    width: 1.75rem;
    height: 1.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-icon:hover {
    background: var(--surface);
    color: var(--text-primary);
  }

  .btn-icon:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .spinning {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .project-list {
    flex: 1;
    overflow-y: auto;
    margin: 0 -1rem;
    padding: 0 1rem;
  }

  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
  }

  .empty-state p {
    margin-bottom: 1rem;
  }
</style>
