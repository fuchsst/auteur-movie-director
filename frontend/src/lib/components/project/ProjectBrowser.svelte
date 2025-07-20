<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { workspaceApi, type ProjectResponse } from '$lib/api/workspace';
  import { projects, selectProject, setLoading, setError } from '$lib/stores';
  import { selectionStore } from '$lib/stores/selection';
  import NewProjectDialog from './NewProjectDialog.svelte';
  import ProjectExportDialog from './ProjectExportDialog.svelte';
  import ProjectImportDialog from './ProjectImportDialog.svelte';
  import { formatBytes } from '$lib/utils/format';

  const dispatch = createEventDispatcher();

  // View mode and UI state
  let viewMode: 'grid' | 'list' = 'list';
  let searchQuery = '';
  let sortBy: 'name' | 'created' | 'modified' = 'modified';
  let sortOrder: 'asc' | 'desc' = 'desc';
  let selectedProject: ProjectResponse | null = null;
  let showContextMenu = false;
  let contextMenuX = 0;
  let contextMenuY = 0;
  let showNewProjectDialog = false;
  let showExportDialog = false;
  let exportProject: ProjectResponse | null = null;
  let showImportDialog = false;
  let refreshing = false;
  let loading = false;

  // Project data
  let allProjects: ProjectResponse[] = [];
  let filteredProjects: ProjectResponse[] = [];

  // Load projects on mount
  onMount(() => {
    loadProjects();
    setupKeyboardShortcuts();
    return () => {
      document.removeEventListener('keydown', handleKeyboard);
      document.removeEventListener('click', hideContextMenu);
    };
  });

  async function loadProjects() {
    loading = true;
    setLoading(true);
    try {
      const projectList = await workspaceApi.listProjects({
        sort_by: sortBy,
        order: sortOrder,
        limit: 1000 // Load all projects for client-side filtering
      });

      allProjects = projectList;
      filterProjects();
      projects.set(allProjects); // Update global store for compatibility
    } catch (error) {
      setError(`Failed to load projects: ${error}`);
    } finally {
      loading = false;
      setLoading(false);
    }
  }

  function filterProjects() {
    if (!searchQuery.trim()) {
      filteredProjects = [...allProjects];
    } else {
      const query = searchQuery.toLowerCase();
      filteredProjects = allProjects.filter(
        (project) =>
          project.name.toLowerCase().includes(query) ||
          project.manifest?.metadata?.description?.toLowerCase().includes(query) ||
          project.quality.toLowerCase().includes(query) ||
          project.narrative_structure.toLowerCase().includes(query)
      );
    }

    // Sort filtered results
    filteredProjects.sort((a, b) => {
      let aVal: string | number, bVal: string | number;
      switch (sortBy) {
        case 'name':
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
          break;
        case 'created':
          aVal = new Date(a.created);
          bVal = new Date(b.created);
          break;
        case 'modified':
        default:
          aVal = new Date(a.modified);
          bVal = new Date(b.modified);
          break;
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }

  async function refreshProjects() {
    refreshing = true;
    await loadProjects();
    refreshing = false;
  }

  function handleProjectSelect(project: ProjectResponse) {
    selectedProject = project;

    // Convert to legacy format for compatibility
    // const legacyProject = {
    //   name: project.name,
    //   path: project.path,
    //   manifest: project.manifest
    // };

    selectProject(project.manifest);
    selectionStore.selectProject(project.id);

    dispatch('projectSelected', project);
  }

  function handleProjectDoubleClick(project: ProjectResponse) {
    handleProjectSelect(project);
    dispatch('openProject', project);
  }

  function handleRightClick(event: MouseEvent, project: ProjectResponse) {
    event.preventDefault();
    selectedProject = project;
    showContextMenu = true;
    contextMenuX = event.clientX;
    contextMenuY = event.clientY;
  }

  function hideContextMenu() {
    showContextMenu = false;
  }

  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', handleKeyboard);
    document.addEventListener('click', hideContextMenu);
  }

  function handleKeyboard(event: KeyboardEvent) {
    if (event.target instanceof HTMLInputElement) return; // Skip if typing in input

    switch (event.key) {
      case 'n':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          handleNewProject();
        }
        break;
      case 'Delete':
        if (selectedProject) {
          event.preventDefault();
          handleDeleteProject();
        }
        break;
      case 'F2':
        if (selectedProject) {
          event.preventDefault();
          handleRenameProject();
        }
        break;
      case 'Enter':
        if (selectedProject) {
          event.preventDefault();
          dispatch('openProject', selectedProject);
        }
        break;
      case 'F5':
        event.preventDefault();
        refreshProjects();
        break;
    }
  }

  function handleNewProject() {
    showNewProjectDialog = true;
  }

  async function handleProjectCreated() {
    showNewProjectDialog = false;
    await loadProjects();
  }

  async function handleDeleteProject() {
    if (!selectedProject) return;

    const confirmed = confirm(
      `Are you sure you want to delete "${selectedProject.name}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    try {
      await workspaceApi.deleteProject(selectedProject.id, true);
      await loadProjects();
      selectedProject = null;
    } catch (error) {
      setError(`Failed to delete project: ${error}`);
    }
    hideContextMenu();
  }

  async function handleRenameProject() {
    if (!selectedProject) return;

    const newName = prompt('Enter new project name:', selectedProject.name);
    if (!newName || newName === selectedProject.name) return;

    try {
      await workspaceApi.updateProject(selectedProject.id, { name: newName });
      await loadProjects();
    } catch (error) {
      setError(`Failed to rename project: ${error}`);
    }
    hideContextMenu();
  }

  function handleExportProject() {
    if (!selectedProject) return;

    exportProject = selectedProject;
    showExportDialog = true;
    hideContextMenu();
  }

  async function handleDuplicateProject() {
    if (!selectedProject) return;

    try {
      const newName = `${selectedProject.name} (Copy)`;
      // Note: Duplicate functionality would need backend support
      // For now, just create a new project with similar settings
      const duplicateData = {
        name: newName,
        narrative_structure: selectedProject.narrative_structure,
        quality: selectedProject.quality,
        description: selectedProject.manifest?.metadata?.description || ''
      };

      await workspaceApi.createProject(duplicateData);
      await loadProjects();
    } catch (error) {
      setError(`Failed to duplicate project: ${error}`);
    }
    hideContextMenu();
  }


  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  function getProjectThumbnail(project: ProjectResponse): string {
    // TODO: Implement thumbnail generation/caching
    // For now, return a placeholder based on narrative structure
    const placeholders: Record<string, string> = {
      'three-act': '🎬',
      'hero-journey': '🗡️',
      'beat-sheet': '📝',
      'story-circle': '🔄'
    };
    return placeholders[project.narrative_structure] || '🎥';
  }

  function getGitStatusColor(status: string | null): string {
    switch (status) {
      case 'clean':
        return '#10b981'; // green
      case 'modified':
        return '#f59e0b'; // amber
      case 'uninitialized':
        return '#6b7280'; // gray
      default:
        return '#ef4444'; // red
    }
  }

  // Reactive statements
  $: {
    filterProjects();
  }
</script>

<div class="project-browser">
  <!-- Header with search and controls -->
  <div class="browser-header">
    <h3>Projects</h3>
    <div class="header-controls">
      <div class="search-box">
        <input
          type="text"
          placeholder="Search projects..."
          bind:value={searchQuery}
          class="search-input"
        />
        <span class="search-icon">🔍</span>
      </div>
      <div class="view-controls">
        <select bind:value={sortBy} class="sort-select">
          <option value="modified">Modified</option>
          <option value="created">Created</option>
          <option value="name">Name</option>
        </select>
        <button
          class="btn-icon"
          title="Sort Order"
          on:click={() => (sortOrder = sortOrder === 'asc' ? 'desc' : 'asc')}
        >
          {sortOrder === 'asc' ? '↑' : '↓'}
        </button>
        <button
          class="btn-icon {viewMode === 'grid' ? 'active' : ''}"
          title="Grid View"
          on:click={() => (viewMode = 'grid')}
        >
          ⊞
        </button>
        <button
          class="btn-icon {viewMode === 'list' ? 'active' : ''}"
          title="List View"
          on:click={() => (viewMode = 'list')}
        >
          ☰
        </button>
        <button class="btn-icon" title="Refresh" on:click={refreshProjects} disabled={refreshing}>
          <span class:spinning={refreshing}>⟳</span>
        </button>
        <button class="btn-icon primary" title="New Project (Ctrl+N)" on:click={handleNewProject}>
          +
        </button>
        <button class="btn-icon" title="Import Project" on:click={() => (showImportDialog = true)}>
          ⬆
        </button>
      </div>
    </div>
  </div>

  <!-- Project display area -->
  <div class="project-container">
    {#if loading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading projects...</p>
      </div>
    {:else if filteredProjects.length === 0}
      <div class="empty-state">
        {#if searchQuery}
          <p>No projects found matching "{searchQuery}"</p>
          <button class="btn btn-secondary" on:click={() => (searchQuery = '')}>
            Clear Search
          </button>
        {:else}
          <p>No projects found</p>
          <button class="btn btn-primary" on:click={handleNewProject}>
            Create First Project
          </button>
        {/if}
      </div>
    {:else if viewMode === 'grid'}
      <div class="project-grid">
        {#each filteredProjects as project}
          <button
            class="project-card {selectedProject?.id === project.id ? 'selected' : ''}"
            on:click={() => handleProjectSelect(project)}
            on:dblclick={() => handleProjectDoubleClick(project)}
            on:contextmenu={(e) => handleRightClick(e, project)}
            type="button"
            aria-label="Open project {project.name}"
          >
            <div class="project-thumbnail">
              <span class="thumbnail-icon">{getProjectThumbnail(project)}</span>
              <div
                class="git-status"
                style="background-color: {getGitStatusColor(project.git_status)}"
              ></div>
            </div>
            <div class="project-info">
              <h4 class="project-name" title={project.name}>{project.name}</h4>
              <p class="project-meta">
                <span class="quality">{project.quality}</span>
                <span class="structure">{project.narrative_structure}</span>
              </p>
              <p class="project-details">
                <span class="size">{formatBytes(project.size_bytes)}</span>
                <span class="date">{formatDate(project.modified)}</span>
              </p>
            </div>
          </button>
        {/each}
      </div>
    {:else}
      <div class="project-list">
        {#each filteredProjects as project}
          <button
            class="project-item {selectedProject?.id === project.id ? 'selected' : ''}"
            on:click={() => handleProjectSelect(project)}
            on:dblclick={() => handleProjectDoubleClick(project)}
            on:contextmenu={(e) => handleRightClick(e, project)}
            type="button"
            aria-label="Open project {project.name}"
          >
            <div class="project-icon">
              <span class="thumbnail-icon">{getProjectThumbnail(project)}</span>
              <div
                class="git-status"
                style="background-color: {getGitStatusColor(project.git_status)}"
              ></div>
            </div>
            <div class="project-details">
              <h4 class="project-name">{project.name}</h4>
              <div class="project-meta">
                <span class="quality badge">{project.quality}</span>
                <span class="structure">{project.narrative_structure}</span>
                <span class="size">{formatBytes(project.size_bytes)}</span>
              </div>
              <div class="project-dates">
                <span>Modified: {formatDate(project.modified)}</span>
                <span>Created: {formatDate(project.created)}</span>
              </div>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>

<!-- Context Menu -->
{#if showContextMenu}
  <div
    class="context-menu"
    style="left: {contextMenuX}px; top: {contextMenuY}px;"
    on:click={hideContextMenu}
    role="menu"
    tabindex="-1"
    on:keydown={(e) => {
      if (e.key === 'Escape') {
        hideContextMenu();
      }
    }}
  >
    <button on:click={() => dispatch('openProject', selectedProject)}>Open</button>
    <button on:click={handleRenameProject}>Rename</button>
    <button on:click={handleDuplicateProject}>Duplicate</button>
    <button on:click={handleExportProject}>Export...</button>
    <button on:click={() => (showImportDialog = true)}>Import...</button>
    <hr />
    <button on:click={handleDeleteProject} class="dangerous">Delete</button>
  </div>
{/if}

<!-- New Project Dialog -->
{#if showNewProjectDialog}
  <NewProjectDialog
    on:close={() => (showNewProjectDialog = false)}
    on:created={handleProjectCreated}
  />
{/if}

<!-- Export Project Dialog -->
{#if showExportDialog && exportProject}
  <ProjectExportDialog
    bind:open={showExportDialog}
    projectId={exportProject.id}
    projectName={exportProject.name}
    on:close={() => {
      showExportDialog = false;
      exportProject = null;
    }}
  />
{/if}

<!-- Import Project Dialog -->
{#if showImportDialog}
  <ProjectImportDialog
    bind:open={showImportDialog}
    on:close={() => (showImportDialog = false)}
    on:imported={async (event) => {
      await loadProjects();
      const importedProject = allProjects.find((p) => p.id === event.detail.projectId);
      if (importedProject) {
        handleProjectSelect(importedProject);
      }
    }}
  />
{/if}

<style>
  .project-browser {
    display: flex;
    flex-direction: column;
    height: 100%;
    position: relative;
  }

  /* Header */
  .browser-header {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
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

  .header-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  /* Search Box */
  .search-box {
    position: relative;
    flex: 1;
    min-width: 200px;
  }

  .search-input {
    width: 100%;
    padding: 0.5rem 2rem 0.5rem 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--surface);
    color: var(--text-primary);
    font-size: 0.875rem;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }

  .search-icon {
    position: absolute;
    right: 0.75rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-secondary);
    pointer-events: none;
  }

  /* View Controls */
  .view-controls {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .sort-select {
    padding: 0.375rem 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 0.25rem;
    background: var(--surface);
    color: var(--text-primary);
    font-size: 0.875rem;
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
    font-size: 0.875rem;
  }

  .btn-icon:hover {
    background: var(--surface);
    color: var(--text-primary);
  }

  .btn-icon.active {
    background: var(--accent);
    color: white;
  }

  .btn-icon.primary {
    background: var(--accent);
    color: white;
  }

  .btn-icon.primary:hover {
    background: var(--accent-hover);
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

  /* Project Container */
  .project-container {
    flex: 1;
    overflow-y: auto;
    margin: 0 -1rem;
    padding: 0 1rem;
  }

  /* Loading State */
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
  }

  .spinner {
    width: 2rem;
    height: 2rem;
    border: 2px solid var(--border-color);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-secondary);
  }

  .empty-state p {
    margin-bottom: 1rem;
  }

  /* Grid View */
  .project-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
    padding: 0.5rem 0;
  }

  .project-card {
    background: var(--surface);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    text-align: left;
    font-family: inherit;
    font-size: inherit;
  }

  .project-card:hover {
    border-color: var(--accent);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .project-card.selected {
    border-color: var(--accent);
    background: rgba(59, 130, 246, 0.05);
  }

  .project-thumbnail {
    position: relative;
    width: 100%;
    height: 80px;
    background: var(--background);
    border-radius: 0.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.75rem;
  }

  .thumbnail-icon {
    font-size: 2rem;
  }

  .git-status {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .project-info {
    text-align: center;
  }

  .project-name {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .project-meta {
    margin: 0 0 0.5rem 0;
    font-size: 0.75rem;
    color: var(--text-secondary);
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .project-details {
    margin: 0;
    font-size: 0.75rem;
    color: var(--text-secondary);
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
  }

  /* List View */
  .project-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.5rem 0;
  }

  .project-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem;
    background: var(--surface);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    font-family: inherit;
    font-size: inherit;
    width: 100%;
  }

  .project-item:hover {
    border-color: var(--accent);
    background: rgba(59, 130, 246, 0.02);
  }

  .project-item.selected {
    border-color: var(--accent);
    background: rgba(59, 130, 246, 0.05);
  }

  .project-icon {
    position: relative;
    width: 3rem;
    height: 3rem;
    background: var(--background);
    border-radius: 0.375rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .project-icon .thumbnail-icon {
    font-size: 1.5rem;
  }

  .project-icon .git-status {
    position: absolute;
    top: -2px;
    right: -2px;
    width: 10px;
    height: 10px;
    border: 2px solid var(--surface);
  }

  .project-details {
    flex: 1;
    min-width: 0;
  }

  .project-details .project-name {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .project-details .project-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.25rem;
    flex-wrap: wrap;
  }

  .project-dates {
    font-size: 0.75rem;
    color: var(--text-secondary);
    display: flex;
    gap: 1rem;
  }

  /* Badges */
  .badge {
    padding: 0.125rem 0.375rem;
    background: var(--accent);
    color: white;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .quality.badge {
    background: var(--accent);
  }

  /* Context Menu */
  .context-menu {
    position: fixed;
    background: var(--surface);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    padding: 0.25rem;
    z-index: 1000;
    min-width: 120px;
  }

  .context-menu button {
    display: block;
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: none;
    border: none;
    text-align: left;
    color: var(--text-primary);
    cursor: pointer;
    border-radius: 0.25rem;
    transition: background 0.15s;
  }

  .context-menu button:hover {
    background: var(--background);
  }

  .context-menu button.dangerous {
    color: #ef4444;
  }

  .context-menu button.dangerous:hover {
    background: rgba(239, 68, 68, 0.1);
  }

  .context-menu hr {
    margin: 0.25rem 0;
    border: none;
    border-top: 1px solid var(--border-color);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .project-grid {
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 0.75rem;
    }

    .header-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .search-box {
      min-width: auto;
    }

    .view-controls {
      justify-content: center;
    }
  }

  @media (max-width: 480px) {
    .project-grid {
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    }

    .project-dates {
      flex-direction: column;
      gap: 0.25rem;
    }
  }
</style>
