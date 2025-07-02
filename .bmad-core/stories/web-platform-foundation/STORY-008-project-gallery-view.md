# Story: Project Gallery View

**Story ID**: STORY-008  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 5 (Medium)  
**Priority**: High  

## Story Description
As a user, I need a visual gallery view of all my projects so that I can easily browse, create new projects, and access existing ones with a clear overview of their status and metadata.

## Acceptance Criteria

### Functional Requirements
- [ ] Display all projects in a responsive grid layout
- [ ] Show project thumbnail/preview image
- [ ] Display project name, creation date, and quality tier
- [ ] Provide "Create New Project" button/card
- [ ] Support grid and list view toggle
- [ ] Click on project navigates to project workspace
- [ ] Show project size and file count
- [ ] Display Git status indicator (clean/dirty)

### UI/UX Requirements
- [ ] Responsive design works on desktop and tablet
- [ ] Loading states while fetching projects
- [ ] Empty state when no projects exist
- [ ] Smooth transitions between views
- [ ] Search/filter projects by name
- [ ] Sort by name, date, or size
- [ ] Hover effects show additional details

### Technical Requirements
- [ ] Fetch projects from API on mount
- [ ] Handle API errors gracefully
- [ ] Use Svelte stores for state management
- [ ] Implement virtual scrolling for many projects
- [ ] Lazy load project thumbnails
- [ ] Debounce search input

## Implementation Notes

### Project Gallery Page
```svelte
<!-- src/routes/+page.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import ProjectCard from '$components/ProjectCard.svelte';
  import CreateProjectModal from '$components/CreateProjectModal.svelte';
  import ViewToggle from '$components/ViewToggle.svelte';
  import { projects, loadProjects } from '$stores/projects';
  import type { Project } from '$types';
  
  let viewMode: 'grid' | 'list' = 'grid';
  let searchQuery = '';
  let sortBy: 'name' | 'date' | 'size' = 'date';
  let showCreateModal = false;
  let loading = true;
  let error: string | null = null;
  
  onMount(async () => {
    try {
      await loadProjects();
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  });
  
  $: filteredProjects = $projects
    .filter(p => p.name.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'date':
          return new Date(b.modified).getTime() - new Date(a.modified).getTime();
        case 'size':
          return b.sizeBytes - a.sizeBytes;
      }
    });
</script>

<div class="gallery-container">
  <header class="gallery-header">
    <h1>My Projects</h1>
    
    <div class="controls">
      <input 
        type="search" 
        placeholder="Search projects..."
        bind:value={searchQuery}
      />
      
      <select bind:value={sortBy}>
        <option value="date">Sort by Date</option>
        <option value="name">Sort by Name</option>
        <option value="size">Sort by Size</option>
      </select>
      
      <ViewToggle bind:mode={viewMode} />
      
      <button class="create-button" on:click={() => showCreateModal = true}>
        + New Project
      </button>
    </div>
  </header>
  
  {#if loading}
    <div class="loading">Loading projects...</div>
  {:else if error}
    <div class="error">
      <p>Failed to load projects: {error}</p>
      <button on:click={() => loadProjects()}>Retry</button>
    </div>
  {:else if filteredProjects.length === 0}
    <div class="empty-state">
      {#if $projects.length === 0}
        <h2>No projects yet</h2>
        <p>Create your first project to get started</p>
        <button on:click={() => showCreateModal = true}>
          Create Project
        </button>
      {:else}
        <p>No projects match your search</p>
      {/if}
    </div>
  {:else}
    <div class="project-{viewMode}">
      {#each filteredProjects as project (project.id)}
        <ProjectCard {project} {viewMode} />
      {/each}
    </div>
  {/if}
</div>

{#if showCreateModal}
  <CreateProjectModal on:close={() => showCreateModal = false} />
{/if}

<style>
  .gallery-container {
    max-width: 1400px;
    margin: 0 auto;
  }
  
  .project-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }
  
  .project-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
</style>
```

### Project Card Component
```svelte
<!-- src/lib/components/ProjectCard.svelte -->
<script lang="ts">
  import type { Project } from '$types';
  import { formatBytes, formatDate } from '$utils/format';
  
  export let project: Project;
  export let viewMode: 'grid' | 'list' = 'grid';
  
  $: thumbnailUrl = `/api/v1/projects/${project.id}/thumbnail`;
</script>

<a 
  href="/project/{project.id}" 
  class="project-card {viewMode}"
  data-quality={project.quality}
>
  {#if viewMode === 'grid'}
    <div class="thumbnail">
      <img 
        src={thumbnailUrl} 
        alt="{project.name} thumbnail"
        loading="lazy"
        on:error={(e) => e.target.src = '/placeholder.png'}
      />
      <div class="quality-badge">{project.quality}</div>
    </div>
  {/if}
  
  <div class="info">
    <h3>{project.name}</h3>
    <div class="metadata">
      <span class="date">{formatDate(project.modified)}</span>
      <span class="size">{formatBytes(project.sizeBytes)}</span>
      <span class="files">{project.fileCount} files</span>
    </div>
    
    {#if project.gitStatus === 'dirty'}
      <div class="git-status" title="Uncommitted changes">●</div>
    {/if}
  </div>
</a>

<style>
  .project-card {
    display: block;
    background: var(--card-bg);
    border-radius: 8px;
    overflow: hidden;
    transition: transform 0.2s;
    text-decoration: none;
    color: inherit;
  }
  
  .project-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }
  
  .project-card.grid .thumbnail {
    aspect-ratio: 16/9;
    position: relative;
  }
  
  .quality-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    padding: 0.25rem 0.5rem;
    background: var(--quality-color);
    border-radius: 4px;
    font-size: 0.75rem;
  }
</style>
```

### Projects Store
```typescript
// src/lib/stores/projects.ts
import { writable, derived } from 'svelte/store';
import { api } from '$lib/api';
import type { Project } from '$types';

export const projects = writable<Project[]>([]);
export const projectsLoading = writable(false);
export const projectsError = writable<string | null>(null);

export async function loadProjects() {
  projectsLoading.set(true);
  projectsError.set(null);
  
  try {
    const response = await api.get('/projects');
    projects.set(response.data);
  } catch (error) {
    projectsError.set(error.message);
    throw error;
  } finally {
    projectsLoading.set(false);
  }
}

export async function createProject(data: CreateProjectData) {
  const response = await api.post('/projects', data);
  const newProject = response.data;
  
  projects.update(p => [...p, newProject]);
  return newProject;
}

export async function deleteProject(id: string) {
  await api.delete(`/projects/${id}`);
  projects.update(p => p.filter(project => project.id !== id));
}

// Derived store for project count
export const projectCount = derived(projects, $projects => $projects.length);
```

### Create Project Modal
```svelte
<!-- src/lib/components/CreateProjectModal.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { createProject } from '$stores/projects';
  import { goto } from '$app/navigation';
  
  const dispatch = createEventDispatcher();
  
  let name = '';
  let quality = 'standard';
  let creating = false;
  let error = '';
  
  async function handleCreate() {
    if (!name.trim()) {
      error = 'Project name is required';
      return;
    }
    
    creating = true;
    error = '';
    
    try {
      const project = await createProject({ name, quality });
      goto(`/project/${project.id}`);
    } catch (e) {
      error = e.message;
    } finally {
      creating = false;
    }
  }
</script>

<div class="modal-backdrop" on:click={() => dispatch('close')}>
  <div class="modal" on:click|stopPropagation>
    <h2>Create New Project</h2>
    
    <form on:submit|preventDefault={handleCreate}>
      <label>
        Project Name
        <input 
          type="text" 
          bind:value={name}
          placeholder="My Amazing Film"
          maxlength="100"
          required
        />
      </label>
      
      <label>
        Quality Tier
        <select bind:value={quality}>
          <option value="draft">Draft (Fast, Lower Quality)</option>
          <option value="standard">Standard (Balanced)</option>
          <option value="premium">Premium (Best Quality)</option>
        </select>
      </label>
      
      {#if error}
        <div class="error">{error}</div>
      {/if}
      
      <div class="actions">
        <button type="button" on:click={() => dispatch('close')}>
          Cancel
        </button>
        <button type="submit" disabled={creating}>
          {creating ? 'Creating...' : 'Create Project'}
        </button>
      </div>
    </form>
  </div>
</div>
```

## Dependencies
- API client setup (STORY-011)
- Projects API endpoints (STORY-004)
- SvelteKit app setup (STORY-007)

## Testing Criteria
- [ ] Projects load and display correctly
- [ ] Search filters projects in real-time
- [ ] Sort options work as expected
- [ ] View toggle switches between grid/list
- [ ] Create project modal validates input
- [ ] Navigation to project page works
- [ ] Error states display appropriately

## Definition of Done
- [ ] Gallery view implemented with both grid and list modes
- [ ] Search and sort functionality working
- [ ] Create project flow complete
- [ ] Loading and error states handled
- [ ] Responsive design verified on different screens
- [ ] Component tests written

## Story Links
- **Depends On**: STORY-004-file-management-api, STORY-007-sveltekit-application-setup, STORY-011-api-client-setup
- **Blocks**: User navigation to project workspace
- **Related PRD**: PRD-001-web-platform-foundation