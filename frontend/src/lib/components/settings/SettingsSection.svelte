<script lang="ts">
  import ProjectSettings from './ProjectSettings.svelte';
  import WorkspaceSettings from './WorkspaceSettings.svelte';
  import SystemInfo from './SystemInfo.svelte';

  export let section: string;

  let hasChanges = false;
</script>

<div class="settings-section">
  {#if section === 'general'}
    <h2>General Settings</h2>
    <div class="setting-group">
      <label>
        <span>Theme</span>
        <select>
          <option>Light</option>
          <option>Dark</option>
          <option>System</option>
        </select>
      </label>
    </div>
    <div class="setting-group">
      <label>
        <span>Language</span>
        <select>
          <option>English</option>
          <option>Spanish</option>
          <option>French</option>
          <option>German</option>
        </select>
      </label>
    </div>
  {:else if section === 'project'}
    <ProjectSettings bind:hasChanges />
  {:else if section === 'quality'}
    <h2>Quality Presets</h2>
    <div class="quality-presets">
      <div class="preset-card">
        <h3>Low (Draft)</h3>
        <p>Fast iteration and preview</p>
        <ul>
          <li>Resolution: 1280×720</li>
          <li>VRAM: 12GB</li>
          <li>Generation: Fast</li>
        </ul>
      </div>
      <div class="preset-card">
        <h3>Standard</h3>
        <p>Production quality</p>
        <ul>
          <li>Resolution: 1920×1080</li>
          <li>VRAM: 16GB</li>
          <li>Generation: Balanced</li>
        </ul>
      </div>
      <div class="preset-card">
        <h3>High (Cinematic)</h3>
        <p>Final renders</p>
        <ul>
          <li>Resolution: 3840×2160</li>
          <li>VRAM: 24GB</li>
          <li>Generation: High Quality</li>
        </ul>
      </div>
    </div>
  {:else if section === 'workspace'}
    <WorkspaceSettings bind:hasChanges />
  {:else if section === 'advanced' || section === 'system'}
    <SystemInfo />
  {/if}
</div>

<style>
  .settings-section h2 {
    margin: 0 0 24px 0;
    font-size: 20px;
    font-weight: 600;
  }

  .setting-group {
    margin-bottom: 20px;
  }

  .setting-group label {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .setting-group label span {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .setting-group input,
  .setting-group select {
    padding: 8px 12px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 14px;
  }

  .setting-group input:focus,
  .setting-group select:focus {
    outline: none;
    border-color: var(--color-primary);
  }

  .setting-group input[type='checkbox'] {
    width: auto;
  }

  .quality-presets {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
  }

  .preset-card {
    padding: 1.5rem;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: var(--bg-secondary);
  }

  .preset-card h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .preset-card p {
    margin: 0 0 1rem 0;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .preset-card ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .preset-card li {
    padding: 0.25rem 0;
    font-size: 0.875rem;
    color: var(--text-muted);
  }
</style>
