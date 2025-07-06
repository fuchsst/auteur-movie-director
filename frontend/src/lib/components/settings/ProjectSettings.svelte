<script lang="ts">
  import { currentProject } from '$lib/stores';
  import type { ProjectSettings } from '$lib/types/project';
  import { workspaceApi } from '$lib/api/workspace';

  export let hasChanges = false;

  let settings: ProjectSettings = {
    fps: 24,
    resolution: [1920, 1080],
    aspectRatio: '16:9',
    defaultQuality: 'standard',
    outputFormat: 'mp4'
  };

  let originalSettings: ProjectSettings | null = null;

  const qualityOptions = [
    { value: 'low', label: 'Low (Draft)', description: 'Fast iteration, 12GB VRAM' },
    { value: 'standard', label: 'Standard', description: 'Production quality, 16GB VRAM' },
    { value: 'high', label: 'High (Cinematic)', description: 'Final renders, 24GB VRAM' }
  ];

  const resolutionPresets = [
    { label: '1080p (1920×1080)', value: [1920, 1080] },
    { label: '4K (3840×2160)', value: [3840, 2160] },
    { label: '720p (1280×720)', value: [1280, 720] },
    { label: 'Custom', value: null }
  ];

  const fpsPresets = [24, 25, 30, 48, 50, 60];

  $: if ($currentProject) {
    settings = { ...$currentProject.settings };
    if (!originalSettings) {
      originalSettings = { ...$currentProject.settings };
    }
  }

  $: hasChanges =
    originalSettings !== null && JSON.stringify(settings) !== JSON.stringify(originalSettings);

  function handleChange() {
    hasChanges = true;
  }

  function handleResolutionPreset(event: Event) {
    const select = event.target as HTMLSelectElement;
    const preset = resolutionPresets.find((p) => p.label === select.value);
    if (preset && preset.value) {
      settings.resolution = preset.value;
      handleChange();
    }
  }

  async function saveSettings() {
    if (!$currentProject) return;

    try {
      // Update project settings via API
      await workspaceApi.updateProjectSettings($currentProject.id, settings);

      // Update store
      currentProject.update((p) => (p ? { ...p, settings } : null));

      originalSettings = { ...settings };
      hasChanges = false;
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  }

  function cancelChanges() {
    if (originalSettings) {
      settings = { ...originalSettings };
      hasChanges = false;
    }
  }
</script>

<div class="project-settings">
  <h2>Project Settings</h2>

  {#if $currentProject}
    <div class="setting-group">
      <label for="project-name">Project Name</label>
      <input id="project-name" type="text" value={$currentProject.name} readonly disabled />
      <small>Project name cannot be changed after creation</small>
    </div>

    <div class="setting-group">
      <label for="fps">Frame Rate (FPS)</label>
      <div class="fps-input">
        <select id="fps" bind:value={settings.fps} on:change={handleChange}>
          {#each fpsPresets as fps}
            <option value={fps}>{fps} fps</option>
          {/each}
        </select>
        <input type="number" bind:value={settings.fps} min="1" max="120" on:change={handleChange} />
      </div>
    </div>

    <div class="setting-group">
      <label>Resolution</label>
      <select on:change={handleResolutionPreset}>
        {#each resolutionPresets as preset}
          <option
            selected={preset.value &&
              preset.value[0] === settings.resolution[0] &&
              preset.value[1] === settings.resolution[1]}
          >
            {preset.label}
          </option>
        {/each}
      </select>
      <div class="resolution-inputs">
        <input
          type="number"
          bind:value={settings.resolution[0]}
          min="128"
          max="7680"
          on:change={handleChange}
        />
        <span>×</span>
        <input
          type="number"
          bind:value={settings.resolution[1]}
          min="128"
          max="4320"
          on:change={handleChange}
        />
      </div>
    </div>

    <div class="setting-group">
      <label>Quality Tier</label>
      <div class="quality-options">
        {#each qualityOptions as option}
          <label class="quality-option">
            <input
              type="radio"
              name="quality"
              value={option.value}
              bind:group={settings.defaultQuality}
              on:change={handleChange}
            />
            <div>
              <strong>{option.label}</strong>
              <small>{option.description}</small>
            </div>
          </label>
        {/each}
      </div>
    </div>

    <div class="setting-group">
      <label for="output-format">Output Format</label>
      <select id="output-format" bind:value={settings.outputFormat} on:change={handleChange}>
        <option value="mp4">MP4 (H.264)</option>
        <option value="mov">MOV (ProRes)</option>
        <option value="webm">WebM</option>
        <option value="png">PNG Sequence</option>
        <option value="exr">EXR Sequence</option>
      </select>
    </div>

    {#if hasChanges}
      <div class="settings-actions">
        <button class="btn-primary" on:click={saveSettings}>Save Changes</button>
        <button class="btn-secondary" on:click={cancelChanges}>Cancel</button>
      </div>
    {/if}
  {:else}
    <p class="no-project">No project selected</p>
  {/if}
</div>

<style>
  .project-settings {
    max-width: 600px;
  }

  h2 {
    margin: 0 0 2rem 0;
    font-size: 1.5rem;
    font-weight: 600;
  }

  .setting-group {
    margin-bottom: 2rem;
  }

  .setting-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .setting-group input,
  .setting-group select {
    width: 100%;
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

  .setting-group small {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.75rem;
    color: var(--text-muted);
  }

  .fps-input {
    display: flex;
    gap: 0.5rem;
  }

  .fps-input select {
    flex: 1;
  }

  .fps-input input {
    width: 100px;
  }

  .resolution-inputs {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  .resolution-inputs input {
    flex: 1;
  }

  .resolution-inputs span {
    color: var(--text-secondary);
  }

  .quality-options {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .quality-option {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .quality-option:hover {
    border-color: var(--color-primary-dim);
  }

  .quality-option:has(input:checked) {
    border-color: var(--color-primary);
    background: var(--color-primary-dim);
  }

  .quality-option input {
    margin-top: 0.125rem;
  }

  .quality-option strong {
    display: block;
    margin-bottom: 0.25rem;
  }

  .quality-option small {
    color: var(--text-secondary);
    font-size: 0.75rem;
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

  .no-project {
    color: var(--text-secondary);
    font-style: italic;
  }
</style>
