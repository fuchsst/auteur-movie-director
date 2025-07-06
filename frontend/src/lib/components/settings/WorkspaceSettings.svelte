<script lang="ts">
  import { onMount } from 'svelte';
  import { workspaceApi, type WorkspaceConfig } from '$lib/api/workspace';

  export let hasChanges = false;

  let config: WorkspaceConfig = {
    root_path: '',
    projects_count: 0,
    available_space_gb: 0,
    enforced_structure: [],
    narrative_structures: []
  };

  let editableConfig = {
    defaultQuality: 'standard',
    enableGitLFS: true,
    autoSaveInterval: 5
  };

  let originalConfig: typeof editableConfig | null = null;
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    await loadWorkspaceConfig();
  });

  async function loadWorkspaceConfig() {
    try {
      loading = true;
      error = null;

      const response = await workspaceApi.getConfig();
      config = response;

      // TODO: Load editable config from backend when endpoints are available
      editableConfig = {
        defaultQuality: 'standard',
        enableGitLFS: true,
        autoSaveInterval: 5
      };

      originalConfig = { ...editableConfig };
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load workspace config';
    } finally {
      loading = false;
    }
  }

  $: hasChanges =
    originalConfig !== null && JSON.stringify(editableConfig) !== JSON.stringify(originalConfig);

  function handleChange() {
    hasChanges = true;
  }

  async function saveSettings() {
    try {
      // TODO: Implement save when backend endpoint is available
      console.log('Saving workspace settings:', editableConfig);

      originalConfig = { ...editableConfig };
      hasChanges = false;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to save settings';
    }
  }

  function cancelChanges() {
    if (originalConfig) {
      editableConfig = { ...originalConfig };
      hasChanges = false;
    }
  }

  function formatBytes(bytes: number): string {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  }
</script>

<div class="workspace-settings">
  <h2>Workspace Settings</h2>

  {#if loading}
    <p>Loading workspace configuration...</p>
  {:else if error}
    <div class="error">{error}</div>
  {:else}
    <div class="info-section">
      <h3>Workspace Information</h3>

      <div class="info-grid">
        <div class="info-item">
          <label>Workspace Root</label>
          <code>{config.root_path}</code>
        </div>

        <div class="info-item">
          <label>Total Projects</label>
          <span>{config.projects_count}</span>
        </div>

        <div class="info-item">
          <label>Available Space</label>
          <span>{config.available_space_gb.toFixed(2)} GB</span>
        </div>
      </div>

      <div class="info-item full-width">
        <label>Required Project Structure</label>
        <ul class="structure-list">
          {#each config.enforced_structure as dir}
            <li><code>{dir}</code></li>
          {/each}
        </ul>
      </div>
    </div>

    <div class="settings-section">
      <h3>Preferences</h3>

      <div class="setting-group">
        <label for="default-quality">Default Quality for New Projects</label>
        <select
          id="default-quality"
          bind:value={editableConfig.defaultQuality}
          on:change={handleChange}
        >
          <option value="low">Low (Draft)</option>
          <option value="standard">Standard</option>
          <option value="high">High (Cinematic)</option>
        </select>
        <small>This setting will be used for all new projects</small>
      </div>

      <div class="setting-group">
        <label class="checkbox-label">
          <input
            type="checkbox"
            bind:checked={editableConfig.enableGitLFS}
            on:change={handleChange}
          />
          <span>Enable Git LFS for new projects</span>
        </label>
        <small>Recommended for managing large media files efficiently</small>
      </div>

      <div class="setting-group">
        <label for="autosave">Auto-save Interval (minutes)</label>
        <input
          id="autosave"
          type="number"
          bind:value={editableConfig.autoSaveInterval}
          min="1"
          max="60"
          on:change={handleChange}
        />
        <small>How often to automatically save project changes</small>
      </div>
    </div>

    {#if hasChanges}
      <div class="settings-actions">
        <button class="btn-primary" on:click={saveSettings}>Save Changes</button>
        <button class="btn-secondary" on:click={cancelChanges}>Cancel</button>
      </div>
    {/if}
  {/if}
</div>

<style>
  .workspace-settings {
    max-width: 800px;
  }

  h2 {
    margin: 0 0 2rem 0;
    font-size: 1.5rem;
    font-weight: 600;
  }

  h3 {
    margin: 2rem 0 1rem 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .error {
    padding: 1rem;
    margin-bottom: 1rem;
    background: var(--color-error-bg);
    color: var(--color-error);
    border: 1px solid var(--color-error);
    border-radius: 4px;
  }

  .info-section {
    margin-bottom: 3rem;
  }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .info-item.full-width {
    grid-column: 1 / -1;
  }

  .info-item label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .info-item code {
    padding: 0.25rem 0.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-family: var(--font-mono);
    font-size: 0.875rem;
  }

  .info-item span {
    font-size: 1.125rem;
    font-weight: 500;
  }

  .structure-list {
    list-style: none;
    padding: 0;
    margin: 0.5rem 0 0 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.5rem;
  }

  .structure-list li {
    font-size: 0.75rem;
  }

  .setting-group {
    margin-bottom: 1.5rem;
  }

  .setting-group > label:not(.checkbox-label) {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .setting-group input[type='text'],
  .setting-group input[type='number'],
  .setting-group select {
    width: 100%;
    max-width: 300px;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 0.875rem;
  }

  .setting-group input:focus,
  .setting-group select:focus {
    outline: none;
    border-color: var(--color-primary);
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .checkbox-label input[type='checkbox'] {
    width: auto;
    cursor: pointer;
  }

  .checkbox-label span {
    font-weight: 500;
  }

  .setting-group small {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.75rem;
    color: var(--text-muted);
  }

  .settings-actions {
    display: flex;
    gap: 1rem;
    margin-top: 2rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border-color);
  }

  .btn-primary,
  .btn-secondary {
    padding: 0.5rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
  }

  .btn-primary:hover {
    background: var(--color-primary-dark);
  }

  .btn-secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }

  .btn-secondary:hover {
    background: var(--bg-hover);
  }
</style>
