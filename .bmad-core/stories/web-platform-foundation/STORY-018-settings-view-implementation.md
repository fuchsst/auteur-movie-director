# STORY-018: Settings View Implementation

**Story ID**: STORY-018  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 3 (Small)  
**Priority**: Medium  
**Status**: ⚠️ Partially Completed (January 2025)

## Story
As a user, I need a settings view in the main panel where I can configure project-level settings, workspace preferences, and view system information, providing a centralized location for all configuration options.

## Acceptance Criteria
- [ ] Settings tab appears in main view area
- [ ] Project settings section with editable fields
- [ ] Workspace settings for default paths
- [ ] System information display (versions, paths)
- [ ] Settings persist across sessions
- [ ] Real-time validation of settings
- [ ] Save/Cancel functionality
- [ ] Settings changes trigger appropriate updates

## Technical Details

### Settings View Component Structure

```svelte
<!-- frontend/src/lib/components/settings/SettingsView.svelte -->
<script lang="ts">
  import { projectStore } from '$lib/stores/project';
  import { workspaceStore } from '$lib/stores/workspace';
  import ProjectSettings from './ProjectSettings.svelte';
  import WorkspaceSettings from './WorkspaceSettings.svelte';
  import SystemInfo from './SystemInfo.svelte';
  
  let activeSection = 'project';
  let hasUnsavedChanges = false;
  
  const sections = [
    { id: 'project', label: 'Project Settings', icon: 'settings' },
    { id: 'workspace', label: 'Workspace', icon: 'folder' },
    { id: 'system', label: 'System Info', icon: 'info' }
  ];
</script>

<div class="settings-view">
  <div class="settings-sidebar">
    {#each sections as section}
      <button
        class="section-button"
        class:active={activeSection === section.id}
        on:click={() => activeSection = section.id}
      >
        <Icon name={section.icon} />
        {section.label}
      </button>
    {/each}
  </div>
  
  <div class="settings-content">
    {#if activeSection === 'project'}
      <ProjectSettings bind:hasChanges={hasUnsavedChanges} />
    {:else if activeSection === 'workspace'}
      <WorkspaceSettings bind:hasChanges={hasUnsavedChanges} />
    {:else if activeSection === 'system'}
      <SystemInfo />
    {/if}
  </div>
</div>
```

### Project Settings Component

```svelte
<!-- frontend/src/lib/components/settings/ProjectSettings.svelte -->
<script lang="ts">
  import { projectStore } from '$lib/stores/project';
  import type { ProjectSettings } from '$lib/types';
  
  export let hasChanges = false;
  
  let settings: ProjectSettings = {
    fps: 24,
    resolution: [1920, 1080],
    aspectRatio: '16:9',
    quality: 'standard'
  };
  
  const qualityOptions = [
    { value: 'low', label: 'Low (Draft)', description: 'Fast iteration, 12GB VRAM' },
    { value: 'standard', label: 'Standard', description: 'Production quality, 16GB VRAM' },
    { value: 'high', label: 'High (Cinematic)', description: 'Final renders, 24GB VRAM' }
  ];
  
  const resolutionPresets = [
    { label: '1080p', value: [1920, 1080] },
    { label: '4K', value: [3840, 2160] },
    { label: '720p', value: [1280, 720] }
  ];
  
  function handleChange() {
    hasChanges = true;
  }
  
  async function saveSettings() {
    await projectStore.updateSettings(settings);
    hasChanges = false;
  }
</script>

<div class="project-settings">
  <h2>Project Settings</h2>
  
  <div class="setting-group">
    <label>Frame Rate (FPS)</label>
    <input
      type="number"
      bind:value={settings.fps}
      min="1"
      max="120"
      on:change={handleChange}
    />
  </div>
  
  <div class="setting-group">
    <label>Resolution</label>
    <select on:change={(e) => {
      const preset = resolutionPresets.find(p => p.label === e.target.value);
      if (preset) {
        settings.resolution = preset.value;
        handleChange();
      }
    }}>
      {#each resolutionPresets as preset}
        <option>{preset.label}</option>
      {/each}
    </select>
    <div class="resolution-inputs">
      <input
        type="number"
        bind:value={settings.resolution[0]}
        on:change={handleChange}
      />
      <span>×</span>
      <input
        type="number"
        bind:value={settings.resolution[1]}
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
            bind:group={settings.quality}
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
  
  {#if hasChanges}
    <div class="settings-actions">
      <button class="btn-primary" on:click={saveSettings}>Save Changes</button>
      <button class="btn-secondary" on:click={() => hasChanges = false}>Cancel</button>
    </div>
  {/if}
</div>
```

### Workspace Settings

```svelte
<!-- frontend/src/lib/components/settings/WorkspaceSettings.svelte -->
<script lang="ts">
  import { workspaceStore } from '$lib/stores/workspace';
  import { apiClient } from '$lib/api';
  
  export let hasChanges = false;
  
  let workspaceRoot = '';
  let defaultQuality = 'standard';
  let autoSaveInterval = 5;
  let enableGitLFS = true;
  
  onMount(async () => {
    const config = await apiClient.getWorkspaceConfig();
    workspaceRoot = config.workspaceRoot;
    defaultQuality = config.defaultQuality;
  });
  
  async function browseFolder() {
    // In a real app, this would open a folder picker
    // For now, just use an input
  }
  
  async function saveSettings() {
    await apiClient.updateWorkspaceConfig({
      workspaceRoot,
      defaultQuality,
      autoSaveInterval,
      enableGitLFS
    });
    hasChanges = false;
  }
</script>

<div class="workspace-settings">
  <h2>Workspace Settings</h2>
  
  <div class="setting-group">
    <label>Workspace Root Directory</label>
    <div class="path-input">
      <input
        type="text"
        bind:value={workspaceRoot}
        on:change={() => hasChanges = true}
        readonly
      />
      <button on:click={browseFolder}>Browse...</button>
    </div>
    <small>Default location for new projects</small>
  </div>
  
  <div class="setting-group">
    <label>Default Quality for New Projects</label>
    <select bind:value={defaultQuality} on:change={() => hasChanges = true}>
      <option value="low">Low (Draft)</option>
      <option value="standard">Standard</option>
      <option value="high">High (Cinematic)</option>
    </select>
  </div>
  
  <div class="setting-group">
    <label>
      <input
        type="checkbox"
        bind:checked={enableGitLFS}
        on:change={() => hasChanges = true}
      />
      Enable Git LFS for new projects
    </label>
    <small>Recommended for managing large media files</small>
  </div>
  
  <div class="setting-group">
    <label>Auto-save Interval (minutes)</label>
    <input
      type="number"
      bind:value={autoSaveInterval}
      min="1"
      max="60"
      on:change={() => hasChanges = true}
    />
  </div>
  
  {#if hasChanges}
    <div class="settings-actions">
      <button class="btn-primary" on:click={saveSettings}>Save Changes</button>
      <button class="btn-secondary" on:click={() => hasChanges = false}>Cancel</button>
    </div>
  {/if}
</div>
```

### System Information

```svelte
<!-- frontend/src/lib/components/settings/SystemInfo.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/api';
  
  let systemInfo = {
    version: '',
    pythonVersion: '',
    nodeVersion: '',
    platform: '',
    gitVersion: '',
    gitLFSInstalled: false,
    dockerVersion: '',
    workspacePath: '',
    apiEndpoint: ''
  };
  
  onMount(async () => {
    systemInfo = await apiClient.getSystemInfo();
  });
</script>

<div class="system-info">
  <h2>System Information</h2>
  
  <div class="info-grid">
    <div class="info-item">
      <label>Application Version</label>
      <span>{systemInfo.version}</span>
    </div>
    
    <div class="info-item">
      <label>Platform</label>
      <span>{systemInfo.platform}</span>
    </div>
    
    <div class="info-item">
      <label>Python Version</label>
      <span>{systemInfo.pythonVersion}</span>
    </div>
    
    <div class="info-item">
      <label>Node.js Version</label>
      <span>{systemInfo.nodeVersion}</span>
    </div>
    
    <div class="info-item">
      <label>Git Version</label>
      <span>{systemInfo.gitVersion}</span>
    </div>
    
    <div class="info-item">
      <label>Git LFS</label>
      <span class:installed={systemInfo.gitLFSInstalled}>
        {systemInfo.gitLFSInstalled ? 'Installed' : 'Not Installed'}
      </span>
    </div>
    
    <div class="info-item">
      <label>Docker Version</label>
      <span>{systemInfo.dockerVersion || 'Not Available'}</span>
    </div>
    
    <div class="info-item full-width">
      <label>Workspace Path</label>
      <code>{systemInfo.workspacePath}</code>
    </div>
    
    <div class="info-item full-width">
      <label>API Endpoint</label>
      <code>{systemInfo.apiEndpoint}</code>
    </div>
  </div>
  
  <div class="system-actions">
    <button on:click={() => location.reload()}>Refresh</button>
    <button on:click={() => navigator.clipboard.writeText(JSON.stringify(systemInfo, null, 2))}>
      Copy to Clipboard
    </button>
  </div>
</div>
```

### Backend API Endpoints

```python
# backend/app/api/endpoints/system.py
from fastapi import APIRouter
import platform
import subprocess
import os
from app.config import settings

router = APIRouter()

@router.get("/system/info")
async def get_system_info():
    """Get system information for display in settings"""
    def get_version(command):
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return None
    
    return {
        "version": settings.APP_VERSION,
        "pythonVersion": platform.python_version(),
        "nodeVersion": get_version(["node", "--version"]),
        "platform": f"{platform.system()} {platform.release()}",
        "gitVersion": get_version(["git", "--version"]),
        "gitLFSInstalled": bool(get_version(["git", "lfs", "version"])),
        "dockerVersion": get_version(["docker", "--version"]),
        "workspacePath": settings.WORKSPACE_ROOT,
        "apiEndpoint": f"http://localhost:{settings.BACKEND_PORT}"
    }

@router.get("/workspace/config")
async def get_workspace_config():
    """Get workspace configuration"""
    return {
        "workspaceRoot": settings.WORKSPACE_ROOT,
        "defaultQuality": settings.DEFAULT_QUALITY,
        "autoSaveInterval": settings.AUTO_SAVE_INTERVAL,
        "enableGitLFS": settings.ENABLE_GIT_LFS
    }

@router.put("/workspace/config")
async def update_workspace_config(config: dict):
    """Update workspace configuration"""
    # In a real implementation, this would persist to a config file
    # For now, just validate and return success
    return {"status": "updated", "config": config}
```

### Styling

```css
/* frontend/src/lib/components/settings/settings.css */
.settings-view {
  display: flex;
  height: 100%;
  background: var(--color-bg);
}

.settings-sidebar {
  width: 200px;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
  padding: 1rem;
}

.section-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.section-button:hover {
  background: var(--color-bg-hover);
}

.section-button.active {
  background: var(--color-primary);
  color: white;
}

.settings-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.setting-group {
  margin-bottom: 2rem;
}

.setting-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.quality-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.quality-option {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 1rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
}

.quality-option:has(input:checked) {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-item label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.settings-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid var(--color-border);
}
```

## Integration Points
- Main view tab system (STORY-016)
- WebSocket for real-time updates
- Project store for settings persistence
- API client for backend communication

## Dependencies
- STORY-007: SvelteKit Application Setup
- STORY-011: API Client Setup
- STORY-016: Main View Tab System

## Notes
- Settings are stored in both project.json (project-specific) and workspace config (global)
- System info is read-only and provides diagnostic information
- Changes to critical settings (like quality) may trigger confirmation dialogs
- Consider adding import/export functionality for settings profiles in the future

## Implementation Status (January 2025)

### ✅ Completed Components (~70% Complete)

1. **Frontend Components**:
   - `SettingsView.svelte` - Main view with sidebar navigation
   - `ProjectSettings.svelte` - Complete UI for project configuration
   - `WorkspaceSettings.svelte` - UI for workspace preferences
   - `SystemInfo.svelte` - System information display
   - `SettingsSection.svelte` - Section routing component

2. **UI Features** (7/8):
   - ✅ Settings tab in main view area
   - ✅ Project settings section with forms
   - ✅ Workspace settings interface
   - ✅ System information display
   - ✅ Real-time validation UI
   - ✅ Save/Cancel UI buttons
   - ✅ Section navigation
   - ❌ Settings persistence

3. **Backend Implementation**:
   - ✅ System info endpoint (`GET /system/info`)
   - ✅ Workspace config endpoint (`GET /workspace/config`)
   - ✅ System API client integration

4. **System Info Display**:
   - Application version
   - Python/Node versions
   - Platform details
   - Git/Git LFS status
   - Workspace paths
   - API endpoints

### ❌ Missing Components (~30% Incomplete)

1. **Backend Endpoints**:
   - ❌ `PUT /workspace/config` - Update workspace settings
   - ❌ `PUT /projects/{id}/settings` - Update project settings
   - ❌ Settings persistence mechanism
   - ❌ Configuration file management

2. **Frontend Integration**:
   - ❌ Actual save functionality (marked as TODO)
   - ❌ Settings change propagation
   - ❌ Folder browser for paths
   - ❌ Session persistence

3. **Code TODOs**:
   - WorkspaceSettings.svelte line 37: "Load editable config from backend"
   - workspace.ts line 66: "Implement when backend endpoint is available"

### Summary
The Settings View UI is well-implemented with all visual components and proper structure. The main gap is the backend persistence layer - the UI exists but cannot actually save settings. This makes it ~70% complete, with the remaining work being backend endpoints and connecting the save functionality.