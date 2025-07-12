# Story: Main View Tab System

**Story ID**: STORY-016  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 3 (Medium)  
**Priority**: Medium  
**Status**: ✅ Completed

## Story Description
As a user, I need a tabbed interface in the center panel that allows me to switch between different views (Canvas, Scene, Assets, Settings), providing organized access to different aspects of my project while maintaining context and state between tab switches.

## Acceptance Criteria

### Functional Requirements
- [ ] Display tabs for Canvas, Scene, Assets, and Settings views
- [ ] Allow switching between tabs with single click
- [ ] Maintain view state when switching tabs
- [ ] Show active tab with visual indicator
- [ ] Remember last active tab per project
- [ ] Support keyboard navigation (Ctrl+1-4)
- [ ] Show tab-specific actions in header
- [ ] Allow closing optional tabs (future)
- [ ] Support tab overflow with scroll/dropdown
- [ ] Enable/disable tabs based on context

### UI/UX Requirements
- [ ] Clear visual distinction for active tab
- [ ] Smooth transition animations between views
- [ ] Tab icons for quick recognition
- [ ] Hover states for interactive feedback
- [ ] Responsive design for narrow screens
- [ ] Tab reordering via drag-and-drop (future)
- [ ] Context menu on tabs (future)
- [ ] Loading states for tab content

### Technical Requirements
- [ ] Lazy load tab content components
- [ ] Route-based tab navigation
- [ ] Tab state persistence in stores
- [ ] Keyboard shortcut handling
- [ ] Memory optimization for hidden tabs
- [ ] Support for dynamic tab addition
- [ ] Tab-specific URL parameters

## Implementation Notes

### Main View Container Component
```svelte
<!-- src/lib/components/layout/MainViewContainer.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import CanvasView from '../views/CanvasView.svelte';
  import SceneView from '../views/SceneView.svelte';
  import AssetsView from '../views/AssetsView.svelte';
  import SettingsView from '../views/SettingsView.svelte';
  import TabBar from './TabBar.svelte';
  import { projectStore } from '$lib/stores/project';
  import { viewStore } from '$lib/stores/views';
  import type { ViewTab } from '$lib/types';
  
  export let projectId: string;
  
  const tabs: ViewTab[] = [
    {
      id: 'canvas',
      label: 'Canvas',
      icon: '🎨',
      component: CanvasView,
      shortcut: 'Ctrl+1'
    },
    {
      id: 'scene',
      label: 'Scene',
      icon: '🎬',
      component: SceneView,
      shortcut: 'Ctrl+2'
    },
    {
      id: 'assets',
      label: 'Assets',
      icon: '📁',
      component: AssetsView,
      shortcut: 'Ctrl+3'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: '⚙️',
      component: SettingsView,
      shortcut: 'Ctrl+4'
    }
  ];
  
  let activeTab = 'canvas';
  let loading = false;
  
  // Get active tab from URL or store
  $: {
    const urlTab = $page.url.searchParams.get('tab');
    if (urlTab && tabs.find(t => t.id === urlTab)) {
      activeTab = urlTab;
    } else {
      activeTab = $viewStore.activeTab || 'canvas';
    }
  }
  
  // Update store and URL when tab changes
  function handleTabChange(tabId: string) {
    loading = true;
    activeTab = tabId;
    viewStore.setActiveTab(tabId);
    
    // Update URL without navigation
    const url = new URL($page.url);
    url.searchParams.set('tab', tabId);
    goto(url.toString(), { replaceState: true, noScroll: true });
    
    // Simulate loading for lazy components
    setTimeout(() => loading = false, 100);
  }
  
  // Keyboard shortcuts
  function handleKeydown(event: KeyboardEvent) {
    if (event.ctrlKey || event.metaKey) {
      const num = parseInt(event.key);
      if (num >= 1 && num <= tabs.length) {
        event.preventDefault();
        handleTabChange(tabs[num - 1].id);
      }
    }
  }
  
  onMount(() => {
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });
  
  $: activeTabConfig = tabs.find(t => t.id === activeTab);
</script>

<div class="main-view-container">
  <TabBar 
    {tabs} 
    {activeTab} 
    on:change={(e) => handleTabChange(e.detail)}
  />
  
  <div class="view-content" class:loading>
    {#if loading}
      <div class="loading-overlay">
        <div class="spinner"></div>
      </div>
    {/if}
    
    {#if activeTabConfig}
      <div class="view-wrapper" data-view={activeTab}>
        <svelte:component 
          this={activeTabConfig.component} 
          {projectId}
        />
      </div>
    {/if}
  </div>
</div>

<style>
  .main-view-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--bg-primary);
  }
  
  .view-content {
    flex: 1;
    position: relative;
    overflow: hidden;
  }
  
  .view-content.loading {
    opacity: 0.7;
    pointer-events: none;
  }
  
  .loading-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.1);
    z-index: 10;
  }
  
  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-color);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .view-wrapper {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
</style>
```

### Tab Bar Component
```svelte
<!-- src/lib/components/layout/TabBar.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ViewTab } from '$lib/types';
  
  export let tabs: ViewTab[];
  export let activeTab: string;
  
  const dispatch = createEventDispatcher();
  
  function selectTab(tabId: string) {
    if (tabId !== activeTab) {
      dispatch('change', tabId);
    }
  }
</script>

<div class="tab-bar">
  <div class="tabs">
    {#each tabs as tab (tab.id)}
      <button
        class="tab"
        class:active={tab.id === activeTab}
        on:click={() => selectTab(tab.id)}
        title="{tab.label} ({tab.shortcut})"
      >
        <span class="tab-icon">{tab.icon}</span>
        <span class="tab-label">{tab.label}</span>
      </button>
    {/each}
  </div>
  
  <div class="tab-actions">
    <slot name="actions" />
  </div>
</div>

<style>
  .tab-bar {
    display: flex;
    align-items: center;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    height: 40px;
    padding: 0 16px;
  }
  
  .tabs {
    display: flex;
    gap: 4px;
    flex: 1;
  }
  
  .tab {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: transparent;
    border: none;
    border-radius: 4px 4px 0 0;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;
    position: relative;
  }
  
  .tab:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
  
  .tab.active {
    background: var(--bg-primary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-bottom-color: var(--bg-primary);
    margin-bottom: -1px;
  }
  
  .tab-icon {
    font-size: 16px;
  }
  
  .tab-label {
    @media (max-width: 768px) {
      display: none;
    }
  }
  
  .tab-actions {
    display: flex;
    gap: 8px;
  }
</style>
```

### View Components

#### Canvas View (Placeholder)
```svelte
<!-- src/lib/components/views/CanvasView.svelte -->
<script lang="ts">
  export let projectId: string;
  
  // Future: This will contain the node-based canvas
</script>

<div class="canvas-view">
  <div class="canvas-toolbar">
    <button>Add Node</button>
    <button>Zoom In</button>
    <button>Zoom Out</button>
    <button>Fit to Screen</button>
  </div>
  
  <div class="canvas-area">
    <div class="placeholder">
      <h2>Production Canvas</h2>
      <p>Node-based workflow will be implemented here</p>
      <p>Project: {projectId}</p>
    </div>
  </div>
</div>

<style>
  .canvas-view {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .canvas-toolbar {
    padding: 8px 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    gap: 8px;
  }
  
  .canvas-area {
    flex: 1;
    position: relative;
    background: var(--bg-canvas);
    background-image: 
      linear-gradient(var(--grid-color) 1px, transparent 1px),
      linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
    background-size: 20px 20px;
  }
  
  .placeholder {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    color: var(--text-secondary);
  }
</style>
```

#### Scene View
```svelte
<!-- src/lib/components/views/SceneView.svelte -->
<script lang="ts">
  import { projectStore } from '$lib/stores/project';
  import SceneHierarchy from '../scene/SceneHierarchy.svelte';
  import ShotList from '../scene/ShotList.svelte';
  
  export let projectId: string;
  
  $: project = $projectStore.projects.find(p => p.id === projectId);
</script>

<div class="scene-view">
  <div class="scene-header">
    <h2>Scene Management</h2>
    <button>Add Chapter</button>
  </div>
  
  <div class="scene-content">
    <div class="scene-sidebar">
      <SceneHierarchy {project} />
    </div>
    
    <div class="shot-details">
      <ShotList />
    </div>
  </div>
</div>

<style>
  .scene-view {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .scene-header {
    padding: 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .scene-content {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  
  .scene-sidebar {
    width: 300px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    overflow-y: auto;
  }
  
  .shot-details {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
  }
</style>
```

#### Assets View
```svelte
<!-- src/lib/components/views/AssetsView.svelte -->
<script lang="ts">
  import { assetStore } from '$lib/stores/assets';
  import AssetGrid from '../asset/AssetGrid.svelte';
  import AssetFilters from '../asset/AssetFilters.svelte';
  
  export let projectId: string;
  
  let selectedCategory = 'all';
  let searchQuery = '';
  
  $: assets = $assetStore.getProjectAssets(projectId);
  $: filteredAssets = filterAssets(assets, selectedCategory, searchQuery);
  
  function filterAssets(assets, category, query) {
    let filtered = assets;
    
    if (category !== 'all') {
      filtered = filtered.filter(a => a.category === category);
    }
    
    if (query) {
      const q = query.toLowerCase();
      filtered = filtered.filter(a => 
        a.name.toLowerCase().includes(q) ||
        a.metadata?.description?.toLowerCase().includes(q)
      );
    }
    
    return filtered;
  }
</script>

<div class="assets-view">
  <div class="assets-header">
    <h2>Project Assets</h2>
    <div class="header-actions">
      <input 
        type="search" 
        placeholder="Search assets..."
        bind:value={searchQuery}
      />
      <button>Import Assets</button>
    </div>
  </div>
  
  <AssetFilters bind:selectedCategory />
  
  <div class="assets-content">
    <AssetGrid assets={filteredAssets} />
  </div>
</div>

<style>
  .assets-view {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .assets-header {
    padding: 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }
  
  .header-actions input {
    width: 200px;
  }
  
  .assets-content {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
  }
</style>
```

#### Settings View
```svelte
<!-- src/lib/components/views/SettingsView.svelte -->
<script lang="ts">
  import { projectStore } from '$lib/stores/project';
  import { settingsStore } from '$lib/stores/settings';
  import SettingsSection from '../settings/SettingsSection.svelte';
  
  export let projectId: string;
  
  $: project = $projectStore.projects.find(p => p.id === projectId);
  $: settings = $settingsStore;
  
  const settingsSections = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'project', label: 'Project', icon: '📁' },
    { id: 'quality', label: 'Quality', icon: '🎨' },
    { id: 'workspace', label: 'Workspace', icon: '💾' },
    { id: 'advanced', label: 'Advanced', icon: '🔧' }
  ];
  
  let activeSection = 'general';
</script>

<div class="settings-view">
  <div class="settings-sidebar">
    <h3>Settings</h3>
    <nav class="settings-nav">
      {#each settingsSections as section}
        <button
          class="nav-item"
          class:active={section.id === activeSection}
          on:click={() => activeSection = section.id}
        >
          <span class="nav-icon">{section.icon}</span>
          <span class="nav-label">{section.label}</span>
        </button>
      {/each}
    </nav>
  </div>
  
  <div class="settings-content">
    <SettingsSection 
      section={activeSection} 
      {project}
      {settings}
    />
  </div>
</div>

<style>
  .settings-view {
    height: 100%;
    display: flex;
  }
  
  .settings-sidebar {
    width: 200px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    padding: 16px;
  }
  
  .settings-sidebar h3 {
    margin: 0 0 16px 0;
    font-size: 16px;
  }
  
  .settings-nav {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .nav-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: transparent;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    color: var(--text-secondary);
    text-align: left;
    transition: all 0.2s;
  }
  
  .nav-item:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
  
  .nav-item.active {
    background: var(--bg-active);
    color: var(--text-primary);
  }
  
  .nav-icon {
    font-size: 16px;
  }
  
  .nav-label {
    font-size: 13px;
    font-weight: 500;
  }
  
  .settings-content {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
  }
</style>
```

### View Store
```typescript
// src/lib/stores/views.ts
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

interface ViewState {
  activeTab: string;
  tabHistory: string[];
  viewStates: Record<string, any>;
}

function createViewStore() {
  const defaultState: ViewState = {
    activeTab: 'canvas',
    tabHistory: ['canvas'],
    viewStates: {}
  };
  
  // Load from localStorage
  const stored = browser ? localStorage.getItem('viewState') : null;
  const initial = stored ? { ...defaultState, ...JSON.parse(stored) } : defaultState;
  
  const { subscribe, update } = writable<ViewState>(initial);
  
  return {
    subscribe,
    
    setActiveTab(tabId: string) {
      update(state => {
        const newState = {
          ...state,
          activeTab: tabId,
          tabHistory: [...state.tabHistory.slice(-9), tabId]
        };
        
        if (browser) {
          localStorage.setItem('viewState', JSON.stringify(newState));
        }
        
        return newState;
      });
    },
    
    saveViewState(tabId: string, state: any) {
      update(s => ({
        ...s,
        viewStates: {
          ...s.viewStates,
          [tabId]: state
        }
      }));
    },
    
    getViewState(tabId: string) {
      let state: any;
      const unsubscribe = subscribe(s => {
        state = s.viewStates[tabId];
      });
      unsubscribe();
      return state;
    }
  };
}

export const viewStore = createViewStore();
```

### Type Definitions
```typescript
// Add to src/lib/types/index.ts
export interface ViewTab {
  id: string;
  label: string;
  icon: string;
  component: any; // Svelte component
  shortcut?: string;
  closeable?: boolean;
}

export interface ViewState {
  zoom?: number;
  pan?: { x: number; y: number };
  selection?: string[];
  filters?: Record<string, any>;
}
```

## Dependencies
- Tab content components (views)
- View state management
- Keyboard shortcut system
- Route-based navigation

## Testing Criteria
- [ ] All tabs load and display correctly
- [ ] Tab switching maintains state
- [ ] Keyboard shortcuts work (Ctrl+1-4)
- [ ] URL updates reflect active tab
- [ ] Browser back/forward works
- [ ] Tab states persist on reload
- [ ] Responsive design works on mobile
- [ ] Memory usage stays reasonable

## Definition of Done
- [ ] Tab system implemented with all views
- [ ] Keyboard navigation functional
- [ ] State persistence working
- [ ] URL integration complete
- [ ] All view placeholders created
- [ ] Responsive design tested
- [ ] Performance optimized
- [ ] Documentation updated

## Story Links
- **Depends On**: STORY-007 (SvelteKit Setup)
- **Blocks**: Future canvas implementation
- **Related PRD**: PRD-001-web-platform-foundation