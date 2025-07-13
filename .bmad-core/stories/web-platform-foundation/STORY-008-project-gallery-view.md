# Story: Project Browser Component with File System Integration

**Story ID**: STORY-008  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: ⚠️ Partially Completed (January 2025)  
**Completion Date**: N/A  

## Story Description
As a user, I need a hierarchical project browser in the left panel that shows my workspace/project structure following the enforced numbered directory pattern (01_Assets through 06_Exports), along with an asset browser that respects the file-based project architecture, so that I can navigate my creative content within the Git-versioned project structure and select items to work on in the main view.

## Acceptance Criteria

### Functional Requirements
- [ ] Project Browser displays in upper portion of left panel
- [ ] Shows workspace-level project list with numbered project directories
- [ ] Displays enforced project structure: 01_Assets → 06_Exports
- [ ] Shows Git repository status indicators (clean, modified, untracked)
- [ ] Validates project structure integrity with visual indicators
- [ ] Expand/collapse nodes for numbered directories
- [ ] Display directory-specific icons (Assets, Generated, Takes, etc.)
- [ ] Show active/selected state for current directory/file
- [ ] Asset Browser displays in lower portion of left panel
- [ ] Routes assets to correct numbered directories based on file type
- [ ] Special handling for character assets in 01_Assets/Characters
- [ ] Shows character-specific metadata (description, trigger word, LoRA status)
- [ ] Respects Git LFS tracking for large media files
- [ ] Shows file size with LFS indicator for tracked files
- [ ] Display asset previews/thumbnails with lazy loading
- [ ] Character base face images highlighted with special indicator
- [ ] Drag-and-drop respects directory structure constraints

### Workspace/Project Structure Requirements
- [ ] Respect workspace/project two-tier hierarchy model
- [ ] Display workspace root path from container volume mount (/app/workspace)
- [ ] Show project count and available disk space at workspace level
- [ ] Validate each project has complete numbered directory structure
- [ ] Handle project.json at project root for metadata
- [ ] Support .auteur/ directory for project-specific configs
- [ ] Show visual indicators for missing required directories
- [ ] Enforce directory naming convention (XX_Name format)
- [ ] Display subdirectory structure within numbered directories

### Git Integration Requirements
- [ ] Show Git repository status for each project (clean/modified/untracked)
- [ ] Display Git LFS tracking status for large files (>50MB)
- [ ] Support Git LFS file pointers for preview generation
- [ ] Handle .gitignore patterns for file visibility
- [ ] Show uncommitted changes count per project
- [ ] Display last commit message/author/date on hover
- [ ] Visual indicators for staged vs unstaged changes
- [ ] Warning for untracked large files that should use LFS

### UI/UX Requirements
- [ ] Panel is resizable via parent layout
- [ ] Smooth expand/collapse animations
- [ ] Loading states for async file system operations
- [ ] Empty states for workspace and projects
- [ ] Search functionality respecting directory boundaries
- [ ] Context menus with Git operations (track, untrack, status)
- [ ] Keyboard navigation support
- [ ] Selection syncs with center panel content
- [ ] Visual distinction between workspace and project levels
- [ ] Directory structure violations shown as errors

### Technical Requirements
- [ ] Integrate with ThreePanelLayout from STORY-007
- [ ] Use workspace/project two-tier hierarchy model
- [ ] Respect numbered directory structure as API contract
- [ ] Handle container volume mount paths correctly
- [ ] Implement virtual scrolling for large file lists
- [ ] Lazy load directory contents on expand
- [ ] Store expansion state per project in local storage
- [ ] WebSocket updates for file system changes
- [ ] Integration with file management API endpoints
- [ ] Handle Git status polling for repository state
- [ ] Support file type routing to appropriate directories
- [ ] Implement file size limits based on Git LFS configuration
- [ ] Cache directory structure for performance
- [ ] Handle symbolic links and junction points properly

## Implementation Notes

### Updated Left Panel Component
```svelte
<!-- src/lib/components/layout/LeftPanel.svelte -->
<script lang="ts">
  import ProjectBrowser from '$components/project/ProjectBrowser.svelte';
  import AssetBrowser from '$components/asset/AssetBrowser.svelte';
  
  export let width: number;
  
  let splitPosition = 60; // More space for project browser with structure
</script>

<div class="left-panel" style="width: {width}px">
  <div class="panel-section project-section" style="height: {splitPosition}%">
    <div class="section-header">
      <h2>Workspace</h2>
      <span class="workspace-path">{$workspaceConfig.root_path}</span>
    </div>
    <ProjectBrowser />
  </div>
  
  <div class="divider" />
  
  <div class="panel-section asset-section" style="height: {100 - splitPosition}%">
    <h2>Assets Library</h2>
    <AssetBrowser />
  </div>
</div>

<style>
  .left-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--panel-bg);
    border-right: 1px solid var(--border-color);
  }
  
  .panel-section {
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  .section-header {
    padding: 0.5rem 1rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .section-header h2 {
    font-size: 0.875rem;
    font-weight: 600;
    margin: 0;
  }
  
  .workspace-path {
    font-size: 0.75rem;
    color: var(--text-secondary);
  }
  
  .divider {
    height: 1px;
    background: var(--border-color);
  }
</style>
```

### Updated Project Browser Component with Enhanced Structure
```svelte
<!-- src/lib/components/project/ProjectBrowser.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import TreeNode from './TreeNode.svelte';
  import { projects, loadProjects, selectedItem, workspaceConfig, loadWorkspaceConfig } from '$stores/projects';
  import type { Project, TreeItem, DirectoryNode } from '$types';
  
  let searchQuery = '';
  let loading = true;
  let error: string | null = null;
  
  // Directory structure icons matching generative pipeline
  const DIRECTORY_ICONS = {
    '01_Assets': '📦',
    '02_Source_Creative': '✍️',
    '03_Renders': '🎬',
    '04_Project_Files': '📁',
    '05_Cache': '💾',
    '06_Exports': '📤',
    // Asset subdirectories (aligned with pipeline)
    'Characters': '👤',
    'Styles': '🎨',
    'Locations': '🏞️',
    'Music': '🎵',
    // Character-specific subdirectories
    'base_face.png': '🎭',
    'lora': '🧠',
    'variations': '🎲',
    // Creative subdirectories (aligned with pipeline)
    'Treatments': '📝',
    'Scripts': '📜',
    'Shot_Lists': '📋',
    'Canvas': '🎯',
    // Takes hierarchy (Chapter → Scene → Shot → Take)
    'Chapter': '📖',
    'Scene': '🎬',
    'Shot': '📸',
    // Export subdirectories
    'EDL': '📋',
    'Masters': '💎',
    'Deliverables': '📦'
  };
  
  onMount(async () => {
    try {
      await loadWorkspaceConfig();
      await loadProjects();
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  });
  
  // Convert projects to tree structure with numbered directories
  $: treeData = $projects.map(project => ({
    id: project.id,
    name: project.name,
    type: 'project',
    icon: project.structureValid ? '🎬' : '⚠️',
    path: project.path,
    gitStatus: project.gitStatus,
    structureValid: project.structureValid,
    missingDirs: project.missingDirs,
    uncommittedChanges: project.uncommittedChanges,
    lastCommit: project.lastCommit,
    children: [
      {
        id: `${project.id}-01`,
        name: '01_Assets',
        type: 'directory',
        icon: DIRECTORY_ICONS['01_Assets'],
        exists: !project.missingDirs?.includes('01_Assets'),
        children: [
          { id: `${project.id}-01-characters`, name: 'Characters', type: 'directory', icon: DIRECTORY_ICONS['Characters'] },
          { id: `${project.id}-01-styles`, name: 'Styles', type: 'directory', icon: DIRECTORY_ICONS['Styles'] },
          { id: `${project.id}-01-locations`, name: 'Locations', type: 'directory', icon: DIRECTORY_ICONS['Locations'] },
          { id: `${project.id}-01-music`, name: 'Music', type: 'directory', icon: DIRECTORY_ICONS['Music'] }
        ]
      },
      {
        id: `${project.id}-02`,
        name: '02_Source_Creative',
        type: 'directory',
        icon: DIRECTORY_ICONS['02_Source_Creative'],
        exists: !project.missingDirs?.includes('02_Source_Creative'),
        children: [
          { id: `${project.id}-02-treatments`, name: 'Treatments', type: 'directory', icon: DIRECTORY_ICONS['Treatments'] },
          { id: `${project.id}-02-scripts`, name: 'Scripts', type: 'directory', icon: DIRECTORY_ICONS['Scripts'] },
          { id: `${project.id}-02-shot-lists`, name: 'Shot_Lists', type: 'directory', icon: DIRECTORY_ICONS['Shot_Lists'] },
          { id: `${project.id}-02-canvas`, name: 'Canvas', type: 'directory', icon: DIRECTORY_ICONS['Canvas'] }
        ]
      },
      {
        id: `${project.id}-03`,
        name: '03_Renders',
        type: 'directory',
        icon: DIRECTORY_ICONS['03_Renders'],
        exists: !project.missingDirs?.includes('03_Renders'),
        narrative: project.narrative,  // Pass narrative structure info
        children: project.narrative?.chapters?.map((chapter, idx) => ({
          id: `${project.id}-03-ch${idx + 1}`,
          name: `Chapter_${String(idx + 1).padStart(2, '0')}`,
          type: 'directory',
          icon: DIRECTORY_ICONS['Chapter'],
          children: [] // Scenes loaded on demand
        })) || []
      },
      {
        id: `${project.id}-04`,
        name: '04_Project_Files',
        type: 'directory',
        icon: DIRECTORY_ICONS['04_Project_Files'],
        exists: !project.missingDirs?.includes('04_Project_Files')
      },
      {
        id: `${project.id}-05`,
        name: '05_Cache',
        type: 'directory',
        icon: DIRECTORY_ICONS['05_Cache'],
        exists: !project.missingDirs?.includes('05_Cache')
      },
      {
        id: `${project.id}-06`,
        name: '06_Exports',
        type: 'directory',
        icon: DIRECTORY_ICONS['06_Exports'],
        exists: !project.missingDirs?.includes('06_Exports'),
        children: [
          { id: `${project.id}-06-edl`, name: 'EDL', type: 'directory', icon: DIRECTORY_ICONS['EDL'] },
          { id: `${project.id}-06-masters`, name: 'Masters', type: 'directory', icon: DIRECTORY_ICONS['Masters'] },
          { id: `${project.id}-06-deliverables`, name: 'Deliverables', type: 'directory', icon: DIRECTORY_ICONS['Deliverables'] }
        ]
      },
      {
        id: `${project.id}-auteur`,
        name: '.auteur',
        type: 'directory',
        icon: '⚙️',
        hidden: true
      }
    ]
  }));
  
  function handleSelect(item: TreeItem) {
    selectedItem.set(item);
  }
  
  function getGitStatusClass(status: string) {
    switch(status) {
      case 'clean': return 'git-clean';
      case 'modified': return 'git-modified';
      case 'untracked': return 'git-untracked';
      default: return '';
    }
  }
  
  function formatDiskSpace(bytes: number): string {
    const gb = bytes / (1024 * 1024 * 1024);
    return `${gb.toFixed(1)} GB`;
  }
</script>

<div class="project-browser">
  <div class="workspace-header">
    <h3>Workspace</h3>
    <div class="workspace-info">
      <span class="path" title={$workspaceConfig.root_path}>
        {$workspaceConfig.root_path || '/app/workspace'}
      </span>
      <span class="stats">
        {$projects.length} projects • {formatDiskSpace($workspaceConfig.available_space)} free
      </span>
    </div>
  </div>
  
  <div class="browser-toolbar">
    <input 
      type="search"
      placeholder="Search projects..."
      bind:value={searchQuery}
      class="search-input"
    />
    <button class="new-project" title="Create New Project">
      +
    </button>
  </div>
  
  <div class="browser-content">
    {#if loading}
      <div class="loading">Loading workspace...</div>
    {:else if error}
      <div class="error">
        <p>Error loading workspace:</p>
        <code>{error}</code>
      </div>
    {:else if !$workspaceConfig.volume_mounted}
      <div class="error">
        <p>Workspace volume not mounted</p>
        <code>Expected: /app/workspace</code>
      </div>
    {:else if treeData.length === 0}
      <div class="empty">
        <p>No projects in workspace</p>
        <button class="create-first">Create First Project</button>
      </div>
    {:else}
      <div class="tree">
        {#each treeData as node (node.id)}
          <TreeNode 
            {node} 
            level={0}
            on:select={() => handleSelect(node)}
            on:contextmenu={(e) => showProjectMenu(e, node)}
          />
        {/each}
      </div>
    {/if}
  </div>
  
  {#if $workspaceConfig.git_available === false}
    <div class="warning-bar">
      Git not available - version control disabled
    </div>
  {/if}
</div>

<style>
  .project-browser {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .browser-toolbar {
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .search-input {
    flex: 1;
    padding: 0.25rem 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.875rem;
  }
  
  .new-project {
    width: 28px;
    height: 28px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: transparent;
    cursor: pointer;
    font-size: 1.2rem;
    line-height: 1;
  }
  
  .browser-content {
    flex: 1;
    overflow-y: auto;
  }
  
  .tree {
    padding: 0.5rem 0;
  }
  
  .empty {
    padding: 2rem;
    text-align: center;
    color: var(--text-secondary);
  }
  
  .create-first {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: var(--primary-bg);
    border: 1px solid var(--primary-color);
    border-radius: 4px;
    cursor: pointer;
  }
  
  .workspace-header {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-color);
    background: var(--secondary-bg);
  }
  
  .workspace-header h3 {
    margin: 0 0 0.25rem 0;
    font-size: 0.875rem;
    font-weight: 600;
  }
  
  .workspace-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }
  
  .workspace-info .path {
    font-size: 0.7rem;
    color: var(--text-secondary);
    font-family: monospace;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .workspace-info .stats {
    font-size: 0.7rem;
    color: var(--text-secondary);
  }
  
  .warning-bar {
    padding: 0.5rem 1rem;
    background: var(--warning-bg);
    color: var(--warning-color);
    font-size: 0.75rem;
    border-top: 1px solid var(--warning-color);
  }
  
  /* Git status indicators */
  :global(.git-clean) {
    color: var(--success-color);
  }
  
  :global(.git-modified) {
    color: var(--warning-color);
  }
  
  :global(.git-untracked) {
    color: var(--error-color);
  }
  
  /* Structure validation indicators */
  :global(.structure-invalid) {
    opacity: 0.7;
  }
  
  :global(.structure-invalid::after) {
    content: ' ⚠️';
  }
  
  :global(.directory-missing) {
    text-decoration: line-through;
    opacity: 0.5;
  }
</style>
```

### Enhanced Projects Store with Full Workspace Integration
```typescript
// src/lib/stores/projects.ts
import { writable, derived } from 'svelte/store';
import { api } from '$lib/api';
import type { Project, WorkspaceConfig, ProjectStructure, GitStatus } from '$types';

export const projects = writable<Project[]>([]);
export const projectsLoading = writable(false);
export const projectsError = writable<string | null>(null);
export const selectedProject = writable<Project | null>(null);
export const selectedItem = writable<TreeItem | null>(null);

// Workspace configuration store with container mount awareness
export const workspaceConfig = writable<WorkspaceConfig>({
  root_path: '/app/workspace',  // Container mount path
  total_size: 0,
  project_count: 0,
  available_space: 0,
  volume_mounted: false,
  git_available: false,
  lfs_available: false,
  lfs_threshold: 50 * 1024 * 1024,  // 50MB threshold for LFS
  structure_version: '1.0',
  required_directories: [
    '01_Assets',
    '02_Generated',
    '03_Takes',
    '04_Previews',
    '05_Production',
    '06_Exports'
  ]
});

export async function loadWorkspaceConfig() {
  try {
    const response = await api.get('/api/v1/workspace/config');
    workspaceConfig.set(response.data);
  } catch (error) {
    console.error('Failed to load workspace config:', error);
    // Set defaults if API fails
    workspaceConfig.update(config => ({
      ...config,
      volume_mounted: false
    }));
  }
}

export async function loadProjects() {
  projectsLoading.set(true);
  projectsError.set(null);
  
  try {
    const response = await api.get('/api/v1/projects');
    const projectsWithStatus = await Promise.all(
      response.data.map(async (project: Project) => {
        // Get Git status and structure validation in parallel
        const [gitStatus, structure, lastCommit] = await Promise.all([
          api.get(`/api/v1/projects/${project.id}/git/status`),
          api.get(`/api/v1/projects/${project.id}/structure`),
          api.get(`/api/v1/projects/${project.id}/git/log?limit=1`)
        ]);
        
        return {
          ...project,
          gitStatus: gitStatus.data.status,
          uncommittedChanges: gitStatus.data.changes_count,
          untrackedLargeFiles: gitStatus.data.untracked_large_files,
          structureValid: structure.data.is_valid,
          missingDirs: structure.data.missing_dirs,
          lastCommit: lastCommit.data[0] || null
        };
      })
    );
    
    projects.set(projectsWithStatus);
  } catch (error) {
    projectsError.set(error.message);
    throw error;
  } finally {
    projectsLoading.set(false);
  }
}

export async function createProject(data: CreateProjectData) {
  // Ensure the project follows the numbered directory structure
  const response = await api.post('/api/v1/projects', {
    ...data,
    init_git: true,
    use_lfs: true,
    create_structure: true  // Ensure all directories are created
  });
  
  const newProject = response.data;
  
  // Validate structure immediately after creation
  const structure = await api.get(`/api/v1/projects/${newProject.id}/structure`);
  if (!structure.data.is_valid) {
    console.error('Project structure validation failed:', structure.data.missing_dirs);
    // Attempt to fix structure
    await api.post(`/api/v1/projects/${newProject.id}/structure/repair`);
  }
  
  // Initialize Git LFS for the project
  await api.post(`/api/v1/projects/${newProject.id}/git/lfs/init`);
  
  projects.update(p => [...p, newProject]);
  return newProject;
}

export async function deleteProject(id: string) {
  // Confirm deletion since this removes Git repository
  if (!confirm('This will permanently delete the project and its Git repository. Continue?')) {
    return;
  }
  
  await api.delete(`/api/v1/projects/${id}`);
  projects.update(p => p.filter(project => project.id !== id));
}

export async function validateProjectStructure(projectId: string) {
  const response = await api.get(`/api/v1/projects/${projectId}/structure`);
  return response.data;
}

export async function repairProjectStructure(projectId: string) {
  const response = await api.post(`/api/v1/projects/${projectId}/structure/repair`);
  if (response.data.success) {
    await loadProjects(); // Reload to update status
  }
  return response.data;
}

// WebSocket subscription for real-time updates
export function subscribeToProjectUpdates(projectId: string) {
  const ws = new WebSocket(`ws://localhost:8000/api/v1/projects/${projectId}/ws`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'file_change' || data.type === 'git_status_change') {
      // Update specific project
      projects.update(projectList => 
        projectList.map(p => p.id === projectId ? { ...p, ...data.project } : p)
      );
    }
  };
  
  return () => ws.close();
}

// Derived stores
export const projectCount = derived(projects, $projects => $projects.length);

export const projectsWithIssues = derived(projects, $projects => 
  $projects.filter(p => !p.structureValid || p.gitStatus !== 'clean' || p.untrackedLargeFiles?.length > 0)
);

export const selectedProjectPath = derived(
  [selectedProject, workspaceConfig], 
  ([$selectedProject, $workspaceConfig]) => {
    if (!$selectedProject) return null;
    return `${$workspaceConfig.root_path}/${$selectedProject.name}`;
  }
);

export const workspaceHealth = derived(
  [workspaceConfig, projects],
  ([$workspaceConfig, $projects]) => ({
    volumeMounted: $workspaceConfig.volume_mounted,
    gitAvailable: $workspaceConfig.git_available,
    lfsAvailable: $workspaceConfig.lfs_available,
    spaceAvailable: $workspaceConfig.available_space > 1024 * 1024 * 1024, // > 1GB
    projectsValid: $projects.every(p => p.structureValid),
    totalIssues: $projects.reduce((sum, p) => 
      sum + (p.structureValid ? 0 : 1) + (p.gitStatus === 'clean' ? 0 : 1), 0
    )
  })
);
```

### Enhanced Asset Browser with Git LFS and Preview Support
```svelte
<!-- src/lib/components/asset/AssetBrowser.svelte -->
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { selectedProject, selectedProjectPath, workspaceConfig } from '$stores/projects';
  import { api } from '$lib/api';
  import type { Asset, DirectoryType } from '$types';
  
  let selectedDirectory: DirectoryType = '01_Assets';
  let selectedSubdir: string | null = null;
  let searchQuery = '';
  let assets: Asset[] = [];
  let loading = false;
  let uploadProgress = 0;
  let wsConnection: WebSocket | null = null;
  
  // Enhanced directory mapping with file type associations
  const ASSET_DIRECTORIES = {
    '01_Assets': {
      subdirs: ['Characters', 'Styles', 'Locations', 'Music', 'Scripts'],
      accepts: ['text', 'json', 'lora', 'style', 'audio', 'image'],
      special: {
        'Characters': {
          structure: ['base_face.png', 'lora/', 'variations/'],
          metadata: true
        }
      }
    },
    '02_Generated': {
      subdirs: ['Images', 'Videos', 'Audio', 'Metadata'],
      accepts: ['image', 'video', 'audio', 'json']
    },
    '03_Takes': {
      subdirs: [],
      accepts: ['json', 'take']
    },
    '04_Previews': {
      subdirs: ['Dailies', 'Rough_Cuts'],
      accepts: ['video', 'image']
    },
    '05_Production': {
      subdirs: ['Scenes', 'Shots', 'Timelines'],
      accepts: ['json', 'edl', 'timeline']
    },
    '06_Exports': {
      subdirs: ['EDL', 'Masters', 'Deliverables'],
      accepts: ['video', 'edl', 'zip']
    }
  };
  
  const DIRECTORY_ICONS = {
    '01_Assets': '📦',
    '02_Generated': '🤖',
    '03_Takes': '🎬',
    '04_Previews': '👁️',
    '05_Production': '🎭',
    '06_Exports': '📤'
  };
  
  const FILE_TYPE_ICONS = {
    'image': '🖼️',
    'video': '🎥',
    'audio': '🎵',
    'script': '📝',
    'json': '📊',
    'lora': '👤',
    'style': '🎨',
    'environment': '🏞️',
    'take': '🎬',
    'edl': '📋',
    'timeline': '⏱️'
  };
  
  // Load assets when project or directory changes
  $: if ($selectedProject && selectedDirectory) {
    loadAssets();
  }
  
  // Subscribe to WebSocket for real-time updates
  $: if ($selectedProject && !wsConnection) {
    connectWebSocket();
  }
  
  onDestroy(() => {
    if (wsConnection) {
      wsConnection.close();
    }
  });
  
  function connectWebSocket() {
    if (!$selectedProject) return;
    
    wsConnection = new WebSocket(`ws://localhost:8000/api/v1/projects/${$selectedProject.id}/assets/ws`);
    
    wsConnection.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'asset_added' || data.type === 'asset_removed') {
        loadAssets(); // Reload assets on changes
      }
    };
  }
  
  async function loadAssets() {
    if (!$selectedProject) return;
    
    loading = true;
    try {
      const params: any = { directory: selectedDirectory };
      if (selectedSubdir) {
        params.subdirectory = selectedSubdir;
      }
      
      const response = await api.get(`/api/v1/projects/${$selectedProject.id}/assets`, { params });
      
      // If viewing Characters directory, also load character metadata
      let characterData = {};
      if (selectedDirectory === '01_Assets' && selectedSubdir === 'Characters') {
        try {
          const charResponse = await api.get(`/api/v1/projects/${$selectedProject.id}/characters`);
          characterData = charResponse.data.reduce((acc, char) => {
            acc[char.name] = char;
            return acc;
          }, {});
        } catch (error) {
          console.error('Failed to load character metadata:', error);
        }
      }
      
      assets = await Promise.all(response.data.map(async (file: any) => {
        const asset = {
          ...file,
          isLFS: file.git_lfs_tracked || file.size > $workspaceConfig.lfs_threshold,
          lfsPointer: file.git_lfs_pointer,
          directory: selectedDirectory,
          subdirectory: selectedSubdir,
          projectId: $selectedProject.id,
          fileType: getFileType(file.name, file.mime_type)
        };
        
        // Add character metadata if this is a character asset
        if (selectedSubdir === 'Characters' && file.path) {
          const charName = file.path.split('/')[0];
          if (characterData[charName]) {
            asset.characterMeta = characterData[charName];
            asset.isBaseFace = file.name === 'base_face.png';
            asset.isLoRA = file.path.includes('/lora/');
            asset.isVariation = file.path.includes('/variations/');
          }
        }
        
        // Load preview for supported file types
        if (asset.fileType === 'image' && !asset.isLFS) {
          asset.preview = await loadPreview(asset);
        }
        
        return asset;
      }));
    } catch (error) {
      console.error('Failed to load assets:', error);
      assets = [];
    } finally {
      loading = false;
    }
  }
  
  async function loadPreview(asset: Asset): Promise<string | null> {
    try {
      const response = await api.get(
        `/api/v1/projects/${asset.projectId}/assets/${asset.id}/preview`,
        { responseType: 'blob' }
      );
      return URL.createObjectURL(response.data);
    } catch {
      return null;
    }
  }
  
  function getFileType(filename: string, mimeType?: string): string {
    const ext = filename.split('.').pop()?.toLowerCase();
    
    if (mimeType?.startsWith('image/')) return 'image';
    if (mimeType?.startsWith('video/')) return 'video';
    if (mimeType?.startsWith('audio/')) return 'audio';
    
    const typeMap: Record<string, string> = {
      'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'webp': 'image',
      'mp4': 'video', 'mov': 'video', 'avi': 'video',
      'mp3': 'audio', 'wav': 'audio', 'ogg': 'audio',
      'json': 'json', 'txt': 'script', 'md': 'script',
      'safetensors': 'lora', 'ckpt': 'lora',
      'style': 'style', 'env': 'environment',
      'take': 'take', 'edl': 'edl', 'timeline': 'timeline'
    };
    
    return typeMap[ext || ''] || 'file';
  }
  
  $: filteredAssets = assets.filter(asset => {
    const matchesSearch = asset.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });
  
  function handleDragStart(event: DragEvent, asset: Asset) {
    event.dataTransfer?.setData('asset', JSON.stringify({
      ...asset,
      sourcePath: `${$selectedProjectPath}/${selectedDirectory}/${asset.path}`
    }));
  }
  
  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  }
  
  async function handleUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || !$selectedProject) return;
    
    // Check file types against directory restrictions
    const acceptedTypes = ASSET_DIRECTORIES[selectedDirectory].accepts;
    
    const formData = new FormData();
    let largeFileWarning = false;
    
    for (const file of input.files) {
      // Warn about large files that will use LFS
      if (file.size > $workspaceConfig.lfs_threshold) {
        largeFileWarning = true;
      }
      formData.append('files', file);
    }
    
    if (largeFileWarning && !confirm('Large files will be tracked with Git LFS. Continue?')) {
      return;
    }
    
    formData.append('directory', selectedDirectory);
    if (selectedSubdir) {
      formData.append('subdirectory', selectedSubdir);
    }
    
    try {
      // Track upload progress
      await api.post(`/api/v1/projects/${$selectedProject.id}/assets`, formData, {
        onUploadProgress: (progressEvent) => {
          uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        }
      });
      
      await loadAssets(); // Reload to show new files
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed: ' + error.message);
    } finally {
      uploadProgress = 0;
      input.value = ''; // Clear input
    }
  }
</script>

<div class="asset-browser">
  <div class="browser-toolbar">
    <input 
      type="search"
      placeholder="Search in {selectedDirectory}..."
      bind:value={searchQuery}
      class="search-input"
      disabled={!$selectedProject}
    />
    <label class="upload-button" class:disabled={!$selectedProject}>
      <input 
        type="file" 
        multiple 
        on:change={handleUpload}
        disabled={!$selectedProject}
      />
      📤
    </label>
  </div>
  
  {#if uploadProgress > 0}
    <div class="upload-progress">
      <div class="progress-bar" style="width: {uploadProgress}%"></div>
      <span class="progress-text">Uploading... {uploadProgress}%</span>
    </div>
  {/if}
  
  {#if $selectedProject}
    <div class="directories">
      {#each Object.keys(ASSET_DIRECTORIES) as dir}
        <button 
          class="directory"
          class:active={selectedDirectory === dir}
          on:click={() => { selectedDirectory = dir; selectedSubdir = null; }}
        >
          <span class="icon">{DIRECTORY_ICONS[dir]}</span>
          <span class="name">{dir}</span>
        </button>
      {/each}
    </div>
    
    {#if ASSET_DIRECTORIES[selectedDirectory].subdirs.length > 0}
      <div class="subdirectories">
        <button 
          class="subdirectory"
          class:active={selectedSubdir === null}
          on:click={() => selectedSubdir = null}
        >
          All
        </button>
        {#each ASSET_DIRECTORIES[selectedDirectory].subdirs as subdir}
          <button 
            class="subdirectory"
            class:active={selectedSubdir === subdir}
            on:click={() => selectedSubdir = subdir}
          >
            {subdir}
          </button>
        {/each}
      </div>
    {/if}
    
    <div class="assets-grid">
      {#if loading}
        <div class="loading">Loading assets...</div>
      {:else if filteredAssets.length === 0}
        <div class="empty">
          No assets in {selectedDirectory}{selectedSubdir ? `/${selectedSubdir}` : ''}
          <p class="hint">Drag files here or use the upload button</p>
        </div>
      {:else}
        {#each filteredAssets as asset (asset.id)}
          <div 
            class="asset-item"
            class:lfs-tracked={asset.isLFS}
            draggable="true"
            on:dragstart={(e) => handleDragStart(e, asset)}
            title="{asset.name} ({formatFileSize(asset.size)}){asset.isLFS ? ' - Git LFS' : ''}"
          >
            {#if asset.preview}
              <img src={asset.preview} alt={asset.name} loading="lazy" />
            {:else}
              <div class="placeholder">
                <span class="icon">{FILE_TYPE_ICONS[asset.fileType] || '📄'}</span>
              </div>
            {/if}
            <span class="name">{asset.name}</span>
            <span class="size">{formatFileSize(asset.size)}</span>
            {#if asset.isLFS}
              <span class="lfs-badge" title="Tracked by Git LFS">LFS</span>
            {/if}
            {#if asset.git_status === 'modified'}
              <span class="git-badge modified" title="Modified">M</span>
            {:else if asset.git_status === 'untracked'}
              <span class="git-badge untracked" title="Untracked">U</span>
            {/if}
            {#if asset.isBaseFace}
              <span class="character-badge base-face" title="Character Base Face">👤</span>
            {:else if asset.isLoRA}
              <span class="character-badge lora" title="LoRA Model">🧠</span>
            {:else if asset.isVariation}
              <span class="character-badge variation" title="Character Variation">🎲</span>
            {/if}
            {#if asset.characterMeta?.loraTrainingStatus === 'training'}
              <span class="character-badge training" title="LoRA Training">⏳</span>
            {/if}
          </div>
        {/each}
      {/if}
    </div>
  {:else}
    <div class="no-project">
      <p>Select a project to browse assets</p>
    </div>
  {/if}
</div>

<style>
  .asset-browser {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .browser-toolbar {
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .upload-button {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
  }
  
  .upload-button input {
    display: none;
  }
  
  .upload-button.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .directories {
    display: flex;
    flex-wrap: wrap;
    padding: 0.5rem;
    gap: 0.25rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .directory {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: transparent;
    cursor: pointer;
    font-size: 0.75rem;
  }
  
  .directory.active {
    background: var(--primary-bg);
    border-color: var(--primary-color);
  }
  
  .subdirectories {
    display: flex;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .subdirectory {
    padding: 0.125rem 0.5rem;
    font-size: 0.7rem;
    color: var(--text-secondary);
    background: transparent;
    border: 1px solid transparent;
    border-radius: 2px;
    cursor: pointer;
  }
  
  .subdirectory:hover {
    background: var(--hover-bg);
  }
  
  .subdirectory.active {
    background: var(--primary-bg);
    border-color: var(--primary-color);
    color: var(--primary-color);
  }
  
  .upload-progress {
    position: relative;
    height: 3px;
    background: var(--secondary-bg);
    overflow: hidden;
  }
  
  .progress-bar {
    position: absolute;
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s ease;
  }
  
  .progress-text {
    position: absolute;
    top: 4px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.7rem;
    color: var(--text-secondary);
  }
  
  .assets-grid {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 0.5rem;
    padding: 0.5rem;
    overflow-y: auto;
  }
  
  .asset-item {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: grab;
    transition: all 0.2s ease;
  }
  
  .asset-item:hover {
    background: var(--hover-bg);
    transform: translateY(-2px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .asset-item.lfs-tracked {
    border-color: var(--warning-color);
  }
  
  .asset-item img {
    width: 60px;
    height: 60px;
    object-fit: cover;
    border-radius: 4px;
  }
  
  .placeholder {
    width: 60px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--secondary-bg);
    border-radius: 4px;
  }
  
  .placeholder .icon {
    font-size: 1.5rem;
  }
  
  .name {
    margin-top: 0.25rem;
    font-size: 0.7rem;
    text-align: center;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
  }
  
  .size {
    font-size: 0.65rem;
    color: var(--text-secondary);
  }
  
  .lfs-badge {
    position: absolute;
    top: 2px;
    right: 2px;
    background: var(--warning-bg);
    color: var(--warning-color);
    font-size: 0.6rem;
    padding: 1px 3px;
    border-radius: 2px;
    font-weight: bold;
  }
  
  .git-badge {
    position: absolute;
    top: 2px;
    left: 2px;
    font-size: 0.6rem;
    padding: 1px 3px;
    border-radius: 2px;
    font-weight: bold;
  }
  
  .git-badge.modified {
    background: var(--warning-bg);
    color: var(--warning-color);
  }
  
  .git-badge.untracked {
    background: var(--error-bg);
    color: var(--error-color);
  }
  
  .character-badge {
    position: absolute;
    bottom: 2px;
    right: 2px;
    font-size: 0.6rem;
    padding: 1px 3px;
    border-radius: 2px;
  }
  
  .character-badge.base-face {
    background: var(--primary-bg);
    color: var(--primary-color);
  }
  
  .character-badge.lora {
    background: var(--accent-bg);
    color: var(--accent-color);
  }
  
  .character-badge.variation {
    background: var(--secondary-bg);
    color: var(--text-primary);
  }
  
  .character-badge.training {
    background: var(--warning-bg);
    color: var(--warning-color);
    animation: pulse 1s infinite;
  }
  
  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
  
  .no-project, .empty, .loading {
    padding: 2rem;
    text-align: center;
    color: var(--text-secondary);
  }
  
  .empty .hint {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    opacity: 0.7;
  }
</style>
```

## Dependencies
- API client setup (STORY-011)
- Projects API endpoints (STORY-004)
- SvelteKit app setup (STORY-007)

## Testing Criteria
- [ ] Workspace configuration loads with volume mount status
- [ ] Projects display with Git status indicators
- [ ] Directory structure validation shows missing directories
- [ ] Asset browser respects numbered directory structure
- [ ] Git LFS indicators appear for large files (>50MB)
- [ ] File uploads route to correct directories
- [ ] WebSocket updates reflect file system changes
- [ ] Preview generation works for non-LFS images
- [ ] Subdirectory navigation filters assets correctly
- [ ] Upload progress shows for large files
- [ ] Context menus provide Git operations
- [ ] Search respects directory boundaries
- [ ] Drag-and-drop includes proper source paths
- [ ] Structure repair function fixes missing directories
- [ ] Warning displays when Git/LFS not available
- [ ] Character assets display with metadata (trigger word, LoRA status)
- [ ] Character base face images show special indicator
- [ ] Character variations organized within character folders
- [ ] LoRA training status displays correctly

## Definition of Done
- [ ] Left panel component implemented with Project and Asset browsers
- [ ] Workspace displays root path and available disk space
- [ ] Projects show with enforced numbered directory structure
- [ ] Git repository status indicators working (clean/modified/untracked)
- [ ] Directory structure validation with visual indicators
- [ ] Asset browser routes files to appropriate directories
- [ ] Git LFS tracking indicators for large files
- [ ] WebSocket integration for real-time updates
- [ ] Preview support for images with LFS awareness
- [ ] Subdirectory navigation within numbered directories
- [ ] Upload progress tracking for large files
- [ ] Context menus with Git operations
- [ ] Structure repair functionality for missing directories
- [ ] Container volume mount status displayed
- [ ] Component tests written for all features
- [ ] Character asset special handling implemented
- [ ] Character metadata integration working

## Story Links
- **Depends On**: STORY-004-file-management-api, STORY-007-sveltekit-application-setup, STORY-011-api-client-setup
- **Blocks**: User navigation to project workspace
- **Related PRD**: PRD-001-web-platform-foundation

## Implementation Status

### ✅ Implemented Features (~35%):
- Basic ProjectBrowser component exists in `frontend/src/lib/components/project/ProjectBrowser.svelte`
- Basic AssetBrowser component exists in `frontend/src/lib/components/asset/AssetBrowser.svelte`
- Three-panel layout integration working in main page
- Basic project listing and selection functionality
- Asset categories with file upload support
- Basic search functionality in asset browser

### ⚠️ Partially Implemented (~15%):
- Git status indicators (API exists but not integrated in UI)
- File upload with basic metadata (exists but lacks directory routing)

### ❌ Not Implemented (~50%):
- Workspace-level project list with numbered directory visualization
- Enforced project structure display (01_Assets through 06_Exports)
- Project structure validation with visual error indicators
- Expandable/collapsible tree nodes for directories
- Directory-specific icons for each numbered folder
- Automatic file routing to correct numbered directories
- Character asset special handling with subdirectory organization
- Git LFS tracking indicators for large files (>50MB)
- File size display with LFS badge for tracked files
- Asset preview thumbnails with lazy loading
- Character metadata display (trigger words, LoRA status)
- WebSocket integration for real-time file system updates
- Search functionality respecting directory boundaries
- Drag-and-drop support with proper source paths
- Context menus for Git operations
- Container volume mount status display
- Structure repair functionality for missing directories
- Virtual scrolling for large file lists
- Progressive loading of directory contents
- Local storage for expansion state persistence

### Implementation Notes:
The story specification shows extensive implementation details, but the actual codebase has only basic components:
- ProjectBrowser is simplified without tree structure or Git integration
- AssetBrowser lacks directory routing and Git LFS awareness
- No workspace configuration display or validation
- No real-time WebSocket updates for file changes
- Missing the sophisticated features described in the story