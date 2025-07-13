<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import CanvasView from '../views/CanvasView.svelte';
  import SceneView from '../views/SceneView.svelte';
  import AssetsView from '../views/AssetsView.svelte';
  import GitView from '../views/GitView.svelte';
  import SettingsView from '../views/SettingsView.svelte';
  import TabBar from './TabBar.svelte';
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
      id: 'git',
      label: 'Git',
      icon: '📦',
      component: GitView,
      shortcut: 'Ctrl+4'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: '⚙️',
      component: SettingsView,
      shortcut: 'Ctrl+5'
    }
  ];

  let activeTab = 'canvas';
  let loading = false;

  // Get active tab from URL or store
  $: {
    const urlTab = $page.url.searchParams.get('tab');
    if (urlTab && tabs.find((t) => t.id === urlTab)) {
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
    setTimeout(() => (loading = false), 100);
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
  });

  onDestroy(() => {
    window.removeEventListener('keydown', handleKeydown);
  });

  $: activeTabConfig = tabs.find((t) => t.id === activeTab);
</script>

<div class="main-view-container">
  <TabBar {tabs} {activeTab} on:change={(e) => handleTabChange(e.detail)} />

  <div class="view-content" class:loading>
    {#if loading}
      <div class="loading-overlay">
        <div class="spinner"></div>
      </div>
    {/if}

    {#if activeTabConfig}
      <div class="view-wrapper" data-view={activeTab}>
        <svelte:component this={activeTabConfig.component} {projectId} />
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
    to {
      transform: rotate(360deg);
    }
  }

  .view-wrapper {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
</style>
