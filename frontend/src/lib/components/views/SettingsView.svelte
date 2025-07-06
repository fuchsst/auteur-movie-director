<script lang="ts">
  import { currentProject } from '$lib/stores';
  import SettingsSection from '../settings/SettingsSection.svelte';

  export let projectId: string;

  const settingsSections = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'project', label: 'Project', icon: '📁' },
    { id: 'quality', label: 'Quality', icon: '🎨' },
    { id: 'workspace', label: 'Workspace', icon: '💾' },
    { id: 'system', label: 'System Info', icon: 'ℹ️' }
  ];

  let activeSection = 'general';
  let settings = {}; // Placeholder for settings store
</script>

<div class="settings-view">
  <div class="settings-sidebar">
    <h3>Settings</h3>
    <nav class="settings-nav">
      {#each settingsSections as section}
        <button
          class="nav-item"
          class:active={section.id === activeSection}
          on:click={() => (activeSection = section.id)}
          type="button"
        >
          <span class="nav-icon">{section.icon}</span>
          <span class="nav-label">{section.label}</span>
        </button>
      {/each}
    </nav>
  </div>

  <div class="settings-content">
    <SettingsSection section={activeSection} project={$currentProject} {settings} />
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
    background: var(--bg-active, var(--color-primary-dim));
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
